"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useTranslation } from "react-i18next";
import {
  Activity,
  Brain,
  Coins,
  Heart,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";

import { TopBar } from "@/components/layout/top-bar";
import { cn } from "@/lib/utils/cn";
import { CrystalShop } from "@/components/lifesim/crystal-shop";
import { useCrystalBalance } from "@/hooks/queries/use-character";
import {
  useLifesimNextChoice,
  useLifesimSubmitChoice,
} from "@/hooks/queries/use-lifesim";
import { useTrackEvent } from "@/hooks/use-analytics";

/**
 * Life Feed — MVP with real choice wiring (sprint task A7).
 *
 * Pulls next eligible event from GET /api/lifesim/next-choice via generated
 * SDK, renders it as a narrative card with choice buttons. On user pick,
 * POSTs /api/lifesim/choice, optimistically applies stat deltas with a
 * 300 ms animation, invalidates caches so the next event auto-loads.
 *
 * Constitution compliance:
 *   Law 1 — no destructive red; only primary / muted / border
 *   Law 3 — shame-free copy on empty + error states
 *   Law 4 — max 800 ms non-decorative anim; respects prefers-reduced-motion
 */

type StatKey =
  | "health"
  | "happiness"
  | "energy"
  | "intelligence"
  | "social"
  | "money";

interface StatRow {
  key: StatKey;
  icon: React.ComponentType<{ className?: string }>;
}

const INITIAL_STATS: Record<StatKey, number> = {
  health: 80,
  happiness: 65,
  energy: 70,
  intelligence: 60,
  social: 55,
  money: 0,
};

const STAT_ICONS: Record<StatKey, React.ComponentType<{ className?: string }>> = {
  health: Heart,
  happiness: Sparkles,
  energy: Zap,
  intelligence: Brain,
  social: Users,
  money: Coins,
};

const ROWS: StatKey[] = [
  "health",
  "happiness",
  "energy",
  "intelligence",
  "social",
  "money",
];

function clampStat(key: StatKey, value: number): number {
  if (key === "money") return value; // unbounded (may go negative for debt)
  return Math.max(0, Math.min(100, value));
}

function StatBar({
  keyName,
  value,
  t,
}: {
  keyName: StatKey;
  value: number;
  t: (k: string, o?: Record<string, unknown>) => string;
}) {
  const Icon = STAT_ICONS[keyName];
  const pct =
    keyName === "money"
      ? Math.min(100, Math.max(0, (value / 9999) * 100))
      : Math.min(100, Math.max(0, value));
  const display = keyName === "money" ? value.toLocaleString() : String(Math.round(value));

  return (
    <div className="flex items-center gap-3">
      <Icon className="size-5 shrink-0 text-muted-foreground" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2 mb-1">
          <span className="text-xs font-medium text-on-surface-variant">
            {t(`lifesim.stat.${keyName}`, { defaultValue: keyName })}
          </span>
          <motion.span
            key={value}
            initial={{ scale: 1.15, color: "var(--color-primary)" }}
            animate={{ scale: 1, color: "inherit" }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="text-xs font-semibold tabular-nums"
          >
            {display}
          </motion.span>
        </div>
        <div
          className="h-1.5 rounded-full bg-surface-container overflow-hidden"
          role="progressbar"
          aria-valuenow={Math.round(value)}
          aria-valuemin={0}
          aria-valuemax={keyName === "money" ? 9999 : 100}
        >
          <motion.div
            className="h-full rounded-full bg-primary/70"
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
        </div>
      </div>
    </div>
  );
}

interface LifesimChoice {
  text_ru?: string;
  consequences?: Record<string, number>;
}

interface LifesimEvent {
  id: string;
  category?: string;
  title_ru?: string;
  description_ru?: string;
  choices?: LifesimChoice[];
}

export default function LifeFeedPage() {
  const { t } = useTranslation();
  const prefersReducedMotion = useReducedMotion();

  const [stats, setStats] = useState<Record<StatKey, number>>(INITIAL_STATS);
  const [age] = useState<number>(25); // TODO A7.1: aggregate from character_events
  const [submitting, setSubmitting] = useState(false);

  const nextChoiceQuery = useLifesimNextChoice({
    age,
    intelligence: stats.intelligence,
    social: stats.social,
    energy: stats.energy,
    happiness: stats.happiness,
    health: stats.health,
    money: stats.money,
  });

  const submitChoice = useLifesimSubmitChoice();
  const crystalBalance = useCrystalBalance();
  const currentCrystals = crystalBalance.data?.crystal_balance ?? 0;
  const track = useTrackEvent();

  // Fire lifesim_feed_viewed once per mount. Guard against strict-mode double-fire
  // in dev via ref flag — same pattern as aura/page.tsx revealFiredRef.
  const feedViewFiredRef = useRef(false);
  useEffect(() => {
    if (feedViewFiredRef.current) return;
    feedViewFiredRef.current = true;
    track("lifesim_feed_viewed", { age });
  }, [track, age]);

  const applyBoostLocally = (boost: Record<string, number>) => {
    setStats((prev) => {
      const next = { ...prev };
      for (const [k, delta] of Object.entries(boost)) {
        if (k in next) {
          next[k as StatKey] = clampStat(k as StatKey, next[k as StatKey] + delta);
        }
      }
      return next;
    });
  };

  const event = nextChoiceQuery.data?.event as LifesimEvent | null | undefined;

  const onPick = async (choiceIndex: number) => {
    if (!event || submitting) return;
    setSubmitting(true);
    const choice = event.choices?.[choiceIndex];
    const consequences = (choice?.consequences ?? {}) as Record<string, number>;
    try {
      await submitChoice.mutateAsync({
        event_id: event.id,
        choice_index: choiceIndex,
        stats_before: stats,
      });
      track("lifesim_choice_submitted", {
        event_id: event.id,
        category: event.category,
        choice_index: choiceIndex,
        age,
      });
      // Optimistic: apply consequences locally (server applied same logic)
      setStats((prev) => {
        const next = { ...prev };
        for (const [k, delta] of Object.entries(consequences)) {
          if (k in next) {
            next[k as StatKey] = clampStat(k as StatKey, next[k as StatKey] + delta);
          }
        }
        return next;
      });
    } catch {
      // Error surfacing via query state; no user-blocking modal
    } finally {
      setSubmitting(false);
    }
  };

  const sectionVariants = useMemo(
    () => ({
      hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 12 },
      visible: { opacity: 1, y: 0 },
    }),
    [prefersReducedMotion]
  );

  const statRows: StatRow[] = ROWS.map((k) => ({ key: k, icon: STAT_ICONS[k] }));

  return (
    <div className="min-h-screen bg-background">
      <TopBar />

      <main className="max-w-6xl mx-auto px-4 py-6 md:py-10">
        <motion.header
          initial="hidden"
          animate="visible"
          variants={sectionVariants}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="mb-8"
        >
          <h1 className="text-2xl md:text-3xl font-headline font-bold tracking-tight text-foreground">
            {t("lifesim.title", { defaultValue: "Life Feed" })}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground max-w-2xl">
            {t("lifesim.subtitle", {
              defaultValue:
                "Твоя жизнь как серия глав. Каждый выбор здесь — отражение того что ты уже проверил в VOLAURA.",
            })}
          </p>
        </motion.header>

        <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
          <motion.aside
            initial="hidden"
            animate="visible"
            variants={sectionVariants}
            transition={{ duration: 0.35, delay: 0.05 }}
            className="rounded-xl border border-border bg-card p-5 h-fit lg:sticky lg:top-24"
            aria-label={t("lifesim.stats.title", { defaultValue: "Character stats" })}
          >
            <div className="flex items-center gap-2 mb-4">
              <Activity className="size-5 text-primary" aria-hidden="true" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                {t("lifesim.stats.title", { defaultValue: "Character" })}
              </h2>
            </div>
            <div className="space-y-4">
              {statRows.map((row) => (
                <StatBar key={row.key} keyName={row.key} value={stats[row.key]} t={t} />
              ))}
            </div>
          </motion.aside>

          <motion.section
            initial="hidden"
            animate="visible"
            variants={sectionVariants}
            transition={{ duration: 0.35, delay: 0.1 }}
            className="min-h-[400px]"
            aria-label={t("lifesim.feed.title", { defaultValue: "Life feed" })}
          >
            <AnimatePresence mode="wait">
              {nextChoiceQuery.isLoading ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-16 min-h-[400px] flex items-center justify-center"
                  role="status"
                  aria-live="polite"
                >
                  <span className="text-sm text-muted-foreground">
                    {t("common.loading", { defaultValue: "Loading…" })}
                  </span>
                </motion.div>
              ) : event ? (
                <motion.article
                  key={event.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  className="rounded-xl border border-border bg-card p-6 md:p-8"
                >
                  {event.category ? (
                    <span className="inline-block mb-3 text-xs font-semibold uppercase tracking-wider text-primary">
                      {t(`lifesim.category.${event.category}`, { defaultValue: event.category })}
                    </span>
                  ) : null}
                  <h2 className="text-xl md:text-2xl font-headline font-bold text-foreground mb-3">
                    {event.title_ru}
                  </h2>
                  <p className="text-base text-on-surface-variant mb-6 leading-relaxed">
                    {event.description_ru}
                  </p>
                  <div className="flex flex-col gap-3">
                    {(event.choices ?? []).map((choice, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => onPick(idx)}
                        disabled={submitting}
                        className={cn(
                          "w-full text-left rounded-lg border border-border bg-surface-container-low px-4 py-3",
                          "text-sm font-medium text-foreground",
                          "hover:border-primary/60 hover:bg-surface-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
                          "transition-colors duration-200",
                          "disabled:opacity-60 disabled:cursor-not-allowed"
                        )}
                      >
                        {choice.text_ru ?? `Choice ${idx + 1}`}
                      </button>
                    ))}
                  </div>
                </motion.article>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-16 min-h-[400px] flex flex-col items-center justify-center text-center"
                  role="status"
                >
                  <Sparkles className="size-10 text-primary/60 mb-4" aria-hidden="true" />
                  <h2 className="text-lg font-semibold text-foreground mb-2">
                    {t("lifesim.emptyState.title", { defaultValue: "Твоя первая глава ждёт" })}
                  </h2>
                  <p className="text-sm text-muted-foreground max-w-md">
                    {t("lifesim.emptyState.body", {
                      defaultValue:
                        "Пройди хотя бы один assessment в VOLAURA — и сюда прилетит первое событие, в котором нужно будет сделать выбор.",
                    })}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.section>
        </div>

        <CrystalShop currentCrystals={currentCrystals} onBoost={applyBoostLocally} />
      </main>
    </div>
  );
}
