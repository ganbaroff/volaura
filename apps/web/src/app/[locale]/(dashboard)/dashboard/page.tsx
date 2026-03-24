"use client";

import React, { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Sparkles, ChevronRight, ClipboardList, RefreshCw } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { TopBar } from "@/components/layout/top-bar";
import { AuraScoreWidget } from "@/components/dashboard/aura-score-widget";
import { StatsRow } from "@/components/dashboard/stats-row";
import { ActivityFeed, type ActivityItem as FeedActivityItem } from "@/components/dashboard/activity-feed";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuraScore } from "@/hooks/queries/use-aura";
import { useActivity, useDashboardStats } from "@/hooks/queries/use-dashboard";
import { ApiError } from "@/lib/api/client";

const pageVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};
const sectionVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
};

export default function DashboardPage() {
  const { locale } = useParams<{ locale: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  // Check auth — redirect if not logged in
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session && isMounted.current) {
        router.replace(`/${locale}/login`);
      }
    });
  }, [locale, router]);

  // Get user display name from Supabase
  const [displayName, setDisplayName] = useState("");
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      if (data.user && isMounted.current) {
        setDisplayName(
          data.user.user_metadata?.display_name ??
          data.user.email?.split("@")[0] ??
          ""
        );
      }
    });
  }, []);

  const { data: aura, isLoading: auraLoading, error: auraError, refetch: refetchAura } = useAuraScore();
  const { data: rawActivity = [], isLoading: activityLoading } = useActivity();
  const { data: stats } = useDashboardStats();

  // Map API ActivityItem (description + created_at) → Component ActivityItem (text + timeAgo)
  const activityItems: FeedActivityItem[] = rawActivity.map((item) => ({
    id: item.id,
    type: item.type as FeedActivityItem["type"],
    text: item.description,
    timeAgo: item.created_at ? new Date(item.created_at).toLocaleDateString() : "",
  }));

  const loading = auraLoading;
  const hasScore = aura != null && aura.total_score > 0;

  // Handle 401 — redirect to login
  useEffect(() => {
    if (auraError instanceof ApiError && auraError.status === 401 && isMounted.current) {
      router.replace(`/${locale}/login`);
    }
  }, [auraError, locale, router]);

  return (
    <>
      <TopBar title={t("nav.dashboard")} />

      <motion.div
        variants={pageVariants}
        initial="hidden"
        animate="visible"
        className="p-4 space-y-5 pb-8"
      >
        {/* ── Welcome ── */}
        <motion.div variants={sectionVariants}>
          <h2 className="text-xl font-bold text-foreground">
            {t("dashboard.welcome")}{displayName ? `, ${displayName}` : ""}!
          </h2>
        </motion.div>

        {/* ── AURA Score Widget ── */}
        <motion.div variants={sectionVariants}>
          {loading ? (
            <Skeleton className="h-28 w-full rounded-2xl" />
          ) : auraError ? (
            <ErrorCard
              message={t("error.generic")}
              onRetry={() => refetchAura()}
              t={t}
            />
          ) : hasScore ? (
            <AuraScoreWidget
              score={aura.total_score}
              badgeTier={aura.badge_tier}
              isElite={aura.is_elite}
              locale={locale}
            />
          ) : (
            <NoScoreBanner locale={locale} t={t} />
          )}
        </motion.div>

        {/* ── Stats Row ── */}
        <motion.div variants={sectionVariants}>
          {loading ? (
            <div className="grid grid-cols-3 gap-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24 rounded-xl" />
              ))}
            </div>
          ) : (
            <StatsRow
              streak={stats?.streak_days ?? 0}
              eventsCount={stats?.events_attended ?? 0}
              leaguePosition={null}
            />
          )}
        </motion.div>

        {/* ── Recent Activity ── */}
        <motion.div variants={sectionVariants} className="space-y-2">
          <SectionHeader label={t("dashboard.recentActivity")} />
          <div className="rounded-xl border border-border bg-card p-4">
            <ActivityFeed
              items={activityItems}
              loading={activityLoading}
              locale={locale}
            />
          </div>
        </motion.div>

        {/* ── Quick Actions ── */}
        <motion.div variants={sectionVariants} className="space-y-2">
          <SectionHeader label={t("dashboard.quickActions")} />
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <QuickAction
              href={`/${locale}/assessment`}
              icon={<ClipboardList className="size-5 text-primary" aria-hidden="true" />}
              label={t("dashboard.startAssessment")}
              sub={t("assessment.title")}
            />
            <QuickAction
              href={`/${locale}/aura`}
              icon={<Sparkles className="size-5 text-yellow-400" aria-hidden="true" />}
              label={t("nav.aura")}
              sub={t("aura.overallScore")}
            />
          </div>
        </motion.div>
      </motion.div>
    </>
  );
}

/* ─── sub-components ─── */

function SectionHeader({ label }: { label: string }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-0.5">
      {label}
    </p>
  );
}

function QuickAction({
  href,
  icon,
  label,
  sub,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  sub: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 rounded-xl border border-border bg-card p-4 transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <span className="shrink-0 size-9 rounded-full bg-muted flex items-center justify-center">
        {icon}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{label}</p>
        <p className="text-xs text-muted-foreground truncate">{sub}</p>
      </div>
      <ChevronRight className="size-4 text-muted-foreground shrink-0" aria-hidden="true" />
    </Link>
  );
}

function NoScoreBanner({
  locale,
  t,
}: {
  locale: string;
  t: (k: string) => string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="rounded-2xl border border-dashed border-border bg-card p-5 text-center space-y-3"
    >
      <div className="size-12 rounded-full bg-muted flex items-center justify-center mx-auto">
        <Sparkles className="size-6 text-muted-foreground" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-semibold text-foreground">{t("aura.noScoreYet")}</p>
        <p className="text-xs text-muted-foreground">{t("aura.noScoreDescription")}</p>
      </div>
      <Link
        href={`/${locale}/assessment`}
        className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        {t("aura.startAssessment")}
      </Link>
    </motion.div>
  );
}

function ErrorCard({
  message,
  onRetry,
  t,
}: {
  message: string;
  onRetry: () => void;
  t: (k: string) => string;
}) {
  return (
    <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5 text-center space-y-3">
      <p className="text-sm text-destructive">{message}</p>
      <button
        onClick={onRetry}
        className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <RefreshCw className="size-3.5" aria-hidden="true" />
        {t("error.retry")}
      </button>
    </div>
  );
}
