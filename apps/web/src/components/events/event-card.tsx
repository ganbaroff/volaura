"use client";

import { useRef, useEffect } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { MapPin, Users, Calendar, CheckCircle2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useRegisterForEvent } from "@/hooks/queries/use-events";
import type { EventResponse } from "@/lib/api/types";

interface EventCardProps {
  event: EventResponse;
  locale: string;
}

function formatDate(iso: string | Date, locale: string): string {
  return new Date(iso).toLocaleDateString(locale === "az" ? "az-Latn-AZ" : "en-US", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

/** Maps API status to display category */
function getDisplayStatus(status: string): "live" | "upcoming" | "past" {
  if (status === "open") return "upcoming";
  if (status === "completed" || status === "closed" || status === "cancelled") return "past";
  return "upcoming";
}

const STATUS_STYLES = {
  live:     "bg-purple-500/10 text-purple-400 border-purple-200",
  upcoming: "bg-emerald-500/10 text-emerald-700 border-emerald-200",
  past:     "bg-muted text-muted-foreground border-border",
} as const;

export function EventCard({ event, locale }: EventCardProps) {
  const { t } = useTranslation();
  const isMounted = useRef(true);
  const registerMutation = useRegisterForEvent();

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const displayStatus = getDisplayStatus(event.status);
  const isPast = displayStatus === "past";
  const isOpen = event.status === "open";
  const isFull = event.capacity != null && event.capacity <= 0;
  const title = locale === "az" ? event.title_az : event.title_en;

  const registered = registerMutation.isSuccess;
  const registering = registerMutation.isPending;

  function handleRegister() {
    registerMutation.mutate({ eventId: event.id });
  }

  return (
    <article
      className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-shadow hover:shadow-md"
      aria-label={title}
    >
      {/* Status bar */}
      <div
        className={cn("px-4 py-1.5 text-xs font-semibold border-b", STATUS_STYLES[displayStatus])}
        aria-live="polite"
      >
        {displayStatus === "live"
          ? t("events.live")
          : displayStatus === "upcoming"
            ? t("events.upcoming")
            : t("events.past")}
      </div>

      <div className="flex flex-1 flex-col p-5 gap-4">
        {/* Title */}
        <h3 className="text-base font-semibold leading-snug text-foreground line-clamp-2">
          {title}
        </h3>

        {/* Meta */}
        <div className="flex flex-col gap-1.5 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Calendar className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            {/* suppressHydrationWarning: toLocaleDateString differs server/browser */}
            <span suppressHydrationWarning>{formatDate(event.start_date, locale)}</span>
          </div>
          {event.location && (
            <div className="flex items-center gap-2">
              <MapPin className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <span className="truncate">{event.location}</span>
            </div>
          )}
          {event.capacity != null && (
            <div className="flex items-center gap-2">
              <Users className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <span>
                {t("events.capacity", { count: event.capacity, defaultValue: `${event.capacity} spots` })}
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-auto flex items-center gap-2 pt-1">
          <Link
            href={`/${locale}/events/${event.id}`}
            className="flex-1 rounded-lg border border-border bg-background py-2 text-center text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            {t("events.viewDetails")}
          </Link>

          {isOpen && (
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
                <Loader2 className="mx-auto h-4 w-4 animate-spin" aria-hidden="true" />
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
