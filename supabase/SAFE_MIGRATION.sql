-- ============================================================
-- Volaura — SAFE Idempotent Migration Script
-- Run this in Supabase SQL Editor — safe to run multiple times
-- Date: 2026-03-24
--
-- This script uses CREATE TABLE IF NOT EXISTS and
-- CREATE OR REPLACE for all objects. Safe to re-run.
-- ============================================================

-- Step 1: Extensions (always safe to re-run)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Step 2: Helper function (always safe to re-run)
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Tables (IF NOT EXISTS = safe to re-run)
CREATE TABLE IF NOT EXISTS public.profiles (
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

CREATE TABLE IF NOT EXISTS public.competencies (
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

CREATE TABLE IF NOT EXISTS public.questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competency_id UUID REFERENCES public.competencies(id) ON DELETE SET NULL,
    difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard', 'expert')),
    type TEXT NOT NULL CHECK (type IN ('mcq', 'open_ended')),
    scenario_en TEXT NOT NULL,
    scenario_az TEXT NOT NULL,
    options JSONB,
    correct_answer TEXT,
    expected_concepts JSONB,
    cefr_level TEXT,
    irt_a FLOAT DEFAULT 1.0,
    irt_b FLOAT DEFAULT 0.0,
    irt_c FLOAT DEFAULT 0.0,
    discrimination_index FLOAT DEFAULT 0.0,
    times_shown INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    is_sjt_reliability BOOLEAN DEFAULT FALSE,
    lie_detector_flag BOOLEAN DEFAULT FALSE,
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

CREATE TABLE IF NOT EXISTS public.assessment_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    competency_id UUID REFERENCES public.competencies(id),
    status TEXT DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'abandoned', 'flagged')),
    language TEXT DEFAULT 'en' CHECK (language IN ('en', 'az')),
    question_ids UUID[] NOT NULL DEFAULT '{}',
    current_question_idx INT DEFAULT 0,
    answers JSONB DEFAULT '[]',
    theta_estimate FLOAT DEFAULT 0.0,
    theta_se FLOAT DEFAULT 1.0,
    fast_responses INT DEFAULT 0,
    flag_reason TEXT,
    aura_result JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '2 hours',
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.aura_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID UNIQUE NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    total_score FLOAT NOT NULL DEFAULT 0,
    badge_tier TEXT DEFAULT 'none'
        CHECK (badge_tier IN ('none', 'bronze', 'silver', 'gold', 'platinum')),
    elite_status BOOLEAN DEFAULT FALSE,
    competency_scores JSONB NOT NULL DEFAULT '{}',
    reliability_score FLOAT DEFAULT 50.0,
    reliability_status TEXT DEFAULT 'pending'
        CHECK (reliability_status IN ('pending', 'verified', 'proven')),
    events_attended INT DEFAULT 0,
    events_no_show INT DEFAULT 0,
    events_late INT DEFAULT 0,
    percentile_rank FLOAT,
    aura_history JSONB DEFAULT '[]',
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.badges (
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

CREATE TABLE IF NOT EXISTS public.volunteer_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    badge_id UUID NOT NULL REFERENCES public.badges(id),
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    open_badges_url TEXT,
    linkedin_exported_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    UNIQUE(volunteer_id, badge_id)
);

CREATE TABLE IF NOT EXISTS public.organizations (
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

CREATE TABLE IF NOT EXISTS public.organization_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_id UUID,
    rating FLOAT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(volunteer_id, organization_id, event_id)
);

CREATE TABLE IF NOT EXISTS public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    title_en TEXT NOT NULL,
    title_az TEXT NOT NULL,
    description_en TEXT,
    description_az TEXT,
    event_type TEXT,
    location TEXT,
    location_coords JSONB,
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

CREATE TABLE IF NOT EXISTS public.registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'waitlisted', 'cancelled')),
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    checked_in_at TIMESTAMPTZ,
    check_in_code TEXT,
    coordinator_rating INT CHECK (coordinator_rating BETWEEN 1 AND 5),
    coordinator_feedback TEXT,
    coordinator_rated_at TIMESTAMPTZ,
    volunteer_rating INT CHECK (volunteer_rating BETWEEN 1 AND 5),
    volunteer_feedback TEXT,
    volunteer_rated_at TIMESTAMPTZ,
    no_show_reason TEXT,
    cancellation_hours_before INT,
    metadata JSONB DEFAULT '{}',
    UNIQUE(event_id, volunteer_id)
);

