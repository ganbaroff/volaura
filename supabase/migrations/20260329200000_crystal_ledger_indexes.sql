-- Performance: composite indexes on game_crystal_ledger
--
-- WHY NOW: character.py has two hot query patterns that scan the full user partition:
--
--   1. Daily-cap check (lines 121-130):
--      .eq("user_id", ...).eq("source", ...).gte("created_at", midnight_utc)
--      Without a composite index on (user_id, source, created_at) Postgres performs
--      a sequential scan of all rows for that user, then filters by source and date.
--      At 50 crystal events/day × 30 days = 1,500 rows per user — acceptable today,
--      but at 100k users with 90-day retention this degrades to a full table scan.
--
--   2. Balance query (lines 264-273):
--      .select("amount").eq("user_id", ...)
--      Aggregates SUM(amount) over all rows for a user. The existing index
--      idx_crystal_ledger_user covers user_id + created_at — but Postgres still
--      reads every row to project the amount column. An index on (user_id, amount)
--      is a covering index: the executor can satisfy the entire SUM from the index
--      without touching the heap, especially valuable after HOT updates vacuum.
--
-- RLS CHECK: game_crystal_ledger already has RLS enabled and a SELECT policy
-- (added in 20260327000031_character_state_tables.sql, lines 142-148).
-- No INSERT policy is intentional — crystal writes are service-role only (API).
-- This migration adds ONLY indexes; no schema or policy changes needed.
--
-- IDEMPOTENT: all statements use IF NOT EXISTS — safe to re-run.

-- Index 1: covers the daily-cap query pattern
--   WHERE user_id = $1 AND source = $2 AND created_at >= $3
--   The leading user_id column ensures per-user partition pruning.
--   source comes second (high selectivity for a given user on a given day).
--   created_at last because gte is a range scan — range columns go last in B-tree.
CREATE INDEX IF NOT EXISTS idx_crystal_ledger_user_source_time
    ON public.game_crystal_ledger(user_id, source, created_at);

-- Index 2: covering index for the balance aggregate query
--   WHERE user_id = $1 → SUM(amount)
--   Including amount as the second column makes this a covering index:
--   Postgres can compute SUM(amount) from the index leaf pages without a heap fetch.
CREATE INDEX IF NOT EXISTS idx_crystal_ledger_user_amount
    ON public.game_crystal_ledger(user_id, amount);
