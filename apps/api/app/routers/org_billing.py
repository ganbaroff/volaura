"""Org billing router — B2B screening monetization (refounding pivot 2026-06-11).

The paid surface is the ranked candidate report. An org pays via EITHER path:

  POST /api/org-billing/subscribe                         — recurring "package" (mode=subscription)
  POST /api/org-billing/campaigns/{campaign_id}/unlock    — one-time per-campaign (mode=payment)
  GET  /api/org-billing/status                            — billing posture for caller's org
  POST /api/org-billing/webhook                           — Stripe webhook (separate secret)

Mirrors app/routers/subscription.py (B2C) for: Stripe client gating, webhook
signature verification, processed_stripe_events idempotency, and the
5xx-retry-on-race pattern (return 500 so Stripe retries when the org row isn't
ready yet). Kept as a SEPARATE router + SEPARATE webhook secret so the B2B and
B2C flows can never cross-write each other's tables.

Security:
- subscribe / unlock / status require a valid Supabase JWT AND org ownership.
- webhook validates Stripe-Signature against STRIPE_ORG_WEBHOOK_SECRET — rejects unsigned.
- stripe_customer_id / stripe_subscription_id are NEVER returned to clients or logged in full.

Graceful degradation:
- stripe library missing OR STRIPE_SECRET_KEY empty OR PAYMENT_ENABLED=False → 503.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.config import settings
from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import RATE_DEFAULT, limiter
from app.schemas.org_billing import (
    OrgBillingStatus,
    OrgCheckoutResponse,
    WebhookAck,
)
from app.services.org_entitlements import _parse_dt, org_has_report_access

# ── Optional Stripe import — graceful if not installed (mirrors subscription.py) ──
try:
    import stripe as _stripe  # type: ignore[import-untyped]

    _STRIPE_AVAILABLE = True
except ImportError:
    _stripe = None  # type: ignore[assignment]
    _STRIPE_AVAILABLE = False


router = APIRouter(prefix="/org-billing", tags=["Org Billing"])

_STRIPE_NOT_CONFIGURED = HTTPException(
    status_code=503,
    detail={
        "code": "STRIPE_NOT_CONFIGURED",
        "message": "Payment processing is not configured on this server",
    },
)

_PAYMENT_DISABLED = HTTPException(
    status_code=503,
    detail={
        "code": "PAYMENT_NOT_ENABLED",
        "message": "Payment processing is not enabled on this server",
    },
)


def _get_stripe_client():
    """Return a configured Stripe client or raise 503 (mirrors subscription.py)."""
    if not settings.payment_enabled:
        raise _PAYMENT_DISABLED
    if not _STRIPE_AVAILABLE:
        raise _STRIPE_NOT_CONFIGURED
    if not settings.stripe_secret_key:
        raise _STRIPE_NOT_CONFIGURED
    _stripe.api_key = settings.stripe_secret_key
    return _stripe


async def _get_owned_org(db_admin: SupabaseAdmin, user_id: str) -> dict:
    """Return the org owned by the caller (id, name, stripe_customer_id) or raise 403."""
    result = (
        await db_admin.table("organizations")
        .select("id, name, stripe_customer_id, subscription_expires_at")
        .eq("owner_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_ORG_OWNER", "message": "You must own an organization to manage billing"},
        )
    return result.data


async def _ensure_stripe_customer(stripe, db_admin: SupabaseAdmin, org: dict, user_id: str) -> str:
    """Return the org's Stripe customer id, creating + persisting it on first use.

    Persists immediately (before checkout) so a later failure cannot orphan the
    customer or create a duplicate on retry — same approach as subscription.py.
    """
    customer_id: str | None = org.get("stripe_customer_id")
    if customer_id:
        return customer_id

    # Resolve owner email for the Stripe customer record (best-effort).
    try:
        auth_response = await db_admin.auth.admin.get_user_by_id(user_id)
        user_email: str | None = auth_response.user.email if auth_response.user else None
    except Exception as e:  # noqa: BLE001 — exception may contain the email; never str(e)
        logger.warning("Could not retrieve owner email for Stripe customer", org_id=org["id"], error=type(e).__name__)
        user_email = None

    try:
        params: dict = {"metadata": {"volaura_org_id": org["id"]}, "name": org.get("name") or None}
        if user_email:
            params["email"] = user_email
        customer = stripe.Customer.create(**params)
        customer_id = customer["id"]
        await db_admin.table("organizations").update({"stripe_customer_id": customer_id}).eq("id", org["id"]).execute()
        logger.info("Org Stripe customer created and persisted", org_id=org["id"])
        return customer_id
    except Exception as e:  # noqa: BLE001
        logger.error("Org Stripe customer creation failed", org_id=org["id"], error=str(e))
        raise HTTPException(
            status_code=502,
            detail={"code": "STRIPE_ERROR", "message": "Payment provider error — please try again"},
        )


# ── GET /api/org-billing/status ───────────────────────────────────────────────


@router.get("/status", response_model=OrgBillingStatus)
@limiter.limit(RATE_DEFAULT)
async def get_org_billing_status(
    request: Request,
    user_id: CurrentUserId,
    db_admin: SupabaseAdmin,
) -> OrgBillingStatus:
    """Billing posture for the caller's organization: subscription + unlocked campaigns."""
    org = await _get_owned_org(db_admin, user_id)

    expires_raw = org.get("subscription_expires_at")
    expires_at = _parse_dt(expires_raw) if expires_raw else None
    has_sub = bool(expires_at and expires_at > datetime.now(UTC))

    unlocks = (
        await db_admin.table("campaign_report_unlocks")
        .select("campaign_id")
        .eq("org_id", org["id"])
        .eq("status", "paid")
        .execute()
    )
    unlocked_ids = [r["campaign_id"] for r in (unlocks.data or [])]

    return OrgBillingStatus(
        has_active_subscription=has_sub,
        subscription_expires_at=expires_at,
        unlocked_campaign_ids=unlocked_ids,
        org_billing_enabled=settings.org_billing_enabled,
    )


