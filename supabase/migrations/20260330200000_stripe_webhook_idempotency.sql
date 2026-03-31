-- Stripe webhook idempotency table (R-02 from Risk Register 2026-03-30)
-- Stripe guarantees "at-least-once" delivery — the same event_id can arrive multiple times
-- on network retries or Stripe-side retries after 5xx responses.
-- This table prevents double-processing subscription events (double grants, double cancellations).
--
-- Pattern: check event_id before processing; insert atomically inside webhook handler.
-- Webhook handler must:
--   1. SELECT id FROM processed_stripe_events WHERE event_id = $1
--   2. If found → return 200 (acknowledged, already processed)
--   3. If not found → process event → INSERT event_id (within same transaction if possible)
--
-- Retention: 90 days (Stripe keeps events for 30 days, 3x buffer for forensics).

CREATE TABLE IF NOT EXISTS public.processed_stripe_events (
    event_id    TEXT        PRIMARY KEY,  -- Stripe event ID (e.g. evt_1234...)
    event_type  TEXT        NOT NULL,     -- e.g. customer.subscription.created
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-purge events older than 90 days (pg_cron job or manual cleanup)
-- Index for purge query
CREATE INDEX IF NOT EXISTS idx_stripe_events_processed_at
    ON public.processed_stripe_events (processed_at);

-- RLS: only service_role can read/write — never exposed to authenticated users
ALTER TABLE public.processed_stripe_events ENABLE ROW LEVEL SECURITY;

-- No policies needed — service_role bypasses RLS.
-- Explicit deny for all other roles:
CREATE POLICY "deny_all_non_service"
    ON public.processed_stripe_events
    FOR ALL
    TO authenticated, anon
    USING (false);

COMMENT ON TABLE public.processed_stripe_events IS
    'Idempotency log for Stripe webhook events. Prevents double-processing on Stripe retries.';
