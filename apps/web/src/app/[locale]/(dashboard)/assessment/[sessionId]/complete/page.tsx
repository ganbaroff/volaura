"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { useTrackEvent } from "@/hooks/use-analytics";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Loader2,
  Share2,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  ListChecks,
  Clock,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api/client";
import { CoachingTips } from "@/components/assessment/coaching-tips";
import { triggerHaptic } from "@/lib/haptics";
import { getAchievementLevelKey } from "@/lib/utils/achievement-level";

// ── Types ──────────────────────────────────────────────────────────────

interface AssessmentResult {
  session_id: string;
  competency_slug: string;
  competency_score: number;
  questions_answered: number;
  stop_reason: string | null;
  aura_updated: boolean;
  gaming_flags: string[];
  completed_at: string | null;
  crystals_earned?: number;
}

interface AuraScore {
  total_score: number;
  badge_tier: string;
  elite_status: boolean;
  competency_scores: Record<string, number>;
  percentile_rank: number | null;
  effective_score: number | null;
}

// ── Gaming flag code → i18n key mapping ───────────────────────────────

const GAMING_FLAG_KEYS: Record<string, string> = {
  excessive_rushing:          "assessment.gamingFlag.excessiveRushing",
  alternating_pattern:        "assessment.gamingFlag.alternatingPattern",
  group_alternating_pattern:  "assessment.gamingFlag.groupAlternatingPattern",
  all_identical_responses:    "assessment.gamingFlag.allIdenticalResponses",
  time_clustering:            "assessment.gamingFlag.timeClustering",
  excessive_slowness:         "assessment.gamingFlag.excessiveSlowness",
};

// ── GamingFlagsWarning component ───────────────────────────────────────

