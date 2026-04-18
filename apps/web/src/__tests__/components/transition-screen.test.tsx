import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...rest }: React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode }) =>
      React.createElement("div", rest, children),
    p: ({ children, ...rest }: React.HTMLAttributes<HTMLParagraphElement> & { children?: React.ReactNode }) =>
      React.createElement("p", rest, children),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}));

vi.mock("lucide-react", () => ({
  CheckCircle2: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "check-icon", ...props }),
  ArrowRight: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "arrow-right-icon", ...props }),
}));

// Mock Button — pass-through rendering
vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    onClick,
    size,
    className,
    ...rest
  }: React.ButtonHTMLAttributes<HTMLButtonElement> & {
    size?: string;
    children?: React.ReactNode;
  }) =>
    React.createElement(
      "button",
      { onClick, className, "data-size": size, ...rest },
      children
    ),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { TransitionScreen } from "@/components/assessment/transition-screen";

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderScreen(
  overrides: Partial<React.ComponentProps<typeof TransitionScreen>> = {}
) {
  const onContinue = vi.fn();
  const defaults = {
    completedLabel: "Communication complete ✓",
    continueLabel: "Continue to Leadership",
    onContinue,
  };
  const utils = render(<TransitionScreen {...defaults} {...overrides} />);
  return { ...utils, onContinue };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("TransitionScreen — rendering", () => {
  it("renders the completedLabel text", () => {
    renderScreen();
    expect(screen.getByText("Communication complete ✓")).toBeInTheDocument();
  });

  it("renders the continueLabel text inside the button", () => {
    renderScreen();
    expect(screen.getByRole("button", { name: /Continue to Leadership/ })).toBeInTheDocument();
  });

  it("renders check icon", () => {
    renderScreen();
    expect(screen.getByTestId("check-icon")).toBeInTheDocument();
  });

  it("renders arrow right icon inside continue button", () => {
    renderScreen();
    expect(screen.getByTestId("arrow-right-icon")).toBeInTheDocument();
  });
});

describe("TransitionScreen — accessibility", () => {
  it("root element has role=status", () => {
    renderScreen();
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("root element has aria-live=polite", () => {
    renderScreen();
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
  });

  it("check icon is aria-hidden", () => {
    renderScreen();
    expect(screen.getByTestId("check-icon")).toHaveAttribute("aria-hidden", "true");
  });

  it("arrow right icon is aria-hidden", () => {
    renderScreen();
    expect(screen.getByTestId("arrow-right-icon")).toHaveAttribute("aria-hidden", "true");
  });
});

describe("TransitionScreen — continue button interaction", () => {
  it("calls onContinue when button is clicked", () => {
    const { onContinue } = renderScreen();
    fireEvent.click(screen.getByRole("button", { name: /Continue to Leadership/ }));
    expect(onContinue).toHaveBeenCalledTimes(1);
  });

  it("does not call onContinue before click", () => {
    const { onContinue } = renderScreen();
    expect(onContinue).not.toHaveBeenCalled();
  });

  it("calls onContinue multiple times on multiple clicks", () => {
    const { onContinue } = renderScreen();
    fireEvent.click(screen.getByRole("button", { name: /Continue to Leadership/ }));
    fireEvent.click(screen.getByRole("button", { name: /Continue to Leadership/ }));
    expect(onContinue).toHaveBeenCalledTimes(2);
  });
});

describe("TransitionScreen — competency name display", () => {
  it("renders custom completedLabel with competency name", () => {
    renderScreen({ completedLabel: "Leadership complete ✓" });
    expect(screen.getByText("Leadership complete ✓")).toBeInTheDocument();
  });

  it("renders custom continueLabel with next competency name", () => {
    renderScreen({ continueLabel: "Continue to Adaptability" });
    expect(
      screen.getByRole("button", { name: /Continue to Adaptability/ })
    ).toBeInTheDocument();
  });

  it("renders correctly for last competency transition", () => {
    renderScreen({
      completedLabel: "All competencies done!",
      continueLabel: "View your results",
    });
    expect(screen.getByText("All competencies done!")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /View your results/ })).toBeInTheDocument();
  });
});
