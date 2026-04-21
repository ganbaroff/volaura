-- Relax character_events CHECK constraints for event bus growth
--
-- Original chk_event_type (Sprint A0, 20260327000032) allowed only 8 event types.
-- The ecosystem now emits 20+ types (lifesim_*, eventshift_*, assessment_completed,
-- aura_updated, badge_tier_changed, consent_given, metric_anomaly_*).
-- Postgres logs show repeated "violates check constraint chk_event_type" errors
-- on production (2026-04-19).
--
-- Fix: replace enum-list with format validation. Event bus should not need a
-- migration for every new event type.

BEGIN;

-- 1. Drop the rigid enum constraint
ALTER TABLE public.character_events DROP CONSTRAINT IF EXISTS chk_event_type;

-- 2. Add format-based constraint: lowercase snake_case, 2-64 chars
ALTER TABLE public.character_events
    ADD CONSTRAINT chk_event_type_format
    CHECK (event_type ~ '^[a-z][a-z0-9_]{1,63}$');

-- 3. Add 'eventshift' to source_product allowlist
ALTER TABLE public.character_events DROP CONSTRAINT IF EXISTS chk_source_product;

ALTER TABLE public.character_events
    ADD CONSTRAINT chk_source_product CHECK (source_product IN (
        'volaura', 'mindshift', 'lifesim', 'brandedby', 'eventshift'
    ));

-- 4. Verify: no existing rows violate the new constraints
DO $$
DECLARE
    bad_type_count INT;
    bad_source_count INT;
BEGIN
    SELECT count(*) INTO bad_type_count
    FROM public.character_events
    WHERE NOT (event_type ~ '^[a-z][a-z0-9_]{1,63}$');

    SELECT count(*) INTO bad_source_count
    FROM public.character_events
    WHERE source_product NOT IN ('volaura', 'mindshift', 'lifesim', 'brandedby', 'eventshift');

    IF bad_type_count > 0 THEN
        RAISE EXCEPTION 'Found % rows with invalid event_type format', bad_type_count;
    END IF;

    IF bad_source_count > 0 THEN
        RAISE EXCEPTION 'Found % rows with invalid source_product', bad_source_count;
    END IF;
END $$;

COMMIT;
