"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { CalendarCheck, Calendar } from "lucide-react";

export interface TimelineEvent {
  id: string;
  event_name: string;
  event_date: string; // ISO date
  role: string | null;
  participated: boolean;
}

interface ActivityTimelineProps {
  events: TimelineEvent[];
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07 } },
};
const row = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.25, ease: "easeOut" as const } },
};

export function ActivityTimeline({ events }: ActivityTimelineProps) {
  const { t } = useTranslation();

  if (events.length === 0) {
    return (
      <div className="py-6 text-center space-y-2">
        <Calendar className="size-8 text-muted-foreground mx-auto" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">{t("profile.noEventsYet")}</p>
      </div>
    );
  }

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="visible"
      className="relative space-y-0"
    >
      {/* Vertical line */}
      <div
        className="absolute left-3.5 top-3 bottom-3 w-px bg-border"
        aria-hidden="true"
      />

      {events.map((ev, i) => {
        const date = new Date(ev.event_date).toLocaleDateString(undefined, {
          day: "numeric",
          month: "short",
          year: "numeric",
        });
        const isLast = i === events.length - 1;

        return (
          <motion.div
            key={ev.id}
            variants={row}
            className={`flex items-start gap-3 ${isLast ? "" : "pb-4"}`}
          >
            {/* Dot */}
            <span
              className={`shrink-0 mt-0.5 size-7 rounded-full flex items-center justify-center z-10 ${
                ev.participated
                  ? "bg-primary/20 text-primary"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              <CalendarCheck className="size-3.5" aria-hidden="true" />
            </span>

            {/* Content */}
            <div className="flex-1 min-w-0 pt-0.5">
              <p className="text-sm font-medium text-foreground leading-snug">
                {ev.event_name}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs text-muted-foreground">{date}</span>
                {ev.role && (
                  <>
                    <span className="text-xs text-muted-foreground">·</span>
                    <span className="text-xs text-muted-foreground capitalize">{ev.role}</span>
                  </>
                )}
                {ev.participated && (
                  <span className="text-xs font-medium text-primary">
                    ✓ {t("events.checkedIn")}
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
