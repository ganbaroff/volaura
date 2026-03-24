"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ArrowRight, Star } from "lucide-react";

interface HeroSectionProps {
  locale: string;
}

const BADGE_PILLS = [
  { tier: "platinum", score: 94, labelKey: "aura.platinum", color: "from-slate-300 to-slate-400", text: "text-slate-900" },
  { tier: "gold", score: 81, labelKey: "aura.gold", color: "from-yellow-400 to-amber-500", text: "text-amber-900" },
  { tier: "silver", score: 67, labelKey: "aura.silver", color: "from-gray-300 to-gray-400", text: "text-gray-800" },
];

export function HeroSection({ locale }: HeroSectionProps) {
  const { t } = useTranslation();

  return (
    <section className="relative overflow-hidden bg-background py-20 md:py-32">
      {/* Background gradient */}
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
      >
        <div className="absolute left-1/2 top-0 -translate-x-1/2 h-[600px] w-[900px] rounded-full bg-primary/5 blur-3xl" />
      </div>

      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center text-center">
          {/* Badge pills (animated) */}
          <motion.div
            className="mb-8 flex flex-wrap justify-center gap-2"
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {BADGE_PILLS.map((pill, i) => (
              <motion.div
                key={pill.tier}
                className={`inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r ${pill.color} px-3 py-1 text-xs font-semibold ${pill.text} shadow-sm`}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <Star className="h-3 w-3 fill-current" aria-hidden="true" />
                {t(pill.labelKey)} · {pill.score}/100
              </motion.div>
            ))}
          </motion.div>

          {/* Headline */}
          <motion.h1
            className="mb-6 text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl md:text-6xl lg:text-7xl"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <span className="block">{t("landing.heroTitle")}</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="mb-10 max-w-2xl text-lg text-muted-foreground sm:text-xl"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {t("landing.heroSubtitle")}
          </motion.p>

          {/* CTAs */}
          <motion.div
            className="flex flex-col gap-3 sm:flex-row sm:gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Link
              href={`/${locale}/signup`}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-7 py-3.5 text-base font-semibold text-primary-foreground shadow-md transition-all hover:bg-primary/90 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              {t("landing.heroCta")}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link
              href={`/${locale}/signup`}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-border bg-background px-7 py-3.5 text-base font-semibold text-foreground transition-all hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              {t("landing.heroCtaOrg")}
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
