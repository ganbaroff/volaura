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

export interface AutomatedDecision {
  id: string;
  decision_type: string;
  created_at: string;
  human_reviewable: boolean;
}

export interface HumanReviewRequest {
  id: string;
  user_id: string;
  automated_decision_id: string;
  source_product: "volaura" | "mindshift" | "lifesim" | "brandedby" | "zeus";
  request_reason: string;
  requested_at: string;
  sla_deadline: string;
  status: "pending" | "in_review" | "resolved_uphold" | "resolved_overturn" | "escalated_to_authority";
  resolved_at: string | null;
  resolution_notes: string | null;
  reviewer_user_id: string | null;
}

export interface HumanReviewCreateInput {
  automated_decision_id: string;
  request_reason: string;
  source_product?: "volaura" | "mindshift" | "lifesim" | "brandedby" | "zeus";
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

export function useAutomatedDecisions(limit = 20) {
  const getToken = useAuthToken();

  return useQuery<AutomatedDecision[], ApiError>({
    queryKey: ["human-review", "decisions", limit],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const res = await apiFetch<{ data: AutomatedDecision[] }>(`/api/aura/human-review/decisions?limit=${limit}`, { token });
      return res.data ?? [];
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

export function useCreateHumanReview() {
  const getToken = useAuthToken();
  const qc = useQueryClient();

  return useMutation<HumanReviewRequest, ApiError, HumanReviewCreateInput>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<HumanReviewRequest>("/api/aura/human-review", {
        token,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["human-review"] });
    },
  });
}

export function useMyHumanReviews() {
  const getToken = useAuthToken();

  return useQuery<HumanReviewRequest[], ApiError>({
    queryKey: ["human-review", "own"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const res = await apiFetch<{ data: HumanReviewRequest[] }>("/api/aura/human-review", { token });
      return res.data ?? [];
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

// ── Admin ─────────────────────────────────────────────────────────────────────

export interface GrievanceAdmin extends Grievance {
  user_id: string;
  admin_notes: string | null;
  updated_at: string;
}

export interface GrievanceTransition {
  grievance_id: string;
  status: "reviewing" | "resolved" | "rejected";
  resolution?: string | null;
}

export function useAdminPendingGrievances() {
  const getToken = useAuthToken();

  return useQuery<GrievanceAdmin[], ApiError>({
    queryKey: ["grievances", "admin", "pending"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const res = await apiFetch<{ data: GrievanceAdmin[] }>(
        "/api/aura/grievance/admin/pending",
        { token }
      );
      return res.data ?? [];
    },
    staleTime: 30 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

export function useAdminHistoryGrievances(limit = 50) {
  const getToken = useAuthToken();

  return useQuery<GrievanceAdmin[], ApiError>({
    queryKey: ["grievances", "admin", "history", limit],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const res = await apiFetch<{ data: GrievanceAdmin[] }>(
        `/api/aura/grievance/admin/history?limit=${limit}`,
        { token }
      );
      return res.data ?? [];
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

export function useTransitionGrievance() {
  const getToken = useAuthToken();
  const qc = useQueryClient();

  return useMutation<GrievanceAdmin, ApiError, GrievanceTransition>({
    mutationFn: async ({ grievance_id, ...body }) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<GrievanceAdmin>(`/api/aura/grievance/admin/${grievance_id}`, {
        token,
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["grievances"] });
    },
  });
}
