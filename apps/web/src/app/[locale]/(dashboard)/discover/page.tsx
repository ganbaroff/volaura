"use client";

import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Search, Users, Star, MapPin, Loader2, ChevronRight } from "lucide-react";
import { useDiscoverableVolunteers } from "@/hooks/queries/use-profile";
import type { DiscoverableVolunteer } from "@/hooks/queries/use-profile";
import { cn } from "@/lib/utils/cn";
import { Skeleton } from "@/components/ui/skeleton";

// ── Animations ────────────────────────────────────────────────────────────────

const fadeUp = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.24, ease: "easeOut" as const } },
};
const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };

// ── Badge styles ──────────────────────────────────────────────────────────────

const BADGE_STYLES: Record<string, { bg: string; text: string }> = {
  platinum: { bg: "bg-sky-400/15",    text: "text-sky-300" },
  gold:     { bg: "bg-yellow-400/15", text: "text-yellow-300" },
  silver:   { bg: "bg-slate-300/15",  text: "text-slate-300" },
  bronze:   { bg: "bg-orange-400/15", text: "text-orange-300" },
};

// ── Volunteer card ────────────────────────────────────────────────────────────

function VolunteerCard({
  volunteer,
  onClick,
}: {
  volunteer: DiscoverableVolunteer;
  onClick: () => void;
}) {
  const badgeStyle = BADGE_STYLES[volunteer.badge_tier?.toLowerCase() ?? ""] ?? null;
  const score = volunteer.total_score != null ? volunteer.total_score.toFixed(1) : "—";
  const initials = (volunteer.display_name ?? volunteer.username)[0]?.toUpperCase() ?? "?";

  return (
    <motion.div
      variants={fadeUp}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      className="flex items-center gap-4 rounded-xl border border-border bg-surface-container-low px-4 py-3 cursor-pointer hover:bg-surface-container hover:border-primary/30 transition-all"
    >
      {/* Avatar */}
      <span className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-sm font-bold text-primary">
        {initials}
      </span>

      {/* Name + bio */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-on-surface truncate">
          {volunteer.display_name ?? volunteer.username}
        </p>
        {volunteer.location && (
          <p className="flex items-center gap-1 text-xs text-on-surface-variant mt-0.5">
            <MapPin className="size-3" aria-hidden="true" />
            {volunteer.location}
          </p>
        )}
      </div>

      {/* Badge */}
      {badgeStyle && volunteer.badge_tier && (
        <span className={cn("shrink-0 text-xs font-medium px-2 py-0.5 rounded-full capitalize", badgeStyle.bg, badgeStyle.text)}>
          {volunteer.badge_tier}
        </span>
      )}

      {/* AURA score */}
      <div className="shrink-0 flex items-center gap-1 text-sm font-bold tabular-nums text-on-surface w-12 text-right">
        <Star className="size-3.5 text-yellow-400 shrink-0" aria-hidden="true" />
        {score}
      </div>

      <ChevronRight className="size-4 text-on-surface-variant shrink-0" aria-hidden="true" />
    </motion.div>
  );
}

function VolunteerSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 rounded-xl border border-border px-4 py-3">
          <Skeleton className="size-10 rounded-full" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="h-3 w-24" />
          </div>
          <Skeleton className="h-6 w-14 rounded-full" />
          <Skeleton className="h-4 w-12" />
        </div>
      ))}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DiscoverPage() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const isMounted = useRef(true);
  useEffect(() => () => { isMounted.current = false; }, []);

  const [search, setSearch] = useState("");
  const { data: volunteers, isLoading, isError } = useDiscoverableVolunteers({ limit: 50 });

  const filtered = (volunteers ?? []).filter((v) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      v.username.toLowerCase().includes(q) ||
      (v.display_name ?? "").toLowerCase().includes(q) ||
      (v.location ?? "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen bg-background px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-3xl space-y-6">

        {/* Header */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp}>
          <h1 className="font-headline text-2xl font-bold text-on-surface">
            {t("discover.title", { defaultValue: "Discover Volunteers" })}
          </h1>
          <p className="mt-1 text-sm text-on-surface-variant">
            {t("discover.subtitle", { defaultValue: "Browse verified volunteers who are open to opportunities" })}
          </p>
        </motion.div>

        {/* Search */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp}>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-on-surface-variant" aria-hidden="true" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("discover.searchPlaceholder", { defaultValue: "Search by name or location…" })}
              className="w-full rounded-xl border border-outline-variant bg-surface-container pl-9 pr-3 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
            />
          </div>
        </motion.div>

        {/* List */}
        {isLoading && <VolunteerSkeleton />}

        {isError && (
          <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center space-y-2">
            <p className="text-sm font-medium text-on-surface">
              {t("discover.accessError", { defaultValue: "Volunteer discovery requires an organization account." })}
            </p>
            <p className="text-xs text-on-surface-variant">
              {t("discover.accessErrorDesc", { defaultValue: "Make sure your account is set up as an organization." })}
            </p>
          </div>
        )}

        {!isLoading && !isError && filtered.length === 0 && (
          <div className="py-16 text-center space-y-2">
            <Users className="mx-auto size-10 text-on-surface-variant" aria-hidden="true" />
            <p className="text-sm text-on-surface-variant">
              {search
                ? t("discover.noResults", { defaultValue: "No volunteers match your search" })
                : t("discover.noVolunteers", { defaultValue: "No volunteers have opted in to discovery yet." })}
            </p>
          </div>
        )}

        {!isLoading && !isError && filtered.length > 0 && (
          <>
            <p className="text-xs text-on-surface-variant">
              {t("discover.count", {
                count: filtered.length,
                defaultValue: `${filtered.length} volunteer${filtered.length !== 1 ? "s" : ""} available`,
              })}
            </p>
            <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-2">
              {filtered.map((v) => (
                <VolunteerCard
                  key={v.id}
                  volunteer={v}
                  onClick={() => router.push(`/${locale}/u/${v.username}`)}
                />
              ))}
            </motion.div>
          </>
        )}

      </div>
    </div>
  );
}
