"use client";

import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import { Calendar, MapPin, Users, Globe, ChevronRight, ChevronLeft, Check, Loader2 } from "lucide-react";
import { useCreateEvent } from "@/hooks/queries/use-events";
import type { EventCreate } from "@/lib/api/types";
import { cn } from "@/lib/utils/cn";

// ── Zod Schemas ────────────────────────────────────────────────────────────────

const step1Schema = z.object({
  title_en: z.string().min(3, "Title must be at least 3 characters").max(200),
  title_az: z.string().min(3, "Başlıq ən az 3 simvol olmalıdır").max(200),
  description_en: z.string().max(2000).optional(),
  description_az: z.string().max(2000).optional(),
  event_type: z.string().optional(),
  location: z.string().max(500).optional(),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string().min(1, "End date is required"),
}).refine((d) => new Date(d.end_date) > new Date(d.start_date), {
  message: "End date must be after start date",
  path: ["end_date"],
});

const step2Schema = z.object({
  capacity: z.coerce.number().int().min(1).max(10000).optional(),
  required_min_aura: z.coerce.number().min(0).max(100).optional(),
  is_public: z.boolean(),
});

type Step1Data = z.infer<typeof step1Schema>;
type Step2Data = z.infer<typeof step2Schema>;

// ── Slide animation ────────────────────────────────────────────────────────────

const slide = (dir: 1 | -1) => ({
  hidden: { opacity: 0, x: dir * 40 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.25, ease: "easeOut" as const } },
  exit: { opacity: 0, x: dir * -40, transition: { duration: 0.2, ease: "easeIn" as const } },
});

// ── Step indicator ─────────────────────────────────────────────────────────────

function StepDot({ n, current }: { n: number; current: number }) {
  const done = n < current;
  const active = n === current;
  return (
    <span
      className={cn(
        "size-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all",
        done && "bg-primary text-on-primary",
        active && "bg-primary/20 text-primary ring-2 ring-primary",
        !done && !active && "bg-surface-container text-on-surface-variant",
      )}
    >
      {done ? <Check className="size-3.5" /> : n}
    </span>
  );
}

// ── Field wrapper ──────────────────────────────────────────────────────────────

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-on-surface-variant uppercase tracking-wide">{label}</label>
      {children}
      {error && <p className="text-xs text-error">{error}</p>}
    </div>
  );
}

const inputClass =
  "w-full rounded-xl border border-outline-variant bg-surface-container px-3.5 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all";

// ── Page ───────────────────────────────────────────────────────────────────────

