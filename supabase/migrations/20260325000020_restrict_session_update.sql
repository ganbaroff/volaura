-- BLOCKER-1: Remove user-level UPDATE on assessment_sessions.
-- Attacker vector: user could POST directly to PostgREST and set theta_estimate=4.0,
-- bypassing the entire IRT engine. Now only service_role (admin) can update sessions.
-- API code already uses db_admin for critical updates.

DROP POLICY IF EXISTS "Users can update own sessions" ON public.assessment_sessions;

-- Service role (used by API) has full access by default (bypasses RLS).
-- No explicit policy needed for service_role.

-- Add a restricted user-level update policy that ONLY allows status changes
-- (for the edge case of user-initiated abandonment via the UI)
CREATE POLICY "Users can only abandon own sessions"
ON public.assessment_sessions FOR UPDATE
USING (auth.uid() = volunteer_id)
WITH CHECK (
    auth.uid() = volunteer_id
    AND status IN ('abandoned')
);
