-- =============================================================================
-- RPC FUNCTIONS — called via supabase.rpc() from Python/TypeScript
-- =============================================================================

-- 1. Semantic volunteer matching via pgvector cosine similarity
-- All vector ops MUST go through this RPC — never PostgREST directly
CREATE OR REPLACE FUNCTION public.match_volunteers(
    query_embedding VECTOR(768),
    match_count INT DEFAULT 10,
    min_aura FLOAT DEFAULT 0,
    badge_tier_filter TEXT DEFAULT NULL
)
RETURNS TABLE(
    volunteer_id UUID,
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


-- 2. Calculate AURA score from competency scores
-- Weights are fixed per spec — DO NOT CHANGE
CREATE OR REPLACE FUNCTION public.calculate_aura_score(
    p_competency_scores JSONB
)
RETURNS FLOAT AS $$
DECLARE
    v_total FLOAT := 0;
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
        v_score := COALESCE((p_competency_scores ->> v_slug)::FLOAT, 0);
        v_total := v_total + (v_score * v_weight);
    END LOOP;

    RETURN ROUND(v_total::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- 3. Get badge tier from AURA total score
CREATE OR REPLACE FUNCTION public.get_badge_tier(p_total_score FLOAT)
RETURNS TEXT AS $$
BEGIN
    IF p_total_score >= 90 THEN RETURN 'platinum';
    ELSIF p_total_score >= 75 THEN RETURN 'gold';
    ELSIF p_total_score >= 60 THEN RETURN 'silver';
    ELSIF p_total_score >= 40 THEN RETURN 'bronze';
    ELSE RETURN 'none';
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- 4. Calculate reliability score from behavior signals
CREATE OR REPLACE FUNCTION public.calculate_reliability_score(p_volunteer_id UUID)
RETURNS FLOAT AS $$
DECLARE
    v_events_attended INT;
    v_behavioral_score FLOAT;
    v_proven_score FLOAT;
    v_behavioral_weight FLOAT;
    v_final_score FLOAT;

    -- Behavioral phase weights (pre-event)
    w_onboarding FLOAT := 0.15;
    w_assessment FLOAT := 0.15;
    w_profile FLOAT := 0.10;
    w_sjt FLOAT := 0.30;
    w_contact FLOAT := 0.15;
    w_availability FLOAT := 0.15;

    -- Proven phase weights (post-event)
    w_attendance FLOAT := 0.40;
    w_punctuality FLOAT := 0.20;
    w_coordinator FLOAT := 0.25;
    w_shift FLOAT := 0.15;
BEGIN
    -- Count completed events
    SELECT COALESCE(events_attended, 0) INTO v_events_attended
    FROM public.aura_scores
    WHERE volunteer_id = p_volunteer_id;

    -- Behavioral phase score (latest signal per type, normalized to 0-100)
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
        WHERE volunteer_id = p_volunteer_id
          AND signal_type IN (
              'onboarding_velocity', 'assessment_completion', 'profile_completeness',
              'sjt_reliability', 'contact_verification', 'availability_specificity'
          )
        ORDER BY signal_type, measured_at DESC
    ) latest;

    -- Cap behavioral score at 70
    v_behavioral_score := LEAST(v_behavioral_score, 70);

    -- Proven phase score from event history
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
        WHERE volunteer_id = p_volunteer_id
          AND signal_type IN ('attendance', 'punctuality', 'shift_completion')
        GROUP BY signal_type
    ) agg;

    -- Add coordinator rating contribution
    SELECT v_proven_score + COALESCE(AVG(coordinator_rating) * 20 * w_coordinator, 0)
    INTO v_proven_score
    FROM public.registrations
    WHERE volunteer_id = p_volunteer_id
      AND coordinator_rating IS NOT NULL;

    -- Phase transition: behavioral_weight = max(0, 1 - events * 0.2)
    v_behavioral_weight := GREATEST(0, 1.0 - v_events_attended * 0.20);

    v_final_score := (v_behavioral_score * v_behavioral_weight)
                   + (v_proven_score * (1 - v_behavioral_weight));

    RETURN ROUND(LEAST(GREATEST(v_final_score, 0), 100)::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- 5. Upsert AURA score after assessment completion
CREATE OR REPLACE FUNCTION public.upsert_aura_score(
    p_volunteer_id UUID,
    p_competency_scores JSONB
)
RETURNS public.aura_scores AS $$
DECLARE
    v_total FLOAT;
    v_tier TEXT;
    v_elite BOOLEAN;
    v_result public.aura_scores;
    v_slug TEXT;
    v_score FLOAT;
    v_high_count INT := 0;
BEGIN
    v_total := public.calculate_aura_score(p_competency_scores);
    v_tier := public.get_badge_tier(v_total);

    -- Elite: total >= 75 AND 2+ competencies >= 75
    FOR v_slug, v_score IN SELECT key, value::FLOAT FROM jsonb_each_text(p_competency_scores)
    LOOP
        IF v_score >= 75 THEN
            v_high_count := v_high_count + 1;
        END IF;
    END LOOP;
    v_elite := (v_total >= 75 AND v_high_count >= 2);

    INSERT INTO public.aura_scores (
        volunteer_id, total_score, badge_tier, elite_status, competency_scores, last_updated
    )
    VALUES (p_volunteer_id, v_total, v_tier, v_elite, p_competency_scores, NOW())
    ON CONFLICT (volunteer_id) DO UPDATE SET
        total_score = v_total,
        badge_tier = v_tier,
        elite_status = v_elite,
        competency_scores = p_competency_scores,
        aura_history = aura_scores.aura_history ||
            jsonb_build_array(jsonb_build_object(
                'date', NOW(),
                'total_score', v_total,
                'badge_tier', v_tier
            )),
        last_updated = NOW()
    RETURNING * INTO v_result;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
