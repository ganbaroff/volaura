-- Expert Verifications table
-- Stores one-use tokenized verification links sent by org admins or volunteers.
-- Token is a URL-safe random string (secrets.token_urlsafe(32)).
-- Rated via public /verify/{token} page — no auth required for verifier.

CREATE TABLE public.expert_verifications (
    id               UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    volunteer_id     UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_by       UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
    verifier_name    TEXT        NOT NULL,
    verifier_org     TEXT,
    competency_id    TEXT        NOT NULL,
    token            TEXT        NOT NULL UNIQUE,
    token_used       BOOLEAN     NOT NULL DEFAULT FALSE,
    token_expires_at TIMESTAMPTZ NOT NULL,
    rating           INTEGER     CHECK (rating BETWEEN 1 AND 5),
    comment          TEXT,
    verified_at      TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast token lookup (public verify page hits this on every load)
CREATE INDEX idx_expert_verifications_token
    ON public.expert_verifications (token);

-- Index for volunteer dashboard (show all verifications for a volunteer)
CREATE INDEX idx_expert_verifications_volunteer_id
    ON public.expert_verifications (volunteer_id, verified_at DESC);

-- ── RLS ──────────────────────────────────────────────────────────────
ALTER TABLE public.expert_verifications ENABLE ROW LEVEL SECURITY;

-- Volunteers can read their own verifications (for profile display)
CREATE POLICY "Volunteers read own verifications"
ON public.expert_verifications FOR SELECT
USING (auth.uid() = volunteer_id);

-- Creators (org admins) can read verifications they sent
CREATE POLICY "Creators read sent verifications"
ON public.expert_verifications FOR SELECT
USING (auth.uid() = created_by);

-- Volunteers can create verification links for themselves
CREATE POLICY "Volunteers create own verification links"
ON public.expert_verifications FOR INSERT
WITH CHECK (auth.uid() = volunteer_id);

-- Creators (org admins) can create links for any volunteer
-- NOTE: we rely on backend auth middleware to validate org membership
CREATE POLICY "Org admins create verification links"
ON public.expert_verifications FOR INSERT
WITH CHECK (auth.uid() = created_by);

-- Nobody can UPDATE or DELETE via PostgREST — only via service_role on the backend
-- (token_used and verified_at are set by the API using admin client)

-- ── Comments ─────────────────────────────────────────────────────────
COMMENT ON TABLE  public.expert_verifications IS 'One-use tokenized expert verification links with ratings';
COMMENT ON COLUMN public.expert_verifications.token IS 'URL-safe random token (secrets.token_urlsafe(32)), stored raw';
COMMENT ON COLUMN public.expert_verifications.token_used IS 'TRUE after verifier submits — token is single-use';
COMMENT ON COLUMN public.expert_verifications.token_expires_at IS 'Token valid for 7 days from creation';
COMMENT ON COLUMN public.expert_verifications.rating IS '1=Poor 2=Fair 3=Good 4=Great 5=Exceptional';
COMMENT ON COLUMN public.expert_verifications.competency_id IS 'One of the 8 AURA competency IDs';
