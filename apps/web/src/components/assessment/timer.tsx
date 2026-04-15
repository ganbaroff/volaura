"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils/cn";
import { Clock } from "lucide-react";

interface TimerProps {
  totalSeconds: number;
  onExpire: () => void;
  label: string; // translated: "Time remaining"
  warningThreshold?: number; // seconds at which to show warning color
}

export function Timer({
  totalSeconds,
  onExpire,
  label,
  warningThreshold = 10,
}: TimerProps) {
  const [remaining, setRemaining] = useState(totalSeconds);
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;

  useEffect(() => {
    setRemaining(totalSeconds);
  }, [totalSeconds]);

  useEffect(() => {
    if (remaining <= 0) {
      onExpireRef.current();
      return;
    }
    const id = setTimeout(() => setRemaining((r) => r - 1), 1000);
    return () => clearTimeout(id);
  }, [remaining]);

  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;
  const timeStr = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  const isWarning = remaining <= warningThreshold;
  const isCritical = remaining <= 5;
  // T1-4 (a11y ghost-audit 2026-04-15): infinite clock pulse → vestibular risk.
  const prefersReducedMotion = useReducedMotion();
  const shouldPulse = isCritical && !prefersReducedMotion;

  // T0-3 (ghost-audit a11y P0-4, 2026-04-15): AT used to be told the initial
  // value at mount and never again because aria-live was "off". Users on
  // screen readers couldn't perceive time pressure. Fix: role="timer" +
  // aria-live="polite" on threshold transitions only (not every second —
  // that would spam the SR).
  const announceLive = isCritical || (remaining === 60 || remaining === 30 || remaining === 10);

  return (
    <div
      role="timer"
      className="flex items-center gap-1.5"
      aria-label={`${label}: ${timeStr}`}
    >
      <motion.div
        animate={shouldPulse ? { scale: [1, 1.15, 1] } : { scale: 1 }}
        transition={shouldPulse ? { repeat: Infinity, duration: 0.8 } : {}}
      >
        <Clock
          className={cn(
            "size-4 transition-colors",
            isWarning ? "text-destructive" : "text-muted-foreground"
          )}
          aria-hidden="true"
        />
      </motion.div>
      <AnimatePresence mode="wait">
        <motion.span
          key={timeStr}
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 4 }}
          transition={{ duration: 0.15 }}
          className={cn(
            "text-sm font-mono font-semibold tabular-nums transition-colors",
            isWarning ? "text-destructive" : "text-foreground"
          )}
          aria-live={announceLive ? "polite" : "off"}
          aria-atomic="true"
        >
          {timeStr}
        </motion.span>
      </AnimatePresence>
    </div>
  );
}
