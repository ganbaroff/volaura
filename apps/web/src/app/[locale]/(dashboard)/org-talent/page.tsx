"use client";

import { useRef, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import {
  Users, TrendingUp, Award, CheckCircle2, Clock,
  ChevronRight, BarChart3, Search, Bookmark, BookmarkCheck, X, Bell, BellOff,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useOrgDashboard, useOrgProfessionals, useCreateSavedSearch, useSavedSearches, useDeleteSavedSearch } from "@/hooks/queries/use-organizations";
import { cn } from "@/lib/utils/cn";
import type { OrgProfessionalRow } from "@/lib/api/types";

// ── Animations ─────────────────────────────────────────────────────────────────

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: "easeOut" as const } },
};
const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
};

// ── Badge tier styles ───────────────────────────────────────────────────────────

const TIER_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  platinum: { bg: "bg-sky-400/15", text: "text-sky-300", label: "Platinum" },
  gold:     { bg: "bg-yellow-400/15", text: "text-yellow-300", label: "Gold" },
  silver:   { bg: "bg-slate-300/15", text: "text-slate-300", label: "Silver" },
  bronze:   { bg: "bg-orange-400/15", text: "text-orange-300", label: "Bronze" },
  none:     { bg: "bg-surface-container", text: "text-on-surface-variant", label: "—" },
};

// ── Stat card ──────────────────────────────────────────────────────────────────

function StatCard({
  icon,
  value,
  label,
  sub,
  highlight,
}: {
  icon: React.ReactNode;
  value: string | number;
  label: string;
  sub?: string;
  highlight?: boolean;
}) {
  return (
    <motion.div variants={fadeUp} className="rounded-xl border border-border bg-surface-container-low p-4 space-y-1">
      <div className={cn("mb-1.5", highlight ? "text-primary" : "text-on-surface-variant")}>{icon}</div>
      <p className={cn("text-2xl font-bold tabular-nums", highlight ? "text-primary" : "text-on-surface")}>{value}</p>
      <p className="text-xs text-on-surface-variant">{label}</p>
      {sub && <p className="text-xs text-on-surface-variant/60">{sub}</p>}
    </motion.div>
  );
}

// ── Professional row ──────────────────────────────────────────────────────────

