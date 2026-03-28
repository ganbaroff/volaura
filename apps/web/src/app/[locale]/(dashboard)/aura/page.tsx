"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { TopBar } from "@/components/layout/top-bar";
import { AuraRadarChart } from "@/components/aura/radar-chart";
import { BadgeDisplay } from "@/components/aura/badge-display";
import { CompetencyBreakdown } from "@/components/aura/competency-breakdown";
import { ShareButtons } from "@/components/aura/share-buttons";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw } from "lucide-react";
import { useAuraScore } from "@/hooks/queries/use-aura";
import { useProfile } from "@/hooks/queries/use-profile";
import { ApiError } from "@/lib/api/client";
import { EvaluationLog } from "@/components/aura/evaluation-log";

// ── Animated counter hook ────────────────────────────────────────────────

function useAnimatedCounter(target: number, duration = 1200, enabled = true) {
  const [value, setValue] = useState(0);
  const startTime = useRef<number | null>(null);
  const animFrameRef = useRef<number>(0);

  useEffect(() => {
    if (!enabled || target <= 0) return;

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
  }, [target, duration, enabled]);

  return value;
}

// ── Score meaning line ───────────────────────────────────────────────────

function ScoreMeaning({ score }: { score: number }) {
  const { t } = useTranslation();
  let key: string;
  if (score >= 90) key = "aura.scoreMeaning_top5";
  else if (score >= 75) key = "aura.scoreMeaning_above";
  else if (score >= 60) key = "aura.scoreMeaning_foundation";
  else key = "aura.scoreMeaning_progress";

  return (
    <p className="text-sm text-muted-foreground mt-1 font-medium">{t(key)}</p>
  );
}

// ── Savant Discovery ─────────────────────────────────────────────────────

interface SavantDiscoveryProps {
  competencyScores: Record<string, number>;
  revealed: boolean;
}

