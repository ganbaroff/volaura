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

// ── Cross-product event feed (ecosystem bus reader) ───────────────────────────

export interface CharacterEvent {
  id: string;
  event_type: string;
  payload: Record<string, unknown>;
  source_product: string;
  created_at: string;
}

export interface UseCharacterEventFeedOptions {
  /** ISO 8601 timestamp — only return events newer than this. Pass last seen created_at for incremental polling. */
  since?: string;
  /** Filter to specific event types (e.g. ["assessment_completed", "aura_updated"]). Empty = all types. */
  eventTypes?: string[];
  /** Poll interval in ms. Default 30 000 (30s). */
  pollInterval?: number;
  /** Disable the hook. Default false. */
  enabled?: boolean;
}

/**
 * Polls the character_events bus for cross-product reactions.
 *
 * The `/api/character/events?since=<ts>` endpoint was specifically designed
 * for this incremental polling pattern (see character.py line 308).
 *
 * Primary consumer: /life page subscribes to "assessment_completed" events
 * to sync VOLAURA competency scores → LifeSim character stats without a
 * full page refresh.
 *
 * Usage:
 *   const { data: events } = useCharacterEventFeed({
 *     eventTypes: ["assessment_completed", "badge_tier_changed"],
 *   });
 */
export function useCharacterEventFeed({
  since,
  eventTypes,
  pollInterval = 30_000,
  enabled = true,
}: UseCharacterEventFeedOptions = {}) {
  const params = new URLSearchParams({ limit: "20" });
  if (since) params.set("since", since);

  return useQuery<CharacterEvent[]>({
    queryKey: ["character-events-feed", since, eventTypes],
    queryFn: async () => {
      try {
        const all = await apiFetch<CharacterEvent[]>(
          `/api/character/events?${params.toString()}`
        );
        if (!eventTypes || eventTypes.length === 0) return all;
        return all.filter((ev) => eventTypes.includes(ev.event_type));
      } catch (err: unknown) {
        const status = (err as { status?: number })?.status;
        if (status === 404) return [];
        throw err;
      }
    },
    staleTime: pollInterval - 1000,
    refetchInterval: pollInterval,
    enabled,
    retry: 1,
  });
}
