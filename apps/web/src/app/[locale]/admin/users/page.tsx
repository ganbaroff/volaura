"use client";

import { useState } from "react";
import { Loader2, ShieldCheck } from "lucide-react";
import { useAdminUsers } from "@/hooks/queries/use-admin";
import { cn } from "@/lib/utils/cn";

const ACCOUNT_TYPE_BADGE: Record<string, string> = {
  volunteer:     "bg-green-500/15 text-green-400 border-green-400/30",
  organization:  "bg-blue-500/15 text-blue-400 border-blue-400/30",
};

const SUB_BADGE: Record<string, string> = {
  trial:     "bg-yellow-500/15 text-yellow-400",
  active:    "bg-green-500/15 text-green-400",
  expired:   "bg-red-500/15 text-red-400",
  cancelled: "bg-slate-400/15 text-slate-300",
};

export default function AdminUsersPage() {
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const { data: users, isLoading } = useAdminUsers({ limit, offset });

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">Users</h1>
          <p className="mt-1 text-sm text-on-surface-variant">All registered platform users</p>
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="size-6 animate-spin text-primary" role="status" aria-label="Loading" />
        </div>
      )}

      {users && (
        <>
          <div className="rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-surface-container">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-on-surface-variant uppercase tracking-wide">User</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-on-surface-variant uppercase tracking-wide">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-on-surface-variant uppercase tracking-wide">Subscription</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-on-surface-variant uppercase tracking-wide">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-surface-container/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div>
                          <p className="font-medium text-on-surface">
                            {user.display_name ?? user.username}
                            {user.is_platform_admin && (
                              <ShieldCheck className="inline size-3.5 ml-1 text-primary" aria-label="Admin" />
                            )}
                          </p>
                          <p className="text-xs text-on-surface-variant">@{user.username}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn("text-xs px-2 py-0.5 rounded-full border font-medium", ACCOUNT_TYPE_BADGE[user.account_type] ?? "bg-slate-500/15 text-slate-300")}>
                        {user.account_type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", SUB_BADGE[user.subscription_status] ?? "bg-slate-500/15 text-slate-300")}>
                        {user.subscription_status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-on-surface-variant">
                      {new Date(user.created_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between text-sm text-on-surface-variant">
            <span>Showing {offset + 1}–{offset + users.length}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="px-3 py-1.5 rounded-lg border border-border hover:bg-surface-container disabled:opacity-40 transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={users.length < limit}
                className="px-3 py-1.5 rounded-lg border border-border hover:bg-surface-container disabled:opacity-40 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
