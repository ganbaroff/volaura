import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import React from "react";

// ── Global browser API stubs ──────────────────────────────────────────────────

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = (cb: FrameRequestCallback) =>
      setTimeout(cb, 16) as unknown as number;
    window.cancelAnimationFrame = (id: number) => clearTimeout(id);
  }
});

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const base = opts?.defaultValue ? String(opts.defaultValue) : key;
      // Interpolate {{count}} if count is provided
      if (opts?.count !== undefined) {
        return base.replace("{{count}}", String(opts.count));
      }
      return base;
    },
    i18n: { language: "en" },
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/en",
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    className,
    "aria-label": ariaLabel,
    ...rest
  }: {
    href: string;
    children?: React.ReactNode;
    className?: string;
    "aria-label"?: string;
    [key: string]: unknown;
  }) =>
    React.createElement(
      "a",
      { href, className, "aria-label": ariaLabel, ...rest },
      children
    ),
}));

vi.mock("framer-motion", () => {
  type PassthroughProps = {
    children?: React.ReactNode;
    initial?: unknown;
    animate?: unknown;
    exit?: unknown;
    whileInView?: unknown;
    viewport?: unknown;
    transition?: unknown;
    variants?: unknown;
    custom?: unknown;
    style?: React.CSSProperties;
    className?: string;
    "aria-label"?: string;
    "aria-labelledby"?: string;
    id?: string;
    [key: string]: unknown;
  };

  const makePassthrough = (tag: string) => {
    function PassthroughComponent({
      children,
      initial: _i,
      animate: _a,
      exit: _e,
      whileInView: _w,
      viewport: _vp,
      transition: _tr,
      variants: _v,
      custom: _c,
      style,
      className,
      "aria-label": ariaLabel,
      "aria-labelledby": ariaLabelledBy,
      id,
      ...rest
    }: PassthroughProps) {
      return React.createElement(
        tag as keyof React.JSX.IntrinsicElements,
        { className, style, "aria-label": ariaLabel, "aria-labelledby": ariaLabelledBy, id, ...rest },
        children
      );
    }
    PassthroughComponent.displayName = `Motion_${tag}`;
    return PassthroughComponent;
  };

  function AnimatePresenceMock({ children }: { children: React.ReactNode }) {
    return React.createElement(React.Fragment, null, children);
  }

  return {
    motion: {
      div: makePassthrough("div"),
      h1: makePassthrough("h1"),
      h2: makePassthrough("h2"),
      p: makePassthrough("p"),
      article: makePassthrough("article"),
      section: makePassthrough("section"),
      span: makePassthrough("span"),
      ul: makePassthrough("ul"),
      li: makePassthrough("li"),
    },
    useReducedMotion: vi.fn(() => false),
    AnimatePresence: AnimatePresenceMock,
  };
});

vi.mock("@/lib/utils/cn", () => ({
  cn: (...classes: (string | undefined | null | false)[]) =>
    classes.filter(Boolean).join(" "),
}));

// ── Hook mocks ────────────────────────────────────────────────────────────────

const mockRegisterMutate = vi.fn();

const mockRegisterMutation: any = {
  mutate: mockRegisterMutate,
  isSuccess: false,
  isPending: false,
};

vi.mock("@/hooks/queries/use-events", () => ({
  useRegisterForEvent: vi.fn(() => mockRegisterMutation),
}));

vi.mock("@/hooks/queries/use-aura-explanation", () => ({
  useAuraExplanation: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    error: null,
  })),
}));

vi.mock("@/hooks/queries/use-community-signal", () => ({
  useCommunitySignal: vi.fn(() => ({
    data: { professionals_today: 10, professionals_this_week: 247, total_professionals: 1200 },
    isLoading: false,
    isError: false,
  })),
}));

// ── Component imports (after mocks) ──────────────────────────────────────────

