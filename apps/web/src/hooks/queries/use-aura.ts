"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { AuraScore } from "@/lib/api/types";
import type { AuraScoreResponse } from "@/lib/api/generated/types.gen";
import { toAuraScore } from "@/lib/api/types";

/**
 * Fetches current user's AURA score.
 * Uses generated AuraScoreResponse type, transforms to AuraScore for UI compatibility.
 */
export function useAuraScore() {
  const getToken = useAuthToken();

  return useQuery<AuraScore, ApiError>({
    queryKey: ["aura-score"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const raw = await apiFetch<AuraScoreResponse>("/api/aura/me", { token });
      return toAuraScore(raw);
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useAuraScoreByVolunteer(volunteerId: string | undefined) {
  const getToken = useAuthToken();

  return useQuery<AuraScore, ApiError>({
    queryKey: ["aura-score", volunteerId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const raw = await apiFetch<AuraScoreResponse>(`/api/aura/${volunteerId}`, { token });
      return toAuraScore(raw);
    },
    enabled: !!volunteerId,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}
