"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { TopBar } from "@/components/layout/top-bar";

/**
 * Product Placeholder — "Coming Soon" page for unreleased ecosystem products
 *
 * Constitution:
 * - Law 3: shame-free — exciting, forward-looking
 * - Law 4: spring entrance animation
 * - Law 5: no CTA (nothing to do yet)
 *
 * Products: MindShift, Life Simulator, ATLAS
 */

interface ProductPlaceholderProps {
  /** Product display name */
  name: string;
  /** Product emoji/icon */
  icon: string;
  /** One-line description */
  tagline: string;
  /** CSS variable for accent color (e.g., "var(--color-product-mindshift)") */
  accentVar: string;
}

export function ProductPlaceholder({
  name,
  icon,
  tagline,
  accentVar,
}: ProductPlaceholderProps) {
  const { t } = useTranslation();

  return (
    <>
      <TopBar title={name} showEnergyPicker={false} />
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ type: "spring", damping: 14, stiffness: 100 }}
          className="space-y-4"
        >
          <span
            className="inline-block text-6xl"
            style={{ filter: `drop-shadow(0 0 12px ${accentVar})` }}
            aria-hidden="true"
          >
            {icon}
          </span>
          <h1
            className="text-3xl font-headline font-bold"
            style={{ color: accentVar }}
          >
            {name}
          </h1>
          <p className="text-base text-muted-foreground max-w-xs mx-auto">
            {tagline}
          </p>
          <div className="liquid-glass inline-block rounded-xl px-6 py-3 mt-4">
            <p className="text-sm font-medium text-foreground">
              {t("common.comingSoon", { defaultValue: "Coming soon" })}
            </p>
          </div>
        </motion.div>
      </div>
    </>
  );
}
