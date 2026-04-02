"use client";

/**
 * Hooks for the cross-product character state (crystal balance, XP, verified skills).
 *
 * Endpoints:
 *   GET /api/character/crystals  — lightweight balance-only (used by dashboard widget)
 *   GET /api/character/state     — full character state (used by future Life Sim page)
 *
 * Both endpoints require auth (Supabase JWT in Authorization header).
 * The generated SDK client already injects the JWT via its interceptor.
 */

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";

// ── Types (mirrors Python CrystalBalanceOut / CharacterStateOut) ─────────────

export interface CrystalBalance {
  user_id: string;
  crystal_balance: number;
  computed_at: string;
}

export interface VerifiedSkill {
  slug: string;
  aura_score: number | null;
  badge_tier: string | null;
}

export interface CharacterState {
  user_id: string;
  crystal_balance: number;
  xp_total: number;
  verified_skills: VerifiedSkill[];
  character_stats: Record<string, number>;
  login_streak: number;
  event_count: number;
  last_event_at: string | null;
  computed_at: string;
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

/**
 * Fetches the user's crystal balance.
 * Lightweight — 1 SQL aggregate. Use this for the dashboard widget.
 * Returns null on 404 (no events yet — balance is implicitly 0).
 */
export function useCrystalBalance() {
  return useQuery<CrystalBalance | null>({
    queryKey: ["crystal-balance"],
    queryFn: async () => {
      try {
        const data = await apiFetch<CrystalBalance>("/api/character/crystals");
        return data;
      } catch (err: unknown) {
        // 404 = user has no character events yet — treat as 0 balance
        const status = (err as { status?: number })?.status;
        if (status === 404) return null;
        throw err;
      }
    },
    staleTime: 30 * 1000,   // 30s — balance changes only on assessment completion
    retry: 1,
  });
}

/**
 * Fetches full character state — used by Life Sim page, profile page.
 * Heavier than useCrystalBalance (5 queries server-side).
 * Only enable when the full state is actually needed.
 */
export function useCharacterState(enabled = true) {
  return useQuery<CharacterState | null>({
    queryKey: ["character-state"],
    queryFn: async () => {
      try {
        const data = await apiFetch<CharacterState>("/api/character/state");
        return data;
      } catch (err: unknown) {
        const status = (err as { status?: number })?.status;
        if (status === 404) return null;
        throw err;
      }
    },
    staleTime: 60 * 1000,   // 1 min — stats change less frequently
    enabled,
    retry: 1,
  });
}
