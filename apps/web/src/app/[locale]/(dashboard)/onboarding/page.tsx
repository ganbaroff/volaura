"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { createClient } from "@/lib/supabase/client";

// ── Types ──────────────────────────────────────────────────────────────────────

type Step = 1 | 2 | 3;
type AccountType = "volunteer" | "organization";

interface FormData {
  display_name: string;
  username: string;
  location: string;
  languages: string[];
  selectedCompetency: string;
  visible_to_orgs: boolean;
}

interface CompetencyInfo {
  slug: string;
  icon: string;
}

const COMPETENCIES: CompetencyInfo[] = [
  { slug: "communication",       icon: "💬" },
  { slug: "reliability",         icon: "⏰" },
  { slug: "english_proficiency", icon: "🌍" },
  { slug: "leadership",          icon: "🧭" },
  { slug: "event_performance",   icon: "🏆" },
  { slug: "tech_literacy",       icon: "💻" },
  { slug: "adaptability",        icon: "🔄" },
  { slug: "empathy_safeguarding", icon: "🤝" },
];

// Language option keys are stable English identifiers stored in DB.
// Labels are i18n keys so they render in the user's current locale.
const LANGUAGE_OPTIONS = [
  { key: "Azerbaijani", labelKey: "onboarding.languageAzerbaijani" },
  { key: "English",     labelKey: "onboarding.languageEnglish" },
  { key: "Russian",     labelKey: "onboarding.languageRussian" },
  { key: "Turkish",     labelKey: "onboarding.languageTurkish" },
  { key: "Arabic",      labelKey: "onboarding.languageArabic" },
] as const;

// ── Slide variants ─────────────────────────────────────────────────────────────

const slideVariants = {
  enter: { opacity: 0, x: 40 },
  center: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -40 },
};

// ── Progress bar ───────────────────────────────────────────────────────────────

function ProgressBar({ step, totalSteps }: { step: Step; totalSteps: number }) {
  const pct = Math.round((step / totalSteps) * 100);
  return (
    <div className="w-full h-1.5 bg-surface-container-high rounded-full overflow-hidden mb-8">
      <motion.div
        className="h-full bg-primary rounded-full"
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      />
    </div>
  );
}

// ── Step label ─────────────────────────────────────────────────────────────────

function StepLabel({ step, total, t }: { step: Step; total: number; t: (k: string, opts?: Record<string, string | number>) => string }) {
  return (
    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-2 text-center">
      {t("onboarding.step")} {step} / {total}
    </p>
  );
}

// ── Input ──────────────────────────────────────────────────────────────────────

