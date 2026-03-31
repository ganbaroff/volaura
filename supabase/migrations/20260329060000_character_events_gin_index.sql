-- Migration: GIN index on character_events.payload
-- Purpose: Speed up JSONB queries on character_events (e.g. payload->>'skill_slug', event_type filters)
-- Trigger: LAUNCH-BLOCKERS.md #17 — needed before 1000 users
-- Cost: ~10ms to apply on empty table at launch; negligible storage overhead

CREATE INDEX IF NOT EXISTS idx_character_events_payload_gin
  ON public.character_events USING GIN (payload);

-- Also index by user + event_type for the most common query pattern:
-- SELECT * FROM character_events WHERE user_id = $1 AND event_type = 'crystal_earned'
CREATE INDEX IF NOT EXISTS idx_character_events_user_type
  ON public.character_events (user_id, event_type);
