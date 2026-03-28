"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Loader2, BellOff, CheckCheck } from "lucide-react";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllRead,
} from "@/hooks/queries/use-notifications";
import type { NotificationItem } from "@/hooks/queries/use-notifications";

// ── Types ─────────────────────────────────────────────────────────────────────

type NotifCategory = "all" | "aura" | "events" | "org";

const CATEGORY_TYPES: Record<NotifCategory, string[]> = {
  all: [],
  aura: ["aura_update", "badge_earned", "assessment_complete"],
  events: ["event_invite"],
  org: ["org_view", "intro_request", "verification"],
};

// ── Icon map ──────────────────────────────────────────────────────────────────

const TYPE_ICON: Record<string, { icon: string; bgClass: string }> = {
  aura_update:          { icon: "⚡", bgClass: "bg-amber-500/10" },
  badge_earned:         { icon: "🏅", bgClass: "bg-violet-500/10" },
  assessment_complete:  { icon: "✓",  bgClass: "bg-green-500/10" },
  event_invite:         { icon: "📅", bgClass: "bg-blue-500/10" },
  org_view:             { icon: "👁",  bgClass: "bg-slate-500/10" },
  intro_request:        { icon: "🤝", bgClass: "bg-primary/10" },
  verification:         { icon: "✅", bgClass: "bg-green-500/10" },
};

function getIcon(type: string) {
  return TYPE_ICON[type] ?? { icon: "🔔", bgClass: "bg-muted/10" };
}

// ── Time formatting ───────────────────────────────────────────────────────────

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "now";
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

// ── NotifItem ─────────────────────────────────────────────────────────────────

function NotifItem({
  notif,
  onMarkRead,
}: {
  notif: NotificationItem;
  onMarkRead: (id: string) => void;
}) {
  const iconCfg = getIcon(notif.type);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn(
        "group relative rounded-xl p-4 transition-colors cursor-default",
        notif.is_read
          ? "bg-surface-container-low hover:bg-surface-container"
          : "bg-surface-container hover:bg-surface-container-high",
      )}
      onClick={() => !notif.is_read && onMarkRead(notif.id)}
      role={!notif.is_read ? "button" : undefined}
      tabIndex={!notif.is_read ? 0 : undefined}
      onKeyDown={(e) => {
        if (!notif.is_read && (e.key === "Enter" || e.key === " ")) onMarkRead(notif.id);
      }}
    >
      <div className="flex gap-3">
        {/* Icon */}
        <div className={cn("flex-shrink-0 size-10 rounded-xl flex items-center justify-center text-lg", iconCfg.bgClass)}>
          {iconCfg.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={cn("text-sm font-semibold leading-snug", !notif.is_read && "text-foreground")}>
              {notif.title}
            </p>
            <span className="text-[10px] text-muted-foreground shrink-0 mt-0.5">
              {timeAgo(notif.created_at)}
            </span>
          </div>
          {notif.body && (
            <p className="text-sm text-muted-foreground mt-0.5 leading-relaxed">{notif.body}</p>
          )}
        </div>

        {/* Unread dot */}
        {!notif.is_read && (
          <div className="size-2 rounded-full bg-primary mt-1.5 flex-shrink-0" aria-hidden="true" />
        )}
      </div>
    </motion.div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const CATEGORY_KEYS: { key: NotifCategory; labelKey: string }[] = [
  { key: "all",    labelKey: "notifications.categoryAll" },
  { key: "aura",   labelKey: "notifications.categoryAura" },
  { key: "events", labelKey: "notifications.categoryEvents" },
  { key: "org",    labelKey: "notifications.categoryOrg" },
];

export default function NotificationsPage() {
  const { t } = useTranslation();
  const [category, setCategory] = useState<NotifCategory>("all");

  const { data, isLoading } = useNotifications({ limit: 50 });
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllRead();

  const allNotifications = data?.notifications ?? [];
  const unreadCount = data?.unread_count ?? 0;

  const filtered = category === "all"
    ? allNotifications
    : allNotifications.filter((n) => CATEGORY_TYPES[category].includes(n.type));

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] ambient-glow-primary pointer-events-none z-0" />
      <div className="fixed bottom-[-5%] right-[-5%] w-[30%] h-[30%] ambient-glow-secondary pointer-events-none z-0" />

      <TopBar title={t("nav.notifications")} />

      <main className="relative z-10 pt-20 pb-10 px-6 max-w-3xl mx-auto">

        {/* Mark all read */}
        {unreadCount > 0 && (
          <div className="flex justify-end mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => markAll.mutate()}
              disabled={markAll.isPending}
              className="gap-1.5 text-primary"
            >
              <CheckCheck className="size-4" />
              {t("notifications.markAllRead")}
            </Button>
          </div>
        )}

        {/* Category tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {CATEGORY_KEYS.map(({ key, labelKey }) => (
            <button
              key={key}
              onClick={() => setCategory(key)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all active:scale-95",
                category === key
                  ? "bg-primary text-on-primary font-bold"
                  : "bg-surface-container text-on-surface-variant hover:bg-surface-container-highest",
              )}
            >
              {t(labelKey, { defaultValue: key })}
              {key === "all" && unreadCount > 0 && (
                <span className="ml-1.5 inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full bg-primary-container text-on-primary text-[10px] font-bold px-1">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex justify-center py-16">
            <Loader2 className="size-8 animate-spin text-primary" aria-label={t("common.loading")} />
          </div>
        )}

        {/* List */}
        {!isLoading && filtered.length > 0 && (
          <div className="space-y-2">
            {filtered.map((notif) => (
              <NotifItem
                key={notif.id}
                notif={notif}
                onMarkRead={(id) => markRead.mutate(id)}
              />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="size-24 mb-6 rounded-full bg-surface-container-high flex items-center justify-center">
              <BellOff className="size-10 text-muted-foreground" aria-hidden="true" />
            </div>
            <h3 className="text-xl font-bold mb-2">{t("notifications.emptyTitle")}</h3>
            <p className="text-muted-foreground text-sm max-w-xs">{t("notifications.emptyDesc")}</p>
          </div>
        )}
      </main>
    </div>
  );
}
