-- Add metadata JSONB column to assessment_sessions
-- Stores: energy_level (Constitution Law 2), article22_consent_at (GDPR)
ALTER TABLE public.assessment_sessions
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

COMMENT ON COLUMN public.assessment_sessions.metadata IS 'Session metadata: energy_level, article22_consent_at, future extensible fields';