function GamingFlagsWarning({ flags }: { flags: string[] }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);

  if (flags.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="rounded-xl bg-amber-500/10 border border-amber-500/30 overflow-hidden"
    >
      {/* Header — always visible */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-start gap-3 p-4 text-left"
        aria-expanded={expanded}
      >
        <AlertTriangle className="size-4 mt-0.5 shrink-0 text-amber-400" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-amber-300">
            {t("assessment.scoringAdjusted")}
          </p>
          <p className="text-xs text-amber-200/80 mt-0.5">
            {t("assessment.scoringAdjustedDesc")}
          </p>
        </div>
        {expanded ? (
          <ChevronUp className="size-4 mt-0.5 shrink-0 text-amber-400" aria-hidden="true" />
        ) : (
          <ChevronDown className="size-4 mt-0.5 shrink-0 text-amber-400" aria-hidden="true" />
        )}
      </button>

      {/* Expanded flag list */}
      {expanded && (
        <div className="px-4 pb-4 space-y-1">
          {flags.map((flag) => {
            const key = GAMING_FLAG_KEYS[flag];
            const label = key
              ? t(key, { defaultValue: flag.replace(/_/g, " ") })
              : flag.replace(/_/g, " ");
            return (
              <div key={flag} className="flex items-center gap-2 text-xs text-amber-200/80">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                {label}
              </div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}

// ── Animated counter ───────────────────────────────────────────────────

// NOTE: Tier identity reveal removed from this page per Crystal Law 6 Amendment
// + G21 (vulnerability window rule). Badge tier and crystal rewards are deferred
// to the next AURA page visit so users don't see emotionally loaded status
// feedback at the moment they complete an assessment. The "View AURA score" card
// (below) routes them there when they choose to look.

function useAnimatedCounter(target: number, duration = 800) {
  const [value, setValue] = useState(0);
  const startTime = useRef<number | null>(null);
  const raf = useRef<number>(0);

  useEffect(() => {
    if (target <= 0) return;
    const animate = (ts: number) => {
      if (!startTime.current) startTime.current = ts;
      const progress = Math.min((ts - startTime.current) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target * 10) / 10);
      if (progress < 1) raf.current = requestAnimationFrame(animate);
      else setValue(target);
    };
    startTime.current = null;
    raf.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration]);

  return value;
}

// ── Page Props ─────────────────────────────────────────────────────────

// ── Page ───────────────────────────────────────────────────────────────

export default function AssessmentResultsPage() {
  const { locale, sessionId } = useParams<{ locale: string; sessionId: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();
  const queryClient = useQueryClient();
  const isMounted = useRef(true);

  const track = useTrackEvent();

  const [phase, setPhase] = useState<"loading" | "reveal" | "error">("loading");
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [aura, setAura] = useState<AuraScore | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const fetchResults = useCallback(async () => {
    try {
      setPhase("loading");
      setError(null);

      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      if (!token) {
        router.replace(`/${locale}/login`);
        return;
      }

      // 1. Complete the assessment (triggers AURA upsert)
      const assessmentResult = await apiFetch<AssessmentResult>(
        `/api/assessment/complete/${sessionId}`,
        { method: "POST", token }
      );

      if (!isMounted.current) return;
      setResult(assessmentResult);

      // 2. Fetch updated AURA score + username for share card
      try {
        const auraResult = await apiFetch<AuraScore>("/api/aura/me", { token });
        if (isMounted.current) setAura(auraResult);
      } catch {
        // AURA fetch failure is non-critical — results still show
      }
      try {
        const supabase2 = createClient();
        const { data: { user } } = await supabase2.auth.getUser();
        if (user) {
          const { data: profile } = await supabase2.from("profiles").select("username").eq("id", user.id).single();
          if (isMounted.current && profile?.username) setUsername(profile.username);
        }
      } catch {
        // username fetch failure is non-critical
      }

      // 3. Invalidate cached AURA score so dashboard refreshes
      queryClient.invalidateQueries({ queryKey: ["aura-score"] });

      // Track frontend assessment_completed (backend already tracks via analytics service)
      track("assessment_completed_view", {
        competency_slug: assessmentResult.competency_slug,
        competency_score: Math.round(assessmentResult.competency_score),
        questions_answered: assessmentResult.questions_answered,
        aura_updated: assessmentResult.aura_updated,
        has_gaming_flags: assessmentResult.gaming_flags.length > 0,
        crystals_earned: assessmentResult.crystals_earned ?? 0,
      }, sessionId);

      if (isMounted.current) {
        // Small delay for suspense effect, then reveal
        setTimeout(() => {
          if (isMounted.current) {
            setPhase("reveal");
            triggerHaptic("badge_reveal");
          }
        }, 800);
      }
    } catch (err: unknown) {
      if (!isMounted.current) return;
      const msg = err instanceof Error ? err.message : t("error.generic");
      setError(msg);
      setPhase("error");
    }
  }, [sessionId, locale, router, queryClient, t, track]);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // ── Derived values ───────────────────────────────────────────────────

  const score = result?.competency_score ?? 0;
  const animatedScore = useAnimatedCounter(phase === "reveal" ? score : 0);
  const overallAura = useAnimatedCounter(phase === "reveal" ? (aura?.total_score ?? 0) : 0, 800);
  const percentile = aura?.percentile_rank ?? null;
  const effectiveScore = aura?.effective_score ?? null;
  // Tier derivation intentionally removed — Crystal Law 6 Amendment defers
  // badge tier reveal to the next /aura page visit. See TIER_IDENTITY_KEYS
  // removal note above. Share-card emoji uses overall AURA score threshold
  // inline below, not a tier name, so we don't leak tier identity on this page.
  const hasGamingFlags = (result?.gaming_flags?.length ?? 0) > 0;

  const competencyLabel = result?.competency_slug
    ? t(`competency.${result.competency_slug}`, {
        defaultValue: result.competency_slug.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      })
    : "";

  // ── Loading state ────────────────────────────────────────────────────

  if (phase === "loading") {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 space-y-8" role="status" aria-live="polite">
        <div className="flex flex-col items-center text-center space-y-4">
          <Skeleton className="size-28 rounded-full" />
          <div className="space-y-2 w-full">
            <Skeleton className="h-3 w-24 mx-auto" />
            <Skeleton className="h-7 w-48 mx-auto" />
            <Skeleton className="h-10 w-20 mx-auto" />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-xl bg-surface-container-low p-3 space-y-2 flex flex-col items-center">
              <Skeleton className="h-7 w-12" />
              <Skeleton className="h-3 w-16" />
            </div>
          ))}
        </div>
        <div className="space-y-2 text-center">
          <Skeleton className="h-5 w-40 mx-auto" />
          <Skeleton className="h-4 w-56 mx-auto" />
        </div>
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────

  if (phase === "error") {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 flex flex-col items-center text-center space-y-6">
        <div className="size-16 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertTriangle className="size-8 text-destructive" />
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-semibold">{t("error.generic")}</h1>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
        <Button onClick={fetchResults} variant="outline">
          <RotateCcw className="size-4 mr-2" />
          {t("error.retry")}
        </Button>
      </div>
    );
  }

  // ── Results reveal ───────────────────────────────────────────────────

  return (
    <div className="mx-auto max-w-lg px-4 py-8 space-y-8">
      {/* Assessment Complete */}
      <motion.div
        initial={{ scale: 0, rotate: -20 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 180, damping: 16, delay: 0.1 }}
        className="flex flex-col items-center text-center space-y-4"
      >
        <div className="relative size-28 rounded-full flex items-center justify-center ring-4 bg-primary/10 ring-primary/20">
          <CheckCircle2 className="size-14 text-primary" />
          {score >= 75 && !prefersReducedMotion && (
            <motion.div
              initial={{ scale: 1, opacity: 0.7 }}
              animate={{ scale: 1.6, opacity: 0 }}
              transition={{ duration: 1.0, delay: 0.4, ease: "easeOut" }}
              className="absolute inset-0 rounded-full ring-4 bg-primary/10 pointer-events-none"
              aria-hidden="true"
            />
          )}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-1"
        >
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            {competencyLabel}
          </p>
          {/* Neutral completion headline — tier identity moved to /aura page per
              Crystal Law 6 Amendment. The competency just assessed stays visible
              as the subject of the completion, but no badge-tier naming. */}
          <h1 className="text-2xl font-bold text-foreground">
            {t("assessment.completeHeadline", {
              defaultValue: "Assessment complete",
            })}
          </h1>
          <p className="text-4xl font-bold tabular-nums text-muted-foreground mt-0.5">
            {animatedScore.toFixed(1)}
          </p>
          {/* BNE: strength-first framing — lead with what went well, regardless of score */}
          <p className="text-sm text-muted-foreground text-center mt-1">
            {score >= 75
              ? t("assessment.strengthExcellent", { competency: competencyLabel, defaultValue: `Strong ${competencyLabel} skills demonstrated` })
              : score >= 60
              ? t("assessment.strengthSolid", { competency: competencyLabel, defaultValue: `Solid ${competencyLabel} foundation` })
              : score >= 40
              ? t("assessment.strengthGrowing", { defaultValue: "You have a foundation to build on" })
              : t("assessment.strengthStart", { defaultValue: "This is your starting point — scores only go up from here" })}
          </p>
          {/* Effective score — shown only when decay reduces score by 2+ points */}
          {effectiveScore !== null && (aura?.total_score ?? 0) - effectiveScore >= 2 && (
            <p className="text-xs text-muted-foreground mt-1">
              {t("aura.effectiveScore", { defaultValue: "Effective (with inactivity decay):" })} {effectiveScore.toFixed(1)}
            </p>
          )}
          {/* Discoverability context line */}
          <p className="text-xs text-muted-foreground text-center mt-2">
            {score >= 60 && result?.aura_updated === true
              ? t("assessment.scoreUnlocksDiscovery")
              : t("assessment.scoreUnlocksMore")}
          </p>
        </motion.div>
      </motion.div>

      {/* Discoverability milestone — shown only if score unlocks org search, no badge tier revealed */}
      {result?.aura_updated && (aura?.total_score ?? 0) >= 60 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -6 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ delay: 0.38, type: "spring", stiffness: 200, damping: 22 }}
          className="rounded-xl border border-primary/30 bg-primary/5 p-4 text-center space-y-1"
          role="status"
          aria-live="polite"
        >
          <p className="text-base font-bold text-primary">
            {t("assessment.milestoneDiscoverable", { defaultValue: "You're now discoverable to organizations on Volaura." })}
          </p>
          <p className="text-xs text-muted-foreground">
            {t("assessment.visitAuraForDetails", { defaultValue: "Visit your AURA page to see what you've unlocked." })}
          </p>
        </motion.div>
      )}

      {/* Stats Row */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="grid grid-cols-3 gap-3"
      >
        <div className="rounded-xl bg-surface-container-low p-3 text-center">
          <p className="text-2xl font-bold tabular-nums">{result?.questions_answered ?? 0}</p>
          <p className="text-xs text-muted-foreground">{t("assessment.question", { count: result?.questions_answered ?? 0 })}</p>
        </div>
        <div className="rounded-xl bg-surface-container-low p-3 text-center">
          <p className="text-2xl font-bold tabular-nums">{overallAura.toFixed(1)}</p>
          <p className="text-xs text-muted-foreground">AURA</p>
        </div>
        <div className="rounded-xl bg-surface-container-low p-3 text-center">
          {percentile !== null ? (
            <>
              {/* CIS-001: Achievement level replaces "Top X%" — non-competitive framing for AZ/CIS users */}
              <p className="text-xl font-bold text-primary leading-tight">
                {t(getAchievementLevelKey(percentile))}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">{t("profile.achievementLabel")}</p>
            </>
          ) : (
            <>
              <p className="text-2xl font-bold tabular-nums flex items-center justify-center gap-1">
                <CheckCircle2 className="size-4 text-green-400" />
                {result?.aura_updated ? t("common.yes") : "—"}
              </p>
              <p className="text-xs text-muted-foreground">{t("aura.title")}</p>
            </>
          )}
        </div>
      </motion.div>

      {/* Growth trajectory with tier names intentionally removed here per
          Crystal Law 6 Amendment. The same progress-to-next-tier bar belongs on
          /aura where the user chooses to see badge context. The "View AURA score"
          card below is the deliberate handoff. */}

      {/* AURA Sync Pending Banner */}
      {result?.aura_updated === false && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3"
          role="status"
          aria-live="polite"
        >
          <Clock className="size-4 mt-0.5 shrink-0 text-amber-700 dark:text-amber-400" aria-hidden="true" />
          <p className="text-sm text-amber-700 dark:text-amber-400">
            {t("assessment.auraSyncPending")}
          </p>
        </motion.div>
      )}

      {/* Gaming Warning */}
      <AnimatePresence>
        {hasGamingFlags && (
          <GamingFlagsWarning flags={result?.gaming_flags ?? []} />
        )}
      </AnimatePresence>

      {/* Competency Breakdown (if AURA available) */}
      {aura && Object.keys(aura.competency_scores).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="space-y-3"
        >
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            {t("aura.competencies")}
          </h2>
          <div className="space-y-2">
            {Object.entries(aura.competency_scores).map(([slug, compScore]) => (
              <div key={slug} className="flex items-center gap-3">
                <span className="text-sm w-32 truncate capitalize">
                  {slug.replace(/_/g, " ")}
                </span>
                <div className="flex-1 h-2 rounded-full bg-muted/30 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(compScore, 100)}%` }}
                    transition={{ delay: 0.9, duration: 0.8, ease: "easeOut" }}
                    className={cn(
                      "h-full rounded-full",
                      compScore >= 90 ? "bg-violet-400" :
                      compScore >= 75 ? "bg-amber-400" :
                      compScore >= 60 ? "bg-slate-400" :
                      compScore >= 40 ? "bg-orange-400" :
                      "bg-muted-foreground"
                    )}
                  />
                </div>
                <span className="text-sm font-mono w-10 text-right tabular-nums">
                  {compScore.toFixed(0)}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Coaching Tips — moved UP per Leyla feedback (was buried below scroll) */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65 }}
          className="rounded-xl border border-border bg-card p-4"
        >
          <CoachingTips
            sessionId={sessionId}
            competencyId={result.competency_slug}
            score={score}
          />
        </motion.div>
      )}

      {/* ISSUE-Q4: Next Steps — actionable cards with narrative closure */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.0 }}
        className="space-y-3"
      >
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          {t("assessment.nextSteps", { defaultValue: "What's Next" })}
        </h2>
        <div className="space-y-2">
          {/* Card 1: Add another competency */}
          <button
            type="button"
            onClick={() => router.push(`/${locale}/assessment`)}
            className="w-full flex items-center gap-3 rounded-xl bg-surface-container-low p-3 text-left hover:bg-muted/30 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <span className="text-2xl shrink-0" aria-hidden="true">🎯</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-foreground">{t("assessment.nextStepAssess")}</p>
              <p className="text-xs text-muted-foreground">{t("assessment.nextStepAssessDesc")}</p>
            </div>
            <ArrowRight className="size-4 text-muted-foreground shrink-0" aria-hidden="true" />
          </button>
          {/* Card 2: View AURA score */}
          <button
            type="button"
            onClick={() => router.push(`/${locale}/aura`)}
            className="w-full flex items-center gap-3 rounded-xl bg-surface-container-low p-3 text-left hover:bg-muted/30 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <span className="text-2xl shrink-0" aria-hidden="true">✨</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-foreground">{t("assessment.nextStepAura")}</p>
              <p className="text-xs text-muted-foreground">
                {aura
                  ? t("assessment.nextStepAuraScore", { score: overallAura.toFixed(1) })
                  : t("assessment.nextStepAuraDesc")}
              </p>
            </div>
            <ArrowRight className="size-4 text-muted-foreground shrink-0" aria-hidden="true" />
          </button>
          {/* Context-sensitive tip line (no duplicate buttons) */}
          {score < 60 && (
            <p className="text-xs text-muted-foreground px-1">
              💡 {t("assessment.tipImprove", { defaultValue: "Practice more and retake to improve your score." })}
            </p>
          )}
          {score >= 90 && (
            <p className="text-xs text-primary px-1">
              🏆 {t("assessment.tipExcellent", { defaultValue: "Outstanding! Organizations can now find you in search." })}
            </p>
          )}
        </div>
      </motion.div>

      {/* Question breakdown link */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.15 }}
        >
          <Button
            onClick={() => router.push(`/${locale}/assessment/${sessionId}/questions`)}
            variant="outline"
            size="sm"
            className="w-full gap-2"
          >
            <ListChecks className="size-4" />
            {t("assessment.seeBreakdown")}
          </Button>
        </motion.div>
      )}

      {/* Share nudge — prominent for Silver+ (GROW-M01: was Gold+ only, Silver tier now included) */}
      {score >= 60 && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
          className="rounded-xl border border-primary/30 bg-primary/5 p-4 flex flex-col items-center gap-3 text-center"
        >
          <p className="text-sm font-semibold text-foreground">
            {/* Neutral share copy — tier-specific framing moved off this page per
                Crystal Law 6 Amendment. Share-nudge stays because the share link
                goes to the public /u/<username> card, where tier context is
                appropriate and user-initiated. */}
            {t("assessment.shareNudge")}
          </p>
          <Button
            onClick={() => {
              if (!username) return;
              const cardUrl = `https://volaura.app/u/${username}?utm_source=assessment_complete&utm_medium=share`;
              // Neutral emoji on the share card — the public profile page carries
              // the actual tier badge imagery, this page does not reveal it.
              const tierEmoji = "✨";
              // BATCH-O CULT #4: locale-aware share text — no more hardcoded English going to Telegram/WhatsApp
              const percentileText = percentile !== null ? ` · ${t("profile.topPercent", { percent: Math.max(1, Math.round(100 - percentile)) })}` : "";
              const text = t("assessment.shareBody", {
                emoji: tierEmoji,
                competency: competencyLabel,
                percentile: percentileText,
                score: (aura?.total_score ?? score).toFixed(1),
              }) + ` ${cardUrl}`;
              if (navigator.share) {
                navigator.share({ title: t("assessment.shareTitle"), text, url: cardUrl }).catch(() => {});
              } else {
                navigator.clipboard.writeText(text).catch(() => {});
              }
            }}
            size="sm"
            className="gap-2 w-full sm:w-auto min-h-[44px] sm:min-h-0"
            disabled={!username}
            aria-busy={phase === "reveal" && !username}
          >
            {phase === "reveal" && !username
              ? <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              : <Share2 className="size-4" />
            }
            {t("aura.share")}
          </Button>
        </motion.div>
      )}

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.3 }}
        className="flex flex-col gap-3 pt-2"
      >
        <Button
          onClick={() => router.push(`/${locale}/aura`)}
          size="lg"
          className="w-full"
        >
          {t("assessment.viewResults")}
          <ArrowRight className="size-4 ml-2" />
        </Button>

        <Button
          onClick={() => router.push(`/${locale}/assessment`)}
          variant="outline"
          size="lg"
          className="w-full"
        >
          <RotateCcw className="size-4 mr-2" />
          {t("aura.retake")}
        </Button>

        {score < 60 && (
          <Button
            onClick={() => {
              if (!username) return;
              const cardUrl = `https://volaura.app/u/${username}?utm_source=assessment_complete&utm_medium=share`;
              // BATCH-O CULT #4: locale-aware low-score share text
              const percentileTextLow = percentile !== null ? ` (${t("profile.topPercent", { percent: Math.max(1, Math.round(100 - percentile)) })})` : "";
              const text = t("assessment.shareBodyLow", {
                score: score.toFixed(1),
                percentile: percentileTextLow,
                competency: competencyLabel,
              }) + `\n${cardUrl}`;
              if (navigator.share) {
                navigator.share({ title: t("assessment.shareTitleLow"), text, url: cardUrl }).catch(() => {});
              }
            }}
            variant="ghost"
            size="sm"
            className="text-muted-foreground w-full min-h-[44px] sm:min-h-0"
            disabled={!username}
            title={!username ? t("assessment.shareNudgeLow") : undefined}
          >
            {phase === "reveal" && !username
              ? <Loader2 className="size-4 mr-2 animate-spin" aria-hidden="true" />
              : <Share2 className="size-4 mr-2" />
            }
            {t("assessment.shareNudgeLow")}
          </Button>
        )}
      </motion.div>
    </div>
  );
}
