CREATE TABLE public.assessment_completion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES public.assessment_sessions(id) ON DELETE CASCADE,
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    competency_slug TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'partial', 'completed')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    side_effects JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_error TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_assessment_completion_jobs_status
    ON public.assessment_completion_jobs(status, updated_at);

CREATE INDEX idx_assessment_completion_jobs_volunteer
    ON public.assessment_completion_jobs(volunteer_id, created_at DESC);

CREATE OR REPLACE FUNCTION public.touch_assessment_completion_jobs_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_assessment_completion_jobs_updated_at
    BEFORE UPDATE ON public.assessment_completion_jobs
    FOR EACH ROW
    EXECUTE FUNCTION public.touch_assessment_completion_jobs_updated_at();

ALTER TABLE public.assessment_completion_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role manages assessment completion jobs"
    ON public.assessment_completion_jobs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
