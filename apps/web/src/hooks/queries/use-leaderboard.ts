"use client";

// TODO: Replace with @hey-api/openapi-ts generated hooks after pnpm generate:api

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";

export interface LeaderboardEntry {
  rank: number;
  display_name: string;
  total_score: number;
  badge_tier: string;
  username: string | null;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  period: string;
}

export type LeaderboardPeriod = "weekly" | "monthly" | "all_time";

/**
 * Fetches the leaderboard for the given period.
 * Backend: GET /api/leaderboard?period=weekly|monthly|all_time&limit=50
 */
export function useLeaderboard(period: LeaderboardPeriod = "all_time") {
  const getToken = useAuthToken();

  return useQuery<LeaderboardResponse, ApiError>({
    queryKey: ["leaderboard", period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<LeaderboardResponse>(
        `/api/leaderboard?period=${period}&limit=50`,
        { token },
      );
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 2,
  });
}
