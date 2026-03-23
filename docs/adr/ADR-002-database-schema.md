# ADR-002: Database Schema & Data Model

**Status:** Accepted
**Date:** 2026-03-22
**Related:** [[ADR-001-system-architecture]], [[ADR-003-auth-verification]], [[ADR-005-aura-scoring]]

## Context

Volaura needs a data model that supports: user profiles, adaptive assessments, composite scoring, event management, organization accounts, referrals, notifications, and semantic search (pgvector). All data lives in Supabase PostgreSQL with RLS.

## Decision

### Entity Relationship Diagram

```
users ─────────────┬──── aura_scores (1:1 latest, 1:N history)
  │                │
  │                ├──── competency_scores (1:N, one per competency)
  │                │
  │                ├──── assessments (1:N)
  │                │        └──── assessment_responses (1:N)
  │                │
  │                ├──── event_registrations (N:M with events)
  │                │
  │                ├──── notifications (1:N)
  │                │
  │                ├──── referrals (1:N as referrer)
  │                │
  │                └──── volunteer_embeddings (1:1)
  │
  │
events ────────────┬──── event_registrations
  │                └──── event_ratings (org rates volunteer)
  │
organizations ─────┬──── events (1:N)
                   ├──── org_members (1:N)
                   └──── volunteer_requests (N:M with users)

questions ─────────────── (standalone, referenced by assessment_responses)
```

### Full Schema

