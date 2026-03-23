"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";

interface CompetencyBreakdownProps {
  scores: Record<string, number>;
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

const staggerChildren = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const slideUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
};

export function CompetencyBreakdown({ scores }: CompetencyBreakdownProps) {
  const { t } = useTranslation();

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

        return (
          <motion.div key={id} variants={slideUp}>
            <div className="flex items-center justify-between text-sm mb-1.5">
              <span className="font-medium text-foreground">{label}</span>
              <span className="text-xs text-muted-foreground tabular-nums">
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
          </motion.div>
        );
      })}
    </motion.div>
  );
}
