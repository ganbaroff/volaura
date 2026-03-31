-- Add pending_aura_sync flag to assessment_sessions
--
-- WHY: If upsert_aura_score RPC fails after session completion (Supabase cold
-- start, network blip, wrong param type), the session is already marked
-- "completed" and cannot be retried safely via complete_assessment (early-return
-- path fires). This flag lets CTO query affected rows and manually trigger
-- re-sync without touching completed session data.
--
-- QUERY TO FIND AFFECTED SESSIONS:
--   SELECT id, user_id, competency_id, completed_at
--   FROM assessment_sessions
--   WHERE pending_aura_sync = TRUE
--   ORDER BY completed_at DESC;

ALTER TABLE public.assessment_sessions
ADD COLUMN IF NOT EXISTS pending_aura_sync BOOLEAN DEFAULT FALSE;

-- Index: CTO recovery query needs to be fast even at scale
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_pending_aura_sync
ON public.assessment_sessions (pending_aura_sync)
WHERE pending_aura_sync = TRUE;

-- No RLS change needed: pending_aura_sync is written by service-role only
-- (db_admin client in complete_assessment). Users never read or write it.
