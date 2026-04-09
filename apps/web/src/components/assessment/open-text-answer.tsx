"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Mic, MicOff } from "lucide-react";
import { cn } from "@/lib/utils/cn";

// Extend Window for webkit-prefixed SpeechRecognition (Safari/older Chrome)
type SpeechRecognitionCtor = typeof SpeechRecognition;
declare global {
  interface Window {
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  }
}

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
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [supported, setSupported] = useState(false);

  // Detect support client-side only (SSR safe)
  useEffect(() => {
    setSupported(!!(window.SpeechRecognition ?? window.webkitSpeechRecognition));
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const startListening = useCallback(() => {
    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!SR) return;

    const recognition = new SR();
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0][0].transcript;
      onChange(value ? `${value} ${transcript}` : transcript);
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, [value, onChange]);

  const remaining = maxLength - value.length;
  const isNearLimit = remaining <= 100;

  return (
    <div className="space-y-2">
      <div className="relative">
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
            "border-border min-h-[120px]",
            supported && "pr-14"
          )}
        />
        {supported && (
          <button
            type="button"
            onClick={isListening ? stopListening : startListening}
            disabled={disabled}
            aria-label={isListening ? t("assessment.voiceHint") : t("assessment.voiceHint")}
            aria-pressed={isListening}
            className={cn(
              "absolute right-3 top-3",
              "flex items-center justify-center",
              "min-w-[44px] min-h-[44px] rounded-lg",
              "transition-colors duration-150",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              isListening
                ? "bg-destructive/10 text-destructive hover:bg-destructive/20"
                : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
            )}
          >
            {isListening ? (
              <MicOff className="size-5" aria-hidden="true" />
            ) : (
              <Mic className="size-5" aria-hidden="true" />
            )}
          </button>
        )}
      </div>
      <div className="flex items-center justify-between gap-2">
        {supported && (
          <p className="text-xs text-muted-foreground">{t("assessment.voiceHint")}</p>
        )}
        <p
          className={cn(
            "text-xs tabular-nums ml-auto",
            isNearLimit ? "text-destructive" : "text-muted-foreground"
          )}
          aria-live="polite"
          aria-atomic="true"
        >
          {remaining} / {maxLength}
        </p>
      </div>
    </div>
  );
}
