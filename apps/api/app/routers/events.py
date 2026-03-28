"""Events and Registrations endpoints."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import limiter, RATE_PROFILE_WRITE, RATE_DISCOVERY
from app.schemas.event import (
    CheckInRequest,
    CoordinatorRatingRequest,
    EventAttendeeRow,
    EventCreate,
    EventResponse,
    EventUpdate,
    RegistrationResponse,
    VolunteerRatingRequest,
)

router = APIRouter(prefix="/events", tags=["Events"])


# ── List & create ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[EventResponse])
@limiter.limit(RATE_DISCOVERY)
async def list_events(
    request: Request,
    db: SupabaseAdmin,
    status: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
) -> list[EventResponse]:
    """List public open events — no auth required."""
    q = db.table("events").select("*").eq("is_public", True).neq("status", "draft")
    if status:
        q = q.eq("status", status)
    result = await q.order("start_date").range(offset, offset + limit - 1).execute()
    return [EventResponse(**row) for row in (result.data or [])]


@router.get("/{event_id}", response_model=EventResponse)
@limiter.limit(RATE_DISCOVERY)
async def get_event(request: Request, event_id: str, db: SupabaseAdmin) -> EventResponse:
    """Get a single event by ID."""
    _validate_uuid(event_id, "event_id")
    result = await db.table("events").select("*").eq("id", event_id).neq("status", "draft").single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    return EventResponse(**result.data)


@router.post("", response_model=EventResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_event(
    request: Request,
    payload: EventCreate,
    db: SupabaseUser,
    user_id: CurrentUserId,
    db_admin: SupabaseAdmin,
) -> EventResponse:
    """Create an event — caller must own an organization."""
    # Find org owned by this user
    org = await db_admin.table("organizations").select("id").eq("owner_id", user_id).execute()
    if not org.data:
        raise HTTPException(
            status_code=403,
            detail={"code": "NO_ORGANIZATION", "message": "You must own an organization to create events"},
        )
    org_id = org.data[0]["id"]

    row = {
        "organization_id": org_id,
        **payload.model_dump(mode="json"),
    }
    result = await db.table("events").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create event"})
    return EventResponse(**result.data[0])


@router.put("/{event_id}", response_model=EventResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_event(
    request: Request,
    event_id: str,
    payload: EventUpdate,
    db: SupabaseUser,
    user_id: CurrentUserId,
    db_admin: SupabaseAdmin,
) -> EventResponse:
    """Update an event — org owner only."""
    _validate_uuid(event_id, "event_id")
    update_data = payload.model_dump(mode="json", exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail={"code": "NO_FIELDS", "message": "No fields to update"})

    # Verify ownership via RLS (SupabaseUser) — the policy handles it
    result = await db.table("events").update(update_data).eq("id", event_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found or not authorized"})
    return EventResponse(**result.data[0])


@router.delete("/{event_id}", status_code=204)
@limiter.limit(RATE_PROFILE_WRITE)
async def delete_event(
    request: Request,
    event_id: str,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> None:
    """Delete (cancel) an event — org owner only (RLS enforced)."""
    _validate_uuid(event_id, "event_id")
    result = await db.table("events").update({"status": "cancelled"}).eq("id", event_id).execute()
    # HIGH-04 + HIGH-06 FIX: verify update succeeded + audit log
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found or not owned"})
    logger.info("Event cancelled", user_id=user_id, event_id=event_id)


# ── Registrations ─────────────────────────────────────────────────────────────

@router.post("/{event_id}/register", response_model=RegistrationResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def register_for_event(
    request: Request,
    event_id: str,
    db: SupabaseUser,
    user_id: CurrentUserId,
    db_admin: SupabaseAdmin,
) -> RegistrationResponse:
    """Volunteer registers for an event."""
    _validate_uuid(event_id, "event_id")
    # Check event is open
    event = await db_admin.table("events").select("status, capacity").eq("id", event_id).single().execute()
    if not event.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    if event.data["status"] != "open":
        raise HTTPException(status_code=409, detail={"code": "EVENT_NOT_OPEN", "message": "Event is not accepting registrations"})

    # Check capacity
    if event.data.get("capacity"):
        count = await db_admin.table("registrations").select("id", count="exact").eq("event_id", event_id).in_("status", ["approved", "pending"]).execute()
        if (count.count or 0) >= event.data["capacity"]:
            raise HTTPException(status_code=409, detail={"code": "EVENT_FULL", "message": "Event is at capacity — you have been waitlisted"})

    # Check duplicate
    existing = await db.table("registrations").select("id, status").eq("event_id", event_id).eq("volunteer_id", user_id).execute()
    if existing.data:
        reg = existing.data[0]
        if reg["status"] not in ("cancelled",):
            raise HTTPException(status_code=409, detail={"code": "ALREADY_REGISTERED", "message": "You are already registered for this event"})
        # Re-activate cancelled registration
        result = await db.table("registrations").update({"status": "pending"}).eq("id", reg["id"]).execute()
        return RegistrationResponse(**result.data[0])

    # New registration
    check_in_code = secrets.token_urlsafe(12)
    result = await db.table("registrations").insert({
        "event_id": event_id,
        "volunteer_id": user_id,
        "status": "pending",
        "check_in_code": check_in_code,
    }).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail={"code": "REGISTER_FAILED", "message": "Failed to register"})
    return RegistrationResponse(**result.data[0])


@router.post("/{event_id}/checkin", response_model=RegistrationResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def check_in(
    request: Request,
    event_id: str,
    payload: CheckInRequest,
    db: SupabaseAdmin,
    user_id: CurrentUserId,
) -> RegistrationResponse:
    """Check in a volunteer via their QR code value.

    SECURITY: Verifies caller is the org owner (event coordinator) before
    allowing check-in. Without this, any authenticated user with a leaked
    check-in code could check in volunteers.
    """
    _validate_uuid(event_id, "event_id")
    # Verify caller is event coordinator (org owner)
    event = await db.table("events").select("organization_id").eq("id", event_id).single().execute()
    if not event.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})

    org = await db.table("organizations").select("owner_id").eq("id", event.data["organization_id"]).single().execute()
    if not org.data or org.data["owner_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_COORDINATOR", "message": "Only the event coordinator can check in volunteers"},
        )

    result = await db.table("registrations").select("*").eq("event_id", event_id).eq("check_in_code", payload.check_in_code).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "INVALID_CODE", "message": "Check-in code not found"})

    reg = result.data
    if reg["checked_in_at"]:
        raise HTTPException(status_code=409, detail={"code": "ALREADY_CHECKED_IN", "message": "Already checked in"})

    updated = await db.table("registrations").update({
        "status": "approved",
        "checked_in_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", reg["id"]).execute()
    return RegistrationResponse(**updated.data[0])


@router.post("/{event_id}/rate/coordinator", response_model=RegistrationResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def coordinator_rate_volunteer(
    request: Request,
    event_id: str,
    payload: CoordinatorRatingRequest,
    db_user: SupabaseUser,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> RegistrationResponse:
    """Coordinator rates a volunteer after the event."""
    _validate_uuid(event_id, "event_id")
    # Verify caller owns the event's organization
    event = await db_admin.table("events").select("organization_id").eq("id", event_id).single().execute()
    if not event.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})

    org = await db_admin.table("organizations").select("owner_id").eq("id", event.data["organization_id"]).single().execute()
    if not org.data or org.data["owner_id"] != user_id:
        raise HTTPException(status_code=403, detail={"code": "NOT_AUTHORIZED", "message": "Only the org owner can rate volunteers"})

    result = await db_admin.table("registrations").update({
        "coordinator_rating": payload.rating,
        "coordinator_feedback": payload.feedback,
        "coordinator_rated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", payload.registration_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "REGISTRATION_NOT_FOUND", "message": "Registration not found"})
    return RegistrationResponse(**result.data[0])


@router.post("/{event_id}/rate/volunteer", response_model=RegistrationResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def volunteer_rate_event(
    request: Request,
    event_id: str,
    payload: VolunteerRatingRequest,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> RegistrationResponse:
    """Volunteer rates an event after attending."""
    _validate_uuid(event_id, "event_id")
    reg = await db.table("registrations").select("*").eq("event_id", event_id).eq("volunteer_id", user_id).single().execute()
    if not reg.data:
        raise HTTPException(status_code=404, detail={"code": "REGISTRATION_NOT_FOUND", "message": "You are not registered for this event"})

    if reg.data["status"] not in ("approved",):
        raise HTTPException(status_code=409, detail={"code": "NOT_ATTENDED", "message": "You can only rate events you attended"})

    if reg.data.get("volunteer_rated_at"):
        raise HTTPException(status_code=409, detail={"code": "ALREADY_RATED", "message": "You have already rated this event"})

    result = await db.table("registrations").update({
        "volunteer_rating": payload.rating,
        "volunteer_feedback": payload.feedback,
        "volunteer_rated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", reg.data["id"]).execute()

    return RegistrationResponse(**result.data[0])


@router.get("/{event_id}/registrations", response_model=list[RegistrationResponse])
@limiter.limit(RATE_DISCOVERY)
async def list_registrations(
    request: Request,
    event_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> list[RegistrationResponse]:
    """List registrations for an event — org owner only."""
    _validate_uuid(event_id, "event_id")
    # SECURITY: Verify requesting user owns the event's organization
    event_result = await db_admin.table("events").select("organization_id").eq("id", event_id).single().execute()
    if not event_result.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})

    org_result = await db_admin.table("organizations").select("owner_id").eq("id", event_result.data["organization_id"]).single().execute()
    if not org_result.data or org_result.data["owner_id"] != str(user_id):
        raise HTTPException(status_code=403, detail={"code": "NOT_ORG_OWNER", "message": "Only the organization owner can view registrations"})

    result = await db_admin.table("registrations").select("*").eq("event_id", event_id).execute()
    return [RegistrationResponse(**row) for row in (result.data or [])]


@router.get("/{event_id}/attendees", response_model=list[EventAttendeeRow])
@limiter.limit(RATE_DISCOVERY)
async def list_attendees(
    request: Request,
    event_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> list[EventAttendeeRow]:
    """Enriched attendee list — org owner only. Joins profiles + AURA scores."""
    _validate_uuid(event_id, "event_id")

    event_result = await db_admin.table("events").select("organization_id").eq("id", event_id).single().execute()
    if not event_result.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})

    org_result = await db_admin.table("organizations").select("owner_id").eq("id", event_result.data["organization_id"]).single().execute()
    if not org_result.data or org_result.data["owner_id"] != str(user_id):
        raise HTTPException(status_code=403, detail={"code": "NOT_ORG_OWNER", "message": "Only the organization owner can view attendees"})

    regs = await db_admin.table("registrations").select("id, volunteer_id, status, registered_at, checked_in_at").eq("event_id", event_id).order("registered_at", desc=True).execute()
    if not regs.data:
        return []

    volunteer_ids = [r["volunteer_id"] for r in regs.data]

    profiles_result = await db_admin.table("profiles").select("id, display_name, username").in_("id", volunteer_ids).execute()
    aura_result = await db_admin.table("aura_scores").select("volunteer_id, total_score, badge_tier").in_("volunteer_id", volunteer_ids).execute()

    profile_map = {p["id"]: p for p in (profiles_result.data or [])}
    aura_map = {a["volunteer_id"]: a for a in (aura_result.data or [])}

    rows: list[EventAttendeeRow] = []
    for reg in regs.data:
        vid = reg["volunteer_id"]
        p = profile_map.get(vid, {})
        a = aura_map.get(vid, {})
        rows.append(EventAttendeeRow(
            registration_id=reg["id"],
            volunteer_id=vid,
            status=reg["status"],
            registered_at=reg["registered_at"],
            checked_in_at=reg.get("checked_in_at"),
            display_name=p.get("display_name"),
            username=p.get("username"),
            total_score=a.get("total_score"),
            badge_tier=a.get("badge_tier"),
        ))
    return rows


@router.get("/my/registrations", response_model=list[RegistrationResponse])
async def my_registrations(
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> list[RegistrationResponse]:
    """List the current volunteer's registrations."""
    result = await db.table("registrations").select("*").eq("volunteer_id", user_id).order("registered_at", desc=True).execute()
    return [RegistrationResponse(**row) for row in (result.data or [])]


def _validate_uuid(value: str, field_name: str) -> None:
    """Validate UUID format to prevent injection."""
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_UUID", "message": f"Invalid {field_name} format"},
        )
