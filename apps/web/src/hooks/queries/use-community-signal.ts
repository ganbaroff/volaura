"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";

export interface CommunitySignal {
  professionals_today: number;
  professionals_this_week: number;
  total_professionals: number;
}

/**
 * Aggregate social proof for Constitution G44 — "N professionals took this
 * assessment today" without leaderboard framing (Crystal Law 5).
 * Public endpoint, no auth required.
 */
export function useCommunitySignal() {
  return useQuery<CommunitySignal, ApiError>({
    queryKey: ["community", "signal"],
    queryFn: async () => apiFetch<CommunitySignal>("/community/signal"),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
