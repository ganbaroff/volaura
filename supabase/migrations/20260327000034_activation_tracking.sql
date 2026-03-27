-- Migration 000034: activation_tracking
-- Captures referral codes and UTM params at registration for activation wave analytics

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS referral_code TEXT,
ADD COLUMN IF NOT EXISTS utm_source TEXT,
ADD COLUMN IF NOT EXISTS utm_campaign TEXT;

-- Fast aggregation index
CREATE INDEX IF NOT EXISTS idx_profiles_referral_code
ON public.profiles(referral_code)
WHERE referral_code IS NOT NULL;

-- CEO activation stats view (no RLS — service role queries only via Supabase dashboard)
CREATE OR REPLACE VIEW public.referral_stats AS
SELECT
    referral_code,
    utm_source,
    utm_campaign,
    COUNT(*) AS registrations,
    COUNT(*) FILTER (WHERE badge_issued_at IS NOT NULL) AS badges_earned,
    ROUND(
        COUNT(*) FILTER (WHERE badge_issued_at IS NOT NULL)::NUMERIC
        / NULLIF(COUNT(*), 0) * 100, 1
    ) AS conversion_pct,
    MIN(created_at) AS first_registration,
    MAX(created_at) AS last_registration
FROM public.profiles
WHERE referral_code IS NOT NULL
GROUP BY referral_code, utm_source, utm_campaign
ORDER BY registrations DESC;
