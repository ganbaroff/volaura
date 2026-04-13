"use client";

import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/cn";

/**
 * Energy Picker — Constitution Law 2 (P0 Pre-Launch Blocker)
 *
 * Three energy modes control ENTIRE app behavior:
 * - Full: Standard UI, all animations, full density
 * - Mid: Reduced animations, larger targets (48px), hide secondary
 * - Low: Single CTA, max 3 elements, zero animation, muted
 *
 * Shame-free (Law 3): No judgment on energy level choice.
 * "How are you feeling?" not "How productive are you?"
 *
 * Accessible: radiogroup pattern, keyboard nav, focus ring
 */

export type EnergyLevel = "full" | "mid" | "low";

interface EnergyOption {
  level: EnergyLevel;
  icon: string;
  labelKey: string;
  descKey: string;
  defaultLabel: string;
  defaultDesc: string;
}

const OPTIONS: EnergyOption[] = [
  {
    level: "full",
    icon: "\u26A1",
    labelKey: "assessment.energyFull",
    descKey: "assessment.energyFullDesc",
    defaultLabel: "Full energy",
    defaultDesc: "I'm ready for a thorough assessment",
  },
  {
    level: "mid",
    icon: "\uD83C\uDF24",
    labelKey: "assessment.energyMid",
    descKey: "assessment.energyMidDesc",
    defaultLabel: "Medium energy",
    defaultDesc: "A balanced session works for me",
  },
  {
    level: "low",
    icon: "\uD83C\uDF19",
    labelKey: "assessment.energyLow",
    descKey: "assessment.energyLowDesc",
    defaultLabel: "Low energy",
    defaultDesc: "Keep it short and focused",
  },
];

interface EnergyPickerProps {
  value: EnergyLevel;
  onChange: (level: EnergyLevel) => void;
  /** Compact mode for settings/header placement */
  variant?: "default" | "compact";
}

export function EnergyPicker({
  value,
  onChange,
  variant = "default",
}: EnergyPickerProps) {
  const { t } = useTranslation();

  if (variant === "compact") {
    return (
      <div
        className="inline-flex items-center gap-1 rounded-xl bg-surface-container-high/50 p-1"
        role="radiogroup"
        aria-label={t("assessment.energyQuestion", {
          defaultValue: "Energy level",
        })}
      >
        {OPTIONS.map((opt) => (
          <button
            key={opt.level}
            type="button"
            role="radio"
            aria-checked={value === opt.level}
            aria-label={t(opt.labelKey, { defaultValue: opt.defaultLabel })}
            onClick={() => onChange(opt.level)}
            className={cn(
              "rounded-lg px-2 py-1.5 text-base transition-all",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
              value === opt.level
                ? "bg-primary/15 shadow-sm"
                : "hover:bg-surface-container-highest/50"
            )}
            style={{
              transitionDuration: "var(--duration-fast)",
            } as React.CSSProperties}
          >
            <span aria-hidden="true">{opt.icon}</span>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-foreground">
        {t("assessment.energyQuestion", {
          defaultValue: "How are you feeling right now?",
        })}
      </p>
      <div
        className="grid grid-cols-3 gap-2"
        role="radiogroup"
        aria-label={t("assessment.energyQuestion", {
          defaultValue: "How are you feeling right now?",
        })}
      >
        {OPTIONS.map((opt) => (
          <button
            key={opt.level}
            type="button"
            role="radio"
            aria-checked={value === opt.level}
            onClick={() => onChange(opt.level)}
            className={cn(
              "flex flex-col items-center gap-1 rounded-xl border p-3 transition-all energy-target",
              "hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
              value === opt.level
                ? "border-primary bg-primary/10 shadow-sm"
                : "border-border bg-card"
            )}
            style={{
              transitionDuration: "var(--duration-fast)",
            } as React.CSSProperties}
          >
            <span className="text-2xl" aria-hidden="true">
              {opt.icon}
            </span>
            <span className="text-xs font-semibold text-foreground">
              {t(opt.labelKey, { defaultValue: opt.defaultLabel })}
            </span>
            <span className="text-[10px] text-muted-foreground text-center leading-tight">
              {t(opt.descKey, { defaultValue: opt.defaultDesc })}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
