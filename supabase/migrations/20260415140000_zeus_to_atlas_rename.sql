-- Rename zeus schema → atlas (CEO directive: ZEUS→ATLAS rebrand)
-- Safe: schema rename is transactional in PostgreSQL.
-- All objects inside (governance_events, indexes, RLS policies) move with the schema.

ALTER SCHEMA zeus RENAME TO atlas;

COMMENT ON SCHEMA atlas IS 'Atlas governance layer — audit log, policy introspection, agent coordination.';

-- Rename the zeus_publications table in public schema (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'zeus_publications') THEN
        ALTER TABLE public.zeus_publications RENAME TO atlas_publications;
    END IF;
END $$;

-- Update the log_governance_event function to reference atlas schema
CREATE OR REPLACE FUNCTION public.log_governance_event(
    p_event_type TEXT,
    p_severity TEXT DEFAULT 'INFO',
    p_source TEXT DEFAULT 'system',
    p_actor TEXT DEFAULT 'atlas',
    p_subject TEXT DEFAULT NULL,
    p_payload JSONB DEFAULT '{}'::JSONB
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, atlas
AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO atlas.governance_events (
        event_type, severity, source, actor, subject, payload
    ) VALUES (
        p_event_type, p_severity, p_source, p_actor, p_subject, p_payload
    ) RETURNING id INTO v_id;
    RETURN v_id;
END;
$$;

COMMENT ON FUNCTION public.log_governance_event IS
'Structured insert for atlas.governance_events. Service role only. Returns the new event id.';

-- Grant access to service_role on renamed schema
GRANT USAGE ON SCHEMA atlas TO service_role;
GRANT SELECT, INSERT ON atlas.governance_events TO service_role;

-- Log the rename itself
INSERT INTO atlas.governance_events (event_type, severity, source, actor, subject, payload)
VALUES (
    'schema_rename',
    'INFO',
    'migration',
    'atlas',
    'zeus_to_atlas_rename',
    '{"reason": "CEO directive: ZEUS→ATLAS rebrand", "migration": "20260415140000"}'::jsonb
);
