"use client";

/**
 * EventShift — create event page. MVP.
 *
 * Single form, not multi-step (primitive-first per CEO directive 2026-04-17:
 * "это очень примитивно в сравнении с тем что мы построили").
 *
 * Constitution:
 * - Law 1 (no red): validation errors use text-error token (purple), not red literals.
 * - Law 2 (energy): low mode hides the optional description + timezone; keeps required fields.
 * - Law 3 (shame-free): error messages say "what's needed", not "what you did wrong".
 * - Law 5 (one CTA): single submit button.
 *
 * Character_events fires server-side on POST /eventshift/events (eventshift_event_created).
 */

import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Check } from "lucide-react";
import Link from "next/link";

import { TopBar } from "@/components/layout/top-bar";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import {
  useCreateEventShiftEvent,
  type EventShiftStatus,
} from "@/hooks/queries/use-eventshift";

const SLUG_REGEX = /^[a-z0-9][a-z0-9-]*$/;

const schema = z
  .object({
    slug: z
      .string()
      .min(1)
      .max(64)
      .regex(SLUG_REGEX, {
        message:
          "Use lowercase letters, numbers, and dashes. Must start with a letter or number.",
      }),
    name: z.string().min(2, "Name needs at least 2 characters").max(200),
    description: z.string().max(2000).optional(),
    start_at: z.string().min(1, "Pick a start date and time"),
    end_at: z.string().min(1, "Pick an end date and time"),
    timezone: z.string().default("Asia/Baku"),
    status: z.enum(["planning", "staffing", "live", "closed", "cancelled"]),
  })
  .refine((d) => new Date(d.end_at) > new Date(d.start_at), {
    message: "End must come after start",
    path: ["end_at"],
  });

type FormValues = z.infer<typeof schema>;

const inputClass =
  "w-full rounded-xl border border-outline-variant bg-surface-container px-3.5 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 transition-all";

const labelClass =
  "text-xs font-medium text-on-surface-variant uppercase tracking-wide";

const STATUSES: EventShiftStatus[] = ["planning", "staffing", "live"];

