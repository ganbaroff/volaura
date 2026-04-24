"use client";

/**
 * Welcome page — post-onboarding activation screen.
 * Focused single CTA: start the selected competency assessment.
 * No sidebar. No distractions. Highest-conversion screen in the funnel.
 *
 * Route: /[locale]/welcome?competency=communication
 */

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { API_BASE } from "@/lib/api/client";
import { buildLoginNextPath } from "../(dashboard)/auth-recovery";

// ── Types ──────────────────────────────────────────────────────────────────────

interface UserInfo {
  displayName: string | null;
}

// ── Competency icons (mirrors onboarding) ──────────────────────────────────────

const COMPETENCY_ICONS: Record<string, string> = {
  communication: "💬",
  reliability: "⏰",
  english_proficiency: "🌍",
  leadership: "🧭",
  event_performance: "🏆",
  tech_literacy: "💻",
  adaptability: "🔄",
  empathy_safeguarding: "🤝",
};

// ── Benefits list ─────────────────────────────────────────────────────────────

function BenefitItem({ text }: { text: string }) {
  return (
    <motion.li
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-3 text-sm text-muted-foreground"
    >
      <span className="mt-0.5 text-primary text-base leading-none">✓</span>
      <span>{text}</span>
    </motion.li>
  );
}

// ── Main content ──────────────────────────────────────────────────────────────

function WelcomeContent() {
  const { locale } = useParams<{ locale: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { t } = useTranslation();
  const isMounted = useRef(true);

  const [user, setUser] = useState<UserInfo | null>(null);
  const reauthPath = buildLoginNextPath(
    locale,
    `/${locale}/welcome${competency ? `?competency=${encodeURIComponent(competency)}` : ""}`
  );

  const competency = searchParams.get("competency") ?? "";
  const competencyIcon = COMPETENCY_ICONS[competency] ?? "⭐";
  const competencyLabel = competency
    ? t(`competency.${competency}`, { defaultValue: competency })
    : "";

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  // Redirect to login if not authenticated
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session && isMounted.current) {
        router.replace(reauthPath);
        return;
      }
      // Fetch display name from profile
      if (session) {
        fetch(`${API_BASE}/profiles/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        })
          .then((r) => r.json())
          .then((data: { display_name?: string | null }) => {
            if (isMounted.current) {
              setUser({ displayName: data?.display_name ?? null });
            }
          })
          .catch(() => {
            if (isMounted.current) setUser({ displayName: null });
          });
      }
    });
  }, [reauthPath, router]);

  const firstName = user?.displayName?.split(" ")[0] ?? t("welcome.defaultName");
  const assessmentHref = `/${locale}/assessment${competency ? `?competency=${competency}` : ""}`;

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-4 py-12 bg-background">
      {/* Ambient glows removed 2026-04-12 — Constitution Law 4 (Animation Safety) / Foundation
          Law 6 "motion only on achievement". Welcome is an action screen, not an achievement
          moment. Behavioural Nudge audit flagged this as continuous decorative motion. Kept in
          globals.css for use on AURA reveal (valid achievement context). */}

      <div className="relative z-10 w-full max-w-md space-y-8">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="text-center space-y-2"
        >
          <div className="text-4xl mb-3">🏆</div>
          <h1 className="text-2xl font-bold text-foreground">
            {t("welcome.title", { name: firstName })}
          </h1>
          <p className="text-muted-foreground text-sm">
            {t("welcome.subtitle")}
          </p>
        </motion.div>

        {/* What is AURA */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="rounded-2xl border border-border bg-card p-5 space-y-4"
        >
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
            {t("welcome.whatIsAura")}
          </p>
          <ul className="space-y-3">
            <BenefitItem text={t("welcome.benefit1")} />
            <BenefitItem text={t("welcome.benefit2")} />
            <BenefitItem text={t("welcome.benefit3")} />
          </ul>
        </motion.div>

        {/* Selected competency callout */}
        {competency && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="rounded-2xl border border-primary/30 bg-primary/5 px-5 py-4 flex items-center gap-4"
          >
            <span className="text-3xl">{competencyIcon}</span>
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">
                {t("welcome.selectedCompetency")}
              </p>
              <p className="font-semibold text-foreground">{competencyLabel}</p>
            </div>
          </motion.div>
        )}

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.25 }}
          className="space-y-3"
        >
          <Link
            href={assessmentHref}
            className="flex items-center justify-center w-full h-14 rounded-2xl bg-primary text-primary-foreground font-semibold text-base transition-all hover:opacity-90 active:scale-95 gap-2"
          >
            <span>
              {competency
                ? t("welcome.startCta", { competency: competencyLabel })
                : t("welcome.startCtaGeneric")}
            </span>
            <span className="text-xs opacity-70 font-normal">
              · {t("welcome.takes")}
            </span>
          </Link>

          <Link
            href={`/${locale}/dashboard`}
            className="flex items-center justify-center w-full h-10 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            {t("welcome.exploreCta")}
          </Link>
        </motion.div>

      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function WelcomePage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <div className="w-full max-w-lg space-y-6">
            <div className="h-10 w-64 mx-auto animate-pulse rounded bg-muted" />
            <div className="h-5 w-80 mx-auto animate-pulse rounded bg-muted" />
            <div className="h-12 w-full animate-pulse rounded-md bg-muted" />
          </div>
        </div>
      }
    >
      <WelcomeContent />
    </Suspense>
  );
}
