"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { useTrackEvent } from "@/hooks/use-analytics";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TribeMemberStatus {
  user_id: string;
  display_name: string;
  avatar_url: string | null;
  active_this_week: boolean;
}

export interface TribeOut {
  tribe_id: string;
  expires_at: string;
  status: "active" | "expired" | "dissolved";
  members: TribeMemberStatus[];
  kudos_count_this_week: number; // 0 = show "Be the first" CTA (Q1)
  renewal_requested: boolean;
}

export interface TribeStreakOut {
  current_streak: number;
  longest_streak: number;
  last_activity_week: string | null;
  consecutive_misses_count: number;
  crystal_fade_level: 0 | 1 | 2; // 0=bright, 1=dim, 2=dimmer (3=just reset, shown as 0)
}

export interface PoolStatusOut {
  in_pool: boolean;
  joined_at: string | null; // ISO 8601 — null when not in pool
}

// ── Queries ───────────────────────────────────────────────────────────────────

export function useMyTribe() {
  return useQuery<TribeOut | null>({
    queryKey: ["tribe", "me"],
    queryFn: async () => {
      const res = await apiFetch<TribeOut | null>("/api/tribes/me");
      return res ?? null;
    },
    staleTime: 60_000, // 1 min — activity status updates hourly at most
  });
}

export function useMyStreak() {
  return useQuery<TribeStreakOut | null>({
    queryKey: ["tribe", "streak"],
    queryFn: async () => {
      const res = await apiFetch<TribeStreakOut | null>("/api/tribes/me/streak");
      return res ?? null;
    },
    staleTime: 5 * 60_000, // 5 min — streak updates weekly
  });
}

// ── Mutations ─────────────────────────────────────────────────────────────────

export function useSendKudos() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await apiFetch("/api/tribes/me/kudos", { method: "POST" });
      return res;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tribe", "me"] });
    },
  });
}

export function useOptOutOfTribe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await apiFetch("/api/tribes/opt-out", { method: "POST" });
      return res;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tribe"] });
    },
  });
}

export function useRequestTribeRenewal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await apiFetch("/api/tribes/renew", { method: "POST" });
      return res;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tribe", "me"] });
    },
  });
}

export function useMyPoolStatus() {
  return useQuery<PoolStatusOut>({
    queryKey: ["tribe", "pool-status"],
    queryFn: async () => {
      const res = await apiFetch("/api/tribes/me/pool-status");
      return res as unknown as PoolStatusOut;
    },
    staleTime: 30_000, // 30s — check frequently while waiting for match
  });
}

export function useJoinTribePool() {
  const queryClient = useQueryClient();
  const track = useTrackEvent();
  return useMutation({
    mutationFn: async () => {
      const res = await apiFetch("/api/tribes/join-pool", { method: "POST" });
      return res;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tribe", "pool-status"] });
      track("tribe_pool_joined");
    },
  });
}
