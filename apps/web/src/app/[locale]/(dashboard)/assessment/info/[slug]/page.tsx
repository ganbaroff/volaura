"use client";

import { useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Clock, ChevronLeft, RotateCcw, AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { useAssessmentInfo } from "@/hooks/queries/use-assessment";
import { ApiError } from "@/lib/api/client";
import { useEnergyMode } from "@/hooks/use-energy-mode";

const SUPPORTED_LOCALES = ["az", "en"] as const;
type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

function isSupportedLocale(l: string): l is SupportedLocale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(l);
}

export default function AssessmentInfoPage() {
  const { locale: rawLocale, slug } = useParams<{ locale: string; slug: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const isMounted = useRef(true);
  const shouldReduceMotion = useReducedMotion();

  // Law 4 — prefers-reduced-motion: skip translate/opacity animations when requested
  const fadeUp = (delay = 0, yOffset = 10) =>
    shouldReduceMotion
      ? {}
      : {
          initial: { opacity: 0, y: yOffset },
          animate: { opacity: 1, y: 0 },
          transition: { delay, duration: 0.3 },
        };

  const fadeIn = (delay = 0) =>
    shouldReduceMotion
      ? {}
      : {
          initial: { opacity: 0 },
          animate: { opacity: 1 },
          transition: { delay, duration: 0.3 },
        };

  const { energy } = useEnergyMode();
  const isLow = energy === "low";
  const locale: SupportedLocale = isSupportedLocale(rawLocale) ? rawLocale : "en";

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const { data, isLoading, error } = useAssessmentInfo(slug);

  // Auth redirect — 401 means session expired or not logged in
  useEffect(() => {
    if (!isMounted.current) return;
    if (error instanceof ApiError && error.status === 401) {
      const returnTo = encodeURIComponent(`/${locale}/assessment/info/${slug}`);
      router.replace(`/${locale}/login?returnTo=${returnTo}`);
    }
    // 404 — invalid slug — stay on page and show error state (handled in render)
  }, [error, locale, slug, router]);

  // ── Loading ──────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-6 space-y-6" role="status" aria-live="polite">
        <Skeleton className="h-4 w-16" />
        <div className="space-y-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Skeleton className="h-16 w-full rounded-lg" />
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-20 w-full rounded-xl" />
          <Skeleton className="h-20 w-full rounded-xl" />
        </div>
        <Skeleton className="h-12 w-full rounded-lg" />
      </div>
    );
  }

  // ── Error states ─────────────────────────────────────────────────────────

  if (error) {
    if (error instanceof ApiError && error.status === 401) {
      // Redirecting — show nothing to avoid flash
      return null;
    }

    if (error instanceof ApiError && error.status === 404) {
      return (
        <div className="mx-auto max-w-lg px-4 py-16 flex flex-col items-center gap-4 text-center">
          <AlertCircle className="size-10 text-muted-foreground" aria-hidden="true" />
          <div className="space-y-1">
            <p className="text-sm font-semibold">{t("error.notFound", { defaultValue: "Not found" })}</p>
            <p className="text-xs text-muted-foreground">
              {t("assessment.sessionNotFound", { defaultValue: "This competency could not be found." })}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={() => {
            if (isMounted.current) router.push(`/${locale}/assessment`);
          }}>
            <ChevronLeft className="size-4 mr-1" />
            {t("common.back")}
          </Button>
        </div>
      );
    }

    if (error instanceof ApiError && error.status === 429) {
      return (
        <div className="mx-auto max-w-lg px-4 py-16 flex flex-col items-center gap-4 text-center">
          <RotateCcw className="size-10 text-muted-foreground" aria-hidden="true" />
          <p className="text-sm text-muted-foreground">
            {t("error.tooManyRequests", { defaultValue: "Too many requests. Please wait a moment and try again." })}
          </p>
        </div>
      );
    }

    return (
      <div className="mx-auto max-w-lg px-4 py-16 flex flex-col items-center gap-4 text-center">
        <AlertCircle className="size-10 text-muted-foreground" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">{t("error.generic", { defaultValue: "Something went wrong." })}</p>
        <Button variant="outline" size="sm" onClick={() => {
          if (isMounted.current) router.push(`/${locale}/assessment`);
        }}>
          <ChevronLeft className="size-4 mr-1" />
          {t("common.back")}
        </Button>
      </div>
    );
  }

  if (!data) return null;

  // ── Derived values ────────────────────────────────────────────────────────

  const competencyLabel = t(`competency.${data.competency_slug}`, {
    defaultValue: data.name,
  });

  const description = data.description ?? t("assessment.infoNoDescription");

  const retakeBlocked = !data.can_retake || (data.days_until_retake != null && data.days_until_retake > 0);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="mx-auto max-w-lg px-4 py-6 space-y-6">
      {/* Back */}
      <button
        type="button"
        onClick={() => {
          if (isMounted.current) router.push(`/${locale}/assessment`);
        }}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        aria-label={t("common.back")}
      >
        <ChevronLeft className="size-4" aria-hidden="true" />
        {t("common.back")}
      </button>

      {/* Header */}
      <motion.div
        {...fadeUp(0, 10)}
        className="space-y-2"
      >
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {t("assessment.infoAbout")}
        </p>
        <h1 className="text-2xl font-bold text-foreground">{competencyLabel}</h1>
      </motion.div>

      {!isLow && (
        <motion.p
          {...fadeUp(0.1, 8)}
          className="text-sm text-muted-foreground leading-relaxed"
          lang={data.description ? "en" : undefined}
        >
          {description}
        </motion.p>
      )}

      {!isLow && (
        <motion.div
          {...fadeUp(0.2, 8)}
          className="grid grid-cols-2 gap-3"
        >
          <div className="rounded-xl bg-surface-container-low p-4 space-y-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="size-3.5" aria-hidden="true" />
              {t("assessment.infoTimeLabel")}
            </div>
            <p className="text-lg font-semibold">
              ~{data.time_estimate_minutes} {t("assessment.min")}
            </p>
          </div>

          <div className={cn(
            "rounded-xl p-4 space-y-1",
            retakeBlocked
              ? "bg-amber-500/10 border border-amber-500/20"
              : "bg-green-500/10 border border-green-500/20"
          )}>
            <p className="text-xs text-muted-foreground">
              {t("assessment.retake", { defaultValue: "Retake" })}
            </p>
            <p className={cn(
              "text-sm font-semibold",
              retakeBlocked ? "text-amber-400" : "text-green-400"
            )}>
              {retakeBlocked
                ? t("assessment.infoRetakeCooldown", { days: data.days_until_retake })
                : t("assessment.infoRetakeAvailable")}
            </p>
          </div>
        </motion.div>
      )}

      {retakeBlocked && !isLow && (
        <motion.div
          {...fadeIn(0.3)}
          className="rounded-xl bg-amber-500/10 border border-amber-500/20 px-4 py-3"
        >
          <p className="text-sm text-amber-300">
            {t("assessment.infoRetakeCooldown", { days: data.days_until_retake })}
          </p>
        </motion.div>
      )}

      {/* CTA */}
      <motion.div
        {...fadeUp(0.35, 8)}
      >
        <Button
          size="lg"
          className="w-full"
          disabled={retakeBlocked}
          onClick={() => {
            if (isMounted.current) {
              router.push(`/${locale}/assessment?competency=${encodeURIComponent(data.competency_slug)}`);
            }
          }}
        >
          {t("assessment.infoContinueButton")}
        </Button>
      </motion.div>
    </div>
  );
}
