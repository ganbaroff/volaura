"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthToken } from "./use-auth-token";
import { apiFetch, ApiError } from "@/lib/api/client";

export interface QuestionResult {
  question_id: string;
  question_en: string | null;
  question_az: string | null;
  difficulty_label: "Easy" | "Medium" | "Hard" | "Expert";
  is_correct: boolean;
  response_time_ms: number | null;
}

export interface QuestionBreakdown {
  session_id: string;
  competency_slug: string;
  questions: QuestionResult[];
}

export function useQuestionBreakdown(sessionId: string | undefined) {
  const getToken = useAuthToken();

  return useQuery<QuestionBreakdown, ApiError>({
    queryKey: ["assessment", "questions", sessionId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<QuestionBreakdown>(
        `/api/assessment/results/${sessionId}/questions`,
        { token }
      );
    },
    enabled: !!sessionId,
    staleTime: 10 * 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}
