"use client";

import { cn } from "@/lib/utils/cn";
import { CheckCircle2 } from "lucide-react";

interface CompetencyCardProps {
  id: string;
  label: string;
  description?: string;
  estimatedMinutes: number;
  estimatedLabel: string; // already translated: "~5 min"
  isSelected: boolean;
  onToggle: (id: string) => void;
}

export function CompetencyCard({
  id,
  label,
  description,
  estimatedMinutes: _estimatedMinutes,
  estimatedLabel,
  isSelected,
  onToggle,
}: CompetencyCardProps) {
  return (
    <button
      type="button"
      aria-pressed={isSelected}
      onClick={() => onToggle(id)}
      className={cn(
        "w-full text-left rounded-xl border-2 p-4 transition-all duration-200 motion-reduce:transition-none",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        isSelected
          ? "border-primary bg-primary/5"
          : "border-border bg-card hover:border-primary/50 hover:bg-accent/50"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-foreground">{label}</p>
          {description && (
            <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
              {description}
            </p>
          )}
          <span className="mt-2 inline-block text-xs text-muted-foreground">
            {estimatedLabel}
          </span>
        </div>
        <div
          className={cn(
            "shrink-0 mt-0.5 transition-colors",
            isSelected ? "text-primary" : "text-muted-foreground/30"
          )}
        >
          <CheckCircle2 className="size-5" aria-hidden="true" />
        </div>
      </div>
    </button>
  );
}
