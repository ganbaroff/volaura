"use client";

import { useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { Skeleton } from "@/components/ui/skeleton";
import { CalendarX } from "lucide-react";
import { EventsList } from "@/components/events/events-list";
import { LandingNav } from "@/components/landing/landing-nav";
import { LandingFooter } from "@/components/landing/landing-footer";
import { useEvents } from "@/hooks/queries/use-events";

function EventsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card">
          <Skeleton className="h-8 w-full" />
          <div className="flex flex-col gap-3 p-5">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-10 w-full mt-2" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function EventsPage() {
  const params = useParams<{ locale: string }>();
  const locale = params.locale ?? "az";
  const { t } = useTranslation();

  const { data: events, isLoading, isError } = useEvents({ limit: 50 });

  return (
    <>
      <LandingNav locale={locale} />
      <main className="mx-auto min-h-screen max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {t("events.title")}
          </h1>
          <p className="mt-2 text-muted-foreground">
            {t("events.noEventsSubtitle")}
          </p>
        </div>

        {isLoading && <EventsSkeleton />}

        {isError && (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center">
            <CalendarX className="mb-4 h-12 w-12 text-muted-foreground/40" aria-hidden="true" />
            <p className="text-lg font-semibold text-muted-foreground">
              {t("events.loadError", { defaultValue: "Could not load events" })}
            </p>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground/70">
              {t("events.loadErrorDesc", { defaultValue: "Please try refreshing the page." })}
            </p>
          </div>
        )}

        {!isLoading && !isError && (
          <EventsList events={events ?? []} locale={locale} />
        )}
      </main>
      <LandingFooter locale={locale} />
    </>
  );
}
