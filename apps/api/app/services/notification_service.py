"""Notification creation service — fire-and-forget helpers.

Usage:
    from app.services.notification_service import notify
    await notify(db_admin, user_id, "badge_earned", "You earned Gold!", body="Communication: Gold badge")

    from app.services.notification_service import notify_profile_viewed
    await notify_profile_viewed(db_admin, volunteer_id, org_id, org_name)
"""

from datetime import UTC, datetime, timedelta

from loguru import logger
from supabase._async.client import AsyncClient as AsyncSupabaseClient

# Throttle: at most 1 org_view notification per (org, volunteer) pair per window
_PROFILE_VIEW_THROTTLE_HOURS = 24


async def notify(
    db_admin: AsyncSupabaseClient,
    user_id: str,
    notification_type: str,
    title: str,
    body: str | None = None,
    reference_id: str | None = None,
) -> None:
    """Insert a notification row. Fire-and-forget — never raises."""
    try:
        await db_admin.table("notifications").insert({
            "user_id": user_id,
            "type": notification_type,
            "title": title,
            "body": body,
            "reference_id": reference_id,
        }).execute()
    except Exception as e:
        logger.warning("Failed to create notification", user_id=user_id, type=notification_type, error=str(e))


async def notify_profile_viewed(
    db_admin: AsyncSupabaseClient,
    volunteer_id: str,
    org_id: str,
    org_name: str,
) -> bool:
    """Emit org_view notification with 24h throttle per (org, volunteer) pair.

    Throttle logic: queries idx_notifications_org_view_throttle partial index.
    One notification per (org_id, volunteer_id) pair per _PROFILE_VIEW_THROTTLE_HOURS window.

    Args:
        db_admin:     Admin Supabase client (service-role — bypasses RLS for insert)
        volunteer_id: UUID of the volunteer whose profile was viewed
        org_id:       UUID of the viewing organization (stored in reference_id)
        org_name:     Display name for the notification title

    Returns:
        True  — notification was inserted
        False — throttled (already sent within window) or error

    Never raises — safe to use with asyncio.create_task().
    """
    try:
        cutoff = (
            datetime.now(UTC) - timedelta(hours=_PROFILE_VIEW_THROTTLE_HOURS)
        ).isoformat()

        # Throttle check — uses idx_notifications_org_view_throttle partial index
        existing = (
            await db_admin.table("notifications")
            .select("id")
            .eq("user_id", volunteer_id)
            .eq("type", "org_view")
            .eq("reference_id", org_id)
            .gte("created_at", cutoff)
            .limit(1)
            .execute()
        )
        if existing.data:
            logger.debug(
                "Profile view notification throttled",
                volunteer_id=volunteer_id,
                org_id=org_id,
            )
            return False

        await db_admin.table("notifications").insert({
            "user_id": volunteer_id,
            "type": "org_view",
            "title": f"{org_name} viewed your AURA profile",
            "body": None,
            "reference_id": org_id,
        }).execute()

        logger.info(
            "Profile view notification sent",
            volunteer_id=volunteer_id,
            org_id=org_id,
        )
        return True

    except Exception as e:
        logger.warning(
            "Failed to emit profile_view notification",
            volunteer_id=volunteer_id,
            org_id=org_id,
            error=str(e),
        )
        return False
