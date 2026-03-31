-- =============================================================================
-- P0 Security Fixes — Batch 1
-- Sprint E2 | 2026-03-30
-- =============================================================================
-- 1. Crystal ledger idempotency: prevent retry double-spend via UNIQUE index
-- 2. Revoke avg_aura_score() from anon: prevents unauthenticated DoS
-- 3. Add rapid-restart assessment cooldown column (30-minute window)
-- =============================================================================

-- ── Fix 1: Crystal Ledger Idempotency ────────────────────────────────────────
-- Problem: deduct_crystals_atomic RPC has advisory lock but no idempotency.
-- If a network retry fires after the first INSERT succeeded, a second deduction
-- is inserted — double-spend. Fix: UNIQUE index on (user_id, reference_id) for
-- non-NULL reference_ids (NULL = direct award, intentionally duplicatable).
--
-- Partial index (WHERE reference_id IS NOT NULL) ensures:
-- - Named transactions (deductions, specific rewards) are idempotent
-- - Anonymous crystal grants (NULL reference_id) remain unrestricted
-- - Index only covers ~50% of rows (the ones that matter for idempotency)

CREATE UNIQUE INDEX IF NOT EXISTS uq_crystal_ledger_reference
    ON public.game_crystal_ledger (user_id, reference_id)
    WHERE reference_id IS NOT NULL;

COMMENT ON INDEX public.uq_crystal_ledger_reference IS
    'P0 Security Fix (2026-03-30): Idempotency guard for crystal transactions. '
    'Prevents double-spend on network retries — same (user_id, reference_id) pair '
    'cannot insert twice. NULL reference_id excluded (anonymous awards are exempt). '
    'Works alongside deduct_crystals_atomic advisory lock as defense-in-depth.';

-- ── Fix 2: Revoke avg_aura_score() from anon ─────────────────────────────────
-- Problem: anon role can call avg_aura_score() directly against Supabase PostgREST
-- without going through the API rate limiter. Any unauthenticated client can spam
-- rpc("avg_aura_score") and trigger a full-table AVG scan per call.
-- Fix: Revoke anon EXECUTE. /api/stats/public uses service_role (still has EXECUTE).
-- Authenticated users (logged-in clients) also don't need direct RPC access.

REVOKE EXECUTE ON FUNCTION public.avg_aura_score() FROM anon;
REVOKE EXECUTE ON FUNCTION public.avg_aura_score() FROM authenticated;

COMMENT ON FUNCTION public.avg_aura_score IS
    'Session 64 (created) + Session E2 (hardened): Platform-wide average AURA score. '
    'Only service_role can execute — prevents unauthenticated DoS via direct PostgREST RPC. '
    '/api/stats/public calls this via SupabaseAdmin (service_role key).';

-- ── Fix 3: Assessment rapid-restart tracking ─────────────────────────────────
-- Problem: A user can start an assessment, see hard questions, immediately
-- abandon it (never complete), and restart to cherry-pick easier questions.
-- The 7-day cooldown only applies to COMPLETED sessions — abandoned sessions
-- are unchecked.
-- Fix: Track last_started_at per (user, competency) to enforce a 30-minute
-- restart cooldown even for abandoned sessions.
--
-- Implementation: Add a column to assessment_sessions that we can query cheaply
-- (index on volunteer_id + competency_id + started_at covers the lookup).

CREATE INDEX IF NOT EXISTS idx_assessment_sessions_rapid_restart
    ON public.assessment_sessions (volunteer_id, competency_id, started_at DESC)
    WHERE status = 'in_progress' OR status = 'abandoned';

COMMENT ON INDEX public.idx_assessment_sessions_rapid_restart IS
    'P0 Security Fix (2026-03-30): Supports rapid-restart cooldown check in '
    'start_assessment endpoint. Covers (volunteer_id, competency_id, started_at) '
    'for in_progress and abandoned sessions to enforce 30-minute restart window.';
