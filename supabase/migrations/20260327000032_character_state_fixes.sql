-- Sprint A0 Audit Fixes
-- Resolves: P0-1 (overdraft crash), P2-1 (search_path), P2-2 (bigint),
--           P2-7 (CHECK constraints), P1-1 (xp_amount cast), P1-3 (stat_changed),
--           P1-5 (verified_skills with score+tier), P2-3 (skill_unverified revocation)

-- ============================================================
-- P2-7: CHECK constraints — DB enforces valid values even without API
-- ============================================================
ALTER TABLE public.character_events
    ADD CONSTRAINT chk_event_type CHECK (event_type IN (
        'crystal_earned', 'crystal_spent',
        'skill_verified', 'skill_unverified',
        'xp_earned', 'stat_changed',
        'login_streak', 'milestone_reached'
    ));

ALTER TABLE public.character_events
    ADD CONSTRAINT chk_source_product CHECK (source_product IN (
        'volaura', 'mindshift', 'lifesim', 'brandedby'
    ));

-- ============================================================
-- Full rewrite of get_character_state fixing all audit issues:
-- P2-1: SET search_path (SECURITY DEFINER safety)
-- P2-2: BIGINT for xp_total and event_count
-- P1-1: xp_amount regex guard before cast (no crash on bad data)
-- P1-3: stat_changed aggregated into character_stats JSONB
-- P1-5: verified_skills returns {slug, aura_score, badge_tier} not just slug
-- P2-3: skill_unverified revocation — latest event per skill wins
-- P0-1 (partial): crystal_balance floored at 0 via GREATEST(0, ...) — DB defense
-- ============================================================
CREATE OR REPLACE FUNCTION public.get_character_state(p_user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_crystal_balance   INT;
    v_xp_total          BIGINT;
    v_verified_skills   JSONB;
    v_login_streak      INT;
    v_last_event_at     TIMESTAMPTZ;
    v_event_count       BIGINT;
    v_character_stats   JSONB;
BEGIN
    -- Crystal balance — floored at 0 as defensive measure
    -- Primary prevention is in the API layer (balance check before crystal_spent)
    SELECT GREATEST(0, COALESCE(SUM(amount), 0))
    INTO v_crystal_balance
    FROM public.game_crystal_ledger
    WHERE user_id = p_user_id;

    -- XP: regex guard prevents cast crash on malformed payload.xp_amount
    SELECT COALESCE(SUM(
        CASE
            WHEN payload->>'xp_amount' ~ '^[0-9]+$'
            THEN (payload->>'xp_amount')::BIGINT
            ELSE 0
        END
    ), 0)
    INTO v_xp_total
    FROM public.character_events
    WHERE user_id = p_user_id
      AND event_type = 'xp_earned';

    -- Verified skills: latest event per skill_slug wins.
    -- If latest is skill_unverified → skill is revoked and excluded.
    SELECT COALESCE(jsonb_agg(
        jsonb_build_object(
            'slug',       t.slug,
            'aura_score', t.aura_score,
            'badge_tier', t.badge_tier
        )
    ), '[]'::jsonb)
    INTO v_verified_skills
    FROM (
        SELECT DISTINCT ON (payload->>'skill_slug')
            payload->>'skill_slug'                                      AS slug,
            CASE
                WHEN payload->>'aura_score' ~ '^[0-9]+(\.[0-9]+)?$'
                THEN (payload->>'aura_score')::FLOAT
                ELSE NULL
            END                                                         AS aura_score,
            payload->>'badge_tier'                                      AS badge_tier,
            event_type
        FROM public.character_events
        WHERE user_id = p_user_id
          AND event_type IN ('skill_verified', 'skill_unverified')
          AND payload->>'skill_slug' IS NOT NULL
        ORDER BY payload->>'skill_slug', created_at DESC
    ) t
    WHERE t.event_type = 'skill_verified';

    -- Character stats from Life Simulator: latest value per stat key
    SELECT COALESCE(
        (SELECT jsonb_object_agg(t.stat_name, t.stat_value)
         FROM (
             SELECT DISTINCT ON (payload->>'stat')
                 payload->>'stat'                AS stat_name,
                 (payload->>'value')::INT        AS stat_value
             FROM public.character_events
             WHERE user_id = p_user_id
               AND event_type = 'stat_changed'
               AND payload->>'stat'  IS NOT NULL
               AND payload->>'value' ~ '^-?[0-9]+$'
             ORDER BY payload->>'stat', created_at DESC
         ) t),
        '{}'::jsonb
    ) INTO v_character_stats;

    -- Current login streak (latest event wins — streak resets produce new events)
    SELECT (payload->>'current_streak')::INT
    INTO v_login_streak
    FROM public.character_events
    WHERE user_id = p_user_id
      AND event_type = 'login_streak'
      AND payload->>'current_streak' ~ '^[0-9]+$'
    ORDER BY created_at DESC
    LIMIT 1;

    -- Event count + last activity timestamp
    SELECT MAX(created_at), COUNT(*)
    INTO v_last_event_at, v_event_count
    FROM public.character_events
    WHERE user_id = p_user_id;

    RETURN jsonb_build_object(
        'user_id',          p_user_id,
        'crystal_balance',  v_crystal_balance,
        'xp_total',         COALESCE(v_xp_total, 0),
        'verified_skills',  v_verified_skills,
        'character_stats',  v_character_stats,
        'login_streak',     COALESCE(v_login_streak, 0),
        'event_count',      COALESCE(v_event_count, 0),
        'last_event_at',    v_last_event_at,
        'computed_at',      now()
    );
END;
$$;
