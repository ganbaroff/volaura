"""Subscription Pydantic schemas (v2).

Covers: status read, checkout session creation, webhook payload ack.
Stripe IDs are present in SubscriptionStatus only for admin-level
callers — never included in public-facing responses.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, computed_field


class SubscriptionStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str  # trial | active | expired | cancelled
    trial_ends_at: datetime | None
    subscription_ends_at: datetime | None
    # Computed — not stored in DB
    days_remaining: int
    is_active: bool  # True when status is 'trial' or 'active'
    # stripe_customer_id intentionally excluded — internal payment ID, never exposed to clients


class CheckoutSessionResponse(BaseModel):
    """Response for POST /api/subscription/create-checkout."""

    checkout_url: str


class WebhookAck(BaseModel):
    """Stripe webhook handler always returns this on success."""

    received: bool = True


# ── Helpers ──────────────────────────────────────────────────────────────────

def compute_days_remaining(
    status: str,
    trial_ends_at: datetime | None,
    subscription_ends_at: datetime | None,
) -> int:
    """Return days remaining for the current active period.

    - 'trial'  → days until trial_ends_at
    - 'active' → days until subscription_ends_at
    - anything else → 0
    """
    now = datetime.now(timezone.utc)
    if status == "trial" and trial_ends_at:
        delta = trial_ends_at - now
        return max(0, delta.days)
    if status == "active" and subscription_ends_at:
        delta = subscription_ends_at - now
        return max(0, delta.days)
    return 0


def build_subscription_status(profile_row: dict) -> SubscriptionStatus:
    """Convert a profiles table row dict to SubscriptionStatus.

    Normalises tz-naive datetimes from Supabase to UTC-aware.
    """
    status = profile_row.get("subscription_status", "trial")

    def _parse_dt(val) -> datetime | None:
        if val is None:
            return None
        if isinstance(val, datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=timezone.utc)
            return val
        # ISO string from Supabase
        dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        return dt

    trial_ends_at = _parse_dt(profile_row.get("trial_ends_at"))
    subscription_ends_at = _parse_dt(profile_row.get("subscription_ends_at"))

    return SubscriptionStatus(
        status=status,
        trial_ends_at=trial_ends_at,
        subscription_ends_at=subscription_ends_at,
        days_remaining=compute_days_remaining(status, trial_ends_at, subscription_ends_at),
        is_active=status in ("trial", "active"),
    )
