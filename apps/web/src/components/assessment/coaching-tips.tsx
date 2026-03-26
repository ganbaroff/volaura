"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Lightbulb, ArrowRight } from "lucide-react";
import { apiFetch, ApiError } from "@/lib/api/client";
import { createClient } from "@/lib/supabase/client";

// ── Types ─────────────────────────────────────────────────────────────────────

interface CoachingTip {
  title: string;
  description: string;
  action: string;
}

interface CoachingResponse {
  tips: CoachingTip[];
  methodology_note?: string;
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface CoachingTipsProps {
  sessionId: string;
  competencyId: string;
  score: number;
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function CoachingSkeleton({ t }: { t: (key: string) => string }) {
  return (
    <div className="space-y-3" role="status" aria-label={t("assessment.coachingLoading")}>
      {[1, 2, 3].map((n) => (
        <div
          key={n}
          className="rounded-xl border border-border bg-card/50 p-4 space-y-2 animate-pulse"
        >
          <div className="h-4 w-2/5 rounded bg-muted" />
          <div className="h-3 w-full rounded bg-muted" />
          <div className="h-3 w-4/5 rounded bg-muted" />
          <div className="h-3 w-1/3 rounded bg-muted mt-1" />
        </div>
      ))}
      <p className="text-xs text-center text-muted-foreground pt-1">
        {t("assessment.coachingLoading")}
      </p>
    </div>
  );
}

// ── TipCard ───────────────────────────────────────────────────────────────────

interface TipCardProps {
  tip: CoachingTip;
  index: number;
  tryThisLabel: string;
}

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.4, ease: "easeOut" as const },
  }),
};

function TipCard({ tip, index, tryThisLabel }: TipCardProps) {
  return (
    <motion.div
      custom={index}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className="rounded-xl border border-border bg-card p-4 space-y-1.5"
    >
      <p className="text-sm font-semibold text-foreground">{tip.title}</p>
      <p className="text-sm text-muted-foreground leading-relaxed">{tip.description}</p>
      {tip.action && (
        <div className="flex items-center gap-1.5 pt-1">
          <ArrowRight className="size-3.5 text-primary shrink-0" aria-hidden="true" />
          <p className="text-sm text-primary font-medium">
            <span className="text-muted-foreground font-normal">{tryThisLabel} </span>
            {tip.action}
          </p>
        </div>
      )}
    </motion.div>
  );
}

// ── CoachingTips ──────────────────────────────────────────────────────────────

export function CoachingTips({ sessionId, competencyId, score }: CoachingTipsProps) {
  const { t } = useTranslation();
  const isMounted = useRef(true);

  const [tips, setTips] = useState<CoachingTip[]>([]);
  const [methodologyNote, setMethodologyNote] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function fetchCoaching() {
      setIsLoading(true);
      setHasError(false);

      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token ?? null;
        if (!token) {
          if (!cancelled && isMounted.current) setHasError(true);
          return;
        }

        const data = await apiFetch<CoachingResponse>(
          `/api/assessment/${sessionId}/coaching`,
          {
            method: "POST",
            token,
            body: JSON.stringify({ competency_id: competencyId, score }),
          }
        );

        if (!cancelled && isMounted.current) {
          setTips(data.tips ?? []);
          setMethodologyNote(data.methodology_note);
        }
      } catch (err: unknown) {
        if (!cancelled && isMounted.current) {
          // 404 / 422 can happen when endpoint not yet live — treat as empty, not error
          if (err instanceof ApiError && (err.status === 404 || err.status === 422)) {
            setTips([]);
          } else {
            setHasError(true);
          }
        }
      } finally {
        if (!cancelled && isMounted.current) setIsLoading(false);
      }
    }

    fetchCoaching();
    return () => { cancelled = true; };
  }, [sessionId, competencyId, score]);

  const isExcellent = score >= 85;
  const sectionTitle = isExcellent
    ? t("assessment.coachingExcellent")
    : t("assessment.coaching");

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="flex items-center gap-2">
        <Lightbulb className="size-4 text-primary shrink-0" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          {sectionTitle}
        </h2>
      </div>

      {!isExcellent && (
        <p className="text-sm text-muted-foreground">
          {t("assessment.coachingSubtitle")}
        </p>
      )}

      {/* Loading */}
      {isLoading && <CoachingSkeleton t={t} />}

      {/* Error */}
      {hasError && !isLoading && (
        <p className="text-sm text-muted-foreground py-2">
          {t("assessment.coachingError")}
        </p>
      )}

      {/* Tip cards */}
      {!isLoading && !hasError && tips.length > 0 && (
        <div className="space-y-3">
          {tips.map((tip, index) => (
            <TipCard
              key={index}
              tip={tip}
              index={index}
              tryThisLabel={t("assessment.coachingTryThis")}
            />
          ))}
        </div>
      )}

      {/* Methodology note */}
      {!isLoading && (methodologyNote || tips.length > 0) && (
        <p className="text-xs text-muted-foreground/70 pt-1 border-t border-border/50">
          {methodologyNote ?? t("aura.methodologyNote")}
        </p>
      )}
    </div>
  );
}
