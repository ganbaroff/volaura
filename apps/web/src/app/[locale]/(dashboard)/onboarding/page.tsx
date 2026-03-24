"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "@/stores/auth-store";

// ── Types ──────────────────────────────────────────────────────────────────────

type Step = 1 | 2 | 3;

interface CompetencyInfo {
  slug: string;
  icon: string;
  minutes: number;
}

const COMPETENCIES: CompetencyInfo[] = [
  { slug: "communication",      icon: "💬", minutes: 5 },
  { slug: "reliability",        icon: "⏰", minutes: 4 },
  { slug: "english_proficiency",icon: "🌍", minutes: 5 },
  { slug: "leadership",         icon: "🧭", minutes: 5 },
  { slug: "event_performance",  icon: "🏆", minutes: 4 },
  { slug: "tech_literacy",      icon: "💻", minutes: 4 },
  { slug: "adaptability",       icon: "🔄", minutes: 4 },
  { slug: "empathy_safeguarding",icon: "🤝", minutes: 3 },
];

// ── Page ──────────────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const displayName = useAuthStore((s) => s.user?.user_metadata?.display_name ?? s.user?.email ?? "");

  const [step, setStep] = useState<Step>(1);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  function goNext() {
    if (step < 3) setStep((s) => (s + 1) as Step);
  }
  function goBack() {
    if (step > 1) setStep((s) => (s - 1) as Step);
  }
  function skip() {
    router.push(`/${locale}/dashboard`);
  }
  function startAssessment() {
    router.push(`/${locale}/assessment`);
  }

  const slideVariants = {
    enter: { opacity: 0, x: 40 },
    center: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -40 },
  };

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {/* Ambient glows */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] ambient-glow-primary pointer-events-none z-0" />
      <div className="fixed bottom-[-5%] right-[-5%] w-[30%] h-[30%] ambient-glow-secondary pointer-events-none z-0" />

      <div className="relative z-10 w-full max-w-lg">
        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-8">
          {([1, 2, 3] as Step[]).map((s) => (
            <div
              key={s}
              className={`h-2 rounded-full transition-all duration-300 ${
                s === step ? "w-8 bg-primary" : s < step ? "w-2 bg-primary/50" : "w-2 bg-surface-container-high"
              }`}
            />
          ))}
        </div>

        {/* Step content */}
        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div
              key="step1"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="space-y-8 text-center"
            >
              <div className="text-7xl">🌟</div>
              <div className="space-y-3">
                <h1 className="text-3xl font-bold text-on-surface">
                  {t("onboarding.step1Title", { name: displayName?.split(" ")[0] || t("onboarding.defaultName") })}
                </h1>
                <p className="text-on-surface-variant text-base max-w-sm mx-auto">
                  {t("onboarding.step1Desc")}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-left">
                {[
                  { icon: "🎯", key: "onboarding.benefit1" },
                  { icon: "🏅", key: "onboarding.benefit2" },
                  { icon: "🔍", key: "onboarding.benefit3" },
                  { icon: "📈", key: "onboarding.benefit4" },
                ].map(({ icon, key }) => (
                  <div key={key} className="flex items-start gap-2 p-3 bg-surface-container-low rounded-xl">
                    <span className="text-xl">{icon}</span>
                    <p className="text-sm text-on-surface-variant">{t(key)}</p>
                  </div>
                ))}
              </div>

              <button
                onClick={goNext}
                className="w-full h-12 rounded-2xl bg-primary text-on-primary font-semibold text-base transition-all hover:opacity-90 active:scale-95"
              >
                {t("onboarding.step1Cta")}
              </button>
              <button onClick={skip} className="w-full text-sm text-on-surface-variant hover:text-on-surface transition-colors">
                {t("onboarding.skip")}
              </button>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-on-surface">{t("onboarding.step2Title")}</h2>
                <p className="text-sm text-on-surface-variant">{t("onboarding.step2Desc")}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {COMPETENCIES.map(({ slug, icon, minutes }) => (
                  <button
                    key={slug}
                    onClick={() => setSelectedSlug(slug === selectedSlug ? null : slug)}
                    className={`p-4 rounded-2xl text-left transition-all border-2 ${
                      selectedSlug === slug
                        ? "border-primary bg-primary/10"
                        : "border-transparent bg-surface-container-low hover:bg-surface-container-high"
                    }`}
                  >
                    <div className="text-2xl mb-2">{icon}</div>
                    <p className="text-sm font-semibold text-on-surface">{t(`competency.${slug}`)}</p>
                    <p className="text-xs text-on-surface-variant mt-0.5">~{minutes} {t("onboarding.min")}</p>
                  </button>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={goBack}
                  className="h-12 px-6 rounded-2xl bg-surface-container-high text-on-surface font-medium transition-all hover:opacity-80"
                >
                  {t("onboarding.back")}
                </button>
                <button
                  onClick={goNext}
                  disabled={!selectedSlug}
                  className="flex-1 h-12 rounded-2xl bg-primary text-on-primary font-semibold transition-all hover:opacity-90 disabled:opacity-40"
                >
                  {t("onboarding.step2Cta")}
                </button>
              </div>
              <button onClick={skip} className="w-full text-sm text-on-surface-variant hover:text-on-surface transition-colors">
                {t("onboarding.skip")}
              </button>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div
              key="step3"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="space-y-8 text-center"
            >
              <div className="text-7xl">🚀</div>
              <div className="space-y-3">
                <h2 className="text-2xl font-bold text-on-surface">{t("onboarding.step3Title")}</h2>
                <p className="text-on-surface-variant text-sm max-w-sm mx-auto">
                  {t("onboarding.step3Desc", {
                    competency: t(`competency.${selectedSlug ?? "communication"}`),
                  })}
                </p>
              </div>

              {/* What happens next */}
              <div className="space-y-3 text-left">
                {[
                  { step: "1", key: "onboarding.next1" },
                  { step: "2", key: "onboarding.next2" },
                  { step: "3", key: "onboarding.next3" },
                ].map(({ step: s, key }) => (
                  <div key={key} className="flex items-center gap-4 p-3 bg-surface-container-low rounded-xl">
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-bold text-primary">{s}</span>
                    </div>
                    <p className="text-sm text-on-surface">{t(key)}</p>
                  </div>
                ))}
              </div>

              <button
                onClick={startAssessment}
                className="w-full h-12 rounded-2xl bg-primary text-on-primary font-semibold text-base transition-all hover:opacity-90 active:scale-95"
              >
                {t("onboarding.step3Cta")}
              </button>
              <button onClick={skip} className="w-full text-sm text-on-surface-variant hover:text-on-surface transition-colors">
                {t("onboarding.skipToDashboard")}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
