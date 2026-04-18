import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: "en" } }),
}));

vi.mock("framer-motion", () => ({
  motion: {
    article: React.forwardRef<
      HTMLElement,
      React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode }
    >(({ children, ...rest }, ref) =>
      React.createElement("article", { ...rest, ref }, children)
    ),
    div: ({ children, ...rest }: React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode }) =>
      React.createElement("div", rest, children),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { AssessmentCard } from "@/components/assessment/assessment-card";

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderCard(overrides: Partial<React.ComponentProps<typeof AssessmentCard>> = {}) {
  const defaults = {
    question: "How do you handle conflict in teams?",
    competencyLabel: "Communication",
    questionNumber: 3,
    approximateTotal: 12,
    energyLevel: "full" as const,
  };
  return render(
    <AssessmentCard {...defaults} {...overrides}>
      <div data-testid="answer-slot">options here</div>
    </AssessmentCard>
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("AssessmentCard — rendering", () => {
  it("renders the question text", () => {
    renderCard();
    expect(screen.getByText("How do you handle conflict in teams?")).toBeInTheDocument();
  });

  it("renders the competency label", () => {
    renderCard();
    expect(screen.getByText("Communication")).toBeInTheDocument();
  });

  it("renders the children slot", () => {
    renderCard();
    expect(screen.getByTestId("answer-slot")).toBeInTheDocument();
  });

  it("renders an article element as the root", () => {
    renderCard();
    expect(screen.getByRole("article")).toBeInTheDocument();
  });
});

describe("AssessmentCard — progress", () => {
  it("renders progressbar role element", () => {
    renderCard();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("sets aria-valuenow to questionNumber", () => {
    renderCard({ questionNumber: 3 });
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "3");
  });

  it("sets aria-valuemin to 1", () => {
    renderCard();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuemin", "1");
  });

  it("sets aria-valuemax to approximateTotal", () => {
    renderCard({ approximateTotal: 12 });
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuemax", "12");
  });
});

describe("AssessmentCard — aria label", () => {
  it("article has aria-label referencing question number", () => {
    renderCard({ questionNumber: 5 });
    const article = screen.getByRole("article");
    expect(article).toHaveAttribute("aria-label");
    // t() returns the key as-is in tests, so we just check the attribute exists
    expect(article.getAttribute("aria-label")).toBeTruthy();
  });
});

describe("AssessmentCard — energy level variant", () => {
  it("applies max-w-md class in low energy mode", () => {
    renderCard({ energyLevel: "low" });
    const article = screen.getByRole("article");
    expect(article.className).toContain("max-w-md");
  });

  it("does not apply max-w-md in full energy mode", () => {
    renderCard({ energyLevel: "full" });
    const article = screen.getByRole("article");
    expect(article.className).not.toContain("max-w-md");
  });

  it("low energy mode uses larger text class on question", () => {
    renderCard({ energyLevel: "low" });
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading.className).toContain("text-xl");
  });

  it("full energy mode uses base text class on question", () => {
    renderCard({ energyLevel: "full" });
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading.className).toContain("text-base");
  });
});

describe("AssessmentCard — progress aria-live", () => {
  it("progress count span has aria-live polite", () => {
    renderCard();
    const spans = document.querySelectorAll("[aria-live='polite']");
    expect(spans.length).toBeGreaterThan(0);
  });
});
