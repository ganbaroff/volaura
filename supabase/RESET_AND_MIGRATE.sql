-- ============================================================
-- Volaura — RESET + MIGRATE
-- Drops all existing tables and recreates from scratch
-- Run this in Supabase SQL Editor if you get "already exists" errors
-- ============================================================

-- Drop in reverse dependency order
DROP TABLE IF EXISTS public.volunteer_behavior_signals CASCADE;
DROP TABLE IF EXISTS public.volunteer_embeddings CASCADE;
DROP TABLE IF EXISTS public.volunteer_badges CASCADE;
DROP TABLE IF EXISTS public.badges CASCADE;
DROP TABLE IF EXISTS public.registrations CASCADE;
DROP TABLE IF EXISTS public.organization_ratings CASCADE;
DROP TABLE IF EXISTS public.events CASCADE;
DROP TABLE IF EXISTS public.organizations CASCADE;
DROP TABLE IF EXISTS public.expert_verifications CASCADE;
DROP TABLE IF EXISTS public.aura_scores CASCADE;
DROP TABLE IF EXISTS public.assessment_sessions CASCADE;
DROP TABLE IF EXISTS public.questions CASCADE;
DROP TABLE IF EXISTS public.competencies CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;

-- Drop views
DROP VIEW IF EXISTS public.organization_trust_scores CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS public.handle_updated_at() CASCADE;
DROP FUNCTION IF EXISTS public.match_volunteers(VECTOR(768), INT, FLOAT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS public.calculate_aura_score(JSONB) CASCADE;
DROP FUNCTION IF EXISTS public.get_badge_tier(FLOAT) CASCADE;
DROP FUNCTION IF EXISTS public.calculate_reliability_score(UUID) CASCADE;
DROP FUNCTION IF EXISTS public.upsert_aura_score(UUID, JSONB) CASCADE;

-- Now safe to run migrations
-- Extensions (idempotent)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
