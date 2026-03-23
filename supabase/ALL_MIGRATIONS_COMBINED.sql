-- ============================================================
-- Volaura — All Migrations Combined
-- Run this ONCE in Supabase SQL Editor to set up the schema
-- Date: 2026-03-23
-- ============================================================

-- ------------------------------------------------------------
-- Migration: 20260321000001_enable_extensions.sql
-- ------------------------------------------------------------
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";


-- ------------------------------------------------------------
-- Migration: 20260321000002_create_profiles.sql
-- ------------------------------------------------------------
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    location TEXT,
    languages TEXT[] DEFAULT '{}',
    social_links JSONB DEFAULT '{}',
    phone TEXT,
    telegram_chat_id BIGINT,
    badge_issued_at TIMESTAMPTZ,
    badge_open_badges_url TEXT,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public profiles are viewable by everyone"
    ON public.profiles FOR SELECT
    USING (is_public = TRUE);

CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);


-- ------------------------------------------------------------
-- Migration: 20260321000003_create_competencies.sql
-- ------------------------------------------------------------
CREATE TABLE public.competencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    name_en TEXT NOT NULL,
    name_az TEXT NOT NULL,
    description_en TEXT,
    description_az TEXT,
    weight FLOAT NOT NULL CHECK (weight > 0 AND weight <= 1),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Public read-only (reference data)
ALTER TABLE public.competencies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Competencies are viewable by everyone"
    ON public.competencies FOR SELECT
    USING (TRUE);


-- ------------------------------------------------------------
-- Migration: 20260321000004_create_questions.sql
-- ------------------------------------------------------------
CREATE TABLE public.questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competency_id UUID REFERENCES public.competencies(id) ON DELETE SET NULL,
    difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard', 'expert')),
    type TEXT NOT NULL CHECK (type IN ('mcq', 'open_ended')),
    scenario_en TEXT NOT NULL,
    scenario_az TEXT NOT NULL,
    options JSONB,                      -- MCQ: [{key, text_en, text_az}]
    correct_answer TEXT,               -- MCQ only
    expected_concepts JSONB,           -- open_ended: [{name, weight, keywords[]}]
    cefr_level TEXT,                   -- English questions: A1-C2
    -- IRT parameters (2PL model)
    irt_a FLOAT DEFAULT 1.0,           -- discrimination
    irt_b FLOAT DEFAULT 0.0,           -- difficulty (theta scale)
    irt_c FLOAT DEFAULT 0.0,           -- guessing (lower asymptote)
    discrimination_index FLOAT DEFAULT 0.0,
    times_shown INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    -- Reliability / SJT flags
    is_sjt_reliability BOOLEAN DEFAULT FALSE,
    lie_detector_flag BOOLEAN DEFAULT FALSE,
    -- Quality flags
    is_ai_generated BOOLEAN DEFAULT FALSE,
    needs_review BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    feedback_en TEXT,
    feedback_az TEXT,
    development_tip_en TEXT,
    development_tip_az TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER questions_updated_at
    BEFORE UPDATE ON public.questions
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Authenticated users can read active questions
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view active questions"
    ON public.questions FOR SELECT
    TO authenticated
    USING (is_active = TRUE AND needs_review = FALSE);


-- ------------------------------------------------------------
-- Migration: 20260321000005_create_assessment_sessions.sql
-- ------------------------------------------------------------
CREATE TABLE public.assessment_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    competency_id UUID REFERENCES public.competencies(id),
    status TEXT DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'abandoned', 'flagged')),
    language TEXT DEFAULT 'en' CHECK (language IN ('en', 'az')),
    -- Question sequence
    question_ids UUID[] NOT NULL DEFAULT '{}',
    current_question_idx INT DEFAULT 0,
    -- Answers stored as JSONB array
    -- [{question_id, answer, time_ms, evaluation_data, irt_score}]
    answers JSONB DEFAULT '[]',
    -- IRT state
    theta_estimate FLOAT DEFAULT 0.0,
    theta_se FLOAT DEFAULT 1.0,
    -- Anti-gaming flags
    fast_responses INT DEFAULT 0,
    flag_reason TEXT,
    -- Results
    aura_result JSONB,                 -- {competency_slug: score, overall: score}
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '2 hours',
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assessment_sessions_volunteer ON public.assessment_sessions(volunteer_id);
CREATE INDEX idx_assessment_sessions_status ON public.assessment_sessions(status);

ALTER TABLE public.assessment_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sessions"
    ON public.assessment_sessions FOR SELECT
    USING (auth.uid() = volunteer_id);

CREATE POLICY "Users can insert own sessions"
    ON public.assessment_sessions FOR INSERT
    WITH CHECK (auth.uid() = volunteer_id);

