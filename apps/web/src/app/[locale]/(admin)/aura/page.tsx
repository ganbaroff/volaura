"use client";

import { Loader2 } from "lucide-react";
import { useAdminUsers } from "@/hooks/queries/use-admin";

// AURA scores page — shows top professionals by score
// Uses the users list for now (MVP); a dedicated /api/admin/aura endpoint
// can be added in Sprint 2 if more detail is needed.

const TIER_BADGE: Record<string, string> = {
  platinum: "bg-cyan-500/15 text-cyan-400 border-cyan-400/30",
  gold:     "bg-yellow-500/15 text-yellow-400 border-yellow-400/30",
  silver:   "bg-slate-400/15 text-slate-300 border-slate-300/30",
  bronze:   "bg-amber-700/15 text-amber-500 border-amber-500/30",
  none:     "bg-surface-container text-on-surface-variant border-border",
};

export default function AdminAuraPage() {
  const { data: users, isLoading } = useAdminUsers({ limit: 100, account_type: "volunteer" });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-on-surface">AURA Scores</h1>
        <p className="mt-1 text-sm text-on-surface-variant">Professional volunteers by verified competency score</p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="size-6 animate-spin text-primary" role="status" aria-label="Loading" />
        </div>
      )}

      {users && (
        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-container">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-on-surface-variant uppercase tracking-wide">#</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-on-surface-variant uppercase tracking-wide">User</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-on-surface-variant uppercase tracking-wide">Subscription</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-on-surface-variant uppercase tracking-wide">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users.map((user, idx) => (
                <tr key={user.id} className="hover:bg-surface-container/50 transition-colors">
                  <td className="px-4 py-3 text-on-surface-variant tabular-nums">{idx + 1}</td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-on-surface">{user.display_name ?? user.username}</p>
                    <p className="text-xs text-on-surface-variant">@{user.username}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-on-surface-variant">{user.subscription_status}</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-on-surface-variant">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-on-surface-variant">
        Sprint 2: Add AURA score column via dedicated <code>/api/admin/aura</code> endpoint with aura_scores join.
      </p>
    </div>
  );
}
