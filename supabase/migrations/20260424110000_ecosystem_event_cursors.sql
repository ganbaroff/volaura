-- Ecosystem event cursors — per-product progress tracking for character_events consumption.
--
-- Problem: character_events is written by producers (VOLAURA emits assessment_completed,
-- aura_updated, badge_tier_changed). No downstream product has a server-side loop that
-- reads and reacts to these events. This migration adds the infrastructure for a
-- cursor-based consumer pattern.
--
-- Design:
--   - One row per downstream product (brandedby, mindshift, lifesim, atlas)
--   - last_event_id: UUID of the most recently processed character_events row
--   - Processor selects: WHERE id > last_event_id ORDER BY id
--   - After processing a batch, cursor is advanced to the highest id in the batch
--   - Idempotent: re-processing the same event_id is a no-op (cursor check)
--
-- The brandedby row is seeded so the first run processes from the beginning.
-- Other products can be added as their handlers are implemented.

CREATE TABLE IF NOT EXISTS public.ecosystem_event_cursors (
    product                 TEXT        PRIMARY KEY,
    last_event_id           UUID,                           -- NULL = start from beginning
    last_processed_at       TIMESTAMPTZ,
    events_processed_total  INT         NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.ecosystem_event_cursors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ecosystem_event_cursors FORCE ROW LEVEL SECURITY;

-- Service role only — never exposed to authenticated users
CREATE POLICY "Service role manages cursors"
    ON public.ecosystem_event_cursors
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Seed the brandedby cursor (starts from beginning — will process all existing events)
INSERT INTO public.ecosystem_event_cursors (product)
    VALUES ('brandedby')
    ON CONFLICT (product) DO NOTHING;

-- Also add needs_personality_refresh to ai_twins so the consumer can mark stale twins.
-- A twin is "stale" when AURA was updated or badge tier changed after last personality gen.
ALTER TABLE brandedby.ai_twins
    ADD COLUMN IF NOT EXISTS needs_personality_refresh BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS personality_refresh_reason TEXT,   -- e.g. 'aura_updated', 'badge_tier_changed'
    ADD COLUMN IF NOT EXISTS personality_refreshed_at TIMESTAMPTZ;

COMMENT ON COLUMN brandedby.ai_twins.needs_personality_refresh IS
    'Set to true by ecosystem_consumer when aura_updated or badge_tier_changed event arrives. '
    'Cleared by refresh_personality endpoint after successful regeneration.';