CREATE POLICY "Users can update own sessions"
    ON public.assessment_sessions FOR UPDATE
    USING (auth.uid() = volunteer_id);


-- ------------------------------------------------------------
-- Migration: 20260321000006_create_aura_scores.sql
-- ------------------------------------------------------------
CREATE TABLE public.aura_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID UNIQUE NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    total_score FLOAT NOT NULL DEFAULT 0,
    badge_tier TEXT DEFAULT 'none'
        CHECK (badge_tier IN ('none', 'bronze', 'silver', 'gold', 'platinum')),
    elite_status BOOLEAN DEFAULT FALSE,
    -- Per-competency scores: {slug: score_0_to_100}
    competency_scores JSONB NOT NULL DEFAULT '{}',
    -- Reliability
    reliability_score FLOAT DEFAULT 50.0,
    reliability_status TEXT DEFAULT 'pending'
        CHECK (reliability_status IN ('pending', 'verified', 'proven')),
    -- Event stats
    events_attended INT DEFAULT 0,
    events_no_show INT DEFAULT 0,
    events_late INT DEFAULT 0,
    -- Rankings
    percentile_rank FLOAT,
    -- History for timeline visualization
    aura_history JSONB DEFAULT '[]',   -- [{date, total_score, badge_tier}]
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_aura_scores_total ON public.aura_scores(total_score DESC);
CREATE INDEX idx_aura_scores_badge ON public.aura_scores(badge_tier);

ALTER TABLE public.aura_scores ENABLE ROW LEVEL SECURITY;

-- Public read for volunteer discovery
CREATE POLICY "AURA scores are publicly readable"
    ON public.aura_scores FOR SELECT
    USING (TRUE);

CREATE POLICY "System can insert AURA scores"
    ON public.aura_scores FOR INSERT
    WITH CHECK (auth.uid() = volunteer_id);

CREATE POLICY "System can update AURA scores"
    ON public.aura_scores FOR UPDATE
    USING (auth.uid() = volunteer_id);


-- ------------------------------------------------------------
-- Migration: 20260321000007_create_badges.sql
-- ------------------------------------------------------------
CREATE TABLE public.badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    name_en TEXT NOT NULL,
    name_az TEXT NOT NULL,
    description_en TEXT,
    description_az TEXT,
    icon_url TEXT,
    badge_type TEXT DEFAULT 'tier'
        CHECK (badge_type IN ('tier', 'achievement', 'special')),
    requirements JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.volunteer_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    badge_id UUID NOT NULL REFERENCES public.badges(id),
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    open_badges_url TEXT,              -- Open Badges 3.0 JSON URL
    linkedin_exported_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    UNIQUE(volunteer_id, badge_id)
);

CREATE INDEX idx_volunteer_badges_volunteer ON public.volunteer_badges(volunteer_id);

ALTER TABLE public.badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_badges ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Badges are viewable by everyone"
    ON public.badges FOR SELECT USING (TRUE);

CREATE POLICY "Users can view own badges"
    ON public.volunteer_badges FOR SELECT
    USING (auth.uid() = volunteer_id);

CREATE POLICY "Public can view volunteer badges"
    ON public.volunteer_badges FOR SELECT
    USING (TRUE);


-- ------------------------------------------------------------
-- Migration: 20260321000008_create_organizations.sql
-- ------------------------------------------------------------
CREATE TABLE public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT CHECK (type IN ('company', 'ngo', 'government', 'individual')),
    logo_url TEXT,
    website TEXT,
    description TEXT,
    subscription_tier TEXT DEFAULT 'free'
        CHECK (subscription_tier IN ('free', 'starter', 'growth', 'enterprise')),
    subscription_expires_at TIMESTAMPTZ,
    stripe_customer_id TEXT,
    trust_score FLOAT,
    verified_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER organizations_updated_at
    BEFORE UPDATE ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE INDEX idx_organizations_owner ON public.organizations(owner_id);

-- Organization ratings (bilateral — volunteer rates org anonymously)
CREATE TABLE public.organization_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_id UUID,                     -- FK added after events table
    rating FLOAT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(volunteer_id, organization_id, event_id)
);

-- Trust Score visible ONLY after 5+ ratings
CREATE OR REPLACE VIEW public.organization_trust_scores AS
SELECT
    organization_id,
    COUNT(*) AS rating_count,
    CASE WHEN COUNT(*) >= 5
        THEN ROUND((AVG(rating) * 20)::numeric, 1)  -- 1-5 → 0-100
        ELSE NULL                          -- hidden until 5+ ratings
    END AS trust_score
