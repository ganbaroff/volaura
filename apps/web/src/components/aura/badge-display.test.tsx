import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@/test/mocks";
import { BadgeDisplay } from "./badge-display";

describe("BadgeDisplay", () => {
  it("renders Platinum badge with correct label", () => {
    render(<BadgeDisplay tier="platinum" label="Platinum" />);
    expect(screen.getByText("Platinum")).toBeInTheDocument();
  });

  it("renders Gold badge with correct label", () => {
    render(<BadgeDisplay tier="gold" label="Gold" />);
    expect(screen.getByText("Gold")).toBeInTheDocument();
  });

  it("renders Silver badge with correct label", () => {
    render(<BadgeDisplay tier="silver" label="Silver" />);
    expect(screen.getByText("Silver")).toBeInTheDocument();
  });

  it("renders Bronze badge with correct label", () => {
    render(<BadgeDisplay tier="bronze" label="Bronze" />);
    expect(screen.getByText("Bronze")).toBeInTheDocument();
  });

  it("renders 'none' tier with em dash character", () => {
    render(<BadgeDisplay tier="none" label="None" />);
    // The badge circle shows "—" for tier=none
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("shows first letter of tier as badge character for platinum", () => {
    render(<BadgeDisplay tier="platinum" label="Platinum" />);
    expect(screen.getByText("P")).toBeInTheDocument();
  });

  it("shows first letter of tier as badge character for gold", () => {
    render(<BadgeDisplay tier="gold" label="Gold" />);
    expect(screen.getByText("G")).toBeInTheDocument();
  });

  it("shows first letter of tier as badge character for silver", () => {
    render(<BadgeDisplay tier="silver" label="Silver" />);
    expect(screen.getByText("S")).toBeInTheDocument();
  });

  it("shows first letter of tier as badge character for bronze", () => {
    render(<BadgeDisplay tier="bronze" label="Bronze" />);
    expect(screen.getByText("B")).toBeInTheDocument();
  });

  it("badge circle has role=img with accessible label", () => {
    render(<BadgeDisplay tier="gold" label="Gold" />);
    const badge = screen.getByRole("img");
    expect(badge).toHaveAttribute("aria-label", "Gold badge");
  });

  it("accessible label uses the provided label prop", () => {
    render(<BadgeDisplay tier="platinum" label="Platinum" />);
    const badge = screen.getByRole("img");
    expect(badge).toHaveAttribute("aria-label", "Platinum badge");
  });

  it("renders elite label when isElite=true and eliteLabel is provided", () => {
    render(
      <BadgeDisplay
        tier="platinum"
        label="Platinum"
        isElite={true}
        eliteLabel="Elite"
      />
    );
    expect(screen.getByText("· Elite")).toBeInTheDocument();
  });

  it("does not render elite label when isElite=false", () => {
    render(
      <BadgeDisplay
        tier="gold"
        label="Gold"
        isElite={false}
        eliteLabel="Elite"
      />
    );
    expect(screen.queryByText("· Elite")).not.toBeInTheDocument();
  });

  it("does not render elite label when eliteLabel is not provided", () => {
    render(<BadgeDisplay tier="platinum" label="Platinum" isElite={true} />);
    expect(screen.queryByText("· Elite")).not.toBeInTheDocument();
  });
});
