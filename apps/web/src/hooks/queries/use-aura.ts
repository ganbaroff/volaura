"use client";

import { useQuery } from "@tanstack/react-query";
import { getMyAuraApiAuraMeGet, getAuraByIdApiAuraVolunteerIdGet } from "@/lib/api/generated";
import type { AuraScore } from "@/lib/api/types";
import type { AuraScoreResponse } from "@/lib/api/generated/types.gen";
import { toAuraScore } from "@/lib/api/types";

/**
 * Fetches current user's AURA score via generated SDK.
 * Auth handled by client interceptor.
 */
export function useAuraScore() {
  return useQuery<AuraScore>({
    queryKey: ["aura-score"],
    queryFn: async () => {
      const { data, error } = await getMyAuraApiAuraMeGet();
      if (error || !data) throw new Error("Failed to fetch AURA score");
      return toAuraScore(data as unknown as AuraScoreResponse);
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useAuraScoreByVolunteer(volunteerId: string | undefined) {
  return useQuery<AuraScore>({
    queryKey: ["aura-score", volunteerId],
    queryFn: async () => {
      const { data, error } = await getAuraByIdApiAuraVolunteerIdGet({
        path: { volunteer_id: volunteerId! },
      });
      if (error || !data) throw new Error("Failed to fetch AURA score");
      return toAuraScore(data as unknown as AuraScoreResponse);
    },
    enabled: !!volunteerId,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}
