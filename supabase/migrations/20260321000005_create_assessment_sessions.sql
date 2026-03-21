CREATE TABLE public.assessment_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    competency_id UUID REFERENCES public.competencies(id),
    status TEXT DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'abandoned', 'flagged')),
    language TEXT DEFAULT 'en' CHECK (language IN ('en', 'az')),
    -- Question sequence
    question_ids UUID[] NOT NULL DEFAULT '{}',
    current_question_idx INT DEFAULT 0,
    -- Answers stored as JSONB array
    -- [{question_id, answer, time_ms, evaluation_data, irt_score}]
    answers JSONB DEFAULT '[]',
    -- IRT state
    theta_estimate FLOAT DEFAULT 0.0,
    theta_se FLOAT DEFAULT 1.0,
    -- Anti-gaming flags
    fast_responses INT DEFAULT 0,
    flag_reason TEXT,
    -- Results
    aura_result JSONB,                 -- {competency_slug: score, overall: score}
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '2 hours',
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assessment_sessions_volunteer ON public.assessment_sessions(volunteer_id);
CREATE INDEX idx_assessment_sessions_status ON public.assessment_sessions(status);

ALTER TABLE public.assessment_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sessions"
    ON public.assessment_sessions FOR SELECT
    USING (auth.uid() = volunteer_id);

CREATE POLICY "Users can insert own sessions"
    ON public.assessment_sessions FOR INSERT
    WITH CHECK (auth.uid() = volunteer_id);

CREATE POLICY "Users can update own sessions"
    ON public.assessment_sessions FOR UPDATE
    USING (auth.uid() = volunteer_id);
