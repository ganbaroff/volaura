-- Phase 1.5: RPC functions accept both p_volunteer_id and p_professional_id
-- Non-breaking: existing callers pass p_volunteer_id, new code can pass p_professional_id.
-- Supabase RPC uses named params — adding DEFAULT NULL param is backward-compatible.
--
-- Functions updated:
--   1. upsert_aura_score — adds p_professional_id UUID DEFAULT NULL
--   2. calculate_reliability_score — adds p_professional_id UUID DEFAULT NULL
--   3. match_volunteers — returns professional_id in result set
--   4. NEW: match_professionals — alias wrapper for match_volunteers

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. upsert_aura_score — accept either p_volunteer_id or p_professional_id
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.upsert_aura_score(
    p_volunteer_id UUID DEFAULT NULL,
    p_competency_scores JSONB DEFAULT '{}'::jsonb,
    p_professional_id UUID DEFAULT NULL
) RETURNS public.aura_scores
LANGUAGE plpgsql SECURITY DEFINER
SET search_path TO ''
AS $$
DECLARE
    v_user_id      UUID;
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
    -- Accept either parameter name — professional_id takes precedence if both given
    v_user_id := COALESCE(p_professional_id, p_volunteer_id);
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Either p_volunteer_id or p_professional_id must be provided';
    END IF;

    -- Get existing competency scores (if any) and MERGE with new
    SELECT COALESCE(competency_scores, '{}'::jsonb) INTO v_existing
    FROM public.aura_scores
    WHERE volunteer_id = v_user_id;

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
      AND volunteer_id != v_user_id;

    SELECT COUNT(*) INTO v_total_public
    FROM public.aura_scores
    WHERE visibility = 'public'
      AND volunteer_id != v_user_id;

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
        v_user_id, v_total, v_tier, v_elite,
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


-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. calculate_reliability_score — accept either parameter name
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.calculate_reliability_score(
    p_volunteer_id UUID DEFAULT NULL,
    p_professional_id UUID DEFAULT NULL
)
RETURNS FLOAT AS $$
DECLARE
    v_user_id UUID;
    v_events_attended INT;
    v_behavioral_score FLOAT;
    v_proven_score FLOAT;
    v_behavioral_weight FLOAT;
    v_final_score FLOAT;

    w_onboarding FLOAT := 0.15;
    w_assessment FLOAT := 0.15;
    w_profile FLOAT := 0.10;
    w_sjt FLOAT := 0.30;
    w_contact FLOAT := 0.15;
    w_availability FLOAT := 0.15;

    w_attendance FLOAT := 0.40;
    w_punctuality FLOAT := 0.20;
    w_coordinator FLOAT := 0.25;
    w_shift FLOAT := 0.15;
BEGIN
    v_user_id := COALESCE(p_professional_id, p_volunteer_id);
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Either p_volunteer_id or p_professional_id must be provided';
    END IF;

    SELECT COALESCE(events_attended, 0) INTO v_events_attended
    FROM public.aura_scores
    WHERE volunteer_id = v_user_id;

    SELECT COALESCE(SUM(
        CASE signal_type
            WHEN 'onboarding_velocity'     THEN signal_value * w_onboarding
            WHEN 'assessment_completion'   THEN signal_value * w_assessment
            WHEN 'profile_completeness'    THEN signal_value * w_profile
            WHEN 'sjt_reliability'         THEN signal_value * w_sjt
            WHEN 'contact_verification'    THEN signal_value * w_contact
            WHEN 'availability_specificity'THEN signal_value * w_availability
            ELSE 0
        END
    ), 30) INTO v_behavioral_score
    FROM (
        SELECT DISTINCT ON (signal_type) signal_type, signal_value
        FROM public.volunteer_behavior_signals
        WHERE volunteer_id = v_user_id
          AND signal_type IN (
              'onboarding_velocity', 'assessment_completion', 'profile_completeness',
              'sjt_reliability', 'contact_verification', 'availability_specificity'
          )
        ORDER BY signal_type, measured_at DESC
    ) latest;

    v_behavioral_score := LEAST(v_behavioral_score, 70);

    SELECT COALESCE(SUM(
        CASE signal_type
            WHEN 'attendance'   THEN signal_value * w_attendance
            WHEN 'punctuality'  THEN signal_value * w_punctuality
            WHEN 'shift_completion' THEN signal_value * w_shift
            ELSE 0
        END
    ), 0) INTO v_proven_score
    FROM (
        SELECT signal_type, AVG(signal_value) AS signal_value
        FROM public.volunteer_behavior_signals
        WHERE volunteer_id = v_user_id
          AND signal_type IN ('attendance', 'punctuality', 'shift_completion')
        GROUP BY signal_type
    ) agg;

    SELECT v_proven_score + COALESCE(AVG(coordinator_rating) * 20 * w_coordinator, 0)
    INTO v_proven_score
    FROM public.registrations
    WHERE volunteer_id = v_user_id
      AND coordinator_rating IS NOT NULL;

    v_behavioral_weight := GREATEST(0, 1.0 - v_events_attended * 0.20);

    v_final_score := (v_behavioral_score * v_behavioral_weight)
                   + (v_proven_score * (1 - v_behavioral_weight));

    RETURN ROUND(LEAST(GREATEST(v_final_score, 0), 100)::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. match_volunteers — add professional_id to result set
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.match_volunteers(
    query_embedding VECTOR(768),
    match_count INT DEFAULT 10,
    min_aura FLOAT DEFAULT 0,
    badge_tier_filter TEXT DEFAULT NULL
)
RETURNS TABLE(
    volunteer_id UUID,
    professional_id UUID,
    similarity FLOAT,
    total_score FLOAT,
    badge_tier TEXT,
    username TEXT,
    display_name TEXT,
    avatar_url TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ve.volunteer_id,
        ve.volunteer_id AS professional_id,
        1 - (ve.embedding <=> query_embedding) AS similarity,
        a.total_score,
        a.badge_tier,
        p.username,
        p.display_name,
        p.avatar_url
    FROM public.volunteer_embeddings ve
    JOIN public.aura_scores a ON ve.volunteer_id = a.volunteer_id
    JOIN public.profiles p ON ve.volunteer_id = p.id
    WHERE
        a.total_score >= min_aura
        AND p.is_public = TRUE
        AND (badge_tier_filter IS NULL OR a.badge_tier = badge_tier_filter)
    ORDER BY ve.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. NEW: match_professionals — alias for new code
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.match_professionals(
    query_embedding VECTOR(768),
    match_count INT DEFAULT 10,
    min_aura FLOAT DEFAULT 0,
    badge_tier_filter TEXT DEFAULT NULL
)
RETURNS TABLE(
    professional_id UUID,
    similarity FLOAT,
    total_score FLOAT,
    badge_tier TEXT,
    username TEXT,
    display_name TEXT,
    avatar_url TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ve.volunteer_id AS professional_id,
        1 - (ve.embedding <=> query_embedding) AS similarity,
        a.total_score,
        a.badge_tier,
        p.username,
        p.display_name,
        p.avatar_url
    FROM public.volunteer_embeddings ve
    JOIN public.aura_scores a ON ve.volunteer_id = a.volunteer_id
    JOIN public.profiles p ON ve.volunteer_id = p.id
    WHERE
        a.total_score >= min_aura
        AND p.is_public = TRUE
        AND (badge_tier_filter IS NULL OR a.badge_tier = badge_tier_filter)
    ORDER BY ve.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMIT;
