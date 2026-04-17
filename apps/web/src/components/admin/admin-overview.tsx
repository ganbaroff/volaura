"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Users,
  Building2,
  ClipboardList,
  Star,
  Gavel,
  Activity,
  TrendingUp,
  AlertTriangle,
  Wallet,
  Zap,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import {
  useAdminStats,
  useAdminOverview,
  useAdminLiveEvents,
  type AdminActivationFunnel,
  type AdminActivityEvent,
} from "@/hooks/queries/use-admin";
import { cn } from "@/lib/utils/cn";

// ── Ecosystem-design-gate compliance ─────────────────────────────────────────
// • No red anywhere. errors use purple #D4B4FF, warnings amber #E9C400.
// • No spinners — Skeletons that match the shape of the final content.
// • No count-up animations on personal scores (anti-pattern #6).
// • Focus-visible ring on every interactive element (WCAG 2.4.7 AA).
// • Respects prefers-reduced-motion via motion-reduce utilities.

type HealthTone = "ok" | "warn" | "crit" | "unknown";

const TONE_STYLES: Record<HealthTone, { dot: string; text: string; ring: string; label: string }> = {
  ok: {
    dot: "bg-emerald-400",
    text: "text-emerald-400",
    ring: "ring-emerald-400/20",
    label: "healthy",
  },
  warn: {
    // amber — never red
    dot: "bg-amber-400",
    text: "text-amber-400",
    ring: "ring-amber-400/20",
    label: "watch",
  },
  crit: {
    // purple stand-in for red, per ecosystem Foundation Law #1
    dot: "bg-[#D4B4FF]",
    text: "text-[#D4B4FF]",
    ring: "ring-[#D4B4FF]/30",
    label: "critical",
  },
  unknown: {
    dot: "bg-on-surface-variant/40",
    text: "text-on-surface-variant",
    ring: "ring-border",
    label: "—",
  },
};

const PRODUCT_ACCENT: Record<string, { hex: string; bg: string; border: string; text: string }> = {
  volaura:   { hex: "#7C5CFC", bg: "bg-[#7C5CFC]/8",  border: "border-[#7C5CFC]/30", text: "text-[#B4A0FF]" },
  mindshift: { hex: "#3B82F6", bg: "bg-[#3B82F6]/8",  border: "border-[#3B82F6]/30", text: "text-[#7BA8F8]" },
  lifesim:   { hex: "#F59E0B", bg: "bg-[#F59E0B]/8",  border: "border-[#F59E0B]/30", text: "text-[#FFC86B]" },
  brandedby: { hex: "#EC4899", bg: "bg-[#EC4899]/8",  border: "border-[#EC4899]/30", text: "text-[#FF8BC4]" },
  zeus:      { hex: "#10B981", bg: "bg-[#10B981]/8",  border: "border-[#10B981]/30", text: "text-[#34D9A6]" },
};

function productChip(product: string) {
  const accent = PRODUCT_ACCENT[product] ?? PRODUCT_ACCENT.zeus;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        accent.bg,
        accent.border,
        accent.text,
      )}
    >
      {product}
    </span>
  );
}

function pct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

function fixed(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(digits);
}

// ── Threshold logic ──────────────────────────────────────────────────────────
// Pre-PMF benchmarks. See docs/research/admin-metrics-2026-04-17.md for sources.
function toneActivation(v: number): HealthTone {
  if (v >= 0.25) return "ok";
  if (v >= 0.10) return "warn";
  return "crit";
}
function toneRetention(v: number | null): HealthTone {
  if (v === null) return "unknown";
  if (v >= 0.30) return "ok";
  if (v >= 0.15) return "warn";
  return "crit";
}
function toneStickiness(v: number): HealthTone {
  if (v >= 0.5) return "ok";
  if (v >= 0.2) return "warn";
  return "crit";
}
function toneErrors(v: number): HealthTone {
  if (v === 0) return "ok";
  if (v <= 10) return "warn";
  return "crit";
}
function toneRunway(v: number | null): HealthTone {
  if (v === null) return "unknown";
  if (v >= 12) return "ok";
  if (v >= 6) return "warn";
  return "crit";
}

