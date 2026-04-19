"use client";

import { cn } from "@/lib/utils/cn";

interface ProgressBarProps {
  current: number; // 0-based answered count
  total: number;
  label: string; // translated: "Question progress"
  className?: string;
}

export function ProgressBar({
  current,
  total,
  label,
  className,
}: ProgressBarProps) {
  const pct = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;

  return (
    <div
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
      className={cn("w-full", className)}
    >
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500 ease-out motion-reduce:transition-none"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
