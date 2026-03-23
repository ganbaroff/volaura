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
      value: streak,
      label: t("dashboard.streak"),
      suffix: ` ${t("dashboard.days")}`,
      highlight: streak > 5,
    },
    {
      icon: Calendar,
      value: eventsCount,
      label: t("dashboard.recentActivity"),
      suffix: "",
      highlight: false,
    },
    {
      icon: Trophy,
      value: leaguePosition ?? "—",
      label: t("dashboard.league"),
      suffix: leaguePosition ? "" : "",
      highlight: false,
    },
  ];

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-3 gap-3"
    >
      {stats.map(({ icon: Icon, value, label, suffix, highlight }) => (
        <motion.div
          key={label}
          variants={item}
          className="rounded-xl border border-border bg-card p-3 text-center"
        >
          <Icon
            className={cn("size-5 mx-auto mb-1.5", highlight ? "text-primary" : "text-muted-foreground")}
            aria-hidden="true"
          />
          <p
            className={cn(
              "text-xl font-bold tabular-nums",
              highlight ? "text-primary" : "text-foreground"
            )}
          >
            {value}{suffix}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5 leading-tight">{label}</p>
        </motion.div>
      ))}
    </motion.div>
  );
}
