-- Migration: BrandedBy personality refresh worker RPCs
-- These SECURITY DEFINER functions cross the public→brandedby schema boundary
-- because the brandedby schema is not exposed via PostgREST.
-- Both functions are called by the brandedby_refresh_worker.py background job.
--
-- Applied: 2026-04-24 (G3.3 — personality refresh loop)

-- ── RPC 1: Read stale AI twins ──────────────────────────────────────────────
-- Returns twins where needs_personality_refresh = true, ordered by oldest first
-- so long-waiting twins are refreshed before newer ones.
-- Runs as postgres role to cross the schema boundary.

CREATE OR REPLACE FUNCTION public.brandedby_get_stale_twins(
    p_limit INT DEFAULT 10
)
RETURNS TABLE(
    id           UUID,
    user_id      UUID,
    display_name TEXT
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, brandedby
AS $$
    SELECT
        t.id,
        t.user_id,
        t.display_name
    FROM brandedby.ai_twins t
    WHERE t.needs_personality_refresh = true
    ORDER BY COALESCE(t.personality_refreshed_at, '1970-01-01'::TIMESTAMPTZ) ASC,
             t.created_at ASC
    LIMIT p_limit;
$$;

-- Restrict to service role only (called by background worker, not end users)
REVOKE ALL ON FUNCTION public.brandedby_get_stale_twins(INT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.brandedby_get_stale_twins(INT) FROM anon;
REVOKE ALL ON FUNCTION public.brandedby_get_stale_twins(INT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.brandedby_get_stale_twins(INT) TO service_role;


-- ── RPC 2: Write refreshed personality + reset stale flag ───────────────────
-- Updates personality_prompt, clears needs_personality_refresh, and records
-- personality_refreshed_at = now() for audit trail and ordering in RPC 1.
-- Runs as postgres role to write into brandedby schema.

CREATE OR REPLACE FUNCTION public.brandedby_apply_twin_personality(
    p_twin_id    UUID,
    p_personality TEXT
)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, brandedby
AS $$
    UPDATE brandedby.ai_twins
    SET
        personality_prompt          = p_personality,
        needs_personality_refresh   = false,
        personality_refreshed_at    = now()
    WHERE id = p_twin_id;
$$;

-- Restrict to service role only
REVOKE ALL ON FUNCTION public.brandedby_apply_twin_personality(UUID, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.brandedby_apply_twin_personality(UUID, TEXT) FROM anon;
REVOKE ALL ON FUNCTION public.brandedby_apply_twin_personality(UUID, TEXT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.brandedby_apply_twin_personality(UUID, TEXT) TO service_role;
