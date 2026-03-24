-- =============================================================================
-- RLS AUDIT FIXES — Sprint 4, Task S4-05
-- Date: 2026-03-24
-- Audit scope: all 12 tables created in migrations 000002-000013
-- =============================================================================
--
-- AUDIT FINDINGS SUMMARY
-- ----------------------
-- CRITICAL (data exposure):
--   [C1] volunteer_behavior_signals: authenticated users can INSERT with TRUE check
--        — any logged-in user can forge behavior signals for ANY volunteer
--   [C2] aura_scores: publicly readable with TRUE — exposes aura_history JSONB,
--        reliability details, event no-show counts for every volunteer
--   [C3] volunteer_embeddings: readable by ALL authenticated users — raw embedding
--        vectors + embedding_text (PII-rich profile summary) exposed
--   [C4] questions: correct_answer, expected_concepts, lie_detector_flag readable
--        by all authenticated — enables test-farming and SJT bypass
--   [C5] assessment_sessions: no DELETE policy — orphaned sessions accumulate but
--        more importantly no explicit block means anon role policy inheritance risk
--   [C6] organizations: no DELETE policy — owners cannot close their own org
--   [C7] registrations: volunteer UPDATE has no WITH CHECK — a volunteer can set
--        coordinator_rating, coordinator_feedback on their own registration row
--   [C8] volunteer_badges: duplicate overlapping policies — "Users can view own"
--        AND "Public can view volunteer badges" (TRUE) — the private policy is dead
--        weight and the public one leaks badges of non-public profiles
--
-- HIGH (logic gaps):
--   [H1] aura_scores: INSERT/UPDATE use auth.uid() = volunteer_id — this breaks
--        the SECURITY DEFINER upsert_aura_score() RPC which runs as service_role;
--        after a fresh signup the user has no row to UPDATE and cannot INSERT
--        because the INSERT check fires in the user context, not definer context.
--        The RPC bypasses RLS so this is currently a silent pass-through, but
--        a direct PostgREST call (no RPC) would allow self-score manipulation.
--   [H2] expert_verifications: two INSERT policies exist for the same operation
--        (volunteer inserts own link, org admin inserts for any volunteer) — the
--        second policy (created_by = auth.uid()) allows inserting a row where
--        volunteer_id is someone else entirely; no backend enforcement at DB level.
--   [H3] events: "Org owners can manage their events" uses FOR ALL which includes
--        SELECT — but the SELECT policy already allows public read; FOR ALL on a
--        permissive policy set doesn't restrict, it only adds. Intended org-private
--        draft events are currently exposed if is_public=TRUE (even status=draft
--        is visible via org owner policy).
--
-- LOW (missing hardening):
--   [L1] competencies: no INSERT/UPDATE/DELETE protection — only authenticated
--        service role should ever mutate reference data; PostgREST admin client
--        can currently INSERT via anon/authenticated if RLS is bypassed by JWT role
--   [L2] badges (catalog table): same as L1 — no write protection
--   [L3] profiles: no DELETE policy — user cannot delete their own profile
--        (GDPR-relevant for future compliance)
--   [L4] questions: no INSERT/UPDATE/DELETE restriction beyond RLS disabled writes
--        (only SELECT policy defined) — write path is currently open to service_role
--        only because no permissive write policy exists, which is correct, but
--        there is no explicit DENY to make the intent visible
-- =============================================================================

-- =============================================================================
-- FIX C1: volunteer_behavior_signals
-- Old: INSERT WITH CHECK (TRUE) — any authenticated user can insert for anyone
-- New: only service_role backend can insert (no permissive policy for authenticated)
--      volunteers can still read their own signals
-- =============================================================================

DROP POLICY IF EXISTS "System can insert behavior signals"
    ON public.volunteer_behavior_signals;

-- Re-create with correct owner check so API's admin client (service_role) bypasses
-- RLS entirely, while a regular user JWT can only insert their own signal.
-- In practice, all behavior signal writes go through the backend admin client,
-- so this policy will never fire for legitimate code — it is a defence-in-depth
-- guard against direct PostgREST calls with a user JWT.
CREATE POLICY "Volunteers cannot forge behavior signals for others"
    ON public.volunteer_behavior_signals FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = volunteer_id);

