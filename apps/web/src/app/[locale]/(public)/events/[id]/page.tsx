"use client";

import { use, useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Users,
  Building2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { getMockEventById } from "@/lib/mock-data";
import { cn } from "@/lib/utils/cn";
import { LandingNav } from "@/components/landing/landing-nav";
import { LandingFooter } from "@/components/landing/landing-footer";

interface EventDetailPageProps {
  params: Promise<{ locale: string; id: string }>;
}

function formatDate(iso: string, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "az" ? "az-Latn-AZ" : "en-US", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type RegisterState = "idle" | "loading" | "success" | "error";

export default function EventDetailPage({ params }: EventDetailPageProps) {
  const { locale, id } = use(params);
  const { t } = useTranslation();
  const [registerState, setRegisterState] = useState<RegisterState>("idle");
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const event = getMockEventById(id);

  if (!event) {
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

  const title = locale === "az" ? event.titleAz : event.title;
  const description = locale === "az" ? event.descriptionAz : event.description;
  const location = locale === "az" ? event.locationAz : event.location;
  const isFull = event.currentVolunteers >= event.maxVolunteers;
  const spotsLeft = event.maxVolunteers - event.currentVolunteers;
  const isPast = event.status === "past";

  async function handleRegister() {
    // Session 11: replace with real POST /api/events/{id}/register + auth guard
    setRegisterState("loading");
    await new Promise((r) => setTimeout(r, 900));
    if (!isMounted.current) return;
    setRegisterState("success");
  }

  return (
    <>
      <LandingNav locale={locale} />
      <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        {/* Back link */}
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
                event.status === "live"
                  ? "bg-red-500/10 text-red-600"
                  : event.status === "upcoming"
                    ? "bg-emerald-500/10 text-emerald-700"
                    : "bg-muted text-muted-foreground"
              )}
            >
              {event.status === "live"
                ? t("events.live")
                : event.status === "upcoming"
                  ? t("events.upcoming")
                  : t("events.past")}
            </span>
          </div>

          {/* Title */}
          <h1 className="mb-6 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {title}
          </h1>

          {/* Meta grid */}
          <div className="mb-6 grid grid-cols-1 gap-4 rounded-xl bg-muted/50 p-5 sm:grid-cols-2">
            <div className="flex items-start gap-3">
              <Building2 className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <div>
                <p className="text-xs font-medium text-muted-foreground">{t("events.organizer")}</p>
                <p className="text-sm font-semibold text-foreground">{event.organizerName}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <div>
                <p className="text-xs font-medium text-muted-foreground">{t("events.location")}</p>
                <p className="text-sm font-semibold text-foreground">{location}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Calendar className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <div>
                <p className="text-xs font-medium text-muted-foreground">{t("events.date")}</p>
                <p className="text-sm font-semibold text-foreground">
                  {formatDate(event.startDate, locale)}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Users className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  {t("events.volunteers")}
                </p>
                <p className="text-sm font-semibold text-foreground">
                  {event.currentVolunteers} / {event.maxVolunteers}
                  {!isPast && (
                    <span
                      className={cn(
                        "ml-2 text-xs font-medium",
                        isFull ? "text-destructive" : "text-emerald-600"
                      )}
                    >
                      {isFull
                        ? t("events.full")
                        : t("events.spotsLeft", { count: spotsLeft })}
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Description */}
          <div className="mb-8">
            <h2 className="mb-3 text-base font-semibold text-foreground">
              {t("events.about")}
            </h2>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {description}
            </p>
          </div>

          {/* Tags */}
          {event.tags.length > 0 && (
            <div className="mb-8 flex flex-wrap gap-2">
              {event.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Register CTA */}
          {!isPast && (
            <AnimatePresence mode="wait">
              {registerState === "success" ? (
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
                  onClick={handleRegister}
                  disabled={isFull || registerState === "loading"}
                  aria-busy={registerState === "loading"}
                  className={cn(
                    "w-full rounded-xl py-4 text-base font-semibold transition-all",
                    isFull
                      ? "cursor-not-allowed bg-muted text-muted-foreground"
                      : registerState === "loading"
                        ? "cursor-wait bg-primary/70 text-primary-foreground"
                        : "bg-primary text-primary-foreground hover:bg-primary/90 shadow-md hover:shadow-lg"
                  )}
                >
                  {registerState === "loading"
                    ? t("events.registering")
                    : isFull
                      ? t("events.full")
                      : t("events.register")}
                </motion.button>
              )}
            </AnimatePresence>
          )}
        </div>
      </main>
      <LandingFooter locale={locale} />
    </>
  );
}