export default function EventShiftCreatePage() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useParams<{ locale: string }>();
  const locale = params?.locale ?? "en";
  const energy = useEnergyMode().energy;
  const createMut = useCreateEventShiftEvent();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema as never),
    defaultValues: {
      timezone: "Asia/Baku",
      status: "planning",
    },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      const created = await createMut.mutateAsync({
        slug: values.slug.trim().toLowerCase(),
        name: values.name.trim(),
        description: values.description?.trim() || undefined,
        start_at: new Date(values.start_at).toISOString(),
        end_at: new Date(values.end_at).toISOString(),
        timezone: values.timezone,
        status: values.status,
      });
      router.push(`/${locale}/eventshift/${created.id}`);
    } catch {
      // Error surfaced below via createMut.error — don't re-throw, stay on page.
    }
  };

  const serverError = createMut.error;
  const isSlugConflict =
    serverError?.status === 409 &&
    serverError?.code === "DUPLICATE_SLUG";

  return (
    <div className="flex min-h-screen flex-col">
      <TopBar
        title={t("eventshift.create.title", { defaultValue: "New event" })}
      />

      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6 sm:px-6 md:py-10">
        <Link
          href={`/${locale}/eventshift`}
          className="mb-6 inline-flex items-center gap-1.5 text-sm text-on-surface-variant transition-colors hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 rounded-md"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {t("eventshift.create.back", { defaultValue: "Back to events" })}
        </Link>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Name */}
          <Field
            label={t("eventshift.create.field.name", { defaultValue: "Name" })}
            error={errors.name?.message}
          >
            <input
              type="text"
              placeholder={t("eventshift.create.field.name_ph", {
                defaultValue: "Championship 2026",
              })}
              className={inputClass}
              {...register("name")}
              aria-invalid={!!errors.name}
            />
          </Field>

          {/* Slug */}
          <Field
            label={t("eventshift.create.field.slug", {
              defaultValue: "Slug (URL identifier)",
            })}
            error={errors.slug?.message ?? (isSlugConflict
              ? t("eventshift.create.err.slug_taken", {
                  defaultValue: "This slug is already in use. Try another.",
                })
              : undefined)}
            hint={t("eventshift.create.field.slug_hint", {
              defaultValue: "lowercase, digits, dashes — e.g. championship-2026",
            })}
          >
            <input
              type="text"
              placeholder="championship-2026"
              className={inputClass}
              autoComplete="off"
              {...register("slug")}
              aria-invalid={!!errors.slug || isSlugConflict}
            />
          </Field>

          {/* Dates — side-by-side except low energy */}
          <div className={energy === "low" ? "space-y-5" : "grid gap-5 sm:grid-cols-2"}>
            <Field
              label={t("eventshift.create.field.start", { defaultValue: "Start" })}
              error={errors.start_at?.message}
            >
              <input
                type="datetime-local"
                className={inputClass}
                {...register("start_at")}
                aria-invalid={!!errors.start_at}
              />
            </Field>

            <Field
              label={t("eventshift.create.field.end", { defaultValue: "End" })}
              error={errors.end_at?.message}
            >
              <input
                type="datetime-local"
                className={inputClass}
                {...register("end_at")}
                aria-invalid={!!errors.end_at}
              />
            </Field>
          </div>

          {/* Status */}
          <Field
            label={t("eventshift.create.field.status", { defaultValue: "Status" })}
            error={errors.status?.message}
          >
            <div className="flex flex-wrap gap-2">
              {STATUSES.map((s) => (
                <StatusRadio key={s} value={s} register={register} />
              ))}
            </div>
          </Field>

          {/* Description + timezone — hidden under low energy */}
          {energy !== "low" && (
            <>
              <Field
                label={t("eventshift.create.field.description", {
                  defaultValue: "Description (optional)",
                })}
                error={errors.description?.message}
              >
                <textarea
                  rows={3}
                  placeholder={t("eventshift.create.field.description_ph", {
                    defaultValue: "What is this event? Who is it for?",
                  })}
                  className={inputClass}
                  {...register("description")}
                />
              </Field>

              <Field
                label={t("eventshift.create.field.timezone", {
                  defaultValue: "Timezone",
                })}
                error={errors.timezone?.message}
              >
                <input
                  type="text"
                  className={inputClass}
                  placeholder="Asia/Baku"
                  {...register("timezone")}
                />
              </Field>
            </>
          )}

          {/* Generic server error (anything other than slug conflict) */}
          {serverError && !isSlugConflict && (
            <div className="rounded-xl border border-outline-variant bg-surface-container p-3 text-sm text-on-surface-variant">
              {t("eventshift.create.err.generic", {
                defaultValue:
                  "We couldn't save this event. Check your fields and try again.",
              })}
            </div>
          )}

          {/* Submit — one primary CTA */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting || createMut.isPending}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-on-primary shadow-sm transition-all hover:opacity-90 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 sm:w-auto"
            >
              <Check className="h-4 w-4" aria-hidden="true" />
              {isSubmitting || createMut.isPending
                ? t("eventshift.create.submitting", {
                    defaultValue: "Creating…",
                  })
                : t("eventshift.create.submit", {
                    defaultValue: "Create event",
                  })}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

// ── Form helpers ────────────────────────────────────────────────────────────

function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1.5">
      <span className={labelClass}>{label}</span>
      {children}
      {hint && !error && (
        <span className="block text-xs text-on-surface-variant/80">{hint}</span>
      )}
      {error && (
        <span
          className="block text-xs font-medium text-error"
          role="alert"
          aria-live="polite"
        >
          {error}
        </span>
      )}
    </label>
  );
}

function StatusRadio({
  value,
  register,
}: {
  value: EventShiftStatus;
  register: ReturnType<typeof useForm<FormValues>>["register"];
}) {
  const { t } = useTranslation();
  return (
    <label className="cursor-pointer">
      <input
        type="radio"
        value={value}
        className="peer sr-only"
        {...register("status")}
      />
      <span className="inline-flex items-center rounded-full border border-outline-variant bg-surface-container px-3 py-1.5 text-xs font-medium text-on-surface-variant transition-all peer-checked:border-primary peer-checked:bg-primary/10 peer-checked:text-primary peer-focus-visible:ring-2 peer-focus-visible:ring-primary/40">
        {t(`eventshift.status.${value}`, {
          defaultValue: value.charAt(0).toUpperCase() + value.slice(1),
        })}
      </span>
    </label>
  );
}
