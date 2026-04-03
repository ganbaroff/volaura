"""Analytics endpoints — frontend event ingestion.

Single endpoint: POST /api/analytics/event
Accepts events from the frontend and writes to analytics_events table.
Rate limited to prevent abuse. Auth required.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import limiter
from app.services.analytics import track_event

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class TrackEventRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    event_name: str
    properties: dict | None = None
    session_id: str | None = None
    locale: str | None = None
    platform: str = "web"


@router.post("/event", status_code=204)
@limiter.limit("60/minute")
async def ingest_event(
    request: Request,
    body: TrackEventRequest,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> None:
    """Ingest a frontend analytics event. Fire-and-forget."""
    await track_event(
        db=db_admin,
        user_id=str(user_id),
        event_name=body.event_name,
        properties=body.properties,
        session_id=body.session_id,
        locale=body.locale,
        platform=body.platform,
    )
