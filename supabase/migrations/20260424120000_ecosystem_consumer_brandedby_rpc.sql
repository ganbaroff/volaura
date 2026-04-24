-- ecosystem_mark_twin_stale — cross-schema RPC for ecosystem consumer
--
-- Problem: brandedby schema is NOT exposed via PostgREST (pgrst.db_schemas only lists
-- public + graphql_public). Direct db.schema("brandedby").table("ai_twins") calls from
-- the Python service client fail with PGRST106: Invalid schema.
--
-- Fix: SECURITY DEFINER function in public schema, runs as postgres, can write to
-- brandedby.ai_twins directly.  Called by ecosystem_consumer._handle_brandedby_event().
--
-- Returns: INT — count of rows updated (0 = user has no twin yet, not an error)

CREATE OR REPLACE FUNCTION public.ecosystem_mark_twin_stale(
    p_user_id UUID,
    p_reason  TEXT
)
RETURNS INT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, brandedby
AS $$
DECLARE
    v_updated INT;
BEGIN
    UPDATE brandedby.ai_twins
       SET needs_personality_refresh  = true,
           personality_refresh_reason = p_reason
     WHERE user_id = p_user_id;

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated;
END;
$$;

-- Only service_role may call this — never authenticated users
GRANT EXECUTE ON FUNCTION public.ecosystem_mark_twin_stale(UUID, TEXT) TO service_role;
REVOKE EXECUTE ON FUNCTION public.ecosystem_mark_twin_stale(UUID, TEXT) FROM PUBLIC;

COMMENT ON FUNCTION public.ecosystem_mark_twin_stale(UUID, TEXT) IS
    'Called by ecosystem_consumer when aura_updated or badge_tier_changed event arrives. '
    'Marks ai_twins.needs_personality_refresh = true so next refresh_personality call '
    'regenerates the twin with the updated AURA profile. '
    'Returns row count (0 = user not yet in BrandedBy — not an error).';