CREATE TABLE IF NOT EXISTS public.volunteer_behavior_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    signal_type TEXT NOT NULL CHECK (signal_type IN (
        'onboarding_velocity', 'assessment_completion', 'profile_completeness',
        'sjt_reliability', 'contact_verification', 'availability_specificity',
        'attendance', 'punctuality', 'shift_completion', 'no_show', 'late_cancellation'
    )),
    signal_value FLOAT NOT NULL,
    measured_at TIMESTAMPTZ DEFAULT NOW(),
    source TEXT,
    source_id UUID,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS public.volunteer_embeddings (
    volunteer_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    embedding VECTOR(768) NOT NULL,
    embedding_text TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.expert_verifications (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    verifier_name TEXT NOT NULL,
    verifier_org TEXT,
    competency_id TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    token_used BOOLEAN NOT NULL DEFAULT FALSE,
    token_expires_at TIMESTAMPTZ NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Step 4: Indexes (CREATE INDEX IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_volunteer ON public.assessment_sessions(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_status ON public.assessment_sessions(status);
CREATE INDEX IF NOT EXISTS idx_aura_scores_total ON public.aura_scores(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_aura_scores_badge ON public.aura_scores(badge_tier);
CREATE INDEX IF NOT EXISTS idx_volunteer_badges_volunteer ON public.volunteer_badges(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_organizations_owner ON public.organizations(owner_id);
CREATE INDEX IF NOT EXISTS idx_events_org ON public.events(organization_id);
CREATE INDEX IF NOT EXISTS idx_events_status ON public.events(status);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON public.events(start_date);
CREATE INDEX IF NOT EXISTS idx_registrations_event ON public.registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_registrations_volunteer ON public.registrations(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_registrations_status ON public.registrations(status);
CREATE INDEX IF NOT EXISTS idx_behavior_signals_volunteer ON public.volunteer_behavior_signals(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_behavior_signals_type ON public.volunteer_behavior_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_expert_verifications_token ON public.expert_verifications(token);
CREATE INDEX IF NOT EXISTS idx_expert_verifications_volunteer_id ON public.expert_verifications(volunteer_id, verified_at DESC);

-- Step 5: Triggers (DROP IF EXISTS + CREATE to avoid duplicates)
DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS questions_updated_at ON public.questions;
CREATE TRIGGER questions_updated_at BEFORE UPDATE ON public.questions
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS organizations_updated_at ON public.organizations;
CREATE TRIGGER organizations_updated_at BEFORE UPDATE ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS events_updated_at ON public.events;
CREATE TRIGGER events_updated_at BEFORE UPDATE ON public.events
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Step 6: FK for org_ratings -> events (safe with IF NOT EXISTS pattern)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_org_ratings_event'
    ) THEN
        ALTER TABLE public.organization_ratings
            ADD CONSTRAINT fk_org_ratings_event
            FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Step 7: Views (CREATE OR REPLACE = safe)
CREATE OR REPLACE VIEW public.organization_trust_scores AS
SELECT
    organization_id,
    COUNT(*) AS rating_count,
    CASE WHEN COUNT(*) >= 5
        THEN ROUND((AVG(rating) * 20)::numeric, 1)
        ELSE NULL
    END AS trust_score
FROM public.organization_ratings
GROUP BY organization_id;

-- Step 8: RLS (safe to re-enable, policies use IF NOT EXISTS pattern)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.competencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.aura_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_behavior_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expert_verifications ENABLE ROW LEVEL SECURITY;

-- Step 9: RLS Policies (DROP + CREATE to avoid "already exists" errors)
-- profiles
DROP POLICY IF EXISTS "Public profiles are viewable by everyone" ON public.profiles;
CREATE POLICY "Public profiles are viewable by everyone" ON public.profiles FOR SELECT USING (is_public = TRUE);
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- competencies
DROP POLICY IF EXISTS "Competencies are viewable by everyone" ON public.competencies;
CREATE POLICY "Competencies are viewable by everyone" ON public.competencies FOR SELECT USING (TRUE);

-- questions
DROP POLICY IF EXISTS "Authenticated users can view active questions" ON public.questions;
CREATE POLICY "Authenticated users can view active questions" ON public.questions FOR SELECT TO authenticated USING (is_active = TRUE AND needs_review = FALSE);

-- assessment_sessions
DROP POLICY IF EXISTS "Users can view own sessions" ON public.assessment_sessions;
CREATE POLICY "Users can view own sessions" ON public.assessment_sessions FOR SELECT USING (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "Users can insert own sessions" ON public.assessment_sessions;
CREATE POLICY "Users can insert own sessions" ON public.assessment_sessions FOR INSERT WITH CHECK (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "Users can update own sessions" ON public.assessment_sessions;
CREATE POLICY "Users can update own sessions" ON public.assessment_sessions FOR UPDATE USING (auth.uid() = volunteer_id);

-- aura_scores
DROP POLICY IF EXISTS "AURA scores are publicly readable" ON public.aura_scores;
CREATE POLICY "AURA scores are publicly readable" ON public.aura_scores FOR SELECT USING (TRUE);
DROP POLICY IF EXISTS "System can insert AURA scores" ON public.aura_scores;
CREATE POLICY "System can insert AURA scores" ON public.aura_scores FOR INSERT WITH CHECK (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "System can update AURA scores" ON public.aura_scores;
CREATE POLICY "System can update AURA scores" ON public.aura_scores FOR UPDATE USING (auth.uid() = volunteer_id);

-- badges
DROP POLICY IF EXISTS "Badges are viewable by everyone" ON public.badges;
CREATE POLICY "Badges are viewable by everyone" ON public.badges FOR SELECT USING (TRUE);
DROP POLICY IF EXISTS "Users can view own badges" ON public.volunteer_badges;
CREATE POLICY "Users can view own badges" ON public.volunteer_badges FOR SELECT USING (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "Public can view volunteer badges" ON public.volunteer_badges;
CREATE POLICY "Public can view volunteer badges" ON public.volunteer_badges FOR SELECT USING (TRUE);

-- organizations
DROP POLICY IF EXISTS "Organizations are publicly viewable" ON public.organizations;
CREATE POLICY "Organizations are publicly viewable" ON public.organizations FOR SELECT USING (is_active = TRUE);
DROP POLICY IF EXISTS "Owners can update their org" ON public.organizations;
CREATE POLICY "Owners can update their org" ON public.organizations FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS "Owners can insert org" ON public.organizations;
CREATE POLICY "Owners can insert org" ON public.organizations FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS "Authenticated users can rate organizations" ON public.organization_ratings;
CREATE POLICY "Authenticated users can rate organizations" ON public.organization_ratings FOR INSERT TO authenticated WITH CHECK (auth.uid() = volunteer_id);

-- events
DROP POLICY IF EXISTS "Public events are viewable by everyone" ON public.events;
CREATE POLICY "Public events are viewable by everyone" ON public.events FOR SELECT USING (is_public = TRUE AND status != 'draft');
DROP POLICY IF EXISTS "Org owners can manage their events" ON public.events;
CREATE POLICY "Org owners can manage their events" ON public.events FOR ALL USING (organization_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

-- registrations
DROP POLICY IF EXISTS "Volunteers can view own registrations" ON public.registrations;
CREATE POLICY "Volunteers can view own registrations" ON public.registrations FOR SELECT USING (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "Volunteers can register" ON public.registrations;
CREATE POLICY "Volunteers can register" ON public.registrations FOR INSERT TO authenticated WITH CHECK (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "Volunteers can cancel own registration" ON public.registrations;
CREATE POLICY "Volunteers can cancel own registration" ON public.registrations FOR UPDATE USING (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "Org owners can manage registrations" ON public.registrations;
CREATE POLICY "Org owners can manage registrations" ON public.registrations FOR ALL USING (event_id IN (SELECT e.id FROM public.events e JOIN public.organizations o ON e.organization_id = o.id WHERE o.owner_id = auth.uid()));

-- behavior_signals
DROP POLICY IF EXISTS "Users can view own behavior signals" ON public.volunteer_behavior_signals;
CREATE POLICY "Users can view own behavior signals" ON public.volunteer_behavior_signals FOR SELECT USING (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "System can insert behavior signals" ON public.volunteer_behavior_signals;
CREATE POLICY "System can insert behavior signals" ON public.volunteer_behavior_signals FOR INSERT TO authenticated WITH CHECK (TRUE);

-- embeddings
DROP POLICY IF EXISTS "Embeddings readable by authenticated" ON public.volunteer_embeddings;
CREATE POLICY "Embeddings readable by authenticated" ON public.volunteer_embeddings FOR SELECT TO authenticated USING (TRUE);

-- expert_verifications
DROP POLICY IF EXISTS "Volunteers read own verifications" ON public.expert_verifications;
CREATE POLICY "Volunteers read own verifications" ON public.expert_verifications FOR SELECT USING (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "Creators read sent verifications" ON public.expert_verifications;
CREATE POLICY "Creators read sent verifications" ON public.expert_verifications FOR SELECT USING (auth.uid() = created_by);
DROP POLICY IF EXISTS "Volunteers create own verification links" ON public.expert_verifications;
CREATE POLICY "Volunteers create own verification links" ON public.expert_verifications FOR INSERT WITH CHECK (auth.uid() = volunteer_id);
DROP POLICY IF EXISTS "Org admins create verification links" ON public.expert_verifications;
CREATE POLICY "Org admins create verification links" ON public.expert_verifications FOR INSERT WITH CHECK (auth.uid() = created_by);

-- Step 10: RPC Functions (CREATE OR REPLACE = safe)
CREATE OR REPLACE FUNCTION public.match_volunteers(
    query_embedding VECTOR(768),
    match_count INT DEFAULT 10,
    min_aura FLOAT DEFAULT 0,
    badge_tier_filter TEXT DEFAULT NULL
)
RETURNS TABLE(volunteer_id UUID, similarity FLOAT, total_score FLOAT, badge_tier TEXT, username TEXT, display_name TEXT, avatar_url TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT ve.volunteer_id, 1 - (ve.embedding <=> query_embedding) AS similarity,
        a.total_score, a.badge_tier, p.username, p.display_name, p.avatar_url
    FROM public.volunteer_embeddings ve
    JOIN public.aura_scores a ON ve.volunteer_id = a.volunteer_id
    JOIN public.profiles p ON ve.volunteer_id = p.id
    WHERE a.total_score >= min_aura AND p.is_public = TRUE
        AND (badge_tier_filter IS NULL OR a.badge_tier = badge_tier_filter)
    ORDER BY ve.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.calculate_aura_score(p_competency_scores JSONB)
RETURNS FLOAT AS $$
DECLARE
    v_total FLOAT := 0;
    v_weights JSONB := '{"communication":0.20,"reliability":0.15,"english_proficiency":0.15,"leadership":0.15,"event_performance":0.10,"tech_literacy":0.10,"adaptability":0.10,"empathy_safeguarding":0.05}';
    v_slug TEXT; v_weight FLOAT; v_score FLOAT;
BEGIN
    FOR v_slug, v_weight IN SELECT key, value::FLOAT FROM jsonb_each_text(v_weights) LOOP
        v_score := COALESCE((p_competency_scores ->> v_slug)::FLOAT, 0);
        v_total := v_total + (v_score * v_weight);
    END LOOP;
    RETURN ROUND(v_total::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION public.get_badge_tier(p_total_score FLOAT)
RETURNS TEXT AS $$
BEGIN
    IF p_total_score >= 90 THEN RETURN 'platinum';
    ELSIF p_total_score >= 75 THEN RETURN 'gold';
    ELSIF p_total_score >= 60 THEN RETURN 'silver';
    ELSIF p_total_score >= 40 THEN RETURN 'bronze';
    ELSE RETURN 'none'; END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION public.calculate_reliability_score(p_volunteer_id UUID)
RETURNS FLOAT AS $$
DECLARE
    v_events_attended INT; v_behavioral_score FLOAT; v_proven_score FLOAT;
    v_behavioral_weight FLOAT; v_final_score FLOAT;
    w_onboarding FLOAT := 0.15; w_assessment FLOAT := 0.15; w_profile FLOAT := 0.10;
    w_sjt FLOAT := 0.30; w_contact FLOAT := 0.15; w_availability FLOAT := 0.15;
    w_attendance FLOAT := 0.40; w_punctuality FLOAT := 0.20;
    w_coordinator FLOAT := 0.25; w_shift FLOAT := 0.15;
BEGIN
    SELECT COALESCE(events_attended, 0) INTO v_events_attended FROM public.aura_scores WHERE volunteer_id = p_volunteer_id;
    SELECT COALESCE(SUM(CASE signal_type
        WHEN 'onboarding_velocity' THEN signal_value * w_onboarding
        WHEN 'assessment_completion' THEN signal_value * w_assessment
        WHEN 'profile_completeness' THEN signal_value * w_profile
        WHEN 'sjt_reliability' THEN signal_value * w_sjt
        WHEN 'contact_verification' THEN signal_value * w_contact
        WHEN 'availability_specificity' THEN signal_value * w_availability
        ELSE 0 END), 30) INTO v_behavioral_score
    FROM (SELECT DISTINCT ON (signal_type) signal_type, signal_value
        FROM public.volunteer_behavior_signals WHERE volunteer_id = p_volunteer_id
        AND signal_type IN ('onboarding_velocity','assessment_completion','profile_completeness','sjt_reliability','contact_verification','availability_specificity')
        ORDER BY signal_type, measured_at DESC) latest;
    v_behavioral_score := LEAST(v_behavioral_score, 70);
    SELECT COALESCE(SUM(CASE signal_type
        WHEN 'attendance' THEN signal_value * w_attendance
        WHEN 'punctuality' THEN signal_value * w_punctuality
        WHEN 'shift_completion' THEN signal_value * w_shift
        ELSE 0 END), 0) INTO v_proven_score
    FROM (SELECT signal_type, AVG(signal_value) AS signal_value
        FROM public.volunteer_behavior_signals WHERE volunteer_id = p_volunteer_id
        AND signal_type IN ('attendance','punctuality','shift_completion') GROUP BY signal_type) agg;
    SELECT v_proven_score + COALESCE(AVG(coordinator_rating) * 20 * w_coordinator, 0)
        INTO v_proven_score FROM public.registrations
        WHERE volunteer_id = p_volunteer_id AND coordinator_rating IS NOT NULL;
    v_behavioral_weight := GREATEST(0, 1.0 - v_events_attended * 0.20);
    v_final_score := (v_behavioral_score * v_behavioral_weight) + (v_proven_score * (1 - v_behavioral_weight));
    RETURN ROUND(LEAST(GREATEST(v_final_score, 0), 100)::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.upsert_aura_score(p_volunteer_id UUID, p_competency_scores JSONB)
RETURNS public.aura_scores AS $$
DECLARE
    v_total FLOAT; v_tier TEXT; v_elite BOOLEAN; v_result public.aura_scores;
    v_slug TEXT; v_score FLOAT; v_high_count INT := 0;
BEGIN
    v_total := public.calculate_aura_score(p_competency_scores);
    v_tier := public.get_badge_tier(v_total);
    FOR v_slug, v_score IN SELECT key, value::FLOAT FROM jsonb_each_text(p_competency_scores) LOOP
        IF v_score >= 75 THEN v_high_count := v_high_count + 1; END IF;
    END LOOP;
    v_elite := (v_total >= 75 AND v_high_count >= 2);
    INSERT INTO public.aura_scores (volunteer_id, total_score, badge_tier, elite_status, competency_scores, last_updated)
    VALUES (p_volunteer_id, v_total, v_tier, v_elite, p_competency_scores, NOW())
    ON CONFLICT (volunteer_id) DO UPDATE SET
        total_score = v_total, badge_tier = v_tier, elite_status = v_elite,
        competency_scores = p_competency_scores,
        aura_history = aura_scores.aura_history || jsonb_build_array(jsonb_build_object('date', NOW(), 'total_score', v_total, 'badge_tier', v_tier)),
        last_updated = NOW()
    RETURNING * INTO v_result;
    RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 11: IVFFlat index (needs data to work, safe to create)
-- Note: This may fail if no data exists yet, which is fine
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_volunteer_embeddings_ivfflat') THEN
        CREATE INDEX idx_volunteer_embeddings_ivfflat ON public.volunteer_embeddings
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'IVFFlat index creation skipped (needs data first): %', SQLERRM;
END $$;

-- ============================================================
-- DONE! All tables, indexes, triggers, RLS, and functions created.
-- Next step: run seed.sql to insert competencies + sample questions.
-- ============================================================
