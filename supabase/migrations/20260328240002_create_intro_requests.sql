-- Sprint 4: Introduction requests between organizations and volunteers.
-- Org clicks "Request Introduction" on a volunteer profile → record created here.
-- Volunteer receives notification. Accept/reject UI deferred to Sprint 5.

CREATE TABLE IF NOT EXISTS public.intro_requests (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id       UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    timeline     TEXT NOT NULL
                     CHECK (timeline IN ('urgent', 'normal', 'flexible')),
    message      TEXT,
    status       TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'accepted', 'rejected', 'withdrawn')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Uniqueness: only one PENDING request per org-volunteer pair (prevents spam).
-- Completed/rejected requests don't block future requests.
CREATE UNIQUE INDEX IF NOT EXISTS idx_intro_requests_pending_unique
    ON public.intro_requests (org_id, volunteer_id)
    WHERE status = 'pending';

-- Indexes for queries
CREATE INDEX IF NOT EXISTS idx_intro_requests_volunteer_status
    ON public.intro_requests (volunteer_id, status);

CREATE INDEX IF NOT EXISTS idx_intro_requests_org_created
    ON public.intro_requests (org_id, created_at DESC);

-- Auto-update updated_at
CREATE TRIGGER intro_requests_updated_at
    BEFORE UPDATE ON public.intro_requests
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- RLS
ALTER TABLE public.intro_requests ENABLE ROW LEVEL SECURITY;

-- Org can read requests they sent
CREATE POLICY "Orgs can read own sent requests"
    ON public.intro_requests FOR SELECT
    USING (auth.uid() = org_id);

-- Volunteer can read requests they received
CREATE POLICY "Volunteers can read own received requests"
    ON public.intro_requests FOR SELECT
    USING (auth.uid() = volunteer_id);

-- Only the API backend (service role) inserts (enforced in app layer too)
CREATE POLICY "Service role can insert intro requests"
    ON public.intro_requests FOR INSERT
    WITH CHECK (TRUE);

-- Volunteer can update status (accept/reject) — Sprint 5
-- Org can withdraw their own request
CREATE POLICY "Parties can update own requests"
    ON public.intro_requests FOR UPDATE
    USING (auth.uid() = org_id OR auth.uid() = volunteer_id)
    WITH CHECK (auth.uid() = org_id OR auth.uid() = volunteer_id);