import { EventCard } from "@/components/events/event-card";
import { EventsList } from "@/components/events/events-list";
import { EvaluationLog } from "@/components/aura/evaluation-log";
import { ShareButtons } from "@/components/aura/share-buttons";
import { CommunitySignalInline } from "@/components/community/community-signal-inline";
import { useRegisterForEvent } from "@/hooks/queries/use-events";
import { useAuraExplanation } from "@/hooks/queries/use-aura-explanation";
import { useCommunitySignal } from "@/hooks/queries/use-community-signal";
import type { EventResponse } from "@/lib/api/types";
import type { AuraExplanationResponse } from "@/hooks/queries/use-aura-explanation";

// ── Test fixtures ─────────────────────────────────────────────────────────────

function makeEvent(overrides: Partial<EventResponse> = {}): EventResponse {
  return {
    id: "evt-001",
    organization_id: "org-001",
    title_en: "Tech Volunteer Summit",
    title_az: "Texnologiya Könüllü Zirvəsi",
    description_en: "A great tech event",
    description_az: "Gözəl texnologiya tədbirı",
    event_type: "workshop",
    location: "Baku, Azerbaijan",
    start_date: "2026-05-10T10:00:00Z",
    end_date: "2026-05-10T18:00:00Z",
    capacity: 50,
    required_min_aura: 0,
    required_languages: ["en"],
    status: "open",
    is_public: true,
    created_at: "2026-04-01T00:00:00Z",
    updated_at: "2026-04-01T00:00:00Z",
    ...overrides,
  };
}

function makeExplanation(): AuraExplanationResponse {
  return {
    volunteer_id: "user-001",
    explanation_count: 2,
    methodology_reference: "BARS",
    explanations: [
      {
        competency_id: "communication",
        role_level: "junior",
        completed_at: "2026-04-10T12:00:00Z",
        items_evaluated: 5,
        evaluations: [
          {
            question_id: "q-001",
            concept_scores: { clarity: 0.8, listening: 0.7 },
            evaluation_confidence: "high",
            methodology: "BARS",
          },
        ],
      },
      {
        competency_id: "leadership",
        role_level: "junior",
        completed_at: "2026-04-11T12:00:00Z",
        items_evaluated: 4,
        evaluations: [
          {
            question_id: "q-002",
            concept_scores: { initiative: 0.6 },
            evaluation_confidence: "medium",
            methodology: "BARS",
          },
        ],
      },
    ],
  };
}

// ── 1. EventCard ──────────────────────────────────────────────────────────────

