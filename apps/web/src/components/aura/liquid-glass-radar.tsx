"use client";

import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";
import { AuraRadarChart } from "./radar-chart";

/**
 * AURA Liquid Glass Radar — identity-first hero component
 *
 * Constitution compliance:
 * - Law 1: tier colors use aura-* tokens, never red
 * - Law 3: shame-free — shows growth direction, not deficiency
 * - Law 4: spring damping ≥14, max 800ms
 * - Law 5: single CTA "Retake Assessment" or "Start Assessment"
 *
 * Design: open-questions-resolved.md Q2 (CSS-only Liquid Glass)
 * Badge tiers: open-questions-resolved.md Q3 (static SVG per tier)
 */

const TIER_GLOWS: Record<string, string> = {
  platinum: "aura-glow-platinum",
  gold: "aura-glow-gold",
  silver: "aura-glow-silver",
  bronze: "",
  none: "",
};

const TIER_LABELS: Record<string, { labelKey: string; default: string }> = {
  platinum: { labelKey: "aura.tierPlatinum", default: "Platinum" },
  gold: { labelKey: "aura.tierGold", default: "Gold" },
  silver: { labelKey: "aura.tierSilver", default: "Silver" },
  bronze: { labelKey: "aura.tierBronze", default: "Bronze" },
  none: { labelKey: "aura.tierNone", default: "Unranked" },
};

interface LiquidGlassRadarProps {
  competencyScores: Record<string, number>;
  totalScore: number;
  badgeTier?: string;
  displayName: string;
  /** Single primary CTA — Constitution Law 5 */
  ctaLabel?: string;
  onCtaClick?: () => void;
}

export function LiquidGlassRadar({
  competencyScores,
  totalScore,
  badgeTier = "none",
  displayName,
  ctaLabel,
  onCtaClick,
}: LiquidGlassRadarProps) {
  const { t } = useTranslation();
  const tierInfo = TIER_LABELS[badgeTier] ?? TIER_LABELS.none;
  const glowClass = TIER_GLOWS[badgeTier] ?? "";

  return (
    <motion.section
      className={cn("liquid-glass p-6 mx-auto max-w-sm", glowClass)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: "spring",
        damping: 14,
        stiffness: 100,
        mass: 1,
      }}
      aria-label={t("aura.radarSection", {
        defaultValue: "Your AURA Profile",
      })}
    >
      {/* Identity-first headline (ecosystem-design-research.md: character-as-identity) */}
      <div className="text-center mb-4">
        <h2 className="text-lg font-headline font-bold text-foreground">
          {displayName}
        </h2>
        <div className="flex items-center justify-center gap-2 mt-1">
          <span
            className="text-2xl font-headline font-black"
            style={{ color: `var(--color-aura-${badgeTier}, var(--color-primary))` }}
          >
            {Math.round(totalScore)}
          </span>
          <span className="text-sm text-muted-foreground">
            {t(tierInfo.labelKey, { defaultValue: tierInfo.default })}
          </span>
        </div>
      </div>

      {/* Radar chart */}
      <AuraRadarChart
        competencyScores={competencyScores}
        badgeTier={badgeTier}
        size="md"
      />

      {/* Shame-free growth direction (Law 3) */}
      <p className="text-xs text-center text-muted-foreground mt-3">
        {t("aura.growthHint", {
          defaultValue: "Your strongest areas shine here. Keep exploring.",
        })}
      </p>

      {/* Single primary CTA (Law 5) */}
      {ctaLabel && onCtaClick && (
        <button
          onClick={onCtaClick}
          className="mt-4 w-full btn-primary-gradient rounded-xl py-3 text-sm font-semibold energy-target transition-all"
          style={{ transitionDuration: "var(--duration-fast)" } as React.CSSProperties}
        >
          {ctaLabel}
        </button>
      )}
    </motion.section>
  );
}
