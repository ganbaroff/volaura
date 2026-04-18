-- Atlas Obligation System — deterministic, forgetting-resistant store
-- Source: memory/atlas/OBLIGATION-SYSTEM-SPEC-2026-04-18.md v2 (Doctor Strange v2 Gate 1 passed)
-- Three structural fixes from external adversarial review included:
--   1. UNIQUE partial index on (obligation_id, telegram_file_id) — dedupe webhook retries
--   2. pg_advisory_xact_lock in attach_proof — serialize concurrent writes
--   3. Ownership check in attach_proof body — SECURITY DEFINER bypasses RLS, auth lives in code

-- ─────────────────────────────────────────────────────────────────────────────
-- atlas_obligations — the deterministic deadline/obligation store
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.atlas_obligations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL UNIQUE,                        -- unique so seed is idempotent
    description TEXT,
    category TEXT NOT NULL,                            -- legal | tax | funding | launch | compliance | other
    deadline TIMESTAMPTZ,                              -- hard date; NULL for trigger-based
    trigger_event TEXT,                                -- natural-language trigger description
    consequence_if_missed TEXT NOT NULL,
    owner TEXT NOT NULL DEFAULT 'CEO',                 -- CEO | Atlas | tax-lawyer | both
    status TEXT NOT NULL DEFAULT 'open',               -- open | in_progress | completed | deferred | cancelled
    proof_required TEXT[] NOT NULL DEFAULT '{}',
    nag_schedule TEXT NOT NULL DEFAULT 'standard',     -- standard | aggressive | silent
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    deferred_until TIMESTAMPTZ,
    source TEXT,                                       -- provenance: "deadlines.md:L29" etc
    CONSTRAINT obligations_status_check
        CHECK (status IN ('open','in_progress','completed','deferred','cancelled')),
    CONSTRAINT obligations_owner_check
        CHECK (owner IN ('CEO','Atlas','tax-lawyer','both')),
    CONSTRAINT obligations_nag_check
        CHECK (nag_schedule IN ('standard','aggressive','silent'))
);

CREATE INDEX IF NOT EXISTS idx_obligations_open
    ON public.atlas_obligations (status, deadline)
    WHERE status IN ('open','in_progress');

CREATE INDEX IF NOT EXISTS idx_obligations_deferred
    ON public.atlas_obligations (deferred_until)
    WHERE status = 'deferred';

-- ─────────────────────────────────────────────────────────────────────────────
-- atlas_proofs — artifacts CEO attaches to close obligations
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.atlas_proofs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obligation_id UUID NOT NULL REFERENCES public.atlas_obligations(id) ON DELETE CASCADE,
    proof_type TEXT NOT NULL,                          -- photo | document | text | url | receipt
    telegram_file_id TEXT,
    telegram_file_unique_id TEXT,
    artifact_url TEXT,                                 -- Supabase Storage URL if migrated off Telegram
    text_content TEXT,                                 -- pasted tracking number / URL
    submitted_by TEXT NOT NULL,                        -- 'CEO' | 'Atlas' | 'automated'
    submitted_via TEXT NOT NULL,                       -- 'telegram' | 'admin-ui' | 'api' | 'migration'
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified BOOLEAN NOT NULL DEFAULT false,
    verified_by TEXT,
    verified_at TIMESTAMPTZ,
    CONSTRAINT proofs_type_check
        CHECK (proof_type IN ('photo','document','text','url','receipt'))
);

CREATE INDEX IF NOT EXISTS idx_proofs_obligation
    ON public.atlas_proofs (obligation_id);

-- v2 fix (OBJECTION 1): dedupe Telegram webhook retries — same file cannot attach twice
CREATE UNIQUE INDEX IF NOT EXISTS idx_proofs_tg_file_unique
    ON public.atlas_proofs (obligation_id, telegram_file_id)
    WHERE telegram_file_id IS NOT NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- atlas_nag_log — at-least-once semantics: row written AFTER Telegram 200
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.atlas_nag_log (
    id BIGSERIAL PRIMARY KEY,
    obligation_id UUID NOT NULL REFERENCES public.atlas_obligations(id) ON DELETE CASCADE,
    fired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    telegram_message_id BIGINT,
    telegram_chat_id BIGINT NOT NULL,
    cadence_tier TEXT NOT NULL,                        -- weekly | 2days | daily | 2x-daily | 4h
    days_until_deadline INTEGER,                       -- negative = past due
    ceo_responded BOOLEAN NOT NULL DEFAULT false,
    ceo_response_at TIMESTAMPTZ,
    CONSTRAINT nag_cadence_check
        CHECK (cadence_tier IN ('weekly','2days','daily','2x-daily','4h'))
);

