"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils/cn";

/**
 * Toast System — Constitution Law 1 compliant
 *
 * - Errors: purple (#D4B4FF bg, NEVER red)
 * - Warnings: amber (#E9C400 bg)
 * - Success: green (colorblind-safe)
 * - Info: primary/neutral
 *
 * Position: top-center (bottom is occupied by tab bar)
 * Auto-dismiss: 5s for info/success, errors persist until dismissed
 * Law 4: enter animation 300ms spring, exit 150ms
 */

type ToastType = "info" | "success" | "warning" | "error";

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  dismissible?: boolean;
}

const typeStyles: Record<ToastType, string> = {
  info: "bg-surface-container-high text-on-surface border-border",
  success: "bg-success-container text-on-success-container border-success/30",
  warning: "bg-warning-container text-on-warning-container border-warning/30",
  error: "bg-error-container text-on-error-container border-error/30",
};

const typeIcons: Record<ToastType, string> = {
  info: "ℹ️",
  success: "✓",
  warning: "⚠",
  error: "!",
};

// Simple toast store (no external dependency)
let listeners: Array<(toasts: Toast[]) => void> = [];
let toasts: Toast[] = [];

function notify(newToasts: Toast[]) {
  toasts = newToasts;
  listeners.forEach((l) => l(toasts));
}

export function toast(message: string, type: ToastType = "info") {
  const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const newToast: Toast = { id, type, message, dismissible: true };
  notify([...toasts, newToast]);

  // Auto-dismiss (errors persist)
  if (type !== "error") {
    setTimeout(() => {
      notify(toasts.filter((t) => t.id !== id));
    }, 5000);
  }

  return id;
}

export function dismissToast(id: string) {
  notify(toasts.filter((t) => t.id !== id));
}

/** Place <Toaster /> once in root layout */
export function Toaster() {
  const [currentToasts, setCurrentToasts] = useState<Toast[]>([]);

  useEffect(() => {
    listeners.push(setCurrentToasts);
    return () => {
      listeners = listeners.filter((l) => l !== setCurrentToasts);
    };
  }, []);

  return (
    <div
      className="fixed top-4 left-1/2 -translate-x-1/2 flex flex-col gap-2 w-full max-w-sm px-4"
      style={{ zIndex: "var(--z-toast)" } as React.CSSProperties}
      role="region"
      aria-label="Notifications"
    >
      <AnimatePresence>
        {currentToasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{
              type: "spring",
              damping: 14,
              stiffness: 100,
            }}
            className={cn(
              "flex items-center gap-3 rounded-xl border px-4 py-3 shadow-lg",
              typeStyles[t.type],
            )}
            role="alert"
            aria-live={t.type === "error" ? "assertive" : "polite"}
          >
            <span className="text-sm" aria-hidden="true">
              {typeIcons[t.type]}
            </span>
            <p className="flex-1 text-sm font-medium">{t.message}</p>
            {t.dismissible && (
              <button
                onClick={() => dismissToast(t.id)}
                className="ml-2 rounded-lg p-1 hover:bg-surface-container-highest/50 transition-colors"
                style={{ transitionDuration: "var(--duration-fast)" } as React.CSSProperties}
                aria-label="Dismiss"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
