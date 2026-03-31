"""Notifications router — user notification feed.

Endpoints:
  GET  /notifications             List notifications (newest first, paginated)
  GET  /notifications/unread-count  Unread count for sidebar badge
  PATCH /notifications/{id}/read  Mark single notification read
  PATCH /notifications/read-all   Mark all notifications read
"""

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict

from app.deps import CurrentUserId, SupabaseUser
from app.middleware.rate_limit import limiter, RATE_DEFAULT

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ── Schemas ────────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    title: str
    body: str | None
    is_read: bool
    reference_id: str | None
    created_at: str


class NotificationListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notifications: list[NotificationOut]
    unread_count: int
    total: int


class UnreadCountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    unread_count: int


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/unread-count", response_model=UnreadCountOut)
@limiter.limit(RATE_DEFAULT)
async def get_unread_count(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> UnreadCountOut:
    """Unread notification count — used for sidebar badge."""
    result = await db.table("notifications") \
        .select("id", count="exact") \
        .eq("user_id", user_id) \
        .eq("is_read", False) \
        .execute()

    return UnreadCountOut(unread_count=result.count or 0)


@router.get("", response_model=NotificationListOut)
@limiter.limit(RATE_DEFAULT)
async def list_notifications(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> NotificationListOut:
    """List user notifications, newest first."""
    result = await db.table("notifications") \
        .select("id, type, title, body, is_read, reference_id, created_at", count="exact") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .range(offset, offset + limit - 1) \
        .execute()

    notifications = [NotificationOut(**row) for row in (result.data or [])]

    # Derive unread count from the already-fetched page — avoids a second DB round-trip.
    # Acceptable because pages are small (max 50) and unread items cluster at the top.
    unread_count = sum(1 for n in notifications if not n.is_read)

    return NotificationListOut(
        notifications=notifications,
        unread_count=unread_count,
        total=result.count or 0,
    )


@router.patch("/read-all", response_model=UnreadCountOut)
@limiter.limit(RATE_DEFAULT)
async def mark_all_read(
    request: Request,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> UnreadCountOut:
    """Mark all unread notifications as read."""
    await db.table("notifications") \
        .update({"is_read": True}) \
        .eq("user_id", user_id) \
        .eq("is_read", False) \
        .execute()

    logger.info("Marked all notifications read", user_id=user_id)
    return UnreadCountOut(unread_count=0)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
@limiter.limit(RATE_DEFAULT)
async def mark_notification_read(
    request: Request,
    notification_id: str,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> NotificationOut:
    """Mark a single notification as read. Returns updated notification."""
    result = await db.table("notifications") \
        .update({"is_read": True}) \
        .eq("id", notification_id) \
        .eq("user_id", user_id) \
        .execute()

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notification not found"},
        )

    return NotificationOut(**result.data[0])
