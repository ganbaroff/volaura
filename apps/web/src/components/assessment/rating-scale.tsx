"use client";

import { cn } from "@/lib/utils/cn";

interface RatingScaleProps {
  value: number | null;
  min?: number;
  max?: number;
  minLabel?: string;
  maxLabel?: string;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export function RatingScale({
  value,
  min = 1,
  max = 5,
  minLabel,
  maxLabel,
  onChange,
  disabled = false,
}: RatingScaleProps) {
  const steps = Array.from({ length: max - min + 1 }, (_, i) => min + i);

  return (
    <div className="space-y-3">
      <div
        role="radiogroup"
        aria-label="Rating scale"
        className="flex items-center justify-between gap-2"
      >
        {steps.map((step) => {
          const isSelected = value === step;
          return (
            <button
              key={step}
              type="button"
              role="radio"
              aria-checked={isSelected}
              aria-label={`Rating ${step}`}
              disabled={disabled}
              onClick={() => onChange(step)}
              className={cn(
                "flex-1 flex flex-col items-center gap-1.5 rounded-xl border-2 py-3 px-1",
                "transition-all duration-150 motion-reduce:transition-none",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                isSelected
                  ? "border-primary bg-primary text-primary-foreground shadow-md scale-105"
                  : "border-border bg-card hover:border-primary/40 text-foreground"
              )}
            >
              <span className="text-base font-bold">{step}</span>
            </button>
          );
        })}
      </div>
      {(minLabel || maxLabel) && (
        <div className="flex justify-between text-xs text-muted-foreground px-1">
          <span>{minLabel}</span>
          <span>{maxLabel}</span>
        </div>
      )}
    </div>
  );
}
