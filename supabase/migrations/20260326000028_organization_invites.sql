-- Organization Invites table for CSV bulk invite feature (Sprint 9)
-- Tracks invitations sent by orgs to volunteers via email
-- Volunteers self-register later; invite tracks status

CREATE TABLE IF NOT EXISTS public.organization_invites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    invited_by UUID NOT NULL REFERENCES auth.users(id),
    email TEXT NOT NULL,
    display_name TEXT,
    phone TEXT,
    skills TEXT[] DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
    batch_id UUID,  -- groups rows from same CSV upload
    error_message TEXT,  -- if row failed validation
    accepted_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '14 days'),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prevent duplicate invites from same org to same email
CREATE UNIQUE INDEX idx_org_invites_org_email
    ON public.organization_invites(org_id, email)
    WHERE status != 'expired';

-- Fast lookup by batch
CREATE INDEX idx_org_invites_batch ON public.organization_invites(batch_id);

-- Fast lookup by email (for dedup check)
CREATE INDEX idx_org_invites_email ON public.organization_invites(email);

-- RLS
ALTER TABLE public.organization_invites ENABLE ROW LEVEL SECURITY;

-- Org owners can read their own invites
CREATE POLICY "Org owners can read own invites"
    ON public.organization_invites FOR SELECT
    USING (
        invited_by = auth.uid()
        OR org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

-- Org owners can insert invites for their org
CREATE POLICY "Org owners can insert invites"
    ON public.organization_invites FOR INSERT
    WITH CHECK (
        org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

-- Org owners can update their invites (status changes)
CREATE POLICY "Org owners can update own invites"
    ON public.organization_invites FOR UPDATE
    USING (
        org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );
