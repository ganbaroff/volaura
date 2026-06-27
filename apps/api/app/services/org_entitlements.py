"""Org billing entitlements — does an organization have access to a paid surface?

Single source of truth for the report paywall (campaigns.py) and the billing
status endpoint (org_billing.py). An org has report access when EITHER:

  1. it has an active org subscription  → organizations.subscription_expires_at > now(), OR
  2. it bought a one-time unlock for THAT campaign → campaign_report_unlocks.status = 'paid'.

When settings.org_billing_enabled is False the report is free for everyone — the
gate is bypassed entirely (design-partner phase). Callers must check that flag
themselves before treating a False return as "blocked".
"""

from __future__ import annotations

from datetime import UTC, datetime

from supabase._async.client import AsyncClient


async def org_has_active_subscription(db_admin: AsyncClient, org_id: str) -> bool:
    """True if the org has a non-expired paid subscription period."""
    result = (
        await db_admin.table("organizations")
        .select("subscription_expires_at")
        .eq("id", org_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        return False
    expires_raw = result.data.get("subscription_expires_at")
    if not expires_raw:
        return False
    return _parse_dt(expires_raw) > datetime.now(UTC)


async def campaign_is_unlocked(db_admin: AsyncClient, campaign_id: str) -> bool:
    """True if a one-time report unlock has been paid for this campaign."""
    result = (
        await db_admin.table("campaign_report_unlocks")
        .select("status")
        .eq("campaign_id", campaign_id)
        .eq("status", "paid")
        .limit(1)
        .execute()
    )
    return bool(result.data)


async def org_has_report_access(db_admin: AsyncClient, org_id: str, campaign_id: str) -> bool:
    """True if the org may read this campaign's ranked report.

    Subscription is checked first (covers all campaigns); falls back to the
    per-campaign one-time unlock. Does NOT consult settings.org_billing_enabled —
    the caller decides whether to enforce.
    """
    if await org_has_active_subscription(db_admin, org_id):
        return True
    return await campaign_is_unlocked(db_admin, campaign_id)


def _parse_dt(val) -> datetime:
    """Normalise a Supabase timestamp (datetime or ISO string) to UTC-aware."""
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=UTC)
    dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
