"use client";

/**
 * Crystal Balance Widget — shows the user's cross-product crystal balance.
 *
 * Crystals are earned on Volaura (assessment completion) and spent in
 * MindShift and Life Simulator. This widget surfaces the balance on the
 * Volaura dashboard so users understand the ecosystem connection.
 *
 * Design principles applied:
 *  - Progressive disclosure: widget only renders when user has crystals (> 0)
 *    or when they just earned some (crystals === 0 + has completed at least
 *    one assessment). Zero-crystal state for brand-new users is hidden.
 *  - Minimal cognitive load: one number, one icon, one CTA label.
 *  - i18n: all strings via t() — AZ text can be 20-30% longer.
 */

import { useTranslation } from "react-i18next";
import { Skeleton } from "@/components/ui/skeleton";
import { useCrystalBalance } from "@/hooks/queries/use-character";

interface CrystalBalanceWidgetProps {
  /** Force-show even if balance is 0 (e.g. right after first assessment). */
  forceShow?: boolean;
}

export function CrystalBalanceWidget({ forceShow = false }: CrystalBalanceWidgetProps) {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useCrystalBalance();

  if (isLoading) {
    return <Skeleton className="h-16 w-full rounded-xl" />;
  }

  // Null = no character events yet (balance is 0). Only show if forceShow.
  if (!data && !forceShow) return null;

  const balance = data?.crystal_balance ?? 0;

  // Hide the widget for users who have never earned crystals (reduces clutter
  // on the dashboard for new users who haven't completed an assessment yet).
  if (balance === 0 && !forceShow) return null;

  // Non-blocking: hide silently on API error — never break the dashboard.
  if (isError) return null;

  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3">
      {/* Crystal icon — amber to match the "precious resource" mental model */}
      <span className="text-2xl shrink-0" role="img" aria-label={t("character.crystalLabel")}>
        💎
      </span>

      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-muted-foreground leading-none mb-0.5">
          {t("character.crystalBalance")}
        </p>
        <p className="text-lg font-bold text-foreground leading-none tabular-nums">
          {balance.toLocaleString()}
          <span className="text-xs font-normal text-muted-foreground ml-1">
            {t("character.crystals")}
          </span>
        </p>
      </div>

      {/* Ecosystem hint — links crystal economy to MindShift */}
      <p className="text-[11px] text-muted-foreground text-right leading-snug shrink-0 max-w-[90px]">
        {t("character.earnOnVolaura")}
      </p>
    </div>
  );
}
