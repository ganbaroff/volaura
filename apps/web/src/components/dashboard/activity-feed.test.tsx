import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@/test/mocks";
import { ActivityFeed, type ActivityItem } from "./activity-feed";

const makeItem = (
  id: string,
  type: ActivityItem["type"],
  text: string,
  timeAgo = "2h ago"
): ActivityItem => ({ id, type, text, timeAgo });

const sampleItems: ActivityItem[] = [
  makeItem("1", "aura_update", "Your AURA score was updated to 78.5"),
  makeItem("2", "org_view", "TechCorp viewed your profile"),
  makeItem("3", "event", "You registered for CIS Games Volunteer Day"),
];

describe("ActivityFeed", () => {
  it("renders empty state when items array is empty", () => {
    render(<ActivityFeed items={[]} locale="en" />);
    expect(screen.getByText("dashboard.activityEmpty")).toBeInTheDocument();
  });

  it("renders a list of activity items", () => {
    render(<ActivityFeed items={sampleItems} locale="en" />);
    expect(screen.getByText("Your AURA score was updated to 78.5")).toBeInTheDocument();
    expect(screen.getByText("TechCorp viewed your profile")).toBeInTheDocument();
    expect(screen.getByText("You registered for CIS Games Volunteer Day")).toBeInTheDocument();
  });

  it("renders each item's timeAgo value", () => {
    const items: ActivityItem[] = [
      makeItem("1", "aura_update", "AURA updated", "3h ago"),
      makeItem("2", "org_view", "Org viewed", "1d ago"),
    ];
    render(<ActivityFeed items={items} locale="en" />);
    expect(screen.getByText("3h ago")).toBeInTheDocument();
    expect(screen.getByText("1d ago")).toBeInTheDocument();
  });

  it("renders aura_update activity item correctly", () => {
    const items: ActivityItem[] = [
      makeItem("1", "aura_update", "AURA score updated"),
    ];
    render(<ActivityFeed items={items} locale="en" />);
    expect(screen.getByText("AURA score updated")).toBeInTheDocument();
  });

  it("renders org_view activity item correctly", () => {
    const items: ActivityItem[] = [
      makeItem("2", "org_view", "TechCorp viewed your profile"),
    ];
    render(<ActivityFeed items={items} locale="en" />);
    expect(screen.getByText("TechCorp viewed your profile")).toBeInTheDocument();
  });

  it("renders event activity item correctly", () => {
    const items: ActivityItem[] = [
      makeItem("3", "event", "Registered for volunteer day"),
    ];
    render(<ActivityFeed items={items} locale="en" />);
    expect(screen.getByText("Registered for volunteer day")).toBeInTheDocument();
  });

  it("renders the correct number of items (up to 5)", () => {
    const manyItems: ActivityItem[] = Array.from({ length: 7 }, (_, i) =>
      makeItem(String(i), "aura_update", `Activity ${i}`)
    );
    render(<ActivityFeed items={manyItems} locale="en" />);
    // Only 5 are shown (slice(0, 5))
    for (let i = 0; i < 5; i++) {
      expect(screen.getByText(`Activity ${i}`)).toBeInTheDocument();
    }
    // Items 5 and 6 are not rendered
    expect(screen.queryByText("Activity 5")).not.toBeInTheDocument();
    expect(screen.queryByText("Activity 6")).not.toBeInTheDocument();
  });

  it("shows 'view all' link when more than 5 items", () => {
    const manyItems: ActivityItem[] = Array.from({ length: 6 }, (_, i) =>
      makeItem(String(i), "org_view", `View ${i}`)
    );
    render(<ActivityFeed items={manyItems} locale="en" />);
    expect(screen.getByText("common.viewAll")).toBeInTheDocument();
  });

  it("does not show 'view all' link when 5 or fewer items", () => {
    render(<ActivityFeed items={sampleItems} locale="en" />);
    expect(screen.queryByText("common.viewAll")).not.toBeInTheDocument();
  });

  it("'view all' link uses correct locale in href", () => {
    const manyItems: ActivityItem[] = Array.from({ length: 6 }, (_, i) =>
      makeItem(String(i), "event", `Event ${i}`)
    );
    render(<ActivityFeed items={manyItems} locale="az" />);
    const link = screen.getByText("common.viewAll").closest("a");
    expect(link).toHaveAttribute("href", "/az/profile");
  });

  it("renders loading skeletons when loading=true", () => {
    const { container } = render(
      <ActivityFeed items={[]} loading={true} locale="en" />
    );
    expect(screen.queryByText("dashboard.activityEmpty")).not.toBeInTheDocument();
    // Each skeleton row has a flex container
    const rows = container.querySelectorAll(".flex.items-center.gap-3");
    expect(rows.length).toBe(3);
  });

  it("icons have aria-hidden=true", () => {
    render(<ActivityFeed items={sampleItems} locale="en" />);
    const icons = document.querySelectorAll("[aria-hidden='true']");
    expect(icons.length).toBeGreaterThan(0);
  });
});
