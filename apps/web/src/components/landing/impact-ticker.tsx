"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Users, CalendarCheck, Clock } from "lucide-react";
import { usePublicStats } from "@/hooks/queries/use-public-stats";

// Fallback numbers shown while loading or if API fails
const FALLBACK_STATS = {
  totalProfessionals: 0,
  totalEvents: 0,
  totalHours: 0,
};

function useCountUp(target: number, duration = 800): number {
  const [count, setCount] = useState(0);
  const startRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    startRef.current = null;

    const animate = (timestamp: number) => {
      if (!isMounted.current) return;
      if (startRef.current === null) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // cubic ease-out
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      isMounted.current = false;
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return count;
}

function StatCard({
  icon: Icon,
  value,
  label,
  fallbackLabel,
}: {
  icon: React.ElementType;
  value: number;
  label: string;
  // T1-1: below-threshold qualitative fallback. Zero counters = anti-social-proof.
  // When count < 5, render the qualitative string instead of the raw number.
  fallbackLabel?: string;
}) {
  const count = useCountUp(value, 1800);
  const belowThreshold = fallbackLabel != null && value < 5;

  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-border bg-card px-8 py-7 shadow-sm text-center">
      <Icon className="h-6 w-6 text-primary" aria-hidden="true" />
      {belowThreshold ? (
        <span className="text-base font-semibold text-foreground sm:text-lg">
          {fallbackLabel}
        </span>
      ) : (
        <>
          <span className="text-4xl font-extrabold tabular-nums text-foreground sm:text-5xl">
            {count.toLocaleString()}
          </span>
          <span className="text-sm font-medium text-muted-foreground">{label}</span>
        </>
      )}
    </div>
  );
}

export function ImpactTicker() {
  const { t } = useTranslation();
  const { data, isError } = usePublicStats();

  // Use real data if available, fallback if API fails or returns null
  const totalProfessionals =
    (data && !isError ? data.total_professionals : null) ?? FALLBACK_STATS.totalProfessionals;
  const totalEvents =
    (data && !isError ? data.total_events : null) ?? FALLBACK_STATS.totalEvents;
  // API returns total_assessments; we map this to "hours" as an approximation
  // (avg ~10h per assessment). Fall back to FALLBACK if no data.
  const totalHours =
    (data && !isError && data.total_assessments
      ? Math.round(data.total_assessments * 10)
      : null) ?? FALLBACK_STATS.totalHours;

  return (
    <section
      className="bg-muted/40 py-16"
      aria-label="Platform impact statistics"
    >
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            icon={Users}
            value={totalProfessionals}
            label={t("landing.impactProfessionals")}
            fallbackLabel={t("landing.statsFallback.professionals")}
          />
          <StatCard
            icon={CalendarCheck}
            value={totalEvents}
            label={t("landing.impactEvents")}
            fallbackLabel={t("landing.statsFallback.events")}
          />
          <StatCard
            icon={Clock}
            value={totalHours}
            label={t("landing.impactHours")}
          />
        </div>
      </div>
    </section>
  );
}
