"""Org billing schemas (Pydantic v2) — B2B screening monetization.

Covers: org billing status read, checkout session creation (subscription +
one-time campaign unlock), and the 402 payment-required detail returned by the
gated report endpoint. Stripe IDs are server-side only — never returned to clients.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrgBillingStatus(BaseModel):
    """Billing posture for the caller's organization."""

    model_config = ConfigDict(from_attributes=True)

    has_active_subscription: bool
    subscription_expires_at: datetime | None = None
    unlocked_campaign_ids: list[str] = []
    org_billing_enabled: bool  # whether the report paywall is live at all
    # stripe_customer_id / stripe_subscription_id intentionally excluded.


class OrgCheckoutResponse(BaseModel):
    """Response for the subscription / campaign-unlock checkout endpoints."""

    checkout_url: str


class ReportPaywall(BaseModel):
    """402 detail body for a locked campaign report — tells the client how to pay."""

    code: str = "PAYMENT_REQUIRED"
    message: str
    campaign_id: str
    subscribe_url: str  # POST endpoint to start an org subscription checkout
    unlock_url: str  # POST endpoint to unlock this single campaign


class WebhookAck(BaseModel):
    """Org-billing webhook handler returns this on success."""

    received: bool = True
