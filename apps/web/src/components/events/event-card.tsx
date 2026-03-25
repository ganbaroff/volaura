"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { MapPin, Users, Calendar, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { MockEvent } from "@/lib/mock-data";

interface EventCardProps {
  event: MockEvent;
  locale: string;
}

function formatDate(iso: string, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "az" ? "az-Latn-AZ" : "en-US", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

const STATUS_STYLES = {
  live: "bg-red-500/10 text-red-600 border-red-200",
  upcoming: "bg-emerald-500/10 text-emerald-700 border-emerald-200",
  past: "bg-muted text-muted-foreground border-border",
} as const;

export function EventCard({ event, locale }: EventCardProps) {
  const { t } = useTranslation();
  const [registering, setRegistering] = useState(false);
  const [registered, setRegistered] = useState(false);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const isFull = event.currentVolunteers >= event.maxVolunteers;
  const spotsLeft = event.maxVolunteers - event.currentVolunteers;
  const isPast = event.status === "past";
  const title = locale === "az" ? event.titleAz : event.title;
  const location = locale === "az" ? event.locationAz : event.location;

  async function handleRegister() {
    // Session 11: replace with real POST /api/events/{id}/register
    setRegistering(true);
    await new Promise((r) => setTimeout(r, 800)); // simulate API
    if (!isMounted.current) return;
    setRegistering(false);
    setRegistered(true);
  }

  return (
    <article
      className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-shadow hover:shadow-md"
      aria-label={title}
    >
      {/* Status bar */}
      <div
        className={cn(
          "px-4 py-1.5 text-xs font-semibold border-b",
          STATUS_STYLES[event.status]
        )}
        aria-live="polite"
      >
        {event.status === "live"
          ? t("events.live")
          : event.status === "upcoming"
            ? t("events.upcoming")
            : t("events.past")}
      </div>

      <div className="flex flex-1 flex-col p-5 gap-4">
        {/* Title + Organizer */}
        <div>
          <h3 className="mb-0.5 text-base font-semibold leading-snug text-foreground line-clamp-2">
            {title}
          </h3>
          <p className="text-xs text-muted-foreground">{event.organizerName}</p>
        </div>

        {/* Meta */}
        <div className="flex flex-col gap-1.5 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Calendar className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            {/* suppressHydrationWarning: toLocaleDateString output differs between
                Node.js (server, limited ICU) and browser (full locale support) */}
            <span suppressHydrationWarning>{formatDate(event.startDate, locale)}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span className="truncate">{location}</span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span>
              {t("events.volunteersCount", { count: event.currentVolunteers })}
              {!isPast && event.maxVolunteers > 0 && (
                <span className="ml-1 text-xs">
                  {isFull ? (
                    <span className="text-destructive font-medium">
                      · {t("events.full")}
                    </span>
                  ) : (
                    <span className="text-emerald-600 font-medium">
                      · {t("events.spotsLeft", { count: spotsLeft })}
                    </span>
                  )}
                </span>
              )}
            </span>
          </div>
        </div>

        {/* Tags */}
        {event.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5" aria-label="Event tags">
            {event.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="mt-auto flex items-center gap-2 pt-1">
          <Link
            href={`/${locale}/events/${event.id}`}
            className="flex-1 rounded-lg border border-border bg-background py-2 text-center text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            {t("events.viewDetails")}
          </Link>

          {!isPast && (
            <button
              type="button"
              onClick={handleRegister}
              disabled={isFull || registered || registering}
              aria-busy={registering}
              aria-label={registered ? t("events.registered") : t("events.register")}
              className={cn(
                "flex-1 rounded-lg py-2 text-sm font-semibold transition-all",
                registered
                  ? "bg-emerald-500/10 text-emerald-700 cursor-default"
                  : isFull
                    ? "bg-muted text-muted-foreground cursor-not-allowed"
                    : registering
                      ? "bg-primary/70 text-primary-foreground cursor-wait"
                      : "bg-primary text-primary-foreground hover:bg-primary/90"
              )}
            >
              {registered ? (
                <span className="flex items-center justify-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                  {t("events.registered")}
                </span>
              ) : registering ? (
                t("events.registering")
              ) : isFull ? (
                t("events.full")
              ) : (
                t("events.register")
              )}
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
