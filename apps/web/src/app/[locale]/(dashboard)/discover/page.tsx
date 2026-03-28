"use client";

import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Users, Star, MapPin, Loader2, ChevronRight, Sparkles } from "lucide-react";
import { useDiscoverableVolunteers } from "@/hooks/queries/use-profile";
import type { DiscoverableVolunteer } from "@/hooks/queries/use-profile";
import { useVolunteerSearch } from "@/hooks/queries/use-organizations";
import type { VolunteerSearchResultItem } from "@/hooks/queries/use-organizations";
import { cn } from "@/lib/utils/cn";
import { Skeleton } from "@/components/ui/skeleton";

// ── Animations ─────────────────────────────────────────────────────────────────

const fadeUp = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.24, ease: "easeOut" as const } },
};
const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };

// ── Badge styles ───────────────────────────────────────────────────────────────

const BADGE_STYLES: Record<string, { bg: string; text: string }> = {
  platinum: { bg: "bg-sky-400/15",    text: "text-sky-300" },
  gold:     { bg: "bg-yellow-400/15", text: "text-yellow-300" },
  silver:   { bg: "bg-slate-300/15",  text: "text-slate-300" },
  bronze:   { bg: "bg-orange-400/15", text: "text-orange-300" },
};

// ── Similarity label ───────────────────────────────────────────────────────────

function similarityLabel(sim: number | null): { label: string; cls: string } | null {
  if (sim === null || sim === undefined) return null;
  if (sim >= 0.70) return { label: "High match", cls: "text-emerald-400 bg-emerald-400/10" };
  if (sim >= 0.50) return { label: "Good match", cls: "text-yellow-400 bg-yellow-400/10" };
  return { label: "Partial match", cls: "text-on-surface-variant bg-surface-container" };
}

// ── Browse volunteer card ──────────────────────────────────────────────────────

function BrowseCard({ volunteer, onClick }: { volunteer: DiscoverableVolunteer; onClick: () => void }) {
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
      <span className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-sm font-bold text-primary">
        {initials}
      </span>
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
      {badgeStyle && volunteer.badge_tier && (
        <span className={cn("shrink-0 text-xs font-medium px-2 py-0.5 rounded-full capitalize", badgeStyle.bg, badgeStyle.text)}>
          {volunteer.badge_tier}
        </span>
      )}
      <div className="shrink-0 flex items-center gap-1 text-sm font-bold tabular-nums text-on-surface w-12 text-right">
        <Star className="size-3.5 text-yellow-400 shrink-0" aria-hidden="true" />
        {score}
      </div>
      <ChevronRight className="size-4 text-on-surface-variant shrink-0" aria-hidden="true" />
    </motion.div>
  );
}

// ── Search result card ─────────────────────────────────────────────────────────

function SearchResultCard({ result, onClick }: { result: VolunteerSearchResultItem; onClick: () => void }) {
  const badgeStyle = BADGE_STYLES[result.badge_tier?.toLowerCase() ?? ""] ?? null;
  const score = result.overall_score != null ? result.overall_score.toFixed(1) : "—";
  const initials = (result.display_name ?? result.username)[0]?.toUpperCase() ?? "?";
  const sim = similarityLabel(result.similarity);

  return (
    <motion.div
      variants={fadeUp}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      className="flex items-center gap-4 rounded-xl border border-border bg-surface-container-low px-4 py-3 cursor-pointer hover:bg-surface-container hover:border-primary/30 transition-all"
    >
      <span className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-sm font-bold text-primary">
        {initials}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-on-surface truncate">
          {result.display_name ?? result.username}
        </p>
        {result.location && (
          <p className="flex items-center gap-1 text-xs text-on-surface-variant mt-0.5">
            <MapPin className="size-3" aria-hidden="true" />
            {result.location}
          </p>
        )}
      </div>
      {sim && (
        <span className={cn("shrink-0 text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap", sim.cls)}>
          {sim.label}
        </span>
      )}
      {badgeStyle && result.badge_tier && (
        <span className={cn("shrink-0 text-xs font-medium px-2 py-0.5 rounded-full capitalize", badgeStyle.bg, badgeStyle.text)}>
          {result.badge_tier}
        </span>
      )}
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
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 rounded-xl border border-border px-4 py-3">
          <Skeleton className="size-10 rounded-full" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="h-3 w-24" />
          </div>
          <Skeleton className="h-6 w-20 rounded-full" />
          <Skeleton className="h-4 w-12" />
        </div>
      ))}
    </div>
  );
}

// ── Min-AURA filter buttons ────────────────────────────────────────────────────

const AURA_FILTERS = [
  { label: "Any",         value: 0  },
  { label: "Bronze+",     value: 40 },
  { label: "Silver+",     value: 60 },
  { label: "Gold+",       value: 75 },
] as const;