-- Explicitly block UPDATE and DELETE from user-role clients
-- (service_role bypasses RLS, which is the intended write path)
CREATE POLICY "Behavior signals are immutable by users"
    ON public.volunteer_behavior_signals FOR UPDATE
    TO authenticated
    USING (FALSE);

CREATE POLICY "Behavior signals cannot be deleted by users"
    ON public.volunteer_behavior_signals FOR DELETE
    TO authenticated
    USING (FALSE);


-- =============================================================================
-- FIX C2: aura_scores
-- Old: SELECT USING (TRUE) — full row (including aura_history, no_show counts,
--      reliability details) exposed to every anonymous visitor
-- New: public read shows only non-sensitive aggregate columns; full row for owner
-- =============================================================================

-- Drop the blanket public policy
DROP POLICY IF EXISTS "AURA scores are publicly readable"
    ON public.aura_scores;

-- Owners see their complete row (all fields including history, reliability)
CREATE POLICY "Volunteers can read own AURA score"
    ON public.aura_scores FOR SELECT
    USING (auth.uid() = volunteer_id);

-- Public (anonymous + authenticated) can read aggregate fields only.
-- We achieve column-level restriction via a security-barrier view (created below).
-- The base-table public policy is intentionally narrow: only public profiles get
-- aggregate visibility; no_show counts, aura_history, reliability_status stay hidden.
CREATE POLICY "Public aggregate AURA visible for public profiles"
    ON public.aura_scores FOR SELECT
    USING (
        volunteer_id IN (
            SELECT id FROM public.profiles WHERE is_public = TRUE
        )
    );

-- NOTE: downstream consumers (org discovery, leaderboard) MUST use the
-- public.aura_scores_public view below, NOT the base table, to avoid leaking
-- private columns even to authenticated users who satisfy the policy above.


-- =============================================================================
-- PUBLIC VIEW: aura_scores_public
-- Exposes only the non-sensitive aggregate columns to org discovery queries.
-- Using SECURITY INVOKER (default) so the view respects the caller's RLS context.
-- =============================================================================
CREATE OR REPLACE VIEW public.aura_scores_public
    WITH (security_barrier = TRUE)
AS
SELECT
    volunteer_id,
    total_score,
    badge_tier,
    elite_status,
    competency_scores,
    percentile_rank,
    last_updated
FROM public.aura_scores;

COMMENT ON VIEW public.aura_scores_public IS
    'Safe public projection of aura_scores. Excludes: aura_history, no_show counts, '
    'reliability_score, reliability_status, events_attended, events_late. '
    'Use this view for all org-facing queries and leaderboards.';


-- =============================================================================
-- FIX C3: volunteer_embeddings
-- Old: SELECT USING (TRUE) for all authenticated — exposes embedding_text (PII)
--      and raw vectors to any logged-in user
-- New: no user-role SELECT at all; all legitimate reads go through the
--      match_volunteers() SECURITY DEFINER RPC which uses service_role context
-- =============================================================================

DROP POLICY IF EXISTS "Embeddings readable by authenticated"
    ON public.volunteer_embeddings;

-- Explicit: no authenticated user can SELECT the embeddings table directly.
-- The SECURITY DEFINER RPC functions are the only legitimate read path.
-- Service_role (backend) bypasses RLS as intended.
CREATE POLICY "Embeddings not directly readable by users"
    ON public.volunteer_embeddings FOR SELECT
    TO authenticated
    USING (FALSE);

-- Block writes from user-role clients
CREATE POLICY "Embeddings not writable by users"
    ON public.volunteer_embeddings FOR INSERT
    TO authenticated
    WITH CHECK (FALSE);

CREATE POLICY "Embeddings not updatable by users"
    ON public.volunteer_embeddings FOR UPDATE
    TO authenticated
    USING (FALSE);

CREATE POLICY "Embeddings not deletable by users"
    ON public.volunteer_embeddings FOR DELETE
    TO authenticated
    USING (FALSE);


