-- Sprint 3: Add time_estimate_minutes and can_retake to competencies
-- Used by GET /api/assessment/info/{competency_slug}
-- time_estimate_minutes: approx time for the user to complete this competency assessment
-- can_retake: FALSE = assessment disabled for retakes (admin control), TRUE = normal 7-day cooldown applies

ALTER TABLE public.competencies
    ADD COLUMN IF NOT EXISTS time_estimate_minutes INT NOT NULL DEFAULT 15,
    ADD COLUMN IF NOT EXISTS can_retake BOOLEAN NOT NULL DEFAULT TRUE;

-- Seed with per-competency estimates (based on question count and complexity)
UPDATE public.competencies SET time_estimate_minutes = 12 WHERE slug = 'communication';
UPDATE public.competencies SET time_estimate_minutes = 10 WHERE slug = 'reliability';
UPDATE public.competencies SET time_estimate_minutes = 10 WHERE slug = 'english_proficiency';
UPDATE public.competencies SET time_estimate_minutes = 15 WHERE slug = 'leadership';
UPDATE public.competencies SET time_estimate_minutes = 8  WHERE slug = 'event_performance';
UPDATE public.competencies SET time_estimate_minutes = 10 WHERE slug = 'tech_literacy';
UPDATE public.competencies SET time_estimate_minutes = 10 WHERE slug = 'adaptability';
UPDATE public.competencies SET time_estimate_minutes = 8  WHERE slug = 'empathy_safeguarding';
