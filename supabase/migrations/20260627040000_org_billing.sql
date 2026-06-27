-- Org-side monetization for the B2B screening pivot.
-- Spec: for-ceo/briefs/2026-06-11-refounding-volaura.md §3 ("per-candidate 5-10 AZN
-- ИЛИ пакет 250-500 AZN/мес", goal: 3 paying orgs by day 90, paid surface = ranked report).
-- Decision: memory/decisions/2026-06-11-b2b-pivot.md (single 90-day metric: paying orgs).
--
-- Two paid paths, both unlock the same deliverable — the ranked candidate report
-- (apps/api/app/routers/campaigns.py GET /{campaign_id}/report):
--   1. One-time per-campaign unlock  → campaign_report_unlocks (Stripe Checkout mode=payment)
--   2. Recurring org subscription     → organizations.subscription_expires_at (mode=subscription)
--
-- Reuses the existing public.processed_stripe_events idempotency table (event_id is
-- globally unique per Stripe account, so B2C and B2B webhooks share it safely).
-- organizations already carries subscription_tier / subscription_expires_at / stripe_customer_id
-- (migration 20260321000008). This adds the subscription id for webhook bookkeeping parity.

-- ── organizations: store the active subscription id (mirror profiles.stripe_subscription_id) ──
ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT;

-- Partial index for webhook lookups by subscription id.
CREATE INDEX IF NOT EXISTS idx_organizations_stripe_customer_id
    ON public.organizations(stripe_customer_id)
    WHERE stripe_customer_id IS NOT NULL;

-- ── campaign_report_unlocks: one-time per-campaign report purchases ────────────
-- One row per campaign once paid. UNIQUE(campaign_id) makes webhook replay
-- idempotent (upsert on conflict). Created by the webhook on
-- checkout.session.completed — never written from the client.
CREATE TABLE IF NOT EXISTS public.campaign_report_unlocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL UNIQUE
        REFERENCES public.screening_campaigns(id) ON DELETE CASCADE,
    org_id UUID NOT NULL
        REFERENCES public.organizations(id) ON DELETE CASCADE,
    stripe_checkout_session_id TEXT UNIQUE,   -- Stripe Checkout Session id (cs_...)
    stripe_payment_intent_id TEXT,            -- Stripe PaymentIntent id (pi_...)
    amount_total INTEGER,                     -- minor units (qəpik / cents) as charged
    currency TEXT,                            -- ISO currency, e.g. 'azn' or 'usd'
    status TEXT NOT NULL DEFAULT 'paid'
        CHECK (status IN ('paid', 'refunded')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_campaign_report_unlocks_org
    ON public.campaign_report_unlocks(org_id);

-- ── RLS ───────────────────────────────────────────────────────────────────────
-- API talks through the service role (bypasses RLS). Policies cover direct
-- PostgREST access: org owners may READ their own unlocks (to render "unlocked"
-- state); writes are service-role-only (the webhook).
ALTER TABLE public.campaign_report_unlocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaign_report_unlocks FORCE ROW LEVEL SECURITY;

CREATE POLICY "Org owners read own report unlocks"
ON public.campaign_report_unlocks FOR SELECT
USING (EXISTS (
    SELECT 1 FROM public.organizations o
    WHERE o.id = org_id AND o.owner_id = auth.uid()
));

-- No INSERT/UPDATE/DELETE policies → only service_role can write (it bypasses RLS).

COMMENT ON TABLE public.campaign_report_unlocks IS
    'One-time per-campaign report unlocks (Stripe Checkout mode=payment). '
    'Written only by the org-billing webhook. UNIQUE(campaign_id) = idempotent replay.';
