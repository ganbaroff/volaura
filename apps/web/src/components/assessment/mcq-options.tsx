"use client";

import { cn } from "@/lib/utils/cn";

interface McqOptionsProps {
  options: string[];
  selected: string | null;
  onSelect: (option: string) => void;
  disabled?: boolean;
}

const OPTION_LABELS = ["A", "B", "C", "D", "E"];

export function McqOptions({
  options,
  selected,
  onSelect,
  disabled = false,
}: McqOptionsProps) {
  return (
    <div className="space-y-3" role="group" aria-label="Answer options">
      {options.map((option, index) => {
        const isSelected = selected === option;
        return (
          <button
            key={option}
            type="button"
            disabled={disabled}
            aria-pressed={isSelected}
            onClick={() => onSelect(option)}
            className={cn(
              "w-full flex items-center gap-3 rounded-xl border-2 p-4 text-left",
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
            <span className="text-sm font-medium">{option}</span>
          </button>
        );
      })}
    </div>
  );
}
