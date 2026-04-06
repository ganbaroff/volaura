"use client";

import { useReducedMotion } from "framer-motion";

/**
 * Returns Framer Motion transition defaults based on user's motion preference.
 * Research #6: reduced motion is a clinical requirement for ADHD users, not a nice-to-have.
 */
export function useMotionPreference() {
  const shouldReduceMotion = useReducedMotion();

  return {
    shouldReduceMotion,
    transition: shouldReduceMotion
      ? { duration: 0 }
      : { type: "spring" as const, stiffness: 100, damping: 15 },
    entrance: shouldReduceMotion
      ? { initial: {}, animate: {} }
      : {
          initial: { opacity: 0, y: 20 },
          animate: { opacity: 1, y: 0 },
        },
    hoverScale: shouldReduceMotion ? {} : { whileHover: { scale: 1.02 } },
    tapScale: shouldReduceMotion ? {} : { whileTap: { scale: 0.98 } },
  };
}
