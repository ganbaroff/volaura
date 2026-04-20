-- Fix: atlas_learnings had USING(true) WITH CHECK(true) for public role,
-- allowing any unauthenticated user to read/write system data.
-- This table is backend-only (service_role writes via Telegram webhook).
-- Correct pattern: RLS enabled, no policies = deny-all client access.
-- service_role bypasses RLS by default in Supabase.

DROP POLICY IF EXISTS "Service role full access on atlas_learnings" ON public.atlas_learnings;

ALTER TABLE public.atlas_learnings ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.atlas_learnings FROM anon;
REVOKE ALL ON public.atlas_learnings FROM authenticated;
