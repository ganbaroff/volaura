"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/cn";

export interface CompetencyScore {
  competency_id: string; // e.g. "communication"
  score: number;         // 0-100
}

interface SkillChipsProps {
  competencies: CompetencyScore[];
}

function getTier(score: number): "platinum" | "gold" | "silver" | "bronze" | "none" {
  if (score >= 90) return "platinum";
  if (score >= 75) return "gold";
  if (score >= 60) return "silver";
  if (score >= 40) return "bronze";
  return "none";
}

const CHIP_STYLES: Record<string, string> = {
  platinum: "bg-violet-500/15 text-violet-400 border-violet-400/30",
  gold:     "bg-yellow-500/15 text-yellow-400 border-yellow-400/30",
  silver:   "bg-slate-400/15 text-slate-300 border-slate-300/30",
  bronze:   "bg-amber-700/15 text-amber-600 border-amber-600/30",
  none:     "bg-muted text-muted-foreground border-border",
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.05 } },
};
const chip = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.2, ease: "easeOut" as const } },
};

export function SkillChips({ competencies }: SkillChipsProps) {
  const { t } = useTranslation();
  const shouldReduceMotion = useReducedMotion();

  if (competencies.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-3">
        {t("aura.noScoreYet")}
      </p>
    );
  }

  return (
    <motion.div
      variants={stagger}
      initial={shouldReduceMotion ? false : "hidden"}
      animate="visible"
      className="flex flex-wrap gap-2"
      role="list"
    >
      {competencies.map(({ competency_id, score }) => {
        const tier = getTier(score);
        const label = t(`competency.${competency_id}`, { defaultValue: competency_id });
        return (
          <motion.span
            key={competency_id}
            variants={chip}
            role="listitem"
            className={cn(
              "inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border",
              CHIP_STYLES[tier]
            )}
          >
            {label}
            <span className="opacity-60 tabular-nums">{score.toFixed(0)}</span>
          </motion.span>
        );
      })}
    </motion.div>
  );
}