const BADGE_FILTERS = [
  { label: "All tiers",  value: null       },
  { label: "Platinum",   value: "platinum" },
  { label: "Gold",       value: "gold"     },
  { label: "Silver",     value: "silver"   },
  { label: "Bronze",     value: "bronze"   },
] as const;

type BadgeTierFilter = "platinum" | "gold" | "silver" | "bronze" | null;

// ── Page ───────────────────────────────────────────────────────────────────────

export default function DiscoverPage() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const isMounted = useRef(true);
  useEffect(() => () => { isMounted.current = false; }, []);

  // Mode toggle
  const [mode, setMode] = useState<"browse" | "search">("browse");

  // Browse state
  const [browseSearch, setBrowseSearch] = useState("");
  const { data: volunteers, isLoading: browseLoading, isError: browseError } = useDiscoverableVolunteers({ limit: 50 });

  const filtered = (volunteers ?? []).filter((v) => {
    if (!browseSearch) return true;
    const q = browseSearch.toLowerCase();
    return (
      v.username.toLowerCase().includes(q) ||
      (v.display_name ?? "").toLowerCase().includes(q) ||
      (v.location ?? "").toLowerCase().includes(q)
    );
  });

  // Semantic search state
  const [query, setQuery] = useState("");
  const [minAura, setMinAura] = useState(0);
  const [badgeTier, setBadgeTier] = useState<BadgeTierFilter>(null);
  const searchMutation = useVolunteerSearch();

  const canSearch = query.trim().length >= 2;

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!canSearch) return;
    searchMutation.mutate({
      query: query.trim(),
      min_aura: minAura,
      badge_tier: badgeTier,
    });
  }

  function handleClearSearch() {
    setMode("browse");
    setQuery("");
    setMinAura(0);
    setBadgeTier(null);
    searchMutation.reset();
  }

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

        {/* Mode toggle */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp}
          className="flex gap-2 p-1 rounded-xl bg-surface-container w-fit"
          role="tablist"
          aria-label={t("discover.modeToggle", { defaultValue: "Discovery mode" })}
        >
          <button
            role="tab"
            aria-selected={mode === "browse"}
            onClick={() => setMode("browse")}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              mode === "browse"
                ? "bg-surface text-on-surface shadow-sm"
                : "text-on-surface-variant hover:text-on-surface"
            )}
          >
            <Users className="size-3.5" aria-hidden="true" />
            {t("discover.browse", { defaultValue: "Browse" })}
          </button>
          <button
            role="tab"
            aria-selected={mode === "search"}
            onClick={() => setMode("search")}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              mode === "search"
                ? "bg-surface text-on-surface shadow-sm"
                : "text-on-surface-variant hover:text-on-surface"
            )}
          >
            <Sparkles className="size-3.5" aria-hidden="true" />
            {t("discover.semanticSearch", { defaultValue: "Smart Search" })}
          </button>
        </motion.div>

        <AnimatePresence mode="wait">

          {/* ── BROWSE MODE ─────────────────────────────────────────────── */}
          {mode === "browse" && (
            <motion.div
              key="browse"
              initial="hidden" animate="visible" exit={{ opacity: 0 }}
              variants={stagger}
              className="space-y-4"
            >
              {/* Search input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-on-surface-variant" aria-hidden="true" />
                <input
                  type="search"
                  value={browseSearch}
                  onChange={(e) => setBrowseSearch(e.target.value)}
                  placeholder={t("discover.searchPlaceholder", { defaultValue: "Filter by name or location…" })}
                  className="w-full rounded-xl border border-outline-variant bg-surface-container pl-9 pr-3 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                />
              </div>

              {/* List */}
              {browseLoading && <VolunteerSkeleton />}

              {browseError && (
                <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center space-y-2">
                  <p className="text-sm font-medium text-on-surface">
                    {t("discover.accessError", { defaultValue: "Volunteer discovery requires an organization account." })}
                  </p>
                  <p className="text-xs text-on-surface-variant">
                    {t("discover.accessErrorDesc", { defaultValue: "Make sure your account is set up as an organization." })}
                  </p>
                </div>
              )}

              {!browseLoading && !browseError && filtered.length === 0 && (
                <div className="py-16 text-center space-y-2">
                  <Users className="mx-auto size-10 text-on-surface-variant" aria-hidden="true" />
                  <p className="text-sm text-on-surface-variant">
                    {browseSearch
                      ? t("discover.noResults", { defaultValue: "No volunteers match your filter" })
                      : t("discover.noVolunteers", { defaultValue: "No volunteers have opted in to discovery yet." })}
                  </p>
                </div>
              )}

              {!browseLoading && !browseError && filtered.length > 0 && (
                <>
                  <p className="text-xs text-on-surface-variant">
                    {t("discover.count", {
                      count: filtered.length,
                      defaultValue: `${filtered.length} volunteer${filtered.length !== 1 ? "s" : ""} available`,
                    })}
                  </p>
                  <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-2">
                    {filtered.map((v) => (
                      <BrowseCard
                        key={v.id}
                        volunteer={v}
                        onClick={() => router.push(`/${locale}/u/${v.username}`)}
                      />
                    ))}
                  </motion.div>
                </>
              )}
            </motion.div>
          )}

          {/* ── SEMANTIC SEARCH MODE ────────────────────────────────────── */}
          {mode === "search" && (
            <motion.div
              key="search"
              initial="hidden" animate="visible" exit={{ opacity: 0 }}
              variants={stagger}
              className="space-y-5"
            >
              <form onSubmit={handleSearch} className="space-y-4">
                {/* Query input */}
                <div className="relative">
                  <Sparkles className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary/60" aria-hidden="true" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={t("discover.queryPlaceholder", { defaultValue: "e.g. experienced team leader for youth events…" })}
                    className="w-full rounded-xl border border-outline-variant bg-surface-container pl-9 pr-3 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                    aria-label={t("discover.queryLabel", { defaultValue: "Search query" })}
                  />
                </div>

                {/* Filters row */}
                <div className="space-y-3">
                  {/* Min AURA */}
                  <div>
                    <p className="text-xs font-medium text-on-surface-variant mb-1.5">
                      {t("discover.minAura", { defaultValue: "Min AURA score" })}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {AURA_FILTERS.map(({ label, value }) => (
                        <button
                          key={value}
                          type="button"
                          onClick={() => setMinAura(value)}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                            minAura === value
                              ? "bg-primary text-on-primary border-primary"
                              : "border-outline-variant text-on-surface-variant hover:bg-surface-container"
                          )}
                        >
                          {t(`discover.aura.${label.replace("+", "Plus")}`, { defaultValue: label })}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Badge tier */}
                  <div>
                    <p className="text-xs font-medium text-on-surface-variant mb-1.5">
                      {t("discover.badgeTier", { defaultValue: "Badge tier" })}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {BADGE_FILTERS.map(({ label, value }) => (
                        <button
                          key={label}
                          type="button"
                          onClick={() => setBadgeTier(value)}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors capitalize",
                            badgeTier === value
                              ? "bg-primary text-on-primary border-primary"
                              : "border-outline-variant text-on-surface-variant hover:bg-surface-container"
                          )}
                        >
                          {t(`discover.badge.${label.replace(" ", "")}`, { defaultValue: label })}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={!canSearch || searchMutation.isPending}
                  className="w-full rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {searchMutation.isPending ? (
                    <>
                      <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                      {t("discover.searching", { defaultValue: "Searching…" })}
                    </>
                  ) : (
                    <>
                      <Search className="size-4" aria-hidden="true" />
                      {t("discover.search", { defaultValue: "Search" })}
                    </>
                  )}
                </button>
              </form>

              {/* Results */}
              {searchMutation.isError && (
                <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-4 text-center">
                  <p className="text-sm text-on-surface">
                    {t("discover.searchError", { defaultValue: "Search failed. Please try again." })}
                  </p>
                </div>
              )}

              {searchMutation.isSuccess && searchMutation.data.length === 0 && (
                <div className="py-12 text-center space-y-3">
                  <Search className="mx-auto size-10 text-on-surface-variant" aria-hidden="true" />
                  <p className="text-sm text-on-surface-variant">
                    {t("discover.searchNoResults", { defaultValue: "No volunteers matched your search." })}
                  </p>
                  <button
                    onClick={handleClearSearch}
                    className="text-sm text-primary underline-offset-2 hover:underline"
                  >
                    {t("discover.backToBrowse", { defaultValue: "← Back to browse" })}
                  </button>
                </div>
              )}

              {searchMutation.isSuccess && searchMutation.data.length > 0 && (
                <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-on-surface-variant">
                      {t("discover.searchCount", {
                        count: searchMutation.data.length,
                        defaultValue: `${searchMutation.data.length} result${searchMutation.data.length !== 1 ? "s" : ""}`,
                      })}
                    </p>
                    <button
                      onClick={handleClearSearch}
                      className="text-xs text-on-surface-variant hover:text-primary transition-colors"
                    >
                      {t("discover.clearSearch", { defaultValue: "Clear" })}
                    </button>
                  </div>
                  <div className="space-y-2">
                    {searchMutation.data.map((r) => (
                      <SearchResultCard
                        key={r.volunteer_id}
                        result={r}
                        onClick={() => router.push(`/${locale}/u/${r.username}`)}
                      />
                    ))}
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}

        </AnimatePresence>

      </div>
    </div>
  );
}
