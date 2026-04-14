"use client";

import { useState } from "react";
import { Loader2, ShieldCheck, ChevronRight, ChevronDown, Inbox } from "lucide-react";
import {
  useAdminPendingGrievances,
  useTransitionGrievance,
  type GrievanceAdmin,
} from "@/hooks/queries/use-grievance";

const STATUS_LABEL: Record<string, string> = {
  pending: "Pending",
  reviewing: "In review",
  resolved: "Resolved",
  rejected: "Closed",
};

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-amber-500/15 text-amber-300 border-amber-400/30",
  reviewing: "bg-primary/15 text-primary border-primary/30",
  resolved: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  rejected: "bg-muted text-on-surface-variant border-border",
};

function GrievanceCard({ g }: { g: GrievanceAdmin }) {
  const [expanded, setExpanded] = useState(false);
  const [status, setStatus] = useState<"reviewing" | "resolved" | "rejected">("reviewing");
  const [resolution, setResolution] = useState("");
  const [adminNotes, setAdminNotes] = useState(g.admin_notes ?? "");

  const { mutate: transition, isPending, error } = useTransitionGrievance();

  const needsResolution = status === "resolved" || status === "rejected";
  const canSubmit = !isPending && (!needsResolution || resolution.trim().length >= 10);

  const onSubmit = () => {
    if (!canSubmit) return;
    transition(
      {
        grievance_id: g.id,
        status,
        resolution: needsResolution ? resolution.trim() : undefined,
        admin_notes: adminNotes.trim() || undefined,
      } as Parameters<typeof transition>[0],
      {
        onSuccess: () => {
          setExpanded(false);
          setResolution("");
        },
      }
    );
  };

  return (
    <article className="rounded-xl border border-border bg-surface-container-low overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-surface-container transition-colors"
      >
        {expanded ? (
          <ChevronDown className="size-4 mt-1 text-on-surface-variant shrink-0" aria-hidden="true" />
        ) : (
          <ChevronRight className="size-4 mt-1 text-on-surface-variant shrink-0" aria-hidden="true" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium border ${STATUS_BADGE[g.status] ?? STATUS_BADGE.pending}`}
            >
              {STATUS_LABEL[g.status] ?? g.status}
            </span>
            {g.related_competency_slug && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-on-surface-variant">
                {g.related_competency_slug}
              </span>
            )}
            <span className="text-xs text-on-surface-variant ml-auto">
              user:{g.user_id.slice(0, 8)} · {new Date(g.created_at).toLocaleString()}
            </span>
          </div>
          <p className="text-sm font-semibold text-on-surface mt-1.5 truncate">{g.subject}</p>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border px-4 py-4 space-y-4">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Full complaint</p>
            <p className="text-sm text-on-surface whitespace-pre-line">{g.description}</p>
          </div>

          {g.related_session_id && (
            <div className="text-xs text-on-surface-variant">
              Session: <code className="bg-muted px-1.5 py-0.5 rounded">{g.related_session_id}</code>
            </div>
          )}

          <div className="pt-3 border-t border-border/40 space-y-3">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider">
                Transition to
              </label>
              <div className="flex gap-2">
                {(["reviewing", "resolved", "rejected"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setStatus(s)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      status === s
                        ? STATUS_BADGE[s]
                        : "border-border text-on-surface-variant hover:bg-surface-container"
                    }`}
                  >
                    {STATUS_LABEL[s]}
                  </button>
                ))}
              </div>
            </div>

            {needsResolution && (
              <div className="space-y-1.5">
                <label htmlFor={`resolution-${g.id}`} className="block text-xs font-semibold text-on-surface uppercase tracking-wider">
                  Resolution (required, visible to user)
                </label>
                <textarea
                  id={`resolution-${g.id}`}
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  rows={3}
                  maxLength={5000}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder="Explain the decision. This is what the user will see."
                />
                <p className="text-xs text-on-surface-variant">{resolution.length}/5000 (min 10)</p>
              </div>
            )}

            <div className="space-y-1.5">
              <label htmlFor={`notes-${g.id}`} className="block text-xs font-semibold text-on-surface uppercase tracking-wider">
                Admin notes (internal, not shown to user)
              </label>
              <textarea
                id={`notes-${g.id}`}
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                rows={2}
                maxLength={5000}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Context, links, colleague handoff"
              />
            </div>

            {error && (
              <div className="rounded-lg border border-primary/30 bg-primary/5 p-2.5 text-xs text-on-surface">
                {error.detail || "Could not transition this grievance."}
              </div>
            )}

            <button
              type="button"
              onClick={onSubmit}
              disabled={!canSubmit}
              className="inline-flex items-center gap-2 rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
            >
              {isPending && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
              {isPending ? "Saving..." : `Set to ${STATUS_LABEL[status]}`}
            </button>
          </div>
        </div>
      )}
    </article>
  );
}

export default function AdminGrievancesPage() {
  const { data: grievances, isLoading, refetch } = useAdminPendingGrievances();

  return (
    <div className="space-y-5 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface flex items-center gap-2">
            <ShieldCheck className="size-6 text-primary" aria-hidden="true" />
            Grievances
          </h1>
          <p className="text-sm text-on-surface-variant mt-1">
            ISO 10667-2 §7 queue — oldest first. Resolution text goes back to the user; admin notes stay internal.
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="text-sm text-on-surface-variant hover:text-on-surface transition-colors"
        >
          Refresh
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-on-surface-variant">
          <Loader2 className="size-6 animate-spin" aria-hidden="true" />
        </div>
      )}

      {!isLoading && (!grievances || grievances.length === 0) && (
        <div className="flex flex-col items-center justify-center py-16 gap-3 text-center rounded-xl border border-border bg-surface-container-low">
          <Inbox className="size-8 text-on-surface-variant" aria-hidden="true" />
          <p className="text-sm font-semibold text-on-surface">Queue is empty.</p>
          <p className="text-xs text-on-surface-variant max-w-sm">
            No pending or in-review grievances right now. New filings appear here automatically.
          </p>
        </div>
      )}

      {!isLoading && grievances && grievances.length > 0 && (
        <div className="space-y-3">
          {grievances.map((g) => (
            <GrievanceCard key={g.id} g={g} />
          ))}
        </div>
      )}
    </div>
  );
}
