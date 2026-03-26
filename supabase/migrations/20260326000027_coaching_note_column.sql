-- Add coaching_note column to store Gemini coaching recommendations per session
-- JSONB: stores list of {title, description, action} objects
-- Null = not yet generated; populated on first POST /{session_id}/coaching call
ALTER TABLE public.assessment_sessions
    ADD COLUMN IF NOT EXISTS coaching_note JSONB;
