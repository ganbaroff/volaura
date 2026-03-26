"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";

// ── Types ────────────────────────────────────────────────────────────────────

export interface ConceptScore {
  [concept: string]: number;
}

export interface EvaluationItem {
  question_id: string;
  concept_scores: ConceptScore;
  evaluation_confidence: "high" | "medium" | "low";
  methodology: string;
}

export interface CompetencyExplanation {
  competency_id: string;
  role_level: string;
  completed_at: string;
  items_evaluated: number;
  evaluations: EvaluationItem[];
}

export interface AuraExplanationResponse {
  volunteer_id: string;
  explanation_count: number;
  methodology_reference: string;
  explanations: CompetencyExplanation[];
}

// ── Hook ─────────────────────────────────────────────────────────────────────

/**
 * Fetches the AURA score explanation for the current user.
 * Lazy by default — only fetches when `enabled` is set to true
 * (i.e., when the user opens the "Why this score?" section).
 * staleTime: 10 minutes (explanation data rarely changes between sessions).
 */
export function useAuraExplanation(enabled: boolean) {
  const getToken = useAuthToken();

  return useQuery<AuraExplanationResponse, ApiError>({
    queryKey: ["aura-explanation"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AuraExplanationResponse>("/api/aura/me/explanation", { token });
    },
    enabled,
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });
}
