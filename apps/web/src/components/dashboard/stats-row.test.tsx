import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@/test/mocks";
import { StatsRow } from "./stats-row";

describe("StatsRow", () => {
  it("renders all 3 stats", () => {
    render(<StatsRow streak={7} eventsCount={12} auraTier="Silver" />);
    expect(screen.getByText("dashboard.streak")).toBeInTheDocument();
    expect(screen.getByText("dashboard.recentActivity")).toBeInTheDocument();
    expect(screen.getByText("AURA Tier")).toBeInTheDocument();
  });

  it("renders streak value with 'days' suffix", () => {
    render(<StatsRow streak={7} eventsCount={3} auraTier={null} />);
    expect(screen.getByText(/7/)).toBeInTheDocument();
  });

  it("renders 'coming soon' when auraTier is null", () => {
    render(<StatsRow streak={1} eventsCount={0} auraTier={null} />);
    expect(screen.getByText("stats.comingSoon")).toBeInTheDocument();
  });

  it("renders events count", () => {
    render(<StatsRow streak={0} eventsCount={42} auraTier={null} />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("has aria-hidden on icons", () => {
    const { container } = render(
      <StatsRow streak={3} eventsCount={5} auraTier="Gold" />
    );
    const svgs = container.querySelectorAll("svg");
    svgs.forEach(svg => {
      expect(svg.getAttribute("aria-hidden")).toBe("true");
    });
  });
});
