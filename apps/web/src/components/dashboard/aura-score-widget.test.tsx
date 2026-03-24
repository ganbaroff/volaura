import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@/test/mocks";
import { AuraScoreWidget } from "./aura-score-widget";

describe("AuraScoreWidget", () => {
  const defaults = {
    score: 78.5,
    badgeTier: "gold" as const,
    isElite: false,
    locale: "en",
  };

  it("renders the badge tier label", () => {
    render(<AuraScoreWidget {...defaults} />);
    expect(screen.getByText("aura.gold")).toBeInTheDocument();
  });

  it("renders a progressbar with correct aria attributes", () => {
    render(<AuraScoreWidget {...defaults} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "79");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("shows elite badge when isElite is true", () => {
    render(<AuraScoreWidget {...defaults} isElite={true} />);
    expect(screen.getByText("aura.elite")).toBeInTheDocument();
  });

  it("does not show elite badge when isElite is false", () => {
    render(<AuraScoreWidget {...defaults} isElite={false} />);
    expect(screen.queryByText("aura.elite")).not.toBeInTheDocument();
  });

  it("links to the AURA detail page", () => {
    render(<AuraScoreWidget {...defaults} locale="az" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/az/aura");
  });

  it("renders platinum tier styling", () => {
    render(<AuraScoreWidget {...defaults} badgeTier="platinum" />);
    expect(screen.getByText("aura.platinum")).toBeInTheDocument();
  });

  it("renders none tier when score is low", () => {
    render(<AuraScoreWidget {...defaults} score={20} badgeTier="none" />);
    expect(screen.getByText("aura.none")).toBeInTheDocument();
  });
});
