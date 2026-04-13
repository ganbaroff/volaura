"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getMyOrganizationApiOrganizationsMeGet,
  listOrganizationsApiOrganizationsGet,
  createOrganizationApiOrganizationsPost,
  updateMyOrganizationApiOrganizationsMePut,
} from "@/lib/api/generated";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { OrganizationResponse, OrganizationCreate, OrgDashboardStats, OrgProfessionalRow } from "@/lib/api/types";

/** My organization — the one the current user owns */
export function useMyOrganization() {
  return useQuery<OrganizationResponse>({
    queryKey: ["organizations", "me"],
    queryFn: async () => {
      const { data, error } = await getMyOrganizationApiOrganizationsMeGet();
      if (error || !data) throw new Error("Failed to fetch organization");
      return data as unknown as OrganizationResponse;
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

/** Public org list — no auth required */
export function useOrganizations(params?: { limit?: number; offset?: number }) {
  return useQuery<OrganizationResponse[]>({
    queryKey: ["organizations", "list", params],
    queryFn: async () => {
      const { data, error } = await listOrganizationsApiOrganizationsGet();
      if (error) throw new Error("Failed to fetch organizations");
      return (data ?? []) as unknown as OrganizationResponse[];
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();

  return useMutation<OrganizationResponse, Error, OrganizationCreate>({
    mutationFn: async (body) => {
      const { data, error } = await createOrganizationApiOrganizationsPost({ body });
      if (error || !data) throw new Error("Failed to create organization");
      return data as unknown as OrganizationResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  });
}

export function useUpdateOrganization() {
  const queryClient = useQueryClient();

  return useMutation<OrganizationResponse, Error, Partial<OrganizationCreate>>({
    mutationFn: async (body) => {
      const { data, error } = await updateMyOrganizationApiOrganizationsMePut({
        body: body as OrganizationCreate,
      });
      if (error || !data) throw new Error("Failed to update organization");
      return data as unknown as OrganizationResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations", "me"] });
    },
  });
}

// ── Org B2B endpoints (not in generated SDK — manual apiFetch) ──

/** Org B2B dashboard stats — completion rate, avg AURA, badge distribution */
export function useOrgDashboard() {
  const getToken = useAuthToken();

  return useQuery<OrgDashboardStats, ApiError>({
    queryKey: ["organizations", "me", "dashboard"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<OrgDashboardStats>("/api/organizations/me/dashboard", { token });
    },
    staleTime: 2 * 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

/** Collective AURA Ladders — org talent pool aggregate */
export interface CollectiveAuraData {
  org_id: string;
  count: number;
  avg_aura: number | null;
  trend: number | null;
}

export function useCollectiveAura(orgId: string | undefined) {
  const getToken = useAuthToken();

  return useQuery<CollectiveAuraData, ApiError>({
    queryKey: ["organizations", orgId, "collective-aura"],
    enabled: !!orgId,
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<CollectiveAuraData>(`/api/organizations/${orgId}/collective-aura`, { token });
    },
    staleTime: 10 * 60 * 1000, // 10 min — aggregate is not real-time sensitive
    retry: 1,
    throwOnError: false,
  });
}

export interface IntroRequestPayload {
  professional_id: string;
  project_name: string;
  timeline: "urgent" | "normal" | "flexible";
  message?: string;
}

export interface IntroRequestResult {
  id: string;
  org_id: string;
  professional_id: string;
  project_name: string;
  timeline: string;
  message: string | null;
  status: string;
  created_at: string;
}

/** Send a Request Introduction to a professional */
export function useCreateIntroRequest() {
  const getToken = useAuthToken();

  return useMutation<IntroRequestResult, ApiError, IntroRequestPayload>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<IntroRequestResult>("/api/organizations/intro-requests", {
        token,
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
  });
}

// ── Semantic professional search ──────────────────────────────────────────

export interface ProfessionalSearchPayload {
  query: string;
  min_aura?: number;
  badge_tier?: "platinum" | "gold" | "silver" | "bronze" | null;
  limit?: number;
  offset?: number;
}

export interface ProfessionalSearchResultItem {
  professional_id: string;
  username: string;
  display_name: string | null;
  overall_score: number;
  badge_tier: string;
  elite_status: boolean;
  location: string | null;
  languages: string[];
  similarity: number | null;
}

/** Semantic professional search — POST /api/organizations/search/professionals */
export function useProfessionalSearch() {
  const getToken = useAuthToken();

  return useMutation<ProfessionalSearchResultItem[], ApiError, ProfessionalSearchPayload>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<ProfessionalSearchResultItem[]>("/api/organizations/search/professionals", {
        token,
        method: "POST",
        body: JSON.stringify({ limit: 20, ...payload }),
      });
    },
  });
}

// ── Saved Searches (Sprint 8) ──────────────────────────────────────────────

export interface SavedSearchFilters {
  query?: string;
  min_aura?: number;
  badge_tier?: "platinum" | "gold" | "silver" | "bronze" | null;
  languages?: string[];
  location?: string;
}

export interface SavedSearchItem {
  id: string;
  org_id: string;
  name: string;
  filters: SavedSearchFilters;
  notify_on_match: boolean;
  last_checked_at: string;
  created_at: string;
}

export interface SaveSearchPayload {
  name: string;
  filters: SavedSearchFilters;
  notify_on_match?: boolean;
}

/** List all saved searches for the current user's org */
export function useSavedSearches() {
  const getToken = useAuthToken();

  return useQuery<SavedSearchItem[], ApiError>({
    queryKey: ["organizations", "saved-searches"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<SavedSearchItem[]>("/api/organizations/saved-searches", { token });
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

/** Save the current search filters under a name */
export function useCreateSavedSearch() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<SavedSearchItem, ApiError, SaveSearchPayload>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<SavedSearchItem>("/api/organizations/saved-searches", {
        token,
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations", "saved-searches"] });
    },
  });
}

/** Delete a saved search */
export function useDeleteSavedSearch() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: async (searchId) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      await apiFetch<void>(`/api/organizations/saved-searches/${searchId}`, {
        token,
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations", "saved-searches"] });
    },
  });
}

/** List professionals assigned assessments by this org */
export function useOrgProfessionals(params?: { status?: string; limit?: number; offset?: number }) {
  const getToken = useAuthToken();

  return useQuery<OrgProfessionalRow[], ApiError>({
    queryKey: ["organizations", "me", "professionals", params],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const search = new URLSearchParams();
      if (params?.status) search.set("status", params.status);
      if (params?.limit) search.set("limit", String(params.limit));
      if (params?.offset) search.set("offset", String(params.offset));
      const qs = search.toString();
      return apiFetch<OrgProfessionalRow[]>(`/api/organizations/me/professionals${qs ? `?${qs}` : ""}`, { token });
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}
