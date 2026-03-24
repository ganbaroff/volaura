import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CompetencyCard } from "./competency-card";

describe("CompetencyCard", () => {
  const baseProps = {
    id: "communication",
    label: "Communication",
    description: "Verbal and written communication skills",
    estimatedMinutes: 5,
    estimatedLabel: "~5 min",
    isSelected: false,
    onToggle: vi.fn(),
  };

  it("renders label and description", () => {
    render(<CompetencyCard {...baseProps} />);
    expect(screen.getByText("Communication")).toBeInTheDocument();
    expect(screen.getByText("Verbal and written communication skills")).toBeInTheDocument();
    expect(screen.getByText("~5 min")).toBeInTheDocument();
  });

  it("calls onToggle with id when clicked", () => {
    const onToggle = vi.fn();
    render(<CompetencyCard {...baseProps} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onToggle).toHaveBeenCalledWith("communication");
  });

  it("has aria-pressed=true when selected", () => {
    render(<CompetencyCard {...baseProps} isSelected={true} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });

  it("has aria-pressed=false when not selected", () => {
    render(<CompetencyCard {...baseProps} isSelected={false} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "false");
  });

  it("renders without description", () => {
    render(<CompetencyCard {...baseProps} description={undefined} />);
    expect(screen.getByText("Communication")).toBeInTheDocument();
    expect(screen.queryByText("Verbal and written communication skills")).not.toBeInTheDocument();
  });
});
