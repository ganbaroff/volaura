-- Harden zeus governance layer — CRITICAL fixes from Session 93 security audit.
-- The previous migration 20260411193900_zeus_governance.sql revoked EXECUTE on
-- public.inspect_table_policies and public.log_governance_event from PUBLIC and
-- anon, but NOT from authenticated. Supabase exposes functions to authenticated
-- role by default, so any logged-in user could:
--   1. Read every RLS policy via inspect_table_policies() — full policy leak
--   2. Inject forged audit rows via log_governance_event() — trust destruction
-- Both holes caught by parallel security review right after the initial push.
--
-- Also:
--   - Explicitly GRANT USAGE ON SCHEMA zeus TO service_role so SECURITY DEFINER
--     functions can INSERT without relying on superuser search_path magic.
--   - Explicitly GRANT INSERT/SELECT on zeus.governance_events to service_role.
--   - Add unique index on reconciliation seed so re-runs do not duplicate the
--     row (the original ON CONFLICT DO NOTHING needed a unique constraint to
--     actually match against).

-- ── 1. Revoke from authenticated (CRITICAL) ─────────────────────────────
REVOKE EXECUTE ON FUNCTION public.inspect_table_policies(TEXT) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.log_governance_event(TEXT, TEXT, TEXT, TEXT, TEXT, JSONB) FROM authenticated;

-- ── 2. Grant explicit access to service_role ────────────────────────────
GRANT USAGE ON SCHEMA zeus TO service_role;
GRANT SELECT, INSERT ON zeus.governance_events TO service_role;
-- service_role must still be able to call the RPCs via PostgREST:
GRANT EXECUTE ON FUNCTION public.inspect_table_policies(TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.log_governance_event(TEXT, TEXT, TEXT, TEXT, TEXT, JSONB) TO service_role;

-- ── 3. Idempotent reconciliation seed ───────────────────────────────────
-- Ensure the Session 93 reconciliation event is present exactly once, even
-- if either migration is re-run. Keep the earliest row by created_at, drop
-- any later duplicates. Uses ORDER BY + LIMIT 1 because Postgres has no
-- MIN() aggregate over uuid type (first attempt: ERROR 42883 min(uuid)).
DELETE FROM zeus.governance_events
WHERE event_type = 'reconciliation'
  AND subject = 'perplexity_proposal_2026-04-11'
  AND id NOT IN (
      SELECT id FROM zeus.governance_events
      WHERE event_type = 'reconciliation'
        AND subject = 'perplexity_proposal_2026-04-11'
      ORDER BY created_at ASC
      LIMIT 1
  );

-- Unique partial index to prevent future duplicates of the reconciliation
-- row across migration re-runs. Other event types are free to repeat.
CREATE UNIQUE INDEX IF NOT EXISTS idx_governance_events_reconciliation_unique
ON zeus.governance_events(subject)
WHERE event_type = 'reconciliation' AND subject = 'perplexity_proposal_2026-04-11';

-- Log this hardening as its own governance event so the audit trail shows
-- the hole existed for ~10 minutes and was closed the moment the review
-- surfaced it.
INSERT INTO zeus.governance_events (event_type, severity, source, actor, subject, payload)
VALUES (
    'security_harden',
    'critical',
    'cto-hands',
    'claude-opus-4-6',
    'zeus_governance_rpcs',
    jsonb_build_object(
        'fixes', jsonb_build_array(
            'revoke_inspect_table_policies_from_authenticated',
            'revoke_log_governance_event_from_authenticated',
            'grant_usage_zeus_schema_to_service_role',
            'grant_select_insert_governance_events_to_service_role',
            'unique_index_reconciliation_seed'
        ),
        'source_review', 'parallel_security_audit',
        'window_of_exposure_minutes_approx', 10,
        'followup_commit_pending', true
    )
);
