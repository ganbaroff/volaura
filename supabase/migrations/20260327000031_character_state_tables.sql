-- Sprint A0: character_state as Thalamus
-- Event-sourced cross-product state: Volaura + MindShift + Life Simulator + BrandedBy
-- All character state changes flow through character_events → computed via character_state view

-- ============================================================
-- 1. character_events — immutable event log (append-only)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.character_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    -- Valid event_type values:
    --   crystal_earned, crystal_spent
    --   skill_verified, xp_earned, stat_changed
    --   login_streak, milestone_reached
    payload JSONB NOT NULL DEFAULT '{}',
    -- payload always includes: { _schema_version: 1, ... }
    source_product TEXT NOT NULL,
    -- Valid source_product values: volaura, mindshift, lifesim, brandedby
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_char_events_user_time
    ON public.character_events(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_char_events_type
    ON public.character_events(event_type, user_id);

-- ============================================================
-- 2. game_crystal_ledger — crystal economy double-entry log
-- ============================================================
CREATE TABLE IF NOT EXISTS public.game_crystal_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    amount INT NOT NULL,
    -- Positive = earned, negative = spent
    source TEXT NOT NULL,
    -- e.g. 'volaura_assessment', 'stripe_purchase', 'daily_login', 'crystal_shop'
    reference_id TEXT,
    -- e.g. stripe payment_intent_id, session_id, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_crystal_ledger_user
    ON public.game_crystal_ledger(user_id, created_at DESC);

-- ============================================================
-- 3. game_character_rewards — idempotent Volaura skill rewards
-- Prevents double-claiming crystals for the same competency
-- ============================================================
CREATE TABLE IF NOT EXISTS public.game_character_rewards (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_slug TEXT NOT NULL,
    crystals INT NOT NULL DEFAULT 50,
    claimed BOOLEAN NOT NULL DEFAULT FALSE,
    claimed_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, skill_slug)
);

-- ============================================================
-- 4. character_state — computed view (materialized per query)
-- Returns current state for a given user from all events
-- ============================================================
CREATE OR REPLACE FUNCTION public.get_character_state(p_user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    v_crystal_balance INT;
    v_xp_total INT;
    v_verified_skills TEXT[];
    v_login_streak INT;
    v_last_event_at TIMESTAMPTZ;
    v_event_count INT;
BEGIN
    -- Crystal balance from ledger (single source of truth for crystals)
    SELECT COALESCE(SUM(amount), 0)
    INTO v_crystal_balance
    FROM public.game_crystal_ledger
    WHERE user_id = p_user_id;

    -- XP from events
    SELECT COALESCE(SUM((payload->>'xp_amount')::INT), 0)
    INTO v_xp_total
    FROM public.character_events
    WHERE user_id = p_user_id
      AND event_type = 'xp_earned';

    -- Verified skills (from Volaura assessment completions)
    SELECT COALESCE(ARRAY_AGG(DISTINCT payload->>'skill_slug'), '{}')
    INTO v_verified_skills
    FROM public.character_events
    WHERE user_id = p_user_id
      AND event_type = 'skill_verified'
      AND payload->>'skill_slug' IS NOT NULL;

    -- Current login streak (from latest login_streak event)
    SELECT (payload->>'current_streak')::INT
    INTO v_login_streak
    FROM public.character_events
    WHERE user_id = p_user_id
      AND event_type = 'login_streak'
    ORDER BY created_at DESC
    LIMIT 1;

    -- Last event timestamp + total count
    SELECT MAX(created_at), COUNT(*)
    INTO v_last_event_at, v_event_count
    FROM public.character_events
    WHERE user_id = p_user_id;

    RETURN jsonb_build_object(
        'user_id', p_user_id,
        'crystal_balance', v_crystal_balance,
        'xp_total', COALESCE(v_xp_total, 0),
        'verified_skills', COALESCE(to_jsonb(v_verified_skills), '[]'::jsonb),
        'login_streak', COALESCE(v_login_streak, 0),
        'event_count', COALESCE(v_event_count, 0),
        'last_event_at', v_last_event_at,
        'computed_at', now()
    );
END;
$$;

-- ============================================================
-- 5. RLS Policies
-- ============================================================

-- character_events: users read/insert own rows; service role bypasses RLS
ALTER TABLE public.character_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own character events"
    ON public.character_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own character events"
    ON public.character_events FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- game_crystal_ledger: users read own balance; only service role writes (via API)
ALTER TABLE public.game_crystal_ledger ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own crystal ledger"
    ON public.game_crystal_ledger FOR SELECT
    USING (auth.uid() = user_id);

-- game_character_rewards: users read own rewards; upsert via service role only
ALTER TABLE public.game_character_rewards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own character rewards"
    ON public.game_character_rewards FOR SELECT
    USING (auth.uid() = user_id);

-- Grant execute on state function to authenticated users
GRANT EXECUTE ON FUNCTION public.get_character_state(UUID) TO authenticated;