FROM public.organization_ratings
GROUP BY organization_id;

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_ratings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Organizations are publicly viewable"
    ON public.organizations FOR SELECT
    USING (is_active = TRUE);

CREATE POLICY "Owners can update their org"
    ON public.organizations FOR UPDATE
    USING (auth.uid() = owner_id);

CREATE POLICY "Owners can insert org"
    ON public.organizations FOR INSERT
    WITH CHECK (auth.uid() = owner_id);

-- Ratings: insert only, no reading individual rows (anonymous by design)
CREATE POLICY "Authenticated users can rate organizations"
    ON public.organization_ratings FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = volunteer_id);


-- ------------------------------------------------------------
-- Migration: 20260321000009_create_events.sql
-- ------------------------------------------------------------
CREATE TABLE public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    title_en TEXT NOT NULL,
    title_az TEXT NOT NULL,
    description_en TEXT,
    description_az TEXT,
    event_type TEXT,                   -- conference, marathon, ceremony, etc.
    location TEXT,
    location_coords JSONB,             -- {lat, lng}
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    capacity INT,
    required_competencies UUID[] DEFAULT '{}',
    required_min_aura FLOAT DEFAULT 0,
    required_languages TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'draft'
        CHECK (status IN ('draft', 'open', 'closed', 'cancelled', 'completed')),
    is_public BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER events_updated_at
    BEFORE UPDATE ON public.events
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE INDEX idx_events_org ON public.events(organization_id);
CREATE INDEX idx_events_status ON public.events(status);
CREATE INDEX idx_events_start_date ON public.events(start_date);

-- Add FK for organization_ratings -> events
ALTER TABLE public.organization_ratings
    ADD CONSTRAINT fk_org_ratings_event
    FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE SET NULL;

CREATE TABLE public.registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'waitlisted', 'cancelled')),
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    checked_in_at TIMESTAMPTZ,
    check_in_code TEXT,                -- QR code value
    -- Coordinator rates volunteer
    coordinator_rating INT CHECK (coordinator_rating BETWEEN 1 AND 5),
    coordinator_feedback TEXT,
    coordinator_rated_at TIMESTAMPTZ,
    -- Volunteer rates event/org
    volunteer_rating INT CHECK (volunteer_rating BETWEEN 1 AND 5),
    volunteer_feedback TEXT,
    volunteer_rated_at TIMESTAMPTZ,
    -- No-show tracking
    no_show_reason TEXT,
    cancellation_hours_before INT,
    metadata JSONB DEFAULT '{}',
    UNIQUE(event_id, volunteer_id)
);

CREATE INDEX idx_registrations_event ON public.registrations(event_id);
CREATE INDEX idx_registrations_volunteer ON public.registrations(volunteer_id);
CREATE INDEX idx_registrations_status ON public.registrations(status);

ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public events are viewable by everyone"
    ON public.events FOR SELECT
    USING (is_public = TRUE AND status != 'draft');

CREATE POLICY "Org owners can manage their events"
    ON public.events FOR ALL
    USING (
        organization_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Volunteers can view own registrations"
    ON public.registrations FOR SELECT
    USING (auth.uid() = volunteer_id);

CREATE POLICY "Volunteers can register"
    ON public.registrations FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = volunteer_id);

CREATE POLICY "Volunteers can cancel own registration"
    ON public.registrations FOR UPDATE
    USING (auth.uid() = volunteer_id);

CREATE POLICY "Org owners can manage registrations"
    ON public.registrations FOR ALL
    USING (
        event_id IN (
            SELECT e.id FROM public.events e
            JOIN public.organizations o ON e.organization_id = o.id
            WHERE o.owner_id = auth.uid()
        )
    );


-- ------------------------------------------------------------
-- Migration: 20260321000010_create_behavior_signals.sql
-- ------------------------------------------------------------
-- 6-signal behavioral reliability model
CREATE TABLE public.volunteer_behavior_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    signal_type TEXT NOT NULL CHECK (signal_type IN (
        'onboarding_velocity',
        'assessment_completion',
        'profile_completeness',
        'sjt_reliability',
        'contact_verification',
        'availability_specificity',
        'attendance',
        'punctuality',
        'shift_completion',
        'no_show',
        'late_cancellation'
    )),
    signal_value FLOAT NOT NULL,
    measured_at TIMESTAMPTZ DEFAULT NOW(),
    source TEXT,                       -- 'system', 'coordinator', 'event'
    source_id UUID,                    -- event_id or session_id
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_behavior_signals_volunteer ON public.volunteer_behavior_signals(volunteer_id);
CREATE INDEX idx_behavior_signals_type ON public.volunteer_behavior_signals(signal_type);

