"use client";

import { useRef, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Building2, Calendar, Users, Plus, ExternalLink, CheckCircle2, Loader2, Globe, UserCheck, Upload, Search, ArrowRight } from "lucide-react";
import { useMyOrganization, useCreateOrganization, useCollectiveAura } from "@/hooks/queries/use-organizations";
import { useMyEvents } from "@/hooks/queries/use-events";
import { cn } from "@/lib/utils/cn";

// ── Stagger ────────────────────────────────────────────────────────────────────

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: "easeOut" as const } },
};

// ── Stat card ──────────────────────────────────────────────────────────────────

function StatCard({ icon, value, label, highlight }: { icon: React.ReactNode; value: string | number; label: string; highlight?: boolean }) {
  return (
    <motion.div variants={item} className="rounded-xl border border-border bg-card p-4">
      <div className={cn("mb-2", highlight ? "text-primary" : "text-on-surface-variant")}>{icon}</div>
      <p className={cn("text-2xl font-bold tabular-nums", highlight ? "text-primary" : "text-on-surface")}>{value}</p>
      <p className="mt-0.5 text-xs text-on-surface-variant">{label}</p>
    </motion.div>
  );
}

// ── Status badge ───────────────────────────────────────────────────────────────

const STATUS_STYLES: Record<string, string> = {
  open:      "bg-green-500/15 text-green-400 border-green-400/30",
  draft:     "bg-yellow-500/15 text-yellow-400 border-yellow-400/30",
  closed:    "bg-slate-400/15 text-slate-300 border-slate-300/30",
  cancelled: "bg-error/15 text-error border-error/30",
  completed: "bg-primary/15 text-primary border-primary/30",
};

// ── Org create form ────────────────────────────────────────────────────────────

