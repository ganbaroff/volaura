import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: "en" } }),
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...rest }: React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode }) =>
      React.createElement("div", rest, children),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}));

// Mock McqOptions — controlled sub-component
vi.mock("@/components/assessment/mcq-options", () => ({
  McqOptions: ({
    options,
    selected,
    onSelect,
    disabled,
  }: {
    options: Array<{ key: string; text_en: string; text_az: string }>;
    selected: string | null;
    onSelect: (key: string) => void;
    disabled?: boolean;
    locale: string;
  }) =>
    React.createElement(
      "div",
      { "data-testid": "mcq-options" },
      options.map((o) =>
        React.createElement(
          "button",
          {
            key: o.key,
            "data-testid": `mcq-option-${o.key}`,
            "aria-pressed": selected === o.key,
            disabled,
            onClick: () => onSelect(o.key),
          },
          o.text_en
        )
      )
    ),
}));

// Mock OpenTextAnswer — controlled sub-component
vi.mock("@/components/assessment/open-text-answer", () => ({
  OpenTextAnswer: ({
    value,
    onChange,
    disabled,
  }: {
    value: string;
    onChange: (v: string) => void;
    disabled?: boolean;
  }) =>
    React.createElement("textarea", {
      "data-testid": "open-text-answer",
      value,
      disabled,
      onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value),
      "aria-label": "open text answer",
    }),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { QuestionCard } from "@/components/assessment/question-card";
import type { Question } from "@/stores/assessment-store";

// ── Fixtures ──────────────────────────────────────────────────────────────────

const mcqQuestion: Question = {
  id: "q-1",
  question_type: "mcq",
  question_en: "Which approach do you prefer?",
  question_az: "Hansı yanaşmanı üstün tutursunuz?",
  options: [
    { key: "a", text_en: "Option A", text_az: "Seçim A" },
    { key: "b", text_en: "Option B", text_az: "Seçim B" },
  ],
  competency_id: "communication",
};

const openEndedQuestion: Question = {
  id: "q-2",
  question_type: "open_ended",
  question_en: "Describe your leadership style.",
  question_az: "Liderlik tərзinizi təsvir edin.",
  options: null,
  competency_id: "leadership",
};

const sjtQuestion: Question = {
  id: "q-3",
  question_type: "sjt",
  question_en: "What would you do in this situation?",
  question_az: "Bu vəziyyətdə nə edərdiniz?",
  options: null,
  competency_id: "adaptability",
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("QuestionCard — MCQ rendering", () => {
  it("renders question text", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach do you prefer?"
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByText("Which approach do you prefer?")).toBeInTheDocument();
  });

  it("renders MCQ options component", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach do you prefer?"
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByTestId("mcq-options")).toBeInTheDocument();
  });

  it("renders multiple choice type badge", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach do you prefer?"
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByText("assessment.typeMultipleChoice")).toBeInTheDocument();
  });

  it("does not render open text answer for MCQ", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach do you prefer?"
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.queryByTestId("open-text-answer")).not.toBeInTheDocument();
  });
});

describe("QuestionCard — open_ended rendering", () => {
  it("renders open text answer component", () => {
    render(
      <QuestionCard
        question={openEndedQuestion}
        questionText="Describe your leadership style."
        questionIndex={1}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByTestId("open-text-answer")).toBeInTheDocument();
  });

  it("renders open response type badge", () => {
    render(
      <QuestionCard
        question={openEndedQuestion}
        questionText="Describe your leadership style."
        questionIndex={1}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByText("assessment.typeOpenEnded")).toBeInTheDocument();
  });

  it("does not render MCQ options for open_ended", () => {
    render(
      <QuestionCard
        question={openEndedQuestion}
        questionText="Describe your leadership style."
        questionIndex={1}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.queryByTestId("mcq-options")).not.toBeInTheDocument();
  });
});

describe("QuestionCard — SJT rendering", () => {
  it("renders open text answer for SJT type", () => {
    render(
      <QuestionCard
        question={sjtQuestion}
        questionText="What would you do in this situation?"
        questionIndex={2}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByTestId("open-text-answer")).toBeInTheDocument();
  });

  it("renders SJT type badge", () => {
    render(
      <QuestionCard
        question={sjtQuestion}
        questionText="What would you do in this situation?"
        questionIndex={2}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByText("assessment.typeSJT")).toBeInTheDocument();
  });
});

describe("QuestionCard — accessibility", () => {
  it("wrapper has role=form", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach?"
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByRole("form")).toBeInTheDocument();
  });

  it("form has aria-label with question index", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach?"
        questionIndex={2}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    const form = screen.getByRole("form");
    expect(form).toHaveAttribute("aria-label");
    expect(form.getAttribute("aria-label")).toContain("3"); // questionIndex + 1
  });

  it("wrapper has aria-live=polite", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach?"
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByRole("form")).toHaveAttribute("aria-live", "polite");
  });

  it("wrapper has aria-atomic=true", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach?"
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
      />
    );
    expect(screen.getByRole("form")).toHaveAttribute("aria-atomic", "true");
  });
});

describe("QuestionCard — disabled prop", () => {
  it("passes disabled to MCQ options", () => {
    render(
      <QuestionCard
        question={mcqQuestion}
        questionText="Which approach?"
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
        disabled={true}
      />
    );
    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it("passes disabled to open text answer", () => {
    render(
      <QuestionCard
        question={openEndedQuestion}
        questionText="Describe style."
        questionIndex={0}
        answer=""
        onAnswerChange={vi.fn()}
        disabled={true}
      />
    );
    expect(screen.getByTestId("open-text-answer")).toBeDisabled();
  });
});