```sql
-- ============================================================
-- EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for fuzzy text search

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE badge_tier AS ENUM ('platinum', 'gold', 'silver', 'bronze', 'none');
CREATE TYPE assessment_status AS ENUM ('in_progress', 'completed', 'abandoned');
CREATE TYPE question_type AS ENUM ('bars', 'mcq', 'open_text');
CREATE TYPE event_status AS ENUM ('draft', 'upcoming', 'open', 'full', 'in_progress', 'completed', 'cancelled');
CREATE TYPE registration_status AS ENUM ('registered', 'attended', 'no_show', 'cancelled');
CREATE TYPE notification_type AS ENUM ('assessment_complete', 'aura_updated', 'event_available', 'event_confirmed', 'org_interest', 'badge_earned', 'referral_joined', 'system');
CREATE TYPE verification_level AS ENUM ('self_assessed', 'org_attested', 'peer_verified');
CREATE TYPE org_role AS ENUM ('owner', 'admin', 'member');
CREATE TYPE visibility AS ENUM ('public', 'organizations_only', 'private');

-- ============================================================
-- USERS (extends Supabase auth.users)
-- ============================================================

CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE NOT NULL,
  display_name TEXT,
  email TEXT NOT NULL,
  avatar_url TEXT,
  bio TEXT,
  location TEXT,
  phone TEXT,
  expertise TEXT[] DEFAULT '{}',
  languages TEXT[] DEFAULT '{}',
  years_experience INT DEFAULT 0,
  linkedin_url TEXT,
  visibility visibility DEFAULT 'public',
  is_verified BOOLEAN DEFAULT FALSE,
  verification_level verification_level DEFAULT 'self_assessed',
  onboarding_completed BOOLEAN DEFAULT FALSE,
  locale TEXT DEFAULT 'az',
  notify_assessment_results BOOLEAN DEFAULT TRUE,
  notify_event_opportunities BOOLEAN DEFAULT TRUE,
  notify_aura_updates BOOLEAN DEFAULT TRUE,
  notify_org_requests BOOLEAN DEFAULT TRUE,
  notify_telegram BOOLEAN DEFAULT FALSE,
  telegram_chat_id BIGINT,
  referral_code TEXT UNIQUE,
  referred_by UUID REFERENCES public.profiles(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Username: lowercase, alphanumeric + underscore, 3-30 chars
ALTER TABLE public.profiles
  ADD CONSTRAINT username_format CHECK (username ~ '^[a-z0-9_]{3,30}$');

-- Auto-generate referral code
CREATE OR REPLACE FUNCTION generate_referral_code()
RETURNS TRIGGER AS $$
BEGIN
  NEW.referral_code := LOWER(SUBSTRING(MD5(NEW.id::TEXT || now()::TEXT) FROM 1 FOR 8));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_referral_code
  BEFORE INSERT ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION generate_referral_code();

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- AURA SCORES
-- ============================================================

CREATE TABLE public.aura_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  composite_score DECIMAL(5,2) NOT NULL DEFAULT 0,
  tier badge_tier NOT NULL DEFAULT 'none',
  is_elite BOOLEAN DEFAULT FALSE,
  percentile DECIMAL(5,2),
  reliability_score DECIMAL(5,2) DEFAULT 0,
  reliability_status TEXT DEFAULT 'new',
  events_attended INT DEFAULT 0,
  events_no_show INT DEFAULT 0,
  is_current BOOLEAN DEFAULT TRUE,  -- only latest is TRUE
  calculated_at TIMESTAMPTZ DEFAULT now(),

  CONSTRAINT score_range CHECK (composite_score >= 0 AND composite_score <= 100)
);

CREATE INDEX idx_aura_scores_user ON public.aura_scores(user_id, is_current);
CREATE INDEX idx_aura_scores_tier ON public.aura_scores(tier, composite_score DESC);
CREATE INDEX idx_aura_scores_leaderboard ON public.aura_scores(composite_score DESC) WHERE is_current = TRUE;

-- Only one current score per user
CREATE UNIQUE INDEX idx_aura_one_current ON public.aura_scores(user_id) WHERE is_current = TRUE;

-- ============================================================
-- COMPETENCY SCORES
-- ============================================================

CREATE TABLE public.competency_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  competency TEXT NOT NULL,
  score DECIMAL(5,2) NOT NULL DEFAULT 0,
  weight DECIMAL(3,2) NOT NULL,
  assessment_id UUID,  -- which assessment produced this score
  verification_level verification_level DEFAULT 'self_assessed',
  llm_insight TEXT,  -- AI-generated 1-line insight
  updated_at TIMESTAMPTZ DEFAULT now(),

  CONSTRAINT competency_valid CHECK (competency IN (
    'communication', 'reliability', 'english_proficiency',
    'leadership', 'event_performance', 'tech_literacy',
    'adaptability', 'empathy_safeguarding'
  )),
  CONSTRAINT score_range CHECK (score >= 0 AND score <= 100),
  CONSTRAINT weight_range CHECK (weight >= 0 AND weight <= 1),
  UNIQUE(user_id, competency)  -- one score per competency per user
);

CREATE INDEX idx_competency_user ON public.competency_scores(user_id);

-- ============================================================
-- QUESTIONS (item bank for assessments)
-- ============================================================

CREATE TABLE public.questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competency TEXT NOT NULL,
  type question_type NOT NULL,
  difficulty_level INT NOT NULL DEFAULT 2,  -- 1=easy, 2=medium, 3=hard (pseudo-IRT)
  text_az TEXT NOT NULL,
  text_en TEXT NOT NULL,
  options_az JSONB,      -- for MCQ: [{"label": "...", "value": "a", "is_correct": true}, ...]
  options_en JSONB,      -- for MCQ: same structure in English
  bars_anchors_az TEXT[], -- for BARS: 7 anchor descriptions in AZ
  bars_anchors_en TEXT[], -- for BARS: 7 anchor descriptions in EN
  max_words INT,          -- for open_text: word limit
  scoring_rubric TEXT,    -- for open_text: LLM evaluation rubric
  irt_a DECIMAL(4,2),     -- discrimination parameter (future IRT)
  irt_b DECIMAL(4,2),     -- difficulty parameter (future IRT)
  irt_c DECIMAL(4,2),     -- guessing parameter (future IRT)
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),

  CONSTRAINT competency_valid CHECK (competency IN (
    'communication', 'reliability', 'english_proficiency',
    'leadership', 'event_performance', 'tech_literacy',
    'adaptability', 'empathy_safeguarding'
  )),
  CONSTRAINT difficulty_valid CHECK (difficulty_level BETWEEN 1 AND 3)
);

CREATE INDEX idx_questions_competency ON public.questions(competency, difficulty_level) WHERE is_active = TRUE;

-- ============================================================
-- ASSESSMENTS
-- ============================================================

CREATE TABLE public.assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  competency TEXT NOT NULL,
  status assessment_status NOT NULL DEFAULT 'in_progress',
  current_difficulty INT DEFAULT 2,  -- pseudo-IRT: adjusts 1-3
  current_theta DECIMAL(4,2),        -- future: IRT theta estimate
  questions_answered INT DEFAULT 0,
  total_correct INT DEFAULT 0,
  raw_score DECIMAL(5,2),            -- before normalization
  final_score DECIMAL(5,2),          -- 0-100 normalized
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  time_elapsed_seconds INT,

  CONSTRAINT competency_valid CHECK (competency IN (
    'communication', 'reliability', 'english_proficiency',
    'leadership', 'event_performance', 'tech_literacy',
    'adaptability', 'empathy_safeguarding'
  ))
);

CREATE INDEX idx_assessments_user ON public.assessments(user_id, competency);
CREATE INDEX idx_assessments_status ON public.assessments(status) WHERE status = 'in_progress';

-- ============================================================
-- ASSESSMENT RESPONSES
-- ============================================================

CREATE TABLE public.assessment_responses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES public.assessments(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES public.questions(id),
  response_value INT,          -- 1-7 for BARS, 1-4 for MCQ
  response_text TEXT,          -- for open_text
  is_correct BOOLEAN,          -- for MCQ
  llm_score DECIMAL(5,2),     -- for open_text: LLM evaluation 0-100
  llm_feedback TEXT,           -- for open_text: LLM explanation
  time_spent_seconds INT,
  answered_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_responses_assessment ON public.assessment_responses(assessment_id);

-- ============================================================
-- ORGANIZATIONS
-- ============================================================

CREATE TABLE public.organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  name_az TEXT,
  slug TEXT UNIQUE NOT NULL,
  logo_url TEXT,
  website TEXT,
  description TEXT,
  description_az TEXT,
  is_verified BOOLEAN DEFAULT FALSE,
  api_key TEXT UNIQUE,  -- for AURA API access
  plan TEXT DEFAULT 'starter',  -- starter/growth/enterprise
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.org_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  role org_role DEFAULT 'member',
  joined_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(org_id, user_id)
);

-- ============================================================
-- EVENTS
-- ============================================================

CREATE TABLE public.events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  title_en TEXT NOT NULL,
  title_az TEXT,
  description_en TEXT,
  description_az TEXT,
  image_url TEXT,
  date_start TIMESTAMPTZ NOT NULL,
  date_end TIMESTAMPTZ,
  location TEXT,
  location_coords POINT,  -- for map display
  is_online BOOLEAN DEFAULT FALSE,
  min_aura_score DECIMAL(5,2),
  min_tier badge_tier,
  required_competencies TEXT[],
  capacity INT,
  registered_count INT DEFAULT 0,
  status event_status DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_events_status ON public.events(status, date_start);
CREATE INDEX idx_events_org ON public.events(org_id);

CREATE TRIGGER events_updated_at
  BEFORE UPDATE ON public.events
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- EVENT REGISTRATIONS
-- ============================================================

CREATE TABLE public.event_registrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  status registration_status DEFAULT 'registered',
  motivation TEXT,
  org_rating INT,  -- 1-5, organization rates volunteer after event
  org_feedback TEXT,
  registered_at TIMESTAMPTZ DEFAULT now(),
  attended_at TIMESTAMPTZ,
  UNIQUE(event_id, user_id),
  CONSTRAINT rating_range CHECK (org_rating IS NULL OR (org_rating >= 1 AND org_rating <= 5))
);

CREATE INDEX idx_registrations_user ON public.event_registrations(user_id);
CREATE INDEX idx_registrations_event ON public.event_registrations(event_id);

-- ============================================================
-- VOLUNTEER REQUESTS (org requests specific volunteer)
-- ============================================================

CREATE TABLE public.volunteer_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
  volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  event_id UUID REFERENCES public.events(id),
  message TEXT,
  status TEXT DEFAULT 'pending',  -- pending/accepted/declined
  created_at TIMESTAMPTZ DEFAULT now(),
  responded_at TIMESTAMPTZ
);

-- ============================================================
-- REFERRALS
-- ============================================================

CREATE TABLE public.referrals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referrer_id UUID NOT NULL REFERENCES public.profiles(id),
  referred_id UUID NOT NULL REFERENCES public.profiles(id),
  referral_code TEXT NOT NULL,
  status TEXT DEFAULT 'joined',  -- joined/first_assessment/active
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(referred_id)  -- each user can only be referred once
);

CREATE INDEX idx_referrals_referrer ON public.referrals(referrer_id);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================

CREATE TABLE public.notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  type notification_type NOT NULL,
  title_az TEXT NOT NULL,
  title_en TEXT NOT NULL,
  body_az TEXT,
  body_en TEXT,
  href TEXT,  -- link to navigate to
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_notifications_user ON public.notifications(user_id, is_read, created_at DESC);

-- ============================================================
-- VOLUNTEER EMBEDDINGS (pgvector for semantic search)
-- ============================================================

CREATE TABLE public.volunteer_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID UNIQUE NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  embedding VECTOR(768) NOT NULL,  -- Gemini text-embedding-004
  metadata JSONB,  -- cached: top skills, tier, location
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_embeddings_vector ON public.volunteer_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- BADGE HISTORY (tracks tier changes over time)
-- ============================================================

CREATE TABLE public.badge_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  tier badge_tier NOT NULL,
  composite_score DECIMAL(5,2) NOT NULL,
  earned_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_badge_history_user ON public.badge_history(user_id, earned_at DESC);

-- ============================================================
-- RPC FUNCTIONS
-- ============================================================

-- Semantic search for organizations finding volunteers
CREATE OR REPLACE FUNCTION match_volunteers(
  query_embedding VECTOR(768),
  match_count INT DEFAULT 20,
  min_aura FLOAT DEFAULT 0,
  filter_location TEXT DEFAULT NULL,
  filter_competencies TEXT[] DEFAULT NULL
)
RETURNS TABLE(
  user_id UUID,
  username TEXT,
  display_name TEXT,
  avatar_url TEXT,
  composite_score DECIMAL,
  tier badge_tier,
  location TEXT,
  expertise TEXT[],
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id AS user_id,
    p.username,
    p.display_name,
    p.avatar_url,
    a.composite_score,
    a.tier,
    p.location,
    p.expertise,
    1 - (ve.embedding <=> query_embedding) AS similarity
  FROM public.volunteer_embeddings ve
  JOIN public.profiles p ON ve.user_id = p.id
  JOIN public.aura_scores a ON a.user_id = p.id AND a.is_current = TRUE
  WHERE a.composite_score >= min_aura
    AND p.visibility = 'public'
    AND (filter_location IS NULL OR p.location ILIKE '%' || filter_location || '%')
    AND (filter_competencies IS NULL OR p.expertise && filter_competencies)
  ORDER BY ve.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Leaderboard query (optimized)
CREATE OR REPLACE FUNCTION get_leaderboard(
  page_size INT DEFAULT 50,
  page_offset INT DEFAULT 0,
  filter_location TEXT DEFAULT NULL
)
RETURNS TABLE(
  rank BIGINT,
  user_id UUID,
  username TEXT,
  display_name TEXT,
  avatar_url TEXT,
  composite_score DECIMAL,
  tier badge_tier,
  location TEXT,
  events_attended INT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ROW_NUMBER() OVER (ORDER BY a.composite_score DESC) AS rank,
    p.id AS user_id,
    p.username,
    p.display_name,
    p.avatar_url,
    a.composite_score,
    a.tier,
    p.location,
    a.events_attended
  FROM public.aura_scores a
  JOIN public.profiles p ON a.user_id = p.id
  WHERE a.is_current = TRUE
    AND p.visibility = 'public'
    AND (filter_location IS NULL OR p.location ILIKE '%' || filter_location || '%')
  ORDER BY a.composite_score DESC
  LIMIT page_size
  OFFSET page_offset;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- RLS POLICIES
-- ============================================================

-- Profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public profiles are viewable by everyone"
  ON public.profiles FOR SELECT
  USING (visibility = 'public');

CREATE POLICY "Users can view own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

-- AURA Scores (read-only for users, write via API)
ALTER TABLE public.aura_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own aura"
  ON public.aura_scores FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Public aura scores for public profiles"
  ON public.aura_scores FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE id = user_id AND visibility = 'public'
    )
    AND is_current = TRUE
  );

-- Competency Scores
ALTER TABLE public.competency_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own competency scores"
  ON public.competency_scores FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Public competency scores"
  ON public.competency_scores FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE id = user_id AND visibility = 'public'
    )
  );

-- Assessments (private to user)
ALTER TABLE public.assessments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own assessments"
  ON public.assessments FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own assessments"
  ON public.assessments FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Assessment Responses (private)
ALTER TABLE public.assessment_responses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own responses"
  ON public.assessment_responses FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.assessments
      WHERE id = assessment_id AND user_id = auth.uid()
    )
  );

-- Events (public read)
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Events are viewable by everyone"
  ON public.events FOR SELECT
  USING (status != 'draft');

-- Event Registrations
ALTER TABLE public.event_registrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own registrations"
  ON public.event_registrations FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can register for events"
  ON public.event_registrations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Notifications (private)
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own notifications"
  ON public.notifications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications"
  ON public.notifications FOR UPDATE
  USING (auth.uid() = user_id);

-- Organizations (public read)
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Verified orgs are viewable"
  ON public.organizations FOR SELECT
  USING (is_verified = TRUE);

-- Referrals
ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own referrals"
  ON public.referrals FOR SELECT
  USING (auth.uid() = referrer_id OR auth.uid() = referred_id);
```