function Input({
  label,
  value,
  onChange,
  placeholder,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-foreground">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full h-11 px-3 rounded-xl border border-border bg-card text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
      />
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const [step, setStep] = useState<Step>(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accountType, setAccountType] = useState<AccountType>("volunteer");

  const [formData, setFormData] = useState<FormData>({
    display_name: "",
    username: "",
    location: "",
    languages: [],
    selectedCompetency: "",
    visible_to_orgs: false,
  });

  // Pre-fill username and account_type from signup user_metadata
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!isMounted.current) return;
      const meta = session?.user?.user_metadata;
      if (meta) {
        if (meta.username) {
          setFormData((prev) => ({ ...prev, username: meta.username as string }));
        }
        if (meta.account_type === "organization" || meta.account_type === "volunteer") {
          setAccountType(meta.account_type as AccountType);
        }
      }
    });
  }, []);

  function setField<K extends keyof FormData>(key: K, value: FormData[K]) {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }

  function toggleLanguage(lang: string) {
    setFormData((prev) => ({
      ...prev,
      languages: prev.languages.includes(lang)
        ? prev.languages.filter((l) => l !== lang)
        : [...prev.languages, lang],
    }));
  }

  // Orgs have 2 steps (no competency selection); volunteers have 3
  const totalSteps = accountType === "organization" ? 2 : 3;

  function goNext() {
    if (step === 2 && accountType === "organization") {
      // Orgs skip competency selection — save and route directly
      handleFinish();
    } else if (step < 3) {
      setStep((s) => (s + 1) as Step);
    }
  }

  function goBack() {
    if (step > 1) setStep((s) => (s - 1) as Step);
  }

  async function handleFinish() {
    setSaving(true);
    setError(null);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      const payload: Record<string, unknown> = {
        account_type: accountType,
      };
      if (formData.display_name.trim()) payload.display_name = formData.display_name.trim();
      if (formData.username.trim()) payload.username = formData.username.trim();
      if (formData.location.trim()) payload.location = formData.location.trim();
      if (formData.languages.length > 0) payload.languages = formData.languages;
      if (accountType === "volunteer") {
        payload.visible_to_orgs = formData.visible_to_orgs;
      }
      if (accountType === "organization") {
        // org_type was captured in user_metadata at signup — read it here and persist to profile
        const orgType = session?.user?.user_metadata?.org_type;
        if (orgType) payload.org_type = orgType;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/profiles/me`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok && res.status !== 404) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail ?? "Failed to save profile");
      }

      if (isMounted.current) {
        const dest = formData.selectedCompetency
          ? `/${locale}/welcome?competency=${formData.selectedCompetency}`
          : `/${locale}/welcome`;
        router.push(dest);
      }
    } catch {
      if (isMounted.current) {
        setError(t("error.generic", { defaultValue: "Something went wrong. Please try again." }));
        setSaving(false);
      }
    }
  }

  const step1Valid = formData.username.trim().length >= 3;
  const step3Valid = formData.selectedCompetency.length > 0;

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {/* Ambient glows */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] ambient-glow-primary pointer-events-none z-0" />
      <div className="fixed bottom-[-5%] right-[-5%] w-[30%] h-[30%] ambient-glow-secondary pointer-events-none z-0" />

      <div className="relative z-10 w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-foreground">{t("onboarding.title")}</h1>
        </div>

        {/* Progress bar */}
        <ProgressBar step={step} totalSteps={totalSteps} />

        {/* Step content */}
        <AnimatePresence mode="wait">

          {/* ── Step 1: Identity ── */}
          {step === 1 && (
            <motion.div
              key="step1"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <StepLabel step={1} total={totalSteps} t={t} />
              <h2 className="text-xl font-bold text-foreground text-center">
                {t("onboarding.step1.title")}
              </h2>

              <div className="rounded-xl border border-border bg-card p-5 space-y-4">
                <Input
                  label={t("onboarding.displayName")}
                  value={formData.display_name}
                  onChange={(v) => setField("display_name", v)}
                  placeholder="Leyla Həsənova"
                />
                <Input
                  label={t("onboarding.username")}
                  value={formData.username}
                  onChange={(v) => setField("username", v.toLowerCase().replace(/\s+/g, "_"))}
                  placeholder="leyla_hasanova"
                />
              </div>

              <button
                onClick={goNext}
                disabled={!step1Valid}
                className="w-full h-12 rounded-2xl bg-primary text-primary-foreground font-semibold text-base transition-all hover:opacity-90 active:scale-95 disabled:opacity-40"
              >
                {t("onboarding.next")}
              </button>
            </motion.div>
          )}

          {/* ── Step 2: Location, Languages, Visibility ── */}
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
              <StepLabel step={2} total={totalSteps} t={t} />
              <h2 className="text-xl font-bold text-foreground text-center">
                {t("onboarding.step2.title")}
              </h2>

              <div className="rounded-xl border border-border bg-card p-5 space-y-4">
                <Input
                  label={t("onboarding.location")}
                  value={formData.location}
                  onChange={(v) => setField("location", v)}
                  placeholder="Baku, Azerbaijan"
                />

                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    {t("onboarding.languages")}
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {LANGUAGE_OPTIONS.map(({ key, labelKey }) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => toggleLanguage(key)}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all border ${
                          formData.languages.includes(key)
                            ? "bg-primary text-primary-foreground border-primary"
                            : "bg-card text-foreground border-border hover:bg-accent"
                        }`}
                      >
                        {t(labelKey)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Org-search visibility — volunteers only */}
                {accountType === "volunteer" && (
                  <label className="flex items-start gap-3 cursor-pointer pt-1">
                    <input
                      type="checkbox"
                      checked={formData.visible_to_orgs}
                      onChange={(e) => setField("visible_to_orgs", e.target.checked)}
                      className="mt-0.5 h-4 w-4 rounded border-border accent-primary flex-shrink-0"
                    />
                    <span className="text-sm text-muted-foreground">
                      {t("onboarding.visibleToOrgs")}
                    </span>
                  </label>
                )}
              </div>

              {error && (
                <p className="text-sm text-destructive text-center">{error}</p>
              )}

              <div className="flex gap-3">
                <button
                  onClick={goBack}
                  disabled={saving}
                  className="h-12 px-6 rounded-2xl bg-card border border-border text-foreground font-medium transition-all hover:bg-accent disabled:opacity-50"
                >
                  {t("onboarding.back")}
                </button>
                <button
                  onClick={goNext}
                  disabled={saving}
                  className="flex-1 h-12 rounded-2xl bg-primary text-primary-foreground font-semibold transition-all hover:opacity-90 active:scale-95 disabled:opacity-40"
                >
                  {saving
                    ? t("onboarding.saving")
                    : accountType === "organization"
                      ? t("onboarding.finish")
                      : t("onboarding.next")}
                </button>
              </div>
            </motion.div>
          )}

          {/* ── Step 3: First Competency (volunteers only) ── */}
          {step === 3 && (
            <motion.div
              key="step3"
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <StepLabel step={3} total={totalSteps} t={t} />
              <div className="text-center space-y-1">
                <h2 className="text-xl font-bold text-foreground">
                  {t("onboarding.step3.title")}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {t("onboarding.step3.subtitle")}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {COMPETENCIES.map(({ slug, icon }) => (
                  <button
                    key={slug}
                    type="button"
                    onClick={() => setField("selectedCompetency", slug === formData.selectedCompetency ? "" : slug)}
                    className={`p-4 rounded-2xl text-left transition-all border-2 ${
                      formData.selectedCompetency === slug
                        ? "border-primary bg-primary/10"
                        : "border-transparent bg-card hover:bg-accent"
                    }`}
                  >
                    <div className="text-2xl mb-2">{icon}</div>
                    <p className="text-sm font-semibold text-foreground">{t(`competency.${slug}`)}</p>
                  </button>
                ))}
              </div>

              {error && (
                <p className="text-sm text-destructive text-center">{error}</p>
              )}

              <div className="flex gap-3">
                <button
                  onClick={goBack}
                  disabled={saving}
                  className="h-12 px-6 rounded-2xl bg-card border border-border text-foreground font-medium transition-all hover:bg-accent disabled:opacity-50"
                >
                  {t("onboarding.back")}
                </button>
                <button
                  onClick={handleFinish}
                  disabled={!step3Valid || saving}
                  className="flex-1 h-12 rounded-2xl bg-primary text-primary-foreground font-semibold transition-all hover:opacity-90 active:scale-95 disabled:opacity-40"
                >
                  {saving ? t("onboarding.saving") : t("onboarding.finish")}
                </button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  );
}
