-- =============================================================================
-- Security Fixes P1 — Grant/Policy Hardening
-- Sprint E2 | 2026-03-30
-- =============================================================================
-- 1. BrandedBy schema: revoke CRUD from authenticated → service_role only
-- 2. Notifications INSERT policy: remove open WITH CHECK(TRUE) for authenticated
-- 3. CEO inbox: explicit deny documentation policy (RLS default-deny confirmed)
-- =============================================================================

-- ── Fix 1: BrandedBy — revoke authenticated CRUD ─────────────────────────────
-- Problem: Authenticated users have SELECT/INSERT/UPDATE/DELETE on ALL brandedby
-- tables directly via PostgREST. RLS protects against unauthorised row access
-- but GRANT is the first gate. Principle of least privilege: authenticated should
-- not have ANY direct access to brandedby schema — only service_role (backend).
-- Note: RLS policies on ai_twins + generations still apply for service_role.

REVOKE SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA brandedby FROM authenticated;

-- Remove default privilege grant for future tables in the schema
ALTER DEFAULT PRIVILEGES IN SCHEMA brandedby
    REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM authenticated;

-- service_role retains full access (unchanged)
COMMENT ON SCHEMA brandedby IS
    'BrandedBy schema. service_role only — authenticated has no direct access. '
    'All writes go through backend API (/api/brandedby/*). '
    'Hardened 2026-03-30: revoked authenticated CRUD from original CREATE SCHEMA migration.';

-- ── Fix 2: Notifications INSERT — remove open INSERT for authenticated ─────
-- Problem: "Service role can insert notifications" policy has no TO clause,
-- so it applies to ALL roles including authenticated. WITH CHECK (TRUE) means
-- any logged-in user can INSERT a notification for any user_id (inbox spam).
-- Fix: Drop the policy. service_role bypasses RLS, so it needs no INSERT policy.
-- authenticated users have no legitimate reason to INSERT notifications directly.

DROP POLICY IF EXISTS "Service role can insert notifications" ON public.notifications;

-- Service_role bypasses RLS by default (BYPASSRLS attribute) — no policy needed.
-- Authenticated users retain SELECT (own) + UPDATE (mark read) policies only.

COMMENT ON TABLE public.notifications IS
    'User notification inbox. RLS: users read/update own rows only. '
    'INSERT: service_role bypasses RLS (no policy needed). '
    'Authenticated users cannot INSERT directly — backend creates all notifications. '
    'Hardened 2026-03-30: removed open INSERT policy (was WITH CHECK TRUE = spam vector).';

-- ── Fix 3: CEO inbox — document explicit default-deny intent ─────────────────
-- CEO inbox has RLS enabled but ZERO policies. This is INTENTIONAL — PostgreSQL
-- default-deny means no non-bypassing role can access the table.
-- service_role (Telegram bot, autonomy system) bypasses RLS.
-- This comment policy makes the intent explicit and prevents future "accidental fix."

-- No policy changes needed. Add explicit documentation via a VIEW + comment.
-- (Adding a fake SELECT policy for anon would OPEN access, which is wrong.)

COMMENT ON TABLE public.ceo_inbox IS
    'CEO ↔ Agent Telegram channel. RLS: ZERO explicit policies = intentional default-deny. '
    'service_role (bot) bypasses RLS by design — no policy needed. '
    'NEVER add a permissive policy to this table without security review. '
    'This is the CEO private channel — zero public/authenticated access is correct. '
    'Documented 2026-03-30 after security audit finding "zero explicit policies."';
