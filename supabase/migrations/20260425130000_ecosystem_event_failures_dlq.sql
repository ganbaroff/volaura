-- Dead-letter table for ecosystem consumer
-- Captures events whose downstream handler raised, so cursor can keep moving
-- without losing the event. Failed events are visible, countable, replayable.

CREATE TABLE IF NOT EXISTS public.ecosystem_event_failures (
  id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  product         TEXT         NOT NULL,
  event_id        UUID         NOT NULL,
  user_id         UUID,
  event_type      TEXT,
  attempts        INT          NOT NULL DEFAULT 1,
  first_failed_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
  last_failed_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
  last_error      TEXT,
  resolved_at     TIMESTAMPTZ,
  CONSTRAINT ecosystem_event_failures_product_event_uniq UNIQUE (product, event_id)
);

CREATE INDEX IF NOT EXISTS idx_ecosystem_failures_unresolved
  ON public.ecosystem_event_failures (product, last_failed_at)
  WHERE resolved_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_ecosystem_failures_event_id
  ON public.ecosystem_event_failures (event_id);

ALTER TABLE public.ecosystem_event_failures ENABLE ROW LEVEL SECURITY;

-- No public policies — service-role bypasses RLS for INSERT/UPDATE.
-- Read access through admin endpoints only.

-- Counter on cursor for fast health checks
ALTER TABLE public.ecosystem_event_cursors
  ADD COLUMN IF NOT EXISTS events_failed_total INT NOT NULL DEFAULT 0;

-- Atomic upsert RPC: increments attempts on conflict, refreshes last_failed_at.
CREATE OR REPLACE FUNCTION public.ecosystem_record_event_failure(
  p_product    TEXT,
  p_event_id   UUID,
  p_user_id    UUID,
  p_event_type TEXT,
  p_error      TEXT
)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  INSERT INTO public.ecosystem_event_failures
    (product, event_id, user_id, event_type, last_error)
  VALUES
    (p_product, p_event_id, p_user_id, p_event_type, left(coalesce(p_error,''), 1000))
  ON CONFLICT (product, event_id) DO UPDATE SET
    attempts        = public.ecosystem_event_failures.attempts + 1,
    last_failed_at  = now(),
    last_error      = left(coalesce(EXCLUDED.last_error, public.ecosystem_event_failures.last_error), 1000),
    resolved_at     = NULL;
$$;

REVOKE ALL ON FUNCTION public.ecosystem_record_event_failure(TEXT, UUID, UUID, TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.ecosystem_record_event_failure(TEXT, UUID, UUID, TEXT, TEXT) FROM anon;
REVOKE ALL ON FUNCTION public.ecosystem_record_event_failure(TEXT, UUID, UUID, TEXT, TEXT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.ecosystem_record_event_failure(TEXT, UUID, UUID, TEXT, TEXT) TO service_role;

-- Mark resolved RPC for replay tooling
CREATE OR REPLACE FUNCTION public.ecosystem_resolve_event_failure(
  p_product  TEXT,
  p_event_id UUID
)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  UPDATE public.ecosystem_event_failures
  SET resolved_at = now()
  WHERE product = p_product
    AND event_id = p_event_id
    AND resolved_at IS NULL;
$$;

REVOKE ALL ON FUNCTION public.ecosystem_resolve_event_failure(TEXT, UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.ecosystem_resolve_event_failure(TEXT, UUID) FROM anon;
REVOKE ALL ON FUNCTION public.ecosystem_resolve_event_failure(TEXT, UUID) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.ecosystem_resolve_event_failure(TEXT, UUID) TO service_role;
