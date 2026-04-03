-- Tribe Streaks: 3-person accountability circles
-- Design spec: docs/TRIBE-STREAKS-DESIGN.md v2.0 (locked 2026-04-02)
-- Board mandate: anti-harassment safeguards FIRST (see Risk 1-4 in design spec)
-- Decisions: Q1=hide-zero-kudos, Q2=fading-crystal-3-consecutive, Q3=2-person-continues
--
-- Tables: tribes, tribe_members, tribe_streaks, tribe_kudos,
--         tribe_renewal_requests, tribe_member_history

-- ─── tribes ───────────────────────────────────────────────────────────────────
CREATE TABLE public.tribes (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ NOT NULL,              -- 4 weeks from creation
    status      TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'expired', 'dissolved'))
);

COMMENT ON TABLE public.tribes IS
    'Tribe Streaks: 3-person accountability circles. Expires after 4 weeks.';

-- ─── tribe_members ────────────────────────────────────────────────────────────
CREATE TABLE public.tribe_members (
    tribe_id    UUID        NOT NULL REFERENCES public.tribes(id)   ON DELETE CASCADE,
    user_id     UUID        NOT NULL REFERENCES public.profiles(id)  ON DELETE CASCADE,
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    opt_out_at  TIMESTAMPTZ,                       -- soft opt-out; NULL = active member
    PRIMARY KEY (tribe_id, user_id)
);

CREATE INDEX idx_tribe_members_user_id
    ON public.tribe_members (user_id);
CREATE INDEX idx_tribe_members_active
    ON public.tribe_members (tribe_id, user_id)
    WHERE opt_out_at IS NULL;

COMMENT ON COLUMN public.tribe_members.opt_out_at IS
    'Soft opt-out. Departed members are invisible in API (filtered WHERE opt_out_at IS NULL).';

-- ─── tribe_streaks ────────────────────────────────────────────────────────────
-- Q2 decision: consecutive_misses_count (3 consecutive = reset)
-- Any active week → consecutive_misses_count = 0
-- Inactive week → consecutive_misses_count++
-- consecutive_misses_count >= 3 → current_streak resets to 0
CREATE TABLE public.tribe_streaks (
    user_id                  UUID        PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    current_streak           INT         NOT NULL DEFAULT 0,
    longest_streak           INT         NOT NULL DEFAULT 0,
    last_activity_week       TEXT                              -- YYYY-Www ISO format
                             CHECK (last_activity_week ~ '^\d{4}-W\d{2}$'),
    consecutive_misses_count INT         NOT NULL DEFAULT 0,   -- 3 consecutive = streak reset
    cycle_started_at         TIMESTAMPTZ NOT NULL DEFAULT NOW() -- grace resets per cycle
);

COMMENT ON COLUMN public.tribe_streaks.consecutive_misses_count IS
    'Fading-crystal model (Q2). 3 consecutive inactive weeks = streak reset. Resets to 0 on any active week.';
COMMENT ON COLUMN public.tribe_streaks.cycle_started_at IS
    'Set when user joins a new tribe. consecutive_misses_count resets at new cycle start.';

-- ─── tribe_kudos ──────────────────────────────────────────────────────────────
-- Truly anonymous: no sender_id stored. Tribe-level kudos only (not member-to-member).
-- Q1 decision: hide count when 0, show "Be the first to send kudos" CTA.
CREATE TABLE public.tribe_kudos (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tribe_id    UUID        NOT NULL REFERENCES public.tribes(id) ON DELETE CASCADE,
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- Intentionally NO sender_id — truly anonymous (anti-harassment safeguard Risk 3)
);

CREATE INDEX idx_tribe_kudos_tribe_week
    ON public.tribe_kudos (tribe_id, sent_at);

COMMENT ON TABLE public.tribe_kudos IS
    'Anonymous kudos at tribe level (not member level). No sender_id stored by design.';

-- ─── tribe_renewal_requests ───────────────────────────────────────────────────
-- Approved change #6: track who wants to renew together
-- Matching service reads this to decide renew vs re-match at cycle end
CREATE TABLE public.tribe_renewal_requests (
    tribe_id     UUID        NOT NULL REFERENCES public.tribes(id) ON DELETE CASCADE,
    user_id      UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tribe_id, user_id)
);

COMMENT ON TABLE public.tribe_renewal_requests IS
    'Opt-in renewal. If all 3 members request renewal before expiry → tribe extends 4 weeks.';

-- ─── tribe_member_history ─────────────────────────────────────────────────────
-- Approved change #3: used by matching service for "no repeat tribes" filter
-- Service-role only. Users cannot read this table.
CREATE TABLE public.tribe_member_history (
    user_id       UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    co_member_id  UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    tribe_id      UUID        REFERENCES public.tribes(id) ON DELETE SET NULL,
    cycle_ended_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, co_member_id, tribe_id)
);

CREATE INDEX idx_tribe_history_user_id
    ON public.tribe_member_history (user_id, cycle_ended_at DESC);

COMMENT ON TABLE public.tribe_member_history IS
    'Service-role only. Prevents repeat pairing in matching algorithm.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- RLS Policies
