"use client";

import { useState } from "react";
import { Loader2, CheckCircle2, XCircle, Globe, ExternalLink } from "lucide-react";
import { usePendingOrganizations, useApproveOrganization, useRejectOrganization } from "@/hooks/queries/use-admin";
import { cn } from "@/lib/utils/cn";

export default function AdminOrganizationsPage() {
  const { data: orgs, isLoading } = usePendingOrganizations();
  const approve = useApproveOrganization();
  const reject = useRejectOrganization();
  const [actingOn, setActingOn] = useState<string | null>(null);

  async function handleApprove(orgId: string) {
    setActingOn(orgId);
    try { await approve.mutateAsync(orgId); } finally { setActingOn(null); }
  }

  async function handleReject(orgId: string) {
    if (!confirm("Reject this organization? This will deactivate it.")) return;
    setActingOn(orgId);
    try { await reject.mutateAsync(orgId); } finally { setActingOn(null); }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-on-surface">Organization Approvals</h1>
        <p className="mt-1 text-sm text-on-surface-variant">
          Organizations pending verification —{" "}
          <span className="text-primary font-medium">{orgs?.length ?? "…"} pending</span>
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="size-6 animate-spin text-primary" role="status" aria-label="Loading" />
        </div>
      )}

      {orgs?.length === 0 && (
        <div className="rounded-2xl border border-dashed border-outline-variant bg-surface-container-low p-10 text-center">
          <CheckCircle2 className="mx-auto size-10 text-green-500" aria-hidden="true" />
          <p className="mt-3 font-semibold text-on-surface">All caught up</p>
          <p className="mt-1 text-sm text-on-surface-variant">No organizations pending approval.</p>
        </div>
      )}

      {orgs && orgs.length > 0 && (
        <div className="space-y-3">
          {orgs.map((org) => {
            const isActing = actingOn === org.id;
            return (
              <div key={org.id} className="rounded-xl border border-border bg-surface-container-low p-4">
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-on-surface truncate">{org.name}</p>
                      {org.trust_score != null && (
                        <span className="text-xs text-on-surface-variant shrink-0">
                          Trust: <span className="text-primary font-medium">{org.trust_score.toFixed(1)}</span>
                        </span>
                      )}
                    </div>
                    {org.description && (
                      <p className="mt-0.5 text-sm text-on-surface-variant line-clamp-2">{org.description}</p>
                    )}
                    <div className="mt-1.5 flex flex-wrap gap-3 text-xs text-on-surface-variant">
                      <span>Owner: <span className="text-on-surface">@{org.owner_username ?? org.owner_id.slice(0, 8)}</span></span>
                      <span>Registered: {new Date(org.created_at).toLocaleDateString()}</span>
                      {org.website && (
                        <a href={org.website} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline">
                          <Globe className="size-3" aria-hidden="true" /> Website
                          <ExternalLink className="size-3" aria-hidden="true" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    {isActing ? (
                      <Loader2 className="size-5 animate-spin text-primary" />
                    ) : (
                      <>
                        <button
                          onClick={() => handleApprove(org.id)}
                          className="flex items-center gap-1.5 rounded-lg bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 transition-opacity"
                          aria-label={`Approve ${org.name}`}
                        >
                          <CheckCircle2 className="size-3.5" aria-hidden="true" /> Approve
                        </button>
                        <button
                          onClick={() => handleReject(org.id)}
                          className={cn(
                            "flex items-center gap-1.5 rounded-lg border border-red-500/40 px-3 py-1.5 text-xs font-semibold text-red-400",
                            "hover:bg-red-500/10 transition-colors"
                          )}
                          aria-label={`Reject ${org.name}`}
                        >
                          <XCircle className="size-3.5" aria-hidden="true" /> Reject
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
