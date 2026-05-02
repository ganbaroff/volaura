"use client";

import { useEffect, useState, useRef } from "react";
import { useFocusTrap } from "@/hooks/use-focus-trap";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { TopBar } from "@/components/layout/top-bar";
import { AuraRadarChart } from "@/components/aura/radar-chart";
import { LiquidGlassRadar } from "@/components/aura/liquid-glass-radar";
import { BadgeDisplay } from "@/components/aura/badge-display";
import { CompetencyBreakdown } from "@/components/aura/competency-breakdown";
import { ShareButtons } from "@/components/aura/share-buttons";
import { Button } from "@/components/ui/button";
import { Clock, RefreshCw, Sparkles } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuraScore } from "@/hooks/queries/use-aura";
import { useProfile } from "@/hooks/queries/use-profile";
import { useAssessmentStore } from "@/stores/assessment-store";
import { useSkill } from "@/hooks/queries/use-skill";
import { useReflection } from "@/hooks/queries/use-reflection";
import { ApiError } from "@/lib/api/client";
import { EvaluationLog } from "@/components/aura/evaluation-log";
import { triggerHaptic } from "@/lib/haptics";
import { useTrackEvent } from "@/hooks/use-analytics";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import { buildLoginNextPath } from "../auth-recovery";

// ── Animated counter hook ────────────────────────────────────────────────

function useAnimatedCounter(target: number, duration = 800, enabled = true) {
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
  else if (score > 0) key = "aura.scoreMeaning_justStarting"; // completed assessment, low score
  else key = "aura.scoreMeaning_progress"; // score === 0 → no assessment yet

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
  const { t } = useTranslation();
  const prefersReducedMotion = useReducedMotion();
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: prefersReducedMotion ? 0 : 0.3 }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/95 backdrop-blur-sm"
      aria-live="polite"
      aria-label={t("aura.revealingAura")}
    >
      <motion.div
        animate={prefersReducedMotion ? {} : { scale: [1, 1.08, 1], opacity: [0.6, 1, 0.6] }}
        transition={prefersReducedMotion ? {} : { repeat: 5, duration: 1.4, ease: "easeInOut" }}
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

// ── AURA Coach ───────────────────────────────────────────────────────────

