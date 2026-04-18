"use client";

// Atlas admin — obligations dashboard.
// Spec: memory/atlas/OBLIGATION-SYSTEM-SPEC-2026-04-18.md §Admin-UI.
// Reads public.atlas_obligations + public.atlas_proofs directly via Supabase client
// (admin-only route, layout already gates access).
//
// Foundation Law 1 (Ecosystem Design Gate anti-pattern #1): NO RED.
// Countdown colors: emerald (>30d), amber (7-30d), orange (1-7d), purple (past-due / blocker).

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { ScrollText, CheckCircle2, Clock, AlertTriangle, FileText } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";

// ── Types ────────────────────────────────────────────────────────────────────

type ObligationStatus = "open" | "in_progress" | "completed" | "deferred" | "cancelled";

interface Obligation {
  id: string;
  title: string;
  description: string | null;
  category: string;
  deadline: string | null;
  trigger_event: string | null;
  consequence_if_missed: string;
  owner: string;
  status: ObligationStatus;
  proof_required: string[];
  nag_schedule: string;
  created_at: string;
  completed_at: string | null;
  source: string | null;
}

interface Proof {
  id: string;
  obligation_id: string;
  proof_type: string;
  text_content: string | null;
  artifact_url: string | null;
  submitted_by: string;
  submitted_via: string;
  submitted_at: string;
  verified: boolean;
}

interface ProofWithTitle extends Proof {
  obligation_title: string;
}

// ── Queries ──────────────────────────────────────────────────────────────────

function useObligations() {
  return useQuery({
    queryKey: ["admin", "obligations"],
    queryFn: async (): Promise<Obligation[]> => {
      const supabase = createClient();
      const { data, error } = await supabase
        .from("atlas_obligations")
        .select("*")
        .order("deadline", { ascending: true, nullsFirst: false });
      if (error) throw error;
      return (data ?? []) as Obligation[];
    },
    staleTime: 60_000,
  });
}

function useRecentProofs() {
  return useQuery({
    queryKey: ["admin", "obligations", "recent-proofs"],
    queryFn: async (): Promise<ProofWithTitle[]> => {
      const supabase = createClient();
      const { data, error } = await supabase
        .from("atlas_proofs")
        .select("*, atlas_obligations!inner(title)")
        .order("submitted_at", { ascending: false })
        .limit(20);
      if (error) throw error;
      type Joined = Proof & { atlas_obligations: { title: string } };
      return ((data ?? []) as Joined[]).map((r) => ({
        ...r,
        obligation_title: r.atlas_obligations?.title ?? "—",
      }));
    },
    staleTime: 60_000,
  });
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function daysUntil(deadline: string | null): number | null {
  if (!deadline) return null;
  const target = new Date(deadline).getTime();
  const now = Date.now();
  return Math.floor((target - now) / (1000 * 60 * 60 * 24));
}

function countdownTone(days: number | null): {
  label: string;
  tone: string;
} {
  if (days === null) return { label: "—", tone: "bg-muted text-on-surface-variant border-border" };
  if (days < 0)
    return {
      label: `${Math.abs(days)}d overdue`,
      // purple = errors / past-due (Foundation Law 1: NEVER red)
      tone: "bg-primary/15 text-primary border-primary/30",
    };
  if (days <= 7)
    return {
      label: `${days}d left`,
      tone: "bg-orange-500/15 text-orange-300 border-orange-400/30",
    };
  if (days <= 30)
    return {
      label: `${days}d left`,
      tone: "bg-amber-500/15 text-amber-300 border-amber-400/30",
    };
  return {
    label: `${days}d left`,
    tone: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  };
}

const STATUS_BADGE: Record<ObligationStatus, string> = {
  open: "bg-amber-500/15 text-amber-300 border-amber-400/30",
  in_progress: "bg-primary/15 text-primary border-primary/30",
  completed: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  deferred: "bg-muted text-on-surface-variant border-border",
  cancelled: "bg-muted text-on-surface-variant border-border",
};

const STATUS_LABEL: Record<ObligationStatus, string> = {
  open: "Open",
  in_progress: "In progress",
  completed: "Completed",
  deferred: "Deferred",
  cancelled: "Cancelled",
};

// ── Components ───────────────────────────────────────────────────────────────

function Scorecard({ obligations }: { obligations: Obligation[] }) {
  const now = Date.now();
  const openCount = obligations.filter((o) => o.status === "open" || o.status === "in_progress").length;
  const atRisk = obligations.filter((o) => {
    if (o.status !== "open" && o.status !== "in_progress") return false;
    const d = daysUntil(o.deadline);
    return d !== null && d >= 0 && d <= 14;
  }).length;
  const overdue = obligations.filter((o) => {
    if (o.status !== "open" && o.status !== "in_progress") return false;
    const d = daysUntil(o.deadline);
    return d !== null && d < 0;
  }).length;
  const completedRecent = obligations.filter((o) => {
    if (o.status !== "completed" || !o.completed_at) return false;
    const ms = new Date(o.completed_at).getTime();
    return now - ms <= 30 * 24 * 60 * 60 * 1000;
  }).length;

  const cards = [
    { label: "Open", value: openCount, icon: ScrollText, tone: "text-on-surface" },
    { label: "At risk (≤14d)", value: atRisk, icon: Clock, tone: "text-amber-300" },
    { label: "Past-due", value: overdue, icon: AlertTriangle, tone: "text-primary" },
    { label: "Completed 30d", value: completedRecent, icon: CheckCircle2, tone: "text-emerald-300" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div key={c.label} className="rounded-xl border border-border bg-surface-container-low p-4">
            <div className="flex items-center gap-2 text-xs font-medium text-on-surface-variant uppercase tracking-wider">
              <Icon className="size-3.5" aria-hidden="true" />
              {c.label}
            </div>
            <div className={`text-2xl font-bold font-headline mt-1.5 ${c.tone}`}>{c.value}</div>
          </div>
        );
      })}
    </div>
  );
}

