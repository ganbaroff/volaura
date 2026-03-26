import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@/test/mocks";

// Mock Recharts — jsdom has no SVG layout engine; recharts throws without this
vi.mock("recharts", () => ({
  RadarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="radar-chart">{children}</div>
  ),
  Radar: () => <div data-testid="radar" />,
  PolarGrid: () => <div data-testid="polar-grid" />,
  PolarAngleAxis: ({ dataKey }: { dataKey: string }) => (
    <div data-testid="polar-angle-axis" data-key={dataKey} />
  ),
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  Tooltip: () => <div data-testid="tooltip" />,
}));

import { AuraRadarChart } from "./radar-chart";

const FULL_SCORES: Record<string, number> = {
  communication: 82,
  reliability: 75,
  english_proficiency: 88,
  leadership: 70,
  event_performance: 65,
  tech_literacy: 90,
  adaptability: 78,
  empathy_safeguarding: 55,
};

const PLATINUM_SCORES: Record<string, number> = {
  communication: 92,
  reliability: 91,
  english_proficiency: 93,
  leadership: 90,
  event_performance: 95,
  tech_literacy: 94,
  adaptability: 91,
  empathy_safeguarding: 90,
};

const BRONZE_SCORES: Record<string, number> = {
  communication: 42,
  reliability: 40,
  english_proficiency: 44,
  leadership: 41,
  event_performance: 43,
  tech_literacy: 45,
  adaptability: 40,
  empathy_safeguarding: 41,
};

describe("AuraRadarChart", () => {
  it("renders without crashing with full 8-competency data", () => {
    const { container } = render(
      <AuraRadarChart competencyScores={FULL_SCORES} />
    );
    expect(container).toBeTruthy();
    expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
  });

  it("renders with partial data (2 of 8 competencies) — no crash", () => {
    const partial = { communication: 80, reliability: 70 };
    const { container } = render(
      <AuraRadarChart competencyScores={partial} />
    );
    expect(container).toBeTruthy();
    expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
  });

  it("renders empty state when scores object is empty", () => {
    const { container } = render(
      <AuraRadarChart competencyScores={{}} />
    );
    expect(container).toBeTruthy();
    // Chart still renders — missing scores default to 0
    expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
  });

  it("has an accessible aria-label on the root element", () => {
    render(<AuraRadarChart competencyScores={FULL_SCORES} />);
    // The outermost motion.div receives aria-label="aura.competencyRadar" (i18n key returned as-is)
    expect(
      document.querySelector("[aria-label='aura.competencyRadar']")
    ).toBeTruthy();
  });

  it("renders with platinum tier (badgeTier='platinum')", () => {
    const { container } = render(
      <AuraRadarChart competencyScores={PLATINUM_SCORES} badgeTier="platinum" />
    );
    expect(container).toBeTruthy();
    expect(screen.getByTestId("radar")).toBeInTheDocument();
  });

  it("renders with bronze tier (badgeTier='bronze')", () => {
    const { container } = render(
      <AuraRadarChart competencyScores={BRONZE_SCORES} badgeTier="bronze" />
    );
    expect(container).toBeTruthy();
    expect(screen.getByTestId("radar")).toBeInTheDocument();
  });

  it("renders with size='sm'", () => {
    const { container } = render(
      <AuraRadarChart competencyScores={FULL_SCORES} size="sm" />
    );
    expect(container).toBeTruthy();
  });

  it("renders with size='lg'", () => {
    const { container } = render(
      <AuraRadarChart competencyScores={FULL_SCORES} size="lg" />
    );
    expect(container).toBeTruthy();
  });

  it("renders PolarAngleAxis with subject as dataKey", () => {
    render(<AuraRadarChart competencyScores={FULL_SCORES} />);
    const axis = screen.getByTestId("polar-angle-axis");
    expect(axis).toHaveAttribute("data-key", "subject");
  });
});
