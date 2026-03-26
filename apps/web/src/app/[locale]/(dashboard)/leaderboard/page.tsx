"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { TopBar } from "@/components/layout/top-bar";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeaderboard } from "@/hooks/queries/use-leaderboard";
import type { LeaderboardPeriod, LeaderboardEntry } from "@/hooks/queries/use-leaderboard";
import { RefreshCw } from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

type UiPeriod = "weekly" | "monthly" | "allTime";
type Tier = "platinum" | "gold" | "silver" | "bronze" | "rising";

interface LeaderEntry {
  id: string;
  rank: number;
  name: string;
  score: number;
  tier: Tier;
  isCurrentUser?: boolean;
  avatarInitial: string;
}

// ── Period mapping ────────────────────────────────────────────────────────────

const UI_TO_API_PERIOD: Record<UiPeriod, LeaderboardPeriod> = {
  weekly: "weekly",
  monthly: "monthly",
  allTime: "all_time",
};

function normalizeTier(badgeTier: string): Tier {
  const valid: Tier[] = ["platinum", "gold", "silver", "bronze"];
  const lower = badgeTier?.toLowerCase() as Tier;
  return valid.includes(lower) ? lower : "rising";
}

function toLeaderEntry(entry: LeaderboardEntry): LeaderEntry {
  const name = entry.display_name || entry.username || `#${entry.rank}`;
  return {
    id: `${entry.rank}`,
    rank: entry.rank,
    name,
    score: entry.total_score,
    tier: normalizeTier(entry.badge_tier),
    avatarInitial: name.charAt(0).toUpperCase(),
  };
}

// ── Animated counter hook ─────────────────────────────────────────────────────

function useAnimatedCounter(target: number, duration = 1400) {
  const [value, setValue] = useState(0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();
    const step = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      setValue(parseFloat((eased * target).toFixed(1)));
      if (t < 1) frameRef.current = requestAnimationFrame(step);
    };
    frameRef.current = requestAnimationFrame(step);
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current); };
  }, [target, duration]);

  return value;
}

// ── Tier display config ───────────────────────────────────────────────────────

const TIER_CONFIG: Record<Tier, { label: string; color: string; glowClass: string; borderColor: string }> = {
  platinum: { label: "Platinum", color: "#e5e4e2", glowClass: "aura-glow-platinum", borderColor: "#e5e4e2" },
  gold:     { label: "Gold",     color: "#ffd700", glowClass: "aura-glow-gold",     borderColor: "#ffd700" },
  silver:   { label: "Silver",   color: "#c0c0c0", glowClass: "aura-glow-silver",   borderColor: "#c0c0c0" },
  bronze:   { label: "Bronze",   color: "#cd7f32", glowClass: "",                   borderColor: "#cd7f32" },
  rising:   { label: "Rising",   color: "#908fa0", glowClass: "",                   borderColor: "transparent" },
};

// ── Skeleton ──────────────────────────────────────────────────────────────────

function LeaderboardSkeleton() {
  return (
    <div className="space-y-3">
      {/* Podium skeleton */}
      <div className="flex items-end justify-center gap-2 min-h-[300px] pt-12 mb-12">
        <Skeleton className="w-[120px] h-[180px] rounded-t-2xl" />
        <Skeleton className="w-[140px] h-[240px] rounded-t-3xl" />
        <Skeleton className="w-[120px] h-[160px] rounded-t-2xl" />
      </div>
      {/* Row skeletons */}
      {[1, 2, 3, 4].map((i) => (
        <Skeleton key={i} className="h-[72px] rounded-2xl" />
      ))}
    </div>
  );
}

// ── PodiumEntry sub-component ─────────────────────────────────────────────────

interface PodiumEntryProps {
  entry: LeaderEntry;
  size: "sm" | "lg";
  delay: number;
}

function PodiumEntry({ entry, size, delay }: PodiumEntryProps) {
  const animated = useAnimatedCounter(entry.score, 1600);
  const tier = TIER_CONFIG[entry.tier];
  const isLg = size === "lg";

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay / 1000, duration: 0.6, type: "spring", stiffness: 100 }}
      className={`flex flex-col items-center ${isLg ? "flex-1 max-w-[140px] z-10 -mb-2" : "flex-1 max-w-[120px]"}`}
    >
      {/* Avatar */}
      <div
        className={`relative mb-4 ${isLg ? "mb-6 animate-float" : delay === 300 ? "animate-float-delayed" : "animate-float-more-delayed"}`}
      >
        {isLg && (
          <div className="absolute -top-10 left-1/2 -translate-x-1/2 text-aura-platinum">
            <span className="text-4xl drop-shadow-[0_0_10px_rgba(229,228,226,0.8)]">★</span>
          </div>
        )}
        <div
          className={`${isLg ? "w-24 h-24" : "w-16 h-16"} rounded-full border-4 overflow-hidden bg-surface-container-high p-1 ${tier.glowClass}`}
          style={{ borderColor: `${tier.borderColor}60` }}
        >
          <div
            className="w-full h-full rounded-full flex items-center justify-center text-lg font-bold bg-surface-container-highest"
            style={{ color: tier.color }}
          >
            {entry.avatarInitial}
          </div>
        </div>
        <div
          className="absolute -bottom-2 left-1/2 -translate-x-1/2 text-[10px] font-bold px-3 py-0.5 rounded-full uppercase tracking-wider whitespace-nowrap"
          style={{ backgroundColor: tier.color, color: "#13131b" }}
        >
          {tier.label}
        </div>
      </div>

      {/* Score block */}
      <div
        className={`${isLg ? "h-32" : "h-20"} w-full bg-surface-container-${isLg ? "high" : "low"} ${isLg ? "rounded-t-3xl" : "rounded-t-2xl"} flex flex-col items-center justify-start pt-4 px-2 text-center`}
      >
        <span className={`${isLg ? "text-sm font-bold" : "text-xs font-semibold"} text-on-surface truncate w-full`}>
          {entry.name}
        </span>
        <span className={`text-primary ${isLg ? "font-extrabold text-lg tracking-tight" : "font-bold text-sm"}`}>
          {animated.toFixed(1)}
        </span>
      </div>
    </motion.div>
  );
}

