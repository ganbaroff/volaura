CREATE TABLE public.questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competency_id UUID REFERENCES public.competencies(id) ON DELETE SET NULL,
    difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard', 'expert')),
    type TEXT NOT NULL CHECK (type IN ('mcq', 'open_ended')),
    scenario_en TEXT NOT NULL,
    scenario_az TEXT NOT NULL,
    options JSONB,                      -- MCQ: [{key, text_en, text_az}]
    correct_answer TEXT,               -- MCQ only
    expected_concepts JSONB,           -- open_ended: [{name, weight, keywords[]}]
    cefr_level TEXT,                   -- English questions: A1-C2
    -- IRT parameters (2PL model)
    irt_a FLOAT DEFAULT 1.0,           -- discrimination
    irt_b FLOAT DEFAULT 0.0,           -- difficulty (theta scale)
    irt_c FLOAT DEFAULT 0.0,           -- guessing (lower asymptote)
    discrimination_index FLOAT DEFAULT 0.0,
    times_shown INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    -- Reliability / SJT flags
    is_sjt_reliability BOOLEAN DEFAULT FALSE,
    lie_detector_flag BOOLEAN DEFAULT FALSE,
    -- Quality flags
    is_ai_generated BOOLEAN DEFAULT FALSE,
    needs_review BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    feedback_en TEXT,
    feedback_az TEXT,
    development_tip_en TEXT,
    development_tip_az TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER questions_updated_at
    BEFORE UPDATE ON public.questions
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Authenticated users can read active questions
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view active questions"
    ON public.questions FOR SELECT
    TO authenticated
    USING (is_active = TRUE AND needs_review = FALSE);
