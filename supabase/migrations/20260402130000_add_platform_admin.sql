-- Add platform admin flag to profiles
-- Used by: require_platform_admin dep in FastAPI, AdminGuard in Next.js
-- Set ONLY via service-role (Supabase dashboard) — never exposed to user-scoped APIs

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN public.profiles.is_platform_admin IS
  'Platform-level admin. Set via service-role only. Never self-promotable.';

-- RLS: normal users cannot read this column via user-scoped client.
-- All admin operations use service-role client which bypasses RLS entirely.
-- No separate policy needed — the column is protected by design (service-role gate).