function SavantDiscovery({ competencyScores, revealed }: SavantDiscoveryProps) {
  const { t } = useTranslation();

  const entries = Object.entries(competencyScores);
  if (entries.length === 0) return null;

  const [topSlug, topScore] = entries.reduce<[string, number]>(
    (best, [slug, score]) => (score > best[1] ? [slug, score] : best),
    ["", -Infinity]
  );

  if (topScore < 75) return null;

  const competencyLabel = t(`competency.${topSlug}`, { defaultValue: topSlug });

  return (
    <AnimatePresence>
      {revealed && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ delay: 0.6, duration: 0.4, ease: "easeOut" }}
          className="rounded-2xl border border-primary/30 bg-primary/5 p-4 flex items-start gap-4"
        >
          <span className="text-2xl mt-0.5" aria-hidden="true">🔍</span>
          <div>
            <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-semibold">
              {t("aura.hiddenStrengthLabel")}
            </p>
            <p className="text-base font-bold text-foreground">
              {competencyLabel}: {Math.round(topScore)}/100
            </p>
            <p className="text-sm text-muted-foreground mt-0.5">
              {t("aura.hiddenStrengthDesc")}
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ── Reveal Curtain ───────────────────────────────────────────────────────

function RevealCurtain() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/95 backdrop-blur-sm"
      aria-live="polite"
      aria-label="Revealing your AURA score"
    >
      <motion.div
        animate={{ scale: [1, 1.08, 1], opacity: [0.6, 1, 0.6] }}
        transition={{ repeat: Infinity, duration: 1.4, ease: "easeInOut" }}
        className="text-6xl mb-6"
        aria-hidden="true"
      >
        ◈
      </motion.div>
      <p className="text-base font-semibold text-foreground tracking-wide">
        {t("aura.revealingAura")}
      </p>
    </motion.div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function AuraPage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language;
  const router = useRouter();
  const isMounted = useRef(true);

  // Reveal sequence — fires exactly once per mount
  const revealFiredRef = useRef(false);
  const [showCurtain, setShowCurtain] = useState(false);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const {
    data: aura,
    isLoading: auraLoading,
    error: auraError,
    refetch: refetchAura,
  } = useAuraScore();

  const { data: profile } = useProfile();

  // Trigger reveal sequence once data is ready
  useEffect(() => {
    if (!aura || aura.total_score == null) return;
    if (revealFiredRef.current) return;
    revealFiredRef.current = true;

    if (!isMounted.current) return;
    setShowCurtain(true);

    // Hold curtain for 800ms (300ms fade-in + 500ms hold), then reveal
    const curtainTimer = setTimeout(() => {
      if (!isMounted.current) return;
      setShowCurtain(false);
      // Small gap for curtain exit animation, then reveal content
      setTimeout(() => {
        if (!isMounted.current) return;
        setRevealed(true);
      }, 350);
    }, 800);

    return () => clearTimeout(curtainTimer);
  }, [aura]);

  // Counter only runs once reveal is complete, with slower 2s drama
  const animatedScore = useAnimatedCounter(
    aura?.total_score ?? 0,
    2000,
    revealed
  );

  // Handle 401
  useEffect(() => {
    if (
      auraError instanceof ApiError &&
      auraError.status === 401 &&
      isMounted.current
    ) {
      router.replace(`/${locale}/login`);
    }
  }, [auraError, locale, router]);

  // ── Loading ──

  if (auraLoading) {
    return (
      <>
        <TopBar title={t("aura.title")} />
        <div className="flex h-64 items-center justify-center">
          <Loader2
            className="size-8 animate-spin text-primary"
            aria-label={t("common.loading")}
          />
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
            <span className="text-3xl text-muted-foreground" aria-hidden="true">
              ◈
            </span>
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
      {/* Reveal curtain — appears over the full page on first load */}
      <AnimatePresence>{showCurtain && <RevealCurtain />}</AnimatePresence>

      <TopBar title={t("aura.title")} />

      <div className="mx-auto max-w-2xl p-6 space-y-8">
        {/* Score + Badge header */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: revealed ? 1 : 0, x: revealed ? 0 : -20 }}
          transition={{ duration: 0.5 }}
          className="flex items-start justify-between gap-6"
        >
          <div>
            <p className="text-sm text-muted-foreground">{t("aura.overallScore")}</p>
            <p
              className="text-6xl font-black tabular-nums text-foreground"
              aria-label={`${t("aura.overallScore")}: ${(aura.total_score ?? 0).toFixed(1)}`}
            >
              {(animatedScore ?? 0).toFixed(1)}
            </p>
            <ScoreMeaning score={aura.total_score} />
          </div>

          {/* Badge with spring overshoot on reveal */}
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={
              revealed
                ? { scale: [0, 1.15, 1], opacity: 1 }
                : { scale: 0, opacity: 0 }
            }
            transition={{
              scale: { duration: 0.55, ease: [0.34, 1.56, 0.64, 1] },
              opacity: { duration: 0.2 },
            }}
          >
            {/* Glow burst on badge reveal */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={revealed ? { opacity: [0, 0.6, 0] } : { opacity: 0 }}
              transition={{ delay: 0.1, duration: 0.7 }}
              className="absolute inset-0 rounded-full blur-xl bg-primary/40 pointer-events-none"
              aria-hidden="true"
            />
            <BadgeDisplay
              tier={aura.badge_tier}
              label={tierLabel}
              eliteLabel={t("aura.elite")}
              isElite={aura.is_elite}
            />
          </motion.div>
        </motion.div>

        {/* Share — visual section header makes buttons discoverable (Leyla test: buttons missed without heading) */}
        {profile && revealed && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.4 }}
            className="space-y-2"
          >
            <p className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider">
              {t("aura.share")}
            </p>
            <ShareButtons
              username={profile.username}
              overallScore={aura.total_score}
              badgeTier={aura.badge_tier}
            />
          </motion.div>
        )}

        {/* Savant Discovery — hidden strength card */}
        {aura.competency_scores && (
          <SavantDiscovery
            competencyScores={aura.competency_scores}
            revealed={revealed}
          />
        )}

        {/* Radar chart */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: revealed ? 1 : 0, y: revealed ? 0 : 16 }}
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
          animate={{ opacity: revealed ? 1 : 0, y: revealed ? 0 : 16 }}
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
          animate={{ opacity: revealed ? 1 : 0, y: revealed ? 0 : 16 }}
          transition={{ delay: 0.65, duration: 0.5 }}
        >
          <EvaluationLog />
        </motion.div>
      </div>
    </>
  );
}
