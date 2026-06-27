-- SECURITY FIX (P0): bot_* RLS policies were public, not service-role-scoped.
--
-- Migration 20260627031500 created (lines 51-53):
--   CREATE POLICY "service_role_all" ON bot_sessions  FOR ALL USING (true) WITH CHECK (true);
--   CREATE POLICY "service_role_all" ON bot_messages  FOR ALL USING (true) WITH CHECK (true);
--   CREATE POLICY "service_role_all" ON bot_heartbeats FOR ALL USING (true) WITH CHECK (true);
--
-- The name says "service_role" but there is NO `TO service_role` clause, so the policy
-- applies to PUBLIC (anon + authenticated). With USING(true)/WITH CHECK(true) that means
-- any anonymous PostgREST caller can read/write every bot row — including the CEO's private
-- Telegram conversation content in bot_messages. That is a data-exposure P0.
--
-- service_role bypasses RLS entirely, so the API keeps working with zero changes. The correct
-- posture is to DENY all non-service roles — mirrors public.processed_stripe_events
-- (20260330200000_stripe_webhook_idempotency.sql). Idempotent: safe whether or not the bad
-- policy was ever applied to prod.

DROP POLICY IF EXISTS "service_role_all" ON public.bot_sessions;
DROP POLICY IF EXISTS "service_role_all" ON public.bot_messages;
DROP POLICY IF EXISTS "service_role_all" ON public.bot_heartbeats;

-- Defense-in-depth: ensure RLS stays on (original migration enabled it; assert here too).
ALTER TABLE public.bot_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bot_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bot_heartbeats ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "deny_all_non_service" ON public.bot_sessions;
DROP POLICY IF EXISTS "deny_all_non_service" ON public.bot_messages;
DROP POLICY IF EXISTS "deny_all_non_service" ON public.bot_heartbeats;

CREATE POLICY "deny_all_non_service" ON public.bot_sessions
    FOR ALL TO authenticated, anon USING (false) WITH CHECK (false);
CREATE POLICY "deny_all_non_service" ON public.bot_messages
    FOR ALL TO authenticated, anon USING (false) WITH CHECK (false);
CREATE POLICY "deny_all_non_service" ON public.bot_heartbeats
    FOR ALL TO authenticated, anon USING (false) WITH CHECK (false);

COMMENT ON TABLE public.bot_messages IS
    'Telegram bot conversation log. service-role-only (RLS denies anon/authenticated). '
    'Fixed public-exposure P0 from migration 20260627031500.';
