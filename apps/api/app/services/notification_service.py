"""Notification creation service — fire-and-forget helpers.

Usage:
    from app.services.notification_service import notify
    await notify(db_admin, user_id, "badge_earned", "You earned Gold!", body="Communication: Gold badge")
"""

from loguru import logger


async def notify(
    db_admin,
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
