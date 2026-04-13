"use client";

import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

/**
 * Assessment Card — energy-responsive question display
 *
 * Constitution compliance:
 * - Law 3: Shame-free progress. "Question 3 of ~12" not "33% complete"
 * - Law 4: spring damping ≥14, enter animation ≤800ms
 * - Law 5: One primary action (the answer options)
 *
 * ADHD rules:
 * - Floor mechanic <2min: first question loads in <30s
 * - Immediate feedback: selected answer highlights instantly
 * - Clear structure: question + options + progress, nothing else
 */

interface AssessmentCardProps {
  /** Question text */
  question: string;
  /** Competency being assessed */
  competencyLabel: string;
  /** Current question number (1-based) */
  questionNumber: number;
  /** Approximate total (from energy stopping profile) */
  approximateTotal: number;
  /** Energy level affects card density */
  energyLevel?: "full" | "mid" | "low";
  children: React.ReactNode;
}

export function AssessmentCard({
  question,
  competencyLabel,
  questionNumber,
  approximateTotal,
  energyLevel = "full",
  children,
}: AssessmentCardProps) {
  const { t } = useTranslation();

  return (
    <motion.article
      className={cn(
        "mx-auto w-full max-w-lg rounded-2xl border border-border bg-card",
        "energy-p",
        energyLevel === "low" && "max-w-md"
      )}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: "spring",
        damping: 14,
        stiffness: 100,
      }}
      aria-label={t("assessment.questionCard", {
        defaultValue: `Question ${questionNumber}`,
        number: questionNumber,
      })}
    >
      {/* Header: competency + progress (shame-free, Law 3) */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {competencyLabel}
        </span>
        {/* Shame-free progress: approximate, not exact percentage */}
        <span className="text-xs text-muted-foreground" aria-live="polite">
          {t("assessment.progressApprox", {
            defaultValue: "Question {{current}} of ~{{total}}",
            current: questionNumber,
            total: approximateTotal,
          })}
        </span>
      </div>

      {/* Progress bar: subtle, not dominant */}
      <div
        className="h-0.5 w-full rounded-full bg-surface-container-highest mb-5"
        role="progressbar"
        aria-valuenow={questionNumber}
        aria-valuemin={1}
        aria-valuemax={approximateTotal}
      >
        <div
          className="h-full rounded-full bg-primary/40 transition-all"
          style={{
            width: `${Math.min((questionNumber / approximateTotal) * 100, 100)}%`,
            transitionDuration: "var(--duration-normal)",
          }}
        />
      </div>

      {/* Question text */}
      <h2
        className={cn(
          "font-headline font-semibold text-foreground mb-6",
          energyLevel === "low" ? "text-xl leading-relaxed" : "text-base leading-snug"
        )}
      >
        {question}
      </h2>

      {/* Answer options (passed as children — MCQ, rating scale, or open text) */}
      <div className="energy-gap flex flex-col">
        {children}
      </div>
    </motion.article>
  );
}
