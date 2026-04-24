-- Update profiles.account_type CHECK constraint: volunteer → professional.
-- 20260416095019_volunteer_to_professional.sql renames all 'volunteer' rows to
-- 'professional', and 20260418194500 sets DEFAULT='professional'. Without this
-- migration the CHECK constraint still blocks 'professional', making every bare
-- INSERT into profiles fail on a fresh DB (including CI and new sign-ups).

ALTER TABLE public.profiles
    DROP CONSTRAINT IF EXISTS profiles_account_type_check;

ALTER TABLE public.profiles
    ADD CONSTRAINT profiles_account_type_check
    CHECK (account_type IN ('professional', 'organization'));
