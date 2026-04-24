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
-- Scope: all 35 public.* tables with rowsecurity=true as of 2026-04-15.
-- Wrapped in DO block: skips tables/views that don't exist yet (migration-order safe).

DO $$
DECLARE
    tbl TEXT;
    vw  TEXT;
    tables_to_force TEXT[] := ARRAY[
        'analytics_events',
        'assessment_sessions',
        'atlas_learnings',
        'aura_scores',
        'badges',
        'ceo_inbox',
        'character_events',
        'competencies',
        'evaluation_queue',
        'events',
        'expert_verifications',
        'game_character_rewards',
        'game_crystal_ledger',
        'grievances',
        'intro_requests',
        'notifications',
        'organization_invites',
        'organization_ratings',
        'organizations',
        'processed_stripe_events',
        'profiles',
        'questions',
        'registrations',
        'sharing_permissions',
        'tribe_kudos',
        'tribe_matching_pool',
        'tribe_member_history',
        'tribe_members',
        'tribe_renewal_requests',
        'tribe_streaks',
        'tribes',
        'user_identity_map',
        'volunteer_badges',
        'volunteer_behavior_signals',
        'volunteer_embeddings'
    ];
    -- View hardening: PG15+ requires security_invoker=true for underlying-table RLS to re-apply.
    -- Without it, views run as their owner (postgres) and silently bypass RLS on source tables.
    views_to_harden TEXT[] := ARRAY[
        'character_events_public_safe',
        'professional_badges',
        'professional_behavior_signals',
        'professional_embeddings'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables_to_force LOOP
        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = tbl AND c.relkind = 'r'
        ) THEN
            EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', tbl);
        END IF;
    END LOOP;

    FOREACH vw IN ARRAY views_to_harden LOOP
        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = vw AND c.relkind = 'v'
        ) THEN
            EXECUTE format('ALTER VIEW public.%I SET (security_invoker = true)', vw);
        END IF;
    END LOOP;
END $$;
