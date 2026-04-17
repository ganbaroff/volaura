"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, ArrowLeft, Clock } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { useQuestionBreakdown } from "@/hooks/queries/use-assessment";
import type { QuestionResult } from "@/hooks/queries/use-assessment";
import { ApiError } from "@/lib/api/client";
import { useEnergyMode } from "@/hooks/use-energy-mode";

// ── Difficulty badge ────────────────────────────────────────────────────

const DIFFICULTY_COLORS: Record<string, string> = {
  easy:   "bg-green-500/15 text-green-400 ring-green-500/25",
  medium: "bg-amber-500/15 text-amber-400 ring-amber-500/25",
  hard:   "bg-orange-500/15 text-orange-400 ring-orange-500/25",
  expert: "bg-purple-500/15 text-purple-400 ring-purple-500/25",
};

function DifficultyBadge({ label }: { label: string }) {
  const { t } = useTranslation();
  const normalized = label.toLowerCase();
  const colorClass = DIFFICULTY_COLORS[normalized] ?? DIFFICULTY_COLORS.medium;
  const i18nKey = `assessment.difficulty_${normalized}`;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1",
        colorClass,
      )}
    >
      {t(i18nKey, { defaultValue: label })}
    </span>
  );
}

// ── Single question row ─────────────────────────────────────────────────

function QuestionRow({ q, locale, index, isLow }: { q: QuestionResult; locale: string; index: number; isLow: boolean }) {
  const { t } = useTranslation();
  const text = locale === "az" && q.question_az ? q.question_az : (q.question_en ?? "—");
  const timeSeconds = q.response_time_ms != null
    ? (q.response_time_ms / 1000).toFixed(1)
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 * index }}
      className={cn(
        "rounded-xl border p-4 space-y-2",
        q.is_correct
          ? "border-green-500/20 bg-green-500/5"
          : "border-purple-500/20 bg-purple-500/5",
      )}
    >
      {/* Header row: result icon + difficulty + time */}
      <div className="flex items-center gap-2">
        {q.is_correct ? (
          <CheckCircle2 className="size-4 shrink-0 text-green-400" aria-label={t("assessment.correct")} />
        ) : (
          <XCircle className="size-4 shrink-0 text-purple-400" aria-label={t("assessment.incorrect")} />
        )}
        <span className={cn(
          "text-xs font-medium",
          q.is_correct ? "text-green-400" : "text-purple-400",
        )}>
          {q.is_correct ? t("assessment.correct") : t("assessment.incorrect")}
        </span>
        <div className="flex-1" />
        {!isLow && <DifficultyBadge label={q.difficulty_label} />}
        {!isLow && timeSeconds !== null && (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="size-3" aria-hidden="true" />
            {t("assessment.responseTime", { n: timeSeconds })}
          </span>
        )}
      </div>

      {/* Question text */}
      <p className="text-sm text-foreground leading-relaxed">{text}</p>
    </motion.div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────

export default function QuestionBreakdownPage() {
  const { locale, sessionId } = useParams<{ locale: string; sessionId: string }>();
  const { t } = useTranslation();
  const router = useRouter();

  const { energy } = useEnergyMode();
  const isLow = energy === "low";
  const { data, isLoading, error } = useQuestionBreakdown(sessionId);

  // 404 → redirect to complete page (session not done yet or not found)
  useEffect(() => {
    if (error instanceof ApiError && (error.status === 404 || error.status === 422)) {
      router.replace(`/${locale}/assessment/${sessionId}/complete`);
    }
  }, [error, locale, sessionId, router]);

  // ── Loading ───────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-8 space-y-4" role="status" aria-live="polite">
        <div className="space-y-1">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-5 w-48" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  // ── Non-404/422 error (network, 500, etc.) ─────────────────────────────

  if (error && !(error instanceof ApiError && (error.status === 404 || error.status === 422))) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 flex flex-col items-center gap-4 text-center">
        <p className="text-sm text-muted-foreground">{error.message}</p>
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="size-4 mr-2" />
          {t("assessment.backToResults")}
        </Button>
      </div>
    );
  }

  if (!data) return null;

  const questions = data.questions ?? [];
  const correctCount = questions.filter((q) => q.is_correct).length;
  const correctQuestions = questions.filter((q) => q.is_correct);
  const incorrectQuestions = questions.filter((q) => !q.is_correct);

  const competencyLabel = t(`competency.${data.competency_slug}`, {
    defaultValue: data.competency_slug.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
  });

  // ── Results ───────────────────────────────────────────────────────────

  return (
    <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 text-muted-foreground"
          onClick={() => router.push(`/${locale}/assessment/${sessionId}/complete`)}
        >
          <ArrowLeft className="size-4 mr-1" />
          {t("assessment.backToResults")}
        </Button>
        <h1 className="text-xl font-bold">{t("assessment.questionBreakdown")}</h1>
        <p className="text-sm text-muted-foreground">
          {competencyLabel} ·{" "}
          {t("assessment.questionsCorrect", {
            correct: correctCount,
            total: questions.length,
          })}
        </p>
      </div>

      {/* Correct section */}
      {correctQuestions.length > 0 && (
        <section className="space-y-3" aria-label={t("assessment.correct")}>
          <h2 className="text-sm font-semibold text-green-400 uppercase tracking-wider flex items-center gap-2">
            <CheckCircle2 className="size-4" aria-hidden="true" />
            {t("assessment.correct")} ({correctQuestions.length})
          </h2>
          <div className="space-y-2">
            {correctQuestions.map((q, i) => (
              <QuestionRow key={q.question_id} q={q} locale={locale} index={i} isLow={isLow} />
            ))}
          </div>
        </section>
      )}

      {/* Incorrect section */}
      {incorrectQuestions.length > 0 && (
        <section className="space-y-3" aria-label={t("assessment.incorrect")}>
          <h2 className="text-sm font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
            <XCircle className="size-4" aria-hidden="true" />
            {t("assessment.incorrect")} ({incorrectQuestions.length})
          </h2>
          <div className="space-y-2">
            {incorrectQuestions.map((q, i) => (
              <QuestionRow key={q.question_id} q={q} locale={locale} index={i} isLow={isLow} />
            ))}
          </div>
        </section>
      )}

      {/* Bottom nav */}
      <div className="flex flex-col gap-3 pt-2">
        <Button
          onClick={() => router.push(`/${locale}/assessment/${sessionId}/complete`)}
          variant="outline"
          size="lg"
          className="w-full"
        >
          <ArrowLeft className="size-4 mr-2" />
          {t("assessment.backToResults")}
        </Button>
        <Button
          onClick={() => router.push(`/${locale}/assessment`)}
          size="lg"
          className="w-full"
        >
          {t("aura.retake")}
        </Button>
      </div>
    </div>
  );
}
