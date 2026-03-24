-- S4-02: Add assessment assignment columns
-- Allows organizations to assign assessments to specific volunteers

-- Add new columns for assignment tracking
ALTER TABLE public.assessment_sessions
    ADD COLUMN IF NOT EXISTS assigned_by_org_id UUID REFERENCES public.organizations(id),
    ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS deadline TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS assignment_message TEXT,
    ADD COLUMN IF NOT EXISTS current_question_id UUID;

-- Update status CHECK to include 'assigned' status
-- Drop old constraint and add new one
ALTER TABLE public.assessment_sessions DROP CONSTRAINT IF EXISTS assessment_sessions_status_check;
ALTER TABLE public.assessment_sessions
    ADD CONSTRAINT assessment_sessions_status_check
    CHECK (status IN ('assigned', 'in_progress', 'completed', 'abandoned', 'flagged'));

-- Index for org-based queries (assigned assessments dashboard)
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_assigned_org
    ON public.assessment_sessions(assigned_by_org_id)
    WHERE assigned_by_org_id IS NOT NULL;

-- Index for deadline tracking
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_deadline
    ON public.assessment_sessions(deadline)
    WHERE deadline IS NOT NULL AND status = 'assigned';

-- RLS: Allow org admins to read sessions they assigned (via service role in practice,
-- but this policy enables future direct-access patterns)
CREATE POLICY "Org admins can view assigned sessions"
    ON public.assessment_sessions FOR SELECT
    USING (
        assigned_by_org_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );
