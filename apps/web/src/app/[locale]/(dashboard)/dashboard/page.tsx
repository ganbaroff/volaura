"use client";

import React, { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
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
import { useMyLeaderboardRank } from "@/hooks/queries/use-leaderboard";
import { useSkill } from "@/hooks/queries/use-skill";
import { useSubscription } from "@/hooks/queries/use-subscription";
import { useProfile } from "@/hooks/queries/use-profile";
import { FeedCards, type FeedCard } from "@/components/dashboard/feed-cards";
import { CrystalBalanceWidget } from "@/components/dashboard/crystal-balance-widget";
import { ApiError } from "@/lib/api/client";

// BATCH-O A11Y #3: motion variants — reduced-motion override applied per component via useDashboardMotion hook
const pageVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};
const pageVariantsReduced = {
  hidden: {},
  visible: {},  // no stagger
};
const sectionVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
};
const sectionVariantsReduced = {
  hidden: { opacity: 1, y: 0 },
  visible: { opacity: 1, y: 0 },
};

// ── Neuroscience helper: relative time (Conscious → Unconscious friction reduction)
// "2 hours ago" is processed faster than "3/27/2026" — no date parsing required.
function getRelativeTime(dateStr: string, t: (key: string, opts?: Record<string, unknown>) => string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return t("common.timeAgo.minutes", { count: diffMins, defaultValue: `${diffMins}m ago` });
  if (diffHours < 24) return t("common.timeAgo.hours", { count: diffHours, defaultValue: `${diffHours}h ago` });
  if (diffDays === 1) return t("common.timeAgo.yesterday", { defaultValue: "Yesterday" });
  if (diffDays < 7) return t("common.timeAgo.days", { count: diffDays, defaultValue: `${diffDays}d ago` });
  return new Date(dateStr).toLocaleDateString();
}

// ── Neuroscience helper: time-of-day greeting (Brain Constructs Reality)
// Opening word sets emotional tone for the entire session.
// Returns i18n key — translated in locales/*/common.json
function getGreetingKey(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "dashboard.greetingMorning";
  if (hour < 17) return "dashboard.greetingAfternoon";
  return "dashboard.greetingEvening";
}

