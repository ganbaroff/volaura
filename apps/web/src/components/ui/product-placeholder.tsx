"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { TopBar } from "@/components/layout/top-bar";
import { useEnergyMode } from "@/hooks/use-energy-mode";

interface ProductPlaceholderProps {
  name: string;
  icon: string;
  tagline: string;
  accentVar: string;
}

export function ProductPlaceholder({
  name,
  icon,
  tagline,
  accentVar,
}: ProductPlaceholderProps) {
  const { t } = useTranslation();
  const { energy } = useEnergyMode();
  const reducedMotion = useReducedMotion();
  const noMotion = reducedMotion || energy === "low";

  return (
    <>
      <TopBar title={name} showEnergyPicker={false} />
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
        <motion.div
          initial={noMotion ? {} : { opacity: 0, scale: 0.9, y: 20 }}
          animate={noMotion ? {} : { opacity: 1, scale: 1, y: 0 }}
          transition={noMotion ? { duration: 0 } : { type: "spring", damping: 14, stiffness: 100 }}
          className="space-y-4"
        >
          <span
            className="inline-block text-6xl"
            style={noMotion ? undefined : { filter: `drop-shadow(0 0 12px ${accentVar})` }}
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
          {energy !== "low" && (
            <p className="text-base text-muted-foreground max-w-xs mx-auto">
              {tagline}
            </p>
          )}
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
