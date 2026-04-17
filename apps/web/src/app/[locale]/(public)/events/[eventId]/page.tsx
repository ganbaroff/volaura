"use client";

import { useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Users,
  AlertCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { LandingNav } from "@/components/landing/landing-nav";
import { LandingFooter } from "@/components/landing/landing-footer";
import { useEvent, useRegisterForEvent } from "@/hooks/queries/use-events";

function formatDate(iso: string | Date, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "az" ? "az-Latn-AZ" : "en-US", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getDisplayStatus(status: string): "live" | "upcoming" | "past" {
  if (status === "open") return "upcoming";
  if (status === "completed" || status === "closed" || status === "cancelled") return "past";
  return "upcoming";
}

export default function EventDetailPage() {
  const { locale, eventId } = useParams<{ locale: string; eventId: string }>();
  const { t } = useTranslation();
  const isMounted = useRef(true);
  const { data: event, isLoading, isError } = useEvent(eventId);
  const registerMutation = useRegisterForEvent();

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  if (isLoading) {
    return (
      <>
        <LandingNav locale={locale} />
        <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
          <Skeleton className="mb-6 h-5 w-32" />
          <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 space-y-5">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-8 w-3/4" />
            <div className="grid grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
            </div>
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-14 w-full rounded-xl" />
          </div>
        </main>
        <LandingFooter locale={locale} />
      </>
    );
  }

  if (isError || !event) {
    return (
      <>
        <LandingNav locale={locale} />
        <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-4 py-20 text-center">
          <AlertCircle className="mb-4 h-12 w-12 text-muted-foreground" aria-hidden="true" />
          <h1 className="mb-2 text-2xl font-bold text-foreground">{t("common.error")}</h1>
          <p className="mb-6 text-muted-foreground">{t("common.noResults")}</p>
          <Link
            href={`/${locale}/events`}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {t("events.backToEvents")}
          </Link>
        </main>
        <LandingFooter locale={locale} />
      </>
    );
  }

  const title = locale === "az" ? event.title_az : event.title_en;
  const description = locale === "az" ? event.description_az : event.description_en;
  const displayStatus = getDisplayStatus(event.status);
  const isPast = displayStatus === "past";
  const isOpen = event.status === "open";
  const registered = registerMutation.isSuccess;
  const registering = registerMutation.isPending;

  return (
    <>
      <LandingNav locale={locale} />
      <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <Link
          href={`/${locale}/events`}
          className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {t("events.backToEvents")}
        </Link>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
          {/* Status badge */}
          <div className="mb-4">
            <span
              className={cn(
                "inline-flex rounded-full px-3 py-1 text-xs font-semibold",
                displayStatus === "live"
                  ? "bg-purple-500/10 text-purple-400"
                  : displayStatus === "upcoming"
                    ? "bg-emerald-500/10 text-emerald-700"
                    : "bg-muted text-muted-foreground"
              )}
            >
              {displayStatus === "live"
                ? t("events.live")
                : displayStatus === "upcoming"
                  ? t("events.upcoming")
                  : t("events.past")}
            </span>
          </div>

          <h1 className="mb-6 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {title}
          </h1>

          {/* Meta grid */}
          <div className="mb-6 grid grid-cols-1 gap-4 rounded-xl bg-muted/50 p-5 sm:grid-cols-2">
            {event.location && (
              <div className="flex items-start gap-3">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                <div>
                  <p className="text-xs font-medium text-muted-foreground">{t("events.location")}</p>
                  <p className="text-sm font-semibold text-foreground">{event.location}</p>
                </div>
              </div>
            )}
            <div className="flex items-start gap-3">
              <Calendar className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <div>
                <p className="text-xs font-medium text-muted-foreground">{t("events.date")}</p>
                <p className="text-sm font-semibold text-foreground" suppressHydrationWarning>
                  {formatDate(event.start_date, locale)}
                </p>
              </div>
            </div>
            {event.capacity != null && (
              <div className="flex items-start gap-3">
                <Users className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                <div>
                  <p className="text-xs font-medium text-muted-foreground">{t("events.participants")}</p>
                  <p className="text-sm font-semibold text-foreground">
                    {t("events.capacity", { count: event.capacity, defaultValue: `${event.capacity} spots` })}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Description */}
          {description && (
            <div className="mb-8">
              <h2 className="mb-3 text-base font-semibold text-foreground">{t("events.about")}</h2>
              <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>
            </div>
          )}

          {/* Register CTA */}
          {isOpen && (
            <AnimatePresence mode="wait">
              {registered ? (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center gap-3 rounded-xl bg-emerald-500/10 p-5 text-emerald-700"
                  role="status"
                  aria-live="polite"
                >
                  <CheckCircle2 className="h-6 w-6 shrink-0" aria-hidden="true" />
                  <div>
                    <p className="font-semibold">{t("events.registerSuccess")}</p>
                    <p className="text-sm">{t("events.registerSuccessBody")}</p>
                  </div>
                </motion.div>
              ) : (
                <motion.button
                  key="register"
                  type="button"
                  onClick={() => registerMutation.mutate({ eventId: event.id })}
                  disabled={registering}
                  aria-busy={registering}
                  className={cn(
                    "w-full rounded-xl py-4 text-base font-semibold transition-all",
                    registering
                      ? "cursor-wait bg-primary/70 text-primary-foreground"
                      : "bg-primary text-primary-foreground hover:bg-primary/90 shadow-md hover:shadow-lg"
                  )}
                >
                  {registering ? (
                    <Loader2 className="mx-auto h-5 w-5 animate-spin" aria-hidden="true" />
                  ) : (
                    t("events.register")
                  )}
                </motion.button>
              )}
            </AnimatePresence>
          )}

          {isPast && (
            <div className="rounded-xl bg-muted/50 p-4 text-center text-sm text-muted-foreground">
              {t("events.eventEnded", { defaultValue: "This event has ended." })}
            </div>
          )}
        </div>
      </main>
      <LandingFooter locale={locale} />
    </>
  );
}
