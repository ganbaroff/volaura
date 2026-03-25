-- Phase 1: Privacy-First Assessment Architecture
-- Adds: role_level to sessions, visibility to aura_scores, sharing_permissions table
-- Based on: PLAN-product-trust-architecture.md v2 (post 5-agent review)

-- 1. Add role_level to assessment_sessions
ALTER TABLE public.assessment_sessions
ADD COLUMN IF NOT EXISTS role_level TEXT DEFAULT 'volunteer'
CHECK (role_level IN ('volunteer', 'coordinator', 'specialist', 'manager', 'senior_manager'));

-- 2. Add visibility to aura_scores (PUBLIC by default — Leyla's feedback: visibility IS the value prop)
ALTER TABLE public.aura_scores
ADD COLUMN IF NOT EXISTS visibility TEXT DEFAULT 'public'
CHECK (visibility IN ('public', 'badge_only', 'hidden'));

-- 3. Create sharing_permissions table (Nigar's feedback: org<>volunteer consent model)
CREATE TABLE IF NOT EXISTS public.sharing_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    permission_type TEXT NOT NULL CHECK (permission_type IN ('read_score', 'read_full_eval', 'export_report')),
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, org_id, permission_type)
);

CREATE INDEX IF NOT EXISTS idx_sharing_permissions_user ON public.sharing_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_sharing_permissions_org ON public.sharing_permissions(org_id);

ALTER TABLE public.sharing_permissions ENABLE ROW LEVEL SECURITY;

-- Users can manage their own permissions
CREATE POLICY "Users can view own permissions"
    ON public.sharing_permissions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can grant permissions"
    ON public.sharing_permissions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can revoke permissions"
    ON public.sharing_permissions FOR UPDATE
    USING (auth.uid() = user_id);

-- Org admins can see permissions granted TO their org
CREATE POLICY "Org admins can view granted permissions"
    ON public.sharing_permissions FOR SELECT
    USING (
        org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
        AND revoked_at IS NULL
    );

-- 4. Add composite index for org aggregate queries (Scaling Engineer feedback)
CREATE INDEX IF NOT EXISTS idx_aura_scores_visibility ON public.aura_scores(visibility)
WHERE visibility = 'public';

-- 5. Add index for leaderboard performance
CREATE INDEX IF NOT EXISTS idx_aura_scores_public_leaderboard
ON public.aura_scores(total_score DESC)
WHERE visibility = 'public';

-- 6. Update existing RLS on aura_scores: respect visibility
DROP POLICY IF EXISTS "AURA scores are publicly readable" ON public.aura_scores;

-- Public can see public scores + own scores
CREATE POLICY "Public scores are readable"
    ON public.aura_scores FOR SELECT
    USING (
        visibility = 'public'
        OR auth.uid() = volunteer_id
    );

-- Org admins can see scores of users who granted permission
CREATE POLICY "Org admins can view permitted scores"
    ON public.aura_scores FOR SELECT
    USING (
        volunteer_id IN (
            SELECT sp.user_id FROM public.sharing_permissions sp
            JOIN public.organizations o ON sp.org_id = o.id
            WHERE o.owner_id = auth.uid()
            AND sp.permission_type = 'read_score'
            AND sp.revoked_at IS NULL
        )
    );
