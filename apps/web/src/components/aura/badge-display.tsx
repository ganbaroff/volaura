"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

type BadgeTier = "platinum" | "gold" | "silver" | "bronze" | "none";

interface BadgeDisplayProps {
  tier: BadgeTier;
  label: string; // translated tier name
  eliteLabel?: string; // translated "Elite"
  isElite?: boolean;
}

const TIER_STYLES: Record<BadgeTier, { bg: string; text: string; ring: string; glow: string }> = {
  platinum: {
    bg: "bg-gradient-to-br from-violet-500/20 to-purple-600/20",
    text: "text-violet-400",
    ring: "ring-violet-400/50",
    glow: "shadow-[0_0_24px_rgba(139,92,246,0.4)]",
  },
  gold: {
    bg: "bg-gradient-to-br from-yellow-400/20 to-amber-500/20",
    text: "text-yellow-400",
    ring: "ring-yellow-400/50",
    glow: "shadow-[0_0_24px_rgba(250,204,21,0.35)]",
  },
  silver: {
    bg: "bg-gradient-to-br from-slate-300/20 to-slate-400/20",
    text: "text-slate-300",
    ring: "ring-slate-300/50",
    glow: "shadow-[0_0_16px_rgba(148,163,184,0.25)]",
  },
  bronze: {
    bg: "bg-gradient-to-br from-amber-600/20 to-orange-700/20",
    text: "text-amber-600",
    ring: "ring-amber-600/50",
    glow: "shadow-[0_0_16px_rgba(180,83,9,0.25)]",
  },
  none: {
    bg: "bg-muted/40",
    text: "text-muted-foreground",
    ring: "ring-border",
    glow: "",
  },
};

export function BadgeDisplay({ tier, label, eliteLabel, isElite }: BadgeDisplayProps) {
  const style = TIER_STYLES[tier] ?? TIER_STYLES.none;

  return (
    <motion.div
      initial={{ scale: 0, rotate: -20 }}
      animate={{ scale: 1, rotate: 0 }}
      transition={{ type: "spring", stiffness: 220, damping: 18, delay: 0.6 }}
      className="flex flex-col items-center gap-2"
    >
      {/* Badge circle */}
      <motion.div
        animate={
          tier === "platinum"
            ? { boxShadow: ["0 0 16px rgba(139,92,246,0.3)", "0 0 32px rgba(139,92,246,0.5)", "0 0 16px rgba(139,92,246,0.3)"] }
            : tier === "gold"
              ? { boxShadow: ["0 0 12px rgba(250,204,21,0.2)", "0 0 24px rgba(250,204,21,0.4)", "0 0 12px rgba(250,204,21,0.2)"] }
              : {}
        }
        transition={
          tier === "platinum" || tier === "gold"
            ? { repeat: Infinity, duration: 2, ease: "easeInOut" }
            : {}
        }
        className={cn(
          "size-20 rounded-full flex items-center justify-center ring-2",
          style.bg,
          style.ring,
          style.glow
        )}
        role="img"
        aria-label={`${label} badge`}
      >
        <span className={cn("text-3xl font-black uppercase tracking-tight", style.text)}>
          {tier === "none" ? "—" : tier.charAt(0).toUpperCase()}
        </span>
      </motion.div>

      {/* Label */}
      <div className="text-center">
        <p className={cn("text-sm font-bold capitalize", style.text)}>
          {label}
          {isElite && eliteLabel && (
            <span className="ml-1.5 text-xs font-medium text-yellow-400">
              · {eliteLabel}
            </span>
          )}
        </p>
      </div>
    </motion.div>
  );
}
