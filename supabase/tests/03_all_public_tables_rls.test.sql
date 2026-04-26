-- pgTAP: catch-all — every public table must have RLS enabled.
-- Prevents regressions where a new migration creates a table without
-- ALTER TABLE ... ENABLE ROW LEVEL SECURITY.
--
-- Audit: findings-codex.md F-11 (6 tables hardcoded, 63-table schema)

BEGIN;

SELECT plan(2);

-- 1. No public table without RLS enabled
SELECT is(
    (
        SELECT count(*)::int
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
          AND c.relrowsecurity = false
    ),
    0,
    'all public tables have relrowsecurity = true'
);

-- 2. No public table with RLS on but FORCE off (owner-bypass hole)
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
    'all RLS-enabled public tables also have FORCE ROW LEVEL SECURITY'
);

SELECT * FROM finish();
ROLLBACK;