describe("EventCard — basic rendering", () => {
  beforeEach(() => {
    vi.mocked(useRegisterForEvent).mockReturnValue({
      ...mockRegisterMutation,
      isSuccess: false,
      isPending: false,
    } as ReturnType<typeof useRegisterForEvent>);
  });

  it("renders an article element", () => {
    render(<EventCard event={makeEvent()} locale="en" />);
    expect(document.querySelector("article")).toBeInTheDocument();
  });

  it("article has aria-label equal to English title", () => {
    render(<EventCard event={makeEvent()} locale="en" />);
    const article = document.querySelector("article");
    expect(article).toHaveAttribute("aria-label", "Tech Volunteer Summit");
  });

  it("shows Azerbaijani title when locale=az", () => {
    render(<EventCard event={makeEvent()} locale="az" />);
    expect(screen.getByText("Texnologiya Könüllü Zirvəsi")).toBeInTheDocument();
  });

  it("shows English title when locale=en", () => {
    render(<EventCard event={makeEvent()} locale="en" />);
    expect(screen.getByText("Tech Volunteer Summit")).toBeInTheDocument();
  });

  it("renders view details link with correct locale href", () => {
    render(<EventCard event={makeEvent()} locale="en" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/en/events/evt-001");
  });

  it("uses az locale in details link href", () => {
    render(<EventCard event={makeEvent()} locale="az" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/az/events/evt-001");
  });

  it("renders location when provided", () => {
    render(<EventCard event={makeEvent()} locale="en" />);
    expect(screen.getByText("Baku, Azerbaijan")).toBeInTheDocument();
  });

  it("does not render location row when location is null", () => {
    render(<EventCard event={makeEvent({ location: null })} locale="en" />);
    expect(screen.queryByText("Baku, Azerbaijan")).not.toBeInTheDocument();
  });

  it("renders capacity when provided", () => {
    render(<EventCard event={makeEvent({ capacity: 30 })} locale="en" />);
    expect(screen.getByText("30 spots")).toBeInTheDocument();
  });

  it("does not render capacity row when capacity is null", () => {
    const { container } = render(
      <EventCard event={makeEvent({ capacity: null })} locale="en" />
    );
    const usersIcons = container.querySelectorAll("svg");
    // MapPin + Calendar icons, no Users icon
    const iconCount = usersIcons.length;
    expect(iconCount).toBeLessThan(4);
  });
});

describe("EventCard — status display", () => {
  beforeEach(() => {
    vi.mocked(useRegisterForEvent).mockReturnValue({
      ...mockRegisterMutation,
      isSuccess: false,
      isPending: false,
    } as ReturnType<typeof useRegisterForEvent>);
  });

  it("shows upcoming status for open event", () => {
    render(<EventCard event={makeEvent({ status: "open" })} locale="en" />);
    expect(screen.getByText("events.upcoming")).toBeInTheDocument();
  });

  it("shows past status for completed event", () => {
    render(<EventCard event={makeEvent({ status: "completed" })} locale="en" />);
    expect(screen.getByText("events.past")).toBeInTheDocument();
  });

  it("shows past status for cancelled event", () => {
    render(<EventCard event={makeEvent({ status: "cancelled" })} locale="en" />);
    expect(screen.getByText("events.past")).toBeInTheDocument();
  });

  it("shows past status for closed event", () => {
    render(<EventCard event={makeEvent({ status: "closed" })} locale="en" />);
    expect(screen.getByText("events.past")).toBeInTheDocument();
  });

  it("status bar has aria-live=polite", () => {
    const { container } = render(<EventCard event={makeEvent()} locale="en" />);
    const statusBar = container.querySelector('[aria-live="polite"]');
    expect(statusBar).toBeInTheDocument();
  });
});

describe("EventCard — register button", () => {
  beforeEach(() => {
    vi.mocked(useRegisterForEvent).mockReturnValue({
      ...mockRegisterMutation,
      isSuccess: false,
      isPending: false,
    } as ReturnType<typeof useRegisterForEvent>);
  });

  it("renders register button for open event", () => {
    render(<EventCard event={makeEvent({ status: "open" })} locale="en" />);
    const btn = screen.getByRole("button", { name: "events.register" });
    expect(btn).toBeInTheDocument();
  });

  it("does not render register button for past event", () => {
    render(<EventCard event={makeEvent({ status: "completed" })} locale="en" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("register button calls mutate on click", () => {
    render(<EventCard event={makeEvent()} locale="en" />);
    const btn = screen.getByRole("button", { name: "events.register" });
    fireEvent.click(btn);
    expect(mockRegisterMutate).toHaveBeenCalledWith({ eventId: "evt-001" });
  });

  it("register button is disabled and shows full text when capacity=0", () => {
    render(<EventCard event={makeEvent({ capacity: 0 })} locale="en" />);
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
    expect(screen.getByText("events.full")).toBeInTheDocument();
  });

  it("shows registered state when mutation succeeded", () => {
    vi.mocked(useRegisterForEvent).mockReturnValue({
      ...mockRegisterMutation,
      isSuccess: true,
      isPending: false,
    } as ReturnType<typeof useRegisterForEvent>);
    render(<EventCard event={makeEvent()} locale="en" />);
    const btn = screen.getByRole("button", { name: "events.registered" });
    expect(btn).toBeDisabled();
    expect(screen.getByText("events.registered")).toBeInTheDocument();
  });

  it("register button is disabled while registering", () => {
    vi.mocked(useRegisterForEvent).mockReturnValue({
      ...mockRegisterMutation,
      isSuccess: false,
      isPending: true,
    } as ReturnType<typeof useRegisterForEvent>);
    render(<EventCard event={makeEvent()} locale="en" />);
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("aria-busy", "true");
  });

  it("calendar icon is aria-hidden", () => {
    const { container } = render(<EventCard event={makeEvent()} locale="en" />);
    const icons = container.querySelectorAll('svg[aria-hidden="true"]');
    expect(icons.length).toBeGreaterThan(0);
  });
});

// ── 2. EventsList ─────────────────────────────────────────────────────────────

describe("EventsList — filter tabs", () => {
  beforeEach(() => {
    vi.mocked(useRegisterForEvent).mockReturnValue({
      ...mockRegisterMutation,
    } as ReturnType<typeof useRegisterForEvent>);
  });

  it("renders tablist with aria-label Filter events", () => {
    render(<EventsList events={[makeEvent()]} locale="en" />);
    expect(
      screen.getByRole("tablist", { name: "Filter events" })
    ).toBeInTheDocument();
  });

  it("renders all 3 filter tabs", () => {
    render(<EventsList events={[makeEvent()]} locale="en" />);
    expect(screen.getByRole("tab", { name: "events.filterAll" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "events.filterUpcoming" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "events.filterPast" })).toBeInTheDocument();
  });

  it("all tab is selected by default", () => {
    render(<EventsList events={[makeEvent()]} locale="en" />);
    expect(
      screen.getByRole("tab", { name: "events.filterAll" })
    ).toHaveAttribute("aria-selected", "true");
  });

  it("upcoming tab becomes selected on click", () => {
    render(<EventsList events={[makeEvent()]} locale="en" />);
    const upcomingTab = screen.getByRole("tab", { name: "events.filterUpcoming" });
    fireEvent.click(upcomingTab);
    expect(upcomingTab).toHaveAttribute("aria-selected", "true");
  });

  it("past tab becomes selected on click", () => {
    render(<EventsList events={[makeEvent()]} locale="en" />);
    const pastTab = screen.getByRole("tab", { name: "events.filterPast" });
    fireEvent.click(pastTab);
    expect(pastTab).toHaveAttribute("aria-selected", "true");
  });

  it("all tab deselected when upcoming is clicked", () => {
    render(<EventsList events={[makeEvent()]} locale="en" />);
    fireEvent.click(screen.getByRole("tab", { name: "events.filterUpcoming" }));
    expect(
      screen.getByRole("tab", { name: "events.filterAll" })
    ).toHaveAttribute("aria-selected", "false");
  });
});

describe("EventsList — events grid", () => {
  beforeEach(() => {
    vi.mocked(useRegisterForEvent).mockReturnValue({
      ...mockRegisterMutation,
    } as ReturnType<typeof useRegisterForEvent>);
  });

  it("renders events grid with role=list when events exist", () => {
    render(<EventsList events={[makeEvent()]} locale="en" />);
    expect(screen.getByRole("list", { name: "Events list" })).toBeInTheDocument();
  });

  it("renders each event as a listitem", () => {
    const events = [makeEvent({ id: "a" }), makeEvent({ id: "b" })];
    render(<EventsList events={events} locale="en" />);
    const items = screen.getAllByRole("listitem");
    expect(items.length).toBe(2);
  });

  it("filters to upcoming when upcoming tab clicked", () => {
    const events = [
      makeEvent({ id: "open-1", status: "open" }),
      makeEvent({ id: "done-1", status: "completed", title_en: "Past Event" }),
    ];
    render(<EventsList events={events} locale="en" />);
    fireEvent.click(screen.getByRole("tab", { name: "events.filterUpcoming" }));
    expect(screen.getByText("Tech Volunteer Summit")).toBeInTheDocument();
    expect(screen.queryByText("Past Event")).not.toBeInTheDocument();
  });

  it("filters to past when past tab clicked", () => {
    const events = [
      makeEvent({ id: "open-1", status: "open" }),
      makeEvent({ id: "done-1", status: "completed", title_en: "Past Event" }),
    ];
    render(<EventsList events={events} locale="en" />);
    fireEvent.click(screen.getByRole("tab", { name: "events.filterPast" }));
    expect(screen.queryByText("Tech Volunteer Summit")).not.toBeInTheDocument();
    expect(screen.getByText("Past Event")).toBeInTheDocument();
  });
});

describe("EventsList — empty state", () => {
  beforeEach(() => {
    vi.mocked(useRegisterForEvent).mockReturnValue({
      ...mockRegisterMutation,
    } as ReturnType<typeof useRegisterForEvent>);
  });

  it("shows empty state when events array is empty", () => {
    render(<EventsList events={[]} locale="en" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText("events.noEvents")).toBeInTheDocument();
    expect(screen.getByText("events.noEventsSubtitle")).toBeInTheDocument();
  });

  it("shows empty state when all events are filtered out", () => {
    // One completed event, switch to upcoming
    render(
      <EventsList
        events={[makeEvent({ status: "completed" })]}
        locale="en"
      />
    );
    fireEvent.click(screen.getByRole("tab", { name: "events.filterUpcoming" }));
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText("events.noEvents")).toBeInTheDocument();
  });

  it("empty state icon is aria-hidden", () => {
    const { container } = render(<EventsList events={[]} locale="en" />);
    const icon = container.querySelector('svg[aria-hidden="true"]');
    expect(icon).toBeInTheDocument();
  });

  it("shows events grid when events exist (no empty state)", () => {
    render(<EventsList events={[makeEvent()]} locale="en" />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});

// ── 3. EvaluationLog ─────────────────────────────────────────────────────────

describe("EvaluationLog — closed state (default)", () => {
  beforeEach(() => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
        
    } as any);
  });

  it("renders the toggle button", () => {
    render(<EvaluationLog />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("toggle button shows why-this-score label", () => {
    render(<EvaluationLog />);
    expect(screen.getByText("aura.whyThisScore")).toBeInTheDocument();
  });

  it("toggle button has aria-expanded=false initially", () => {
    render(<EvaluationLog />);
    const btn = screen.getByRole("button");
    expect(btn).toHaveAttribute("aria-expanded", "false");
  });

  it("toggle button has aria-controls=evaluation-log-body", () => {
    render(<EvaluationLog />);
    const btn = screen.getByRole("button");
    expect(btn).toHaveAttribute("aria-controls", "evaluation-log-body");
  });

  it("section has id evaluation-log-section", () => {
    const { container } = render(<EvaluationLog />);
    const section = container.querySelector("#evaluation-log-section");
    expect(section).toBeInTheDocument();
  });

  it("chevron down icon present when closed", () => {
    const { container } = render(<EvaluationLog />);
    const icons = container.querySelectorAll('svg[aria-hidden="true"]');
    expect(icons.length).toBeGreaterThan(0);
  });
});

describe("EvaluationLog — open state", () => {
  it("aria-expanded becomes true after click", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    const btn = screen.getByRole("button");
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
  });

  it("shows loading skeleton while fetching", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    const { container } = { container: document.body };
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows error message when error occurs", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Failed"),
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByText("error.generic")).toBeInTheDocument();
  });

  it("shows empty state when no explanations", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: { volunteer_id: "u1", explanation_count: 0, methodology_reference: "BARS", explanations: [] },
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByText("aura.noExplanations")).toBeInTheDocument();
  });

  it("renders competency cards with data", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: makeExplanation(),
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    // "Communication" formatted from competency_id "communication"
    expect(screen.getByText("Communication")).toBeInTheDocument();
    expect(screen.getByText("Leadership")).toBeInTheDocument();
  });

  it("renders concept score progress bars", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: makeExplanation(),
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    const bars = screen.getAllByRole("progressbar");
    expect(bars.length).toBeGreaterThan(0);
  });

  it("progress bars have aria-valuenow, aria-valuemin, aria-valuemax", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: makeExplanation(),
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    const bars = screen.getAllByRole("progressbar");
    bars.forEach((bar) => {
      expect(bar).toHaveAttribute("aria-valuenow");
      expect(bar).toHaveAttribute("aria-valuemin", "0");
      expect(bar).toHaveAttribute("aria-valuemax", "100");
    });
  });

  it("shows concept scores label", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: makeExplanation(),
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getAllByText("aura.conceptScores").length).toBeGreaterThan(0);
  });

  it("shows methodology note when data has explanations", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: makeExplanation(),
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByText("aura.methodologyNote")).toBeInTheDocument();
  });

  it("closes when toggle button clicked again", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    const btn = screen.getByRole("button");
    fireEvent.click(btn); // open
    fireEvent.click(btn); // close
    expect(btn).toHaveAttribute("aria-expanded", "false");
  });

  it("shows methodology value (BARS) in competency card", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: makeExplanation(),
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getAllByText("BARS").length).toBeGreaterThan(0);
  });

  it("items_evaluated count is shown", () => {
    vi.mocked(useAuraExplanation).mockReturnValue({
      data: makeExplanation(),
      isLoading: false,
      error: null,
        
    } as any);
    render(<EvaluationLog />);
    fireEvent.click(screen.getByRole("button"));
    // items_evaluated = 5 for first competency
    expect(screen.getByText(/5/)).toBeInTheDocument();
  });
});

