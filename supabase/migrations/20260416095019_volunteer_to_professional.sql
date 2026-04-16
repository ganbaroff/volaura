-- Sprint Task 2: Close the three-layer positioning split.
-- Locales already say "professional", frontend displays "I'm a professional",
-- but DB stores account_type='volunteer' for every individual user.
-- Constitution Sprint E1 (2026-03-29): "NEVER say volunteer platform."
--
-- This migration is idempotent and reversible:
--   Rollback: UPDATE profiles SET account_type='volunteer' WHERE account_type='professional';

-- 1. Rename existing individual accounts
UPDATE public.profiles
SET account_type = 'professional'
WHERE account_type = 'volunteer';

-- 2. Update the signup-status view/query defaults if any reference 'volunteer'
-- (signup flow already sends 'professional' after frontend fix — this catches
-- any rows created between code deploy and migration apply)

-- 3. Update role_levels enum reference in assessment schemas
-- Note: role_level column in assessment_sessions also accepts 'volunteer' —
-- existing sessions keep their historical value (no rewrite of completed data).
-- New sessions will use 'professional' from the frontend.
