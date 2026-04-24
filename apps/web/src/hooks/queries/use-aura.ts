"use client";

import { useQuery } from "@tanstack/react-query";
import { getMyAuraApiAuraMeGet, getAuraByIdApiAuraProfessionalIdGet } from "@/lib/api/generated";
import type { AuraScore } from "@/lib/api/types";
import type { AuraScoreResponse } from "@/lib/api/generated/types.gen";
import { toAuraScore } from "@/lib/api/types";
import { ApiError, toApiError } from "@/lib/api/client";

/**
 * Fetches current user's AURA score via generated SDK.
 * Auth handled by client interceptor.
 */
export function useAuraScore() {
  return useQuery<AuraScore | null, ApiError>({
    queryKey: ["aura-score"],
    queryFn: async () => {
      const { data, error } = await getMyAuraApiAuraMeGet();
      if (error) {
        const apiError = toApiError(error, { message: "Failed to fetch AURA score" });
        if (apiError.code === "AURA_NOT_FOUND") return null;
        throw apiError;
      }
      if (!data) return null;
      return toAuraScore(data as unknown as AuraScoreResponse);
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useAuraScoreByProfessional(professionalId: string | undefined) {
  return useQuery<AuraScore | null, ApiError>({
    queryKey: ["aura-score", professionalId],
    queryFn: async () => {
      const { data, error } = await getAuraByIdApiAuraProfessionalIdGet({
        path: { professional_id: professionalId! },
      });
      if (error) {
        const apiError = toApiError(error, { message: "Failed to fetch AURA score" });
        if (apiError.code === "AURA_NOT_FOUND") return null;
        throw apiError;
      }
      if (!data) return null;
      return toAuraScore(data as unknown as AuraScoreResponse);
    },
    enabled: !!professionalId,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}
