-- Ecosystem-wide GDPR Art.22 + EU AI Act + AZ PDPA compliance schema.
-- Spans all 5 products: volaura, mindshift, lifesim, brandedby, zeus.
-- Each row carries source_product so any product can write via its own
-- service_role without forking this schema.
--
-- Research: docs/research/gdpr-article-22/summary.md + raw.md
-- RLS baseline: 20260415210000_force_row_level_security.sql (FORCE on every table).
-- No UPDATE / DELETE policies on consent_events or automated_decision_log —
-- those ledgers are append-only by construction. service_role bypasses RLS
-- anyway (rolbypassrls=true), so admin mutations are still possible but
-- never via the anon/authenticated roles even under SQL injection.
--
-- Idempotent: CREATE ... IF NOT EXISTS throughout; policies dropped-if-exists
-- then recreated so re-running the migration is safe.

BEGIN;

-- -----------------------------------------------------------------------
-- Shared CHECK: source_product across all 5 ecosystem products.
-- -----------------------------------------------------------------------
-- Codified as CHECK constraints on each table (Postgres has no
-- schema-level ENUM reuse across tables without creating a TYPE; using
-- a TYPE makes future additions a schema migration, CHECK is easier
-- to amend via ALTER TABLE DROP/ADD CONSTRAINT).

-- =======================================================================
-- 1. policy_versions — immutable log of published policy/terms/consent text
-- =======================================================================
CREATE TABLE IF NOT EXISTS public.policy_versions (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type     text NOT NULL,
    version           text NOT NULL,
    locale            text NOT NULL,
    content_markdown  text NOT NULL,
    content_sha256    text NOT NULL,
    effective_from    timestamptz NOT NULL,
    superseded_by     uuid REFERENCES public.policy_versions(id),
    created_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT policy_versions_document_type_chk CHECK (document_type IN (
        'privacy_policy',
        'terms_of_service',
        'ai_decision_notice',
        'cookie_policy',
        'data_processing_agreement'
    )),
    CONSTRAINT policy_versions_locale_chk CHECK (locale IN ('az','en','ru')),
    CONSTRAINT policy_versions_unique UNIQUE (document_type, version, locale)
);

-- Auto-hash content_sha256 on insert/update to prevent drift.
CREATE OR REPLACE FUNCTION public.policy_versions_hash_content()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.content_sha256 := encode(digest(NEW.content_markdown, 'sha256'), 'hex');
    RETURN NEW;
END;
$$;

-- digest() requires pgcrypto.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DROP TRIGGER IF EXISTS trg_policy_versions_hash ON public.policy_versions;
CREATE TRIGGER trg_policy_versions_hash
    BEFORE INSERT OR UPDATE OF content_markdown ON public.policy_versions
    FOR EACH ROW EXECUTE FUNCTION public.policy_versions_hash_content();

ALTER TABLE public.policy_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.policy_versions FORCE  ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "policy_versions_public_read"    ON public.policy_versions;
DROP POLICY IF EXISTS "policy_versions_no_anon_write"  ON public.policy_versions;

-- Everyone (incl. anon) can read — this is published law-of-the-land.
CREATE POLICY "policy_versions_public_read"
    ON public.policy_versions
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- No INSERT/UPDATE/DELETE policy => anon/authenticated blocked.
-- service_role bypasses RLS via BYPASSRLS role attribute.

-- =======================================================================
-- 2. consent_events — append-only consent ledger
-- =======================================================================
CREATE TABLE IF NOT EXISTS public.consent_events (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    source_product      text NOT NULL,
    event_type          text NOT NULL,
    policy_version_id   uuid NOT NULL REFERENCES public.policy_versions(id),
    consent_scope       jsonb NOT NULL DEFAULT '{}'::jsonb,
    ip_address          inet,
    user_agent          text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT consent_events_source_product_chk CHECK (source_product IN (
        'volaura','mindshift','lifesim','brandedby','zeus'
    )),
    CONSTRAINT consent_events_event_type_chk CHECK (event_type IN (
        'consent_given','consent_withdrawn','consent_updated','policy_reaccepted'
    ))
);

