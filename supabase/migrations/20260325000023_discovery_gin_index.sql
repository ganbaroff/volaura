-- Discovery endpoint performance: GIN index on competency_scores JSONB
-- Enables fast key-existence checks + numeric extraction on volunteer search.
-- At 3K users, full scan is ~ms. Index pays off at 10K+ users.
-- Architecture agent recommendation: add now, pay nothing at current scale.

CREATE INDEX IF NOT EXISTS idx_aura_competency_scores_gin
    ON public.aura_scores USING GIN (competency_scores);

-- Composite index for cursor pagination: (total_score DESC, volunteer_id ASC)
-- Keyset pagination cursor: WHERE (total_score, volunteer_id) < (cursor_score, cursor_id)
CREATE INDEX IF NOT EXISTS idx_aura_discovery_cursor
    ON public.aura_scores (total_score DESC, volunteer_id ASC)
    WHERE visibility = 'public';

-- Index to speed up role_level filter via assessment_sessions
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_volunteer_role
    ON public.assessment_sessions (volunteer_id, role_level, completed_at DESC)
    WHERE status = 'completed';
