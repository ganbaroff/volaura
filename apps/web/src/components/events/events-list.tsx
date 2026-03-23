"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { EventCard } from "./event-card";
import type { MockEvent } from "@/lib/mock-data";
import { CalendarX } from "lucide-react";
import { cn } from "@/lib/utils/cn";

type FilterTab = "all" | "upcoming" | "past";

interface EventsListProps {
  events: MockEvent[];
  locale: string;
}

const FILTERS: FilterTab[] = ["all", "upcoming", "past"];

export function EventsList({ events, locale }: EventsListProps) {
  const { t } = useTranslation();
  const [activeFilter, setActiveFilter] = useState<FilterTab>("all");

  const filtered = events.filter((e) => {
    if (activeFilter === "all") return true;
    return e.status === activeFilter || (activeFilter === "upcoming" && e.status === "live");
  });

  return (
    <div>
      {/* Filter tabs */}
      <div
        className="mb-6 flex gap-1 rounded-xl bg-muted p-1 w-fit"
        role="tablist"
        aria-label="Filter events"
      >
        {FILTERS.map((filter) => (
          <button
            key={filter}
            role="tab"
            aria-selected={activeFilter === filter}
            onClick={() => setActiveFilter(filter)}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-medium transition-all",
              activeFilter === filter
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {filter === "all"
              ? t("events.filterAll")
              : filter === "upcoming"
                ? t("events.filterUpcoming")
                : t("events.filterPast")}
          </button>
        ))}
      </div>

      {/* Events grid or empty state */}
      {filtered.length === 0 ? (
        <div
          className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-20 text-center"
          role="status"
        >
          <CalendarX className="mb-4 h-12 w-12 text-muted-foreground/40" aria-hidden="true" />
          <p className="text-lg font-semibold text-muted-foreground">
            {t("events.noEvents")}
          </p>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground/70">
            {t("events.noEventsSubtitle")}
          </p>
        </div>
      ) : (
        <div
          className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
          role="list"
          aria-label="Events list"
        >
          {filtered.map((event) => (
            <div key={event.id} role="listitem">
              <EventCard event={event} locale={locale} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
