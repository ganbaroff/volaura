import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: "en" } }),
}));

vi.mock("lucide-react", () => ({
  Mic: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "mic-icon", ...props }),
  MicOff: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "mic-off-icon", ...props }),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { OpenTextAnswer } from "@/components/assessment/open-text-answer";

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderAnswer(
  overrides: Partial<React.ComponentProps<typeof OpenTextAnswer>> = {}
) {
  const onChange = vi.fn();
  const defaults = {
    value: "",
    onChange,
    disabled: false,
    maxLength: 1000,
  };
  const utils = render(<OpenTextAnswer {...defaults} {...overrides} />);
  return { ...utils, onChange };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("OpenTextAnswer — textarea rendering", () => {
  it("renders a textarea element", () => {
    renderAnswer();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("shows current value in textarea", () => {
    renderAnswer({ value: "Hello world" });
    expect(screen.getByRole("textbox")).toHaveValue("Hello world");
  });

  it("uses placeholder from props", () => {
    renderAnswer({ placeholder: "Type here..." });
    expect(screen.getByPlaceholderText("Type here...")).toBeInTheDocument();
  });

  it("falls back to i18n key for placeholder", () => {
    renderAnswer();
    expect(screen.getByPlaceholderText("assessment.answerPlaceholder")).toBeInTheDocument();
  });

  it("textarea has aria-label matching placeholder", () => {
    renderAnswer({ placeholder: "My label" });
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveAttribute("aria-label", "My label");
  });

  it("textarea has rows=4 attribute", () => {
    renderAnswer();
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveAttribute("rows", "4");
  });
});

describe("OpenTextAnswer — change handling", () => {
  it("calls onChange when user types", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<OpenTextAnswer value="" onChange={onChange} />);
    await user.type(screen.getByRole("textbox"), "a");
    expect(onChange).toHaveBeenCalled();
  });

  it("calls onChange with the new value on each keystroke", () => {
    const onChange = vi.fn();
    render(<OpenTextAnswer value="Hello" onChange={onChange} />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Hello world" } });
    expect(onChange).toHaveBeenCalledWith("Hello world");
  });
});

describe("OpenTextAnswer — character counter", () => {
  it("displays remaining characters correctly", () => {
    renderAnswer({ value: "Hi", maxLength: 100 });
    expect(screen.getByText("98 / 100")).toBeInTheDocument();
  });

  it("displays full count when value is empty", () => {
    renderAnswer({ value: "", maxLength: 500 });
    expect(screen.getByText("500 / 500")).toBeInTheDocument();
  });

  it("counter has aria-live polite", () => {
    renderAnswer();
    const counter = screen.getByText(/\/ 1000/);
    expect(counter).toHaveAttribute("aria-live", "polite");
  });

  it("counter has aria-atomic true", () => {
    renderAnswer();
    const counter = screen.getByText(/\/ 1000/);
    expect(counter).toHaveAttribute("aria-atomic", "true");
  });

  it("applies destructive class when near limit (<=100 remaining)", () => {
    const longValue = "a".repeat(920);
    renderAnswer({ value: longValue, maxLength: 1000 });
    const counter = screen.getByText(/\/ 1000/);
    expect(counter.className).toContain("text-destructive");
  });

  it("applies muted class when not near limit", () => {
    renderAnswer({ value: "short", maxLength: 1000 });
    const counter = screen.getByText(/\/ 1000/);
    expect(counter.className).toContain("text-muted-foreground");
  });
});

describe("OpenTextAnswer — disabled state", () => {
  it("disables the textarea when disabled=true", () => {
    renderAnswer({ disabled: true });
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("textarea is enabled by default", () => {
    renderAnswer();
    expect(screen.getByRole("textbox")).not.toBeDisabled();
  });

  it("applies disabled styling class on textarea", () => {
    renderAnswer({ disabled: true });
    expect(screen.getByRole("textbox").className).toContain("disabled:opacity-50");
  });
});

describe("OpenTextAnswer — maxLength", () => {
  it("sets maxLength attribute on textarea", () => {
    renderAnswer({ maxLength: 500 });
    expect(screen.getByRole("textbox")).toHaveAttribute("maxLength", "500");
  });

  it("defaults maxLength to 1000", () => {
    renderAnswer();
    expect(screen.getByRole("textbox")).toHaveAttribute("maxLength", "1000");
  });
});

describe("OpenTextAnswer — focus accessibility", () => {
  it("has focus-visible ring class", () => {
    renderAnswer();
    expect(screen.getByRole("textbox").className).toContain("focus-visible:ring-2");
  });
});

describe("OpenTextAnswer — speech recognition (no API available)", () => {
  beforeEach(() => {
    // Ensure SpeechRecognition is NOT available (default jsdom environment)
    Object.defineProperty(window, "SpeechRecognition", {
      value: undefined,
      writable: true,
      configurable: true,
    });
    Object.defineProperty(window, "webkitSpeechRecognition", {
      value: undefined,
      writable: true,
      configurable: true,
    });
  });

  it("does not render mic button when speech recognition is unavailable", () => {
    renderAnswer();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
