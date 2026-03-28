-- Sprint 4: Add missing profile columns that exist in Pydantic schema but were never migrated.
-- These were likely added via Supabase Studio in Sprint 1. Using IF NOT EXISTS is safe.
-- Affected: profile creation (POST /api/profiles), onboarding flow, org volunteer browse.

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS account_type TEXT NOT NULL DEFAULT 'volunteer'
        CHECK (account_type IN ('volunteer', 'organization')),
    ADD COLUMN IF NOT EXISTS visible_to_orgs BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS org_type TEXT
        CHECK (org_type IN ('ngo', 'corporate', 'government', 'startup', 'academic', 'other'));

-- Index for volunteer browse query: WHERE visible_to_orgs = TRUE
CREATE INDEX IF NOT EXISTS idx_profiles_visible_to_orgs
    ON public.profiles (visible_to_orgs)
    WHERE visible_to_orgs = TRUE;

-- Comment: account_type drives access control for org-gated endpoints.
-- visible_to_orgs drives GET /api/profiles/public (opt-in only).