function ObligationRow({ o }: { o: Obligation }) {
  const days = daysUntil(o.deadline);
  const countdown = countdownTone(days);
  const deadlineLabel = o.deadline
    ? new Date(o.deadline).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : o.trigger_event
      ? "trigger-based"
      : "—";

  return (
    <tr className="border-b border-border/40 last:border-b-0 align-top">
      <td className="py-3 pr-3">
        <div className="text-sm font-semibold text-on-surface">{o.title}</div>
        <div className="text-xs text-on-surface-variant mt-0.5 line-clamp-2">
          {o.consequence_if_missed}
        </div>
      </td>
      <td className="py-3 pr-3">
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium border ${STATUS_BADGE[o.status]}`}
        >
          {STATUS_LABEL[o.status]}
        </span>
      </td>
      <td className="py-3 pr-3 text-xs text-on-surface-variant whitespace-nowrap">
        {o.category}
      </td>
      <td className="py-3 pr-3 text-xs text-on-surface whitespace-nowrap">{deadlineLabel}</td>
      <td className="py-3 pr-0">
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium border whitespace-nowrap ${countdown.tone}`}
        >
          {countdown.label}
        </span>
      </td>
    </tr>
  );
}

function ObligationsTable({ obligations }: { obligations: Obligation[] }) {
  const active = useMemo(
    () =>
      obligations.filter((o) => o.status === "open" || o.status === "in_progress"),
    [obligations],
  );
  if (active.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-surface-container-low p-8 text-center">
        <CheckCircle2 className="size-8 text-emerald-300 mx-auto mb-2" aria-hidden="true" />
        <p className="text-sm font-semibold text-on-surface">No open obligations.</p>
        <p className="text-xs text-on-surface-variant mt-1">
          Every tracked commitment is closed or deferred.
        </p>
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-border bg-surface-container-low overflow-hidden">
      <table className="w-full text-left">
        <thead className="bg-surface-container">
          <tr>
            <th className="py-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
              Obligation
            </th>
            <th className="py-2 pr-3 text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
              Status
            </th>
            <th className="py-2 pr-3 text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
              Category
            </th>
            <th className="py-2 pr-3 text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
              Deadline
            </th>
            <th className="py-2 pr-3 text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
              Countdown
            </th>
          </tr>
        </thead>
        <tbody className="px-3">
          {active.map((o) => (
            <ObligationRow key={o.id} o={o} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProofsFeed({ proofs }: { proofs: ProofWithTitle[] }) {
  if (proofs.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-surface-container-low p-6 text-center">
        <FileText className="size-6 text-on-surface-variant mx-auto mb-2" aria-hidden="true" />
        <p className="text-sm text-on-surface-variant">No proofs attached yet.</p>
      </div>
    );
  }
  return (
    <ol className="space-y-2">
      {proofs.map((p) => (
        <li
          key={p.id}
          className="rounded-lg border border-border bg-surface-container-low px-3 py-2.5 flex items-start gap-3"
        >
          <FileText className="size-4 text-on-surface-variant mt-0.5 shrink-0" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold text-on-surface truncate">
                {p.obligation_title}
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                {p.proof_type}
              </span>
              {p.verified && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-400/30 font-medium">
                  verified
                </span>
              )}
            </div>
            {p.text_content && (
              <p className="text-xs text-on-surface-variant mt-1 line-clamp-2">
                {p.text_content}
              </p>
            )}
            <p className="text-[10px] text-on-surface-variant mt-1">
              {new Date(p.submitted_at).toLocaleString()} · via {p.submitted_via}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function AdminObligationsPage() {
  const { data: obligations, isLoading, error } = useObligations();
  const { data: proofs, isLoading: proofsLoading } = useRecentProofs();

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold font-headline text-on-surface flex items-center gap-2">
          <ScrollText className="size-6 text-primary" aria-hidden="true" />
          Obligations
        </h1>
        <p className="text-sm text-on-surface-variant mt-1">
          What Atlas is holding for CEO. Nag cadence escalates until proof is attached. Source of
          truth: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">public.atlas_obligations</code>.
        </p>
      </div>

      {isLoading && (
        <div className="space-y-4" role="status" aria-label="Loading obligations">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-[72px] rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-[260px] rounded-xl" />
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-primary/30 bg-primary/5 p-4 text-sm text-on-surface">
          Failed to load obligations: {error.message}
        </div>
      )}

      {!isLoading && obligations && (
        <>
          <Scorecard obligations={obligations} />
          <section className="space-y-2">
            <h2 className="text-lg font-semibold font-headline text-on-surface">Active</h2>
            <ObligationsTable obligations={obligations} />
          </section>
          <section className="space-y-2">
            <h2 className="text-lg font-semibold font-headline text-on-surface">
              Recent proofs
            </h2>
            {proofsLoading ? (
              <Skeleton className="h-[180px] rounded-xl" />
            ) : (
              <ProofsFeed proofs={proofs ?? []} />
            )}
          </section>
        </>
      )}
    </div>
  );
}
