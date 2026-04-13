"use client";

import { cn } from "@/lib/utils/cn";
import { Button } from "./button";

/**
 * Empty State — shame-free messaging (Constitution Law 3)
 *
 * NEVER: "You haven't done X yet", "No X found", "0 results"
 * ALWAYS: encouraging, forward-looking, actionable
 *
 * Examples:
 * - "Start your first assessment" (not "No assessments")
 * - "Explore competencies" (not "You have no AURA score")
 * - "Your activity will appear here" (not "No activity found")
 */

interface EmptyStateProps {
  /** Encouraging headline */
  title: string;
  /** Optional supportive description */
  description?: string;
  /** Optional icon/illustration (emoji or React node) */
  icon?: React.ReactNode;
  /** Single CTA (Law 5) */
  ctaLabel?: string;
  onCtaClick?: () => void;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon,
  ctaLabel,
  onCtaClick,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center py-12 px-6",
        className,
      )}
    >
      {icon && (
        <div className="mb-4 text-4xl text-muted-foreground/60" aria-hidden="true">
          {icon}
        </div>
      )}
      <h3 className="text-base font-headline font-semibold text-foreground mb-1">
        {title}
      </h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-xs mb-6">
          {description}
        </p>
      )}
      {ctaLabel && onCtaClick && (
        <Button variant="primary" onClick={onCtaClick}>
          {ctaLabel}
        </Button>
      )}
    </div>
  );
}
