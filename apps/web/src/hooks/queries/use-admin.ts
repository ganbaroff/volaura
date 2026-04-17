"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface AdminUserRow {
  id: string;
  username: string;
  display_name: string | null;
  account_type: string;
  subscription_status: string;
  is_platform_admin: boolean;
  created_at: string;
}

export interface AdminOrgRow {
  id: string;
  name: string;
  description: string | null;
  website: string | null;
  owner_id: string;
  owner_username: string | null;
  trust_score: number | null;
  verified_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  total_organizations: number;
  pending_org_approvals: number;
  assessments_today: number;
  avg_aura_score: number | null;
  pending_grievances: number;
}

// ── Is Admin check (used by AdminGuard) ───────────────────────────────────────

export function useAdminPing() {
  const getToken = useAuthToken();

  return useQuery<boolean, ApiError>({
    queryKey: ["admin", "ping"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return false;
      try {
        await apiFetch<{ ok: boolean }>("/api/admin/ping", { token });
        return true;
      } catch {
        return false;
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
    throwOnError: false,
  });
}

// ── Stats ──────────────────────────────────────────────────────────────────────

export function useAdminStats() {
  const getToken = useAuthToken();

  return useQuery<AdminStats, ApiError>({
    queryKey: ["admin", "stats"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AdminStats>("/api/admin/stats", { token });
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

// ── Users ──────────────────────────────────────────────────────────────────────

export function useAdminUsers(params?: { limit?: number; offset?: number; account_type?: string }) {
  const getToken = useAuthToken();

  return useQuery<AdminUserRow[], ApiError>({
    queryKey: ["admin", "users", params],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const qs = new URLSearchParams();
      if (params?.limit) qs.set("limit", String(params.limit));
      if (params?.offset) qs.set("offset", String(params.offset));
      if (params?.account_type) qs.set("account_type", params.account_type);
      return apiFetch<AdminUserRow[]>(`/api/admin/users${qs.toString() ? `?${qs}` : ""}`, { token });
    },
    staleTime: 30 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

// ── Organizations ──────────────────────────────────────────────────────────────

export function usePendingOrganizations() {
  const getToken = useAuthToken();

  return useQuery<AdminOrgRow[], ApiError>({
    queryKey: ["admin", "organizations", "pending"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AdminOrgRow[]>("/api/admin/organizations/pending", { token });
    },
    staleTime: 30 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

export function useApproveOrganization() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<{ org_id: string; action: string }, ApiError, string>({
    mutationFn: async (orgId) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch(`/api/admin/organizations/${orgId}/approve`, { token, method: "POST" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "organizations"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
    },
  });
}

export function useRejectOrganization() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<{ org_id: string; action: string }, ApiError, string>({
    mutationFn: async (orgId) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch(`/api/admin/organizations/${orgId}/reject`, { token, method: "POST" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "organizations"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
    },
  });
}

// ── Swarm Office ──────────────────────────────────────────────────────────────

export interface SwarmAgent {
  name: string;
  display_name: string;
  status: string;
  last_task: string;
  last_run: string | null;
  next_scheduled: string | null;
  blockers: string[];
  tasks_completed: number;
  tasks_failed: number;
}

export interface SwarmProposal {
  id: string;
  timestamp: string;
  agent: string;
  severity: string;
  type: string;
  status: string;
  title: string;
  content?: string;
  ceo_decision?: string;
}

export function useSwarmAgents() {
  const getToken = useAuthToken();

  return useQuery<{ agents: SwarmAgent[]; total_tracked: number; total_untracked: number }, ApiError>({
    queryKey: ["admin", "swarm", "agents"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch("/admin/swarm/agents", { token });
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: 1,
  });
}

export function useSwarmProposals(status?: string) {
  const getToken = useAuthToken();

  return useQuery<{ proposals: SwarmProposal[]; summary: { pending: number; approved: number; rejected: number } }, ApiError>({
    queryKey: ["admin", "swarm", "proposals", status],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const qs = status ? `?status=${status}` : "";
      return apiFetch(`/api/admin/swarm/proposals${qs}`, { token });
    },
    staleTime: 30_000,
    retry: 1,
  });
}

export function useDecideProposal() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<unknown, ApiError, { proposalId: string; action: string }>({
    mutationFn: async ({ proposalId, action }) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch(`/api/admin/swarm/proposals/${proposalId}/decide`, {
        method: "POST",
        body: JSON.stringify({ action }),
        token,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "swarm", "proposals"] });
    },
  });
}

export type SwarmFinding = {
  agent_id: string;
  task_id: string;
  ts: number;
  importance: number;
  category: string;
  severity: string;
  summary: string;
  recommendation: string;
  files: string[];
  confidence: number;
};

// ── M1 Admin Overview (2026-04-18) ────────────────────────────────────────────
// Backend: apps/api/app/routers/admin.py → /api/admin/stats/overview
// Schemas: apps/api/app/schemas/admin.py → AdminOverviewResponse
// Spec:    docs/engineering/ADMIN-DASHBOARD-SPEC.md §7 (Strange v2 pivot)
// Activation-first; pre-PMF. MRR/NRR/CAC stubbed until revenue exists.

export interface AdminActivationFunnel {
  product: "volaura" | "mindshift";
  signups_24h: number;
  activated_24h: number;
  activation_rate: number; // 0.0-1.0
}

export interface AdminPresenceMatrix {
  volaura_only: number;
  mindshift_only: number;
  both_products: number;
  total_users: number;
}

export interface AdminOverviewResponse {
  // Tier 1 scorecard
  activation_rate_24h: number;
  w4_retention: number | null;
  dau_wau_ratio: number;
  errors_24h: number;
  runway_months: number | null;
  // Tier 2 cross-product
  presence: AdminPresenceMatrix;
  funnels: AdminActivationFunnel[];
  // Meta
  computed_at: string;
  stale_after_seconds: number;
}

export interface AdminActivityEvent {
  id: string;
  product: "volaura" | "mindshift" | "lifesim" | "brandedby" | "zeus";
  event_type: string;
  user_id_prefix: string;
  created_at: string;
  payload_summary: string | null;
}

/** Exec scorecard + cross-product presence. 30s stale, 60s refetch. */
export function useAdminOverview() {
  const getToken = useAuthToken();

  return useQuery<AdminOverviewResponse, ApiError>({
    queryKey: ["admin", "stats", "overview"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AdminOverviewResponse>("/api/admin/stats/overview", { token });
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: 1,
    throwOnError: false,
  });
}

/** Live character_events tail for the admin feed. 15s poll. */
export function useAdminLiveEvents(limit = 50) {
  const getToken = useAuthToken();

  return useQuery<AdminActivityEvent[], ApiError>({
    queryKey: ["admin", "events", "live", limit],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AdminActivityEvent[]>(`/api/admin/events/live?limit=${limit}`, { token });
    },
    staleTime: 10_000,
    refetchInterval: 15_000,
    retry: 1,
    throwOnError: false,
  });
}

export function useSwarmFindings(category?: string, minImportance?: number) {
  const getToken = useAuthToken();

  return useQuery<{ findings: SwarmFinding[]; total: number; db_exists: boolean }, ApiError>({
    queryKey: ["admin", "swarm", "findings", category, minImportance],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      if (minImportance !== undefined) params.set("min_importance", String(minImportance));
      const qs = params.toString() ? `?${params}` : "";
      return apiFetch(`/api/admin/swarm/findings${qs}`, { token });
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: 1,
  });
}
