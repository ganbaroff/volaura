"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import type { Question } from "@/stores/assessment-store";
import { McqOptions } from "./mcq-options";
import { OpenTextAnswer } from "./open-text-answer";
import { RatingScale } from "./rating-scale";

interface QuestionCardProps {
  question: Question;
  questionIndex: number; // for animation key
  answer: string;
  onAnswerChange: (value: string) => void;
  disabled?: boolean;
}

export function QuestionCard({
  question,
  questionIndex,
  answer,
  onAnswerChange,
  disabled = false,
}: QuestionCardProps) {
  const { t } = useTranslation();
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
            {question.text}
          </p>
          <span
            className="mt-2 inline-block text-xs font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground capitalize"
            aria-label={`${t("assessment.difficulty")}: ${t(`assessment.difficulty_${question.difficulty_level}`, { defaultValue: question.difficulty_level })}`}
          >
            {t(`assessment.difficulty_${question.difficulty_level}`, { defaultValue: question.difficulty_level })}
          </span>
        </div>

        {/* Answer input */}
        <div>
          {question.type === "mcq" && question.options && (
            <McqOptions
              options={question.options}
              selected={answer || null}
              onSelect={onAnswerChange}
              disabled={disabled}
            />
          )}

          {question.type === "open_text" && (
            <OpenTextAnswer
              value={answer}
              onChange={onAnswerChange}
              disabled={disabled}
            />
          )}

          {question.type === "rating_scale" && (
            <RatingScale
              value={answer ? parseInt(answer, 10) : null}
              onChange={(v) => onAnswerChange(String(v))}
              disabled={disabled}
            />
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
