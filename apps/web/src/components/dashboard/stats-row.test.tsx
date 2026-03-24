import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@/test/mocks";
import { StatsRow } from "./stats-row";

describe("StatsRow", () => {
  it("renders all 3 stats", () => {
    render(<StatsRow streak={7} eventsCount={12} leaguePosition="8%" />);
    expect(screen.getByText("dashboard.streak")).toBeInTheDocument();
    expect(screen.getByText("dashboard.recentActivity")).toBeInTheDocument();
    expect(screen.getByText("dashboard.league")).toBeInTheDocument();
  });

  it("renders streak value with 'days' suffix", () => {
    render(<StatsRow streak={7} eventsCount={3} leaguePosition={null} />);
    expect(screen.getByText(/7/)).toBeInTheDocument();
  });

  it("renders dash when leaguePosition is null", () => {
    render(<StatsRow streak={1} eventsCount={0} leaguePosition={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders events count", () => {
    render(<StatsRow streak={0} eventsCount={42} leaguePosition={null} />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("has aria-hidden on icons", () => {
    const { container } = render(
      <StatsRow streak={3} eventsCount={5} leaguePosition="12%" />
    );
    const svgs = container.querySelectorAll("svg");
    svgs.forEach(svg => {
      expect(svg.getAttribute("aria-hidden")).toBe("true");
    });
  });
});
