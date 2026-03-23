"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { useAssessmentStore } from "@/stores/assessment-store";
import { CompetencyCard } from "@/components/assessment/competency-card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

// Static competency metadata — labels fetched from i18n, weights from CLAUDE.md
const COMPETENCIES = [
  { id: "communication", weight: 0.20, estimatedMinutes: 5 },
  { id: "reliability", weight: 0.15, estimatedMinutes: 4 },
  { id: "english_proficiency", weight: 0.15, estimatedMinutes: 5 },
  { id: "leadership", weight: 0.15, estimatedMinutes: 5 },
  { id: "event_performance", weight: 0.10, estimatedMinutes: 4 },
  { id: "tech_literacy", weight: 0.10, estimatedMinutes: 4 },
  { id: "adaptability", weight: 0.10, estimatedMinutes: 4 },
  { id: "empathy_safeguarding", weight: 0.05, estimatedMinutes: 3 },
] as const;

type CompetencyId = (typeof COMPETENCIES)[number]["id"];

// Assessment page lives at /[locale]/assessment — no params needed, locale from i18n context
export default function AssessmentPage() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const locale = i18n.language;
  const { setCompetencies } = useAssessmentStore();

  const [selected, setSelected] = useState<Set<CompetencyId>>(new Set());
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push(`/${locale}/login`);
        return;
      }

      // Start the first competency session via API
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/assessments/start`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({ competency: competencyList[0] }),
        }
      );

      if (!res.ok) {
        throw new Error("start_failed");
      }

      const data = (await res.json()) as { session_id: string };
      router.push(`/${locale}/assessment/${data.session_id}`);
    } catch {
      setError(t("assessment.errorStartFailed"));
      setIsStarting(false);
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

      {error && (
        <Alert variant="destructive" role="alert">
          <AlertCircle className="size-4" aria-hidden="true" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-3" role="group" aria-label={t("assessment.selectCompetencies")}>
        {COMPETENCIES.map((comp) => {
          const label = t(`competency.${comp.id}`, { defaultValue: comp.id });
          const estimatedLabel = t("assessment.estimatedTime", {
            n: comp.estimatedMinutes,
          });
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