ALTER TABLE public.volunteer_behavior_signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own behavior signals"
    ON public.volunteer_behavior_signals FOR SELECT
    USING (auth.uid() = volunteer_id);

CREATE POLICY "System can insert behavior signals"
    ON public.volunteer_behavior_signals FOR INSERT
    TO authenticated
    WITH CHECK (TRUE);


-- ------------------------------------------------------------
-- Migration: 20260321000011_create_embeddings.sql
-- ------------------------------------------------------------
-- Vector embeddings for semantic volunteer matching
-- Uses Gemini text-embedding-004: 768 dimensions
CREATE TABLE public.volunteer_embeddings (
    volunteer_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    embedding VECTOR(768) NOT NULL,    -- Gemini text-embedding-004
    embedding_text TEXT,               -- the text that was embedded (for debugging)
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for approximate nearest neighbor search
-- Lists = sqrt(expected_rows): start with 100, tune after 10k+ rows
CREATE INDEX idx_volunteer_embeddings_ivfflat
    ON public.volunteer_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

ALTER TABLE public.volunteer_embeddings ENABLE ROW LEVEL SECURITY;

-- Only accessible via RPC functions (service role)
CREATE POLICY "Embeddings readable by authenticated"
    ON public.volunteer_embeddings FOR SELECT
    TO authenticated
    USING (TRUE);


-- ------------------------------------------------------------
-- Migration: 20260321000012_create_rpc_functions.sql
-- ------------------------------------------------------------
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


-- ------------------------------------------------------------
-- Migration: 20260323000013_create_expert_verifications.sql
-- ------------------------------------------------------------
-- Expert Verifications table
-- Stores one-use tokenized verification links sent by org admins or volunteers.
-- Token is a URL-safe random string (secrets.token_urlsafe(32)).
-- Rated via public /verify/{token} page — no auth required for verifier.

CREATE TABLE public.expert_verifications (
    id               UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    volunteer_id     UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_by       UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
    verifier_name    TEXT        NOT NULL,
    verifier_org     TEXT,
    competency_id    TEXT        NOT NULL,
    token            TEXT        NOT NULL UNIQUE,
    token_used       BOOLEAN     NOT NULL DEFAULT FALSE,
    token_expires_at TIMESTAMPTZ NOT NULL,
    rating           INTEGER     CHECK (rating BETWEEN 1 AND 5),
    comment          TEXT,
    verified_at      TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast token lookup (public verify page hits this on every load)
CREATE INDEX idx_expert_verifications_token
    ON public.expert_verifications (token);

-- Index for volunteer dashboard (show all verifications for a volunteer)
CREATE INDEX idx_expert_verifications_volunteer_id
    ON public.expert_verifications (volunteer_id, verified_at DESC);

-- ── RLS ──────────────────────────────────────────────────────────────
ALTER TABLE public.expert_verifications ENABLE ROW LEVEL SECURITY;

-- Volunteers can read their own verifications (for profile display)
CREATE POLICY "Volunteers read own verifications"
ON public.expert_verifications FOR SELECT
USING (auth.uid() = volunteer_id);

-- Creators (org admins) can read verifications they sent
CREATE POLICY "Creators read sent verifications"
ON public.expert_verifications FOR SELECT
USING (auth.uid() = created_by);

-- Volunteers can create verification links for themselves
CREATE POLICY "Volunteers create own verification links"
ON public.expert_verifications FOR INSERT
WITH CHECK (auth.uid() = volunteer_id);

-- Creators (org admins) can create links for any volunteer
-- NOTE: we rely on backend auth middleware to validate org membership
CREATE POLICY "Org admins create verification links"
ON public.expert_verifications FOR INSERT
WITH CHECK (auth.uid() = created_by);

-- Nobody can UPDATE or DELETE via PostgREST — only via service_role on the backend
-- (token_used and verified_at are set by the API using admin client)

-- ── Comments ─────────────────────────────────────────────────────────
COMMENT ON TABLE  public.expert_verifications IS 'One-use tokenized expert verification links with ratings';
COMMENT ON COLUMN public.expert_verifications.token IS 'URL-safe random token (secrets.token_urlsafe(32)), stored raw';
COMMENT ON COLUMN public.expert_verifications.token_used IS 'TRUE after verifier submits — token is single-use';
COMMENT ON COLUMN public.expert_verifications.token_expires_at IS 'Token valid for 7 days from creation';
COMMENT ON COLUMN public.expert_verifications.rating IS '1=Poor 2=Fair 3=Good 4=Great 5=Exceptional';
COMMENT ON COLUMN public.expert_verifications.competency_id IS 'One of the 8 AURA competency IDs';


