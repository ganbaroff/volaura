"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { TopBar } from "@/components/layout/top-bar";
import { AuraRadarChart } from "@/components/aura/radar-chart";
import { BadgeDisplay } from "@/components/aura/badge-display";
import { CompetencyBreakdown } from "@/components/aura/competency-breakdown";
import { ShareButtons } from "@/components/aura/share-buttons";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useAuraScore } from "@/hooks/queries/use-aura";
import { useProfile } from "@/hooks/queries/use-profile";
import { ApiError } from "@/lib/api/client";
import { EvaluationLog } from "@/components/aura/evaluation-log";

// ── Animated counter hook ────────────────────────────────────────────────

function useAnimatedCounter(target: number, duration = 1200) {
  const [value, setValue] = useState(0);
  const startTime = useRef<number | null>(null);
  const animFrameRef = useRef<number>(0);

  useEffect(() => {
    if (target <= 0) return;

    const animate = (timestamp: number) => {
      if (!startTime.current) startTime.current = timestamp;
      const elapsed = timestamp - startTime.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target * 10) / 10);

      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        setValue(target);
      }
    };

    startTime.current = null;
    animFrameRef.current = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animFrameRef.current);
  }, [target, duration]);

  return value;
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function AuraPage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language;
  const router = useRouter();
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const {
    data: aura,
    isLoading: auraLoading,
    error: auraError,
    refetch: refetchAura,
  } = useAuraScore();

  const { data: profile } = useProfile();

  const animatedScore = useAnimatedCounter(aura?.total_score ?? 0);

  // Handle 401
  useEffect(() => {
    if (auraError instanceof ApiError && auraError.status === 401 && isMounted.current) {
      router.replace(`/${locale}/login`);
    }
  }, [auraError, locale, router]);

  // ── Loading ──

  if (auraLoading) {
    return (
      <>
        <TopBar title={t("aura.title")} />
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="size-8 animate-spin text-primary" aria-label={t("common.loading")} />
        </div>
      </>
    );
  }

  // ── Error state ──

  if (auraError && !(auraError instanceof ApiError && auraError.status === 401)) {
    return (
      <>
        <TopBar title={t("aura.title")} />
        <div className="flex flex-col items-center justify-center h-64 gap-3 text-center p-6">
          <p className="text-sm text-muted-foreground">{t("error.generic")}</p>
          <button
            onClick={() => refetchAura()}
            className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
          >
            <RefreshCw className="size-3.5" aria-hidden="true" />
            {t("error.retry")}
          </button>
        </div>
      </>
    );
  }

  // ── Empty state — also catches aura record with no total_score yet ──

  if (!aura || aura.total_score == null) {
    return (
      <>
        <TopBar title={t("aura.title")} />
        <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
          <div className="size-16 rounded-full bg-muted/40 flex items-center justify-center">
            <span className="text-3xl text-muted-foreground" aria-hidden="true">◈</span>
          </div>
          <h2 className="text-xl font-semibold text-foreground">
            {t("aura.noScoreYet")}
          </h2>
          <p className="text-sm text-muted-foreground max-w-xs">
            {t("aura.noScoreDescription")}
          </p>
          <Button asChild size="lg" className="mt-2">
            <a href={`/${locale}/assessment`}>{t("aura.startAssessment")}</a>
          </Button>
        </div>
      </>
    );
  }

  // ── Score view ──

  const tierLabel = t(`aura.${aura.badge_tier}`, { defaultValue: aura.badge_tier });

  return (
    <>
      <TopBar title={t("aura.title")} />
      <div className="mx-auto max-w-2xl p-6 space-y-8">
        {/* Score + Badge header */}
        <div className="flex items-center justify-between gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <p className="text-sm text-muted-foreground">{t("aura.overallScore")}</p>
            <p
              className="text-6xl font-black tabular-nums text-foreground"
              aria-label={`${t("aura.overallScore")}: ${(aura.total_score ?? 0).toFixed(1)}`}
            >
              {(animatedScore ?? 0).toFixed(1)}
            </p>
          </motion.div>

          <BadgeDisplay
            tier={aura.badge_tier}
            label={tierLabel}
            eliteLabel={t("aura.elite")}
            isElite={aura.is_elite}
          />
        </div>

        {/* Radar chart */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="rounded-xl border border-border bg-card p-4"
        >
          <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            {t("aura.competencyRadar")}
          </h3>
          <AuraRadarChart
            competencyScores={aura.competency_scores}
            badgeTier={aura.badge_tier}
            size="md"
          />
        </motion.div>

        {/* Competency breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="rounded-xl border border-border bg-card p-4"
        >
          <h3 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            {t("aura.breakdown")}
          </h3>
          <CompetencyBreakdown scores={aura.competency_scores} />
        </motion.div>

        {/* Why this score? — Evaluation Log */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65, duration: 0.5 }}
        >
          <EvaluationLog />
        </motion.div>

        {/* Share */}
        {profile && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.5 }}
            className="rounded-xl border border-border bg-card p-4 space-y-3"
          >
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              {t("aura.share")}
            </h3>
            <ShareButtons
              username={profile.username}
              overallScore={aura.total_score}
              badgeTier={aura.badge_tier}
            />
          </motion.div>
        )}
      </div>
    </>
  );
}