// ── 4. ShareButtons ───────────────────────────────────────────────────────────

describe("ShareButtons — no username (guard state)", () => {
  it("shows set-username prompt when username is null", () => {
    render(
      <ShareButtons username={null} overallScore={74} badgeTier="silver" />
    );
    expect(
      screen.getByText("Set a username in Settings to unlock sharing.")
    ).toBeInTheDocument();
  });

  it("shows set-username prompt when username is undefined", () => {
    render(
      <ShareButtons username={undefined} overallScore={74} badgeTier="silver" />
    );
    expect(
      screen.getByText("Set a username in Settings to unlock sharing.")
    ).toBeInTheDocument();
  });

  it("shows settings link when settingsUrl provided", () => {
    render(
      <ShareButtons
        username={null}
        overallScore={74}
        badgeTier="silver"
        settingsUrl="/en/settings"
      />
    );
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/en/settings");
    expect(link).toHaveTextContent("Go to Settings →");
  });

  it("does not show settings link when settingsUrl not provided", () => {
    render(
      <ShareButtons username={null} overallScore={74} badgeTier="silver" />
    );
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("does not render share buttons when username is null", () => {
    render(
      <ShareButtons username={null} overallScore={74} badgeTier="silver" />
    );
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("ShareButtons — with username", () => {
  it("renders copy link button", () => {
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    expect(screen.getByText("aura.copyLink")).toBeInTheDocument();
  });

  it("renders telegram button", () => {
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    expect(screen.getByText("aura.telegram")).toBeInTheDocument();
  });

  it("renders linkedin button", () => {
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    expect(screen.getByText("aura.linkedin")).toBeInTheDocument();
  });

  it("renders whatsapp button", () => {
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    expect(screen.getByText("aura.whatsapp")).toBeInTheDocument();
  });

  it("renders tiktok button", () => {
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    expect(screen.getByText("aura.tiktok")).toBeInTheDocument();
  });

  it("renders download card button", () => {
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    expect(screen.getByText("aura.downloadCard")).toBeInTheDocument();
  });

  it("copy link shows copied feedback after click", async () => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    const copyBtn = screen.getByText("aura.copyLink").closest("button")!;
    await act(async () => {
      fireEvent.click(copyBtn);
    });
    await waitFor(() => {
      expect(screen.getByText("aura.copied")).toBeInTheDocument();
    });
  });

  it("tiktok button shows caption-copied feedback after click", async () => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
    vi.stubGlobal("open", vi.fn());
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    const tiktokBtn = screen.getByText("aura.tiktok").closest("button")!;
    await act(async () => {
      fireEvent.click(tiktokBtn);
    });
    await waitFor(() => {
      expect(screen.getByText("Caption copied!")).toBeInTheDocument();
    });
  });

  it("telegram button calls window.open", () => {
    const openSpy = vi.fn();
    window.open = openSpy;
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    const telegramBtn = screen.getByText("aura.telegram").closest("button")!;
    fireEvent.click(telegramBtn);
    expect(openSpy).toHaveBeenCalledWith(
      expect.stringContaining("t.me/share/url"),
      "_blank",
      "noopener"
    );
  });

  it("linkedin button calls window.open with linkedin URL", () => {
    const openSpy = vi.fn();
    window.open = openSpy;
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    const linkedinBtn = screen.getByText("aura.linkedin").closest("button")!;
    fireEvent.click(linkedinBtn);
    expect(openSpy).toHaveBeenCalledWith(
      expect.stringContaining("linkedin.com"),
      "_blank",
      "noopener"
    );
  });

  it("whatsapp button calls window.open with wa.me URL", () => {
    const openSpy = vi.fn();
    window.open = openSpy;
    render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    const waBtn = screen.getByText("aura.whatsapp").closest("button")!;
    fireEvent.click(waBtn);
    expect(openSpy).toHaveBeenCalledWith(
      expect.stringContaining("wa.me"),
      "_blank",
      "noopener"
    );
  });

  it("icons in buttons are aria-hidden", () => {
    const { container } = render(
      <ShareButtons username="leyla" overallScore={74} badgeTier="silver" />
    );
    const hiddenIcons = container.querySelectorAll('svg[aria-hidden="true"]');
    expect(hiddenIcons.length).toBeGreaterThan(0);
  });
});

// ── 5. CommunitySignalInline ─────────────────────────────────────────────────

describe("CommunitySignalInline — renders signal", () => {
  it("renders signal text when data available", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: { professionals_today: 10, professionals_this_week: 247, total_professionals: 1200 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useCommunitySignal>);
    render(<CommunitySignalInline />);
    expect(
      screen.getByText("247 professionals took an assessment this week")
    ).toBeInTheDocument();
  });

  it("container has aria-label for community activity", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: { professionals_today: 10, professionals_this_week: 247, total_professionals: 1200 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useCommunitySignal>);
    render(<CommunitySignalInline />);
    expect(
      screen.getByLabelText("Community activity this week")
    ).toBeInTheDocument();
  });

  it("users icon is aria-hidden", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: { professionals_today: 10, professionals_this_week: 247, total_professionals: 1200 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useCommunitySignal>);
    const { container } = render(<CommunitySignalInline />);
    const icon = container.querySelector('svg[aria-hidden="true"]');
    expect(icon).toBeInTheDocument();
  });
});

describe("CommunitySignalInline — silent states", () => {
  it("renders nothing while loading", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useCommunitySignal>);
    const { container } = render(<CommunitySignalInline />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing on error", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as ReturnType<typeof useCommunitySignal>);
    const { container } = render(<CommunitySignalInline />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when data is null/undefined", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useCommunitySignal>);
    const { container } = render(<CommunitySignalInline />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when professionals_this_week is 0 (silence over zero)", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: { professionals_today: 0, professionals_this_week: 0, total_professionals: 0 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useCommunitySignal>);
    const { container } = render(<CommunitySignalInline />);
    expect(container.firstChild).toBeNull();
  });

  it("renders signal for count=1", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: { professionals_today: 1, professionals_this_week: 1, total_professionals: 1 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useCommunitySignal>);
    render(<CommunitySignalInline />);
    expect(
      screen.getByText("1 professionals took an assessment this week")
    ).toBeInTheDocument();
  });

  it("renders signal for large count", () => {
    vi.mocked(useCommunitySignal).mockReturnValue({
      data: { professionals_today: 500, professionals_this_week: 9999, total_professionals: 50000 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useCommunitySignal>);
    render(<CommunitySignalInline />);
    expect(
      screen.getByText("9999 professionals took an assessment this week")
    ).toBeInTheDocument();
  });
});
