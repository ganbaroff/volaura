CREATE TABLE public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT CHECK (type IN ('company', 'ngo', 'government', 'individual')),
    logo_url TEXT,
    website TEXT,
    description TEXT,
    subscription_tier TEXT DEFAULT 'free'
        CHECK (subscription_tier IN ('free', 'starter', 'growth', 'enterprise')),
    subscription_expires_at TIMESTAMPTZ,
    stripe_customer_id TEXT,
    trust_score FLOAT,
    verified_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER organizations_updated_at
    BEFORE UPDATE ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE INDEX idx_organizations_owner ON public.organizations(owner_id);

-- Organization ratings (bilateral — volunteer rates org anonymously)
CREATE TABLE public.organization_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_id UUID,                     -- FK added after events table
    rating FLOAT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(volunteer_id, organization_id, event_id)
);

-- Trust Score visible ONLY after 5+ ratings
CREATE OR REPLACE VIEW public.organization_trust_scores AS
SELECT
    organization_id,
    COUNT(*) AS rating_count,
    CASE WHEN COUNT(*) >= 5
        THEN ROUND((AVG(rating) * 20)::numeric, 1)  -- 1-5 → 0-100
        ELSE NULL                          -- hidden until 5+ ratings
    END AS trust_score
FROM public.organization_ratings
GROUP BY organization_id;

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_ratings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Organizations are publicly viewable"
    ON public.organizations FOR SELECT
    USING (is_active = TRUE);

CREATE POLICY "Owners can update their org"
    ON public.organizations FOR UPDATE
    USING (auth.uid() = owner_id);

CREATE POLICY "Owners can insert org"
    ON public.organizations FOR INSERT
    WITH CHECK (auth.uid() = owner_id);

-- Ratings: insert only, no reading individual rows (anonymous by design)
CREATE POLICY "Authenticated users can rate organizations"
    ON public.organization_ratings FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = volunteer_id);
