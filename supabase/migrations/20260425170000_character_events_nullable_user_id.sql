-- Allow user_id NULL on character_events for system-emitted events.
--
-- Pre-fix: error_watcher used sentinel UUID 00000000-0000-0000-0000-000000000000
-- which violated FK constraint character_events_user_id_fkey REFERENCES auth.users(id).
-- Every watcher emit_anomaly silently failed (caught by try/except in service).
-- All four watcher signals (stuck_sessions, orphan_events, error_rate, DLQ failures)
-- counted correctly but never landed in character_events for admin dashboard feed.
--
-- Fix: drop NOT NULL on user_id. System events pass NULL.
-- RLS read policy "Users can read own character events" USING (auth.uid() = user_id)
-- correctly evaluates NULL as falsy → system events stay invisible to user-client SELECT.
-- Service-role bypasses RLS for admin dashboard live feed.

ALTER TABLE public.character_events
  ALTER COLUMN user_id DROP NOT NULL;

COMMENT ON COLUMN public.character_events.user_id IS
  'NULL for system-emitted events (watcher anomalies, future system signals). Set for user-driven events.';
