"use client";

import { useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdminGrowth, type AdminGrowthFunnel } from "@/hooks/queries/use-admin";

// ── Funnel step definitions ────────────────────────────────────────────────────

interface FunnelStep {
  key: keyof Omit<AdminGrowthFunnel, "computed_at">;
  label: string;
  description: string;
}

const FUNNEL_STEPS: FunnelStep[] = [
  {
    key: "signups_7d",
    label: "Signups",
    description: "New accounts created",
  },
  {
    key: "profiles_created_7d",
    label: "Profiles Created",
    description: "Completed onboarding",
  },
  {
    key: "assessments_started_7d",
    label: "Assessments Started",
    description: "Entered assessment flow",
  },
  {
    key: "assessments_completed_7d",
    label: "Assessments Completed",
    description: "Finished all questions",
  },
  {
    key: "aura_scores_7d",
    label: "AURA Scores Earned",
    description: "Score computed & stored",
  },
];

// ── Conversion colour gate ────────────────────────────────────────────────────
// Purple (#D4B4FF) for low conversion (<40%), teal for healthy (≥40%).

function conversionColor(rate: number | null): string {
  if (rate === null) return "text-on-surface-variant";
  return rate >= 0.4 ? "text-teal-400" : "text-[#D4B4FF]";
}

function formatRate(rate: number | null): string {
  if (rate === null) return "—";
  return `${Math.round(rate * 100)}%`;
}

// ── Metric card ───────────────────────────────────────────────────────────────

interface MetricCardProps {
  step: number;
  label: string;
  description: string;
  value: number;
  conversionRate: number | null;
}

function MetricCard({ step, label, description, value, conversionRate }: MetricCardProps) {
  return (
    <Card className="bg-surface-container-low border-border">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant mb-1">
              Step {step}
            </p>
            <p className="text-2xl font-bold text-on-surface tabular-nums">{value.toLocaleString()}</p>
            <p className="text-sm font-semibold text-on-surface mt-0.5">{label}</p>
            <p className="text-xs text-on-surface-variant mt-0.5">{description}</p>
          </div>
          {conversionRate !== null && (
            <div className="shrink-0 text-right">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant mb-1">
                Conv.
              </p>
              <p className={`text-lg font-bold tabular-nums ${conversionColor(conversionRate)}`}>
                {formatRate(conversionRate)}
              </p>
              <p className="text-[10px] text-on-surface-variant">from prev</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function MetricCardSkeleton() {
  return (
    <Card className="bg-surface-container-low border-border">
      <CardContent className="p-5">
        <Skeleton className="h-3 w-12 mb-2 rounded" />
        <Skeleton className="h-8 w-20 mb-1 rounded" />
        <Skeleton className="h-4 w-32 mb-1 rounded" />
        <Skeleton className="h-3 w-40 rounded" />
      </CardContent>
    </Card>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminGrowthPage() {
  useEffect(() => {
    document.title = "Growth — Admin · Volaura";
  }, []);

  const { data, isLoading, isError } = useAdminGrowth();

  // Build conversion rates: step N value / step N-1 value
  const values = data
    ? FUNNEL_STEPS.map((s) => data[s.key] as number)
    : null;

  const conversionRates: (number | null)[] = values
    ? values.map((v, i) => {
        if (i === 0) return null; // first step has no previous
        const prev = values[i - 1];
        return prev > 0 ? v / prev : null;
      })
    : [];

  return (
    <div className="flex-1 p-6 max-w-3xl mx-auto w-full">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold font-headline text-on-surface">Growth Funnel</h1>
        <p className="text-sm text-on-surface-variant mt-1">
          Last 7 days — AARRR acquisition to AURA
          {data?.computed_at && (
            <span className="ml-2 text-xs opacity-60">
              · {new Date(data.computed_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
        </p>
      </div>

      {/* Error state */}
      {isError && (
        <Card className="bg-surface-container-low border-border mb-4">
          <CardContent className="p-5">
            <p className="text-sm text-[#D4B4FF]">Failed to load growth data. Check API connection.</p>
          </CardContent>
        </Card>
      )}

      {/* Funnel cards */}
      <div className="flex flex-col gap-3">
        {isLoading || !data
          ? FUNNEL_STEPS.map((s) => <MetricCardSkeleton key={s.key} />)
          : FUNNEL_STEPS.map((s, i) => (
              <MetricCard
                key={s.key}
                step={i + 1}
                label={s.label}
                description={s.description}
                value={data[s.key] as number}
                conversionRate={conversionRates[i] ?? null}
              />
            ))}
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center gap-4 text-xs text-on-surface-variant">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-teal-400" />
          Healthy (≥40%)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#D4B4FF]" />
          Low (&lt;40%)
        </span>
      </div>
    </div>
  );
}
