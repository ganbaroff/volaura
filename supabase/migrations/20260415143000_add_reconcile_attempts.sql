-- Add reconcile_attempts counter for aura_reconciler worker.
-- ghost-audit P0-2 follow-up: worker caps retries at MAX_RECONCILE_ATTEMPTS
-- and logs CRITICAL on give-up. Counter resets to 0 on successful RPC.

ALTER TABLE public.assessment_sessions
ADD COLUMN IF NOT EXISTS reconcile_attempts INT NOT NULL DEFAULT 0;

COMMENT ON COLUMN public.assessment_sessions.reconcile_attempts IS
  'ghost-audit P0-2: incremented by aura_reconciler each time upsert_aura_score RPC fails. Reset to 0 on success. Give-up threshold via AURA_RECONCILE_MAX_ATTEMPTS env var.';