// ── RankRow sub-component ─────────────────────────────────────────────────────

function RankRow({ entry }: { entry: LeaderEntry }) {
  const tier = TIER_CONFIG[entry.tier];
  return (
    <div
      className={`flex items-center gap-4 p-4 rounded-2xl transition-colors ${
        entry.isCurrentUser
          ? "bg-surface-container-low ring-2 ring-primary/50 relative overflow-hidden"
          : "bg-surface-container-low hover:bg-surface-container-high"
      }`}
    >
      {entry.isCurrentUser && (
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-2xl" />
      )}
      <span
        className={`w-6 text-center font-bold text-sm ${entry.isCurrentUser ? "text-primary" : "text-outline"}`}
      >
        {entry.rank}
      </span>
      <div
        className={`w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-sm ${
          entry.isCurrentUser ? "border-2 border-primary" : ""
        } bg-surface-container-highest`}
        style={{ color: tier.color }}
      >
        {entry.avatarInitial}
      </div>
      <div className="flex-grow">
        <p className={`font-semibold text-on-surface ${entry.isCurrentUser ? "font-bold" : ""}`}>
          {entry.name}
        </p>
        <span
          className="text-[10px] font-bold uppercase tracking-widest"
          style={{ color: tier.color }}
        >
          {tier.label}
        </span>
      </div>
      <div className="text-right">
        <p className="font-bold text-primary">{entry.score.toFixed(1)}</p>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const PERIOD_KEYS: Record<UiPeriod, string> = {
  weekly:  "leaderboard.periodWeekly",
  monthly: "leaderboard.periodMonthly",
  allTime: "leaderboard.periodAllTime",
};

const pageVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

export default function LeaderboardPage() {
  const { t } = useTranslation();
  const [uiPeriod, setUiPeriod] = useState<UiPeriod>("weekly");

  const { data, isLoading, error, refetch } = useLeaderboard(UI_TO_API_PERIOD[uiPeriod]);

  const entries: LeaderEntry[] = (data?.entries ?? []).map(toLeaderEntry);
  const top3 = entries.slice(0, 3);
  const rest = entries.slice(3);

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Ambient glows */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] ambient-glow-primary pointer-events-none z-0" />
      <div className="fixed bottom-[-5%] right-[-5%] w-[30%] h-[30%] ambient-glow-secondary pointer-events-none z-0" />

      <TopBar title={t("nav.leaderboard")} />

      <main className="relative z-10 pt-20 pb-10 px-4 max-w-2xl mx-auto">
        {/* Period filter tabs */}
        <nav className="flex p-1 bg-surface-container-low rounded-xl mb-8">
          {(["weekly", "monthly", "allTime"] as UiPeriod[]).map((p) => (
            <button
              key={p}
              onClick={() => setUiPeriod(p)}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${
                uiPeriod === p
                  ? "bg-surface-container-high text-primary shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
            >
              {t(PERIOD_KEYS[p])}
            </button>
          ))}
        </nav>

        {/* Loading state */}
        {isLoading && <LeaderboardSkeleton />}

        {/* Error state */}
        {error && !isLoading && (
          <div className="flex flex-col items-center justify-center py-20 text-center gap-4">
            <p className="text-sm text-on-surface-variant">{t("error.generic")}</p>
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
            >
              <RefreshCw className="size-3.5" aria-hidden="true" />
              {t("error.retry")}
            </button>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && entries.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-20 h-20 bg-surface-container-high rounded-full flex items-center justify-center mb-6">
              <span className="text-4xl">🏆</span>
            </div>
            <h3 className="text-xl font-semibold mb-2 text-on-surface">
              {t("leaderboard.emptyTitle")}
            </h3>
            <p className="text-on-surface-variant max-w-xs mx-auto text-sm">
              {t("leaderboard.emptyDesc")}
            </p>
          </div>
        )}

        {/* Podium — only if we have at least 3 entries */}
        {!isLoading && !error && top3.length >= 3 && (
          <section className="relative flex items-end justify-center gap-2 md:gap-6 mb-12 min-h-[300px] podium-gradient pt-12 rounded-3xl overflow-hidden">
            {/* Order: 2nd, 1st, 3rd */}
            <PodiumEntry entry={top3[1]} size="sm" delay={300} />
            <PodiumEntry entry={top3[0]} size="lg" delay={0} />
            <PodiumEntry entry={top3[2]} size="sm" delay={500} />
          </section>
        )}

        {/* Partial podium — fewer than 3 entries */}
        {!isLoading && !error && top3.length > 0 && top3.length < 3 && (
          <motion.div
            variants={pageVariants}
            initial="hidden"
            animate="visible"
            className="space-y-3 mb-4"
          >
            {top3.map((entry) => (
              <motion.div
                key={entry.id}
                variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
              >
                <RankRow entry={entry} />
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* Rankings list (rank 4+) */}
        {!isLoading && !error && rest.length > 0 && (
          <motion.div
            variants={pageVariants}
            initial="hidden"
            animate="visible"
            className="space-y-3"
          >
            {rest.map((entry) => (
              <motion.div
                key={entry.id}
                variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
              >
                <RankRow entry={entry} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </main>
    </div>
  );
}
