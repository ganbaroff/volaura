import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { McqOptions } from "./mcq-options";

describe("McqOptions", () => {
  const options = [
    { key: "a", text_en: "Active listening and clear articulation", text_az: "Aktiv dinləmə və aydın ifadə" },
    { key: "b", text_en: "Speaking loudly to be heard", text_az: "Eşidilmək üçün ucadan danışmaq" },
    { key: "c", text_en: "Avoiding eye contact to focus", text_az: "Diqqəti cəmləmək üçün göz təmasından qaçmaq" },
    { key: "d", text_en: "Using only written communication", text_az: "Yalnız yazılı ünsiyyətdən istifadə" },
  ];

  it("renders all options with labels A-D", () => {
    render(<McqOptions options={options} selected={null} onSelect={vi.fn()} />);
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("C")).toBeInTheDocument();
    expect(screen.getByText("D")).toBeInTheDocument();
    expect(screen.getByText(options[0].text_en)).toBeInTheDocument();
  });

  it("calls onSelect with option key when clicked", () => {
    const onSelect = vi.fn();
    render(<McqOptions options={options} selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText(options[1].text_en));
    expect(onSelect).toHaveBeenCalledWith("b");
  });

  it("marks selected option with aria-pressed=true", () => {
    render(<McqOptions options={options} selected="c" onSelect={vi.fn()} />);
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

  it("renders Azerbaijani text when locale=az", () => {
    render(<McqOptions options={options} selected={null} onSelect={vi.fn()} locale="az" />);
    expect(screen.getByText(options[0].text_az)).toBeInTheDocument();
  });
});
