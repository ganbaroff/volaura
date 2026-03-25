-- HIGH-01: Optimistic locking to prevent race conditions on concurrent answer submissions.
-- answer_version increments with each answer. Update uses WHERE answer_version = N,
-- so a concurrent duplicate request will match 0 rows and fail safely.

ALTER TABLE public.assessment_sessions
    ADD COLUMN IF NOT EXISTS answer_version INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN public.assessment_sessions.answer_version IS
    'Optimistic lock counter. Incremented on each answer submission. Used in WHERE clause to prevent race conditions.';
