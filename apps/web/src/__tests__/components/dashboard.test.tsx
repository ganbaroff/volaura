import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// ── Standard mocks ────────────────────────────────────────────────────────────

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  },
  useReducedMotion: () => false,
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: any) => opts?.defaultValue ?? key,
  }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: ({ className }: { className?: string }) =>
    React.createElement("div", { "data-testid": "skeleton", className }),
}));

// ── Component-specific mocks ──────────────────────────────────────────────────

vi.mock("@/hooks/queries/use-character", () => ({
  useCrystalBalance: vi.fn(),
}));

const mockSendKudos = { mutate: vi.fn(), isPending: false, isSuccess: false };
const mockOptOut = { mutate: vi.fn(), isPending: false };
const mockRequestRenewal = { mutate: vi.fn(), isPending: false };
const mockJoinPool = { mutate: vi.fn(), isPending: false };

vi.mock("@/hooks/queries/use-tribes", () => ({
  useMyTribe: vi.fn(),
  useMyStreak: vi.fn(),
  useMyPoolStatus: vi.fn(),
  useSendKudos: vi.fn(() => mockSendKudos),
  useOptOutOfTribe: vi.fn(() => mockOptOut),
  useRequestTribeRenewal: vi.fn(() => mockRequestRenewal),
  useJoinTribePool: vi.fn(() => mockJoinPool),
}));

vi.mock("@/lib/utils/cn", () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(" "),
}));

vi.mock("lucide-react", () => ({
  Target: ({ className, "aria-hidden": ah }: any) => (
    <svg data-testid="icon-target" className={className} aria-hidden={ah} />
  ),
  Users: ({ className, "aria-hidden": ah }: any) => (
    <svg data-testid="icon-users" className={className} aria-hidden={ah} />
  ),
  CalendarCheck: ({ className, "aria-hidden": ah }: any) => (
    <svg data-testid="icon-calendar" className={className} aria-hidden={ah} />
  ),
  Trophy: ({ className, "aria-hidden": ah }: any) => (
    <svg data-testid="icon-trophy" className={className} aria-hidden={ah} />
  ),
  Lightbulb: ({ className, "aria-hidden": ah }: any) => (
    <svg data-testid="icon-lightbulb" className={className} aria-hidden={ah} />
  ),
  ArrowRight: ({ className }: any) => (
    <svg data-testid="icon-arrow-right" className={className} />
  ),
}));

// ── Imports after mocks ───────────────────────────────────────────────────────

import { CrystalBalanceWidget } from "@/components/dashboard/crystal-balance-widget";
import { FeedCards, type FeedCard } from "@/components/dashboard/feed-cards";
import { TribeCard } from "@/components/dashboard/tribe-card";

import { useCrystalBalance } from "@/hooks/queries/use-character";
import {
  useMyTribe,
  useMyStreak,
  useMyPoolStatus,
  useSendKudos,
  useOptOutOfTribe,
  useJoinTribePool,
} from "@/hooks/queries/use-tribes";

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockCrystalBalance = useCrystalBalance as ReturnType<typeof vi.fn>;
const mockUseMyTribe = useMyTribe as ReturnType<typeof vi.fn>;
const mockUseMyStreak = useMyStreak as ReturnType<typeof vi.fn>;
const mockUseMyPoolStatus = useMyPoolStatus as ReturnType<typeof vi.fn>;
const mockUseSendKudos = useSendKudos as ReturnType<typeof vi.fn>;
const mockUseOptOutOfTribe = useOptOutOfTribe as ReturnType<typeof vi.fn>;
const mockUseJoinTribePool = useJoinTribePool as ReturnType<typeof vi.fn>;

function makeTribe(overrides: Record<string, any> = {}) {
  return {
    tribe_id: "t1",
    expires_at: "2026-05-01T00:00:00Z",
    status: "active",
    kudos_count_this_week: 0,
    renewal_requested: false,
    members: [
      { user_id: "u1", display_name: "Alice", avatar_url: null, active_this_week: true },
      { user_id: "u2", display_name: "Bob", avatar_url: null, active_this_week: false },
    ],
    ...overrides,
  };
}

