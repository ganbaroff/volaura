"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
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

function useCountUp(target: number, duration = 800) {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number>(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (target <= 0) return;
    startRef.current = null;
    const animate = (ts: number) => {
      if (!startRef.current) startRef.current = ts;
      const p = Math.min((ts - startRef.current) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(Math.round(eased * target * 10) / 10);
      if (p < 1) rafRef.current = requestAnimationFrame(animate);
      else setValue(target);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return value;
}

export function AuraScoreWidget({ score, badgeTier, isElite, locale }: AuraScoreWidgetProps) {
  const { t } = useTranslation();
  const displayScore = useCountUp(score);
  const style = BADGE_STYLES[badgeTier] ?? BADGE_STYLES.none;
  const tierLabel = t(`aura.${badgeTier}`, { defaultValue: badgeTier });
  const pct = Math.min(100, score);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      whileHover={{ scale: 1.02 }}
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
            AURA {displayScore.toFixed(1)}
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
              transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 }}
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
