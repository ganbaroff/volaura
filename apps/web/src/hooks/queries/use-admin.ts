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