function setupTribeMocks(opts: {
  tribe?: any;
  tribeLoading?: boolean;
  poolStatus?: any;
  poolLoading?: boolean;
  streak?: any;
  sendKudos?: any;
  optOut?: any;
  requestRenewal?: any;
  joinPool?: any;
} = {}) {
  mockUseMyTribe.mockReturnValue({
    data: opts.tribe !== undefined ? opts.tribe : null,
    isLoading: opts.tribeLoading ?? false,
  });
  mockUseMyPoolStatus.mockReturnValue({
    data: opts.poolStatus ?? { in_pool: false, joined_at: null },
    isLoading: opts.poolLoading ?? false,
  });
  mockUseMyStreak.mockReturnValue({
    data: opts.streak ?? { current_streak: 0, longest_streak: 0, crystal_fade_level: 0 },
  });
  mockUseSendKudos.mockReturnValue(opts.sendKudos ?? { ...mockSendKudos });
  mockUseOptOutOfTribe.mockReturnValue(opts.optOut ?? { ...mockOptOut });
  mockUseJoinTribePool.mockReturnValue(opts.joinPool ?? { ...mockJoinPool });
}

// ═════════════════════════════════════════════════════════════════════════════
// 1. CrystalBalanceWidget
// ═════════════════════════════════════════════════════════════════════════════

