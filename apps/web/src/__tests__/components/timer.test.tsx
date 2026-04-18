import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

// framer-motion: render children directly, skip animation complexity
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...rest }: React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode }) =>
      React.createElement("div", rest, children),
    span: ({ children, ...rest }: React.HTMLAttributes<HTMLSpanElement> & { children?: React.ReactNode }) =>
      React.createElement("span", rest, children),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
  useReducedMotion: () => false,
}));

// lucide-react Clock icon
vi.mock("lucide-react", () => ({
  Clock: ({ className, ...props }: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "clock-icon", className, ...props }),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { Timer } from "@/components/assessment/timer";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Timer — initial rendering and formatting", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the timer role element", () => {
    render(<Timer totalSeconds={60} onExpire={vi.fn()} label="Time remaining" />);
    expect(screen.getByRole("timer")).toBeInTheDocument();
  });

  it("formats 90 seconds as 01:30", () => {
    render(<Timer totalSeconds={90} onExpire={vi.fn()} label="Time remaining" />);
    expect(screen.getByText("01:30")).toBeInTheDocument();
  });

  it("formats 60 seconds as 01:00", () => {
    render(<Timer totalSeconds={60} onExpire={vi.fn()} label="Time remaining" />);
    expect(screen.getByText("01:00")).toBeInTheDocument();
  });

  it("formats 5 seconds as 00:05 (zero-padded)", () => {
    render(<Timer totalSeconds={5} onExpire={vi.fn()} label="Time remaining" />);
    expect(screen.getByText("00:05")).toBeInTheDocument();
  });

  it("aria-label includes the label and formatted time", () => {
    render(<Timer totalSeconds={90} onExpire={vi.fn()} label="Time remaining" />);
    expect(screen.getByRole("timer")).toHaveAttribute("aria-label", "Time remaining: 01:30");
  });
});

describe("Timer — countdown behavior", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("decrements by 1 second after 1000ms", () => {
    render(<Timer totalSeconds={10} onExpire={vi.fn()} label="Time" />);
    expect(screen.getByText("00:10")).toBeInTheDocument();

    act(() => { vi.advanceTimersByTime(1000); });
    expect(screen.getByText("00:09")).toBeInTheDocument();
  });

  it("decrements correctly over multiple seconds", () => {
    render(<Timer totalSeconds={10} onExpire={vi.fn()} label="Time" />);

    act(() => { vi.advanceTimersByTime(1000); });
    act(() => { vi.advanceTimersByTime(1000); });
    act(() => { vi.advanceTimersByTime(1000); });
    expect(screen.getByText("00:07")).toBeInTheDocument();
  });

  it("counts down from 65 seconds crossing minute boundary", () => {
    render(<Timer totalSeconds={65} onExpire={vi.fn()} label="Time" />);

    for (let i = 0; i < 6; i++) {
      act(() => { vi.advanceTimersByTime(1000); });
    }
    expect(screen.getByText("00:59")).toBeInTheDocument();
  });

  it("resets countdown when totalSeconds prop changes", () => {
    const { rerender } = render(<Timer totalSeconds={30} onExpire={vi.fn()} label="Time" />);
    for (let i = 0; i < 5; i++) {
      act(() => { vi.advanceTimersByTime(1000); });
    }
    expect(screen.getByText("00:25")).toBeInTheDocument();

    rerender(<Timer totalSeconds={60} onExpire={vi.fn()} label="Time" />);
    expect(screen.getByText("01:00")).toBeInTheDocument();
  });
});

describe("Timer — expiry callback", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("calls onExpire when countdown reaches zero", () => {
    const onExpire = vi.fn();
    render(<Timer totalSeconds={2} onExpire={onExpire} label="Time" />);

    act(() => { vi.advanceTimersByTime(1000); });
    act(() => { vi.advanceTimersByTime(1000); });
    expect(onExpire).toHaveBeenCalledTimes(1);
  });

  it("calls onExpire exactly once, not repeatedly", () => {
    const onExpire = vi.fn();
    render(<Timer totalSeconds={1} onExpire={onExpire} label="Time" />);

    act(() => { vi.advanceTimersByTime(1000); });
    act(() => { vi.advanceTimersByTime(1000); });
    act(() => { vi.advanceTimersByTime(1000); });
    expect(onExpire).toHaveBeenCalledTimes(1);
  });

  it("does not call onExpire before countdown reaches zero", () => {
    const onExpire = vi.fn();
    render(<Timer totalSeconds={10} onExpire={onExpire} label="Time" />);

    for (let i = 0; i < 5; i++) {
      act(() => { vi.advanceTimersByTime(1000); });
    }
    expect(onExpire).not.toHaveBeenCalled();
  });
});

describe("Timer — warning thresholds", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("clock icon has muted-foreground class above warning threshold", () => {
    render(<Timer totalSeconds={30} onExpire={vi.fn()} label="Time" warningThreshold={10} />);
    const icon = screen.getByTestId("clock-icon");
    const cls = icon.getAttribute("class") ?? "";
    expect(cls).toContain("text-muted-foreground");
    expect(cls).not.toContain("text-destructive");
  });

  it("clock icon switches to text-destructive at or below warning threshold", () => {
    render(<Timer totalSeconds={10} onExpire={vi.fn()} label="Time" warningThreshold={10} />);
    const icon = screen.getByTestId("clock-icon");
    expect(icon.getAttribute("class") ?? "").toContain("text-destructive");
  });

  it("uses default warningThreshold of 10 when not specified", () => {
    render(<Timer totalSeconds={10} onExpire={vi.fn()} label="Time" />);
    const icon = screen.getByTestId("clock-icon");
    expect(icon.getAttribute("class") ?? "").toContain("text-destructive");
  });

  it("does not show warning at 11 seconds with default threshold", () => {
    render(<Timer totalSeconds={11} onExpire={vi.fn()} label="Time" />);
    const icon = screen.getByTestId("clock-icon");
    expect(icon.getAttribute("class") ?? "").toContain("text-muted-foreground");
  });
});

describe("Timer — aria-live announcements", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("aria-live is polite at 60 seconds (announcement threshold)", () => {
    render(<Timer totalSeconds={60} onExpire={vi.fn()} label="Time" />);
    // The span with the time string should have aria-live="polite" at t=60
    const spans = document.querySelectorAll("[aria-live]");
    const politeSpan = Array.from(spans).find((el) => el.getAttribute("aria-live") === "polite");
    expect(politeSpan).toBeDefined();
  });

  it("aria-live is polite when remaining <= 5 (critical)", () => {
    render(<Timer totalSeconds={5} onExpire={vi.fn()} label="Time" />);
    const spans = document.querySelectorAll("[aria-live]");
    const politeSpan = Array.from(spans).find((el) => el.getAttribute("aria-live") === "polite");
    expect(politeSpan).toBeDefined();
  });
});
