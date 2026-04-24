"use client";

import { useState, useCallback, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { useAssessmentStore } from "@/stores/assessment-store";
import { CompetencyCard } from "@/components/assessment/competency-card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { API_BASE } from "@/lib/api/client";
import { useTrackEvent } from "@/hooks/use-analytics";
import { EnergyPicker } from "@/components/assessment/energy-picker";
import { PreAssessmentSummary } from "@/components/assessment/pre-assessment-summary";
import { SafetyBlock } from "@/components/assessment/safety-block";
import { TopBar } from "@/components/layout/top-bar";
import { CommunitySignalInline } from "@/components/community/community-signal-inline";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import { buildLoginNextPath } from "../auth-recovery";

// Static competency metadata — labels fetched from i18n, weights from CLAUDE.md
const COMPETENCIES = [
  { id: "communication",        weight: 0.20, estimatedMinutes: 5,  icon: "\u{1F4AC}" },
  { id: "reliability",          weight: 0.15, estimatedMinutes: 4,  icon: "\u23F0" },
  { id: "english_proficiency",  weight: 0.15, estimatedMinutes: 5,  icon: "\u{1F30D}" },
  { id: "leadership",           weight: 0.15, estimatedMinutes: 5,  icon: "\u{1F9ED}" },
  { id: "event_performance",    weight: 0.10, estimatedMinutes: 4,  icon: "\u{1F3C6}" },
  { id: "tech_literacy",        weight: 0.10, estimatedMinutes: 4,  icon: "\u{1F4BB}" },
  { id: "adaptability",         weight: 0.10, estimatedMinutes: 4,  icon: "\u{1F504}" },
  { id: "empathy_safeguarding", weight: 0.05, estimatedMinutes: 3,  icon: "\u{1F91D}" },
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
  const track = useTrackEvent();
  const isMounted = useRef(true);

  const [selected, setSelected] = useState<Set<CompetencyId>>(new Set());
  // Global energy state so the TopBar picker and the assessment picker stay in sync
  // (Constitution Law 2 compliance — was previously local, drift-prone)
  const { energy: energyLevel, setEnergy: setEnergyLevel } = useEnergyMode();
  const [consentGiven, setConsentGiven] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reauthPath = buildLoginNextPath(locale, `/${locale}/assessment`);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  // Pre-select competency from ?competency= query param, or default to communication (BATCH-O A1)
  useEffect(() => {
    const slug = searchParams.get("competency");
    if (slug) {
      const valid = COMPETENCIES.find((c) => c.id === slug);
      if (valid) setSelected(new Set([valid.id]));
    } else {
      // Default: pre-select highest-weight competency to eliminate 8-way decision paralysis
      setSelected(new Set(["communication"]));
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

      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push(reauthPath);
        return;
      }

      const res = await fetch(`${API_BASE}/assessment/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          competency_slug: competencyList[0],
          energy_level: energyLevel,
          automated_decision_consent: consentGiven,
          assessment_plan_competencies: competencyList,
          assessment_plan_current_index: 0,
        }),
      });

      if (!res.ok) {
        // BATCH-O A3: expose cooldown wait time — 429 means rate limited, show minutes remaining
        if (res.status === 429) {
          const retryAfter = res.headers.get("Retry-After");
          const waitMin = retryAfter ? Math.ceil(parseInt(retryAfter, 10) / 60) : 30;
          if (isMounted.current) {
            setError(t("assessment.cooldownError", { minutes: waitMin }));
            setIsStarting(false);
          }
          return;
        }
        // 409 = active session already exists — resume it instead of showing error
        if (res.status === 409) {
          const body = await res.json().catch(() => ({})) as { session_id?: string };
          if (body.session_id && isMounted.current) {
            setSession(body.session_id);
            router.push(`/${locale}/assessment/${body.session_id}`);
          } else if (isMounted.current) {
            setIsStarting(false);
          }
          return;
        }
        throw new Error("start_failed");
      }

      const data = (await res.json()) as {
        session_id: string;
        next_question: import("@/stores/assessment-store").Question | null;
      };
      setCompetencies(competencyList);
      setSession(data.session_id);
      if (data.next_question) {
        setQuestion(data.next_question);
      }
      track("assessment_started", { competency_slug: competencyList[0] }, data.session_id);
      router.push(`/${locale}/assessment/${data.session_id}`);
    } catch {
      if (isMounted.current) {
        setError(t("assessment.errorStartFailed"));
        setIsStarting(false);
      }
    }
  };

  return (
    <>
    <TopBar title={t("assessment.title")} />
    <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-headline text-foreground">
          {t("assessment.title")}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("assessment.selectCompetencies")}
        </p>
        {/* G44 Community Signal — silent when zero, no comparison framing */}
        <div className="mt-2">
          <CommunitySignalInline />
        </div>
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
          <button
            type="button"
            onClick={() => router.push(`/${locale}/assessment/info/${preselectedComp.id}`)}
            className="text-xs text-primary hover:underline shrink-0"
          >
            {t("assessment.infoAbout", { defaultValue: "About" })}
          </button>
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

      {/* ADHD guidance: reduce decision paralysis (Behavioral Nudge Engine finding BNE-001) */}
      <p className="text-xs text-muted-foreground text-center">
        {t("assessment.guidance", { defaultValue: "New here? Start with 1-2 competencies. You can always come back for more." })}
      </p>

      <div className="grid gap-3" role="group" aria-label={t("assessment.selectCompetencies")}>
        {COMPETENCIES.map((comp) => {
          const label = t(`competency.${comp.id}`, { defaultValue: comp.id });
          const description = t(`competency.${comp.id}_desc`, { defaultValue: "" });
          const estimatedLabel = t("assessment.estimatedTime", { n: comp.estimatedMinutes });
          return (
            <CompetencyCard
              key={comp.id}
              id={comp.id}
              label={label}
              description={description || undefined}
              estimatedMinutes={comp.estimatedMinutes}
              estimatedLabel={estimatedLabel}
              isSelected={selected.has(comp.id)}
              onToggle={toggle}
            />
          );
        })}
      </div>

      {/* Sequential flow indicator — clarify one-at-a-time when multiple selected */}
      {selected.size > 1 && (
        <div className="rounded-2xl border border-border bg-surface-container-low p-4 space-y-2">
          <p className="text-xs font-semibold text-foreground uppercase tracking-wide">
            {t("assessment.yourOrder", { defaultValue: "Your assessment order" })}
          </p>
          <ol className="space-y-1.5">
            {Array.from(selected).map((id, i) => (
              <li key={id} className="flex items-center gap-2 text-sm">
                <span className="flex items-center justify-center size-5 rounded-full bg-primary/10 text-primary text-[10px] font-bold shrink-0">
                  {i + 1}
                </span>
                <span className="text-foreground">
                  {t(`competency.${id}`, { defaultValue: id })}
                </span>
                <span className="text-xs text-muted-foreground">
                  ~{COMPETENCIES.find(c => c.id === id)?.estimatedMinutes ?? 0} {t("assessment.min", { defaultValue: "min" })}
                </span>
              </li>
            ))}
          </ol>
          <p className="text-xs text-muted-foreground">
            {t("assessment.sequentialNote", { defaultValue: "You'll complete one competency at a time. Progress is saved between each." })}
          </p>
        </div>
      )}

      {/* Pre-assessment layer: what user gets before they commit */}
      {selected.size > 0 && (
        <PreAssessmentSummary
          totalMinutes={totalMinutes}
          competencyCount={selected.size}
        />
      )}

      {/* Constitution P0 (E4) Pre-Assessment Layer: psychotype hint + pause + safety copy */}
      {selected.size > 0 && <SafetyBlock />}

      {/* GDPR Article 22: consent for automated decision-making — above energy picker so it's visible without scrolling on mobile */}
      {selected.size > 0 && (
        <label className="flex items-start gap-3 text-sm text-muted-foreground cursor-pointer">
          <input
            type="checkbox"
            checked={consentGiven}
            onChange={(e) => setConsentGiven(e.target.checked)}
            className="mt-0.5 size-4 rounded border-border accent-primary"
          />
          <span>{t("assessment.automatedScoringConsent")}</span>
        </label>
      )}

      {/* Constitution Law 2: Energy Adaptation — user picks energy level before assessment */}
      {selected.size > 0 && (
        <EnergyPicker value={energyLevel} onChange={setEnergyLevel} />
      )}

      <Button
        onClick={handleStart}
        disabled={isStarting || selected.size === 0 || !consentGiven}
        variant="primary"
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
          selected.size > 1
            ? t("assessment.startFirst", {
                name: t(`competency.${Array.from(selected)[0]}`, { defaultValue: Array.from(selected)[0] }),
                defaultValue: `Start with ${t(`competency.${Array.from(selected)[0]}`, { defaultValue: Array.from(selected)[0] })}`,
              })
            : t("assessment.start")
        )}
      </Button>
    </div>
    </>
  );
}

export default function AssessmentPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
          <div className="grid gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-12 w-full rounded-lg" />
        </div>
      }
    >
      <AssessmentContent />
    </Suspense>
  );
}
