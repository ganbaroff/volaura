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

  // BATCH-O A11Y #4: screen-reader accessible table mirrors the visual radar chart
  const srTable = (
    <table className="sr-only" aria-label={t("aura.competencyRadar")}>
      <caption>{t("aura.competencyRadar")}</caption>
      <thead>
        <tr>
          <th scope="col">{t("aura.competency")}</th>
          <th scope="col">{t("aura.score")}</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row) => (
          <tr key={row.subject}>
            <td>{row.subject}</td>
            <td>{row.score}/100</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  // T0-1 (ghost-audit a11y P0-1, 2026-04-15): previously `aria-hidden="true"`
  // wrapped BOTH the visual chart AND the sr-only table — AT saw zero data.
  // Fix: srTable sits OUTSIDE the aria-hidden wrapper so screen readers get
  // the competency scores as a real table; only the decorative Recharts SVG
  // inside the motion.div is hidden.
  return (
    <div>
      {srTable}
      <motion.div
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.3, ease: "easeOut" }}
        aria-hidden="true"
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
              animationDuration={800}
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
    </div>
  );
}
