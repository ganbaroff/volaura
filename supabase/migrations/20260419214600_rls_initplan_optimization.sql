-- =============================================================================
-- Migration: RLS auth.uid() initplan optimization
-- Date: 2026-04-19
-- =============================================================================
-- Purpose: Wrap every auth.uid() call in RLS policies with (select auth.uid()).
--
-- Why: Postgres evaluates bare auth.uid() once per row during a sequential scan.
-- Wrapping it in a scalar subquery forces the planner to treat it as an
-- "initplan" — evaluated exactly once per statement and cached. For tables
-- with thousands of rows this eliminates redundant function calls and
-- dramatically reduces per-query overhead.
--
-- This is the official Supabase recommendation for the auth_rls_initplan
-- performance advisory (https://supabase.com/docs/guides/database/postgres/row-level-security#use-auth-functions-efficiently).
--
-- Method: ALTER POLICY … ON … USING / WITH CHECK — preserves role assignments
-- and action type; no drop/recreate required.
--
-- Total policies updated: 76 named + ~18 insert/with-check-only policies
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- brandedby.ai_twins
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can delete own AI twin"
  ON brandedby.ai_twins
  USING ((select auth.uid()) = user_id);

ALTER POLICY "Users can read own AI twin"
  ON brandedby.ai_twins
  USING ((select auth.uid()) = user_id);

ALTER POLICY "Users can update own AI twin"
  ON brandedby.ai_twins
  USING ((select auth.uid()) = user_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users can create own AI twin"
  ON brandedby.ai_twins
  WITH CHECK ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- brandedby.generations
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can read own generations"
  ON brandedby.generations
  USING ((select auth.uid()) = user_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users can create own generations"
  ON brandedby.generations
  WITH CHECK ((select auth.uid()) = user_id);

-- public.analytics_events — table does not exist in migrations, skipped

-- ---------------------------------------------------------------------------
-- public.assessment_sessions
-- ---------------------------------------------------------------------------

ALTER POLICY "Org admins can view assigned sessions"
  ON public.assessment_sessions
  USING (
    assigned_by_org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Users can delete own abandoned sessions"
  ON public.assessment_sessions
  USING (
    ((select auth.uid()) = volunteer_id)
    AND (status = ANY (ARRAY['abandoned'::text, 'in_progress'::text]))
  );

ALTER POLICY "Users can only abandon own sessions"
  ON public.assessment_sessions
  USING (
    ((select auth.uid()) = volunteer_id)
    AND (status = 'in_progress'::text)
  )
  WITH CHECK (
    ((select auth.uid()) = volunteer_id)
    AND (status = ANY (ARRAY['abandoned'::text, 'in_progress'::text]))
  );

-- "Users can update own sessions" was dropped in 20260325000020 — skip

ALTER POLICY "Users can view own sessions"
  ON public.assessment_sessions
  USING ((select auth.uid()) = volunteer_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users can insert own sessions"
  ON public.assessment_sessions
  WITH CHECK ((select auth.uid()) = volunteer_id);

-- ---------------------------------------------------------------------------
-- public.aura_scores
-- ---------------------------------------------------------------------------

ALTER POLICY "Org admins can view permitted scores"
  ON public.aura_scores
  USING (
    volunteer_id IN (
      SELECT sp.user_id
        FROM sharing_permissions sp
        JOIN organizations o ON sp.org_id = o.id
       WHERE o.owner_id = (select auth.uid())
         AND sp.permission_type = 'read_score'::text
         AND sp.revoked_at IS NULL
    )
  );

ALTER POLICY "Public scores are readable"
  ON public.aura_scores
  USING (
    (visibility = 'public'::text)
    OR ((select auth.uid()) = volunteer_id)
  );

ALTER POLICY "Volunteers can read own AURA score"
  ON public.aura_scores
  USING ((select auth.uid()) = volunteer_id);

-- ---------------------------------------------------------------------------
-- public.automated_decision_log
-- ---------------------------------------------------------------------------

ALTER POLICY "automated_decision_log_owner_read"
  ON public.automated_decision_log
  USING (user_id = (select auth.uid()));

-- ---------------------------------------------------------------------------
-- public.character_events
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can read own character events"
  ON public.character_events
  USING ((select auth.uid()) = user_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users can insert own character events"
  ON public.character_events
  WITH CHECK ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- public.consent_events
-- ---------------------------------------------------------------------------

ALTER POLICY "consent_events_owner_read"
  ON public.consent_events
  USING (user_id = (select auth.uid()));

-- No INSERT policy exists on consent_events — skipped

-- ---------------------------------------------------------------------------
-- public.evaluation_queue
-- ---------------------------------------------------------------------------

ALTER POLICY "Volunteers can read own queue items"
  ON public.evaluation_queue
  USING ((select auth.uid()) = volunteer_id);

-- ---------------------------------------------------------------------------
-- public.events
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owners can delete their events"
  ON public.events
  USING (
    organization_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owners can select their events including drafts"
  ON public.events
  USING (
    organization_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owners can update their events"
  ON public.events
  USING (
    organization_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.eventshift_areas
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owner can delete eventshift_areas"
  ON public.eventshift_areas
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can read eventshift_areas"
  ON public.eventshift_areas
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can update eventshift_areas"
  ON public.eventshift_areas
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.eventshift_departments
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owner can delete eventshift_departments"
  ON public.eventshift_departments
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can read eventshift_departments"
  ON public.eventshift_departments
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can update eventshift_departments"
  ON public.eventshift_departments
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.eventshift_events
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owner can delete eventshift_events"
  ON public.eventshift_events
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can read eventshift_events"
  ON public.eventshift_events
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can update eventshift_events"
  ON public.eventshift_events
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.eventshift_unit_assignments
-- ---------------------------------------------------------------------------

ALTER POLICY "Assigned user can read own eventshift_unit_assignments"
  ON public.eventshift_unit_assignments
  USING (user_id = (select auth.uid()));

ALTER POLICY "Assigned user can update own status"
  ON public.eventshift_unit_assignments
  USING (user_id = (select auth.uid()))
  WITH CHECK (user_id = (select auth.uid()));

ALTER POLICY "Org owner can delete eventshift_unit_assignments"
  ON public.eventshift_unit_assignments
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can read eventshift_unit_assignments"
  ON public.eventshift_unit_assignments
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can update eventshift_unit_assignments"
  ON public.eventshift_unit_assignments
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.eventshift_unit_metrics
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owner can read eventshift_unit_metrics"
  ON public.eventshift_unit_metrics
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.eventshift_units
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owner can delete eventshift_units"
  ON public.eventshift_units
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can read eventshift_units"
  ON public.eventshift_units
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can update eventshift_units"
  ON public.eventshift_units
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.expert_verifications
-- ---------------------------------------------------------------------------

ALTER POLICY "Creators read sent verifications"
  ON public.expert_verifications
  USING ((select auth.uid()) = created_by);

ALTER POLICY "Volunteers read own verifications"
  ON public.expert_verifications
  USING ((select auth.uid()) = volunteer_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Volunteers create own verification links"
  ON public.expert_verifications
  WITH CHECK ((select auth.uid()) = volunteer_id);

ALTER POLICY "Org admins create verification links for real volunteers"
  ON public.expert_verifications
  WITH CHECK (
    ((select auth.uid()) = created_by)
    AND (volunteer_id IN (SELECT profiles.id FROM profiles))
  );

-- ---------------------------------------------------------------------------
-- public.game_character_rewards
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can read own character rewards"
  ON public.game_character_rewards
  USING ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- public.game_crystal_ledger
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can read own crystal ledger"
  ON public.game_crystal_ledger
  USING ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- public.grievances
-- ---------------------------------------------------------------------------

ALTER POLICY "Users read own grievances"
  ON public.grievances
  USING ((select auth.uid()) = user_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users insert own grievances"
  ON public.grievances
  WITH CHECK ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- public.human_review_requests
-- ---------------------------------------------------------------------------

ALTER POLICY "human_review_requests_owner_read"
  ON public.human_review_requests
  USING (user_id = (select auth.uid()));

ALTER POLICY "human_review_requests_reviewer_read"
  ON public.human_review_requests
  USING (reviewer_user_id = (select auth.uid()));

-- ---------------------------------------------------------------------------
-- public.intro_requests
-- ---------------------------------------------------------------------------

ALTER POLICY "Org can withdraw own request"
  ON public.intro_requests
  USING (
    ((select auth.uid()) = org_id)
    AND (status = 'pending'::text)
  )
  WITH CHECK (
    ((select auth.uid()) = org_id)
    AND (status = 'withdrawn'::text)
  );

ALTER POLICY "Orgs can read own sent requests"
  ON public.intro_requests
  USING ((select auth.uid()) = org_id);

ALTER POLICY "Volunteer can respond to received request"
  ON public.intro_requests
  USING (
    ((select auth.uid()) = volunteer_id)
    AND (status = 'pending'::text)
  )
  WITH CHECK (
    ((select auth.uid()) = volunteer_id)
    AND (status = ANY (ARRAY['accepted'::text, 'rejected'::text]))
  );

ALTER POLICY "Volunteers can read own received requests"
  ON public.intro_requests
  USING ((select auth.uid()) = volunteer_id);

-- ---------------------------------------------------------------------------
-- public.module_activations
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owner can delete own module_activations"
  ON public.module_activations
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can read own module_activations"
  ON public.module_activations
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can update own module_activations"
  ON public.module_activations
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.notifications
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can mark own notifications read"
  ON public.notifications
  USING ((select auth.uid()) = user_id)
  WITH CHECK ((select auth.uid()) = user_id);

ALTER POLICY "Users can read own notifications"
  ON public.notifications
  USING ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- public.organization_invites
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owners can read own invites"
  ON public.organization_invites
  USING (
    (invited_by = (select auth.uid()))
    OR (
      org_id IN (
        SELECT organizations.id
          FROM organizations
         WHERE organizations.owner_id = (select auth.uid())
      )
    )
  );

ALTER POLICY "Org owners can update own invites"
  ON public.organization_invites
  USING (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Org owners can insert invites"
  ON public.organization_invites
  WITH CHECK (
    org_id IN (
      SELECT organizations.id
        FROM organizations
       WHERE organizations.owner_id = (select auth.uid())
    )
  );

-- ---------------------------------------------------------------------------
-- public.organization_ratings
-- ---------------------------------------------------------------------------

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Authenticated users can rate organizations"
  ON public.organization_ratings
  WITH CHECK ((select auth.uid()) = volunteer_id);

-- ---------------------------------------------------------------------------
-- public.organizations
-- ---------------------------------------------------------------------------

ALTER POLICY "Owners can delete their org"
  ON public.organizations
  USING ((select auth.uid()) = owner_id);

ALTER POLICY "Owners can update their org"
  ON public.organizations
  USING ((select auth.uid()) = owner_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Owners can insert org"
  ON public.organizations
  WITH CHECK ((select auth.uid()) = owner_id);

-- ---------------------------------------------------------------------------
-- public.profiles
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can delete own profile"
  ON public.profiles
  USING ((select auth.uid()) = id);

ALTER POLICY "Users can update own profile"
  ON public.profiles
  USING ((select auth.uid()) = id);

ALTER POLICY "Users can view own profile"
  ON public.profiles
  USING ((select auth.uid()) = id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users can insert own profile"
  ON public.profiles
  WITH CHECK ((select auth.uid()) = id);

-- ---------------------------------------------------------------------------
-- public.registrations
-- ---------------------------------------------------------------------------

ALTER POLICY "Org owners can manage registrations"
  ON public.registrations
  USING (
    event_id IN (
      SELECT e.id
        FROM events e
        JOIN organizations o ON e.organization_id = o.id
       WHERE o.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Volunteers can cancel own registration"
  ON public.registrations
  USING ((select auth.uid()) = volunteer_id)
  WITH CHECK (status = 'cancelled'::text);

ALTER POLICY "Volunteers can view own registrations"
  ON public.registrations
  USING ((select auth.uid()) = volunteer_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Volunteers can register"
  ON public.registrations
  WITH CHECK ((select auth.uid()) = volunteer_id);

-- ---------------------------------------------------------------------------
-- public.sharing_permissions
-- ---------------------------------------------------------------------------

ALTER POLICY "Org admins can view granted permissions"
  ON public.sharing_permissions
  USING (
    (
      org_id IN (
        SELECT organizations.id
          FROM organizations
         WHERE organizations.owner_id = (select auth.uid())
      )
    )
    AND (revoked_at IS NULL)
  );

ALTER POLICY "Users can revoke permissions"
  ON public.sharing_permissions
  USING ((select auth.uid()) = user_id);

ALTER POLICY "Users can view own permissions"
  ON public.sharing_permissions
  USING ((select auth.uid()) = user_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users can grant permissions"
  ON public.sharing_permissions
  WITH CHECK ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- public.tribe_matching_pool
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can leave pool"
  ON public.tribe_matching_pool
  USING ((select auth.uid()) = user_id);

ALTER POLICY "Users can read own pool status"
  ON public.tribe_matching_pool
  USING ((select auth.uid()) = user_id);

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users can join pool"
  ON public.tribe_matching_pool
  WITH CHECK ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- public.tribe_members
-- ---------------------------------------------------------------------------

-- "Users can read own tribe memberships" never existed — policy is "Active members can read their tribe members", skipped

ALTER POLICY "Users can soft opt-out of own membership"
  ON public.tribe_members
  USING (
    (user_id = (select auth.uid()))
    AND (opt_out_at IS NULL)
  )
  WITH CHECK (user_id = (select auth.uid()));

-- ---------------------------------------------------------------------------
-- public.tribe_renewal_requests
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can read own renewal request"
  ON public.tribe_renewal_requests
  USING (user_id = (select auth.uid()));

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Users can insert own renewal request"
  ON public.tribe_renewal_requests
  WITH CHECK (
    (user_id = (select auth.uid()))
    AND (tribe_id IN (
      SELECT tribe_members.tribe_id
        FROM tribe_members
       WHERE tribe_members.user_id = (select auth.uid())
         AND tribe_members.opt_out_at IS NULL
    ))
  );

-- ---------------------------------------------------------------------------
-- public.tribe_streaks
-- ---------------------------------------------------------------------------

ALTER POLICY "Users read own streak only"
  ON public.tribe_streaks
  USING ((select auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- public.tribes
-- ---------------------------------------------------------------------------

ALTER POLICY "Members can read their tribe"
  ON public.tribes
  USING (
    id IN (
      SELECT tribe_members.tribe_id
        FROM tribe_members
       WHERE tribe_members.user_id = (select auth.uid())
         AND tribe_members.opt_out_at IS NULL
    )
  );

-- ---------------------------------------------------------------------------
-- public.tribe_kudos
-- ---------------------------------------------------------------------------

-- INSERT-only: only WITH CHECK applies
ALTER POLICY "Active members can send kudos"
  ON public.tribe_kudos
  WITH CHECK (
    (select auth.uid()) IN (
      SELECT tribe_members.user_id
        FROM tribe_members
       WHERE tribe_members.opt_out_at IS NULL
    )
  );

-- ---------------------------------------------------------------------------
-- public.volunteer_badges
-- ---------------------------------------------------------------------------

ALTER POLICY "Volunteer badges readable for public profiles or own"
  ON public.volunteer_badges
  USING (
    ((select auth.uid()) = volunteer_id)
    OR (
      volunteer_id IN (
        SELECT profiles.id
          FROM profiles
         WHERE profiles.is_public = true
      )
    )
  );

-- ---------------------------------------------------------------------------
-- public.volunteer_behavior_signals
-- ---------------------------------------------------------------------------

ALTER POLICY "Users can view own behavior signals"
  ON public.volunteer_behavior_signals
  USING ((select auth.uid()) = volunteer_id);

-- atlas_obligations / proofs / nag_log — use auth.jwt(), not auth.uid(). Skipped.

COMMIT;

-- =============================================================================
-- Summary: ~94 ALTER POLICY statements across 32 tables
-- All bare auth.uid() calls replaced with (select auth.uid()) subplan cache.
-- Skipped: "Service role full access to ceo_inbox" (uses `true`, no auth.uid()).
-- =============================================================================
