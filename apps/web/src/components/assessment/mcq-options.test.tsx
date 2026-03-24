import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { McqOptions } from "./mcq-options";

describe("McqOptions", () => {
  const options = [
    "Active listening and clear articulation",
    "Speaking loudly to be heard",
    "Avoiding eye contact to focus",
    "Using only written communication",
  ];

  it("renders all options with labels A-D", () => {
    render(<McqOptions options={options} selected={null} onSelect={vi.fn()} />);
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("C")).toBeInTheDocument();
    expect(screen.getByText("D")).toBeInTheDocument();
    expect(screen.getByText(options[0])).toBeInTheDocument();
  });

  it("calls onSelect when option clicked", () => {
    const onSelect = vi.fn();
    render(<McqOptions options={options} selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText(options[1]));
    expect(onSelect).toHaveBeenCalledWith(options[1]);
  });

  it("marks selected option with aria-pressed=true", () => {
    render(<McqOptions options={options} selected={options[2]} onSelect={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons[2]).toHaveAttribute("aria-pressed", "true");
    expect(buttons[0]).toHaveAttribute("aria-pressed", "false");
  });

  it("disables all buttons when disabled=true", () => {
    render(<McqOptions options={options} selected={null} onSelect={vi.fn()} disabled={true} />);
    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it("has group role with aria-label", () => {
    render(<McqOptions options={options} selected={null} onSelect={vi.fn()} />);
    expect(screen.getByRole("group")).toHaveAttribute("aria-label", "Answer options");
  });
});