## Table Summary

| Table | Rows (est. 6mo) | Access Pattern | RLS |
|-------|-----------------|----------------|-----|
| profiles | 10,000 | R: public, W: owner | ✓ |
| aura_scores | 10,000 (current) + 30K history | R: public (current), W: API only | ✓ |
| competency_scores | 80,000 (10K × 8) | R: public, W: API only | ✓ |
| questions | 400 (50 × 8 competencies) | R: API only | Admin |
| assessments | 50,000 | R: owner, W: owner+API | ✓ |
| assessment_responses | 500,000 | R: owner, W: owner | ✓ |
| events | 200 | R: public, W: org admin | ✓ |
| event_registrations | 5,000 | R: owner+org, W: owner | ✓ |
| organizations | 50 | R: public (verified), W: org admin | ✓ |
| notifications | 100,000 | R: owner, W: system | ✓ |
| volunteer_embeddings | 10,000 | R: RPC only, W: API | Admin |
| badge_history | 20,000 | R: owner+public, W: API | ✓ |
| referrals | 5,000 | R: owner, W: system | ✓ |

## Indexes Strategy

- **Leaderboard**: composite index on `aura_scores(composite_score DESC) WHERE is_current`
- **Semantic search**: IVFFlat on embeddings with 100 lists (optimal for <100K rows)
- **Assessment lookup**: `assessments(user_id, competency)` for "has user completed X?"
- **Notifications**: `notifications(user_id, is_read, created_at DESC)` for unread-first feed

## Migration Strategy

One migration file per logical unit:
1. `001_extensions.sql` — pgvector, pg_trgm
2. `002_enums.sql` — all type definitions
3. `003_profiles.sql` — profiles + triggers
4. `004_aura_scoring.sql` — aura_scores + competency_scores + badge_history
5. `005_assessment.sql` — questions + assessments + responses
6. `006_events.sql` — organizations + events + registrations
7. `007_social.sql` — referrals + notifications + volunteer_requests
8. `008_search.sql` — embeddings + RPC functions
9. `009_rls.sql` — all RLS policies
10. `010_seed.sql` — initial questions, demo org, major event data

## Action Items

1. [ ] Create Supabase project
2. [ ] Run migrations in order
3. [ ] Write seed data (50+ questions for Communication, English, Reliability)
4. [ ] Test RLS policies with anon/authenticated/service_role keys
5. [ ] Set up pg_cron for scheduled AURA recalculation
