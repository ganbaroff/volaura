import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// ── Import (no mocks needed — no i18n, no motion) ─────────────────────────────

import { RatingScale } from "@/components/assessment/rating-scale";

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderScale(
  overrides: Partial<React.ComponentProps<typeof RatingScale>> = {}
) {
  const onChange = vi.fn();
  const defaults = {
    value: null,
    onChange,
  };
  const utils = render(<RatingScale {...defaults} {...overrides} />);
  return { ...utils, onChange };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("RatingScale — rendering", () => {
  it("renders a radiogroup element", () => {
    renderScale();
    expect(screen.getByRole("radiogroup")).toBeInTheDocument();
  });

  it("renders 5 radio buttons by default (1–5)", () => {
    renderScale();
    expect(screen.getAllByRole("radio")).toHaveLength(5);
  });

  it("renders buttons labelled 1 through 5", () => {
    renderScale();
    for (let i = 1; i <= 5; i++) {
      expect(screen.getByRole("radio", { name: `Rating ${i}` })).toBeInTheDocument();
    }
  });

  it("renders correct count for custom min/max range", () => {
    renderScale({ min: 0, max: 10 });
    expect(screen.getAllByRole("radio")).toHaveLength(11);
  });

  it("renders numeric label inside each button", () => {
    renderScale();
    for (let i = 1; i <= 5; i++) {
      expect(screen.getByText(String(i))).toBeInTheDocument();
    }
  });
});

describe("RatingScale — selection state", () => {
  it("marks selected value as aria-checked true", () => {
    renderScale({ value: 3 });
    expect(screen.getByRole("radio", { name: "Rating 3" })).toHaveAttribute(
      "aria-checked",
      "true"
    );
  });

  it("marks unselected buttons as aria-checked false", () => {
    renderScale({ value: 3 });
    [1, 2, 4, 5].forEach((n) => {
      expect(screen.getByRole("radio", { name: `Rating ${n}` })).toHaveAttribute(
        "aria-checked",
        "false"
      );
    });
  });

  it("all buttons are aria-checked false when value is null", () => {
    renderScale({ value: null });
    screen.getAllByRole("radio").forEach((btn) => {
      expect(btn).toHaveAttribute("aria-checked", "false");
    });
  });
});

describe("RatingScale — selection callback", () => {
  it("calls onChange with the clicked rating value", () => {
    const { onChange } = renderScale();
    fireEvent.click(screen.getByRole("radio", { name: "Rating 4" }));
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it("calls onChange with 1 when first button clicked", () => {
    const { onChange } = renderScale();
    fireEvent.click(screen.getByRole("radio", { name: "Rating 1" }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("calls onChange with 5 when last button clicked", () => {
    const { onChange } = renderScale();
    fireEvent.click(screen.getByRole("radio", { name: "Rating 5" }));
    expect(onChange).toHaveBeenCalledWith(5);
  });

  it("calls onChange exactly once per click", () => {
    const { onChange } = renderScale();
    fireEvent.click(screen.getByRole("radio", { name: "Rating 2" }));
    expect(onChange).toHaveBeenCalledTimes(1);
  });
});

describe("RatingScale — disabled state", () => {
  it("disables all buttons when disabled=true", () => {
    renderScale({ disabled: true });
    screen.getAllByRole("radio").forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it("does not call onChange when disabled button is clicked", () => {
    const { onChange } = renderScale({ disabled: true });
    fireEvent.click(screen.getByRole("radio", { name: "Rating 3" }));
    expect(onChange).not.toHaveBeenCalled();
  });
});

describe("RatingScale — labels", () => {
  it("renders minLabel text when provided", () => {
    renderScale({ minLabel: "Not at all", maxLabel: "Completely" });
    expect(screen.getByText("Not at all")).toBeInTheDocument();
  });

  it("renders maxLabel text when provided", () => {
    renderScale({ minLabel: "Not at all", maxLabel: "Completely" });
    expect(screen.getByText("Completely")).toBeInTheDocument();
  });

  it("does not render label row when neither label is provided", () => {
    renderScale();
    expect(screen.queryByText("Not at all")).not.toBeInTheDocument();
    expect(screen.queryByText("Completely")).not.toBeInTheDocument();
  });

  it("renders label row when only minLabel is provided", () => {
    renderScale({ minLabel: "Low" });
    expect(screen.getByText("Low")).toBeInTheDocument();
  });
});

describe("RatingScale — accessibility", () => {
  it("radiogroup has aria-label 'Rating scale'", () => {
    renderScale();
    expect(screen.getByRole("radiogroup")).toHaveAttribute("aria-label", "Rating scale");
  });

  it("each radio has aria-label 'Rating N'", () => {
    renderScale();
    screen.getAllByRole("radio").forEach((btn, i) => {
      expect(btn).toHaveAttribute("aria-label", `Rating ${i + 1}`);
    });
  });

  it("selected button has scale-105 applied", () => {
    renderScale({ value: 2 });
    const selected = screen.getByRole("radio", { name: "Rating 2" });
    expect(selected.className).toContain("scale-105");
  });

  it("focus-visible ring class is present on buttons", () => {
    renderScale();
    screen.getAllByRole("radio").forEach((btn) => {
      expect(btn.className).toContain("focus-visible:ring-2");
    });
  });
});
