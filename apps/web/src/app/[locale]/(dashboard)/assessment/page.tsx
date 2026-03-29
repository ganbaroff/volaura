"use client";

import { useState, useCallback, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { useAssessmentStore } from "@/stores/assessment-store";
import { CompetencyCard } from "@/components/assessment/competency-card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { API_BASE } from "@/lib/api/client";

// Static competency metadata — labels fetched from i18n, weights from CLAUDE.md
const COMPETENCIES = [
  { id: "communication",        weight: 0.20, estimatedMinutes: 5,  icon: "💬" },
  { id: "reliability",          weight: 0.15, estimatedMinutes: 4,  icon: "⏰" },
  { id: "english_proficiency",  weight: 0.15, estimatedMinutes: 5,  icon: "🌍" },
  { id: "leadership",           weight: 0.15, estimatedMinutes: 5,  icon: "🧭" },
  { id: "event_performance",    weight: 0.10, estimatedMinutes: 4,  icon: "🏆" },
  { id: "tech_literacy",        weight: 0.10, estimatedMinutes: 4,  icon: "💻" },
  { id: "adaptability",         weight: 0.10, estimatedMinutes: 4,  icon: "🔄" },
  { id: "empathy_safeguarding", weight: 0.05, estimatedMinutes: 3,  icon: "🤝" },
] as const;

type CompetencyId = (typeof COMPETENCIES)[number]["id"];

// Assessment page lives at /[locale]/assessment
// Supports ?competency=<slug> to pre-select a single competency (from onboarding flow)
function AssessmentContent() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const searchParams = useSearchParams();
  const locale = i18n.language;
  const { setCompetencies, setSession, setQuestion } = useAssessmentStore();
  const isMounted = useRef(true);

  const [selected, setSelected] = useState<Set<CompetencyId>>(new Set());
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  // Pre-select competency from ?competency= query param (onboarding → welcome → assessment flow)
  useEffect(() => {
    const slug = searchParams.get("competency");
    if (!slug) return;
    const valid = COMPETENCIES.find((c) => c.id === slug);
    if (valid) {
      setSelected(new Set([valid.id]));
    }
  }, [searchParams]);

  // Total estimated minutes for selected competencies
  const totalMinutes = Array.from(selected).reduce((sum, id) => {
    const comp = COMPETENCIES.find((c) => c.id === id);
    return sum + (comp?.estimatedMinutes ?? 0);
  }, 0);

  // Pre-selected single competency info (from onboarding flow)
  const preselectedSlug = searchParams.get("competency");
  const preselectedComp = preselectedSlug
    ? COMPETENCIES.find((c) => c.id === preselectedSlug)
    : null;

  const toggle = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id as CompetencyId)) {
        next.delete(id as CompetencyId);
      } else {
        next.add(id as CompetencyId);
      }
      return next;
    });
    setError(null);
  }, []);

  const handleStart = async () => {
    if (selected.size === 0) {
      setError(t("assessment.selectAtLeastOne"));
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      const competencyList = Array.from(selected);
      setCompetencies(competencyList);

      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push(`/${locale}/login`);
        return;
      }

      const res = await fetch(`${API_BASE}/api/assessment/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ competency_slug: competencyList[0] }),
      });

      if (!res.ok) {
        throw new Error("start_failed");
      }

      const data = (await res.json()) as {
        session_id: string;
        next_question: import("@/stores/assessment-store").Question | null;
      };
      setSession(data.session_id);
      if (data.next_question) {
        setQuestion(data.next_question);
      }
      router.push(`/${locale}/assessment/${data.session_id}`);
    } catch {
      if (isMounted.current) {
        setError(t("assessment.errorStartFailed"));
        setIsStarting(false);
      }
    }
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          {t("assessment.title")}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("assessment.selectCompetencies")}
        </p>
      </div>

      {/* Pre-selected competency info callout (onboarding → welcome → assessment flow) */}
      {preselectedComp && (
        <div className="rounded-2xl border border-primary/30 bg-primary/5 px-4 py-3 flex items-center gap-3">
          <span className="text-2xl" aria-hidden="true">{preselectedComp.icon}</span>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground mb-0.5">
              {t("assessment.recommended", { defaultValue: "Recommended for you" })}
            </p>
            <p className="text-sm font-semibold text-foreground">
              {t(`competency.${preselectedComp.id}`, { defaultValue: preselectedComp.id })}
            </p>
          </div>
          <span className="text-xs text-muted-foreground shrink-0">
            ~{preselectedComp.estimatedMinutes} {t("assessment.min", { defaultValue: "min" })}
          </span>
        </div>
      )}

      {error && (
        <Alert variant="destructive" role="alert">
          <AlertCircle className="size-4" aria-hidden="true" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-3" role="group" aria-label={t("assessment.selectCompetencies")}>
        {COMPETENCIES.map((comp) => {
          const label = t(`competency.${comp.id}`, { defaultValue: comp.id });
          const estimatedLabel = t("assessment.estimatedTime", { n: comp.estimatedMinutes });
          return (
            <CompetencyCard
              key={comp.id}
              id={comp.id}
              label={label}
              estimatedMinutes={comp.estimatedMinutes}
              estimatedLabel={estimatedLabel}
              isSelected={selected.has(comp.id)}
              onToggle={toggle}
            />
          );
        })}
      </div>

      {selected.size > 0 && (
        <p className="text-sm text-center text-muted-foreground" aria-live="polite">
          {t("assessment.totalTime", {
            n: totalMinutes,
            defaultValue: `~${totalMinutes} min total`,
          })}
        </p>
      )}

      <Button
        onClick={handleStart}
        disabled={isStarting || selected.size === 0}
        size="lg"
        className="w-full"
        aria-busy={isStarting}
      >
        {isStarting ? (
          <>
            <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
            {t("common.loading")}
          </>
        ) : (
          t("assessment.start")
        )}
      </Button>
    </div>
  );
}

export default function AssessmentPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-lg px-4 py-16 flex items-center justify-center">
          <Loader2 className="size-8 text-primary animate-spin" aria-hidden="true" />
        </div>
      }
    >
      <AssessmentContent />
    </Suspense>
  );
}
