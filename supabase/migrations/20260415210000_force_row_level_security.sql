-- FORCE ROW LEVEL SECURITY on every public.* table with RLS enabled.
-- Research: docs/research/rls-testing/summary.md §"Two follow-ups" (#1) + §"Attack-surface checklist" #1.
--
-- Why: without FORCE, table owner (postgres role, rolbypassrls=true) bypasses all RLS.
-- If an admin endpoint ever leaks SQL injection, or a migration connects as owner,
-- every row becomes readable regardless of policy. FORCE removes that owner-bypass path.
--
-- Safety: service_role retains BYPASSRLS at role level (pg_roles.rolbypassrls=true),
-- so Supabase REST / FastAPI admin client continues to work unchanged. FORCE only
-- affects the table-owner bypass, not the role-level BYPASSRLS attribute.
--
-- Verified: pg_roles shows service_role.rolbypassrls=true on this project — no
-- service_role pass-through policies needed.
--
-- Scope: all 35 public.* tables with rowsecurity=true as of 2026-04-15.

ALTER TABLE public.analytics_events             FORCE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_sessions          FORCE ROW LEVEL SECURITY;
ALTER TABLE public.atlas_learnings              FORCE ROW LEVEL SECURITY;
ALTER TABLE public.aura_scores                  FORCE ROW LEVEL SECURITY;
ALTER TABLE public.badges                       FORCE ROW LEVEL SECURITY;
ALTER TABLE public.ceo_inbox                    FORCE ROW LEVEL SECURITY;
ALTER TABLE public.character_events             FORCE ROW LEVEL SECURITY;
ALTER TABLE public.competencies                 FORCE ROW LEVEL SECURITY;
ALTER TABLE public.evaluation_queue             FORCE ROW LEVEL SECURITY;
ALTER TABLE public.events                       FORCE ROW LEVEL SECURITY;
ALTER TABLE public.expert_verifications         FORCE ROW LEVEL SECURITY;
ALTER TABLE public.game_character_rewards       FORCE ROW LEVEL SECURITY;
ALTER TABLE public.game_crystal_ledger          FORCE ROW LEVEL SECURITY;
ALTER TABLE public.grievances                   FORCE ROW LEVEL SECURITY;
ALTER TABLE public.intro_requests               FORCE ROW LEVEL SECURITY;
ALTER TABLE public.notifications                FORCE ROW LEVEL SECURITY;
ALTER TABLE public.organization_invites         FORCE ROW LEVEL SECURITY;
ALTER TABLE public.organization_ratings         FORCE ROW LEVEL SECURITY;
ALTER TABLE public.organizations                FORCE ROW LEVEL SECURITY;
ALTER TABLE public.processed_stripe_events      FORCE ROW LEVEL SECURITY;
ALTER TABLE public.profiles                     FORCE ROW LEVEL SECURITY;
ALTER TABLE public.questions                    FORCE ROW LEVEL SECURITY;
ALTER TABLE public.registrations                FORCE ROW LEVEL SECURITY;
ALTER TABLE public.sharing_permissions          FORCE ROW LEVEL SECURITY;
ALTER TABLE public.tribe_kudos                  FORCE ROW LEVEL SECURITY;
ALTER TABLE public.tribe_matching_pool          FORCE ROW LEVEL SECURITY;
ALTER TABLE public.tribe_member_history         FORCE ROW LEVEL SECURITY;
ALTER TABLE public.tribe_members                FORCE ROW LEVEL SECURITY;
ALTER TABLE public.tribe_renewal_requests       FORCE ROW LEVEL SECURITY;
ALTER TABLE public.tribe_streaks                FORCE ROW LEVEL SECURITY;
ALTER TABLE public.tribes                       FORCE ROW LEVEL SECURITY;
ALTER TABLE public.user_identity_map            FORCE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_badges             FORCE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_behavior_signals   FORCE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_embeddings         FORCE ROW LEVEL SECURITY;

-- View hardening: PG15+ requires security_invoker=true for underlying-table RLS to re-apply.
-- Without it, views run as their owner (postgres) and silently bypass RLS on source tables.
-- Research §"Two follow-ups" (#2) + §"Specific test patterns we'd miss" (View bypass on PG15+).
--
-- Already set (verified 2026-04-15): aura_scores_public, organization_trust_scores,
-- questions_safe, referral_stats. Fixing the four remaining views here.

ALTER VIEW public.character_events_public_safe   SET (security_invoker = true);
ALTER VIEW public.professional_badges            SET (security_invoker = true);
ALTER VIEW public.professional_behavior_signals  SET (security_invoker = true);
ALTER VIEW public.professional_embeddings        SET (security_invoker = true);
