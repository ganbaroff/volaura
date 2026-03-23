"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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

  return (
    <div
      className="flex items-center gap-1.5"
      aria-label={`${label}: ${timeStr}`}
    >
      <motion.div
        animate={isCritical ? { scale: [1, 1.15, 1] } : { scale: 1 }}
        transition={isCritical ? { repeat: Infinity, duration: 0.8 } : {}}
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
          aria-live="off" // parent has the aria-label
        >
          {timeStr}
        </motion.span>
      </AnimatePresence>
    </div>
  );
}
