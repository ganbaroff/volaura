-- Fix: upsert_aura_score was overwriting competency_scores instead of merging.
-- Bug found in E2E Leyla journey: completing leadership erased communication score.
-- Fix: MERGE new scores into existing JSONB using || operator.
-- Also: recalculate total from MERGED scores, not just new ones.

CREATE OR REPLACE FUNCTION public.upsert_aura_score(
    p_volunteer_id UUID,
    p_competency_scores JSONB
) RETURNS public.aura_scores
LANGUAGE plpgsql SECURITY DEFINER
SET search_path TO ''
AS $$
DECLARE
    v_merged       JSONB;
    v_total        FLOAT;
    v_tier         TEXT;
    v_elite        BOOLEAN;
    v_result       public.aura_scores;
    v_slug         TEXT;
    v_score        FLOAT;
    v_high_count   INT := 0;
    v_count_below  INT := 0;
    v_total_public INT := 0;
    v_percentile   NUMERIC;
    v_existing     JSONB;
BEGIN
    -- Get existing competency scores (if any) and MERGE with new
    SELECT COALESCE(competency_scores, '{}'::jsonb) INTO v_existing
    FROM public.aura_scores
    WHERE volunteer_id = p_volunteer_id;

    -- Merge: existing scores + new scores (new overwrites same key)
    v_merged := COALESCE(v_existing, '{}'::jsonb) || p_competency_scores;

    -- Calculate total from MERGED scores (all competencies, not just new)
    v_total := public.calculate_aura_score(v_merged);
    v_tier  := public.get_badge_tier(v_total);

    -- Elite: total >= 75 AND 2+ competencies >= 75
    FOR v_slug, v_score IN
        SELECT key, value::FLOAT FROM jsonb_each_text(v_merged)
    LOOP
        IF v_score >= 75 THEN
            v_high_count := v_high_count + 1;
        END IF;
    END LOOP;
    v_elite := (v_total >= 75 AND v_high_count >= 2);

    -- Percentile rank
    SELECT COUNT(*) INTO v_count_below
    FROM public.aura_scores
    WHERE total_score < v_total
      AND visibility = 'public'
      AND volunteer_id != p_volunteer_id;

    SELECT COUNT(*) INTO v_total_public
    FROM public.aura_scores
    WHERE visibility = 'public'
      AND volunteer_id != p_volunteer_id;

    IF v_total_public > 0 THEN
        v_percentile := ROUND(
            (v_count_below::NUMERIC / (v_total_public + 1)::NUMERIC) * 100,
            1
        );
    ELSE
        v_percentile := NULL;
    END IF;

    INSERT INTO public.aura_scores (
        volunteer_id, total_score, badge_tier, elite_status,
        competency_scores, percentile_rank, last_updated
    )
    VALUES (
        p_volunteer_id, v_total, v_tier, v_elite,
        v_merged, v_percentile, NOW()
    )
    ON CONFLICT (volunteer_id) DO UPDATE SET
        total_score       = v_total,
        badge_tier        = v_tier,
        elite_status      = v_elite,
        competency_scores = v_merged,
        percentile_rank   = v_percentile,
        aura_history      = aura_scores.aura_history ||
            jsonb_build_array(jsonb_build_object(
                'date',       NOW(),
                'total_score', v_total,
                'badge_tier',  v_tier
            )),
        last_updated = NOW()
    RETURNING * INTO v_result;

    RETURN v_result;
END;
$$;