-- Security model: users read only their own tribe. All writes via service_role.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ─── tribes RLS ──────────────────────────────────────────────────────────────
ALTER TABLE public.tribes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Members can read their tribe"
    ON public.tribes FOR SELECT
    USING (
        id IN (
            SELECT tribe_id FROM public.tribe_members
            WHERE user_id = auth.uid() AND opt_out_at IS NULL
        )
    );

CREATE POLICY "No direct insert by users"
    ON public.tribes FOR INSERT TO authenticated
    WITH CHECK (FALSE);

CREATE POLICY "No direct update by users"
    ON public.tribes FOR UPDATE TO authenticated
    USING (FALSE);

CREATE POLICY "No direct delete by users"
    ON public.tribes FOR DELETE TO authenticated
    USING (FALSE);

-- ─── tribe_members RLS ───────────────────────────────────────────────────────
ALTER TABLE public.tribe_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Active members can read their tribe members"
    ON public.tribe_members FOR SELECT
    USING (
        tribe_id IN (
            SELECT tribe_id FROM public.tribe_members AS tm
            WHERE tm.user_id = auth.uid() AND tm.opt_out_at IS NULL
        )
    );

-- Users can soft-opt-out their own membership only
CREATE POLICY "Users can soft opt-out of own membership"
    ON public.tribe_members FOR UPDATE
    USING (user_id = auth.uid() AND opt_out_at IS NULL)
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "No direct membership insert"
    ON public.tribe_members FOR INSERT TO authenticated
    WITH CHECK (FALSE);

CREATE POLICY "No hard delete by users"
    ON public.tribe_members FOR DELETE TO authenticated
    USING (FALSE);

-- ─── tribe_streaks RLS ───────────────────────────────────────────────────────
ALTER TABLE public.tribe_streaks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own streak only"
    ON public.tribe_streaks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "No direct streak insert"
    ON public.tribe_streaks FOR INSERT TO authenticated
    WITH CHECK (FALSE);

CREATE POLICY "No direct streak update"
    ON public.tribe_streaks FOR UPDATE TO authenticated
    USING (FALSE);

CREATE POLICY "No direct streak delete"
    ON public.tribe_streaks FOR DELETE TO authenticated
    USING (FALSE);

-- ─── tribe_kudos RLS ─────────────────────────────────────────────────────────
-- INSERT allowed for active members. SELECT BLOCKED — use SECURITY DEFINER RPC for count.
ALTER TABLE public.tribe_kudos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Active members can send kudos"
    ON public.tribe_kudos FOR INSERT TO authenticated
    WITH CHECK (
        tribe_id IN (
            SELECT tribe_id FROM public.tribe_members
            WHERE user_id = auth.uid() AND opt_out_at IS NULL
        )
    );

CREATE POLICY "Kudos not directly readable"
    ON public.tribe_kudos FOR SELECT TO authenticated
    USING (FALSE);

CREATE POLICY "Kudos immutable"
    ON public.tribe_kudos FOR UPDATE TO authenticated
    USING (FALSE);

CREATE POLICY "Kudos not deleteable by users"
    ON public.tribe_kudos FOR DELETE TO authenticated
    USING (FALSE);

-- ─── tribe_renewal_requests RLS ──────────────────────────────────────────────
ALTER TABLE public.tribe_renewal_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert own renewal request"
    ON public.tribe_renewal_requests FOR INSERT TO authenticated
    WITH CHECK (
        user_id = auth.uid()
        AND tribe_id IN (
            SELECT tribe_id FROM public.tribe_members
            WHERE user_id = auth.uid() AND opt_out_at IS NULL
        )
    );

CREATE POLICY "Users can read own renewal request"
    ON public.tribe_renewal_requests FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "No renewal update or delete by users"
    ON public.tribe_renewal_requests FOR UPDATE TO authenticated
    USING (FALSE);

-- ─── tribe_member_history RLS ────────────────────────────────────────────────
-- Service-role only. No user can read this table directly.
ALTER TABLE public.tribe_member_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "No user access to member history"
    ON public.tribe_member_history FOR ALL TO authenticated
    USING (FALSE);

-- ─── SECURITY DEFINER RPC: kudos count ───────────────────────────────────────
-- Users cannot SELECT tribe_kudos directly (anti-harassment).
-- This RPC returns count only — no sender info.
-- Q1: if count = 0, frontend hides count and shows "Be the first to send kudos" CTA.
CREATE OR REPLACE FUNCTION public.get_tribe_kudos_count(p_tribe_id UUID)
RETURNS INT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_count INT;
    v_current_week TEXT;
BEGIN
    -- Only returns count for current ISO week
    v_current_week := TO_CHAR(NOW(), 'IYYY-"W"IW');

    -- Verify caller is an active member of this tribe
    IF NOT EXISTS (
        SELECT 1 FROM public.tribe_members
        WHERE tribe_id = p_tribe_id
          AND user_id = auth.uid()
          AND opt_out_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Not a member of this tribe';
    END IF;

    SELECT COUNT(*) INTO v_count
    FROM public.tribe_kudos
    WHERE tribe_id = p_tribe_id
      AND TO_CHAR(sent_at, 'IYYY-"W"IW') = v_current_week;

    RETURN v_count;
END;
$$;
