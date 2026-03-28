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
import type { OrganizationResponse, OrganizationCreate, OrgDashboardStats, OrgVolunteerRow } from "@/lib/api/types";

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
