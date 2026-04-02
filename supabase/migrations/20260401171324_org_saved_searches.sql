-- Sprint 8: Org Saved Searches + Match Notifications
-- Organizations save talent search filters → get Telegram notifications when new matches appear.
-- Design: JSONB filters mirror VolunteerSearchRequest exactly (no drift risk — same schema).

CREATE TABLE public.org_saved_searches (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID         NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name        TEXT         NOT NULL CHECK (char_length(name) BETWEEN 1 AND 100),
    filters     JSONB        NOT NULL DEFAULT '{}',
    -- Filters schema mirrors VolunteerSearchRequest:
    --   query: TEXT, min_aura: FLOAT, badge_tier: TEXT | NULL,
    --   languages: TEXT[], location: TEXT | NULL
    notify_on_match  BOOLEAN      NOT NULL DEFAULT TRUE,
    last_checked_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Soft uniqueness: one org cannot have two searches with the same name
    UNIQUE (org_id, name)
);

CREATE INDEX idx_org_saved_searches_org   ON public.org_saved_searches(org_id);
CREATE INDEX idx_org_saved_searches_notify ON public.org_saved_searches(notify_on_match, last_checked_at)
    WHERE notify_on_match = TRUE;
-- Partial index — match checker only scans notification-enabled rows efficiently.

CREATE TRIGGER org_saved_searches_updated_at
    BEFORE UPDATE ON public.org_saved_searches
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE public.org_saved_searches ENABLE ROW LEVEL SECURITY;

-- Org owners can read their own saved searches only.
-- Join through organizations to verify ownership without exposing org_id tricks.
CREATE POLICY "Org owners can read own saved searches"
    ON public.org_saved_searches FOR SELECT
    USING (
        org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Org owners can insert saved searches"
    ON public.org_saved_searches FOR INSERT
    WITH CHECK (
        org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Org owners can update own saved searches"
    ON public.org_saved_searches FOR UPDATE
    USING (
        org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Org owners can delete own saved searches"
    ON public.org_saved_searches FOR DELETE
    USING (
        org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

-- ── Cap: max 20 saved searches per org (anti-spam) ───────────────────────────
-- Enforced at API layer (not DB constraint — error messages are better there).
-- The index above efficiently enforces listing.

COMMENT ON TABLE public.org_saved_searches IS
    'Saved talent search filters for organizations. One row = one named search with JSONB filter state. '
    'Notification-enabled rows are polled daily by match_checker.py.';

COMMENT ON COLUMN public.org_saved_searches.filters IS
    'JSONB mirrors VolunteerSearchRequest: {query, min_aura, badge_tier, languages, location}. '
    'Schema version tracked by _filters_version key. Breaking filter changes bump version.';

COMMENT ON COLUMN public.org_saved_searches.last_checked_at IS
    'Timestamp of last match check. match_checker.py only returns candidates newer than this. '
    'Updated to NOW() after every check, including runs that find zero new matches.';
