"use client";

/**
 * EventShift — list page. MVP.
 *
 * Constitution:
 * - Law 1 (no red): status pills use teal/indigo/gold/amber, cancelled = muted gray.
 * - Law 2 (energy): grid density shrinks under "mid", single-card mode under "low".
 * - Law 3 (shame-free): empty state is an invitation, not a verdict.
 * - Law 4 (motion): gated via useReducedMotion; skeleton, not spinner.
 * - Law 5 (one CTA): single "Create event" primary per screen.
 *
 * Activation gate: queries /eventshift/debug/activation-state.
 * - active=true                   → normal list
 * - 404 NO_ORGANIZATION           → "Create an organization first" empty state
 * - 403 MODULE_NOT_ACTIVATED      → "Activate EventShift" empty state
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Calendar, Plus, Layers, Clock } from "lucide-react";

import { TopBar } from "@/components/layout/top-bar";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import { useMotionPreference } from "@/hooks/use-reduced-motion";
import {
  useEventShiftActivation,
  useEventShiftEvents,
  type EventShiftEvent,
  type EventShiftStatus,
} from "@/hooks/queries/use-eventshift";

// Status pill palette — all tokenized, no literal red/hex for semantics.
// cancelled uses muted foreground so it reads as "archived", not "failed".
const STATUS_STYLE: Record<EventShiftStatus, string> = {
  planning: "bg-primary/10 text-primary border-primary/30",
  staffing: "bg-secondary-container text-on-secondary-container border-outline-variant",
  live: "bg-success/10 text-success border-success/40",
  closed: "bg-surface-container-high text-on-surface-variant border-outline-variant",
  cancelled: "bg-surface-container-high text-on-surface-variant/70 border-outline-variant",
};

export default function EventShiftListPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useParams<{ locale: string }>();
  const locale = params?.locale ?? "en";
  const energy = useEnergyMode().energy;
  const { shouldReduceMotion } = useMotionPreference();

  const activation = useEventShiftActivation();
  const events = useEventShiftEvents();

  const isLoading = activation.isLoading || events.isLoading;

  // ── Error branches: org missing or module not activated ─────────────────────
  const activationError = activation.error;
  const eventsError = events.error;

  const needsOrg =
    activationError?.status === 404 && activationError?.code === "NO_ORGANIZATION";
  const needsActivation =
    activationError?.status === 403 && activationError?.code === "MODULE_NOT_ACTIVATED";

  const headerAction = (
    <Link
      href={`/${locale}/eventshift/create`}
      className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-on-primary shadow-sm transition-all hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
      aria-label={t("eventshift.create_cta", { defaultValue: "Create event" })}
    >
      <Plus className="h-4 w-4" aria-hidden="true" />
      {t("eventshift.create_cta", { defaultValue: "Create event" })}
    </Link>
  );

  return (
    <div className="flex min-h-screen flex-col">
      <TopBar
        title={t("eventshift.title", { defaultValue: "EventShift" })}
      />

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 sm:px-6 md:py-10">
        {/* Loading — skeleton cards, no spinner (design gate STEP 6) */}
        {isLoading && (
          <div className="grid gap-3 md:grid-cols-2">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-[140px] w-full rounded-2xl" />
            ))}
          </div>
        )}

        {/* Activation error: no organization */}
        {!isLoading && needsOrg && (
          <EmptyState
            icon={<Layers className="mx-auto h-12 w-12 text-on-surface-variant" aria-hidden="true" />}
            title={t("eventshift.empty.no_org.title", {
              defaultValue: "First, set up your organization",
            })}
            description={t("eventshift.empty.no_org.desc", {
              defaultValue:
                "EventShift belongs to an organization. Create one and you'll unlock events, departments, areas, and unit staffing.",
            })}
            ctaLabel={t("eventshift.empty.no_org.cta", {
              defaultValue: "Create organization",
            })}
            onCtaClick={() => router.push(`/${locale}/my-organization`)}
          />
        )}

        {/* Activation error: module not activated for org */}
        {!isLoading && needsActivation && (
          <EmptyState
            icon={<Calendar className="mx-auto h-12 w-12 text-primary" aria-hidden="true" />}
            title={t("eventshift.empty.not_active.title", {
              defaultValue: "Activate EventShift for your organization",
            })}
            description={t("eventshift.empty.not_active.desc", {
              defaultValue:
                "EventShift is one of several modules you can turn on. Activate it from Settings to start staffing your first event.",
            })}
            ctaLabel={t("eventshift.empty.not_active.cta", {
              defaultValue: "Open module settings",
            })}
            onCtaClick={() => router.push(`/${locale}/settings`)}
          />
        )}

        {/* Other activation/events errors — neutral, not red, not shaming */}
        {!isLoading && activationError && !needsOrg && !needsActivation && (
          <div className="rounded-2xl border border-outline-variant bg-surface-container p-6 text-sm text-on-surface-variant">
            {t("eventshift.error.generic", {
              defaultValue:
                "We couldn't load EventShift right now. Please try again in a moment.",
            })}
          </div>
        )}

        {/* Happy path */}
        {!isLoading && !activationError && (
          <>
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-on-surface font-headline">
                  {t("eventshift.list.heading", { defaultValue: "Your events" })}
                </h1>
                <p className="mt-1 text-sm text-on-surface-variant">
                  {t("eventshift.list.sub", {
                    defaultValue:
                      "Each event holds departments, areas, and shift units. Reliability proofs live here.",
                  })}
                </p>
              </div>
              {energy !== "low" && headerAction}
            </div>

            {/* Empty list — one primary CTA, shame-free copy */}
            {events.data && events.data.length === 0 && !eventsError && (
              <EmptyState
                icon={<Calendar className="mx-auto h-12 w-12 text-primary" aria-hidden="true" />}
                title={t("eventshift.list.empty.title", {
                  defaultValue: "Your first event starts here",
                })}
                description={t("eventshift.list.empty.desc", {
                  defaultValue:
                    "Give it a name, pick a start and end, and the structure grows from there.",
                })}
                ctaLabel={t("eventshift.create_cta", { defaultValue: "Create event" })}
                onCtaClick={() => router.push(`/${locale}/eventshift/create`)}
              />
            )}

            {/* Event list */}
            {events.data && events.data.length > 0 && (
              <ul
                className={
                  energy === "low"
                    ? "space-y-3"
                    : "grid gap-3 md:grid-cols-2"
                }
                aria-label={t("eventshift.list.heading", {
                  defaultValue: "Your events",
                })}
              >
                {events.data.map((ev, idx) => (
                  <motion.li
                    key={ev.id}
                    initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
                    animate={shouldReduceMotion ? undefined : { opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: idx * 0.03 }}
                  >
                    <EventCard ev={ev} locale={locale} />
                  </motion.li>
                ))}
              </ul>
            )}

            {/* Low-energy fallback CTA below list (still one primary) */}
            {energy === "low" && events.data && events.data.length > 0 && (
              <div className="mt-8 flex justify-center">{headerAction}</div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

// ── Event card ───────────────────────────────────────────────────────────────

function EventCard({ ev, locale }: { ev: EventShiftEvent; locale: string }) {
  const { t } = useTranslation();
  const start = new Date(ev.start_at);
  const end = new Date(ev.end_at);

  return (
    <Link
      href={`/${locale}/eventshift/${ev.id}`}
      className="group block rounded-2xl border border-outline-variant bg-surface-container p-5 transition-all hover:border-primary/40 hover:bg-surface-container-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-base font-semibold text-on-surface font-headline">
            {ev.name}
          </h2>
          <p className="mt-0.5 truncate text-xs text-on-surface-variant">
            /{ev.slug}
          </p>
        </div>
        <StatusPill status={ev.status} />
      </div>

      {ev.description && (
        <p className="mt-3 line-clamp-2 text-sm text-on-surface-variant">
          {ev.description}
        </p>
      )}

      <div className="mt-4 flex items-center gap-4 text-xs text-on-surface-variant">
        <span className="inline-flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
          {start.toLocaleDateString(locale, {
            day: "numeric",
            month: "short",
            year: "numeric",
          })}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5" aria-hidden="true" />
          {formatDuration(start, end)}
        </span>
      </div>
    </Link>
  );
}

function StatusPill({ status }: { status: EventShiftStatus }) {
  const { t } = useTranslation();
  const label = t(`eventshift.status.${status}`, {
    defaultValue: status.charAt(0).toUpperCase() + status.slice(1),
  });
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-widest ${STATUS_STYLE[status]}`}
    >
      {label}
    </span>
  );
}

function formatDuration(start: Date, end: Date): string {
  const hrs = Math.max(1, Math.round((end.getTime() - start.getTime()) / 3_600_000));
  if (hrs < 24) return `${hrs} h`;
  return `${Math.round(hrs / 24)} d`;
}
