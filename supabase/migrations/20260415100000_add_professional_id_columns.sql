-- Phase 1: Add professional_id alias columns alongside volunteer_id
-- Non-breaking, additive-only migration. Both column names work simultaneously.
-- Phase 2 (separate migration, needs downtime): drop volunteer_id, rename tables.
--
-- Tables affected:
--   assessment_sessions, aura_scores, volunteer_badges,
--   org_volunteer_records, registrations, volunteer_behavior_signals,
--   volunteer_embeddings, expert_verifications

BEGIN;

-- assessment_sessions: add professional_id as generated column
ALTER TABLE public.assessment_sessions
  ADD COLUMN IF NOT EXISTS professional_id UUID GENERATED ALWAYS AS (volunteer_id) STORED;

-- aura_scores: add professional_id as generated column
ALTER TABLE public.aura_scores
  ADD COLUMN IF NOT EXISTS professional_id UUID GENERATED ALWAYS AS (volunteer_id) STORED;

-- volunteer_badges: add professional_id as generated column
ALTER TABLE public.volunteer_badges
  ADD COLUMN IF NOT EXISTS professional_id UUID GENERATED ALWAYS AS (volunteer_id) STORED;

-- org_volunteer_records: add professional_id as generated column
ALTER TABLE public.org_volunteer_records
  ADD COLUMN IF NOT EXISTS professional_id UUID GENERATED ALWAYS AS (volunteer_id) STORED;

-- registrations: add professional_id as generated column
ALTER TABLE public.registrations
  ADD COLUMN IF NOT EXISTS professional_id UUID GENERATED ALWAYS AS (volunteer_id) STORED;

-- volunteer_behavior_signals: add professional_id as generated column
ALTER TABLE public.volunteer_behavior_signals
  ADD COLUMN IF NOT EXISTS professional_id UUID GENERATED ALWAYS AS (volunteer_id) STORED;

-- volunteer_embeddings: add professional_id as generated column
ALTER TABLE public.volunteer_embeddings
  ADD COLUMN IF NOT EXISTS professional_id UUID GENERATED ALWAYS AS (volunteer_id) STORED;

-- expert_verifications: add professional_id as generated column
ALTER TABLE public.expert_verifications
  ADD COLUMN IF NOT EXISTS professional_id UUID GENERATED ALWAYS AS (volunteer_id) STORED;

-- Create views with professional naming for new code to use
CREATE OR REPLACE VIEW public.professional_badges AS
  SELECT *, volunteer_id AS professional_id_v
  FROM public.volunteer_badges;

CREATE OR REPLACE VIEW public.professional_behavior_signals AS
  SELECT *, volunteer_id AS professional_id_v
  FROM public.volunteer_behavior_signals;

CREATE OR REPLACE VIEW public.professional_embeddings AS
  SELECT *, volunteer_id AS professional_id_v
  FROM public.volunteer_embeddings;

COMMIT;
