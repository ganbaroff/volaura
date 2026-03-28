"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";

// Skills endpoint not in generated OpenAPI spec — manual fetch

export interface SkillResponse {
  skill: string;
  output: Record<string, unknown> | string;
  model_used: string;
}

interface SkillRequest {
  context?: Record<string, unknown>;
  question?: string;
  language?: string;
}

/**
 * Execute a product skill via POST /api/skills/{name}.
 * Returns LLM-generated structured output per skill spec.
 */
export function useSkill(
  skillName: string,
  request?: SkillRequest,
  options?: { enabled?: boolean; staleTime?: number },
) {
  const getToken = useAuthToken();

  return useQuery<SkillResponse, ApiError>({
    queryKey: ["skill", skillName, request],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<SkillResponse>(`/api/skills/${skillName}`, {
        method: "POST",
        token,
        body: JSON.stringify(request ?? { language: "en" }),
      });
    },
    enabled: options?.enabled !== false,
    staleTime: options?.staleTime ?? 5 * 60 * 1000,
    retry: 1,
  });
}
