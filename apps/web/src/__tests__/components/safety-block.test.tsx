import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: "en" } }),
}));

vi.mock("lucide-react", () => ({
  HeartHandshake: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "heart-icon", ...props }),
  Pause: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "pause-icon", ...props }),
  Sparkle: (props: React.SVGProps<SVGSVGElement>) =>
    React.createElement("svg", { "data-testid": "sparkle-icon", ...props }),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { SafetyBlock } from "@/components/assessment/safety-block";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("SafetyBlock — structure", () => {
  it("renders element with role=note", () => {
    render(<SafetyBlock />);
    expect(screen.getByRole("note")).toBeInTheDocument();
  });

  it("note is labelled by safety-block-title element", () => {
    render(<SafetyBlock />);
    const note = screen.getByRole("note");
    expect(note).toHaveAttribute("aria-labelledby", "safety-block-title");
  });

  it("title element has correct id", () => {
    render(<SafetyBlock />);
    expect(document.getElementById("safety-block-title")).toBeInTheDocument();
  });

  it("renders 'before you start' title", () => {
    render(<SafetyBlock />);
    expect(screen.getByText("assessment.beforeYouStartTitle")).toBeInTheDocument();
  });
});

describe("SafetyBlock — psychotype section", () => {
  it("renders sparkle icon", () => {
    render(<SafetyBlock />);
    expect(screen.getByTestId("sparkle-icon")).toBeInTheDocument();
  });

  it("renders psychotype hint title", () => {
    render(<SafetyBlock />);
    expect(screen.getByText("assessment.psychotypeHintTitle")).toBeInTheDocument();
  });

  it("renders psychotype hint description", () => {
    render(<SafetyBlock />);
    expect(screen.getByText("assessment.psychotypeHint")).toBeInTheDocument();
  });
});

describe("SafetyBlock — pause section", () => {
  it("renders pause icon", () => {
    render(<SafetyBlock />);
    expect(screen.getByTestId("pause-icon")).toBeInTheDocument();
  });

  it("renders pause anytime title", () => {
    render(<SafetyBlock />);
    expect(screen.getByText("assessment.pauseAnytimeTitle")).toBeInTheDocument();
  });

  it("renders pause anytime description", () => {
    render(<SafetyBlock />);
    expect(screen.getByText("assessment.pauseAnytime")).toBeInTheDocument();
  });
});

describe("SafetyBlock — confidentiality section", () => {
  it("renders heart handshake icon", () => {
    render(<SafetyBlock />);
    expect(screen.getByTestId("heart-icon")).toBeInTheDocument();
  });

  it("renders safety note title", () => {
    render(<SafetyBlock />);
    expect(screen.getByText("assessment.safetyNoteTitle")).toBeInTheDocument();
  });

  it("renders safety note description", () => {
    render(<SafetyBlock />);
    expect(screen.getByText("assessment.safetyNote")).toBeInTheDocument();
  });
});

describe("SafetyBlock — icons accessibility", () => {
  it("all icons are aria-hidden", () => {
    render(<SafetyBlock />);
    ["sparkle-icon", "pause-icon", "heart-icon"].forEach((id) => {
      expect(screen.getByTestId(id)).toHaveAttribute("aria-hidden", "true");
    });
  });
});

describe("SafetyBlock — content count", () => {
  it("renders exactly 3 safety items", () => {
    render(<SafetyBlock />);
    // Each item has a title + description pair; we verify 3 icons as proxy
    expect(document.querySelectorAll("[data-testid$='-icon']")).toHaveLength(3);
  });
});