export default function DashboardPage() {
  const { locale } = useParams<{ locale: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const isMounted = useRef(true);
  const prefersReducedMotion = useReducedMotion(); // BATCH-O A11Y: respect system motion preference
  const pVariants = prefersReducedMotion ? pageVariantsReduced : pageVariants;
  const sVariants = prefersReducedMotion ? sectionVariantsReduced : sectionVariants;

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

  // Get user display name + account_type from Supabase
  const [displayName, setDisplayName] = useState("");
  const [accountType, setAccountType] = useState<"volunteer" | "organization">("volunteer");
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      if (data.user && isMounted.current) {
        setDisplayName(
          data.user.user_metadata?.display_name ??
          data.user.email?.split("@")[0] ??
          ""
        );
        if (data.user.user_metadata?.account_type === "organization") {
          setAccountType("organization");
        }
      }
    });
  }, []);

  const { data: aura, isLoading: auraLoading, error: auraError, refetch: refetchAura } = useAuraScore();
  const { isTrial, isExpired, daysRemaining } = useSubscription();
  const { data: profile } = useProfile();

  // Trial banner dismissed per-session
  const [bannerDismissed, setBannerDismissed] = useState(() => {
    if (typeof window === "undefined") return false;
    return sessionStorage.getItem("trial_banner_dismissed") === "1";
  });

  function dismissBanner() {
    sessionStorage.setItem("trial_banner_dismissed", "1");
    setBannerDismissed(true);
  }

  // Share prompt — one-time, localStorage-persisted (survives tab close)
  const [sharePromptDismissed, setSharePromptDismissed] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("share_prompt_dismissed") === "true";
  });

  function handleDismissSharePrompt() {
    localStorage.setItem("share_prompt_dismissed", "true");
    setSharePromptDismissed(true);
  }

  function handleShare() {
    const username = profile?.username;
    if (!username) return;
    const url = `https://volaura.app/u/${username}?utm_source=dashboard_share&utm_medium=banner`;
    // Copy to clipboard
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(url).catch(() => {/* silent */});
    }
    // Open Telegram share
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent("My AURA profile — verified skills on Volaura")}`;
    window.open(telegramUrl, "_blank", "noopener,noreferrer");
    // Dismiss after sharing
    localStorage.setItem("share_prompt_dismissed", "true");
    setSharePromptDismissed(true);
  }
  const { data: rawActivity = [], isLoading: activityLoading } = useActivity();
  const { data: stats } = useDashboardStats();
  const { data: myRank } = useMyLeaderboardRank();

  // Feed curator — personalized recommendations (only when user has AURA score)
  const { data: feedData, isLoading: feedLoading } = useSkill(
    "feed-curator",
    { language: locale },
    { enabled: aura != null && aura.total_score > 0, staleTime: 5 * 60 * 1000 },
  );

  // Parse feed cards from skill output
  const feedCards: FeedCard[] = (() => {
    if (!feedData?.output) return [];
    try {
      const output = feedData.output;
      if (typeof output === "string") return JSON.parse(output) as FeedCard[];
      if (Array.isArray(output)) return output as FeedCard[];
      if ("cards" in output && Array.isArray(output.cards)) return output.cards as FeedCard[];
      return [];
    } catch {
      return [];
    }
  })();

  // Map API ActivityItem → Component ActivityItem
  // timeAgo uses relative time (getRelativeTime) instead of locale date string
  const activityItems: FeedActivityItem[] = rawActivity.map((item) => ({
    id: item.id,
    type: item.type as FeedActivityItem["type"],
    text: item.description,
    timeAgo: item.created_at ? getRelativeTime(item.created_at, t) : "",
  }));

  const loading = auraLoading;
  const hasScore = aura != null && aura.total_score > 0;
  // BATCH-O D1: never show share prompt when trial/expired banner is active — competing signals kill both
  const showSharePrompt = hasScore && !sharePromptDismissed && !!profile?.username && !(!bannerDismissed && (isTrial || isExpired));

  // Handle 401 — redirect to login
  useEffect(() => {
    if (auraError instanceof ApiError && auraError.status === 401 && isMounted.current) {
      router.replace(`/${locale}/login`);
    }
  }, [auraError, locale, router]);

  return (
    <>
      <TopBar title={t("nav.dashboard")} />

      {/* ── Trial / Expired Banner ── */}
      {!bannerDismissed && (isTrial || isExpired) && (
        <TrialBanner
          isTrial={isTrial}
          daysRemaining={daysRemaining ?? 0}
          onDismiss={dismissBanner}
          t={t}
        />
      )}

      {/* ── Share Profile Prompt — one-time viral loop trigger (AZ market: Telegram groups) ── */}
      {showSharePrompt && (
        <div className="mx-4 mt-3 rounded-xl border border-border bg-card p-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-xl shrink-0" aria-hidden="true">🎉</span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {t("dashboard.sharePrompt.title")}
              </p>
              <p className="text-xs text-muted-foreground">
                {t("dashboard.sharePrompt.desc")}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleShare}
              className="text-xs font-medium px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              {t("dashboard.sharePrompt.cta")}
            </button>
            <button
              type="button"
              onClick={handleDismissSharePrompt}
              aria-label="Dismiss"
              className="min-h-[44px] min-w-[44px] flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors -mr-2"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      <motion.div
        variants={pVariants}
        initial="hidden"
        animate="visible"
        className="p-4 space-y-5 pb-8"
      >
        {/* ── Welcome — time-aware greeting (Brain Constructs Reality principle) ── */}
        <motion.div variants={sVariants}>
          <h2 className="text-xl font-bold text-foreground">
            {t(getGreetingKey())}{displayName ? `, ${displayName}` : ""}! 👋
          </h2>
        </motion.div>

        {/* ── AURA Score Widget ── */}
        <motion.div variants={sVariants}>
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
            <NoScoreBanner locale={locale} t={t} accountType={accountType} />
          )}
        </motion.div>

        {/* ── Stats Row — only shown when user has score; zeros before first assessment are meaningless (BATCH-O D2) ── */}
        {hasScore && (
          <motion.div variants={sVariants}>
            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-24 rounded-xl" />
                ))}
              </div>
            ) : (
              <StatsRow
                streak={stats?.streak_days ?? 0}
                eventsCount={stats?.events_attended ?? 0}
                leaguePosition={myRank?.rank != null ? `#${myRank.rank}` : null}
              />
            )}
          </motion.div>
        )}

        {/* ── Crystal Balance — ecosystem link (Volaura→MindShift→Life Sim) ── */}
        {/* Only renders when balance > 0; invisible for new users until first assessment */}
        {hasScore && (
          <motion.div variants={sVariants}>
            <CrystalBalanceWidget />
          </motion.div>
        )}

        {/* ── Personalized Feed (feed-curator skill) ── */}
        {hasScore && (
          <motion.div variants={sVariants} className="space-y-2">
            <SectionHeader label={t("dashboard.feed.title", { defaultValue: "Recommended for you" })} />
            <FeedCards
              cards={feedCards}
              loading={feedLoading}
              locale={locale}
              onCardAction={(card) => {
                if (card.type === "challenge") router.push(`/${locale}/assessment`);
                else if (card.type === "event") router.push(`/${locale}/events`);
                else if (card.type === "people") router.push(`/${locale}/leaderboard`);
                else if (card.type === "achievement") router.push(`/${locale}/aura`);
              }}
            />
          </motion.div>
        )}

        {/* ── Recent Activity ── */}
        <motion.div variants={sVariants} className="space-y-2">
          <SectionHeader label={t("dashboard.recentActivity")} />
          <div className="rounded-xl border border-border bg-card p-4">
            <ActivityFeed
              items={activityItems}
              loading={activityLoading}
              locale={locale}
            />
          </div>
        </motion.div>

        {/* ── Quick Actions — Peak Shift: dominant primary CTA ── */}
        {/* hasScore: full-width "See your AURA" (dominant) + smaller secondary below.
            !hasScore: NoScoreBanner replaces the AURA widget above; QuickActions
            only shows the assessment link as the single dominant action. */}
        <motion.div variants={sVariants} className="space-y-2">
          <SectionHeader label={t("dashboard.quickActions")} />
          {hasScore ? (
            <div className="flex flex-col gap-3">
              {/* Primary — full-width dominant CTA */}
              <QuickActionPrimary
                href={`/${locale}/aura`}
                icon={<Sparkles className="size-5 text-yellow-400" aria-hidden="true" />}
                label={t("nav.aura")}
                sub={t("aura.overallScore")}
              />
              {/* Secondary — smaller, visually subordinate */}
              <QuickAction
                href={`/${locale}/assessment`}
                icon={<ClipboardList className="size-5 text-primary" aria-hidden="true" />}
                label={t("dashboard.startAssessment")}
                sub={t("assessment.title")}
              />
            </div>
          ) : (
            /* No score: single full-width dominant action */
            <QuickActionPrimary
              href={`/${locale}/assessment`}
              icon={<ClipboardList className="size-5 text-primary" aria-hidden="true" />}
              label={t("dashboard.startAssessment")}
              sub={t("assessment.title")}
            />
          )}
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

