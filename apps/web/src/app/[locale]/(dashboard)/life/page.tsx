"use client";

import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Sparkles, Heart, Zap, Brain, Users, Activity, Coins } from "lucide-react";

import { TopBar } from "@/components/layout/top-bar";
import { cn } from "@/lib/utils/cn";

/**
 * Life Feed — MVP skeleton (sprint task A6).
 *
 * Surface for the reimagined Life Simulator (Path C from
 * docs/LIFE-SIMULATOR-REIMAGINE-2026-04-15.md): narrative "chapters" inside
 * the VOLAURA web app instead of a standalone Godot build.
 *
 * This iteration wires layout + stats sidebar + empty state. Next iteration (A7)
 * wires the choice modal to POST /api/lifesim/choice via the freshly generated
 * SDK. Iteration A8 wires the Crystal Shop.
 *
 * Constitution compliance:
 *  • Law 1 (no red) — all states use accent/muted, never destructive color
 *  • Law 2 (energy modes) — minimal layout already adapts to low-energy users
 *  • Law 3 (shame-free copy) — empty state frames as "ready for first chapter"
 */

type StatKey = "health" | "happiness" | "energy" | "intelligence" | "social" | "money";

interface StatRow {
  key: StatKey;
  icon: React.ComponentType<{ className?: string }>;
  value: number;
  max: number;
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

function StatBar({ row, t }: { row: StatRow; t: (k: string, o?: Record<string, unknown>) => string }) {
  const Icon = row.icon;
  const pct = row.key === "money"
    ? Math.min(100, Math.max(0, (row.value / 9999) * 100))
    : Math.min(100, Math.max(0, (row.value / row.max) * 100));
  const displayValue = row.key === "money" ? row.value.toLocaleString() : String(Math.round(row.value));

  return (
    <div className="flex items-center gap-3" role="group" aria-label={t(`lifesim.stat.${row.key}`, { defaultValue: row.key })}>
      <Icon className="size-5 shrink-0 text-muted-foreground" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2 mb-1">
          <span className="text-xs font-medium text-on-surface-variant">
            {t(`lifesim.stat.${row.key}`, { defaultValue: row.key })}
          </span>
          <span className="text-xs font-semibold tabular-nums">{displayValue}</span>
        </div>
        <div
          className="h-1.5 rounded-full bg-surface-container overflow-hidden"
          role="progressbar"
          aria-valuenow={Math.round(row.value)}
          aria-valuemin={0}
          aria-valuemax={row.key === "money" ? 9999 : 100}
        >
          <div
            className="h-full rounded-full bg-primary/70 transition-all duration-500 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default function LifeFeedPage() {
  const { t } = useTranslation();
  const prefersReducedMotion = useReducedMotion();

  // MVP: stats are client-side placeholder. A7 will pull from GET /api/character/events
  // aggregate + VOLAURA verified-skills boosts via apply_stat_boosts_from_verified_skills.
  const [stats] = useState<Record<StatKey, number>>(INITIAL_STATS);

  const statRows: StatRow[] = (
    ["health", "happiness", "energy", "intelligence", "social", "money"] as StatKey[]
  ).map((k) => ({ key: k, icon: STAT_ICONS[k], value: stats[k], max: 100 }));

  const sectionVariants = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 12 },
    visible: { opacity: 1, y: 0 },
  };

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
          {/* Stats sidebar */}
          <motion.aside
            initial="hidden"
            animate="visible"
            variants={sectionVariants}
            transition={{ duration: 0.35, delay: 0.05 }}
            className={cn(
              "rounded-xl border border-border bg-card p-5",
              "h-fit lg:sticky lg:top-24"
            )}
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
                <StatBar key={row.key} row={row} t={t} />
              ))}
            </div>
          </motion.aside>

          {/* Feed / empty state */}
          <motion.section
            initial="hidden"
            animate="visible"
            variants={sectionVariants}
            transition={{ duration: 0.35, delay: 0.1 }}
            className="min-h-[400px]"
            aria-label={t("lifesim.feed.title", { defaultValue: "Life feed" })}
          >
            <div
              className={cn(
                "rounded-xl border border-dashed border-border bg-card/50",
                "flex flex-col items-center justify-center text-center",
                "px-6 py-16 min-h-[400px]"
              )}
              role="status"
            >
              <Sparkles className="size-10 text-primary/60 mb-4" aria-hidden="true" />
              <h2 className="text-lg font-semibold text-foreground mb-2">
                {t("lifesim.emptyState.title", {
                  defaultValue: "Твоя первая глава ждёт",
                })}
              </h2>
              <p className="text-sm text-muted-foreground max-w-md mb-6">
                {t("lifesim.emptyState.body", {
                  defaultValue:
                    "Пройди хотя бы один assessment в VOLAURA — и сюда прилетит первое событие, в котором нужно будет сделать выбор.",
                })}
              </p>
              <span className="text-xs text-muted-foreground/70 font-mono">
                {t("lifesim.emptyState.hint", {
                  defaultValue: "MVP preview — live pool wire coming in next iteration",
                })}
              </span>
            </div>
          </motion.section>
        </div>
      </main>
    </div>
  );
}
