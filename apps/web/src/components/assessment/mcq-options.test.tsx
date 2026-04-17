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

  it("marks selected option with aria-checked=true", () => {
    render(<McqOptions options={options} selected="c" onSelect={vi.fn()} />);
    const radios = screen.getAllByRole("radio");
    expect(radios[2]).toHaveAttribute("aria-checked", "true");
    expect(radios[0]).toHaveAttribute("aria-checked", "false");
  });

  it("disables all buttons when disabled=true", () => {
    render(<McqOptions options={options} selected={null} onSelect={vi.fn()} disabled={true} />);
    const radios = screen.getAllByRole("radio");
    radios.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it("has radiogroup role with aria-label", () => {
    render(<McqOptions options={options} selected={null} onSelect={vi.fn()} />);
    expect(screen.getByRole("radiogroup")).toHaveAttribute("aria-label", "Answer options");
  });

  it("renders Azerbaijani text when locale=az", () => {
    render(<McqOptions options={options} selected={null} onSelect={vi.fn()} locale="az" />);
    expect(screen.getByText(options[0].text_az)).toBeInTheDocument();
  });
});
