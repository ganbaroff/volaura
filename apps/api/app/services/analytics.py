"""Analytics event tracking service.

Fire-and-forget event emitter that writes to public.analytics_events.
Never raises — analytics failure must never block product flows.

Usage:
    from app.services.analytics import track_event

    asyncio.create_task(track_event(
        db=db_admin,
        user_id=str(user_id),
        event_name="assessment_completed",
        properties={"competency_slug": slug, "score": competency_score},
    ))
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from supabase._async.client import AsyncClient


async def track_event(
    db: AsyncClient,
    user_id: str,
    event_name: str,
    properties: dict[str, Any] | None = None,
    session_id: str | None = None,
    locale: str | None = None,
    platform: str = "web",
) -> None:
    """Insert a single analytics event row.

    Never raises. Analytics failure is logged but does not propagate.
    Uses service-role db (SupabaseAdmin) — bypasses RLS INSERT restriction.
    """
    try:
        payload: dict[str, Any] = {
            "user_id": user_id,
            "event_name": event_name,
            "properties": properties or {},
            "platform": platform,
        }
        if session_id is not None:
            payload["session_id"] = session_id
        if locale is not None:
            payload["locale"] = locale

        await db.table("analytics_events").insert(payload).execute()
        logger.debug("analytics event tracked", event=event_name, user_id=user_id)
    except Exception as exc:
        logger.warning(
            "analytics track_event failed (non-fatal)",
            event=event_name,
            user_id=user_id,
            error=str(exc),
        )