function CreateOrgForm({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const createOrg = useCreateOrganization();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await createOrg.mutateAsync({ name: name.trim(), description: description.trim() || undefined });
    onDone();
  }

  const inputClass = "w-full rounded-xl border border-outline-variant bg-surface-container px-3.5 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all";

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-border bg-surface-container-low p-5">
      <h3 className="font-semibold text-on-surface">{t("orgs.createTitle")}</h3>
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-on-surface-variant uppercase tracking-wide">{t("orgs.orgName")}</label>
        <input value={name} onChange={(e) => setName(e.target.value)} required minLength={2} maxLength={200} className={inputClass} placeholder={t("orgs.namePlaceholder", { defaultValue: "Your organization name" })} />
      </div>
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-on-surface-variant uppercase tracking-wide">{t("orgs.orgDescription")}</label>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} maxLength={2000} className={cn(inputClass, "resize-none")} placeholder={t("orgs.descPlaceholder")} />
      </div>
      {createOrg.isError && <p role="alert" className="text-xs text-error">{t("error.generic")}</p>}
      <div className="flex justify-end gap-3">
        <button type="button" onClick={onDone} className="rounded-xl px-4 py-2 text-sm text-on-surface-variant border border-outline-variant hover:bg-surface-container transition-colors">
          {t("common.cancel")}
        </button>
        <button type="submit" disabled={createOrg.isPending || !name.trim()} className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-on-primary hover:opacity-90 disabled:opacity-60 transition-opacity">
          {createOrg.isPending && <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />}
          {t("orgs.create")}
        </button>
      </div>
    </form>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function OrganizationsPage() {
  const { t } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const isMounted = useRef(true);
  useEffect(() => () => { isMounted.current = false; }, []);

  const [showCreateOrg, setShowCreateOrg] = useState(false);

  const { data: org, isLoading: orgLoading, error: orgError } = useMyOrganization();
  const { data: events, isLoading: eventsLoading } = useMyEvents();
  const { data: collective } = useCollectiveAura(org?.id);

  const hasOrg = !!org && !orgError;

  // Stats
  const totalEvents = events?.length ?? 0;
  const openEvents = events?.filter((e) => e.status === "open").length ?? 0;
  const completedEvents = events?.filter((e) => e.status === "completed").length ?? 0;

  if (orgLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="size-6 animate-spin text-primary" aria-label="Loading" role="status" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-2xl space-y-8">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, ease: "easeOut" as const }}>
          <h1 className="font-headline text-2xl font-bold text-on-surface">{t("orgs.dashboardTitle")}</h1>
          <p className="mt-1 text-sm text-on-surface-variant">{t("orgs.dashboardSubtitle")}</p>
        </motion.div>

        {/* No org yet */}
        {!hasOrg && !showCreateOrg && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, ease: "easeOut" as const }}
            className="rounded-2xl border border-dashed border-outline-variant bg-surface-container-low p-8 text-center"
          >
            <Building2 className="mx-auto size-10 text-on-surface-variant" aria-hidden="true" />
            <p className="mt-3 font-semibold text-on-surface">{t("orgs.noOrgTitle")}</p>
            <p className="mt-1 text-sm text-on-surface-variant">{t("orgs.noOrgSubtitle")}</p>
            <button
              onClick={() => setShowCreateOrg(true)}
              className="mt-5 flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-on-primary mx-auto hover:opacity-90 transition-opacity"
            >
              <Plus className="size-4" aria-hidden="true" /> {t("orgs.createFirst")}
            </button>
          </motion.div>
        )}

        {/* Inline create form */}
        {showCreateOrg && (
          <CreateOrgForm onDone={() => setShowCreateOrg(false)} />
        )}

        {/* Org exists */}
        {hasOrg && (
          <>
            {/* Org card */}
            <motion.div
              variants={item}
              initial="hidden"
              animate="visible"
              className="rounded-2xl border border-border bg-surface-container-low p-5"
            >
              <div className="flex items-start gap-4">
                <span className="size-12 rounded-xl bg-primary/15 flex items-center justify-center shrink-0">
                  <Building2 className="size-6 text-primary" aria-hidden="true" />
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h2 className="font-semibold text-on-surface truncate">{org.name}</h2>
                    {org.verified_at && (
                      <CheckCircle2 className="size-4 text-primary shrink-0" aria-label={t("orgs.verified")} />
                    )}
                  </div>
                  {org.description && (
                    <p className="mt-1 text-sm text-on-surface-variant line-clamp-2">{org.description}</p>
                  )}
                  <div className="mt-2 flex flex-wrap items-center gap-3">
                    {org.trust_score != null && (
                      <span className="text-xs text-on-surface-variant">
                        {t("orgs.trustScore")}: <span className="text-primary font-medium">{org.trust_score!.toFixed(1)}</span>
                      </span>
                    )}
                    {org.website && (
                      <a href={org.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-primary hover:underline">
                        <Globe className="size-3" aria-hidden="true" /> {t("orgs.website")}
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Stats row */}
            <motion.div variants={stagger} initial="hidden" animate="visible" className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <StatCard icon={<Calendar className="size-5" />} value={totalEvents} label={t("orgs.totalEvents")} />
              <StatCard icon={<Globe className="size-5" />} value={openEvents} label={t("orgs.openEvents")} highlight />
              <StatCard icon={<CheckCircle2 className="size-5" />} value={completedEvents} label={t("orgs.completedEvents")} />
            </motion.div>

            {/* Collective AURA Ladders widget */}
            {collective && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="rounded-xl border border-primary/20 bg-gradient-to-br from-primary/5 to-transparent p-4 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-on-surface">
                    {t("orgs.collectiveAuraTitle", { defaultValue: "Talent Pool AURA" })}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <Users className="size-3.5 text-primary" aria-hidden="true" />
                    <span className="text-xs text-muted-foreground">{collective.count} {t("orgs.professionals", { defaultValue: "professionals" })}</span>
                  </div>
                </div>
                {collective.avg_aura !== null ? (
                  <div className="flex items-end gap-2">
                    <span className="text-3xl font-bold tabular-nums text-primary">{collective.avg_aura.toFixed(1)}</span>
                    {collective.trend !== null && (
                      <span className={cn("text-sm font-medium mb-0.5", collective.trend >= 0 ? "text-green-500" : "text-red-400")}>
                        {collective.trend >= 0 ? "↑" : "↓"} {Math.abs(collective.trend).toFixed(1)}
                      </span>
                    )}
                    <span className="text-xs text-muted-foreground mb-0.5">{t("orgs.avgAuraLabel", { defaultValue: "avg AURA" })}</span>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    {t("orgs.collectiveAuraEmpty", { defaultValue: "Invite professionals to start building your talent pool score." })}
                  </p>
                )}
              </motion.div>
            )}

            {/* First-action onboarding banner — shown when org exists but no events yet */}
            {totalEvents === 0 && !eventsLoading && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.15 }}
                className="rounded-2xl border border-primary/25 bg-gradient-to-br from-primary/8 to-transparent p-5 space-y-3"
              >
                <div className="flex items-start gap-3">
                  <span className="size-9 rounded-xl bg-primary/15 flex items-center justify-center shrink-0">
                    <Search className="size-4 text-primary" aria-hidden="true" />
                  </span>
                  <div>
                    <p className="font-semibold text-on-surface text-sm">
                      {t("orgs.firstActionTitle", { defaultValue: "Start by finding talent" })}
                    </p>
                    <p className="text-xs text-on-surface-variant mt-0.5">
                      {t("orgs.firstActionDesc", { defaultValue: "Browse verified professionals with real AURA scores. Filter by skill, language, and score." })}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    onClick={() => router.push(`/${locale}/discover`)}
                    className="flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-on-primary hover:opacity-90 transition-opacity"
                  >
                    <Search className="size-3.5" aria-hidden="true" />
                    {t("orgs.browseVolunteers", { defaultValue: "Browse professionals" })}
                    <ArrowRight className="size-3.5" aria-hidden="true" />
                  </button>
                  <button
                    onClick={() => router.push(`/${locale}/my-organization/invite`)}
                    className="flex items-center gap-1.5 rounded-xl border border-border bg-surface-container px-4 py-2 text-xs font-semibold text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
                  >
                    <Upload className="size-3.5" aria-hidden="true" />
                    {t("orgs.inviteProfessionals", { defaultValue: "Invite by email" })}
                  </button>
                </div>
              </motion.div>
            )}

            {/* My events list */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-on-surface">{t("orgs.myEvents")}</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => router.push(`/${locale}/my-organization/invite`)}
                    className="flex items-center gap-1.5 rounded-xl border border-border bg-surface-container px-3.5 py-2 text-xs font-semibold text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
                  >
                    <Upload className="size-3.5" aria-hidden="true" /> {t("orgs.bulkInvite", { defaultValue: "Invite" })}
                  </button>
                  <button
                    onClick={() => router.push(`/${locale}/events/create`)}
                    className="flex items-center gap-1.5 rounded-xl bg-primary px-3.5 py-2 text-xs font-semibold text-on-primary hover:opacity-90 transition-opacity"
                  >
                    <Plus className="size-3.5" aria-hidden="true" /> {t("events.create")}
                  </button>
                </div>
              </div>

              {eventsLoading && (
                <div className="flex justify-center py-6">
                  <Loader2 className="size-5 animate-spin text-primary" role="status" aria-label="Loading" />
                </div>
              )}

              {!eventsLoading && (!events || events.length === 0) && (
                <div className="rounded-2xl border border-dashed border-outline-variant bg-surface-container-low p-6 text-center">
                  <Calendar className="mx-auto size-8 text-on-surface-variant" aria-hidden="true" />
                  <p className="mt-2 text-sm text-on-surface-variant">{t("orgs.noEventsYet")}</p>
                  <button
                    onClick={() => router.push(`/${locale}/events/create`)}
                    className="mt-3 text-sm text-primary underline-offset-2 hover:underline"
                  >
                    {t("events.createFirst")}
                  </button>
                </div>
              )}

              {!eventsLoading && events && events.length > 0 && (
                <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-2">
                  {events.map((ev) => (
                    <motion.div
                      key={ev.id}
                      variants={item}
                      className="flex items-center gap-3 rounded-xl border border-border bg-surface-container-low p-4 cursor-pointer hover:bg-surface-container transition-colors"
                      onClick={() => router.push(`/${locale}/events/${ev.id}`)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === "Enter" && router.push(`/${locale}/events/${ev.id}`)}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-on-surface truncate">{ev.title_en}</p>
                        <p className="text-xs text-on-surface-variant mt-0.5">
                          {new Date(ev.start_date).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}
                          {ev.location && ` · ${ev.location}`}
                        </p>
                      </div>
                      <span className={cn("shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border", STATUS_STYLES[ev.status] ?? STATUS_STYLES.draft)}>
                        {t(`events.status.${ev.status}`, { defaultValue: ev.status })}
                      </span>
                      <button
                        type="button"
                        aria-label={t("events.viewAttendees", { defaultValue: "View attendees" })}
                        className="shrink-0 flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors px-2 py-1 rounded-lg hover:bg-primary/10"
                        onClick={(e) => { e.stopPropagation(); router.push(`/${locale}/events/${ev.id}/attendees`); }}
                      >
                        <UserCheck className="size-3.5" aria-hidden="true" />
                        {t("events.attendees", { defaultValue: "Attendees" })}
                      </button>
                      <ExternalLink className="size-3.5 text-on-surface-variant shrink-0" aria-hidden="true" />
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
