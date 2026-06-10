-- B2B screening campaigns: org creates a vacancy, shares one link,
-- candidates join via link, take assigned assessments, org sees ranked report.
-- Decision: memory/decisions/2026-06-11-b2b-pivot.md

CREATE TABLE public.screening_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES public.profiles(id),
    title TEXT NOT NULL CHECK (char_length(title) BETWEEN 3 AND 120),
    description TEXT CHECK (char_length(description) <= 2000),
    competency_slugs TEXT[] NOT NULL CHECK (array_length(competency_slugs, 1) BETWEEN 1 AND 8),
    invite_token TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed', 'archived')),
    deadline_days INT NOT NULL DEFAULT 14 CHECK (deadline_days BETWEEN 1 AND 60),
    candidate_cap INT NOT NULL DEFAULT 500 CHECK (candidate_cap BETWEEN 1 AND 2000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_screening_campaigns_org ON public.screening_campaigns(org_id);

CREATE TABLE public.campaign_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES public.screening_campaigns(id) ON DELETE CASCADE,
    professional_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (campaign_id, professional_id)
);

CREATE INDEX idx_campaign_candidates_campaign ON public.campaign_candidates(campaign_id);

ALTER TABLE public.assessment_sessions
    ADD COLUMN campaign_id UUID REFERENCES public.screening_campaigns(id) ON DELETE SET NULL;

CREATE INDEX idx_assessment_sessions_campaign
    ON public.assessment_sessions(campaign_id) WHERE campaign_id IS NOT NULL;

-- RLS: API talks through service role; policies cover direct PostgREST access.
ALTER TABLE public.screening_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaign_candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Org owners read own campaigns"
ON public.screening_campaigns FOR SELECT
USING (EXISTS (
    SELECT 1 FROM public.organizations o
    WHERE o.id = org_id AND o.owner_id = auth.uid()
));

CREATE POLICY "Candidates read campaigns they joined"
ON public.screening_campaigns FOR SELECT
USING (EXISTS (
    SELECT 1 FROM public.campaign_candidates cc
    WHERE cc.campaign_id = id AND cc.professional_id = auth.uid()
));

CREATE POLICY "Org owners read own campaign candidates"
ON public.campaign_candidates FOR SELECT
USING (EXISTS (
    SELECT 1 FROM public.screening_campaigns sc
    JOIN public.organizations o ON o.id = sc.org_id
    WHERE sc.id = campaign_id AND o.owner_id = auth.uid()
));

CREATE POLICY "Candidates read own campaign membership"
ON public.campaign_candidates FOR SELECT
USING (professional_id = auth.uid());
