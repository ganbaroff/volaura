-- Recurring-symptoms watchdog — Sentry regression receiver.
--
-- Research: docs/research/recurring-symptoms-watchdog/summary.md
-- Pattern ref: INC-017 (Google OAuth silently broken 11 days), INC-001/INC-008
-- (Telegram cascade fix-of-fix), INC-002 (swarm archive cascade).
--
-- Contract:
--   One row per distinct Sentry issue fingerprint. Webhook upserts on every
--   regression event, bumping occurrences and last_seen. Merge-gate CI workflow
--   reads needs_rca_label_set to decide whether a `memory/decisions/*.md`
--   RCA file is required on any PR that touches a related_pr_urls entry.
--
-- Idempotent: CREATE ... IF NOT EXISTS + DROP POLICY IF EXISTS. Safe to re-apply.
-- No UPDATE/DELETE policies — rows are mutated only via service_role (webhook
-- runs with service key). authenticated/anon have no access.

BEGIN;

CREATE TABLE IF NOT EXISTS public.recurring_symptom_events (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint_hash     text NOT NULL,
    source_product       text NOT NULL,
    sentry_issue_id      text,
    sentry_project       text,
    title                text,
    culprit              text,
    commit_sha           text,
    first_seen           timestamptz NOT NULL DEFAULT now(),
    last_seen            timestamptz NOT NULL DEFAULT now(),
    occurrences          integer NOT NULL DEFAULT 1,
    related_pr_urls      jsonb NOT NULL DEFAULT '[]'::jsonb,
    needs_rca_label_set  boolean NOT NULL DEFAULT false,
    gh_issue_url         text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT recurring_symptom_events_source_product_chk CHECK (source_product IN (
        'volaura', 'mindshift', 'lifesim', 'brandedby', 'zeus', 'unknown'
    )),
    CONSTRAINT recurring_symptom_events_fingerprint_unique UNIQUE (fingerprint_hash, source_product)
);

CREATE INDEX IF NOT EXISTS recurring_symptom_events_last_seen_idx
    ON public.recurring_symptom_events (last_seen DESC);

CREATE INDEX IF NOT EXISTS recurring_symptom_events_needs_rca_idx
    ON public.recurring_symptom_events (needs_rca_label_set)
    WHERE needs_rca_label_set = true;

ALTER TABLE public.recurring_symptom_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recurring_symptom_events FORCE ROW LEVEL SECURITY;

-- No anon/authenticated policies: service_role bypasses RLS and is the only
-- writer. This table is operational infra, not user-facing.

COMMIT;