// ── Scorecard card ───────────────────────────────────────────────────────────
function ScoreCard({
  icon,
  label,
  value,
  tone,
  hint,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: HealthTone;
  hint?: string;
}) {
  const s = TONE_STYLES[tone];
  return (
    <Card
      className={cn(
        "relative overflow-hidden border-border bg-card",
        "ring-1 ring-inset transition-colors motion-reduce:transition-none",
        s.ring,
      )}
    >
      <CardContent className="p-5">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-on-surface-variant">{icon}</div>
          <div className="flex items-center gap-1.5">
            <span className={cn("size-1.5 rounded-full", s.dot)} aria-hidden />
            <span className={cn("text-[10px] font-semibold uppercase tracking-wider", s.text)}>
              {s.label}
            </span>
          </div>
        </div>
        <p className="text-3xl font-bold tabular-nums text-on-surface">{value}</p>
        <p className="mt-1 text-sm text-on-surface-variant">{label}</p>
        {hint ? (
          <p className="mt-2 text-[11px] text-on-surface-variant/80">{hint}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function ScoreCardSkeleton() {
  return (
    <Card className="border-border bg-card">
      <CardContent className="space-y-3 p-5">
        <div className="flex items-center justify-between">
          <Skeleton className="size-5 rounded" />
          <Skeleton className="h-3 w-14 rounded" />
        </div>
        <Skeleton className="h-8 w-20 rounded" />
        <Skeleton className="h-4 w-28 rounded" />
      </CardContent>
    </Card>
  );
}

// ── Funnel + presence widgets ────────────────────────────────────────────────
function FunnelRow({ funnel }: { funnel: AdminActivationFunnel }) {
  const rate = funnel.activation_rate;
  const tone = toneActivation(rate);
  const s = TONE_STYLES[tone];
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-border bg-surface-container/40 p-3">
      <div className="flex items-center gap-3">
        {productChip(funnel.product)}
        <div className="text-sm text-on-surface-variant">
          <span className="font-semibold tabular-nums text-on-surface">{funnel.activated_24h}</span>
          <span className="mx-1">/</span>
          <span className="tabular-nums">{funnel.signups_24h}</span>
          <span className="ml-2 text-xs">activated / signups · 24h</span>
        </div>
      </div>
      <span className={cn("text-sm font-semibold tabular-nums", s.text)}>{pct(rate)}</span>
    </div>
  );
}

function PresenceStrip({
  volaura_only,
  mindshift_only,
  both_products,
  total_users,
}: {
  volaura_only: number;
  mindshift_only: number;
  both_products: number;
  total_users: number;
}) {
  const seg = (n: number) => (total_users > 0 ? (n / total_users) * 100 : 0);
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-on-surface-variant">
        <span>Cross-product presence</span>
        <span className="tabular-nums">{total_users} total</span>
      </div>
      <div
        className="flex h-2 w-full overflow-hidden rounded-full bg-surface-container"
        role="img"
        aria-label={`VOLAURA only ${volaura_only}, MindShift only ${mindshift_only}, both ${both_products}, total ${total_users}`}
      >
        <div className="h-full bg-[#7C5CFC]/80" style={{ width: `${seg(volaura_only)}%` }} />
        <div className="h-full bg-[#3B82F6]/80" style={{ width: `${seg(mindshift_only)}%` }} />
        <div className="h-full bg-[#10B981]/80" style={{ width: `${seg(both_products)}%` }} />
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-on-surface-variant">
        <span className="inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-[#7C5CFC]" aria-hidden /> VOLAURA-only
          <span className="tabular-nums text-on-surface">{volaura_only}</span>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-[#3B82F6]" aria-hidden /> MindShift-only
          <span className="tabular-nums text-on-surface">{mindshift_only}</span>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-[#10B981]" aria-hidden /> Both
          <span className="tabular-nums text-on-surface">{both_products}</span>
        </span>
      </div>
    </div>
  );
}

// ── Live feed ────────────────────────────────────────────────────────────────
function truncate(s: string | null, n = 120): string {
  if (!s) return "";
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}

function LiveFeedRow({ ev }: { ev: AdminActivityEvent }) {
  const at = new Date(ev.created_at);
  const rel = relativeTime(at);
  return (
    <li className="flex items-start gap-3 rounded-md border border-border/60 bg-surface-container/30 px-3 py-2 text-sm">
      <div className="shrink-0 pt-0.5">{productChip(ev.product)}</div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-on-surface">{ev.event_type}</span>
          <span className="text-xs text-on-surface-variant">· {ev.user_id_prefix}</span>
        </div>
        {ev.payload_summary ? (
          <p className="mt-0.5 truncate text-xs text-on-surface-variant">
            {truncate(ev.payload_summary)}
          </p>
        ) : null}
      </div>
      <time
        className="shrink-0 text-xs tabular-nums text-on-surface-variant"
        dateTime={ev.created_at}
        title={at.toISOString()}
      >
        {rel}
      </time>
    </li>
  );
}

function relativeTime(d: Date): string {
  const diff = Math.max(0, Date.now() - d.getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

// ── Legacy StatCard (kept for ops links) ─────────────────────────────────────
function StatCard({
  icon,
  label,
  value,
  highlight,
  href,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  highlight?: boolean;
  href?: string;
}) {
  const body = (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-5 transition-colors motion-reduce:transition-none",
        href && "hover:bg-surface-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary cursor-pointer",
      )}
    >
      <div className={cn("mb-2", highlight ? "text-primary" : "text-on-surface-variant")}>{icon}</div>
      <p
        className={cn(
          "text-3xl font-bold tabular-nums",
          highlight ? "text-primary" : "text-on-surface",
        )}
      >
        {value}
      </p>
      <p className="mt-1 text-sm text-on-surface-variant">{label}</p>
    </div>
  );
  return href ? <Link href={href}>{body}</Link> : body;
}

// ── Main component ───────────────────────────────────────────────────────────
export function AdminOverview() {
  const { locale } = useParams<{ locale: string }>();
  const { data: overview, isLoading: overviewLoading, isError: overviewError } = useAdminOverview();
  const { data: stats, isLoading: statsLoading } = useAdminStats();
  const liveQuery = useAdminLiveEvents(50);
  const events = liveQuery.data as AdminActivityEvent[] | undefined;
  const eventsLoading = liveQuery.isLoading;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold font-headline text-on-surface">Platform Overview</h1>
        <p className="mt-1 text-sm text-on-surface-variant">
          Activation-first scorecard · pre-PMF stage · refreshes every 60 seconds
        </p>
      </div>

      {/* Tier 1 scorecard */}
      <section aria-labelledby="scorecard-h" className="space-y-3">
        <h2 id="scorecard-h" className="text-lg font-semibold font-headline text-on-surface">
          Health scorecard
        </h2>

        {overviewError && !overview ? (
          <Card className="border-[#D4B4FF]/30 bg-[#D4B4FF]/5">
            <CardContent className="flex items-start gap-3 p-4 text-sm">
              <AlertTriangle className="mt-0.5 size-4 text-[#D4B4FF]" aria-hidden />
              <div>
                <p className="font-medium text-on-surface">Overview endpoint unreachable</p>
                <p className="mt-1 text-on-surface-variant">
                  Legacy stats shown below. Check <code className="rounded bg-surface-container px-1">/api/admin/stats/overview</code>.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : null}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {overviewLoading || !overview ? (
            Array.from({ length: 5 }).map((_, i) => <ScoreCardSkeleton key={i} />)
          ) : (
            <>
              <ScoreCard
                icon={<Zap className="size-5" />}
                label="Activation rate · 24h"
                value={pct(overview.activation_rate_24h)}
                tone={toneActivation(overview.activation_rate_24h)}
                hint="signup → first key action"
              />
              <ScoreCard
                icon={<TrendingUp className="size-5" />}
                label="W4 retention"
                value={pct(overview.w4_retention)}
                tone={toneRetention(overview.w4_retention)}
                hint="week-0 cohort still active at week-4"
              />
              <ScoreCard
                icon={<Activity className="size-5" />}
                label="DAU / WAU"
                value={fixed(overview.dau_wau_ratio, 2)}
                tone={toneStickiness(overview.dau_wau_ratio)}
                hint="stickiness · 1.0 = use every day"
              />
              <ScoreCard
                icon={<AlertTriangle className="size-5" />}
                label="Errors · 24h"
                value={String(overview.errors_24h)}
                tone={toneErrors(overview.errors_24h)}
                hint="5xx + failed assessments + orphan events"
              />
              <ScoreCard
                icon={<Wallet className="size-5" />}
                label="Runway"
                value={overview.runway_months === null ? "—" : `${fixed(overview.runway_months, 1)} mo`}
                tone={toneRunway(overview.runway_months)}
                hint="set via PLATFORM_RUNWAY_MONTHS"
              />
            </>
          )}
        </div>
      </section>

      {/* Tier 2 cross-product presence + funnels */}
      <section aria-labelledby="presence-h" className="space-y-3">
        <h2 id="presence-h" className="text-lg font-semibold font-headline text-on-surface">
          Cross-product presence
        </h2>
        <Card className="border-border bg-card">
          <CardContent className="space-y-4 p-5">
            {overviewLoading || !overview ? (
              <div className="space-y-3">
                <Skeleton className="h-2 w-full rounded-full" />
                <Skeleton className="h-4 w-64 rounded" />
              </div>
            ) : (
              <PresenceStrip
                volaura_only={overview.presence.volaura_only}
                mindshift_only={overview.presence.mindshift_only}
                both_products={overview.presence.both_products}
                total_users={overview.presence.total_users}
              />
            )}

            <div className="space-y-2 pt-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                24h activation funnels
              </p>
              {overviewLoading || !overview ? (
                <div className="space-y-2">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full rounded-lg" />
                  ))}
                </div>
              ) : overview.funnels.length === 0 ? (
                <p className="text-sm text-on-surface-variant">No signups in the last 24 hours.</p>
              ) : (
                overview.funnels.map((f) => <FunnelRow key={f.product} funnel={f} />)
              )}
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Live feed */}
      <section aria-labelledby="live-h" className="space-y-3">
        <div className="flex items-end justify-between">
          <h2 id="live-h" className="text-lg font-semibold font-headline text-on-surface">
            Live activity
          </h2>
          <span className="text-xs text-on-surface-variant">polling every 15s</span>
        </div>
        <Card className="border-border bg-card">
          <CardContent className="p-3">
            {eventsLoading && (!events || events.length === 0) ? (
              <ul className="space-y-2" aria-label="Loading live events">
                {Array.from({ length: 6 }).map((_, i) => (
                  <li key={i}>
                    <Skeleton className="h-12 w-full rounded-md" />
                  </li>
                ))}
              </ul>
            ) : !events || events.length === 0 ? (
              <p className="px-2 py-6 text-center text-sm text-on-surface-variant">
                No events yet. The feed will populate as users cross products.
              </p>
            ) : (
              <ul className="max-h-[520px] space-y-2 overflow-y-auto pr-1">
                {events.map((ev) => (
                  <LiveFeedRow key={ev.id} ev={ev} />
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Legacy ops links (pending approvals, grievances, assessments) */}
      <section aria-labelledby="ops-h" className="space-y-3">
        <h2 id="ops-h" className="text-lg font-semibold font-headline text-on-surface">
          Operational queues
        </h2>
        {statsLoading && (
          <div
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
            role="status"
            aria-label="Loading queues"
          >
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-3 rounded-xl border border-border bg-card p-5">
                <Skeleton className="size-5 rounded" />
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-4 w-24" />
              </div>
            ))}
          </div>
        )}
        {stats && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard
              icon={<Users className="size-5" />}
              label="Total Users"
              value={stats.total_users}
            />
            <StatCard
              icon={<Building2 className="size-5" />}
              label="Active Organizations"
              value={stats.total_organizations}
            />
            <StatCard
              icon={<Building2 className="size-5" />}
              label="Pending Org Approvals"
              value={stats.pending_org_approvals}
              highlight={stats.pending_org_approvals > 0}
              href={`/${locale}/admin/organizations`}
            />
            <StatCard
              icon={<ClipboardList className="size-5" />}
              label="Assessments Today"
              value={stats.assessments_today}
            />
            <StatCard
              icon={<Star className="size-5" />}
              label="Avg AURA Score"
              value={stats.avg_aura_score?.toFixed(1) ?? "—"}
              highlight
            />
            <StatCard
              icon={<Gavel className="size-5" />}
              label="Pending Grievances"
              value={stats.pending_grievances}
              highlight={stats.pending_grievances > 0}
              href={`/${locale}/admin/grievances`}
            />
          </div>
        )}
      </section>
    </div>
  );
}