CREATE INDEX IF NOT EXISTS idx_nag_log_obligation
    ON public.atlas_nag_log (obligation_id, fired_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- Row Level Security — service_role for Atlas cron, CEO by email claim for UI
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.atlas_obligations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.atlas_proofs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.atlas_nag_log ENABLE ROW LEVEL SECURITY;

-- atlas_obligations
CREATE POLICY "service_role_all_obligations" ON public.atlas_obligations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "ceo_read_obligations" ON public.atlas_obligations
    FOR SELECT TO authenticated
    USING (auth.jwt() ->> 'email' = 'ganbarov.y@gmail.com');

-- atlas_proofs
CREATE POLICY "service_role_all_proofs" ON public.atlas_proofs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "ceo_read_proofs" ON public.atlas_proofs
    FOR SELECT TO authenticated
    USING (auth.jwt() ->> 'email' = 'ganbarov.y@gmail.com');

-- atlas_nag_log
CREATE POLICY "service_role_all_nag_log" ON public.atlas_nag_log
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "ceo_read_nag_log" ON public.atlas_nag_log
    FOR SELECT TO authenticated
    USING (auth.jwt() ->> 'email' = 'ganbarov.y@gmail.com');

-- ─────────────────────────────────────────────────────────────────────────────
-- RPC: list_open_obligations — returns open/in_progress sorted by urgency
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.list_open_obligations()
RETURNS TABLE (
    id UUID,
    title TEXT,
    category TEXT,
    deadline TIMESTAMPTZ,
    days_until_deadline INTEGER,
    owner TEXT,
    status TEXT,
    proof_required TEXT[],
    attached_proof_count INTEGER,
    nag_schedule TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.title,
        o.category,
        o.deadline,
        CASE
            WHEN o.deadline IS NULL THEN NULL
            ELSE EXTRACT(DAY FROM (o.deadline - now()))::INTEGER
        END AS days_until_deadline,
        o.owner,
        o.status,
        o.proof_required,
        (
            SELECT count(DISTINCT p.proof_type)::INTEGER
            FROM public.atlas_proofs p
            WHERE p.obligation_id = o.id AND p.verified
        ) AS attached_proof_count,
        o.nag_schedule
    FROM public.atlas_obligations o
    WHERE o.status IN ('open','in_progress')
      AND (o.deferred_until IS NULL OR o.deferred_until < now())
    ORDER BY o.deadline ASC NULLS LAST;
END;
$$;

REVOKE ALL ON FUNCTION public.list_open_obligations() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.list_open_obligations() TO authenticated, service_role;

-- ─────────────────────────────────────────────────────────────────────────────
-- RPC: attach_proof — the authoritative close-with-evidence operation
-- v2: advisory lock + ownership check + idempotent ON CONFLICT + DISTINCT count
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.attach_proof(
    p_obligation_id UUID,
    p_proof_type TEXT,
    p_telegram_file_id TEXT DEFAULT NULL,
    p_text_content TEXT DEFAULT NULL,
    p_submitted_via TEXT DEFAULT 'telegram'
) RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_obligation public.atlas_obligations%ROWTYPE;
    v_proof_id UUID;
    v_distinct_proof_count INT;
    v_required_count INT;
    v_caller_email TEXT;
    v_is_service_role BOOLEAN;
BEGIN
    -- v2 fix (OBJECTION 1): serialize concurrent webhook retries on this obligation
    PERFORM pg_advisory_xact_lock(hashtext(p_obligation_id::text));

    SELECT * INTO v_obligation
        FROM public.atlas_obligations
        WHERE id = p_obligation_id
        FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Obligation not found' USING ERRCODE = 'P0002';
    END IF;

    IF v_obligation.status IN ('completed','cancelled') THEN
        -- idempotent: second webhook retry after close is no-op, not failure
        RETURN json_build_object(
            'obligation_id', p_obligation_id,
            'already_closed', true,
            'status', v_obligation.status
        );
    END IF;

    -- v2 fix (OBJECTION 3): ownership check in code — SECURITY DEFINER bypasses RLS
    v_caller_email := current_setting('request.jwt.claims', true)::json ->> 'email';
    v_is_service_role := (v_caller_email IS NULL);

    IF NOT v_is_service_role THEN
        IF v_obligation.owner IN ('CEO','both') THEN
            IF v_caller_email <> 'ganbarov.y@gmail.com' THEN
                RAISE EXCEPTION 'Not authorized: obligation owner=% but caller=%',
                    v_obligation.owner, v_caller_email USING ERRCODE = '42501';
            END IF;
        ELSIF v_obligation.owner = 'Atlas' THEN
            RAISE EXCEPTION 'Atlas-owned obligation, only cron/service_role may close'
                USING ERRCODE = '42501';
        ELSIF v_obligation.owner = 'tax-lawyer' THEN
            RAISE EXCEPTION 'tax-lawyer-owned obligation not supported yet (Phase 2)'
                USING ERRCODE = '42501';
        END IF;
    END IF;

    -- v2 fix (OBJECTION 1): idempotent insert — duplicate webhook retry returns existing row
    INSERT INTO public.atlas_proofs (
        obligation_id, proof_type, telegram_file_id, text_content,
        submitted_by, submitted_via, verified, verified_by, verified_at
    ) VALUES (
        p_obligation_id, p_proof_type, p_telegram_file_id, p_text_content,
        CASE WHEN v_is_service_role THEN 'Atlas' ELSE 'CEO' END,
        p_submitted_via, true,
        CASE WHEN v_is_service_role THEN 'Atlas' ELSE 'CEO' END,
        now()
    )
    ON CONFLICT (obligation_id, telegram_file_id) WHERE telegram_file_id IS NOT NULL
    DO UPDATE SET submitted_at = atlas_proofs.submitted_at
    RETURNING id INTO v_proof_id;

    -- v2 fix (OBJECTION 1): count DISTINCT proof_type, not raw rows
    SELECT count(DISTINCT proof_type)
        INTO v_distinct_proof_count
        FROM public.atlas_proofs
        WHERE obligation_id = p_obligation_id AND verified;

    v_required_count := coalesce(array_length(v_obligation.proof_required, 1), 1);

    IF v_distinct_proof_count >= v_required_count THEN
        UPDATE public.atlas_obligations
            SET status = 'completed', completed_at = now(), updated_at = now()
            WHERE id = p_obligation_id AND status IN ('open','in_progress');
    ELSE
        -- partial proof — mark in_progress if not already
        UPDATE public.atlas_obligations
            SET status = 'in_progress', updated_at = now()
            WHERE id = p_obligation_id AND status = 'open';
    END IF;

    RETURN json_build_object(
        'proof_id', v_proof_id,
        'obligation_id', p_obligation_id,
        'distinct_proofs', v_distinct_proof_count,
        'required', v_required_count,
        'closed', v_distinct_proof_count >= v_required_count
    );
END;
$$;

REVOKE ALL ON FUNCTION public.attach_proof FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.attach_proof TO authenticated, service_role;

-- ─────────────────────────────────────────────────────────────────────────────
-- RPC: defer_obligation — snooze until future date (no nag before deferred_until)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.defer_obligation(
    p_obligation_id UUID,
    p_defer_until TIMESTAMPTZ
) RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_caller_email TEXT;
    v_is_service_role BOOLEAN;
    v_obligation public.atlas_obligations%ROWTYPE;
BEGIN
    v_caller_email := current_setting('request.jwt.claims', true)::json ->> 'email';
    v_is_service_role := (v_caller_email IS NULL);

    SELECT * INTO v_obligation FROM public.atlas_obligations
        WHERE id = p_obligation_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Obligation not found' USING ERRCODE = 'P0002';
    END IF;

    IF NOT v_is_service_role AND v_obligation.owner IN ('CEO','both')
       AND v_caller_email <> 'ganbarov.y@gmail.com' THEN
        RAISE EXCEPTION 'Not authorized' USING ERRCODE = '42501';
    END IF;

    UPDATE public.atlas_obligations
        SET status = 'deferred', deferred_until = p_defer_until, updated_at = now()
        WHERE id = p_obligation_id;

    RETURN json_build_object('obligation_id', p_obligation_id, 'deferred_until', p_defer_until);
END;
$$;

REVOKE ALL ON FUNCTION public.defer_obligation FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.defer_obligation TO authenticated, service_role;

-- ─────────────────────────────────────────────────────────────────────────────
-- RPC: cancel_obligation — CEO-only, terminal state
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.cancel_obligation(
    p_obligation_id UUID,
    p_reason TEXT DEFAULT NULL
) RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_caller_email TEXT;
    v_is_service_role BOOLEAN;
    v_obligation public.atlas_obligations%ROWTYPE;
BEGIN
    v_caller_email := current_setting('request.jwt.claims', true)::json ->> 'email';
    v_is_service_role := (v_caller_email IS NULL);

    SELECT * INTO v_obligation FROM public.atlas_obligations
        WHERE id = p_obligation_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Obligation not found' USING ERRCODE = 'P0002';
    END IF;

    IF NOT v_is_service_role AND v_obligation.owner IN ('CEO','both')
       AND v_caller_email <> 'ganbarov.y@gmail.com' THEN
        RAISE EXCEPTION 'Not authorized' USING ERRCODE = '42501';
    END IF;

    UPDATE public.atlas_obligations
        SET status = 'cancelled',
            updated_at = now(),
            description = coalesce(description, '') ||
                          E'\n\n[CANCELLED ' || now()::TEXT || ']: ' || coalesce(p_reason, 'no reason given')
        WHERE id = p_obligation_id;

    RETURN json_build_object('obligation_id', p_obligation_id, 'status', 'cancelled');
END;
$$;

REVOKE ALL ON FUNCTION public.cancel_obligation FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.cancel_obligation TO authenticated, service_role;

-- ─────────────────────────────────────────────────────────────────────────────
-- RPC: try_claim_obligation_nag — DB-layer single-writer for the nag cron
-- (v2 fix OBJECTION 2: belt-and-braces around workflow concurrency group)
-- ─────────────────────────────────────────────────────────────────────────────
-- Returns TRUE if the caller successfully claimed the nag slot (no other worker
-- holds it AND no nag row was inserted within p_cooldown_minutes). Returns
-- FALSE otherwise. Uses session-level pg_try_advisory_lock (non-blocking,
-- released when the connection closes) so it is safe to call from supabase-py
-- which does not expose explicit transactions.

CREATE OR REPLACE FUNCTION public.try_claim_obligation_nag(
    p_obligation_id UUID,
    p_cooldown_minutes INT DEFAULT 60
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_lock_key BIGINT;
    v_got_lock BOOLEAN;
    v_recent_count INT;
BEGIN
    -- Deterministic 64-bit lock key from the obligation UUID, scoped with 'nag:' prefix
    v_lock_key := hashtextextended('nag:' || p_obligation_id::text, 0);
    v_got_lock := pg_try_advisory_lock(v_lock_key);
    IF NOT v_got_lock THEN
        RETURN FALSE;
    END IF;

    -- Cooldown window check — prevents double-nag inside the cadence tier window
    SELECT count(*) INTO v_recent_count
        FROM public.atlas_nag_log
        WHERE obligation_id = p_obligation_id
          AND fired_at > now() - (p_cooldown_minutes || ' minutes')::INTERVAL;

    IF v_recent_count > 0 THEN
        PERFORM pg_advisory_unlock(v_lock_key);
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$;

REVOKE ALL ON FUNCTION public.try_claim_obligation_nag FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.try_claim_obligation_nag TO service_role;


CREATE OR REPLACE FUNCTION public.release_obligation_nag_lock(
    p_obligation_id UUID
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_lock_key BIGINT;
BEGIN
    v_lock_key := hashtextextended('nag:' || p_obligation_id::text, 0);
    RETURN pg_advisory_unlock(v_lock_key);
END;
$$;

REVOKE ALL ON FUNCTION public.release_obligation_nag_lock FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.release_obligation_nag_lock TO service_role;


-- ─────────────────────────────────────────────────────────────────────────────
-- RPC: log_obligation_nag — at-least-once write AFTER Telegram 200
-- (v2 fix OBJECTION 2: do NOT log optimistically; only log on delivered send)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.log_obligation_nag(
    p_obligation_id UUID,
    p_telegram_chat_id BIGINT,
    p_telegram_message_id BIGINT DEFAULT NULL,
    p_cadence_tier TEXT DEFAULT 'weekly',
    p_days_until_deadline INT DEFAULT NULL
) RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_id BIGINT;
BEGIN
    INSERT INTO public.atlas_nag_log (
        obligation_id, telegram_chat_id, telegram_message_id,
        cadence_tier, days_until_deadline
    ) VALUES (
        p_obligation_id, p_telegram_chat_id, p_telegram_message_id,
        p_cadence_tier, p_days_until_deadline
    ) RETURNING id INTO v_id;
    RETURN v_id;
END;
$$;

REVOKE ALL ON FUNCTION public.log_obligation_nag FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.log_obligation_nag TO service_role;
