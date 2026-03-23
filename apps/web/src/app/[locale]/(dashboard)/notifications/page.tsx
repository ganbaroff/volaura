"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { TopBar } from "@/components/layout/top-bar";

// ── Types ────────────────────────────────────────────────────────────────────

type NotifCategory = "all" | "aura" | "events";

type NotifType = "aura_update" | "event_invite" | "org_view" | "badge_earned" | "verification";

interface Notification {
  id: string;
  type: NotifType;
  titleKey: string;
  bodyKey: string;
  timeAgo: string;
  isUnread: boolean;
  category: NotifCategory;
  actions?: { labelKey: string; variant: "primary" | "secondary" }[];
}

// ── Mock data (replace with useNotifications() TanStack Query hook when endpoint exists) ──

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: "1",
    type: "aura_update",
    titleKey: "notifications.types.auraUpdate",
    bodyKey: "notifications.bodies.auraIncreased",
    timeAgo: "2m",
    isUnread: true,
    category: "aura",
  },
  {
    id: "2",
    type: "event_invite",
    titleKey: "notifications.types.eventInvite",
    bodyKey: "notifications.bodies.eventInviteDesc",
    timeAgo: "1h",
    isUnread: true,
    category: "events",
    actions: [
      { labelKey: "notifications.actions.accept", variant: "primary" },
      { labelKey: "notifications.actions.details", variant: "secondary" },
    ],
  },
  {
    id: "3",
    type: "org_view",
    titleKey: "notifications.types.profileActivity",
    bodyKey: "notifications.bodies.orgViewed",
    timeAgo: "4h",
    isUnread: false,
    category: "all",
  },
  {
    id: "4",
    type: "badge_earned",
    titleKey: "notifications.types.badgeEarned",
    bodyKey: "notifications.bodies.badgeEarnedDesc",
    timeAgo: "1d",
    isUnread: false,
    category: "aura",
  },
];

// ── Icon map ─────────────────────────────────────────────────────────────────

const TYPE_ICON: Record<NotifType, { icon: string; bgClass: string; colorClass: string }> = {
  aura_update:   { icon: "⚡", bgClass: "bg-tertiary/10",   colorClass: "text-tertiary" },
  event_invite:  { icon: "📅", bgClass: "bg-primary/10",   colorClass: "text-primary" },
  org_view:      { icon: "👁",  bgClass: "bg-secondary/10", colorClass: "text-secondary" },
  badge_earned:  { icon: "🏅", bgClass: "bg-tertiary/10",   colorClass: "text-tertiary" },
  verification:  { icon: "✓",  bgClass: "bg-primary/10",   colorClass: "text-primary" },
};

// ── NotifItem sub-component ───────────────────────────────────────────────────

function NotifItem({
  notif,
  onMarkRead,
}: {
  notif: Notification;
  onMarkRead: (id: string) => void;
}) {
  const { t } = useTranslation();
  const iconCfg = TYPE_ICON[notif.type];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="group relative bg-surface-container-low p-5 rounded-xl transition-all hover:bg-surface-container-high"
      onClick={() => notif.isUnread && onMarkRead(notif.id)}
    >
      <div className="flex gap-4">
        {/* Icon */}
        <div className={`flex-shrink-0 w-12 h-12 rounded-xl ${iconCfg.bgClass} flex items-center justify-center text-xl ${iconCfg.colorClass}`}>
          {iconCfg.icon}
        </div>

        {/* Content */}
        <div className="flex-grow">
          <div className="flex justify-between items-start mb-1">
            <h3 className="font-headline font-semibold text-primary text-sm">
              {t(notif.titleKey)}
            </h3>
            <span className="text-[10px] font-label text-outline uppercase tracking-widest ml-2 flex-shrink-0">
              {notif.timeAgo}
            </span>
          </div>
          <p className="text-on-surface-variant text-sm leading-relaxed">
            {t(notif.bodyKey)}
          </p>

          {/* Action buttons */}
          {notif.actions && notif.actions.length > 0 && (
            <div className="mt-4 flex gap-3">
              {notif.actions.map((action) => (
                <button
                  key={action.labelKey}
                  className={`px-4 py-2 text-xs font-bold rounded-lg transition-all active:scale-95 ${
                    action.variant === "primary"
                      ? "bg-primary text-on-primary hover:opacity-90"
                      : "bg-surface-container-highest text-on-surface hover:bg-outline-variant"
                  }`}
                >
                  {t(action.labelKey)}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Unread dot */}
        {notif.isUnread && (
          <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0" />
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
];

export default function NotificationsPage() {
  const { t } = useTranslation();

  const [category, setCategory] = useState<NotifCategory>("all");
  const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS);

  const unreadCount = notifications.filter((n) => n.isUnread).length;

  const filtered = category === "all"
    ? notifications
    : notifications.filter((n) => n.category === category || n.category === "all");

  function markRead(id: string) {
    setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, isUnread: false } : n));
  }

  function markAllRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, isUnread: false })));
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Ambient glows */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] ambient-glow-primary pointer-events-none z-0" />
      <div className="fixed bottom-[-5%] right-[-5%] w-[30%] h-[30%] ambient-glow-secondary pointer-events-none z-0" />

      <TopBar title={t("nav.notifications")} />

      <main className="relative z-10 pt-20 pb-10 px-6 max-w-3xl mx-auto">
        {/* Mark all read */}
        {unreadCount > 0 && (
          <div className="flex justify-end mb-4">
            <button
              onClick={markAllRead}
              className="text-primary font-semibold text-sm hover:opacity-80 transition-opacity active:scale-95"
            >
              {t("notifications.markAllRead")}
            </button>
          </div>
        )}

        {/* Category tabs */}
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {CATEGORY_KEYS.map(({ key, labelKey }) => (
            <button
              key={key}
              onClick={() => setCategory(key)}
              className={`px-5 py-2.5 rounded-full text-sm font-medium whitespace-nowrap transition-all active:scale-95 ${
                category === key
                  ? "bg-primary text-on-primary font-bold shadow-[0_0_12px_rgba(192,193,255,0.2)]"
                  : "bg-surface-container text-on-surface-variant hover:bg-surface-container-highest"
              }`}
            >
              {t(labelKey)}
              {key === "all" && unreadCount > 0 && (
                <span className="ml-2 inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary-container text-on-primary text-[10px] font-bold">
                  {unreadCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Notification list */}
        {filtered.length > 0 ? (
          <div className="space-y-3">
            {/* Today section */}
            <div className="pb-2">
              <span className="text-[11px] font-bold text-outline tracking-[0.2em] uppercase">
                {t("notifications.today")}
              </span>
            </div>
            {filtered.map((notif) => (
              <NotifItem key={notif.id} notif={notif} onMarkRead={markRead} />
            ))}
          </div>
        ) : (
          /* Empty state */
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-24 h-24 mb-6 rounded-full bg-surface-container-high flex items-center justify-center">
              <span className="text-5xl">🔕</span>
            </div>
            <h3 className="text-xl font-headline font-bold text-on-surface mb-2">
              {t("notifications.emptyTitle")}
            </h3>
            <p className="text-on-surface-variant text-sm max-w-xs">
              {t("notifications.emptyDesc")}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
