-- Close the two latent owner-bypass holes flagged by rls-tests (CX-F11):
-- lifesim_events (created 20260416, missed by both FORCE catch-up migrations)
-- ecosystem_event_failures (created 20260425, after the last catch-up).
-- Both had RLS ENABLED but not FORCED, so the table owner bypassed policies.

ALTER TABLE public.lifesim_events FORCE ROW LEVEL SECURITY;
ALTER TABLE public.ecosystem_event_failures FORCE ROW LEVEL SECURITY;
