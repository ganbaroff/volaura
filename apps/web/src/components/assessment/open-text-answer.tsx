"use client";

import { useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/cn";

interface OpenTextAnswerProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export function OpenTextAnswer({
  value,
  onChange,
  disabled = false,
  placeholder,
  maxLength = 1000,
}: OpenTextAnswerProps) {
  const { t } = useTranslation();
  const resolvedPlaceholder = placeholder ?? t("assessment.answerPlaceholder");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);

  const remaining = maxLength - value.length;
  const isNearLimit = remaining <= 100;

  return (
    <div className="space-y-2">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={resolvedPlaceholder}
        maxLength={maxLength}
        rows={4}
        aria-label={resolvedPlaceholder}
        className={cn(
          "w-full resize-none rounded-xl border-2 bg-card px-4 py-3",
          "text-sm text-foreground placeholder:text-muted-foreground",
          "transition-colors duration-150 outline-none",
          "focus:border-primary",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "border-border min-h-[120px]"
        )}
      />
      <p
        className={cn(
          "text-right text-xs tabular-nums",
          isNearLimit ? "text-destructive" : "text-muted-foreground"
        )}
        aria-live="polite"
        aria-atomic="true"
      >
        {remaining} / {maxLength}
      </p>
    </div>
  );
}