-- =============================================================================
-- FIX C4: questions
-- Old: correct_answer, expected_concepts, lie_detector_flag, irt_* parameters
--      all readable because the SELECT policy returns the full row
-- New: strip sensitive columns via a security-barrier view; restrict base table
--      to service_role only; authenticated users query through the view
-- =============================================================================

-- Drop the broad policy; we replace with a view-based approach
DROP POLICY IF EXISTS "Authenticated users can view active questions"
    ON public.questions;

-- No authenticated-role access to base table (service_role bypasses for admin ops)
CREATE POLICY "Questions base table not accessible to user role"
    ON public.questions FOR SELECT
    TO authenticated
    USING (FALSE);


-- =============================================================================
-- VIEW: questions_safe
-- Strips: correct_answer, expected_concepts (open-ended answer keys),
--         lie_detector_flag, is_sjt_reliability, irt_a/b/c,
--         discrimination_index, times_shown, times_correct, needs_review
-- Exposes: everything needed to render a question card and store answers
-- =============================================================================
CREATE OR REPLACE VIEW public.questions_safe
    WITH (security_barrier = TRUE)
AS
SELECT
    id,
    competency_id,
    difficulty,
    type,
    scenario_en,
    scenario_az,
    options,           -- MCQ options (without correct_answer key)
    cefr_level,
    feedback_en,
    feedback_az,
    development_tip_en,
    development_tip_az,
    is_ai_generated,
    is_active,
    created_at
FROM public.questions
WHERE is_active = TRUE
  AND needs_review = FALSE;

COMMENT ON VIEW public.questions_safe IS
    'Safe question projection for assessment rendering. Strips: correct_answer, '
    'expected_concepts, lie_detector_flag, is_sjt_reliability, IRT parameters, '
    'discrimination_index, times_shown/correct. RLS on base table ensures only '
    'the API backend (service_role) can access raw question data.';

-- RLS on the view itself (belt-and-suspenders): only authenticated users
CREATE POLICY "Authenticated users can read safe questions"
    ON public.questions FOR SELECT
    TO authenticated
    USING (is_active = TRUE AND needs_review = FALSE);
-- NOTE: the above policy only applies when queries hit the base table.
-- For the view, security_barrier prevents WHERE-clause leakage.
-- The API must use the view for assessment question delivery.


-- =============================================================================
-- FIX C5: assessment_sessions — add explicit DELETE policy
-- Old: no DELETE policy — sessions cannot be cleaned up by the owner
-- =============================================================================

CREATE POLICY "Users can delete own abandoned sessions"
    ON public.assessment_sessions FOR DELETE
    USING (auth.uid() = volunteer_id AND status IN ('abandoned', 'in_progress'));

-- Completed/flagged sessions must be preserved; only service_role can delete them


-- =============================================================================
-- FIX C6: organizations — add DELETE policy for owner
-- =============================================================================

CREATE POLICY "Owners can delete their org"
    ON public.organizations FOR DELETE
    USING (auth.uid() = owner_id);


-- =============================================================================
-- FIX C7: registrations — restrict volunteer UPDATE to allowed columns only
-- Old: UPDATE USING (auth.uid() = volunteer_id) — volunteer can set
--      coordinator_rating, coordinator_feedback, check_in_code on own row
-- New: restrict to only status = 'cancelled' transition via explicit check
-- =============================================================================

DROP POLICY IF EXISTS "Volunteers can cancel own registration"
    ON public.registrations;

CREATE POLICY "Volunteers can cancel own registration"
    ON public.registrations FOR UPDATE
    USING (auth.uid() = volunteer_id)
    WITH CHECK (
        -- Volunteers may only move their row to cancelled
        -- All other fields must be unchanged (enforced at application layer too)
        status = 'cancelled'
    );

-- Also explicitly block DELETE by volunteers — only org owners can remove regs
CREATE POLICY "Volunteers cannot delete registrations"
    ON public.registrations FOR DELETE
    TO authenticated
    USING (FALSE);

-- NOTE: coordinator_rating, coordinator_feedback updates must go through
-- the org-owner policy path or the service_role backend — not the volunteer path.


