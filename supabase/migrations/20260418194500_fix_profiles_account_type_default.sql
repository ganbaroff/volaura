-- Fix profiles.account_type DEFAULT from 'volunteer' to 'professional'.
-- The CHECK constraint allows only ('professional','organization') but the
-- column DEFAULT was still 'volunteer' from the original schema, causing
-- constraint violations when any INSERT omits account_type explicitly
-- (e.g. e2e-setup endpoint, any future code path relying on DEFAULT).
-- G2.5 trigger sets it explicitly, but defense-in-depth requires a valid DEFAULT.

ALTER TABLE public.profiles
  ALTER COLUMN account_type SET DEFAULT 'professional';
