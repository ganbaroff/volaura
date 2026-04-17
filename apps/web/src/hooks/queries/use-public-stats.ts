"use client";

// TODO: Replace with @hey-api/openapi-ts generated hooks after pnpm generate:api

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";

export interface PublicStats {
  total_professionals: number;
  total_assessments: number;
  total_events: number;
  avg_aura_score: number;
}

/**
 * Fetches public platform stats — no auth required.
 * Backend: GET /api/stats/public
 */
export function usePublicStats() {
  return useQuery<PublicStats, ApiError>({
    queryKey: ["stats", "public"],
    queryFn: async () => {
      return apiFetch<PublicStats>("/stats/public");
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}
