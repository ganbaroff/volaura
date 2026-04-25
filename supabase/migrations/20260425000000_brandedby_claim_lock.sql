-- Migration: BrandedBy AI twin claim-lock for parallel refresh safety
-- Adds refresh_locked_at + refresh_lock_token to brandedby.ai_twins
-- Replaces brandedby_get_stale_twins with atomic brandedby_claim_stale_twins (FOR UPDATE SKIP LOCKED)
-- Updates brandedby_apply_twin_personality to clear lock on success
-- Adds brandedby_release_twin_lock for failure-path cleanup

-- 1. Add lock columns
ALTER TABLE brandedby.ai_twins
  ADD COLUMN IF NOT EXISTS refresh_locked_at  TIMESTAMPTZ DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS refresh_lock_token UUID        DEFAULT NULL;

-- 2. Atomic claim RPC — replaces brandedby_get_stale_twins
--    Claims oldest stale twins where lock is null or expired (>30 min)
--    Uses FOR UPDATE SKIP LOCKED so concurrent workers never claim the same twin
CREATE OR REPLACE FUNCTION public.brandedby_claim_stale_twins(
  p_limit            INT DEFAULT 10,
  p_lock_ttl_minutes INT DEFAULT 30
)
RETURNS TABLE(id UUID, user_id UUID, display_name TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, brandedby
AS $$
BEGIN
  RETURN QUERY
    UPDATE brandedby.ai_twins
    SET
      refresh_locked_at  = now(),
      refresh_lock_token = gen_random_uuid()
    WHERE brandedby.ai_twins.id IN (
      SELECT t.id
      FROM brandedby.ai_twins t
      WHERE t.needs_personality_refresh = true
        AND (
          t.refresh_locked_at IS NULL
          OR t.refresh_locked_at < now() - make_interval(mins => p_lock_ttl_minutes)
        )
      ORDER BY COALESCE(t.personality_refreshed_at, '1970-01-01'::TIMESTAMPTZ) ASC,
               t.created_at ASC
      LIMIT p_limit
      FOR UPDATE SKIP LOCKED
    )
    RETURNING
      brandedby.ai_twins.id,
      brandedby.ai_twins.user_id,
      brandedby.ai_twins.display_name;
END;
$$;

REVOKE ALL ON FUNCTION public.brandedby_claim_stale_twins(INT, INT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.brandedby_claim_stale_twins(INT, INT) FROM anon;
REVOKE ALL ON FUNCTION public.brandedby_claim_stale_twins(INT, INT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.brandedby_claim_stale_twins(INT, INT) TO service_role;

-- 3. Update apply RPC to also clear lock on success
CREATE OR REPLACE FUNCTION public.brandedby_apply_twin_personality(
  p_twin_id     UUID,
  p_personality TEXT
)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, brandedby
AS $$
  UPDATE brandedby.ai_twins
  SET
    personality_prompt        = p_personality,
    needs_personality_refresh = false,
    personality_refreshed_at  = now(),
    refresh_locked_at         = NULL,
    refresh_lock_token        = NULL
  WHERE id = p_twin_id;
$$;

REVOKE ALL ON FUNCTION public.brandedby_apply_twin_personality(UUID, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.brandedby_apply_twin_personality(UUID, TEXT) FROM anon;
REVOKE ALL ON FUNCTION public.brandedby_apply_twin_personality(UUID, TEXT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.brandedby_apply_twin_personality(UUID, TEXT) TO service_role;

-- 4. Release lock on failure — does NOT touch stale flag (twin stays stale, lock is freed)
CREATE OR REPLACE FUNCTION public.brandedby_release_twin_lock(p_twin_id UUID)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, brandedby
AS $$
  UPDATE brandedby.ai_twins
  SET
    refresh_locked_at  = NULL,
    refresh_lock_token = NULL
  WHERE id = p_twin_id;
$$;

REVOKE ALL ON FUNCTION public.brandedby_release_twin_lock(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.brandedby_release_twin_lock(UUID) FROM anon;
REVOKE ALL ON FUNCTION public.brandedby_release_twin_lock(UUID) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.brandedby_release_twin_lock(UUID) TO service_role;