CREATE INDEX IF NOT EXISTS consent_events_user_created_idx
    ON public.consent_events (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS consent_events_product_created_idx
    ON public.consent_events (source_product, created_at DESC);

ALTER TABLE public.consent_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consent_events FORCE  ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "consent_events_owner_read" ON public.consent_events;

CREATE POLICY "consent_events_owner_read"
    ON public.consent_events
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- No INSERT / UPDATE / DELETE policies: append-only via service_role only.

-- =======================================================================
-- 3. automated_decision_log — every AI-Act-relevant decision
-- =======================================================================
CREATE TABLE IF NOT EXISTS public.automated_decision_log (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid NOT NULL REFERENCES auth.users(id),
    source_product      text NOT NULL,
    decision_type       text NOT NULL,
    decision_output     jsonb NOT NULL,
    algorithm_version   text NOT NULL,
    model_inputs_hash   text,
    explanation_text    text,
    human_reviewable    bool NOT NULL DEFAULT true,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT automated_decision_log_source_product_chk CHECK (source_product IN (
        'volaura','mindshift','lifesim','brandedby','zeus'
    ))
);

CREATE INDEX IF NOT EXISTS automated_decision_log_user_created_idx
    ON public.automated_decision_log (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS automated_decision_log_product_type_idx
    ON public.automated_decision_log (source_product, decision_type);

ALTER TABLE public.automated_decision_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automated_decision_log FORCE  ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "automated_decision_log_owner_read" ON public.automated_decision_log;

CREATE POLICY "automated_decision_log_owner_read"
    ON public.automated_decision_log
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Append-only: no INSERT/UPDATE/DELETE policies => service_role only.

-- =======================================================================
-- 4. human_review_requests — Art.22 contest / review tickets
-- =======================================================================
CREATE TABLE IF NOT EXISTS public.human_review_requests (
    id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                  uuid NOT NULL REFERENCES auth.users(id),
    automated_decision_id    uuid NOT NULL REFERENCES public.automated_decision_log(id),
    source_product           text NOT NULL,
    request_reason           text NOT NULL,
    requested_at             timestamptz NOT NULL DEFAULT now(),
    sla_deadline             timestamptz NOT NULL,
    status                   text NOT NULL DEFAULT 'pending',
    resolved_at              timestamptz,
    resolution_notes         text,
    reviewer_user_id         uuid REFERENCES auth.users(id),
    CONSTRAINT human_review_requests_source_product_chk CHECK (source_product IN (
        'volaura','mindshift','lifesim','brandedby','zeus'
    )),
    CONSTRAINT human_review_requests_status_chk CHECK (status IN (
        'pending','in_review','resolved_uphold','resolved_overturn','escalated_to_authority'
    ))
);

CREATE INDEX IF NOT EXISTS human_review_requests_status_deadline_idx
    ON public.human_review_requests (status, sla_deadline);
CREATE INDEX IF NOT EXISTS human_review_requests_user_idx
    ON public.human_review_requests (user_id, requested_at DESC);

-- Trigger: enforce sla_deadline = requested_at + 30 days on insert.
CREATE OR REPLACE FUNCTION public.human_review_requests_set_sla()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.requested_at IS NULL THEN
        NEW.requested_at := now();
    END IF;
    NEW.sla_deadline := NEW.requested_at + interval '30 days';
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_human_review_requests_sla ON public.human_review_requests;
CREATE TRIGGER trg_human_review_requests_sla
    BEFORE INSERT ON public.human_review_requests
    FOR EACH ROW EXECUTE FUNCTION public.human_review_requests_set_sla();

ALTER TABLE public.human_review_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.human_review_requests FORCE  ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "human_review_requests_owner_read"   ON public.human_review_requests;
DROP POLICY IF EXISTS "human_review_requests_owner_insert" ON public.human_review_requests;
DROP POLICY IF EXISTS "human_review_requests_reviewer_read" ON public.human_review_requests;

CREATE POLICY "human_review_requests_owner_read"
    ON public.human_review_requests
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "human_review_requests_owner_insert"
    ON public.human_review_requests
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- Reviewers (anyone who self-assigned) can read the ticket they review.
CREATE POLICY "human_review_requests_reviewer_read"
    ON public.human_review_requests
    FOR SELECT
    TO authenticated
    USING (reviewer_user_id = auth.uid());

COMMIT;
