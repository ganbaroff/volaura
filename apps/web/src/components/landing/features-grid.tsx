"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import {
  BarChart3,
  Award,
  UserCheck,
} from "lucide-react";

/**
 * FeaturesGrid — ADHD-first: 3 cards max (not 6)
 *
 * Constitution:
 * - ADHD research: max 3 feature cards on landing (reduce decision fatigue)
 * - Law 4: spring physics for card entrance
 * - Law 5: no CTA per card — page-level CTA only
 */

const FEATURES = [
  { key: "1", Icon: BarChart3, color: "text-blue-500", bg: "bg-blue-500/10" },
  { key: "2", Icon: Award, color: "text-yellow-500", bg: "bg-yellow-500/10" },
  { key: "3", Icon: UserCheck, color: "text-emerald-500", bg: "bg-emerald-500/10" },
] as const;

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { type: "spring" as const, damping: 14, stiffness: 100 } },
};

export function FeaturesGrid() {
  const { t } = useTranslation();

  return (
    <section className="py-20 md:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-14 text-center">
          <h2 className="mb-3 text-3xl font-headline font-bold tracking-tight text-foreground sm:text-4xl">
            {t("landing.featuresTitle")}
          </h2>
          <p className="text-lg text-muted-foreground">
            {t("landing.featuresSubtitle")}
          </p>
        </div>

        {/* Grid — 3 cards (ADHD-first) */}
        <motion.div
          className="grid grid-cols-1 gap-5 sm:grid-cols-3"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
        >
          {FEATURES.map(({ key, Icon, color, bg }) => (
            <motion.div
              key={key}
              variants={cardVariants}
              className="group rounded-2xl border border-border bg-card energy-p shadow-sm transition-shadow hover:shadow-md"
              style={{ transitionDuration: "var(--duration-fast)" } as React.CSSProperties}
            >
              <div className={`mb-4 inline-flex rounded-xl ${bg} p-3`}>
                <Icon className={`h-6 w-6 ${color}`} aria-hidden="true" />
              </div>
              <h3 className="mb-2 text-lg font-headline font-semibold text-foreground">
                {t(`landing.feature${key}Title`)}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {t(`landing.feature${key}Desc`)}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