// Secondary quick-action card — standard size, visually subordinate
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

// Primary dominant quick-action — full-width, elevated border + background (Peak Shift)
function QuickActionPrimary({
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
      className="flex items-center gap-4 rounded-2xl border-2 border-primary/40 bg-primary/5 p-5 transition-all hover:border-primary/70 hover:bg-primary/10 active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <span className="shrink-0 size-11 rounded-full bg-primary/10 flex items-center justify-center">
        {icon}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-base font-semibold text-foreground truncate">{label}</p>
        <p className="text-xs text-muted-foreground truncate">{sub}</p>
      </div>
      <ChevronRight className="size-5 text-primary shrink-0" aria-hidden="true" />
    </Link>
  );
}

// NoScoreBanner — professional value prop framing.
// Volunteer: "Companies are searching for you — not a résumé"
// Org:       "Verified talent is waiting for you"
function NoScoreBanner({
  locale,
  t,
  accountType,
}: {
  locale: string;
  t: (k: string) => string;
  accountType: "volunteer" | "organization";
}) {
  const isOrg = accountType === "organization";
  const href = isOrg ? `/${locale}/org-volunteers` : `/${locale}/assessment`;

  return (
    <Link
      href={href}
      className="block rounded-2xl border-2 border-primary/40 bg-primary/5 p-6 transition-all hover:border-primary/70 hover:bg-primary/10 active:scale-[0.99]"
    >
      <div className="flex flex-col gap-3">
        <div className="text-3xl" aria-hidden="true">{isOrg ? "🏢" : "🎯"}</div>
        <div>
          <p className="font-bold text-foreground text-lg leading-snug">
            {isOrg ? t("dashboard.orgZeroHeadline") : t("dashboard.noScoreHeadline")}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {isOrg ? t("dashboard.orgZeroSub") : t("dashboard.noScoreSub")}
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-primary font-semibold text-sm">
          {isOrg ? t("dashboard.orgZeroCta") : t("dashboard.noScoreCta")}
        </div>
      </div>
    </Link>
  );
}

function TrialBanner({
  isTrial,
  daysRemaining,
  onDismiss,
  t,
}: {
  isTrial: boolean;
  daysRemaining: number;
  onDismiss: () => void;
  t: (k: string, opts?: Record<string, unknown>) => string;
}) {
  const isExpiredBanner = !isTrial;
  return (
    <div
      role="alert"
      className={`flex items-center justify-between gap-3 px-4 py-3 text-sm font-medium ${
        isExpiredBanner
          ? "bg-destructive/10 border-b border-destructive/20 text-destructive"
          : "bg-amber-50 border-b border-amber-200 text-amber-900 dark:bg-amber-900/20 dark:border-amber-700/40 dark:text-amber-200"
      }`}
    >
      <span className="flex-1 leading-snug">
        {isExpiredBanner
          ? t("subscription.trialExpiredBanner")
          : t("subscription.trialBanner", { count: daysRemaining })}
      </span>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-xs font-medium text-amber-700">
          {t("subscription.comingSoon")}
        </span>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss"
          className="size-11 flex items-center justify-center rounded-full text-amber-600 hover:text-amber-900 transition-colors -mr-2"
        >
          ×
        </button>
      </div>
    </div>
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