# ── POST /api/org-billing/subscribe ───────────────────────────────────────────


@router.post("/subscribe", response_model=OrgCheckoutResponse, status_code=201)
@limiter.limit(RATE_DEFAULT)
async def create_subscription_checkout(
    request: Request,
    user_id: CurrentUserId,
    db_admin: SupabaseAdmin,
) -> OrgCheckoutResponse:
    """Create a recurring org subscription Checkout Session (the 'package' tier)."""
    stripe = _get_stripe_client()
    if not settings.stripe_org_subscription_price_id:
        raise HTTPException(
            status_code=503,
            detail={"code": "STRIPE_NOT_CONFIGURED", "message": "Org subscription price not configured"},
        )

    org = await _get_owned_org(db_admin, user_id)
    customer_id = await _ensure_stripe_customer(stripe, db_admin, org, user_id)

    base_url = settings.app_url.rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": settings.stripe_org_subscription_price_id, "quantity": 1}],
            success_url=f"{base_url}/my-organization/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/my-organization/billing/cancelled",
            customer_update={"address": "auto"},
            metadata={"volaura_org_id": org["id"]},
            subscription_data={"metadata": {"volaura_org_id": org["id"]}},
        )
        logger.info("Org subscription checkout created", org_id=org["id"])
        return OrgCheckoutResponse(checkout_url=session["url"])
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error("Org subscription checkout failed", org_id=org["id"], error=str(e))
        raise HTTPException(
            status_code=502,
            detail={"code": "STRIPE_ERROR", "message": "Payment provider error — please try again"},
        )


# ── POST /api/org-billing/campaigns/{campaign_id}/unlock ──────────────────────


