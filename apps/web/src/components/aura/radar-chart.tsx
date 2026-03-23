"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const COMPETENCY_IDS = [
  "communication",
  "reliability",
  "english_proficiency",
  "leadership",
  "event_performance",
  "tech_literacy",
  "adaptability",
  "empathy_safeguarding",
] as const;

const BADGE_STROKE: Record<string, string> = {
  platinum: "#a78bfa",
  gold: "#facc15",
  silver: "#94a3b8",
  bronze: "#b45309",
  none: "#6366f1",
};

interface AuraRadarChartProps {
  competencyScores: Record<string, number>;
  badgeTier?: string;
  size?: "sm" | "md" | "lg";
}

export function AuraRadarChart({
  competencyScores,
  badgeTier = "none",
  size = "md",
}: AuraRadarChartProps) {
  const { t } = useTranslation();
  const [revealed, setRevealed] = useState(false);

  // Animate in after mount
  useEffect(() => {
    const timer = setTimeout(() => setRevealed(true), 400);
    return () => clearTimeout(timer);
  }, []);

  const data = COMPETENCY_IDS.map((id) => ({
    subject: t(`competency.${id}`, { defaultValue: id }),
    score: revealed ? Math.round(competencyScores[id] ?? 0) : 0,
    fullMark: 100,
  }));

  const heights = { sm: 200, md: 300, lg: 400 };
  const stroke = BADGE_STROKE[badgeTier] ?? BADGE_STROKE.none;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.3, ease: "easeOut" }}
      aria-label={t("aura.competencyRadar")}
    >
      <ResponsiveContainer width="100%" height={heights[size]}>
        <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
          />
          <Radar
            name="AURA"
            dataKey="score"
            stroke={stroke}
            fill={stroke}
            fillOpacity={0.18}
            strokeWidth={2}
            animationDuration={1200}
            animationEasing="ease-out"
          />
          <Tooltip
            formatter={(value: number) => [`${value}/100`, t("aura.totalScore")]}
            contentStyle={{
              background: "hsl(var(--popover))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              fontSize: "12px",
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
