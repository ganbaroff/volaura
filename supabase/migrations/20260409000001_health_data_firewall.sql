-- GDPR Firewall — Sprint E2 research finding (Kamila, data ethicist)
--
-- Risk: character_events stores stat_changed events from MindShift.
-- Payloads can include health-sensitive stat names: energy_level, burnout_score,
-- medication_timing. These aggregate into character_stats JSONB via get_character_state().
-- character_stats is user-scoped today, but no DB-level guarantee prevents future leaks.
--
-- Fix: DB-level health stat blocklist excluded from get_character_state().
-- Also: aura_scores_public view already excludes character data.
-- Discovery endpoint reads aura_scores_public only — no current leak path.
-- This migration hardens the DB so future endpoints cannot accidentally expose health data.

-- ============================================================
-- 1. Health stat blocklist — defines what counts as health data
-- ============================================================
-- Any stat_changed payload with stat IN this set is classified as
-- protected health data and MUST NOT appear in public-facing aggregates.
COMMENT ON TABLE public.character_events IS
    'Immutable event log for all ecosystem products. '
    'Health-sensitive stat names (energy_level, burnout_score, burnout_signals, '
    'medication_timing, medication_dose, sleep_hours, heart_rate_variability) '
    'are EXCLUDED from get_character_state() character_stats output. '
    'Never add these names to the public character state API — GDPR Art. 9.';

-- ============================================================
-- 2. Rewrite get_character_state — exclude health stat names
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

    -- GDPR Art. 9 health data blocklist.
    -- Stat names in this array are NEVER included in character_stats output.
    -- Add new health stat names here — never remove existing ones.
    v_health_stat_blocklist TEXT[] := ARRAY[
        'energy_level',
        'burnout_score',
        'burnout_signals',
        'medication_timing',
        'medication_dose',
        'sleep_hours',
        'heart_rate_variability',
        'hrv',
        'pain_level'
    ];
BEGIN
    -- Crystal balance — floored at 0 as defensive measure
    SELECT GREATEST(0, COALESCE(SUM(amount), 0))
    INTO v_crystal_balance
    FROM public.game_crystal_ledger
    WHERE user_id = p_user_id;

    -- XP: regex guard prevents cast crash on malformed payload
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

    -- Verified skills: latest event per skill_slug wins
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

    -- Character stats: latest value per stat key.
    -- GDPR FIREWALL: exclude health stat names via blocklist.
    -- Any stat whose name appears in v_health_stat_blocklist is silently dropped.
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
               -- GDPR Art. 9: exclude health-sensitive stat names
               AND NOT (payload->>'stat' = ANY(v_health_stat_blocklist))
             ORDER BY payload->>'stat', created_at DESC
         ) t),
        '{}'::jsonb
    ) INTO v_character_stats;

    -- Login streak (latest event)
    SELECT (payload->>'current_streak')::INT
    INTO v_login_streak
    FROM public.character_events
    WHERE user_id = p_user_id
      AND event_type = 'login_streak'
      AND payload->>'current_streak' ~ '^[0-9]+$'
    ORDER BY created_at DESC
    LIMIT 1;

    -- Event count + last activity
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

-- ============================================================
-- 3. Safe view: character_events_public_safe
-- ============================================================
-- For any future endpoint that needs to read character events in a
-- public/org context: use this view. It strips all health-sensitive rows.
-- Direct queries on character_events base table require explicit justification.
CREATE OR REPLACE VIEW public.character_events_public_safe
    WITH (security_barrier = TRUE)
AS
SELECT
    id,
    user_id,
    event_type,
    source_product,
    created_at,
    -- payload with health stat values redacted for non-health event types.
    -- vital_logged events are entirely excluded (WHERE clause below).
    CASE
        WHEN event_type = 'stat_changed'
             AND payload->>'stat' = ANY(ARRAY[
                 'energy_level', 'burnout_score', 'burnout_signals',
                 'medication_timing', 'medication_dose', 'sleep_hours',
                 'heart_rate_variability', 'hrv', 'pain_level'
             ])
        THEN NULL   -- redact entire payload row (excluded by WHERE below)
        ELSE payload
    END AS payload
FROM public.character_events
WHERE
    -- Exclude health event types entirely
    event_type NOT IN ('vital_logged', 'health_check')
    -- Exclude stat_changed rows with health stat names
    AND NOT (
        event_type = 'stat_changed'
        AND payload->>'stat' = ANY(ARRAY[
            'energy_level', 'burnout_score', 'burnout_signals',
            'medication_timing', 'medication_dose', 'sleep_hours',
            'heart_rate_variability', 'hrv', 'pain_level'
        ])
    );

COMMENT ON VIEW public.character_events_public_safe IS
    'GDPR-safe projection of character_events. Excludes vital_logged, health_check events, '
    'and any stat_changed row where payload.stat is a health-sensitive name. '
    'Use this view (never the base table) in any org-facing, public, or cross-product query. '
    'Base table: user-scoped RLS only (auth.uid() = user_id). '
    'Health stat blocklist: energy_level, burnout_score, burnout_signals, medication_timing, '
    'medication_dose, sleep_hours, heart_rate_variability, hrv, pain_level.';

-- Revoke direct access to base table from anonymous/authenticated roles.
-- Service role bypasses RLS by design — document the constraint here.
-- Future devs: any service_role query against character_events MUST go through
-- character_events_public_safe or explicitly justify health data access.
REVOKE SELECT ON public.character_events FROM anon;
-- authenticated already limited by RLS (auth.uid() = user_id) — no change needed.
