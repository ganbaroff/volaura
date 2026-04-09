"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Flame, Calendar, Trophy } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface StatsRowProps {
  streak: number;
  eventsCount: number;
  leaguePosition: string | null; // e.g. "8%" or null
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" as const } },
};

export function StatsRow({ streak, eventsCount, leaguePosition }: StatsRowProps) {
  const { t } = useTranslation();

  const stats = [
    {
      icon: Flame,
      displayValue: streak > 0 ? `${streak} ${t("dashboard.days")}` : null,
      label: t("dashboard.streak"),
      highlight: streak > 5,
    },
    {
      icon: Calendar,
      displayValue: eventsCount > 0 ? String(eventsCount) : null,
      label: t("dashboard.recentActivity"),
      highlight: false,
    },
    {
      icon: Trophy,
      displayValue: leaguePosition ?? null,
      label: t("dashboard.league"),
      highlight: false,
      comingSoon: !leaguePosition,
    },
  ];

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 gap-3 sm:grid-cols-3"
    >
      {stats.map(({ icon: Icon, displayValue, label, highlight, comingSoon }) => {
        const isEmpty = displayValue === null;
        const text = isEmpty
          ? (comingSoon ? t("stats.comingSoon") : t("stats.notYet"))
          : displayValue;

        return (
          <motion.div
            key={label}
            variants={item}
            className="rounded-xl border border-border bg-card p-3 text-center"
          >
            <Icon
              className={cn(
                "size-5 mx-auto mb-1.5",
                highlight ? "text-primary" : "text-muted-foreground"
              )}
              aria-hidden="true"
            />
            <p
              className={cn(
                "tabular-nums",
                isEmpty
                  ? "text-sm text-muted-foreground font-normal"
                  : cn("text-xl font-bold", highlight ? "text-primary" : "text-foreground")
              )}
            >
              {text}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5 leading-tight">{label}</p>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
