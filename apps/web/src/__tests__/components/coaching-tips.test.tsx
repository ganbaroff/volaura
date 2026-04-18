import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: "en" } }),
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...rest }: React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode }) =>
      React.createElement("div", rest, children),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}));

vi.mock("lucide-react", () => ({
  Lightbulb: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "lightbulb-icon", ...props }),
  ArrowRight: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "arrow-right-icon", ...props }),
}));

// Mock Supabase client
vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: "test-token" } },
      }),
    },
  }),
}));

// Mock apiFetch and ApiError
const mockApiFetch = vi.fn();

vi.mock("@/lib/api/client", () => {
  class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
      this.name = "ApiError";
    }
  }
  return {
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
    ApiError,
  };
});

// ── Import after mocks ────────────────────────────────────────────────────────

import { CoachingTips } from "@/components/assessment/coaching-tips";

// ── Helpers ───────────────────────────────────────────────────────────────────

const defaultProps = {
  sessionId: "session-abc",
  competencyId: "communication",
  score: 70,
};

const sampleTips = [
  { title: "Tip 1", description: "Desc 1", action: "Do X" },
  { title: "Tip 2", description: "Desc 2", action: "Do Y" },
];

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("CoachingTips — loading state", () => {
  beforeEach(() => {
    // Never resolves — keeps loading
    mockApiFetch.mockReturnValue(new Promise(() => {}));
  });

  it("renders skeleton with role status while loading", () => {
    render(<CoachingTips {...defaultProps} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows loading label on skeleton", () => {
    render(<CoachingTips {...defaultProps} />);
    // t() returns key, so aria-label will be the key string
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "assessment.coachingLoading");
  });
});

describe("CoachingTips — successful data", () => {
  beforeEach(() => {
    mockApiFetch.mockResolvedValue({ tips: sampleTips });
  });

  it("renders section header after loading", async () => {
    render(<CoachingTips {...defaultProps} />);
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    expect(screen.getByTestId("lightbulb-icon")).toBeInTheDocument();
  });

  it("renders tip titles after loading", async () => {
    render(<CoachingTips {...defaultProps} />);
    await waitFor(() => expect(screen.getByText("Tip 1")).toBeInTheDocument());
    expect(screen.getByText("Tip 2")).toBeInTheDocument();
  });

  it("renders tip descriptions", async () => {
    render(<CoachingTips {...defaultProps} />);
    await waitFor(() => expect(screen.getByText("Desc 1")).toBeInTheDocument());
    expect(screen.getByText("Desc 2")).toBeInTheDocument();
  });

  it("renders tip action text with arrow icon", async () => {
    render(<CoachingTips {...defaultProps} />);
    await waitFor(() => expect(screen.getByText("Do X")).toBeInTheDocument());
    expect(screen.getAllByTestId("arrow-right-icon").length).toBeGreaterThan(0);
  });

  it("renders methodology note when tips exist", async () => {
    mockApiFetch.mockResolvedValue({ tips: sampleTips, methodology_note: "IRT-based" });
    render(<CoachingTips {...defaultProps} />);
    await waitFor(() => expect(screen.getByText("IRT-based")).toBeInTheDocument());
  });
});

describe("CoachingTips — excellent score", () => {
  beforeEach(() => {
    mockApiFetch.mockResolvedValue({ tips: sampleTips });
  });

  it("uses excellent heading key when score >= 85", async () => {
    render(<CoachingTips {...defaultProps} score={90} />);
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    expect(screen.getByText("assessment.coachingExcellent")).toBeInTheDocument();
  });

  it("uses coaching heading key when score < 85", async () => {
    render(<CoachingTips {...defaultProps} score={70} />);
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    expect(screen.getByText("assessment.coaching")).toBeInTheDocument();
  });

  it("hides subtitle paragraph when score >= 85", async () => {
    render(<CoachingTips {...defaultProps} score={85} />);
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    expect(screen.queryByText("assessment.coachingSubtitle")).not.toBeInTheDocument();
  });

  it("shows subtitle paragraph when score < 85", async () => {
    render(<CoachingTips {...defaultProps} score={70} />);
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    expect(screen.getByText("assessment.coachingSubtitle")).toBeInTheDocument();
  });
});

describe("CoachingTips — error state", () => {
  it("shows error message when apiFetch rejects with non-404", async () => {
    mockApiFetch.mockRejectedValue(new Error("Server error"));
    render(<CoachingTips {...defaultProps} />);
    await waitFor(() =>
      expect(screen.getByText("assessment.coachingError")).toBeInTheDocument()
    );
  });

  it("shows empty tips (no error UI) when apiFetch returns 404", async () => {
    const { ApiError } = await import("@/lib/api/client");
    mockApiFetch.mockRejectedValue(new ApiError("not found", 404));
    render(<CoachingTips {...defaultProps} />);
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    expect(screen.queryByText("assessment.coachingError")).not.toBeInTheDocument();
  });
});
