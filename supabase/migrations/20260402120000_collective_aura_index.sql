-- Collective AURA Ladders — org talent pool aggregate query index
-- Serves GET /api/organizations/me/collective-aura
-- Query: AVG(aura_scores.total_score) WHERE assessment_sessions.organization_id = ?
-- Without this index: seq scan on assessment_sessions at scale.

CREATE INDEX IF NOT EXISTS idx_assessment_sessions_org_volunteer
    ON public.assessment_sessions (organization_id, volunteer_id);

-- Also index aura_scores for the JOIN
CREATE INDEX IF NOT EXISTS idx_aura_scores_volunteer_total
    ON public.aura_scores (volunteer_id, total_score);
