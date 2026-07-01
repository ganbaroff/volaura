-- P0-1: Fix AURA score calculation for partial competency completion.
--
-- ROOT CAUSE (Kimi deep audit 2026-06-28):
-- calculate_aura_score used COALESCE(..., 0) for missing competencies.
-- A user scoring 61 on communication alone got: 61×0.20 + 0×0.80 = 12.2
-- Result: max total_score = 14.33, all badge_tier = "none". The product
-- has NEVER given anyone a badge because of this bug.
--
-- FIX: Average only COMPLETED competencies, re-normalize weights.
-- User scoring 61 on communication now gets: 61×(0.20/0.20) = 61.0 → Silver badge.

CREATE OR REPLACE FUNCTION public.calculate_aura_score(
    p_competency_scores JSONB
)
RETURNS FLOAT AS $$
DECLARE
    v_total FLOAT := 0;
    v_weight_sum FLOAT := 0;
    v_weights JSONB := '{
        "communication": 0.20,
        "reliability": 0.15,
        "english_proficiency": 0.15,
        "leadership": 0.15,
        "event_performance": 0.10,
        "tech_literacy": 0.10,
        "adaptability": 0.10,
        "empathy_safeguarding": 0.05
    }';
    v_slug TEXT;
    v_weight FLOAT;
    v_score FLOAT;
BEGIN
    FOR v_slug, v_weight IN
        SELECT key, value::FLOAT FROM jsonb_each_text(v_weights)
    LOOP
        v_score := (p_competency_scores ->> v_slug)::FLOAT;
        IF v_score IS NOT NULL THEN
            v_total := v_total + (v_score * v_weight);
            v_weight_sum := v_weight_sum + v_weight;
        END IF;
    END LOOP;

    -- No completed competencies = 0
    IF v_weight_sum < 0.001 THEN
        RETURN 0;
    END IF;

    RETURN ROUND((v_total / v_weight_sum)::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Recalculate ALL existing AURA scores with the fixed function
UPDATE aura_scores
SET total_score = calculate_aura_score(competency_scores),
    badge_tier = get_badge_tier(calculate_aura_score(competency_scores)),
    last_updated = NOW()
WHERE competency_scores IS NOT NULL
  AND competency_scores != '{}'::JSONB;