function ProfessionalRow({ row, onClick }: { row: OrgProfessionalRow; onClick: () => void }) {
  const tier = TIER_STYLES[row.badge_tier?.toLowerCase() ?? "none"] ?? TIER_STYLES.none;
  const score = row.overall_score != null ? row.overall_score.toFixed(1) : "—";

  return (
    <motion.div
      variants={fadeUp}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      className="flex items-center gap-3 rounded-xl border border-border bg-surface-container-low px-4 py-3 cursor-pointer hover:bg-surface-container hover:border-primary/30 transition-all"
    >
      {/* Avatar initials */}
      <span className="size-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-sm font-bold text-primary">
        {(row.display_name ?? row.username)[0]?.toUpperCase() ?? "?"}
      </span>

      {/* Name + username */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-on-surface truncate">
          {row.display_name ?? row.username}
        </p>
        <p className="text-xs text-on-surface-variant">@{row.username}</p>
      </div>

      {/* Badge tier */}
      <span className={cn("shrink-0 text-xs font-medium px-2 py-0.5 rounded-full", tier.bg, tier.text)}>
        {tier.label}
      </span>

      {/* AURA score */}
      <span className="shrink-0 text-sm font-bold tabular-nums text-on-surface w-10 text-right">
        {score}
      </span>

      {/* Competencies */}
      <span className="hidden sm:inline shrink-0 text-xs text-on-surface-variant w-16 text-right">
        {row.competencies_completed} comp.
      </span>

      <ChevronRight className="size-4 text-on-surface-variant shrink-0" aria-hidden="true" />
    </motion.div>
  );
}

// ── Badge distribution mini-chart ──────────────────────────────────────────────

function BadgeBar({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-14 text-on-surface-variant shrink-0">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.2 }}
          className={cn("h-full rounded-full", color)}
        />
      </div>
      <span className="w-5 text-right text-on-surface-variant tabular-nums">{count}</span>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

const STATUS_FILTERS = [
  { key: undefined,       label: "All" },
  { key: "assigned",      label: "Assigned" },
  { key: "completed",     label: "Completed" },
  { key: "in_progress",   label: "In Progress" },
];

export default function OrgTalentPage() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const isMounted = useRef(true);
  useEffect(() => () => { isMounted.current = false; }, []);

  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [search, setSearch] = useState("");

  // ── Saved searches ──────────────────────────────────────────────────────────
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saveNotify, setSaveNotify] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const { data: savedSearches } = useSavedSearches();
  const createSavedSearch = useCreateSavedSearch();
  const deleteSavedSearch = useDeleteSavedSearch();

  async function handleSaveSearch() {
    if (!saveName.trim()) return;
    try {
      await createSavedSearch.mutateAsync({
        name: saveName.trim(),
        filters: { query: search || undefined },
        notify_on_match: saveNotify,
      });
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        setShowSaveModal(false);
        setSaveName("");
      }, 1500);
    } catch {
      // Error handled by mutation state
    }
  }

  const { data: stats, isLoading: statsLoading } = useOrgDashboard();
  const { data: professionals, isLoading: volsLoading } = useOrgProfessionals({ status: statusFilter, limit: 50 });

  const filtered = (professionals ?? []).filter((v) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      v.username.toLowerCase().includes(q) ||
      (v.display_name ?? "").toLowerCase().includes(q)
    );
  });

  const bd = stats?.badge_distribution;
  const totalBadges = bd
    ? (bd.platinum ?? 0) + (bd.gold ?? 0) + (bd.silver ?? 0) + (bd.bronze ?? 0) + (bd.none ?? 0)
    : 0;

  const isLoading = statsLoading || volsLoading;

  return (
    <div className="min-h-screen bg-background px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-3xl space-y-8">

        {/* Header */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp}>
          <h1 className="font-headline text-2xl font-bold text-on-surface">
            {t("orgDash.title", { defaultValue: "Talent Dashboard" })}
          </h1>
          <p className="mt-1 text-sm text-on-surface-variant">
            {t("orgDash.subtitle", { defaultValue: "Track assessment completion and AURA scores across your professionals" })}
          </p>
        </motion.div>

        {isLoading && (
          <div className="space-y-6" role="status" aria-live="polite">
            {/* Stats row skeleton */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="rounded-xl border border-border bg-surface-container-low p-4 space-y-2">
                  <Skeleton className="size-5 rounded" />
                  <Skeleton className="h-7 w-16" />
                  <Skeleton className="h-3 w-24" />
                </div>
              ))}
            </div>
            {/* Professional list skeleton */}
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 rounded-xl border border-border px-4 py-3">
                  <Skeleton className="size-9 rounded-full" />
                  <div className="flex-1 space-y-1.5">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                  <Skeleton className="h-5 w-16 rounded-full" />
                  <Skeleton className="h-4 w-10" />
                </div>
              ))}
            </div>
          </div>
        )}

        {!isLoading && stats && (
          <>
            {/* Stats row */}
            <motion.div variants={stagger} initial="hidden" animate="visible" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard
                icon={<Users className="size-5" />}
                value={stats.total_assigned}
                label={t("orgDash.assigned", { defaultValue: "Assigned" })}
                highlight={false}
              />
              <StatCard
                icon={<CheckCircle2 className="size-5" />}
                value={stats.total_completed}
                label={t("orgDash.completed", { defaultValue: "Completed" })}
                sub={`${Math.round(stats.completion_rate * 100)}% rate`}
                highlight
              />
              <StatCard
                icon={<TrendingUp className="size-5" />}
                value={stats.avg_aura_score != null ? stats.avg_aura_score.toFixed(1) : "—"}
                label={t("orgDash.avgAura", { defaultValue: "Avg AURA" })}
              />
              <StatCard
                icon={<Award className="size-5" />}
                value={(bd?.platinum ?? 0) + (bd?.gold ?? 0)}
                label={t("orgDash.topTier", { defaultValue: "Gold/Platinum" })}
              />
            </motion.div>

            {/* Badge distribution */}
            {totalBadges > 0 && (
              <motion.div variants={fadeUp} initial="hidden" animate="visible" className="rounded-xl border border-border bg-surface-container-low p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="size-4 text-on-surface-variant" aria-hidden="true" />
                  <h3 className="text-sm font-semibold text-on-surface">
                    {t("orgDash.badgeDist", { defaultValue: "Badge Distribution" })}
                  </h3>
                </div>
                <div className="space-y-2">
                  <BadgeBar label="Platinum" count={bd?.platinum ?? 0} total={totalBadges} color="bg-sky-400" />
                  <BadgeBar label="Gold"     count={bd?.gold ?? 0}     total={totalBadges} color="bg-yellow-400" />
                  <BadgeBar label="Silver"   count={bd?.silver ?? 0}   total={totalBadges} color="bg-slate-400" />
                  <BadgeBar label="Bronze"   count={bd?.bronze ?? 0}   total={totalBadges} color="bg-orange-400" />
                  <BadgeBar label="None"     count={bd?.none ?? 0}     total={totalBadges} color="bg-border" />
                </div>
              </motion.div>
            )}

            {/* Top professionals highlight */}
            {stats.top_professionals.length > 0 && (
              <motion.div variants={fadeUp} initial="hidden" animate="visible" className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3">
                <h3 className="text-sm font-semibold text-primary">
                  {t("orgDash.topTalent", { defaultValue: "⭐ Top Talent" })}
                </h3>
                <div className="space-y-2">
                  {stats.top_professionals.map((v) => {
                    const tier = TIER_STYLES[v.badge_tier?.toLowerCase() ?? "none"] ?? TIER_STYLES.none;
                    return (
                      <div
                        key={v.professional_id}
                        className="flex items-center gap-3 text-sm"
                      >
                        <span className="size-7 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary shrink-0">
                          {(v.display_name ?? v.username)[0]?.toUpperCase()}
                        </span>
                        <span className="flex-1 text-on-surface truncate">{v.display_name ?? v.username}</span>
                        <span className={cn("text-xs px-1.5 py-0.5 rounded-full font-medium", tier.bg, tier.text)}>
                          {tier.label}
                        </span>
                        <span className="font-bold tabular-nums text-on-surface w-10 text-right">
                          {v.overall_score?.toFixed(1) ?? "—"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </>
        )}

        {/* Professional list */}
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-on-surface-variant" aria-hidden="true" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("orgDash.searchProfessionals", { defaultValue: "Search professionals…" })}
                className="w-full rounded-xl border border-outline-variant bg-surface-container pl-9 pr-3 py-2 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
              />
            </div>

            <div className="flex flex-wrap gap-1.5 shrink-0">
              {STATUS_FILTERS.map(({ key, label }) => (
                <button
                  key={label}
                  onClick={() => setStatusFilter(key)}
                  className={cn(
                    "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors border",
                    statusFilter === key
                      ? "bg-primary text-on-primary border-primary"
                      : "border-outline-variant text-on-surface-variant hover:bg-surface-container"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Save Search — only show when a search term is active */}
          {search && (
            <div className="flex items-center justify-between rounded-xl border border-primary/20 bg-primary/5 px-4 py-2.5">
              <p className="text-xs text-on-surface-variant">
                {t("orgDash.saveSearchHint", { defaultValue: "Save this search to get notified of new matches" })}
              </p>
              <button
                type="button"
                onClick={() => { setSaveName(search); setShowSaveModal(true); }}
                className="ml-3 shrink-0 flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
              >
                <Bookmark className="size-3.5" aria-hidden="true" />
                {t("orgDash.saveSearch", { defaultValue: "Save search" })}
              </button>
            </div>
          )}

          {/* Saved searches list — compact pills */}
          {savedSearches && savedSearches.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {savedSearches.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center gap-1.5 rounded-full border border-border bg-surface-container px-3 py-1 text-xs text-on-surface-variant"
                >
                  <BookmarkCheck className="size-3 text-primary shrink-0" aria-hidden="true" />
                  <span className="max-w-[120px] truncate">{s.name}</span>
                  {s.notify_on_match
                    ? <Bell className="size-3 text-primary shrink-0" aria-label="Notifications on" />
                    : <BellOff className="size-3 shrink-0" aria-label="Notifications off" />
                  }
                  <button
                    type="button"
                    onClick={() => deleteSavedSearch.mutate(s.id)}
                    aria-label={`Delete saved search ${s.name}`}
                    className="ml-0.5 size-4 flex items-center justify-center rounded-full hover:bg-border transition-colors"
                  >
                    <X className="size-2.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Save Search Modal */}
          {showSaveModal && (
            <div
              role="dialog"
              aria-modal="true"
              aria-label={t("orgDash.saveSearchModal", { defaultValue: "Save search" })}
              className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm p-4"
              onClick={(e) => { if (e.target === e.currentTarget) setShowSaveModal(false); }}
            >
              <div className="w-full max-w-sm rounded-2xl border border-border bg-surface-container p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-on-surface">
                    {t("orgDash.saveSearchModal", { defaultValue: "Save this search" })}
                  </h2>
                  <button
                    type="button"
                    onClick={() => setShowSaveModal(false)}
                    aria-label="Close"
                    className="size-8 flex items-center justify-center rounded-full text-on-surface-variant hover:bg-border transition-colors"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                <div className="space-y-3">
                  <div>
                    <label htmlFor="save-name" className="text-xs text-on-surface-variant">
                      {t("orgDash.saveSearchName", { defaultValue: "Search name" })}
                    </label>
                    <input
                      id="save-name"
                      type="text"
                      value={saveName}
                      onChange={(e) => setSaveName(e.target.value)}
                      maxLength={100}
                      placeholder={t("orgDash.saveSearchPlaceholder", { defaultValue: "e.g. Senior communicators" })}
                      className="mt-1 w-full rounded-xl border border-outline-variant bg-background px-3 py-2 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                      // eslint-disable-next-line jsx-a11y/no-autofocus
                      autoFocus
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => setSaveNotify(!saveNotify)}
                    className={cn(
                      "w-full flex items-center gap-2 rounded-xl border px-3 py-2.5 text-xs transition-all",
                      saveNotify
                        ? "border-primary/40 bg-primary/5 text-primary"
                        : "border-border bg-transparent text-on-surface-variant"
                    )}
                  >
                    {saveNotify
                      ? <Bell className="size-3.5" aria-hidden="true" />
                      : <BellOff className="size-3.5" aria-hidden="true" />
                    }
                    {saveNotify
                      ? t("orgDash.notifyOn", { defaultValue: "Notify me when new talent matches" })
                      : t("orgDash.notifyOff", { defaultValue: "No notifications" })
                    }
                  </button>
                </div>

                <button
                  type="button"
                  onClick={handleSaveSearch}
                  disabled={!saveName.trim() || createSavedSearch.isPending || saveSuccess}
                  className={cn(
                    "w-full rounded-xl py-2.5 text-sm font-semibold transition-all",
                    saveSuccess
                      ? "bg-green-500/10 text-green-600 border border-green-500/30"
                      : "bg-primary text-on-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  {createSavedSearch.isPending
                    ? t("common.saving", { defaultValue: "Saving…" })
                    : saveSuccess
                    ? t("orgDash.saveSearchSaved", { defaultValue: "Saved!" })
                    : t("orgDash.saveSearchCta", { defaultValue: "Save search" })
                  }
                </button>

                {createSavedSearch.isError && (
                  <p className="text-xs text-destructive text-center">
                    {t("error.generic", { defaultValue: "Something went wrong. Please try again." })}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* List */}
          {volsLoading && (
            <div className="space-y-2" role="status" aria-live="polite">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 rounded-xl border border-border px-4 py-3">
                  <Skeleton className="size-9 rounded-full" />
                  <div className="flex-1 space-y-1.5">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                  <Skeleton className="h-5 w-16 rounded-full" />
                  <Skeleton className="h-4 w-10" />
                </div>
              ))}
            </div>
          )}

          {!volsLoading && filtered.length === 0 && (
            <div className="py-12 text-center space-y-2">
              <Users className="mx-auto size-10 text-on-surface-variant" aria-hidden="true" />
              <p className="text-sm text-on-surface-variant">
                {search
                  ? t("orgDash.noSearchResults", { defaultValue: "No professionals match your search" })
                  : t("orgDash.noProfessionals", { defaultValue: "No professionals assigned yet. Use the search to find and assign assessments." })}
              </p>
              {!search && (
                <button
                  onClick={() => router.push(`/${locale}/my-organization`)}
                  className="mt-2 text-sm text-primary underline-offset-2 hover:underline"
                >
                  {t("orgDash.goToOrg", { defaultValue: "Go to Organization Dashboard →" })}
                </button>
              )}
            </div>
          )}

          {!volsLoading && filtered.length > 0 && (
            <>
              <p className="text-xs text-on-surface-variant">
                {t("orgDash.showing", {
                  count: filtered.length,
                  defaultValue: `Showing ${filtered.length} professional${filtered.length !== 1 ? "s" : ""}`,
                })}
              </p>
              <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-2">
                {filtered.map((v) => (
                  <ProfessionalRow
                    key={v.professional_id}
                    row={v}
                    onClick={() => router.push(`/${locale}/u/${v.username}`)}
                  />
                ))}
              </motion.div>
            </>
          )}
        </div>

        {/* Pending assignments notice */}
        {!isLoading && stats && stats.total_assigned > stats.total_completed && (
          <motion.div variants={fadeUp} initial="hidden" animate="visible" className="rounded-xl border border-yellow-400/20 bg-yellow-400/5 p-4">
            <div className="flex items-start gap-3">
              <Clock className="size-4 text-yellow-400 mt-0.5 shrink-0" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium text-on-surface">
                  {stats.total_assigned - stats.total_completed}{" "}
                  {t("orgDash.pendingTitle", { defaultValue: "assessments pending" })}
                </p>
                <p className="mt-0.5 text-xs text-on-surface-variant">
                  {t("orgDash.pendingDesc", { defaultValue: "Professionals have been assigned — assessment in progress." })}
                </p>
              </div>
            </div>
          </motion.div>
        )}

      </div>
    </div>
  );
}
