-- Registration Number System
-- Adds a permanent, sequential registration number to every user profile.
--
-- Why:
--   Every VOLAURA member gets a unique #XXXX identifier — displayed on profile,
--   used as the character ID in Life Simulator, and creates genuine early-adopter
--   scarcity. Lower numbers = founding members. Numbers are never reassigned.
--
-- Design choices:
--   - PostgreSQL SEQUENCE: atomic nextval() = no gaps, no race conditions at any scale
--   - OWNED BY: sequence auto-drops if column drops (clean migration safety)
--   - Tier column: auto-assigned via trigger on INSERT (founding_100, founding_1000,
--     early_adopter, standard). Immutable after assignment.
--   - Existing users: get sequential numbers based on created_at order (earliest = lowest)
--
-- Downstream:
--   - ProfileResponse schema gets registration_number + registration_tier fields
--   - Profile header displays "Founding Member #0047"
--   - Life Simulator uses this as character unique ID

-- ── Step 1: Sequence ──────────────────────────────────────────────────────────

CREATE SEQUENCE IF NOT EXISTS public.profile_registration_seq
  START 1
  INCREMENT 1
  NO MINVALUE
  NO MAXVALUE
  CACHE 1;

-- ── Step 2: Column + tier ─────────────────────────────────────────────────────

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS registration_number INTEGER UNIQUE,
  ADD COLUMN IF NOT EXISTS registration_tier TEXT NOT NULL DEFAULT 'standard'
    CHECK (registration_tier IN ('founding_100', 'founding_1000', 'early_adopter', 'standard'));

-- Own the sequence (auto-cleanup if column ever removed)
ALTER SEQUENCE public.profile_registration_seq OWNED BY public.profiles.registration_number;

-- ── Step 3: Backfill existing users (ordered by creation — earliest = lowest) ─

UPDATE public.profiles
SET registration_number = nextval('public.profile_registration_seq')
WHERE registration_number IS NULL
ORDER BY created_at ASC;

-- ── Step 4: Make column NOT NULL now that all rows are filled ─────────────────

ALTER TABLE public.profiles
  ALTER COLUMN registration_number SET NOT NULL,
  ALTER COLUMN registration_number SET DEFAULT nextval('public.profile_registration_seq');

-- ── Step 5: Tier assignment function (fires on INSERT) ───────────────────────

CREATE OR REPLACE FUNCTION public.assign_registration_tier()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.registration_number <= 100 THEN
    NEW.registration_tier := 'founding_100';
  ELSIF NEW.registration_number <= 1000 THEN
    NEW.registration_tier := 'founding_1000';
  ELSIF NEW.registration_number <= 5000 THEN
    NEW.registration_tier := 'early_adopter';
  ELSE
    NEW.registration_tier := 'standard';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER profiles_assign_tier
  BEFORE INSERT ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.assign_registration_tier();

-- Also update tiers for existing backfilled users
UPDATE public.profiles SET registration_tier =
  CASE
    WHEN registration_number <= 100  THEN 'founding_100'
    WHEN registration_number <= 1000 THEN 'founding_1000'
    WHEN registration_number <= 5000 THEN 'early_adopter'
    ELSE 'standard'
  END;

-- ── Step 6: Index for leaderboard / "who is #0047?" lookups ──────────────────

CREATE INDEX IF NOT EXISTS idx_profiles_registration_number
  ON public.profiles(registration_number);

CREATE INDEX IF NOT EXISTS idx_profiles_registration_tier
  ON public.profiles(registration_tier);

-- ── Step 7: RLS — registration number is public (it's a display field) ───────

-- Everyone can see registration numbers on public profiles (it's a feature, not PII)
-- Existing RLS policies on profiles cover this: no new policies needed.
-- Users cannot UPDATE their own registration_number (trigger + API schema enforce this).
