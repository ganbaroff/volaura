-- BUG-003 + BUG-014 FIX: Harden intro_requests RLS policies.
--
-- BUG-003: INSERT policy was WITH CHECK (TRUE) — any client hitting PostgREST directly
--          could insert with any org_id, impersonating another org.
--          Fix: require auth.uid() = org_id on INSERT so only the actual org can create.
--          Note: application code uses SupabaseAdmin (service role) which bypasses RLS,
--          but this policy defends against direct PostgREST API abuse.
--
-- BUG-014: UPDATE policy allowed both parties to change ANY field (project_name, message,
--          status) with no transition guard. An org could self-accept their own request.
--          Fix: split into two separate policies:
--            - Org can only SET status='withdrawn' (withdraw their request)
--            - Volunteer can only SET status='accepted' OR 'rejected', only from 'pending'

-- Drop the overly broad existing policies
DROP POLICY IF EXISTS "Service role can insert intro requests" ON public.intro_requests;
DROP POLICY IF EXISTS "Parties can update own requests" ON public.intro_requests;

-- INSERT: require the inserting user to be the org themselves.
-- Service role bypasses this (used by the API), but direct PostgREST calls are blocked.
CREATE POLICY "Org can insert own intro requests"
    ON public.intro_requests FOR INSERT
    WITH CHECK (auth.uid() = org_id);

-- UPDATE for ORG: can only withdraw (set status='withdrawn') — cannot self-accept.
-- Cannot modify project_name, message, timeline, or volunteer_id.
CREATE POLICY "Org can withdraw own request"
    ON public.intro_requests FOR UPDATE
    USING (auth.uid() = org_id AND status = 'pending')
    WITH CHECK (auth.uid() = org_id AND status = 'withdrawn');

-- UPDATE for VOLUNTEER: can only accept or reject a PENDING request.
-- Cannot change org_id, volunteer_id, project_name, message, or timeline.
CREATE POLICY "Volunteer can respond to received request"
    ON public.intro_requests FOR UPDATE
    USING (auth.uid() = volunteer_id AND status = 'pending')
    WITH CHECK (auth.uid() = volunteer_id AND status IN ('accepted', 'rejected'));
