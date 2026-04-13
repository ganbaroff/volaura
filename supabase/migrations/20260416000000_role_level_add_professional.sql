-- Add "professional" to assessment_sessions role_level CHECK constraint.
-- The volunteer→professional migration added "professional" to the Pydantic schema
-- but missed the DB CHECK constraint, causing 500 errors on assessment start.
ALTER TABLE public.assessment_sessions
DROP CONSTRAINT IF EXISTS assessment_sessions_role_level_check;

ALTER TABLE public.assessment_sessions
ADD CONSTRAINT assessment_sessions_role_level_check
CHECK (role_level IN ('volunteer', 'professional', 'coordinator', 'specialist', 'manager', 'senior_manager'));
