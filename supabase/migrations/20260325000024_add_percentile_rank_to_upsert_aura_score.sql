-- Migration: compute percentile_rank inside upsert_aura_score RPC
-- Problem: percentile_rank column exists in aura_scores but was never set — always NULL.
-- Fix: after computing total_score, count public volunteers scoring below this user
--      and store the result. Excludes current user from both counts to avoid stale
--      self-comparison during updates.
-- Result: NULL when no other public users exist (frontend shows "Be first!");
--         0–100.0 otherwise (rounded to 1 decimal).

CREATE OR REPLACE FUNCTION public.upsert_aura_score(
    p_volunteer_id UUID,
    p_competency_scores JSONB
)
RETURNS public.aura_scores AS $$
DECLARE
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
BEGIN
    v_total := public.calculate_aura_score(p_competency_scores);
    v_tier  := public.get_badge_tier(v_total);

    -- Elite: total >= 75 AND 2+ competencies >= 75
    FOR v_slug, v_score IN
        SELECT key, value::FLOAT FROM jsonb_each_text(p_competency_scores)
    LOOP
        IF v_score >= 75 THEN
            v_high_count := v_high_count + 1;
        END IF;
    END LOOP;
    v_elite := (v_total >= 75 AND v_high_count >= 2);

    -- ── Percentile rank ────────────────────────────────────────────────────────
    -- Exclude current user from both counts so the comparison is always against
    -- OTHER public users. Denominator is (others + 1) to include this user.
    -- Returns NULL when no other public users exist yet (early-launch state).
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
        v_percentile := NULL;  -- Not enough users yet
    END IF;
    -- ── End percentile ─────────────────────────────────────────────────────────

    INSERT INTO public.aura_scores (
        volunteer_id, total_score, badge_tier, elite_status,
        competency_scores, percentile_rank, last_updated
    )
    VALUES (
        p_volunteer_id, v_total, v_tier, v_elite,
        p_competency_scores, v_percentile, NOW()
    )
    ON CONFLICT (volunteer_id) DO UPDATE SET
        total_score       = v_total,
        badge_tier        = v_tier,
        elite_status      = v_elite,
        competency_scores = p_competency_scores,
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
$$ LANGUAGE plpgsql SECURITY DEFINER;
