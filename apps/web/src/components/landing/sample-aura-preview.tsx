"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ArrowRight, Shield } from "lucide-react";
import { cn } from "@/lib/utils/cn";

/**
 * Sunk-Cost Registration — Constitution v1.7 / VOLAURA Rule 28.
 *
 * Shows a fictional "Leyla" AURA profile (Communication 74, Silver tier) on the
 * landing page before the visitor ever creates an account. The bet: seeing the
 * artefact you would earn makes the signup feel like retrieving something that
 * is already yours. No leaderboard framing (Crystal Law 5), no comparison with
 * the visitor, just a concrete picture of the outcome.
 *
 * Accessibility: clearly labeled as a sample. "Not a real profile" disclosure
 * meets transparency expectations and avoids the impression of stolen identity.
 */

interface SampleCompetency {
  slug: string;
  score: number;
  labelKey: string;
}

const SAMPLE_LEYLA: { name: string; tier: string; tierColor: string; primary: SampleCompetency; others: SampleCompetency[] } = {
  name: "Leyla Mammadova",
  tier: "silver",
  tierColor: "from-gray-300 to-gray-400",
  primary: {
    slug: "communication",
    score: 74,
    labelKey: "competency.communication",
  },
  others: [
    { slug: "reliability", score: 68, labelKey: "competency.reliability" },
    { slug: "english_proficiency", score: 71, labelKey: "competency.english_proficiency" },
    { slug: "leadership", score: 62, labelKey: "competency.leadership" },
  ],
};

interface SampleAuraPreviewProps {
  locale: string;
}

export function SampleAuraPreview({ locale }: SampleAuraPreviewProps) {
  const { t } = useTranslation();

  return (
    <section
      className="bg-muted/30 py-16"
      aria-labelledby="sample-aura-heading"
    >
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8 text-center">
          <h2
            id="sample-aura-heading"
            className="text-3xl font-headline font-bold tracking-tight text-foreground sm:text-4xl"
          >
            {t("landing.samplePreviewTitle", {
              defaultValue: "What your profile could look like",
            })}
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {t("landing.samplePreviewSubtitle", {
              defaultValue: "Sample profile — no account required to preview",
            })}
          </p>
        </div>

        <motion.article
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5 }}
          className="rounded-3xl border border-border bg-card p-6 shadow-lg sm:p-8"
          aria-label={t("landing.sampleProfileAria", {
            defaultValue: "Sample AURA profile preview",
          })}
        >
          {/* "Sample" watermark */}
          <div className="mb-4 inline-flex items-center gap-1.5 rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
            <Shield className="size-3" aria-hidden="true" />
            {t("landing.sampleBadge", { defaultValue: "Sample profile" })}
          </div>

          <div className="grid gap-6 sm:grid-cols-[1fr_auto]">
            {/* Left: identity + primary score */}
            <div className="space-y-4">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">
                  {t("landing.sampleFictionalLabel", { defaultValue: "Fictional example" })}
                </p>
                <p className="text-2xl font-semibold text-foreground">{SAMPLE_LEYLA.name}</p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">
                  {t(SAMPLE_LEYLA.primary.labelKey, {
                    defaultValue: SAMPLE_LEYLA.primary.slug,
                  })}
                </p>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-5xl font-extrabold tabular-nums text-foreground">
                    {SAMPLE_LEYLA.primary.score}
                  </span>
                  <span className="text-base text-muted-foreground">/ 100</span>
                </div>
              </div>

              {/* Other competencies — compact list */}
              <ul className="space-y-1.5 text-sm">
                {SAMPLE_LEYLA.others.map((c) => (
                  <li key={c.slug} className="flex items-center justify-between gap-4">
                    <span className="text-muted-foreground">
                      {t(c.labelKey, { defaultValue: c.slug })}
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary/60"
                          style={{ width: `${c.score}%` }}
                        />
                      </div>
                      <span className="w-8 text-right tabular-nums font-medium text-foreground">
                        {c.score}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Right: badge tier */}
            <div className="flex flex-col items-center justify-center gap-2 sm:min-w-[140px]">
              <div
                className={cn(
                  "flex size-20 items-center justify-center rounded-full bg-gradient-to-br shadow-md",
                  SAMPLE_LEYLA.tierColor
                )}
                aria-hidden="true"
              >
                <span className="text-xs font-bold uppercase tracking-wider text-gray-800">
                  {t(`aura.${SAMPLE_LEYLA.tier}`, { defaultValue: SAMPLE_LEYLA.tier })}
                </span>
              </div>
              <p className="text-xs text-muted-foreground text-center">
                {t("landing.sampleBadgeLabel", { defaultValue: "Badge tier" })}
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-6 flex flex-col items-center gap-2 border-t border-border pt-6 sm:flex-row sm:justify-between">
            <p className="text-sm text-muted-foreground text-center sm:text-left">
              {t("landing.sampleCtaPrompt", {
                defaultValue: "Take the assessment and earn your own verified profile.",
              })}
            </p>
            <Link
              href={`/${locale}/signup`}
              className="inline-flex items-center gap-2 rounded-xl btn-primary-gradient px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-all hover:shadow-md energy-target focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              {t("landing.heroCta", { defaultValue: "Get started" })}
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
          </div>
        </motion.article>
      </div>
    </section>
  );
}
