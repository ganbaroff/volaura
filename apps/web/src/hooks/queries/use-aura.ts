"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { AuraScore } from "@/lib/api/types";

// TODO: Replace with @hey-api/openapi-ts generated hooks after pnpm generate:api

export function useAuraScore() {
  const getToken = useAuthToken();

  return useQuery<AuraScore, ApiError>({
    queryKey: ["aura-score"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AuraScore>("/api/aura/me", { token });
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
      return apiFetch<AuraScore>(`/api/aura/${volunteerId}`, { token });
    },
    enabled: !!volunteerId,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}
