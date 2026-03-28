"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Eye, Zap, Calendar } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export type ActivityType = "org_view" | "aura_update" | "event";

export interface ActivityItem {
  id: string;
  type: ActivityType;
  text: string;
  timeAgo: string;
}

interface ActivityFeedProps {
  items: ActivityItem[];
  loading?: boolean;
  locale: string;
}

const ICONS: Record<ActivityType, typeof Eye> = {
  org_view:    Eye,
  aura_update: Zap,
  event:       Calendar,
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
};
const row = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.25, ease: "easeOut" as const } },
};

export function ActivityFeed({ items, loading, locale }: ActivityFeedProps) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="size-8 rounded-full shrink-0" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-2.5 w-1/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="py-6 text-center space-y-1">
        <p className="text-sm font-medium text-on-surface">
          {t("dashboard.activityEmpty", { defaultValue: "Your story starts here" })}
        </p>
        <p className="text-xs text-muted-foreground">
          {t("dashboard.activityEmptyHint", { defaultValue: "Complete an assessment to see your first activity" })}
        </p>
      </div>
    );
  }

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-3">
      {items.slice(0, 5).map((item) => {
        const Icon = ICONS[item.type] ?? Zap;
        return (
          <motion.div
            key={item.id}
            variants={row}
            className="flex items-start gap-3"
          >
            <span className="shrink-0 mt-0.5 size-8 rounded-full bg-muted flex items-center justify-center">
              <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-foreground leading-snug">{item.text}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{item.timeAgo}</p>
            </div>
          </motion.div>
        );
      })}

      {items.length > 5 && (
        <a
          href={`/${locale}/profile`}
          className="block text-center text-xs text-primary hover:underline pt-1"
        >
          {t("common.viewAll")}
        </a>
      )}
    </motion.div>
  );
}
