"use client";

import { useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { useParams } from "next/navigation";
import { triggerHaptic } from "@/lib/haptics";

interface CompetencyBreakdownProps {
  scores: Record<string, number>;
  lastUpdated?: string | null;
  /** Hide freshness + retake for public/org views */
  isOwner?: boolean;
}

const COMPETENCY_ORDER = [
  { id: "communication", weight: 20 },
  { id: "reliability", weight: 15 },
  { id: "english_proficiency", weight: 15 },
  { id: "leadership", weight: 15 },
  { id: "event_performance", weight: 10 },
  { id: "tech_literacy", weight: 10 },
  { id: "adaptability", weight: 10 },
  { id: "empathy_safeguarding", weight: 5 },
] as const;

const RETEST_COOLDOWN_DAYS = 7;

const staggerChildren = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const slideUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
};

function getFreshnessInfo(daysSince: number) {
  if (daysSince <= 7) return { key: "freshnessRecent", color: "text-cyan-600" };
  if (daysSince <= 21) return { key: "freshnessWeeks", color: "text-amber-600" };
  return { key: "freshnessMonth", color: "text-muted-foreground" };
}

export function CompetencyBreakdown({ scores, lastUpdated, isOwner = false }: CompetencyBreakdownProps) {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();

  // Single gentle tap when competency scores first render — ADHD reward signal
  // Only fires if owner is viewing their own scores (not org/public views)
  useEffect(() => {
    if (isOwner) triggerHaptic("gentle_reminder");
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const daysSinceUpdate = lastUpdated
    ? Math.max(0, Math.floor((Date.now() - new Date(lastUpdated).getTime()) / 86_400_000))
    : null;

  const canRetake = daysSinceUpdate !== null && daysSinceUpdate >= RETEST_COOLDOWN_DAYS;
  const daysUntilRetake = daysSinceUpdate !== null ? Math.max(0, RETEST_COOLDOWN_DAYS - daysSinceUpdate) : null;

  const freshness = daysSinceUpdate !== null ? getFreshnessInfo(daysSinceUpdate) : null;

  return (
    <motion.div
      variants={staggerChildren}
      initial="hidden"
      animate="visible"
      className="space-y-3"
    >
      {COMPETENCY_ORDER.map(({ id, weight }) => {
        const score = Math.round(scores[id] ?? 0);
        const label = t(`competency.${id}`, { defaultValue: id });
        const assessed = score > 0;

        return (
          <motion.div key={id} variants={slideUp}>
            <div className="flex items-center justify-between gap-2 text-sm mb-1.5">
              <span className="font-medium text-foreground truncate min-w-0">{label}</span>
              <span className="text-xs text-muted-foreground tabular-nums shrink-0">
                {score}/100 · {weight}%
              </span>
            </div>
            <div
              className="h-2 w-full overflow-hidden rounded-full bg-muted"
              role="progressbar"
              aria-valuenow={score}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${label}: ${score}/100`}
            >
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${score}%` }}
                transition={{ duration: 0.8, ease: "easeOut", delay: 0.3 }}
                className="h-full rounded-full bg-primary"
              />
            </div>

            {/* Freshness + retake — only for owner, only if assessed */}
            {isOwner && assessed && freshness && (
              <div className="flex items-center justify-between mt-1.5">
                <span className={`text-xs ${freshness.color}`}>
                  {t(`aura.${freshness.key}`)}
                </span>
                {canRetake ? (
                  <Link
                    href={`/${locale}/assessment?competency=${id}`}
                    className="text-xs font-medium text-cyan-600 hover:text-cyan-700 transition-colors"
                  >
                    {t("aura.retakeNow")}
                  </Link>
                ) : daysUntilRetake !== null && daysUntilRetake > 0 ? (
                  <span className="text-xs text-muted-foreground">
                    {t("aura.retakeIn", { days: daysUntilRetake })}
                  </span>
                ) : null}
              </div>
            )}
          </motion.div>
        );
      })}
    </motion.div>
  );
}
