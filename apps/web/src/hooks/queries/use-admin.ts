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
