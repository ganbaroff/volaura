"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useAuraExplanation } from "@/hooks/queries/use-aura-explanation";
import type { CompetencyExplanation } from "@/hooks/queries/use-aura-explanation";

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function confidenceColor(confidence: string): string {
  switch (confidence) {
    case "high":   return "text-green-400";
    case "medium": return "text-amber-400";
    case "low":    return "text-purple-400";
    default:       return "text-muted-foreground";
  }
}

// ── Skeleton ─────────────────────────────────────────────────────────────────

function EvaluationSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2].map((n) => (
        <div key={n} className="rounded-xl border border-border bg-card/50 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="h-4 w-32 rounded bg-muted" />
            <div className="h-3 w-20 rounded bg-muted" />
          </div>
          <div className="space-y-2">
            <div className="h-3 w-full rounded bg-muted" />
            <div className="h-3 w-4/5 rounded bg-muted" />
            <div className="h-3 w-3/5 rounded bg-muted" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── ConceptBar ────────────────────────────────────────────────────────────────

interface ConceptBarProps {
  concept: string;
  value: number;
}

function ConceptBar({ concept, value }: ConceptBarProps) {
  const pct = Math.round(value * 100);
  const label = concept.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-muted-foreground">{label}</span>
        <span className="tabular-nums text-foreground font-medium">{pct}%</span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${pct}%`}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="h-full rounded-full bg-primary"
        />
      </div>
    </div>
  );
}

// ── CompetencyCard ────────────────────────────────────────────────────────────

interface CompetencyCardProps {
  item: CompetencyExplanation;
  index: number;
}

const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.35, ease: "easeOut" as const },
  }),
};

function CompetencyCard({ item, index }: CompetencyCardProps) {
  const { t } = useTranslation();

  // Aggregate concept_scores across all evaluations (average per concept)
  const conceptAggregates: Record<string, number[]> = {};
  for (const ev of item.evaluations) {
    for (const [concept, score] of Object.entries(ev.concept_scores)) {
      if (!conceptAggregates[concept]) conceptAggregates[concept] = [];
      conceptAggregates[concept].push(score);
    }
  }
  const avgConcepts: Record<string, number> = {};
  for (const [concept, scores] of Object.entries(conceptAggregates)) {
    avgConcepts[concept] = scores.reduce((a, b) => a + b, 0) / scores.length;
  }

  // Use the last evaluation's confidence + methodology as representative
  const lastEv = item.evaluations[item.evaluations.length - 1];
  const confidence = lastEv?.evaluation_confidence ?? "medium";
  const methodology = lastEv?.methodology ?? "BARS";

  const competencyLabel = item.competency_id
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <motion.div
      custom={index}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className="rounded-xl border border-border bg-card p-4 space-y-3"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-foreground">{competencyLabel}</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {formatDate(item.completed_at)}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xs text-muted-foreground">
            {item.items_evaluated} {t("assessment.question", { count: item.items_evaluated, defaultValue: "items" })}
          </p>
        </div>
      </div>

      {/* Concept bars */}
      {Object.keys(avgConcepts).length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {t("aura.conceptScores")}
          </p>
          <div className="space-y-2">
            {Object.entries(avgConcepts).map(([concept, value]) => (
              <ConceptBar key={concept} concept={concept} value={value} />
            ))}
          </div>
        </div>
      )}

      {/* Metadata row */}
      <div className="flex items-center gap-4 pt-1 border-t border-border/50">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">{t("aura.evaluationConfidence")}:</span>
          <span className={cn("text-xs font-medium capitalize", confidenceColor(confidence))}>
            {confidence}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">{t("aura.methodology")}:</span>
          <span className="text-xs font-medium text-foreground">{methodology}</span>
        </div>
      </div>
    </motion.div>
  );
}

// ── EvaluationLog ─────────────────────────────────────────────────────────────

export function EvaluationLog() {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  // Only start fetching once the section is opened
  const { data, isLoading, error } = useAuraExplanation(isOpen);

  // Scroll into view smoothly when opened
  useEffect(() => {
    if (!isOpen) return;
    // Allow DOM to update before scrolling
    const timer = setTimeout(() => {
      document.getElementById("evaluation-log-section")?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }, 100);
    return () => clearTimeout(timer);
  }, [isOpen]);

  return (
    <div id="evaluation-log-section" className="rounded-xl border border-border bg-card">
      {/* Toggle button */}
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-3 p-4 text-left"
        aria-expanded={isOpen}
        aria-controls="evaluation-log-body"
      >
        <span className="text-sm font-semibold text-foreground">
          {t("aura.whyThisScore")}
        </span>
        {isOpen ? (
          <ChevronUp className="size-4 text-muted-foreground shrink-0" aria-hidden="true" />
        ) : (
          <ChevronDown className="size-4 text-muted-foreground shrink-0" aria-hidden="true" />
        )}
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            id="evaluation-log-body"
            key="evaluation-log-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            style={{ overflow: "hidden" }}
          >
            <div className="px-4 pb-4 space-y-4">
              {/* Loading state */}
              {isLoading && <EvaluationSkeleton />}

              {/* Error state */}
              {error && !isLoading && (
                <p className="text-sm text-muted-foreground py-2">
                  {t("error.generic")}
                </p>
              )}

              {/* Empty state */}
              {!isLoading && !error && (!data || data.explanation_count === 0) && (
                <p className="text-sm text-muted-foreground py-2">
                  {t("aura.noExplanations")}
                </p>
              )}

              {/* Competency cards */}
              {!isLoading && !error && data && data.explanations.length > 0 && (
                <div className="space-y-3">
                  {data.explanations.map((item, index) => (
                    <CompetencyCard key={item.competency_id} item={item} index={index} />
                  ))}
                </div>
              )}

              {/* Footer methodology note */}
              {!isLoading && data && data.explanation_count > 0 && (
                <p className="text-xs text-muted-foreground/70 pt-1 border-t border-border/50">
                  {t("aura.methodologyNote")}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
