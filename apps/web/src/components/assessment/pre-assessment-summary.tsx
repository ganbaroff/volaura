"use client";

import { useTranslation } from "react-i18next";
import { Clock, Target, Sparkles, ShieldCheck } from "lucide-react";

interface PreAssessmentSummaryProps {
  totalMinutes: number;
  competencyCount: number;
  crystalReward?: number;
}

/**
 * Compact "what to expect" panel shown before user starts an assessment.
 * Constitution Law 5: One Primary Action — informs without distracting from the main CTA.
 * Shame-free framing (Law 3): no "you should", just honest expectations.
 */
export function PreAssessmentSummary({
  totalMinutes,
  competencyCount,
  crystalReward = 50,
}: PreAssessmentSummaryProps) {
  const { t } = useTranslation();
  const totalCrystals = crystalReward * competencyCount;

  return (
    <div className="rounded-2xl border border-border bg-surface-container-low p-4 space-y-3">
      <p className="text-xs font-semibold text-foreground uppercase tracking-wide">
        {t("assessment.whatToExpect", { defaultValue: "What to expect" })}
      </p>

      <div className="grid gap-2.5">
        <div className="flex items-start gap-3">
          <Clock className="size-4 text-primary mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {t("assessment.expectTime", {
                minutes: totalMinutes,
                defaultValue: `~${totalMinutes} minutes`,
              })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("assessment.expectTimeNote", {
                defaultValue: "Pause and resume anytime — no pressure to finish in one go",
              })}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Target className="size-4 text-primary mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {t("assessment.expectAdaptive", {
                defaultValue: "Adaptive questions",
              })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("assessment.expectAdaptiveNote", {
                defaultValue: "Questions adjust to your level — no trick questions",
              })}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Sparkles className="size-4 text-primary mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {t("assessment.expectReward", {
                crystals: totalCrystals,
                defaultValue: `Earn ${totalCrystals} crystals + AURA score`,
              })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("assessment.expectRewardNote", {
                defaultValue: "Plus a verifiable badge for your profile",
              })}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <ShieldCheck className="size-4 text-primary mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {t("assessment.expectPrivate", {
                defaultValue: "Your data stays private",
              })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("assessment.expectPrivateNote", {
                defaultValue: "Only you decide what to share publicly",
              })}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