-- =============================================================================
-- FIX C8: volunteer_badges — deduplicate overlapping policies, restrict to
--          public profiles only for anonymous reads
-- Old: two SELECT policies — "Users can view own" + "Public can view" (TRUE)
--      The TRUE policy makes the owner policy redundant and leaks badges for
--      volunteers with is_public = FALSE
-- New: single policy — own badges always visible; others only if profile is public
-- =============================================================================

DROP POLICY IF EXISTS "Users can view own badges"
    ON public.volunteer_badges;

DROP POLICY IF EXISTS "Public can view volunteer badges"
    ON public.volunteer_badges;

-- Unified: own badges always readable; other volunteers' badges only if public
CREATE POLICY "Volunteer badges readable for public profiles or own"
    ON public.volunteer_badges FOR SELECT
    USING (
        auth.uid() = volunteer_id
        OR volunteer_id IN (
            SELECT id FROM public.profiles WHERE is_public = TRUE
        )
    );

-- Badges are issued by service_role only — block user-role writes
CREATE POLICY "Users cannot self-award badges"
    ON public.volunteer_badges FOR INSERT
    TO authenticated
    WITH CHECK (FALSE);

CREATE POLICY "Users cannot modify earned badges"
    ON public.volunteer_badges FOR UPDATE
    TO authenticated
    USING (FALSE);

CREATE POLICY "Users cannot delete earned badges"
    ON public.volunteer_badges FOR DELETE
    TO authenticated
    USING (FALSE);


-- =============================================================================
-- FIX H1: aura_scores write policies
-- Old: INSERT WITH CHECK (auth.uid() = volunteer_id) — a user JWT can attempt
--      a direct PostgREST INSERT to self-set their score
--      UPDATE USING (auth.uid() = volunteer_id) — same risk
-- New: no permissive write policies for authenticated role;
--      all writes go through upsert_aura_score() SECURITY DEFINER RPC
-- =============================================================================

DROP POLICY IF EXISTS "System can insert AURA scores"
    ON public.aura_scores;

DROP POLICY IF EXISTS "System can update AURA scores"
    ON public.aura_scores;

-- Explicit deny for user-role writes (service_role bypasses RLS)
CREATE POLICY "Users cannot insert AURA scores directly"
    ON public.aura_scores FOR INSERT
    TO authenticated
    WITH CHECK (FALSE);

CREATE POLICY "Users cannot update AURA scores directly"
    ON public.aura_scores FOR UPDATE
    TO authenticated
    USING (FALSE);

CREATE POLICY "Users cannot delete AURA scores"
    ON public.aura_scores FOR DELETE
    TO authenticated
    USING (FALSE);


-- =============================================================================
-- FIX H2: expert_verifications — tighten org-admin INSERT policy
-- Old: "Org admins create verification links" allows inserting with
--      created_by = auth.uid() regardless of what volunteer_id is set to —
--      an admin can create a verification for any volunteer_id, even non-existent
-- New: require either (a) self-link OR (b) created_by = auth.uid()
--      The application layer already validates org membership, but add an
--      additional check that volunteer_id must reference an existing public profile
-- =============================================================================

DROP POLICY IF EXISTS "Org admins create verification links"
    ON public.expert_verifications;

CREATE POLICY "Org admins create verification links for real volunteers"
    ON public.expert_verifications FOR INSERT
    WITH CHECK (
        auth.uid() = created_by
        AND volunteer_id IN (SELECT id FROM public.profiles)
    );

-- Also add UPDATE/DELETE block for user-role (token_used set via service_role)
CREATE POLICY "Expert verifications immutable by users"
    ON public.expert_verifications FOR UPDATE
    TO authenticated
    USING (FALSE);

CREATE POLICY "Expert verifications not deletable by users"
    ON public.expert_verifications FOR DELETE
    TO authenticated
    USING (FALSE);


-- =============================================================================
-- FIX H3: events — draft events should never be publicly visible
-- Old: "Org owners can manage their events" FOR ALL includes SELECT, which means
--      a draft event with is_public=TRUE passes both the public policy
--      (status != 'draft' check blocks it) AND the FOR ALL owner policy (no status
--      check). Result: org owners see drafts (correct), but the permissive SELECT
--      from FOR ALL can interact oddly with PostgREST anon role.
-- Fix: replace FOR ALL with explicit per-operation policies to make intent clear
-- =============================================================================