function AuraCoach({ output }: { output: string | Record<string, unknown> }) {
  const { t } = useTranslation();
  const text = typeof output === "string" ? output : JSON.stringify(output, null, 2);

  return (
    <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="size-4 text-primary" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
          {t("aura.coach.title", { defaultValue: "Your Growth Path" })}
        </h3>
      </div>
      <p className="text-sm text-foreground/80 whitespace-pre-line leading-relaxed">
        {text}
      </p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function AuraPage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language;
  const router = useRouter();
  const isMounted = useRef(true);
  const prefersReducedMotion = useReducedMotion(); // BATCH-O A11Y: respect user motion preference
  const activeSessionId = useAssessmentStore((s) => s.sessionId); // BATCH-O AU2: route Continue to active session
  const track = useTrackEvent();
  const { energy } = useEnergyMode();
  const isLowEnergy = energy === "low";
  const isReducedEnergy = energy === "low" || energy === "mid";
  const reauthPath = buildLoginNextPath(locale, `/${locale}/aura`);

  // Reveal sequence — fires exactly once per mount
  const revealFiredRef = useRef(false);
  const [showCurtain, setShowCurtain] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [showSharePrompt, setShowSharePrompt] = useState(false);
  const shareDialogRef = useFocusTrap<HTMLDivElement>(showSharePrompt);

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

  const { data: reflectionText, isLoading: reflectionLoading } = useReflection(
    revealed && aura != null && (aura.total_score ?? 0) > 0,
  );

  const { data: coachData, isLoading: coachLoading } = useSkill(
    "aura-coach",
    { language: locale },
    { enabled: revealed && aura != null && (aura.total_score ?? 0) > 0, staleTime: 10 * 60 * 1000 },
  );

  // Trigger reveal sequence once data is ready
  useEffect(() => {
    if (!aura || aura.total_score == null) return;
    if (revealFiredRef.current) return;
    revealFiredRef.current = true;
    track("aura_page_viewed", {
      total_score: aura.total_score,
      badge_tier: aura.badge_tier,
    });

    if (!isMounted.current) return;

    // BUG-GROWTH-6 FIX: use localStorage to skip curtain animation on revisits.
    // Key includes score value — animation re-fires only when score actually changes.
    const revealKey = `aura_reveal_shown_${Math.round(aura.total_score)}`;
    const alreadyRevealed = typeof localStorage !== "undefined" && localStorage.getItem(revealKey);

    if (alreadyRevealed) {
      // Revisit: skip animation, show score immediately
      setRevealed(true);
      triggerHaptic("task_complete"); // Subtle confirmation — not the full reveal sequence
      return;
    }

    // First time seeing this score — run full reveal animation
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(revealKey, "1");
    }

    setShowCurtain(true);

    // Hold curtain for 800ms (300ms fade-in + 500ms hold), then reveal
    const curtainTimer = setTimeout(() => {
      if (!isMounted.current) return;
      setShowCurtain(false);
      // Small gap for curtain exit animation, then reveal content
      setTimeout(() => {
        if (!isMounted.current) return;
        setRevealed(true);
        triggerHaptic("badge_reveal"); // First-time AURA reveal — dramatic crescendo pattern
        // BUG-GROWTH-7 FIX: share prompt resets after 24h (not just once per session).
        // Uses localStorage timestamp — survives tab close, resets daily.
        const shareKey = "aura_share_prompted_at";
        const tsStr = typeof localStorage !== "undefined" ? localStorage.getItem(shareKey) : null;
        const shouldShowPrompt = !tsStr || (Date.now() - parseInt(tsStr, 10)) > 24 * 60 * 60 * 1000;
        if (shouldShowPrompt) {
          setTimeout(() => {
            if (!isMounted.current) return;
            setShowSharePrompt(true);
            if (typeof localStorage !== "undefined") {
              localStorage.setItem(shareKey, Date.now().toString());
            }
          }, 5000); // BATCH-O AU4: delay past counter animation (2000ms) + reveal sequence (~2.5s total)
        }
      }, 350);
    }, 800);

    return () => clearTimeout(curtainTimer);
  }, [aura, track]);

  // Use effective (decay-adjusted) score when available, fallback to raw total.
  // !== null check instead of ?? because effective_score can be 0 (valid after
  // full decay to floor), and ?? would skip it for the raw total_score.
  const displayScore = aura?.effective_score !== null && aura?.effective_score !== undefined
    ? aura.effective_score
    : aura?.total_score ?? 0;

  // Counter only runs once reveal is complete; skip animation if user prefers reduced motion
  const animatedScore = useAnimatedCounter(
    displayScore,
    prefersReducedMotion ? 0 : 800,
    revealed
  );

  // Handle 401
  useEffect(() => {
    if (
      auraError instanceof ApiError &&
      auraError.status === 401 &&
      isMounted.current
    ) {
      router.replace(reauthPath);
    }
  }, [auraError, reauthPath, router]);

  // Close share prompt on Escape key (accessibility: keyboard dismiss)
  useEffect(() => {
    if (!showSharePrompt) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowSharePrompt(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [showSharePrompt]);

  // ── Loading ──

  if (auraLoading) {
    // BATCH-O A11Y #5: skeleton layout matches page structure — no bare spinner
    return (
      <>
        <TopBar title={t("aura.title")} />
        <div className="p-4 space-y-5 pb-8" aria-busy="true" aria-label={t("common.loading")}>
          {/* Score header skeleton */}
          <div className="rounded-2xl border border-border bg-card p-6 space-y-3">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-14 w-32" />
            <Skeleton className="h-5 w-20" />
          </div>
          {/* Radar skeleton */}
          <Skeleton className="h-[300px] w-full rounded-2xl" />
          {/* Competency bars skeleton */}
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-1.5">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-2 w-full" />
              </div>
            ))}
          </div>
        </div>
      </>
    );
  }

  // ── Error state ──

  if (auraError && !(auraError instanceof ApiError && (auraError.status === 401 || auraError.status === 404))) {
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

  // ── AURA-02: Distinguish "never started" (!aura) from "in progress" (aura exists, score null) ──

  if (!aura) {
    // No AURA record at all — user has never started an assessment
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
          {/* T1-6: identity aspiration — empty state lacked pull, only had push. */}
          <p className="text-sm font-medium text-primary max-w-xs">
            {t("aura.emptyAspiration")}
          </p>
          <Button asChild size="lg" className="mt-2">
            <Link href={`/${locale}/assessment`}>{t("aura.startAssessment")}</Link>
          </Button>
        </div>
      </>
    );
  }

  if (aura.total_score == null) {
    // AURA record exists but score not yet finalized — assessment is in progress
    return (
      <>
        <TopBar title={t("aura.title")} />
        <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
          <div className="size-16 rounded-full bg-muted/40 flex items-center justify-center">
            <Clock className="size-8 text-muted-foreground" aria-hidden="true" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">
            {t("aura.assessmentInProgress")}
          </h2>
          <p className="text-sm text-muted-foreground max-w-xs">
            {t("aura.assessmentInProgressDesc")}
          </p>
          <Button asChild size="lg" className="mt-2">
            {/* BATCH-O AU2: if Zustand has active sessionId, resume it — don't create a new session */}
            <Link href={activeSessionId ? `/${locale}/assessment/${activeSessionId}` : `/${locale}/assessment`}>
              {t("assessment.infoContinueButton")}
            </Link>
          </Button>
        </div>
      </>
    );
  }

  // ── Score view ──

  const tierLabel = t(`aura.${aura.badge_tier}`, { defaultValue: aura.badge_tier });

  return (
    <>
      {/* Reveal curtain — appears over the full page on first load (skip in mid/low energy) */}
      <AnimatePresence>{showCurtain && !isReducedEnergy && <RevealCurtain />}</AnimatePresence>

      <TopBar title={t("aura.title")} />

      <div className="mx-auto max-w-2xl p-6 space-y-8">
        {/* Score + Badge header */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: revealed ? 1 : 0, x: revealed ? 0 : -20 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between sm:gap-6"
        >
          <div className="min-w-0">
            <p className="text-sm text-muted-foreground">{t("aura.overallScore")}</p>
            <p
              className="text-5xl sm:text-6xl font-black tabular-nums text-foreground"
              aria-label={`${t("aura.overallScore")}: ${displayScore.toFixed(1)}`}
            >
              {(animatedScore ?? 0).toFixed(1)}
            </p>
            <ScoreMeaning score={displayScore} />
            {(() => {
              const assessed = Object.keys(aura.competency_scores ?? {}).length;
              const total = 8;
              if (assessed < total) {
                return (
                  <p className="text-xs text-muted-foreground mt-1.5">
                    {t("aura.competenciesAssessed", {
                      assessed,
                      total,
                      defaultValue: `${assessed} of ${total} competencies assessed`,
                    })}
                    {assessed < 3 && (
                      <span className="block mt-0.5 text-primary/80">
                        {t("aura.assessMoreForFullScore", {
                          defaultValue: "Complete more to build your full AURA score",
                        })}
                      </span>
                    )}
                  </p>
                );
              }
              return null;
            })()}
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
              settingsUrl={`/${locale}/settings`}
            />
          </motion.div>
        )}

        {/* Share prompt modal — fires 3s after first reveal (Product Agent recommendation) */}
        <AnimatePresence>
          {showSharePrompt && profile && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
              onClick={() => setShowSharePrompt(false)}
            >
              <motion.div
                ref={shareDialogRef}
                role="dialog"
                aria-modal="true"
                aria-label={t("aura.sharePromptTitle", { defaultValue: "Share your AURA score" })}
                initial={{ y: 40, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 40, opacity: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="w-full max-w-sm rounded-2xl bg-card border border-border p-6 space-y-4 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="text-center space-y-1">
                  <p className="text-lg font-bold text-foreground">
                    {t("aura.sharePromptTitle", { defaultValue: "Your AURA score is live." })}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {t("aura.sharePromptBody", { defaultValue: "Share it so organizations can find you." })}
                  </p>
                </div>
                <ShareButtons
                  username={profile.username}
                  overallScore={aura.total_score}
                  badgeTier={aura.badge_tier}
                />
                <button
                  onClick={() => setShowSharePrompt(false)}
                  className="w-full text-sm text-muted-foreground hover:text-foreground transition-colors py-1"
                >
                  {t("common.dismiss", { defaultValue: "Dismiss" })}
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Savant Discovery — hidden strength card (hidden in low energy) */}
        {!isLowEnergy && aura.competency_scores && (
          <SavantDiscovery
            competencyScores={aura.competency_scores}
            revealed={revealed}
          />
        )}

        {/* Liquid Glass Radar — identity-first hero (Constitution Law 3, 5) */}
        {revealed && aura.competency_scores && (
          <LiquidGlassRadar
            competencyScores={aura.competency_scores}
            totalScore={displayScore}
            badgeTier={aura.badge_tier}
            displayName={profile?.display_name ?? profile?.username ?? ""}
            ctaLabel={t("aura.retake", { defaultValue: "Retake Assessment" })}
            onCtaClick={() => router.push(`/${locale}/assessment`)}
          />
        )}

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
          <CompetencyBreakdown scores={aura.competency_scores} lastUpdated={aura.last_updated} isOwner />
        </motion.div>

        {/* AURA Coach — personalized growth path (hidden in low energy) */}
        {!isLowEnergy && revealed && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.5 }}
          >
            {coachLoading ? (
              <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : coachData?.output ? (
              <AuraCoach output={coachData.output} />
            ) : null}
          </motion.div>
        )}

        {/* Atlas Reflection — personalized narrative from LLM (hidden in low energy) */}
        {!isLowEnergy && revealed && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.5 }}
          >
            {reflectionLoading ? (
              <div className="rounded-xl border border-border bg-surface-container-low p-5 space-y-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : reflectionText ? (
              <div className="rounded-xl border border-border bg-surface-container-low p-5 space-y-2">
                <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                  {t("aura.reflectionTitle", { defaultValue: "Atlas says" })}
                </p>
                <p className="text-sm text-foreground/90 leading-relaxed italic">
                  {reflectionText}
                </p>
              </div>
            ) : null}
          </motion.div>
        )}

        {/* Why this score? — Evaluation Log (hidden in low energy) */}
        {!isLowEnergy && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: revealed ? 1 : 0, y: revealed ? 0 : 16 }}
            transition={{ delay: 0.65, duration: 0.5 }}
          >
            <EvaluationLog />
          </motion.div>
        )}

        {/* ISSUE-AU3: NextStepCard — what to do after seeing AURA score */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: revealed ? 1 : 0, y: revealed ? 0 : 16 }}
          transition={{ delay: 0.75, duration: 0.5 }}
          className="space-y-3 pb-6"
        >
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            {t("aura.nextSteps", { defaultValue: "Keep Going" })}
          </h2>
          <div className="space-y-2">
            {/* Assess more competencies */}
            <button
              type="button"
              onClick={() => router.push(`/${locale}/assessment`)}
              className="w-full flex items-center gap-3 rounded-xl bg-surface-container-low p-3 text-left hover:bg-muted/30 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <span className="text-2xl shrink-0" aria-hidden="true">🎯</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-foreground">{t("aura.nextStepAssess")}</p>
                <p className="text-xs text-muted-foreground">{t("aura.nextStepAssessDesc")}</p>
              </div>
              <span className="text-muted-foreground shrink-0" aria-hidden="true">→</span>
            </button>
            {/* Leaderboard CTA removed 2026-04-12 — Constitution v1.7 G9/G46 bans leaderboards.
                The page itself is already a redirect to /dashboard. This tombstone prevents
                future re-introduction. See docs/ECOSYSTEM-CONSTITUTION.md lines 967, 1004. */}
          </div>

          {/* Grievance link — ISO 10667-2 §7 / Constitution G35. Quiet, not a primary CTA. */}
          <div className="pt-4 border-t border-border/40">
            <Link
              href={`/${locale}/aura/contest`}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors underline-offset-2 hover:underline"
            >
              {t("aura.contestLink", { defaultValue: "Does this score feel off? Request a review." })}
            </Link>
          </div>
        </motion.div>
      </div>
    </>
  );
}
