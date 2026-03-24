"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { Badge, ActivityItem, DashboardStats } from "@/lib/api/types";

// TODO: Replace with @hey-api/openapi-ts generated hooks after pnpm generate:api

export function useBadges() {
  const getToken = useAuthToken();

  return useQuery<Badge[], ApiError>({
    queryKey: ["badges", "me"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<Badge[]>("/api/badges/me", { token });
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Activity feed — aggregated from assessment_sessions, badges, events, behavior_signals.
 * Backend: GET /api/activity/me
 */
export function useActivity(limit = 20) {
  const getToken = useAuthToken();

  return useQuery<ActivityItem[], ApiError>({
    queryKey: ["activity", limit],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<ActivityItem[]>(`/api/activity/me?limit=${limit}`, { token });
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Dashboard stats — events attended, verified skills, streak, hours.
 * Backend: GET /api/activity/stats/me
 */
export function useDashboardStats() {
  const getToken = useAuthToken();

  return useQuery<DashboardStats, ApiError>({
    queryKey: ["dashboard", "stats"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<DashboardStats>("/api/activity/stats/me", { token });
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}
