-- Migration: evaluation_queue — async re-evaluation of keyword_fallback answers
--
-- WHY: keyword_fallback produces vocabulary scores, not competency scores.
-- ADR-010: these are flagged evaluation_mode="degraded" in the evaluation_log.
-- This queue holds degraded answers so a background task can re-evaluate them
-- via Gemini once the LLM recovers. The user gets a provisional score immediately;
-- the silent update improves accuracy when the queue drains.
--
-- SCOPE: beta (~100 users). No Redis, no Celery. Simple Postgres polling loop.
-- Retry cap at 3 to avoid hammering Gemini on a hard failure. Dead items (max
-- retries exceeded, or older than 7 days) are left in status='failed' for audit.

CREATE TABLE public.evaluation_queue (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source tracing — needed to write the result back
    session_id       UUID NOT NULL REFERENCES public.assessment_sessions(id) ON DELETE CASCADE,
    volunteer_id     UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    question_id      UUID NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    competency_slug  TEXT NOT NULL,

    -- Payload for re-evaluation (stored so we never re-fetch from DB during eval)
    question_en      TEXT NOT NULL,
    answer_text      TEXT NOT NULL,
    expected_concepts JSONB NOT NULL DEFAULT '[]',

    -- Degraded score that is currently applied — stored so reconciliation can
    -- tell whether the AURA score changed and log the delta.
    degraded_score   FLOAT NOT NULL,

    -- Queue state machine: pending → processing → done | failed
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'processing', 'done', 'failed')),
    retry_count      INT NOT NULL DEFAULT 0,
    max_retries      INT NOT NULL DEFAULT 3,

    -- Timestamps
    queued_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at       TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ,

    -- Result written back after successful re-evaluation
    llm_score        FLOAT,           -- composite score from LLM
    llm_model        TEXT,            -- e.g. "gemini-2.5-flash"
    score_delta      FLOAT,           -- llm_score - degraded_score (signed)
    error_detail     TEXT             -- last error message (for failed items)
);

-- Poll query: background task fetches pending items ordered by queued_at
CREATE INDEX idx_evaluation_queue_pending
    ON public.evaluation_queue (queued_at ASC)
    WHERE status = 'pending';

-- Cleanup query: find stale processing items (crashed worker) to reset
CREATE INDEX idx_evaluation_queue_processing
    ON public.evaluation_queue (started_at ASC)
    WHERE status = 'processing';

-- Audit query: per-volunteer view of queued items
CREATE INDEX idx_evaluation_queue_volunteer
    ON public.evaluation_queue (volunteer_id, queued_at DESC);

-- RLS: volunteers can only read their own queue items (not write — service role only)
ALTER TABLE public.evaluation_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Volunteers can read own queue items"
    ON public.evaluation_queue FOR SELECT
    USING (auth.uid() = volunteer_id);

-- Service role (backend) has full access via SECURITY DEFINER RPCs and db_admin client.
-- No INSERT/UPDATE policy for anon/authenticated — all mutations go through service role.
