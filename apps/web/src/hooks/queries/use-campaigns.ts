"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";

// ── Types (mirror apps/api/app/schemas/campaign.py) ────────────────────────────

export interface Campaign {
  id: string;
  org_id: string;
  title: string;
  description: string | null;
  competency_slugs: string[];
  invite_token: string;
  status: "active" | "closed" | "archived";
  deadline_days: number;
  candidate_cap: number;
  created_at: string;
  candidate_count: number;
  completed_count: number;
}

export interface CampaignCreateInput {
  title: string;
  description?: string;
  competency_slugs: string[];
  deadline_days?: number;
  candidate_cap?: number;
}

export interface PublicCampaign {
  title: string;
  description: string | null;
  org_name: string;
  org_logo_url: string | null;
  competency_slugs: string[];
  status: string;
  deadline_days: number;
  is_full: boolean;
}

export interface JoinedSession {
  session_id: string;
  competency_slug: string;
  status: string;
}

export interface CampaignJoinResult {
  campaign_id: string;
  already_joined: boolean;
  sessions: JoinedSession[];
}

export interface CandidateReportRow {
  professional_id: string;
  display_name: string | null;
  username: string | null;
  avatar_url: string | null;
  joined_at: string;
  completed_sessions: number;
  assigned_sessions: number;
  campaign_score: number | null;
  badge_tier: string | null;
  competency_scores: Record<string, number>;
}

export interface CampaignReport {
  campaign: Campaign;
  candidates: CandidateReportRow[];
}

// ── Org-side hooks ──────────────────────────────────────────────────────────────

export function useMyCampaigns() {
  return useQuery<Campaign[], ApiError>({
    queryKey: ["campaigns", "mine"],
    queryFn: () => apiFetch<Campaign[]>("/campaigns"),
    staleTime: 60 * 1000,
    retry: 1,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();
  return useMutation<Campaign, ApiError, CampaignCreateInput>({
    mutationFn: (body) =>
      apiFetch<Campaign>("/campaigns", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}

export function useUpdateCampaignStatus() {
  const queryClient = useQueryClient();
  return useMutation<Campaign, ApiError, { campaignId: string; status: "active" | "closed" | "archived" }>({
    mutationFn: ({ campaignId, status }) =>
      apiFetch<Campaign>(`/campaigns/${campaignId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}

export function useCampaignReport(campaignId: string | null) {
  return useQuery<CampaignReport, ApiError>({
    queryKey: ["campaigns", "report", campaignId],
    queryFn: () => apiFetch<CampaignReport>(`/campaigns/${campaignId}/report`),
    enabled: Boolean(campaignId),
    staleTime: 30 * 1000,
    retry: 1,
  });
}

// ── Candidate-side hooks (public landing) ──────────────────────────────────────

export function usePublicCampaign(token: string | null) {
  return useQuery<PublicCampaign, ApiError>({
    queryKey: ["campaigns", "public", token],
    queryFn: () => apiFetch<PublicCampaign>(`/campaigns/public/${token}`),
    enabled: Boolean(token),
    staleTime: 60 * 1000,
    retry: 1,
  });
}

export function useJoinCampaign() {
  const queryClient = useQueryClient();
  return useMutation<CampaignJoinResult, ApiError, string>({
    mutationFn: (token) =>
      apiFetch<CampaignJoinResult>(`/campaigns/public/${token}/join`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assessment"] });
    },
  });
}
