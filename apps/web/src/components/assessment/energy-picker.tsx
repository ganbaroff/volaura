"use client";

import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/cn";

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
    icon: "⚡",
    labelKey: "assessment.energyFull",
    descKey: "assessment.energyFullDesc",
    defaultLabel: "Full energy",
    defaultDesc: "I'm ready for a thorough assessment",
  },
  {
    level: "mid",
    icon: "🌤",
    labelKey: "assessment.energyMid",
    descKey: "assessment.energyMidDesc",
    defaultLabel: "Medium energy",
    defaultDesc: "A balanced session works for me",
  },
  {
    level: "low",
    icon: "🌙",
    labelKey: "assessment.energyLow",
    descKey: "assessment.energyLowDesc",
    defaultLabel: "Low energy",
    defaultDesc: "Keep it short and focused",
  },
];

interface EnergyPickerProps {
  value: EnergyLevel;
  onChange: (level: EnergyLevel) => void;
}

export function EnergyPicker({ value, onChange }: EnergyPickerProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-foreground">
        {t("assessment.energyQuestion", {
          defaultValue: "How are you feeling right now?",
        })}
      </p>
      <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label={t("assessment.energyQuestion", { defaultValue: "How are you feeling right now?" })}>
        {OPTIONS.map((opt) => (
          <button
            key={opt.level}
            type="button"
            role="radio"
            aria-checked={value === opt.level}
            onClick={() => onChange(opt.level)}
            className={cn(
              "flex flex-col items-center gap-1 rounded-xl border p-3 transition-all",
              "hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
              value === opt.level
                ? "border-primary bg-primary/10 shadow-sm"
                : "border-border bg-card"
            )}
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
