"use client";

import { useTranslation } from "react-i18next";
import { HeartHandshake, Pause, Sparkle } from "lucide-react";

/**
 * Pre-Assessment safety + psychotype block.
 *
 * Constitution P0 (E4): displayed before the first question alongside the
 * GDPR Art. 22 consent checkbox. Three short notes:
 *   1. Psychotype hint — the score reflects this attempt, not your worth.
 *   2. Pause / retake — you can stop anytime, no shame, retake possible.
 *   3. Confidentiality — what is private vs what you choose to share.
 *
 * Constitution Law 3 — shame-free language: no "you must", no "incomplete",
 * no profile-percent indicators. Reads as a teammate, not a compliance form.
 */
export function SafetyBlock() {
  const { t } = useTranslation();

  return (
    <div
      role="note"
      aria-labelledby="safety-block-title"
      className="rounded-2xl border border-border bg-surface-container-low p-4 space-y-3"
    >
      <p
        id="safety-block-title"
        className="text-xs font-semibold text-foreground uppercase tracking-wide"
      >
        {t("assessment.beforeYouStartTitle", { defaultValue: "Before you start" })}
      </p>

      <div className="grid gap-2.5">
        <div className="flex items-start gap-3">
          <Sparkle className="size-4 text-primary mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {t("assessment.psychotypeHintTitle", {
                defaultValue: "A snapshot, not a verdict",
              })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("assessment.psychotypeHint", {
                defaultValue:
                  "Your AURA score reflects how this assessment went today. It does not define you, your potential, or your worth as a person.",
              })}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Pause className="size-4 text-primary mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {t("assessment.pauseAnytimeTitle", {
                defaultValue: "Pause whenever",
              })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("assessment.pauseAnytime", {
                defaultValue:
                  "You can leave the page mid-question and come back later. The assessment can be retaken if you want a fresh attempt.",
              })}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <HeartHandshake className="size-4 text-primary mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {t("assessment.safetyNoteTitle", {
                defaultValue: "Your answers, your choice",
              })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("assessment.safetyNote", {
                defaultValue:
                  "Your responses stay private. Only the final score becomes part of your profile, and you decide whether to share it.",
              })}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