export default function CreateEventPage() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const createEvent = useCreateEvent();
  const isMounted = useRef(true);
  useEffect(() => () => { isMounted.current = false; }, []);

  const [step, setStep] = useState(1);
  const [dir, setDir] = useState<1 | -1>(1);

  // Persisted across steps
  const [step1Data, setStep1Data] = useState<Step1Data | null>(null);
  const [step2Data, setStep2Data] = useState<Step2Data | null>(null);

  // ── Step 1 form ────────────────────────────────────────────────────────────
  const form1 = useForm<Step1Data>({ resolver: zodResolver(step1Schema), defaultValues: step1Data ?? undefined });
  const form2 = useForm<Step2Data>({
    resolver: zodResolver(step2Schema),
    defaultValues: step2Data ?? { is_public: true, required_min_aura: 0 },
  });

  function goNext1(data: Step1Data) {
    setStep1Data(data);
    setDir(1);
    setStep(2);
  }

  function goNext2(data: Step2Data) {
    setStep2Data(data);
    setDir(1);
    setStep(3);
  }

  function goBack() {
    setDir(-1);
    setStep((s) => s - 1);
  }

  async function handlePublish() {
    if (!step1Data || !step2Data) return;

    const payload: EventCreate = {
      title_en: step1Data.title_en,
      title_az: step1Data.title_az,
      description_en: step1Data.description_en,
      description_az: step1Data.description_az,
      event_type: step1Data.event_type,
      location: step1Data.location,
      start_date: new Date(step1Data.start_date).toISOString(),
      end_date: new Date(step1Data.end_date).toISOString(),
      capacity: step2Data.capacity,
      required_min_aura: step2Data.required_min_aura ?? 0,
      is_public: step2Data.is_public,
      status: "open",
    };

    const result = await createEvent.mutateAsync(payload);
    if (isMounted.current && result?.id) {
      router.push(`/${locale}/events/${result.id}?created=1`);
    }
  }

  const EVENT_TYPES = ["conference", "workshop", "hackathon", "community", "sports", "cultural", "other"];

  return (
    <div className="min-h-screen bg-background px-4 py-8 sm:px-6">
      {/* Header */}
      <div className="mx-auto max-w-xl">
        <h1 className="font-headline text-2xl font-bold text-on-surface">{t("events.createTitle")}</h1>
        <p className="mt-1 text-sm text-on-surface-variant">{t("events.createSubtitle")}</p>

        {/* Step bar */}
        <div className="mt-6 flex items-center gap-2">
          {[1, 2, 3].map((n) => (
            <div key={n} className="flex items-center gap-2">
              <StepDot n={n} current={step} />
              {n < 3 && <span className={cn("h-px flex-1 w-8 transition-colors", step > n ? "bg-primary" : "bg-outline-variant")} />}
            </div>
          ))}
          <span className="ml-2 text-xs text-on-surface-variant">{t("events.stepOf", { step, total: 3 })}</span>
        </div>
      </div>

      {/* Forms */}
      <div className="mx-auto mt-8 max-w-xl overflow-hidden">
        <AnimatePresence mode="wait" initial={false}>
          {/* Step 1 — Details */}
          {step === 1 && (
            <motion.div key="step1" variants={slide(dir)} initial="hidden" animate="visible" exit="exit">
              <form onSubmit={form1.handleSubmit(goNext1)} className="space-y-5 rounded-2xl border border-border bg-surface-container-low p-6">
                <h2 className="font-semibold text-on-surface">{t("events.stepDetailsTitle")}</h2>

                <Field label={t("events.titleEn")} error={form1.formState.errors.title_en?.message}>
                  <input {...form1.register("title_en")} className={inputClass} placeholder="Summer Tech Volunteer Summit" />
                </Field>

                <Field label={t("events.titleAz")} error={form1.formState.errors.title_az?.message}>
                  <input {...form1.register("title_az")} className={inputClass} placeholder="Yay Texnologiya Könüllü Sammiti" />
                </Field>

                <div className="grid grid-cols-2 gap-4">
                  <Field label={t("events.startDate")} error={form1.formState.errors.start_date?.message}>
                    <input type="datetime-local" {...form1.register("start_date")} className={inputClass} />
                  </Field>
                  <Field label={t("events.endDate")} error={form1.formState.errors.end_date?.message}>
                    <input type="datetime-local" {...form1.register("end_date")} className={inputClass} />
                  </Field>
                </div>

                <Field label={t("events.location")} error={form1.formState.errors.location?.message}>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-on-surface-variant" aria-hidden="true" />
                    <input {...form1.register("location")} className={cn(inputClass, "pl-9")} placeholder="Baku, Azerbaijan" />
                  </div>
                </Field>

                <Field label={t("events.eventType")}>
                  <select {...form1.register("event_type")} className={inputClass}>
                    <option value="">{t("events.selectType")}</option>
                    {EVENT_TYPES.map((et) => (
                      <option key={et} value={et}>{t(`events.type.${et}`, { defaultValue: et })}</option>
                    ))}
                  </select>
                </Field>

                <Field label={t("events.descriptionEn")}>
                  <textarea {...form1.register("description_en")} rows={3} className={cn(inputClass, "resize-none")} placeholder="Describe the event goals and volunteer tasks..." />
                </Field>

                <Field label={t("events.descriptionAz")}>
                  <textarea {...form1.register("description_az")} rows={3} className={cn(inputClass, "resize-none")} placeholder="Tədbirın məqsədini və könüllü vəzifələrini izah edin..." />
                </Field>

                <div className="flex justify-end pt-2">
                  <button type="submit" className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-on-primary transition-opacity hover:opacity-90">
                    {t("common.next")} <ChevronRight className="size-4" aria-hidden="true" />
                  </button>
                </div>
              </form>
            </motion.div>
          )}

          {/* Step 2 — Recruitment */}
          {step === 2 && (
            <motion.div key="step2" variants={slide(dir)} initial="hidden" animate="visible" exit="exit">
              <form onSubmit={form2.handleSubmit(goNext2)} className="space-y-5 rounded-2xl border border-border bg-surface-container-low p-6">
                <h2 className="font-semibold text-on-surface">{t("events.stepRecruitTitle")}</h2>

                <Field label={t("events.capacity")} error={form2.formState.errors.capacity?.message}>
                  <div className="relative">
                    <Users className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-on-surface-variant" aria-hidden="true" />
                    <input type="number" min={1} max={10000} {...form2.register("capacity")} className={cn(inputClass, "pl-9")} placeholder="50" />
                  </div>
                </Field>

                <Field label={t("events.minAura")} error={form2.formState.errors.required_min_aura?.message}>
                  <input type="number" min={0} max={100} step={5} {...form2.register("required_min_aura")} className={inputClass} placeholder="0" />
                  <p className="text-xs text-on-surface-variant">{t("events.minAuraHint")}</p>
                </Field>

                <Field label={t("events.visibility")}>
                  <label className="flex items-center gap-3 rounded-xl border border-outline-variant bg-surface-container p-3 cursor-pointer">
                    <input type="checkbox" {...form2.register("is_public")} className="accent-primary size-4" />
                    <div>
                      <p className="text-sm font-medium text-on-surface">{t("events.makePublic")}</p>
                      <p className="text-xs text-on-surface-variant">{t("events.makePublicHint")}</p>
                    </div>
                    <Globe className="ml-auto size-4 text-on-surface-variant" aria-hidden="true" />
                  </label>
                </Field>

                <div className="flex justify-between pt-2">
                  <button type="button" onClick={goBack} className="flex items-center gap-2 rounded-xl border border-outline-variant px-4 py-2.5 text-sm font-medium text-on-surface-variant transition-colors hover:bg-surface-container">
                    <ChevronLeft className="size-4" aria-hidden="true" /> {t("common.back")}
                  </button>
                  <button type="submit" className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-on-primary transition-opacity hover:opacity-90">
                    {t("common.next")} <ChevronRight className="size-4" aria-hidden="true" />
                  </button>
                </div>
              </form>
            </motion.div>
          )}

          {/* Step 3 — Review & Publish */}
          {step === 3 && step1Data && step2Data && (
            <motion.div key="step3" variants={slide(dir)} initial="hidden" animate="visible" exit="exit">
              <div className="space-y-5 rounded-2xl border border-border bg-surface-container-low p-6">
                <h2 className="font-semibold text-on-surface">{t("events.stepReviewTitle")}</h2>

                {/* Summary */}
                <div className="space-y-3 rounded-xl border border-outline-variant bg-surface-container p-4">
                  <ReviewRow icon={<Calendar className="size-4" />} label={t("events.titleEn")} value={step1Data.title_en} />
                  <ReviewRow icon={<Calendar className="size-4" />} label={t("events.titleAz")} value={step1Data.title_az} />
                  {step1Data.location && (
                    <ReviewRow icon={<MapPin className="size-4" />} label={t("events.location")} value={step1Data.location} />
                  )}
                  <ReviewRow
                    icon={<Calendar className="size-4" />}
                    label={t("events.startDate")}
                    value={new Date(step1Data.start_date).toLocaleString()}
                  />
                  <ReviewRow
                    icon={<Calendar className="size-4" />}
                    label={t("events.endDate")}
                    value={new Date(step1Data.end_date).toLocaleString()}
                  />
                  {step2Data.capacity && (
                    <ReviewRow icon={<Users className="size-4" />} label={t("events.capacity")} value={String(step2Data.capacity)} />
                  )}
                  <ReviewRow
                    icon={<Globe className="size-4" />}
                    label={t("events.visibility")}
                    value={step2Data.is_public ? t("events.public") : t("events.private")}
                  />
                  {(step2Data.required_min_aura ?? 0) > 0 && (
                    <ReviewRow icon={<span className="text-xs">⊛</span>} label={t("events.minAura")} value={String(step2Data.required_min_aura)} />
                  )}
                </div>

                {createEvent.isError && (
                  <p role="alert" className="text-sm text-error text-center">{t("error.generic")}</p>
                )}

                <div className="flex justify-between pt-2">
                  <button type="button" onClick={goBack} className="flex items-center gap-2 rounded-xl border border-outline-variant px-4 py-2.5 text-sm font-medium text-on-surface-variant transition-colors hover:bg-surface-container">
                    <ChevronLeft className="size-4" aria-hidden="true" /> {t("common.back")}
                  </button>
                  <button
                    onClick={handlePublish}
                    disabled={createEvent.isPending}
                    className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:opacity-60"
                  >
                    {createEvent.isPending ? (
                      <><Loader2 className="size-4 animate-spin" aria-hidden="true" /> {t("events.publishing")}</>
                    ) : (
                      <><Check className="size-4" aria-hidden="true" /> {t("events.publishNow")}</>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function ReviewRow({ icon, label, value }: { icon: React.ReactNode; value: string; label: string }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="shrink-0 text-on-surface-variant">{icon}</span>
      <span className="text-xs text-on-surface-variant w-24 shrink-0">{label}</span>
      <span className="text-sm font-medium text-on-surface truncate">{value}</span>
    </div>
  );
}
