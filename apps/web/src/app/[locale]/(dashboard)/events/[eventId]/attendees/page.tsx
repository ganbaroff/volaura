"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { ArrowLeft, Users, UserCheck, UserX, Star } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";
import { useEventAttendees, useRateProfessional } from "@/hooks/queries/use-events";
import { useEvent } from "@/hooks/queries/use-events";
import type { EventAttendeeRow } from "@/hooks/queries/use-events";
import { ApiError } from "@/lib/api/client";
import { useEnergyMode } from "@/hooks/use-energy-mode";

// ── Badge chip ─────────────────────────────────────────────────────────────────

const BADGE_COLORS: Record<string, string> = {
  platinum: "bg-violet-500/15 text-violet-300 ring-violet-400/25",
  gold:     "bg-amber-500/15 text-amber-300 ring-amber-400/25",
  silver:   "bg-slate-400/15 text-slate-300 ring-slate-300/25",
  bronze:   "bg-orange-500/15 text-orange-300 ring-orange-400/25",
};

function BadgeChip({ tier }: { tier: string | null }) {
  if (!tier || tier === "none") return null;
  const cls = BADGE_COLORS[tier] ?? "bg-muted/15 text-muted-foreground ring-muted/25";
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 capitalize", cls)}>
      {tier}
    </span>
  );
}

// ── Status chip ────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  approved: "text-green-400",
  pending:  "text-amber-400",
  cancelled: "text-purple-400",
  checked_in: "text-primary",
};

// ── Star rating widget ─────────────────────────────────────────────────────────

function StarRating({
  registrationId,
  onRate,
  isPending,
}: {
  registrationId: string;
  onRate: (registrationId: string, rating: number) => void;
  isPending: boolean;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  const [selected, setSelected] = useState<number | null>(null);

  function handleClick(star: number) {
    if (isPending) return;
    setSelected(star);
    onRate(registrationId, star);
  }

  return (
    <div
      className="flex items-center gap-0.5"
      role="group"
      aria-label="Rate participant"
    >
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={isPending || selected !== null}
          onClick={(e) => { e.stopPropagation(); handleClick(star); }}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(null)}
          className="p-0.5 disabled:opacity-50"
          aria-label={`${star} star`}
        >
          <Star
            className={cn(
              "size-4 transition-colors",
              (hovered ?? selected ?? 0) >= star
                ? "fill-amber-400 text-amber-400"
                : "text-muted-foreground",
            )}
          />
        </button>
      ))}
    </div>
  );
}

// ── Attendee row ───────────────────────────────────────────────────────────────

function AttendeeRow({
  a,
  locale,
  index,
  onRate,
  isRatingPending,
  isLow,
}: {
  a: EventAttendeeRow;
  locale: string;
  index: number;
  onRate: (registrationId: string, rating: number) => void;
  isRatingPending: boolean;
  isLow: boolean;
}) {
  const router = useRouter();
  const statusColor = STATUS_COLORS[a.status] ?? "text-muted-foreground";
  const displayName = a.display_name ?? a.username ?? a.professional_id.slice(0, 8);
  const checkedIn = a.status === "checked_in" || !!a.checked_in_at;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.04 * index }}
      className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 hover:bg-card/80 transition-colors cursor-pointer"
      onClick={() => a.username && router.push(`/${locale}/u/${a.username}`)}
      role={a.username ? "link" : undefined}
      tabIndex={a.username ? 0 : undefined}
      onKeyDown={(e) => {
        if (a.username && (e.key === "Enter" || e.key === " ")) router.push(`/${locale}/u/${a.username}`);
      }}
      aria-label={displayName}
    >
      {/* Check-in indicator */}
      <div className="flex-shrink-0">
        {checkedIn ? (
          <UserCheck className="size-5 text-green-400" aria-label="Checked in" />
        ) : (
          <UserX className="size-5 text-muted-foreground" aria-label="Not checked in" />
        )}
      </div>

      {/* Name */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{displayName}</p>
        {a.username && (
          <p className="text-xs text-muted-foreground">@{a.username}</p>
        )}
      </div>

      {/* AURA score — hidden at low energy */}
      {!isLow && a.total_score !== null && (
        <span className="text-sm font-mono tabular-nums text-muted-foreground w-12 text-right shrink-0">
          {a.total_score.toFixed(1)}
        </span>
      )}

      {/* Badge tier — hidden at low energy */}
      {!isLow && <BadgeChip tier={a.badge_tier} />}

      {/* Status */}
      <span className={cn("text-xs font-medium capitalize shrink-0", statusColor)}>
        {a.status.replace(/_/g, " ")}
      </span>

      {/* Star rating — hidden at low energy */}
      {!isLow && checkedIn && (
        <StarRating
          registrationId={a.registration_id}
          onRate={onRate}
          isPending={isRatingPending}
        />
      )}
    </motion.div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function EventAttendeesPage() {
  const { locale, eventId } = useParams<{ locale: string; eventId: string }>();
  const { t } = useTranslation();
  const router = useRouter();

  const { energy } = useEnergyMode();
  const isLow = energy === "low";

  const { data: event } = useEvent(eventId);
  const { data: attendees, isLoading, error } = useEventAttendees(eventId);
  const rateProfessional = useRateProfessional(eventId);

  function handleRate(registrationId: string, rating: number) {
    rateProfessional.mutate({ registration_id: registrationId, rating });
  }

  const eventTitle = locale === "az"
    ? (event?.title_az ?? event?.title_en ?? "")
    : (event?.title_en ?? event?.title_az ?? "");

  const checkedInCount = (attendees ?? []).filter((a) => a.status === "checked_in" || !!a.checked_in_at).length;
  const totalCount = (attendees ?? []).length;

  // 403 → not org owner
  const isForbidden = error instanceof ApiError && error.status === 403;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 space-y-6">
      {/* Back */}
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 text-muted-foreground"
        onClick={() => router.back()}
      >
        <ArrowLeft className="size-4 mr-1" />
        {t("common.back", { defaultValue: "Back" })}
      </Button>

      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <Users className="size-5 text-primary" />
          <h1 className="text-xl font-bold">{t("events.attendees", { defaultValue: "Attendees" })}</h1>
        </div>
        {eventTitle && (
          <p className="text-sm text-muted-foreground">{eventTitle}</p>
        )}
        {!isLow && !isLoading && totalCount > 0 && (
          <p className="text-xs text-muted-foreground">
            {totalCount} {t("events.registered", { defaultValue: "registered" })} ·{" "}
            {checkedInCount} {t("events.checkedIn", { defaultValue: "checked in" })}
          </p>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-2" role="status" aria-live="polite">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3">
              <Skeleton className="size-5 rounded" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      )}

      {/* Forbidden */}
      {isForbidden && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center">
          <p className="text-sm text-muted-foreground">
            {t("events.notOrgOwner", { defaultValue: "Only the organization owner can view attendees." })}
          </p>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isForbidden && (attendees ?? []).length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
          <Users className="size-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            {t("events.noAttendees", { defaultValue: "No registrations yet." })}
          </p>
        </div>
      )}

      {/* List */}
      {!isLoading && (attendees ?? []).length > 0 && (
        <div className="space-y-2">
          {attendees!.map((a, i) => (
            <AttendeeRow
              key={a.registration_id}
              a={a}
              locale={locale}
              index={i}
              onRate={handleRate}
              isRatingPending={rateProfessional.isPending}
              isLow={isLow}
            />
          ))}
        </div>
      )}
    </div>
  );
}
