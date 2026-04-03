-- GDPR-CONSENT: Add legal compliance columns to profiles.
-- Fixes: age_confirmed always false, terms_version never written, no consent timestamp.
-- Surfaced by legal agent in SWARM-AUTONOMY-BRIEF-2026-04-03.
-- Required for GDPR Art. 7 (conditions for consent) + Art. 8 (16+ age threshold).

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS age_confirmed     BOOLEAN    NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS terms_version     TEXT       DEFAULT '1.0',
    ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMPTZ;

-- Backfill existing users: unknown consent state before this migration.
-- Set terms_version='unknown' so we can identify pre-GDPR accounts in audits.
-- age_confirmed stays FALSE for existing users — they must re-confirm on next login if required.
UPDATE public.profiles
    SET terms_version = 'unknown'
    WHERE terms_version IS NULL;

COMMENT ON COLUMN public.profiles.age_confirmed     IS 'User confirmed they are 16+ at signup. GDPR Art. 8.';
COMMENT ON COLUMN public.profiles.terms_version     IS 'Version of ToS accepted. "unknown" = pre-GDPR migration. "1.0" = current.';
COMMENT ON COLUMN public.profiles.terms_accepted_at IS 'Timestamp when user accepted ToS. Required for GDPR Art. 7 audit trail.';
