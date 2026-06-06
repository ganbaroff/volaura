-- Security audit 2026-05-07 P0 fix: profiles table over-shared via RLS.
--
-- Existing "Public profiles are viewable by everyone" policy granted anon
-- SELECT on ALL 36 columns of any row where is_public=TRUE. Confirmed by
-- security-auditor agent: anon could pull stripe_customer_id,
-- stripe_subscription_id, subscription_status, trial_ends_at,
-- is_platform_admin, phone, telegram_chat_id, terms_version, etc. via one
-- curl with the publishable key Vercel ships in every page bundle. 27 rows
-- enumerable today, scales to founding-100 with billing intent.
--
-- Fix
-- ---
-- 1. Drop the all-columns public-read policy on public.profiles
-- 2. Create public.profiles_public view exposing only safe columns
-- 3. GRANT SELECT on the view to anon and authenticated
--
-- Per-user own-profile reads (auth.uid() = id) remain via the existing
-- "Users can view own profile" policy — frontend hooks (use-energy-mode,
-- assessment complete page) continue to work through that path.
--
-- Backend reads via service-role and bypasses RLS — no backend impact.
--
-- Future discovery routes (org search, public profile view) must read
-- public.profiles_public, not public.profiles.

DROP POLICY IF EXISTS "Public profiles are viewable by everyone" ON public.profiles;

CREATE OR REPLACE VIEW public.profiles_public
WITH (security_invoker = ON) AS
SELECT
    id,
    username,
    display_name,
    avatar_url,
    bio,
    location,
    languages,
    social_links,
    badge_issued_at,
    badge_open_badges_url,
    is_public,
    created_at,
    account_type,
    org_type
FROM public.profiles
WHERE is_public = TRUE;

GRANT SELECT ON public.profiles_public TO anon, authenticated;

COMMENT ON VIEW public.profiles_public IS
'Column-restricted projection of profiles for unauthenticated discovery.
Hides phone, telegram_chat_id, stripe_customer_id, stripe_subscription_id,
subscription_status, trial_*, is_platform_admin, age_confirmed, terms_*,
energy_level, registration_tier, registration_number, utm_*, referral_code,
ghosting_grace_sent_at, visible_to_orgs.
Authenticated users querying their own row use public.profiles directly via
auth.uid()=id RLS policy. Created 2026-05-07 in response to security audit P0.';
