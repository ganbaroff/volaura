"use client";

import { cn } from "@/lib/utils/cn";

interface McqOption {
  key: string;
  text_en: string;
  text_az: string;
}

interface McqOptionsProps {
  options: McqOption[];
  selected: string | null; // selected option key
  onSelect: (optionKey: string) => void;
  disabled?: boolean;
  locale?: string;
}

const OPTION_LABELS = ["A", "B", "C", "D", "E"];

export function McqOptions({
  options,
  selected,
  onSelect,
  disabled = false,
  locale = "en",
}: McqOptionsProps) {
  return (
    <div className="space-y-3" role="radiogroup" aria-label="Answer options">
      {options.map((option, index) => {
        const isSelected = selected === option.key;
        const displayText = locale === "az" ? option.text_az : option.text_en;
        return (
          <button
            key={option.key}
            type="button"
            role="radio"
            disabled={disabled}
            aria-checked={isSelected}
            onClick={() => onSelect(option.key)}
            className={cn(
              "w-full flex items-center gap-3 rounded-xl border-2 p-4 text-left min-h-[52px]",
              "transition-all duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              isSelected
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-card hover:border-primary/40 hover:bg-accent/40 text-foreground"
            )}
          >
            <span
              className={cn(
                "shrink-0 size-7 rounded-full flex items-center justify-center text-xs font-bold",
                isSelected
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              )}
              aria-hidden="true"
            >
              {OPTION_LABELS[index] ?? index + 1}
            </span>
            <span className="text-sm font-medium">{displayText}</span>
          </button>
        );
      })}
    </div>
  );
}
