"""Subscription router — trial tracking + Stripe Billing integration.

GET  /api/subscription/status          — current subscription status for authed user
POST /api/subscription/create-checkout — create Stripe Checkout Session (redirect flow)
POST /api/subscription/webhook         — Stripe webhook (no auth, validated by signature)

Security:
- Status + checkout endpoints require valid Supabase JWT (CurrentUserId)
- Webhook endpoint validates Stripe-Signature header — rejects all unsigned requests
- stripe_customer_id / stripe_subscription_id are NEVER logged in plain text
- SupabaseAdmin used for all subscription writes (RLS bypass needed for service writes)
- Webhook excluded from rate limiter (Stripe needs reliable delivery)

Graceful degradation:
- If stripe library not installed → checkout + webhook return 503 STRIPE_NOT_CONFIGURED
- If STRIPE_SECRET_KEY empty → same 503
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.config import settings
from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import RATE_DEFAULT, limiter
from app.schemas.subscription import (
    CheckoutSessionResponse,
    SubscriptionStatus,
    WebhookAck,
    build_subscription_status,
)

# ── Optional Stripe import — graceful if not installed ────────────────────────
try:
    import stripe as _stripe  # type: ignore[import-untyped]
    _STRIPE_AVAILABLE = True
except ImportError:
    _stripe = None  # type: ignore[assignment]
    _STRIPE_AVAILABLE = False


router = APIRouter(prefix="/subscription", tags=["Subscription"])

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
    """Return a configured Stripe client or raise 503."""
    if not settings.payment_enabled:
        raise _PAYMENT_DISABLED
    if not _STRIPE_AVAILABLE:
        raise _STRIPE_NOT_CONFIGURED
    if not settings.stripe_secret_key:
        raise _STRIPE_NOT_CONFIGURED
    # Set key on every call — no module-level state (matches per-request pattern)
    _stripe.api_key = settings.stripe_secret_key
    return _stripe


# ── GET /api/subscription/status ─────────────────────────────────────────────

@router.get("/status", response_model=SubscriptionStatus)
@limiter.limit(RATE_DEFAULT)
async def get_subscription_status(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> SubscriptionStatus:
    """Return current subscription status for the authenticated user.

    Auto-expires trials whose trial_ends_at has passed — writes the update
    to the database so subsequent reads are consistent without a cron job.
    """
    result = (
        await db.table("profiles")
        .select(
            "subscription_status, trial_ends_at, subscription_ends_at, stripe_customer_id"
        )
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    row: dict = result.data

    # ── Auto-expire stale trials ──────────────────────────────────────────────
    status = row.get("subscription_status", "trial")
    if status == "trial":
        trial_ends_at_raw = row.get("trial_ends_at")
        if trial_ends_at_raw:
            trial_ends_at = (
                trial_ends_at_raw
                if isinstance(trial_ends_at_raw, datetime)
                else datetime.fromisoformat(str(trial_ends_at_raw).replace("Z", "+00:00"))
            )
            if trial_ends_at.tzinfo is None:
                trial_ends_at = trial_ends_at.replace(tzinfo=timezone.utc)

            if trial_ends_at < datetime.now(timezone.utc):
                await db.table("profiles").update(
                    {"subscription_status": "expired"}
                ).eq("id", user_id).execute()
                row["subscription_status"] = "expired"
                logger.info("Trial auto-expired", user_id=user_id)

    return build_subscription_status(row)


# ── POST /api/subscription/create-checkout ───────────────────────────────────

@router.post("/create-checkout", response_model=CheckoutSessionResponse, status_code=201)
@limiter.limit(RATE_DEFAULT)
async def create_checkout_session(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> CheckoutSessionResponse:
    """Create a Stripe Checkout Session for the monthly subscription.

    Flow:
    1. Read profile (email + existing stripe_customer_id)
    2. Create Stripe Customer if not already linked
    3. Persist new stripe_customer_id immediately (before checkout — avoids orphans)
    4. Create Checkout Session with customer pre-filled
    5. Return {checkout_url}
    """
    stripe = _get_stripe_client()

    # ── Read profile ──────────────────────────────────────────────────────────
    profile_result = (
        await db.table("profiles")
        .select("stripe_customer_id, subscription_status")
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not profile_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    profile = profile_result.data
    stripe_customer_id: str | None = profile.get("stripe_customer_id")

    # ── Resolve user email from Supabase Auth ─────────────────────────────────
    try:
        auth_response = await db.auth.admin.get_user_by_id(user_id)
        user_email: str | None = auth_response.user.email if auth_response.user else None
    except Exception as e:
        logger.warning("Could not retrieve user email for Stripe customer", user_id=user_id, error=type(e).__name__)  # SEC-Q5: no str(e) — exception may contain email
        user_email = None

    # ── Create Stripe Customer if not linked ──────────────────────────────────
    if not stripe_customer_id:
        try:
            customer_params: dict = {"metadata": {"volaura_user_id": user_id}}
            if user_email:
                customer_params["email"] = user_email
            customer = stripe.Customer.create(**customer_params)
            stripe_customer_id = customer["id"]

            # Persist immediately — if checkout creation fails below, the customer
            # record is still linked so we don't create a duplicate on retry.
            await db.table("profiles").update(
                {"stripe_customer_id": stripe_customer_id}
            ).eq("id", user_id).execute()

            logger.info("Stripe customer created and persisted", user_id=user_id)
        except Exception as e:
            logger.error("Stripe customer creation failed", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=502,
                detail={"code": "STRIPE_ERROR", "message": "Payment provider error — please try again"},
            )

    # ── Create Checkout Session ───────────────────────────────────────────────
    if not settings.stripe_price_id:
        raise HTTPException(
            status_code=503,
            detail={"code": "STRIPE_NOT_CONFIGURED", "message": "Subscription price not configured"},
        )

    base_url = settings.app_url.rstrip("/")
    success_url = f"{base_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/subscription/cancelled"

    try:
        price_id = settings.stripe_price_id
        if not price_id:
            raise HTTPException(
                status_code=503,
                detail={"code": "STRIPE_NOT_CONFIGURED", "message": "Subscription price ID not configured"},
            )

        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            customer_update={"address": "auto"},
            metadata={"volaura_user_id": user_id},
        )
        logger.info("Checkout session created", user_id=user_id)
        return CheckoutSessionResponse(checkout_url=session["url"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Stripe checkout session creation failed", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=502,
            detail={"code": "STRIPE_ERROR", "message": "Payment provider error — please try again"},
        )


# ── POST /api/subscription/webhook ───────────────────────────────────────────
# Rate limit is lenient (100/minute per IP) to block DoS while allowing Stripe bursts.
# Stripe's legitimate delivery rate never exceeds ~20/minute from a single IP.
# Signature verification is the PRIMARY security gate — rate limit is defense-in-depth.

@router.post("/webhook", response_model=WebhookAck)
@limiter.limit("100/minute")
async def stripe_webhook(request: Request) -> WebhookAck:
    """Handle Stripe webhook events.

    Security: validates Stripe-Signature header using stripe_webhook_secret.
    Rejects any request that fails signature verification with 400.

    Handled events:
    - customer.subscription.created  → status = active
    - customer.subscription.updated  → status = active | cancelled depending on Stripe status
    - customer.subscription.deleted  → status = cancelled
    """
    stripe = _get_stripe_client()

    if not settings.stripe_webhook_secret:
        logger.warning("Stripe webhook received but STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=503,
            detail={"code": "STRIPE_NOT_CONFIGURED", "message": "Webhook secret not configured"},
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except stripe.errors.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_SIGNATURE", "message": "Webhook signature verification failed"},
        )
    except Exception as e:
        logger.error("Stripe webhook payload parsing failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_PAYLOAD", "message": "Could not parse webhook payload"},
        )

    event_id: str = event.get("id", "")
    event_type: str = event["type"]
    data_object: dict = event["data"]["object"]

    logger.info("Stripe webhook received", event_type=event_type, event_id=event_id)

    # ── Idempotency check (R-02) ──────────────────────────────────────────────
    # Stripe delivers events at-least-once. Check processed_stripe_events before
    # executing any subscription state change to prevent double-processing.
    already_processed = await _is_stripe_event_processed(event_id)
    if already_processed:
        logger.info("Stripe webhook already processed — skipping", event_id=event_id)
        return WebhookAck()

    # ── customer.subscription.created ────────────────────────────────────────
    if event_type == "customer.subscription.created":
        success = await _handle_subscription_created(data_object)
        if not success:
            # Profile not found — return 500 so Stripe retries (signup race condition)
            raise HTTPException(status_code=500, detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not yet created — Stripe will retry"})

    # ── customer.subscription.updated ────────────────────────────────────────
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data_object)

    # ── customer.subscription.deleted ────────────────────────────────────────
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data_object)

    else:
        # Unhandled event type — acknowledge silently (Stripe retries on non-2xx)
        logger.info("Unhandled Stripe event type — acknowledged", event_type=event_type)

    # Mark event as processed — prevents double-processing on Stripe retries
    await _mark_stripe_event_processed(event_id, event_type)

    return WebhookAck()


# ── Webhook sub-handlers ──────────────────────────────────────────────────────

async def _is_stripe_event_processed(event_id: str) -> bool:
    """Return True if this Stripe event_id was already processed (idempotency check)."""
    from supabase._async.client import create_client as acreate_client

    admin = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
    result = (
        await admin.table("processed_stripe_events")
        .select("event_id")
        .eq("event_id", event_id)
        .limit(1)
        .execute()
    )
    return bool(result.data)


async def _mark_stripe_event_processed(event_id: str, event_type: str) -> None:
    """Record a Stripe event as processed. Idempotent — duplicate inserts are silently ignored."""
    from supabase._async.client import create_client as acreate_client

    admin = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
    try:
        await admin.table("processed_stripe_events").insert(
            {"event_id": event_id, "event_type": event_type},
            upsert=False,
        ).execute()
    except Exception as e:
        # Log but don't fail — event was processed; idempotency insert is best-effort
        logger.warning("Could not record processed Stripe event", event_id=event_id, error=str(e)[:200])


async def _resolve_user_id_by_stripe_customer(
    customer_id: str,
    db_factory=None,
) -> str | None:
    """Look up the Volaura user_id for a given stripe_customer_id.

    We need a fresh admin client here since webhook has no auth context.
    """
    from supabase._async.client import create_client as acreate_client

    admin = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
    result = (
        await admin.table("profiles")
        .select("id")
        .eq("stripe_customer_id", customer_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]
    return None


async def _update_profile_subscription(
    customer_id: str,
    updates: dict,
) -> bool:
    """Apply subscription field updates to the profile with the given stripe_customer_id."""
    from supabase._async.client import create_client as acreate_client

    admin = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )

    result = (
        await admin.table("profiles")
        .update(updates)
        .eq("stripe_customer_id", customer_id)
        .execute()
    )

    if not result.data:
        # No profile matched — profile row may not yet exist (signup race condition).
        # Return False; caller must raise HTTP 500 so Stripe retries.
        logger.warning(
            "Webhook: no profile matched stripe_customer_id — will retry",
            customer_id_prefix=customer_id[:8] if customer_id else "none",
            updates_keys=list(updates.keys()),
        )
        return False
    else:
        logger.info(
            "Subscription profile updated via webhook",
            customer_id_prefix=customer_id[:8] if customer_id else "none",
            updates_keys=list(updates.keys()),
        )
        return True


async def _handle_subscription_created(sub: dict) -> bool:
    customer_id: str = sub.get("customer", "")
    subscription_id: str = sub.get("id", "")
    current_period_end: int | None = sub.get("current_period_end")

    ends_at: str | None = None
    if current_period_end:
        ends_at = datetime.fromtimestamp(current_period_end, tz=timezone.utc).isoformat()

    return await _update_profile_subscription(
        customer_id,
        {
            "subscription_status": "active",
            "stripe_subscription_id": subscription_id,
            "subscription_started_at": datetime.now(timezone.utc).isoformat(),
            "subscription_ends_at": ends_at,
        },
    ) is not False


async def _handle_subscription_updated(sub: dict) -> None:
    customer_id: str = sub.get("customer", "")
    subscription_id: str = sub.get("id", "")
    stripe_status: str = sub.get("status", "")
    current_period_end: int | None = sub.get("current_period_end")

    # Map Stripe subscription statuses to Volaura statuses
    # https://docs.stripe.com/billing/subscriptions/overview#subscription-statuses
    status_map = {
        "active": "active",
        "trialing": "trial",
        "past_due": "active",   # keep active — payment may recover
        "unpaid": "expired",
        "canceled": "cancelled",
        "incomplete": "trial",
        "incomplete_expired": "expired",
        "paused": "expired",
    }
    volaura_status = status_map.get(stripe_status, "active")

    ends_at: str | None = None
    if current_period_end:
        ends_at = datetime.fromtimestamp(current_period_end, tz=timezone.utc).isoformat()

    await _update_profile_subscription(
        customer_id,
        {
            "subscription_status": volaura_status,
            "stripe_subscription_id": subscription_id,
            "subscription_ends_at": ends_at,
        },
    )


async def _handle_subscription_deleted(sub: dict) -> None:
    customer_id: str = sub.get("customer", "")

    await _update_profile_subscription(
        customer_id,
        {
            "subscription_status": "cancelled",
            "subscription_ends_at": datetime.now(timezone.utc).isoformat(),
        },
    )
