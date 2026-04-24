-- Collective AURA Ladders — org talent pool aggregate query index
-- Serves GET /api/organizations/me/collective-aura
-- NOTE: assessment_sessions has no organization_id column; collective AURA is
-- computed via aura_scores JOIN organization_volunteers. Only index aura_scores.

CREATE INDEX IF NOT EXISTS idx_aura_scores_volunteer_total
    ON public.aura_scores (volunteer_id, total_score);
