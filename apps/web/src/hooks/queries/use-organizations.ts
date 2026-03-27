"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { OrganizationResponse, OrganizationCreate, OrgDashboardStats, OrgVolunteerRow } from "@/lib/api/types";

// TODO: Replace with @hey-api/openapi-ts generated hooks after pnpm generate:api

/** My organization — the one the current user owns */
export function useMyOrganization() {
  const getToken = useAuthToken();

  return useQuery<OrganizationResponse, ApiError>({
    queryKey: ["organizations", "me"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<OrganizationResponse>("/api/organizations/me", { token });
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
    // 404 = no org yet — treat as null, not error
    throwOnError: false,
  });
}

/** Public org list — no auth required */
export function useOrganizations(params?: { limit?: number; offset?: number }) {
  return useQuery<OrganizationResponse[], ApiError>({
    queryKey: ["organizations", "list", params],
    queryFn: async () => {
      const search = new URLSearchParams();
      if (params?.limit) search.set("limit", String(params.limit));
      if (params?.offset) search.set("offset", String(params.offset));
      const qs = search.toString();
      return apiFetch<OrganizationResponse[]>(`/api/organizations${qs ? `?${qs}` : ""}`);
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useCreateOrganization() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<OrganizationResponse, ApiError, OrganizationCreate>({
    mutationFn: async (data) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<OrganizationResponse>("/api/organizations", {
        method: "POST",
        token,
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  });
}

export function useUpdateOrganization() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<OrganizationResponse, ApiError, Partial<OrganizationCreate>>({
    mutationFn: async (data) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<OrganizationResponse>("/api/organizations/me", {
        method: "PUT",
        token,
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations", "me"] });
    },
  });
}

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

/** List volunteers assigned assessments by this org */
export function useOrgVolunteers(params?: { status?: string; limit?: number; offset?: number }) {
  const getToken = useAuthToken();

  return useQuery<OrgVolunteerRow[], ApiError>({
    queryKey: ["organizations", "me", "volunteers", params],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const search = new URLSearchParams();
      if (params?.status) search.set("status", params.status);
      if (params?.limit) search.set("limit", String(params.limit));
      if (params?.offset) search.set("offset", String(params.offset));
      const qs = search.toString();
      return apiFetch<OrgVolunteerRow[]>(`/api/organizations/me/volunteers${qs ? `?${qs}` : ""}`, { token });
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}
