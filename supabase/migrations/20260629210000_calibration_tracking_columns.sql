-- Sprint checkpoint #5: calibration-tracking columns
-- Makes "estimated vs empirically proven" IRT params queryable.
-- Per research §8.4: all 123 prod questions have LLM-estimated IRT params,
-- zero have empirical calibration from real response data.

ALTER TABLE public.questions
  ADD COLUMN IF NOT EXISTS calibration_status TEXT NOT NULL DEFAULT 'estimated'
    CHECK (calibration_status IN ('estimated', 'pilot', 'calibrated', 'retired')),
  ADD COLUMN IF NOT EXISTS response_count INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS generation_source TEXT NOT NULL DEFAULT 'manual'
    CHECK (generation_source IN ('manual', 'agent_evolved', 'aig_pipeline', 'imported'));

COMMENT ON COLUMN public.questions.calibration_status IS
  'estimated = LLM-set IRT params (current state); pilot = collecting responses; calibrated = empirically verified; retired = removed from active bank';
COMMENT ON COLUMN public.questions.response_count IS
  'Number of real candidate responses used for IRT param estimation (0 = untested)';
COMMENT ON COLUMN public.questions.generation_source IS
  'How the question was created: manual, agent_evolved (swarm sprint), aig_pipeline (auto-generation), imported';

-- Index for filtering by calibration status (admin dashboard, bank health queries)
CREATE INDEX IF NOT EXISTS idx_questions_calibration ON public.questions (calibration_status, is_active);
