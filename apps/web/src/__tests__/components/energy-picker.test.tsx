import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: "en" } }),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { EnergyPicker, EnergyLevel } from "@/components/assessment/energy-picker";

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderPicker(
  value: EnergyLevel = "full",
  onChange = vi.fn(),
  variant: "default" | "compact" = "default"
) {
  return render(<EnergyPicker value={value} onChange={onChange} variant={variant} />);
}

/**
 * In the default variant, buttons don't have explicit aria-label —
 * their accessible name is computed from nested child text spans.
 * Use getByRole("radio") and check their text content via getByText().
 */

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("EnergyPicker — default variant rendering", () => {
  it("renders radiogroup with 3 radio buttons", () => {
    renderPicker();
    const group = screen.getByRole("radiogroup");
    expect(group.querySelectorAll("[role='radio']")).toHaveLength(3);
  });

  it("renders all 3 energy level label texts", () => {
    renderPicker();
    expect(screen.getByText("assessment.energyFull")).toBeInTheDocument();
    expect(screen.getByText("assessment.energyMid")).toBeInTheDocument();
    expect(screen.getByText("assessment.energyLow")).toBeInTheDocument();
  });

  it("marks selected value as aria-checked true", () => {
    renderPicker("mid");
    const radios = screen.getAllByRole("radio");
    const midBtn = radios.find((btn) =>
      btn.textContent?.includes("assessment.energyMid")
    );
    expect(midBtn).toHaveAttribute("aria-checked", "true");
  });

  it("marks unselected values as aria-checked false", () => {
    renderPicker("mid");
    const radios = screen.getAllByRole("radio");
    const nonMid = radios.filter((btn) =>
      !btn.textContent?.includes("assessment.energyMid")
    );
    nonMid.forEach((btn) => expect(btn).toHaveAttribute("aria-checked", "false"));
  });

  it("all radio buttons are type=button", () => {
    renderPicker();
    screen.getAllByRole("radio").forEach((btn) => {
      expect(btn).toHaveAttribute("type", "button");
    });
  });
});

describe("EnergyPicker — selection callback", () => {
  it("calls onChange with 'full' when full option clicked", () => {
    const onChange = vi.fn();
    renderPicker("mid", onChange);
    const fullBtn = screen.getAllByRole("radio").find((btn) =>
      btn.textContent?.includes("assessment.energyFull")
    );
    if (fullBtn) fireEvent.click(fullBtn);
    expect(onChange).toHaveBeenCalledWith("full");
  });

  it("calls onChange with 'mid' when mid option clicked", () => {
    const onChange = vi.fn();
    renderPicker("full", onChange);
    const midBtn = screen.getAllByRole("radio").find((btn) =>
      btn.textContent?.includes("assessment.energyMid")
    );
    if (midBtn) fireEvent.click(midBtn);
    expect(onChange).toHaveBeenCalledWith("mid");
  });

  it("calls onChange with 'low' when low option clicked", () => {
    const onChange = vi.fn();
    renderPicker("full", onChange);
    const lowBtn = screen.getAllByRole("radio").find((btn) =>
      btn.textContent?.includes("assessment.energyLow")
    );
    if (lowBtn) fireEvent.click(lowBtn);
    expect(onChange).toHaveBeenCalledWith("low");
  });

  it("calls onChange exactly once per click", () => {
    const onChange = vi.fn();
    renderPicker("full", onChange);
    const lowBtn = screen.getAllByRole("radio").find((btn) =>
      btn.textContent?.includes("assessment.energyLow")
    );
    if (lowBtn) fireEvent.click(lowBtn);
    expect(onChange).toHaveBeenCalledTimes(1);
  });
});

describe("EnergyPicker — compact variant", () => {
  it("renders radiogroup in compact variant", () => {
    renderPicker("full", vi.fn(), "compact");
    expect(screen.getByRole("radiogroup")).toBeInTheDocument();
  });

  it("renders 3 radio buttons in compact variant", () => {
    renderPicker("full", vi.fn(), "compact");
    const group = screen.getByRole("radiogroup");
    expect(group.querySelectorAll("[role='radio']")).toHaveLength(3);
  });

  it("marks selected level as aria-checked true in compact variant", () => {
    renderPicker("low", vi.fn(), "compact");
    const radios = screen.getAllByRole("radio");
    const lowBtn = radios.find((r) => r.getAttribute("aria-label") === "assessment.energyLow");
    expect(lowBtn).toHaveAttribute("aria-checked", "true");
  });

  it("marks non-selected as aria-checked false in compact variant", () => {
    renderPicker("low", vi.fn(), "compact");
    const radios = screen.getAllByRole("radio");
    const nonLow = radios.filter((r) => r.getAttribute("aria-label") !== "assessment.energyLow");
    nonLow.forEach((btn) => expect(btn).toHaveAttribute("aria-checked", "false"));
  });

  it("compact buttons have explicit aria-label", () => {
    renderPicker("full", vi.fn(), "compact");
    screen.getAllByRole("radio").forEach((btn) => {
      expect(btn).toHaveAttribute("aria-label");
    });
  });

  it("calls onChange in compact variant when mid clicked", () => {
    const onChange = vi.fn();
    renderPicker("full", onChange, "compact");
    const midBtn = screen.getAllByRole("radio").find(
      (r) => r.getAttribute("aria-label") === "assessment.energyMid"
    );
    if (midBtn) fireEvent.click(midBtn);
    expect(onChange).toHaveBeenCalledWith("mid");
  });
});

describe("EnergyPicker — accessibility", () => {
  it("radiogroup has accessible aria-label", () => {
    renderPicker();
    expect(screen.getByRole("radiogroup")).toHaveAttribute("aria-label");
  });

  it("emoji spans are aria-hidden in default variant", () => {
    renderPicker();
    const hiddenSpans = document.querySelectorAll("span[aria-hidden='true']");
    expect(hiddenSpans.length).toBeGreaterThan(0);
  });

  it("emoji spans are aria-hidden in compact variant", () => {
    renderPicker("full", vi.fn(), "compact");
    const hiddenSpans = document.querySelectorAll("span[aria-hidden='true']");
    expect(hiddenSpans.length).toBeGreaterThan(0);
  });

  it("selected button has primary border class", () => {
    renderPicker("full");
    const fullBtn = screen.getAllByRole("radio").find((btn) =>
      btn.textContent?.includes("assessment.energyFull")
    );
    expect(fullBtn?.className).toContain("border-primary");
  });

  it("focus-visible ring class on default variant buttons", () => {
    renderPicker();
    screen.getAllByRole("radio").forEach((btn) => {
      expect(btn.className).toContain("focus-visible:ring-2");
    });
  });
});