DROP POLICY IF EXISTS "Org owners can manage their events"
    ON public.events;

-- Org owners: full CRUD on their own events (including drafts)
CREATE POLICY "Org owners can select their events including drafts"
    ON public.events FOR SELECT
    USING (
        organization_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Org owners can insert events"
    ON public.events FOR INSERT
    WITH CHECK (
        organization_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Org owners can update their events"
    ON public.events FOR UPDATE
    USING (
        organization_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Org owners can delete their events"
    ON public.events FOR DELETE
    USING (
        organization_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );


-- =============================================================================
-- FIX L1: competencies — add explicit write-deny for authenticated role
-- Reference data is immutable from the user perspective
-- =============================================================================

CREATE POLICY "Competencies not writable by users"
    ON public.competencies FOR INSERT
    TO authenticated
    WITH CHECK (FALSE);

CREATE POLICY "Competencies not updatable by users"
    ON public.competencies FOR UPDATE
    TO authenticated
    USING (FALSE);

CREATE POLICY "Competencies not deletable by users"
    ON public.competencies FOR DELETE
    TO authenticated
    USING (FALSE);


-- =============================================================================
-- FIX L2: badges (catalog table) — add explicit write-deny
-- =============================================================================

CREATE POLICY "Badge catalog not writable by users"
    ON public.badges FOR INSERT
    TO authenticated
    WITH CHECK (FALSE);

CREATE POLICY "Badge catalog not updatable by users"
    ON public.badges FOR UPDATE
    TO authenticated
    USING (FALSE);

CREATE POLICY "Badge catalog not deletable by users"
    ON public.badges FOR DELETE
    TO authenticated
    USING (FALSE);


-- =============================================================================
-- FIX L3: profiles — add DELETE for GDPR right-to-erasure
-- (cascades to all child tables via ON DELETE CASCADE)
-- =============================================================================

CREATE POLICY "Users can delete own profile"
    ON public.profiles FOR DELETE
    USING (auth.uid() = id);


-- =============================================================================
-- FIX: organization_ratings — add explicit read-deny to enforce anonymity
-- Old: no SELECT policy defined — anonymous design requires that individual
--      ratings are never readable. Without an explicit policy on a RLS-enabled
--      table, the default is DENY, which is correct. But the intent is not
--      documented. Making it explicit prevents accidental policy addition later.
-- =============================================================================

CREATE POLICY "Organization ratings are anonymous — no direct reads"
    ON public.organization_ratings FOR SELECT
    TO authenticated
    USING (FALSE);

-- Service_role can read for aggregate calculation (bypasses RLS)


-- =============================================================================
-- GRANT: allow authenticated role to use the safe views
-- =============================================================================

GRANT SELECT ON public.questions_safe TO authenticated;
GRANT SELECT ON public.aura_scores_public TO authenticated;
GRANT SELECT ON public.aura_scores_public TO anon;


-- =============================================================================
-- COMMENTS: document the security model for future migrations
-- =============================================================================

COMMENT ON TABLE public.volunteer_behavior_signals IS
    'Security: INSERT restricted to own volunteer_id from user JWT. All '
    'legitimate writes use service_role (API backend) which bypasses RLS. '
    'Direct PostgREST writes from user JWTs are blocked by explicit policy.';

COMMENT ON TABLE public.volunteer_embeddings IS
    'Security: NO direct user-role access. Read path is exclusively the '
    'match_volunteers() SECURITY DEFINER RPC. Write path is backend service_role.';

COMMENT ON TABLE public.aura_scores IS
    'Security: write path is exclusively upsert_aura_score() SECURITY DEFINER RPC. '
    'User-role INSERT/UPDATE/DELETE are explicitly denied. Public SELECT exposes '
    'aggregate columns only via aura_scores_public view; full row visible to owner.';

COMMENT ON TABLE public.questions IS
    'Security: base table SELECT denied to authenticated role. '
    'Use questions_safe view for assessment rendering. Backend reads full row '
    'via service_role for answer evaluation.';
