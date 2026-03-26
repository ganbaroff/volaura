"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import type { Question } from "@/stores/assessment-store";
import { McqOptions } from "./mcq-options";
import { OpenTextAnswer } from "./open-text-answer";

interface QuestionCardProps {
  question: Question;
  questionText: string; // locale-aware text (question_en or question_az)
  questionIndex: number; // for animation key
  answer: string;
  onAnswerChange: (value: string) => void;
  disabled?: boolean;
}

export function QuestionCard({
  question,
  questionText,
  questionIndex,
  answer,
  onAnswerChange,
  disabled = false,
}: QuestionCardProps) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language;

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={question.id}
        initial={{ opacity: 0, x: 60 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -60 }}
        transition={{ duration: 0.25, ease: "easeInOut" }}
        aria-live="polite"
        aria-atomic="true"
        role="form"
        aria-label={`${t("assessment.question")} ${questionIndex + 1}`}
        className="space-y-6"
      >
        {/* Question text */}
        <div className="rounded-2xl bg-card border border-border p-5">
          <p className="text-base font-medium text-foreground leading-relaxed">
            {questionText}
          </p>
          <span
            className="mt-2 inline-block text-xs font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground capitalize"
          >
            {question.question_type === "mcq"
              ? t("assessment.typeMultipleChoice", { defaultValue: "Multiple Choice" })
              : question.question_type === "sjt"
              ? t("assessment.typeSJT", { defaultValue: "Situational Judgment" })
              : t("assessment.typeOpenEnded", { defaultValue: "Open Response" })}
          </span>
        </div>

        {/* Answer input */}
        <div>
          {question.question_type === "mcq" && question.options && (
            <McqOptions
              options={question.options}
              selected={answer || null}
              onSelect={onAnswerChange}
              disabled={disabled}
              locale={locale}
            />
          )}

          {(question.question_type === "open_ended" || question.question_type === "sjt") && (
            <OpenTextAnswer
              value={answer}
              onChange={onAnswerChange}
              disabled={disabled}
            />
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
