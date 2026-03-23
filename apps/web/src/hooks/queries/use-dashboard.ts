"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { Badge, ActivityItem } from "@/lib/api/types";

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
 * Activity feed — currently not a dedicated endpoint.
 * Uses assessment results + events as activity items.
 * TODO: Add dedicated /api/activity endpoint when backend supports it
 */
export function useActivity() {
  const getToken = useAuthToken();

  return useQuery<ActivityItem[], ApiError>({
    queryKey: ["activity"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      // No dedicated activity endpoint yet — return empty
      // The dashboard components handle empty state gracefully
      return [];
    },
    // Don't retry since this is a placeholder
    retry: false,
  });
}