@router.post("/campaigns/{campaign_id}/unlock", response_model=OrgCheckoutResponse, status_code=201)
@limiter.limit(RATE_DEFAULT)
async def create_campaign_unlock_checkout(
    request: Request,
    campaign_id: str,
    user_id: CurrentUserId,
    db_admin: SupabaseAdmin,
) -> OrgCheckoutResponse:
    """Create a one-time Checkout Session to unlock a single campaign's report."""
    _validate_uuid(campaign_id)
    stripe = _get_stripe_client()
    if not settings.stripe_campaign_report_price_id:
        raise HTTPException(
            status_code=503,
            detail={"code": "STRIPE_NOT_CONFIGURED", "message": "Campaign report price not configured"},
        )

    org = await _get_owned_org(db_admin, user_id)

    # Campaign must belong to this org.
    campaign = (
        await db_admin.table("screening_campaigns")
        .select("id")
        .eq("id", campaign_id)
        .eq("org_id", org["id"])
        .maybe_single()
        .execute()
    )
    if not campaign or not campaign.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign not found"},
        )

    # Don't let an org pay twice — already covered by a subscription or a prior unlock.
    if await org_has_report_access(db_admin, org["id"], campaign_id):
        raise HTTPException(
            status_code=409,
            detail={"code": "ALREADY_HAS_ACCESS", "message": "You already have access to this report"},
        )

    customer_id = await _ensure_stripe_customer(stripe, db_admin, org, user_id)

    base_url = settings.app_url.rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="payment",
            line_items=[{"price": settings.stripe_campaign_report_price_id, "quantity": 1}],
            success_url=f"{base_url}/my-organization/campaigns?unlocked={campaign_id}",
            cancel_url=f"{base_url}/my-organization/campaigns",
            customer_update={"address": "auto"},
            metadata={"volaura_org_id": org["id"], "volaura_campaign_id": campaign_id},
            payment_intent_data={"metadata": {"volaura_org_id": org["id"], "volaura_campaign_id": campaign_id}},
        )
        logger.info("Campaign unlock checkout created", org_id=org["id"], campaign_id=campaign_id)
        return OrgCheckoutResponse(checkout_url=session["url"])
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error("Campaign unlock checkout failed", org_id=org["id"], campaign_id=campaign_id, error=str(e))
        raise HTTPException(
            status_code=502,
            detail={"code": "STRIPE_ERROR", "message": "Payment provider error — please try again"},
        )


# ── POST /api/org-billing/webhook ─────────────────────────────────────────────
# Separate signing secret from the B2C webhook. Lenient rate limit (Stripe bursts).


@router.post("/webhook", response_model=WebhookAck)
@limiter.limit("100/minute")
async def org_stripe_webhook(request: Request) -> WebhookAck:
    """Handle org-billing Stripe events.

    Handled:
    - checkout.session.completed (mode=payment + campaign metadata) → unlock campaign report
    - customer.subscription.created / updated / deleted              → org subscription state
    """
    stripe = _get_stripe_client()

    if not settings.stripe_org_webhook_secret:
        logger.warning("Org webhook received but STRIPE_ORG_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=503,
            detail={"code": "STRIPE_NOT_CONFIGURED", "message": "Org webhook secret not configured"},
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_org_webhook_secret,
        )
    except stripe.errors.SignatureVerificationError:
        logger.warning("Org webhook signature verification failed")
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_SIGNATURE", "message": "Webhook signature verification failed"},
        )
    except Exception as e:  # noqa: BLE001
        logger.error("Org webhook payload parsing failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_PAYLOAD", "message": "Could not parse webhook payload"},
        )

    event_id: str = event.get("id", "")
    event_type: str = event["type"]
    data_object: dict = event["data"]["object"]

    logger.info("Org webhook received", event_type=event_type, event_id=event_id)

    # ── Idempotency (reuse processed_stripe_events; event_id is globally unique) ──
    if await _is_org_stripe_event_processed(event_id):
        logger.info("Org webhook already processed — skipping", event_id=event_id)
        return WebhookAck()

    if event_type == "checkout.session.completed":
        success = await _handle_checkout_completed(data_object)
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"code": "UNLOCK_WRITE_FAILED", "message": "Could not record unlock — Stripe will retry"},
            )

    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        success = await _handle_org_subscription_upsert(data_object)
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"code": "ORG_NOT_FOUND", "message": "Org not yet linked — Stripe will retry"},
            )

    elif event_type == "customer.subscription.deleted":
        success = await _handle_org_subscription_deleted(data_object)
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"code": "ORG_NOT_FOUND", "message": "Org not yet linked — Stripe will retry"},
            )

    else:
        logger.info("Unhandled org Stripe event type — acknowledged", event_type=event_type)

    await _mark_org_stripe_event_processed(event_id, event_type)
    return WebhookAck()


# ── Webhook sub-handlers ───────────────────────────────────────────────────────
# Own copies of the idempotency helpers (rather than importing subscription.py's)
# so org-billing tests can patch them independently and the working B2C path stays
# untouched. Both write the same shared processed_stripe_events table.


async def _is_org_stripe_event_processed(event_id: str) -> bool:
    from supabase._async.client import create_client as acreate_client

    admin = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
    result = await admin.table("processed_stripe_events").select("event_id").eq("event_id", event_id).limit(1).execute()
    return bool(result.data)


