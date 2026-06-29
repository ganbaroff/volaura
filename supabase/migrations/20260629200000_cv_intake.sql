-- Sprint 1: CV Truth Machine — cv_intake table for parsed CVs and extracted claims.
--
-- Stores extracted TEXT and structured CLAIMS, NOT the original file (GDPR minimization).
-- Claims are later used to generate experience interview questions (Sprint 2).

CREATE TABLE IF NOT EXISTS public.cv_intake (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    file_hash   TEXT NOT NULL,         -- SHA-256 prefix of cv_text for dedup
    cv_text     TEXT NOT NULL,         -- extracted plain text (max ~50k chars)
    claims      JSONB NOT NULL DEFAULT '{}',  -- ClaimExtractionResult: {claims: [...], meta: {...}}
    status      TEXT NOT NULL DEFAULT 'extracted' CHECK (status IN ('extracted', 'questions_generated', 'interview_complete')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for dedup lookup (same user + same text hash = skip re-extraction)
CREATE INDEX IF NOT EXISTS idx_cv_intake_user_hash ON public.cv_intake(user_id, file_hash);

-- Index for listing user's CVs
CREATE INDEX IF NOT EXISTS idx_cv_intake_user_id ON public.cv_intake(user_id);

-- RLS: users can only see their own CVs
ALTER TABLE public.cv_intake ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own CVs"
    ON public.cv_intake FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own CVs"
    ON public.cv_intake FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Service role (admin) bypasses RLS for background workers
