"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Users, Building2, ClipboardList, Star, Loader2, Gavel } from "lucide-react";
import { useAdminStats } from "@/hooks/queries/use-admin";
import { cn } from "@/lib/utils/cn";

function StatCard({
  icon, label, value, highlight, href,
}: { icon: React.ReactNode; label: string; value: string | number; highlight?: boolean; href?: string }) {
  const body = (
    <div className={cn(
      "rounded-xl border border-border bg-card p-5 transition-colors",
      href && "hover:bg-surface-container cursor-pointer"
    )}>
      <div className={cn("mb-2", highlight ? "text-primary" : "text-on-surface-variant")}>{icon}</div>
      <p className={cn("text-3xl font-bold tabular-nums", highlight ? "text-primary" : "text-on-surface")}>{value}</p>
      <p className="mt-1 text-sm text-on-surface-variant">{label}</p>
    </div>
  );
  return href ? <Link href={href}>{body}</Link> : body;
}

export function AdminOverview() {
  const { locale } = useParams<{ locale: string }>();
  const { data: stats, isLoading } = useAdminStats();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-on-surface">Platform Overview</h1>
        <p className="mt-1 text-sm text-on-surface-variant">Live stats — refreshes every 60 seconds</p>
      </div>
      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="size-6 animate-spin text-primary" role="status" aria-label="Loading" />
        </div>
      )}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard icon={<Users className="size-5" />} label="Total Users" value={stats.total_users} />
          <StatCard icon={<Building2 className="size-5" />} label="Active Organizations" value={stats.total_organizations} />
          <StatCard
            icon={<Building2 className="size-5" />}
            label="Pending Approvals"
            value={stats.pending_org_approvals}
            highlight={stats.pending_org_approvals > 0}
          />
          <StatCard icon={<ClipboardList className="size-5" />} label="Assessments Today" value={stats.assessments_today} />
          <StatCard icon={<Star className="size-5" />} label="Avg AURA Score" value={stats.avg_aura_score?.toFixed(1) ?? "—"} highlight />
          <StatCard
            icon={<Gavel className="size-5" />}
            label="Pending Grievances"
            value={stats.pending_grievances}
            highlight={stats.pending_grievances > 0}
            href={`/${locale}/admin/grievances`}
          />
        </div>
      )}
    </div>
  );
}