async def _mark_org_stripe_event_processed(event_id: str, event_type: str) -> None:
    from supabase._async.client import create_client as acreate_client

    admin = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
    try:
        await (
            admin.table("processed_stripe_events")
            .insert({"event_id": event_id, "event_type": event_type}, upsert=False)
            .execute()
        )
    except Exception as e:  # noqa: BLE001 — best-effort; event already processed
        logger.warning("Could not record processed org Stripe event", event_id=event_id, error=str(e)[:200])


async def _handle_checkout_completed(session: dict) -> bool:
    """One-time campaign-report unlock. Returns True when handled (incl. no-op cases).

    Returns False only on a transient write failure so Stripe retries. Subscription-
    mode completions are a no-op here — they're handled by customer.subscription.* events.
    """
    if session.get("mode") != "payment":
        return True  # subscription checkout completion — handled elsewhere

    metadata: dict = session.get("metadata") or {}
    campaign_id = metadata.get("volaura_campaign_id")
    org_id = metadata.get("volaura_org_id")
    if not campaign_id or not org_id:
        logger.warning("Org checkout.session.completed missing campaign/org metadata — acknowledged")
        return True  # malformed/foreign event — retry won't help

    row = {
        "campaign_id": campaign_id,
        "org_id": org_id,
        "stripe_checkout_session_id": session.get("id"),
        "stripe_payment_intent_id": session.get("payment_intent"),
        "amount_total": session.get("amount_total"),
        "currency": session.get("currency"),
        "status": "paid",
    }
    from supabase._async.client import create_client as acreate_client

    admin = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
    try:
        # Idempotent: UNIQUE(campaign_id) — replay upserts the same row.
        await admin.table("campaign_report_unlocks").upsert(row, on_conflict="campaign_id").execute()
        logger.info("Campaign report unlocked via webhook", campaign_id=campaign_id, org_id=org_id)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to write campaign unlock — will retry", campaign_id=campaign_id, error=str(e)[:200])
        return False


# Stripe subscription status → does the org keep report access?
# https://docs.stripe.com/billing/subscriptions/overview#subscription-statuses
_ACTIVE_SUB_STATUSES = {"active", "trialing", "past_due"}  # past_due keeps access — payment may recover


async def _handle_org_subscription_upsert(sub: dict) -> bool:
    customer_id: str = sub.get("customer", "")
    subscription_id: str = sub.get("id", "")
    stripe_status: str = sub.get("status", "")
    current_period_end: int | None = sub.get("current_period_end")

    if stripe_status in _ACTIVE_SUB_STATUSES:
        ends_at = datetime.fromtimestamp(current_period_end, tz=UTC).isoformat() if current_period_end else None
        updates = {
            "subscription_tier": "growth",
            "subscription_expires_at": ends_at,
            "stripe_subscription_id": subscription_id,
        }
    else:
        # unpaid / canceled / incomplete_expired / paused → access lapses now.
        updates = {
            "subscription_tier": "free",
            "subscription_expires_at": datetime.now(UTC).isoformat(),
            "stripe_subscription_id": subscription_id,
        }
    return await _update_org_subscription(customer_id, updates)


async def _handle_org_subscription_deleted(sub: dict) -> bool:
    customer_id: str = sub.get("customer", "")
    return await _update_org_subscription(
        customer_id,
        {"subscription_tier": "free", "subscription_expires_at": datetime.now(UTC).isoformat()},
    )


async def _update_org_subscription(customer_id: str, updates: dict) -> bool:
    """Apply subscription updates to the org with this stripe_customer_id.

    Returns False if no org matched (org row not ready yet) so the caller raises
    500 and Stripe retries — mirrors subscription.py's profile-race handling.
    """
    from supabase._async.client import create_client as acreate_client

    admin = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
    result = await admin.table("organizations").update(updates).eq("stripe_customer_id", customer_id).execute()
    if not result.data:
        logger.warning(
            "Org webhook: no org matched stripe_customer_id — will retry",
            customer_id_prefix=customer_id[:8] if customer_id else "none",
            updates_keys=list(updates.keys()),
        )
        return False
    logger.info(
        "Org subscription updated via webhook",
        customer_id_prefix=customer_id[:8] if customer_id else "none",
        updates_keys=list(updates.keys()),
    )
    return True


def _validate_uuid(value: str) -> None:
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail={"code": "INVALID_UUID", "message": "Invalid id format"})
