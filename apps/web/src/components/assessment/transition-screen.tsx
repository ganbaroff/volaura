"use client";

import { motion, useReducedMotion } from "framer-motion";
import { CheckCircle2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface TransitionScreenProps {
  completedLabel: string;   // e.g. "Communication complete ✓"
  continueLabel: string;    // e.g. "Continue to Leadership"
  onContinue: () => void;
}

export function TransitionScreen({
  completedLabel,
  continueLabel,
  onContinue,
}: TransitionScreenProps) {
  const prefersReduced = useReducedMotion();
  return (
    <motion.div
      initial={prefersReduced ? false : { opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={prefersReduced ? undefined : { opacity: 0, scale: 0.95 }}
      transition={prefersReduced ? { duration: 0 } : { duration: 0.3, ease: "easeOut" }}
      className="flex flex-col items-center justify-center gap-6 py-16 text-center"
      role="status"
      aria-live="polite"
    >
      <motion.div
        initial={prefersReduced ? false : { scale: 0 }}
        animate={{ scale: 1 }}
        transition={prefersReduced ? { duration: 0 } : { type: "spring", stiffness: 260, damping: 20, delay: 0.1 }}
      >
        <CheckCircle2 className="size-16 text-primary" aria-hidden="true" />
      </motion.div>

      <motion.p
        initial={prefersReduced ? false : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={prefersReduced ? { duration: 0 } : { delay: 0.2 }}
        className="text-lg font-semibold text-foreground"
      >
        {completedLabel}
      </motion.p>

      <motion.div
        initial={prefersReduced ? false : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={prefersReduced ? { duration: 0 } : { delay: 0.35 }}
      >
        <Button onClick={onContinue} size="lg" className="gap-2">
          {continueLabel}
          <ArrowRight className="size-4" aria-hidden="true" />
        </Button>
      </motion.div>
    </motion.div>
  );
}
