"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { CalendarCheck, Clock, BadgeCheck } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export interface ImpactData {
  events_count: number;
  hours_volunteered: number;
  verified_skills: number;
}

interface ImpactMetricsProps {
  data: ImpactData;
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: "easeOut" as const } },
};

export function ImpactMetrics({ data }: ImpactMetricsProps) {
  const { t } = useTranslation();

  const metrics = [
    {
      icon: CalendarCheck,
      value: data.events_count,
      label: t("profile.eventsCount"),
      color: "text-primary",
    },
    {
      icon: Clock,
      value: data.hours_volunteered,
      label: t("profile.hoursContributed"),
      color: "text-blue-400",
    },
    {
      icon: BadgeCheck,
      value: data.verified_skills,
      label: t("profile.skills"),
      color: "text-green-400",
    },
  ];

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-3 gap-2 sm:gap-3"
    >
      {metrics.map(({ icon: Icon, value, label, color }) => (
        <motion.div
          key={label}
          variants={item}
          className="rounded-xl border border-border bg-card p-2 sm:p-3 text-center"
        >
          <Icon
            className={cn("size-5 mx-auto mb-1.5", color)}
            aria-hidden="true"
          />
          <p className="text-lg sm:text-xl font-bold tabular-nums text-foreground">{value}</p>
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-0.5 leading-tight">{label}</p>
        </motion.div>
      ))}
    </motion.div>
  );
}
