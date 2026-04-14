"use client";

import { useTranslation } from "react-i18next";
import { Users } from "lucide-react";
import { useCommunitySignal } from "@/hooks/queries/use-community-signal";

/**
 * Constitution G44 — small inline social-proof line.
 * Shows "247 professionals took an assessment this week" style text.
 * No competitive framing, no ranking, no per-user data (Crystal Law 5).
 *
 * Design choice: show `professionals_this_week` not `_today` — today can be
 * a zero for the first hour after midnight and cause flicker; week is more
 * stable and equally honest.
 *
 * Silent when data unavailable or count is 0 (new deploy, no signal yet) —
 * a zero-signal is worse than no-signal (Law 3 shame-free applies to empty
 * rooms too).
 */
export function CommunitySignalInline() {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useCommunitySignal();

  if (isLoading || isError) return null;
  if (!data || data.professionals_this_week === 0) return null;

  return (
    <div
      className="flex items-center gap-2 text-sm text-muted-foreground"
      aria-label={t("community.signalAriaLabel", {
        defaultValue: "Community activity this week",
      })}
    >
      <Users className="size-4" aria-hidden="true" />
      <span>
        {t("community.signalThisWeek", {
          count: data.professionals_this_week,
          defaultValue_one: "{{count}} professional took an assessment this week",
          defaultValue_other: "{{count}} professionals took an assessment this week",
          defaultValue: `${data.professionals_this_week} professionals took an assessment this week`,
        })}
      </span>
    </div>
  );
}
