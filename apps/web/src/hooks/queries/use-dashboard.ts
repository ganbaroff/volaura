"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getMyActivityApiActivityMeGet,
  getMyStatsApiActivityStatsMeGet,
} from "@/lib/api/generated";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { Badge, ActivityItem, DashboardStats } from "@/lib/api/types";

// Badges endpoint not in OpenAPI spec — keep manual
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
 * Activity feed — uses generated SDK.
 * Backend: GET /api/activity/me
 */
export function useActivity(limit = 20) {
  return useQuery<ActivityItem[]>({
    queryKey: ["activity", limit],
    queryFn: async () => {
      const { data, error } = await getMyActivityApiActivityMeGet({
        query: { limit },
      });
      if (error) throw new Error("Failed to fetch activity");
      return (data ?? []) as ActivityItem[];
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Dashboard stats — uses generated SDK.
 * Backend: GET /api/activity/stats/me
 */
export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard", "stats"],
    queryFn: async () => {
      const { data, error } = await getMyStatsApiActivityStatsMeGet();
      if (error || !data) throw new Error("Failed to fetch dashboard stats");
      return data as DashboardStats;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}
