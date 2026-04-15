"use client";

import { motion, useReducedMotion } from "framer-motion";
import NumberFlow from "@number-flow/react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/cn";
import { ChevronRight, Star } from "lucide-react";
import Link from "next/link";

interface AuraScoreWidgetProps {
  score: number;
  badgeTier: "platinum" | "gold" | "silver" | "bronze" | "none";
  isElite: boolean;
  locale: string;
}

const BADGE_STYLES: Record<string, { pill: string; glow: string }> = {
  platinum: { pill: "bg-violet-500/20 text-violet-400 border-violet-400/30", glow: "shadow-violet-500/20" },
  gold:     { pill: "bg-yellow-500/20 text-yellow-400 border-yellow-400/30", glow: "shadow-yellow-500/20" },
  silver:   { pill: "bg-slate-400/20 text-slate-300 border-slate-300/30",   glow: "shadow-slate-400/10"  },
  bronze:   { pill: "bg-amber-700/20 text-amber-600 border-amber-600/30",   glow: "shadow-amber-600/10"  },
  none:     { pill: "bg-muted text-muted-foreground border-border",          glow: ""                     },
};

export function AuraScoreWidget({ score, badgeTier, isElite, locale }: AuraScoreWidgetProps) {
  const { t } = useTranslation();
  const style = BADGE_STYLES[badgeTier] ?? BADGE_STYLES.none;
  const tierLabel = t(`aura.${badgeTier}`, { defaultValue: badgeTier });
  const pct = Math.min(100, score);
  // T1-4 (a11y ghost-audit 2026-04-15): drop hover scale + long width
  // transition when user prefers reduced motion.
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      whileHover={prefersReducedMotion ? undefined : { scale: 1.02 }}
      className={cn(
        "rounded-2xl border border-border bg-card p-5 cursor-pointer",
        "transition-shadow duration-300",
        style.glow && `hover:shadow-lg hover:${style.glow}`
      )}
    >
      <Link href={`/${locale}/aura`} className="flex items-center justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Identity headline first, score as context (Research #10: Overjustification) */}
          <p className="text-lg font-bold text-foreground">
            {t(`aura.identity_${badgeTier}`, {
              defaultValue: badgeTier !== "none"
                ? `${badgeTier.charAt(0).toUpperCase() + badgeTier.slice(1)}-level Professional`
                : t("dashboard.yourScore"),
            })}
          </p>
          <p
            className="text-2xl font-bold tabular-nums text-muted-foreground mt-0.5"
            aria-label={`${t("aura.overallScore")}: ${score.toFixed(1)}`}
          >
            AURA <NumberFlow value={score} format={{ minimumFractionDigits: 1, maximumFractionDigits: 1 }} />
          </p>

          {/* Progress bar */}
          <div
            role="progressbar"
            aria-valuenow={Math.round(score)}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${t("aura.overallScore")}: ${score.toFixed(1)}/100`}
            className="mt-3 h-1.5 w-full rounded-full bg-muted overflow-hidden"
          >
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={prefersReducedMotion ? { duration: 0 } : { duration: 1.2, ease: "easeOut", delay: 0.3 }}
              className="h-full rounded-full bg-primary"
            />
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <span
            className={cn(
              "text-xs font-semibold px-2.5 py-1 rounded-full border capitalize",
              style.pill
            )}
          >
            {tierLabel}
          </span>
          {isElite && (
            <span className="flex items-center gap-1 text-xs text-yellow-400 font-medium">
              <Star className="size-3" aria-hidden="true" />
              {t("aura.elite")}
            </span>
          )}
          <ChevronRight className="size-4 text-muted-foreground mt-1" aria-hidden="true" />
        </div>
      </Link>
    </motion.div>
  );
}