describe("CrystalBalanceWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Skeleton when loading", () => {
    mockCrystalBalance.mockReturnValue({ data: undefined, isLoading: true, isError: false });
    render(<CrystalBalanceWidget />);
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("returns null when no data and forceShow=false", () => {
    mockCrystalBalance.mockReturnValue({ data: null, isLoading: false, isError: false });
    const { container } = render(<CrystalBalanceWidget />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null when balance=0 and forceShow=false", () => {
    mockCrystalBalance.mockReturnValue({
      data: { user_id: "u1", crystal_balance: 0, computed_at: "" },
      isLoading: false,
      isError: false,
    });
    const { container } = render(<CrystalBalanceWidget />);
    expect(container.firstChild).toBeNull();
  });

  it("shows widget when balance > 0", () => {
    mockCrystalBalance.mockReturnValue({
      data: { user_id: "u1", crystal_balance: 42, computed_at: "" },
      isLoading: false,
      isError: false,
    });
    render(<CrystalBalanceWidget />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("shows formatted balance with toLocaleString", () => {
    mockCrystalBalance.mockReturnValue({
      data: { user_id: "u1", crystal_balance: 1000, computed_at: "" },
      isLoading: false,
      isError: false,
    });
    render(<CrystalBalanceWidget />);
    // toLocaleString may produce "1,000" or "1 000" depending on locale — just check it renders
    const formatted = (1000).toLocaleString();
    expect(screen.getByText(formatted)).toBeInTheDocument();
  });

  it("shows widget with balance=0 when forceShow=true", () => {
    mockCrystalBalance.mockReturnValue({
      data: { user_id: "u1", crystal_balance: 0, computed_at: "" },
      isLoading: false,
      isError: false,
    });
    render(<CrystalBalanceWidget forceShow />);
    // Should render the balance display (not null)
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("shows widget when data is null but forceShow=true", () => {
    mockCrystalBalance.mockReturnValue({ data: null, isLoading: false, isError: false });
    render(<CrystalBalanceWidget forceShow />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("returns null on error (isError=true)", () => {
    mockCrystalBalance.mockReturnValue({
      data: { user_id: "u1", crystal_balance: 100, computed_at: "" },
      isLoading: false,
      isError: true,
    });
    const { container } = render(<CrystalBalanceWidget />);
    expect(container.firstChild).toBeNull();
  });

  it("shows crystal emoji with aria-label", () => {
    mockCrystalBalance.mockReturnValue({
      data: { user_id: "u1", crystal_balance: 5, computed_at: "" },
      isLoading: false,
      isError: false,
    });
    render(<CrystalBalanceWidget />);
    const emoji = screen.getByRole("img");
    expect(emoji).toHaveAttribute("aria-label", "character.crystalLabel");
  });

  it("shows ecosystem hint text", () => {
    mockCrystalBalance.mockReturnValue({
      data: { user_id: "u1", crystal_balance: 5, computed_at: "" },
      isLoading: false,
      isError: false,
    });
    render(<CrystalBalanceWidget />);
    expect(screen.getByText("character.earnOnVolaura")).toBeInTheDocument();
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// 2. FeedCards
// ═════════════════════════════════════════════════════════════════════════════

describe("FeedCards", () => {
  const baseCard: FeedCard = {
    type: "challenge",
    title: "Test Challenge",
    description: "A test description",
  };

  it("shows 3 skeletons when loading=true", () => {
    render(<FeedCards cards={[]} loading locale="en" />);
    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons).toHaveLength(3);
  });

  it("shows empty state with link to assessment when cards=[]", () => {
    render(<FeedCards cards={[]} locale="en" />);
    expect(
      screen.getByText("Complete an assessment to unlock personalized recommendations"),
    ).toBeInTheDocument();
  });

  it("shows empty state action link when cards=[]", () => {
    render(<FeedCards cards={[]} locale="en" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/en/assessment");
  });

  it("shows empty state with link when cards is null/undefined", () => {
    render(<FeedCards cards={null as any} locale="az" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/az/assessment");
  });

  it("renders card titles and descriptions", () => {
    const cards: FeedCard[] = [
      { type: "challenge", title: "My Challenge", description: "Do something hard" },
    ];
    render(<FeedCards cards={cards} locale="en" />);
    expect(screen.getByText("My Challenge")).toBeInTheDocument();
    expect(screen.getByText("Do something hard")).toBeInTheDocument();
  });

  it("challenge card gets amber accent class", () => {
    render(
      <FeedCards cards={[{ type: "challenge", title: "C", description: "D" }]} locale="en" />,
    );
    const title = screen.getByText("C");
    expect(title.className).toContain("text-amber-600");
  });

  it("people card gets blue accent class", () => {
    render(
      <FeedCards cards={[{ type: "people", title: "P", description: "D" }]} locale="en" />,
    );
    expect(screen.getByText("P").className).toContain("text-blue-600");
  });

  it("event card gets green accent class", () => {
    render(
      <FeedCards cards={[{ type: "event", title: "E", description: "D" }]} locale="en" />,
    );
    expect(screen.getByText("E").className).toContain("text-green-600");
  });

  it("achievement card gets purple accent class", () => {
    render(
      <FeedCards cards={[{ type: "achievement", title: "A", description: "D" }]} locale="en" />,
    );
    expect(screen.getByText("A").className).toContain("text-purple-600");
  });

  it("insight card gets cyan accent class", () => {
    render(
      <FeedCards cards={[{ type: "insight", title: "I", description: "D" }]} locale="en" />,
    );
    expect(screen.getByText("I").className).toContain("text-cyan-400");
  });

  it("shows relevance_reason when present", () => {
    const cards: FeedCard[] = [
      { ...baseCard, relevance_reason: "You did well last time" },
    ];
    render(<FeedCards cards={cards} locale="en" />);
    expect(screen.getByText("You did well last time")).toBeInTheDocument();
  });

  it("shows match_reason when present", () => {
    const cards: FeedCard[] = [{ ...baseCard, match_reason: "Skills match 90%" }];
    render(<FeedCards cards={cards} locale="en" />);
    expect(screen.getByText("Skills match 90%")).toBeInTheDocument();
  });

  it("shows CTA text when card has cta and onCardAction", () => {
    const cards: FeedCard[] = [{ ...baseCard, cta: "Start now" }];
    render(<FeedCards cards={cards} locale="en" onCardAction={vi.fn()} />);
    expect(screen.getByText("Start now")).toBeInTheDocument();
  });

  it("calls onCardAction when card clicked", () => {
    const onCardAction = vi.fn();
    const cards: FeedCard[] = [baseCard];
    render(<FeedCards cards={cards} locale="en" onCardAction={onCardAction} />);
    fireEvent.click(screen.getByText("Test Challenge").closest("div[role='button']")!);
    expect(onCardAction).toHaveBeenCalledWith(baseCard);
  });

  it("card has role=button when onCardAction provided", () => {
    render(<FeedCards cards={[baseCard]} locale="en" onCardAction={vi.fn()} />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("card has tabIndex=0 when onCardAction provided", () => {
    render(<FeedCards cards={[baseCard]} locale="en" onCardAction={vi.fn()} />);
    const card = screen.getByRole("button");
    expect(card).toHaveAttribute("tabindex", "0");
  });

  it("no role when no onCardAction", () => {
    render(<FeedCards cards={[baseCard]} locale="en" />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("no tabIndex when no onCardAction", () => {
    render(<FeedCards cards={[baseCard]} locale="en" />);
    const titleEl = screen.getByText("Test Challenge");
    const cardEl = titleEl.closest("div");
    expect(cardEl).not.toHaveAttribute("tabindex");
  });

  it("achievement with celebration_level=big gets ring class", () => {
    const cards: FeedCard[] = [
      { type: "achievement", title: "Big Win", description: "D", celebration_level: "big" },
    ];
    render(<FeedCards cards={cards} locale="en" />);
    const title = screen.getByText("Big Win");
    // The ring class is on the outer card div, walk up until we find it
    let el: HTMLElement | null = title;
    let found = false;
    while (el) {
      if (el.className.includes("ring-2")) {
        found = true;
        break;
      }
      el = el.parentElement;
    }
    expect(found).toBe(true);
  });

  it("achievement with celebration_level=small does not get ring class", () => {
    const cards: FeedCard[] = [
      { type: "achievement", title: "Small Win", description: "D", celebration_level: "small" },
    ];
    const { container } = render(<FeedCards cards={cards} locale="en" />);
    expect(container.querySelector(".ring-2")).toBeNull();
  });

  it("limits cards to 7 (slice 0..7)", () => {
    const cards: FeedCard[] = Array.from({ length: 10 }, (_, i) => ({
      type: "insight" as const,
      title: `Card ${i}`,
      description: "D",
    }));
    render(<FeedCards cards={cards} locale="en" />);
    // Cards 0-6 should be present, card 7+ absent
    expect(screen.getByText("Card 6")).toBeInTheDocument();
    expect(screen.queryByText("Card 7")).toBeNull();
  });

  it("empty state link uses correct locale", () => {
    render(<FeedCards cards={[]} locale="az" />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/az/assessment");
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// 3. TribeCard
// ═════════════════════════════════════════════════════════════════════════════

describe("TribeCard — loading state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSendKudos.mockReturnValue({ ...mockSendKudos });
    mockUseOptOutOfTribe.mockReturnValue({ ...mockOptOut });
    vi.mocked(vi.importMock?.("@/hooks/queries/use-tribes") as any);
  });

  it("returns null when tribeLoading=true", () => {
    setupTribeMocks({ tribeLoading: true });
    const { container } = render(<TribeCard />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null when poolLoading=true", () => {
    setupTribeMocks({ poolLoading: true });
    const { container } = render(<TribeCard />);
    expect(container.firstChild).toBeNull();
  });
});

describe("TribeCard — no tribe states", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows 'Finding your tribe' when no tribe and in_pool=true", () => {
    setupTribeMocks({ tribe: null, poolStatus: { in_pool: true, joined_at: "2026-01-01" } });
    render(<TribeCard />);
    expect(screen.getByText("Finding your tribe...")).toBeInTheDocument();
  });

  it("shows 'Joined pool' message when no tribe and in_pool=true", () => {
    setupTribeMocks({ tribe: null, poolStatus: { in_pool: true, joined_at: "2026-01-01" } });
    render(<TribeCard />);
    expect(screen.getByText("You're in the pool! Matched within 24h.")).toBeInTheDocument();
  });

  it("shows 'Join a Tribe' CTA when no tribe and not in pool", () => {
    setupTribeMocks({ tribe: null, poolStatus: { in_pool: false, joined_at: null } });
    render(<TribeCard />);
    expect(screen.getByText("Join a Tribe")).toBeInTheDocument();
  });

  it("join button calls joinPool.mutate on click", () => {
    const mutateFn = vi.fn();
    setupTribeMocks({
      tribe: null,
      poolStatus: { in_pool: false, joined_at: null },
      joinPool: { mutate: mutateFn, isPending: false },
    });
    render(<TribeCard />);
    fireEvent.click(screen.getByRole("button", { name: /find my tribe/i }));
    expect(mutateFn).toHaveBeenCalledOnce();
  });

  it("join button is disabled when isPending", () => {
    setupTribeMocks({
      tribe: null,
      poolStatus: { in_pool: false, joined_at: null },
      joinPool: { mutate: vi.fn(), isPending: true },
    });
    render(<TribeCard />);
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
  });
});

describe("TribeCard — tribe exists", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows tribe member display names", () => {
    setupTribeMocks({ tribe: makeTribe() });
    render(<TribeCard />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("shows active indicator text for active members", () => {
    setupTribeMocks({ tribe: makeTribe() });
    render(<TribeCard />);
    // MemberRow renders "✓ active" label for active members
    expect(screen.getByText("✓ active")).toBeInTheDocument();
  });

  it("shows emerald activity dot for active member", () => {
    setupTribeMocks({ tribe: makeTribe() });
    render(<TribeCard />);
    const dots = document.querySelectorAll('[aria-label]');
    const activeDot = Array.from(dots).find(
      (el) => el.getAttribute("aria-label") === "Active this week",
    );
    expect(activeDot).toBeDefined();
    expect(activeDot?.className).toContain("bg-emerald-500");
  });

  it("shows muted activity dot for inactive member", () => {
    setupTribeMocks({ tribe: makeTribe() });
    render(<TribeCard />);
    const inactiveDots = document.querySelectorAll('[aria-label="Not active yet this week"]');
    expect(inactiveDots.length).toBeGreaterThan(0);
    expect(inactiveDots[0].className).toContain("bg-muted-foreground/30");
  });

  it("shows avatar image when avatar_url is present", () => {
    const tribe = makeTribe({
      members: [
        { user_id: "u1", display_name: "Alice", avatar_url: "https://example.com/avatar.png", active_this_week: true },
      ],
    });
    setupTribeMocks({ tribe });
    const { container } = render(<TribeCard />);
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    expect(img).toHaveAttribute("src", "https://example.com/avatar.png");
  });

  it("shows initial letter when no avatar_url", () => {
    setupTribeMocks({ tribe: makeTribe() });
    render(<TribeCard />);
    // Alice → "A", Bob → "B"
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
  });

  it("shows streak count when currentStreak > 1", () => {
    setupTribeMocks({
      tribe: makeTribe(),
      streak: { current_streak: 3, longest_streak: 5, crystal_fade_level: 0 },
    });
    render(<TribeCard />);
    expect(screen.getByText("3 week streak")).toBeInTheDocument();
  });

  it("hides streak display when currentStreak <= 1", () => {
    setupTribeMocks({
      tribe: makeTribe(),
      streak: { current_streak: 1, longest_streak: 1, crystal_fade_level: 0 },
    });
    render(<TribeCard />);
    expect(screen.queryByText(/week streak/)).toBeNull();
  });

  it("shows crystal fading message when fadeLevel > 0", () => {
    setupTribeMocks({
      tribe: makeTribe(),
      streak: { current_streak: 0, longest_streak: 0, crystal_fade_level: 1 },
    });
    render(<TribeCard />);
    expect(screen.getByText("Your crystal glow is fading")).toBeInTheDocument();
  });

  it("does not show crystal fading message when fadeLevel=0", () => {
    setupTribeMocks({
      tribe: makeTribe(),
      streak: { current_streak: 0, longest_streak: 0, crystal_fade_level: 0 },
    });
    render(<TribeCard />);
    expect(screen.queryByText("Your crystal glow is fading")).toBeNull();
  });
});

describe("TribeCard — kudos section", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows 'Be the first to send kudos' when kudosCount=0", () => {
    setupTribeMocks({ tribe: makeTribe({ kudos_count_this_week: 0 }) });
    render(<TribeCard />);
    expect(screen.getByText("Be the first to send kudos")).toBeInTheDocument();
  });

  it("never shows '0 kudos'", () => {
    setupTribeMocks({ tribe: makeTribe({ kudos_count_this_week: 0 }) });
    render(<TribeCard />);
    expect(screen.queryByText(/0 kudos/)).toBeNull();
  });

  it("shows kudos count when kudosCount > 0", () => {
    setupTribeMocks({ tribe: makeTribe({ kudos_count_this_week: 5 }) });
    render(<TribeCard />);
    expect(screen.getByText("5 kudos this week")).toBeInTheDocument();
  });

  it("send kudos button calls sendKudos.mutate", () => {
    const mutateFn = vi.fn();
    setupTribeMocks({
      tribe: makeTribe(),
      sendKudos: { mutate: mutateFn, isPending: false, isSuccess: false },
    });
    render(<TribeCard />);
    fireEvent.click(screen.getByText("Send kudos"));
    expect(mutateFn).toHaveBeenCalledOnce();
  });

  it("shows 'Sent ✓' when isSuccess", () => {
    setupTribeMocks({
      tribe: makeTribe(),
      sendKudos: { mutate: vi.fn(), isPending: false, isSuccess: true },
    });
    render(<TribeCard />);
    expect(screen.getByText("Sent ✓")).toBeInTheDocument();
  });
});

describe("TribeCard — opt-out flow", () => {
  beforeEach(() => vi.clearAllMocks());

  it("opt-out confirmation appears after clicking overflow menu then leave", () => {
    const optOutMutate = vi.fn();
    setupTribeMocks({
      tribe: makeTribe(),
      optOut: { mutate: optOutMutate, isPending: false },
    });
    render(<TribeCard />);

    // Open overflow menu (···)
    const moreBtn = screen.getByRole("button", { name: "More options" });
    fireEvent.click(moreBtn);

    // Click "Leave this tribe"
    fireEvent.click(screen.getByText("Leave this tribe"));

    // Confirmation dialog now visible
    expect(
      screen.getByText(/Leave this tribe\? Your streak is safe/),
    ).toBeInTheDocument();
  });

  it("opt-out confirm button calls optOut.mutate", () => {
    const optOutMutate = vi.fn();
    setupTribeMocks({
      tribe: makeTribe(),
      optOut: { mutate: optOutMutate, isPending: false },
    });
    render(<TribeCard />);

    // Open overflow → leave
    fireEvent.click(screen.getByRole("button", { name: "More options" }));
    fireEvent.click(screen.getByText("Leave this tribe"));

    // Click the confirm button
    fireEvent.click(screen.getByText("Leave tribe"));
    expect(optOutMutate).toHaveBeenCalledOnce();
  });

  it("cancel button dismisses opt-out confirmation", () => {
    setupTribeMocks({ tribe: makeTribe() });
    render(<TribeCard />);

    fireEvent.click(screen.getByRole("button", { name: "More options" }));
    fireEvent.click(screen.getByText("Leave this tribe"));

    expect(screen.getByText("Leave tribe")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Cancel"));
    expect(screen.queryByText("Leave tribe")).toBeNull();
  });
});
