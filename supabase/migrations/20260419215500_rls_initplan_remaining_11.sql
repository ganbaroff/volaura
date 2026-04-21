-- =============================================================================
-- Migration: RLS initplan optimization — remaining 11 INSERT policies
-- Date: 2026-04-19
-- Companion to 20260419214600_rls_initplan_optimization.sql
-- =============================================================================

ALTER POLICY "Org owners can insert events"
  ON public.events
  WITH CHECK (
    organization_id IN (
      SELECT organizations.id FROM organizations
      WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can insert eventshift_areas"
  ON public.eventshift_areas
  WITH CHECK (
    org_id IN (
      SELECT organizations.id FROM organizations
      WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can insert eventshift_departments"
  ON public.eventshift_departments
  WITH CHECK (
    org_id IN (
      SELECT organizations.id FROM organizations
      WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can insert eventshift_events"
  ON public.eventshift_events
  WITH CHECK (
    org_id IN (
      SELECT organizations.id FROM organizations
      WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can insert eventshift_unit_assignments"
  ON public.eventshift_unit_assignments
  WITH CHECK (
    org_id IN (
      SELECT organizations.id FROM organizations
      WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can insert eventshift_unit_metrics"
  ON public.eventshift_unit_metrics
  WITH CHECK (
    org_id IN (
      SELECT organizations.id FROM organizations
      WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Org owner can insert eventshift_units"
  ON public.eventshift_units
  WITH CHECK (
    org_id IN (
      SELECT organizations.id FROM organizations
      WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "human_review_requests_owner_insert"
  ON public.human_review_requests
  WITH CHECK (user_id = (select auth.uid()));

ALTER POLICY "Org can insert own intro requests"
  ON public.intro_requests
  WITH CHECK ((select auth.uid()) = org_id);

ALTER POLICY "Org owner can insert own module_activations"
  ON public.module_activations
  WITH CHECK (
    org_id IN (
      SELECT organizations.id FROM organizations
      WHERE organizations.owner_id = (select auth.uid())
    )
  );

ALTER POLICY "Volunteers cannot forge behavior signals for others"
  ON public.volunteer_behavior_signals
  WITH CHECK ((select auth.uid()) = volunteer_id);
