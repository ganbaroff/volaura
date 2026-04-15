-- pgTAP: every critical public.* table has RLS ENABLED and FORCE RLS on.
-- Catches: (1) future migration forgets ENABLE, (2) FORCE regression (owner-bypass path),
-- (3) table recreated without carrying the RLS flags forward.
--
-- Research: docs/research/rls-testing/summary.md §"Attack-surface checklist" #1
-- + §"Specific test patterns we'd miss" (FORCE ROW LEVEL SECURITY absence).

BEGIN;

SELECT plan(14);

-- Helper-free: query pg_class directly. Two assertions per table (rls + force_rls).

SELECT is(
    (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.profiles'::regclass),
    true,
    'profiles.relrowsecurity = true'
);
SELECT is(
    (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.profiles'::regclass),
    true,
    'profiles.relforcerowsecurity = true (blocks owner bypass)'
);

SELECT is(
    (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.aura_scores'::regclass),
    true,
    'aura_scores.relrowsecurity = true'
);
SELECT is(
    (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.aura_scores'::regclass),
    true,
    'aura_scores.relforcerowsecurity = true'
);

SELECT is(
    (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.registrations'::regclass),
    true,
    'registrations.relrowsecurity = true'
);
SELECT is(
    (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.registrations'::regclass),
    true,
    'registrations.relforcerowsecurity = true'
);

SELECT is(
    (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.assessment_sessions'::regclass),
    true,
    'assessment_sessions.relrowsecurity = true'
);
SELECT is(
    (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.assessment_sessions'::regclass),
    true,
    'assessment_sessions.relforcerowsecurity = true'
);

SELECT is(
    (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.events'::regclass),
    true,
    'events.relrowsecurity = true'
);
SELECT is(
    (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.events'::regclass),
    true,
    'events.relforcerowsecurity = true'
);

SELECT is(
    (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.organizations'::regclass),
    true,
    'organizations.relrowsecurity = true'
);
SELECT is(
    (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.organizations'::regclass),
    true,
    'organizations.relforcerowsecurity = true'
);

-- Smoke check: no public table has RLS on but FORCE off (Splinter-style drift test).
SELECT is(
    (
        SELECT count(*)::int
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
          AND c.relrowsecurity = true
          AND c.relforcerowsecurity = false
    ),
    0,
    'zero public tables have RLS=on AND FORCE=off (owner-bypass hole)'
);

-- Smoke check: service_role retains bypass at role level (REST path unchanged).
SELECT is(
    (SELECT rolbypassrls FROM pg_roles WHERE rolname = 'service_role'),
    true,
    'service_role.rolbypassrls = true (FastAPI admin path continues to work)'
);

SELECT * FROM finish();
ROLLBACK;
