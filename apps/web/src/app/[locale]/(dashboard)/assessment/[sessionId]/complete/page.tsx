"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Loader2,
  Trophy,
  Award,
  Star,
  Share2,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api/client";

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
}

interface AuraScore {
  overall_score: number;
  badge_tier: string;
  elite_status: boolean;
  competency_scores: Record<string, number>;
}

// ── Badge Config ───────────────────────────────────────────────────────

const BADGE_CONFIG: Record<string, { color: string; bg: string; icon: typeof Trophy; label: string }> = {
  platinum: { color: "text-violet-300", bg: "bg-violet-500/20 ring-violet-400/50", icon: Star, label: "Platinum" },
  gold: { color: "text-amber-300", bg: "bg-amber-500/20 ring-amber-400/50", icon: Trophy, label: "Gold" },
  silver: { color: "text-slate-300", bg: "bg-slate-400/20 ring-slate-300/50", icon: Award, label: "Silver" },
  bronze: { color: "text-orange-400", bg: "bg-orange-500/20 ring-orange-400/50", icon: Award, label: "Bronze" },
  none: { color: "text-muted-foreground", bg: "bg-muted/20 ring-muted/50", icon: Award, label: "—" },
};

// ── Animated counter ───────────────────────────────────────────────────

function useAnimatedCounter(target: number, duration = 1500) {
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
  const queryClient = useQueryClient();
  const isMounted = useRef(true);

  const [phase, setPhase] = useState<"loading" | "reveal" | "error">("loading");
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [aura, setAura] = useState<AuraScore | null>(null);
  const [error, setError] = useState<string | null>(null);

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

      // 2. Fetch updated AURA score
      try {
        const auraResult = await apiFetch<AuraScore>("/api/aura/me", { token });
        if (isMounted.current) setAura(auraResult);
      } catch {
        // AURA fetch failure is non-critical — results still show
      }

      // 3. Invalidate cached AURA score so dashboard refreshes
      queryClient.invalidateQueries({ queryKey: ["aura-score"] });

      if (isMounted.current) {
        // Small delay for suspense effect, then reveal
        setTimeout(() => {
          if (isMounted.current) setPhase("reveal");
        }, 800);
      }
    } catch (err: unknown) {
      if (!isMounted.current) return;
      const msg = err instanceof Error ? err.message : t("error.generic");
      setError(msg);
      setPhase("error");
    }
  }, [sessionId, locale, router, queryClient, t]);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // ── Derived values ───────────────────────────────────────────────────

  const score = result?.competency_score ?? 0;
  const animatedScore = useAnimatedCounter(phase === "reveal" ? score : 0);
  const overallAura = useAnimatedCounter(phase === "reveal" ? (aura?.overall_score ?? 0) : 0, 2000);
  const tier = aura?.badge_tier ?? (score >= 90 ? "platinum" : score >= 75 ? "gold" : score >= 60 ? "silver" : score >= 40 ? "bronze" : "none");
  const badge = BADGE_CONFIG[tier] || BADGE_CONFIG.none;
  const BadgeIcon = badge.icon;
  const hasGamingFlags = (result?.gaming_flags?.length ?? 0) > 0;

  const competencyLabel = result?.competency_slug
    ? result.competency_slug.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
    : "";

  // ── Loading state ────────────────────────────────────────────────────

  if (phase === "loading") {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 flex flex-col items-center text-center space-y-8">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 18 }}
        >
          <div className="size-24 rounded-full bg-primary/10 flex items-center justify-center">
            <Loader2 className="size-12 text-primary animate-spin" aria-hidden="true" />
          </div>
        </motion.div>
        <div className="space-y-2" role="status" aria-live="polite">
          <h1 className="text-xl font-semibold text-foreground">{t("assessment.processingResults")}</h1>
          <p className="text-sm text-muted-foreground">{t("assessment.evaluating")}</p>
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
      {/* Badge Reveal */}
      <motion.div
        initial={{ scale: 0, rotate: -20 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 180, damping: 16, delay: 0.1 }}
        className="flex flex-col items-center text-center space-y-4"
      >
        <div className={cn(
          "size-28 rounded-full flex items-center justify-center ring-4",
          badge.bg,
        )}>
          <BadgeIcon className={cn("size-14", badge.color)} />
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
          <h1 className={cn("text-5xl font-bold tabular-nums", badge.color)}>
            {animatedScore.toFixed(1)}
          </h1>
          <p className="text-lg font-semibold">
            {t(`aura.${tier}`, { defaultValue: badge.label })}
          </p>
        </motion.div>
      </motion.div>

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
          <p className="text-2xl font-bold tabular-nums flex items-center justify-center gap-1">
            <CheckCircle2 className="size-4 text-green-400" />
            {result?.aura_updated ? t("common.yes") : "—"}
          </p>
          <p className="text-xs text-muted-foreground">{t("aura.title")}</p>
        </div>
      </motion.div>

      {/* Gaming Warning */}
      <AnimatePresence>
        {hasGamingFlags && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4 text-sm text-amber-200"
          >
            <div className="flex items-start gap-2">
              <AlertTriangle className="size-4 mt-0.5 shrink-0" />
              <p>
                {t("assessment.gamingWarning", {
                  defaultValue: "Some responses were flagged for unusual patterns. Your score may be adjusted.",
                })}
              </p>
            </div>
          </motion.div>
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

      {/* Next Steps */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.0 }}
        className="space-y-3"
      >
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          {t("assessment.nextSteps", { defaultValue: "What's Next" })}
        </h2>
        <div className="space-y-2 text-sm text-muted-foreground">
          {score < 60 && (
            <p>💡 {t("assessment.tipImprove", { defaultValue: "Practice more in this area and retake the assessment to improve your score." })}</p>
          )}
          {score >= 60 && score < 90 && (
            <p>🎯 {t("assessment.tipGood", { defaultValue: "Great score! Try other competencies to build your full AURA profile." })}</p>
          )}
          {score >= 90 && (
            <p>🏆 {t("assessment.tipExcellent", { defaultValue: "Outstanding! You're in the top tier. Share your achievement with organizations." })}</p>
          )}
        </div>
      </motion.div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
        className="flex flex-col gap-3 pt-4"
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

        <Button
          onClick={() => {
            if (navigator.share) {
              navigator.share({
                title: `Volaura AURA: ${score.toFixed(1)}`,
                text: `I scored ${score.toFixed(1)} in ${competencyLabel} on Volaura! 🏅`,
                url: typeof window !== "undefined" ? window.location.origin : "",
              }).catch(() => {});
            }
          }}
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
        >
          <Share2 className="size-4 mr-2" />
          {t("aura.share")}
        </Button>
      </motion.div>
    </div>
  );
}
