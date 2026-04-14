"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";

export interface GrievanceCreateInput {
  subject: string;
  description: string;
  related_competency_slug?: string | null;
  related_session_id?: string | null;
}

export interface Grievance {
  id: string;
  subject: string;
  description: string;
  related_competency_slug: string | null;
  related_session_id: string | null;
  status: "pending" | "reviewing" | "resolved" | "rejected";
  resolution: string | null;
  created_at: string;
  resolved_at: string | null;
}

export function useFileGrievance() {
  const getToken = useAuthToken();
  const qc = useQueryClient();

  return useMutation<Grievance, ApiError, GrievanceCreateInput>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<Grievance>("/api/aura/grievance", {
        token,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["grievances"] });
    },
  });
}

export function useOwnGrievances() {
  const getToken = useAuthToken();

  return useQuery<Grievance[], ApiError>({
    queryKey: ["grievances", "own"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const res = await apiFetch<{ data: Grievance[] }>("/api/aura/grievance", { token });
      return res.data ?? [];
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}
