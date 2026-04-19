"""EventShift — universal event shift operations (first VOLAURA module).

Domain: Event → Department → Area → Unit → People + Metrics (MODULES.md §10).
Multi-tenant from day 1: org_id injected on every row from the caller's
owned organization. Activation-gated via `is_module_active_for_org` RPC.

Every mutation emits a character_events row so the ecosystem bus stays alive
(MODULES.md §4 rule 4). org_id lives in the payload (character_events has
no org_id column in the MVP schema; Path 5 adds JWT-claim tenancy later).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from loguru import logger

from app.deps import CurrentUserId, SupabaseAdmin
from app.middleware.rate_limit import RATE_DEFAULT, RATE_DISCOVERY, RATE_PROFILE_WRITE, limiter
from app.schemas.eventshift import (
    AreaCreate,
    AreaResponse,
    AreaUpdate,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    EventShiftEventCreate,
    EventShiftEventResponse,
    EventShiftEventUpdate,
    UnitAssignmentCreate,
    UnitAssignmentResponse,
    UnitAssignmentUpdate,
    UnitCreate,
    UnitMetricCreate,
    UnitMetricResponse,
    UnitResponse,
    UnitUpdate,
)

router = APIRouter(prefix="/eventshift", tags=["EventShift"])

MODULE_SLUG = "eventshift"
SOURCE_PRODUCT = "eventshift"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _validate_uuid(value: str, field_name: str) -> None:
    """Validate UUID format to prevent injection."""
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_UUID", "message": f"Invalid {field_name} format"},
        ) from exc


async def _resolve_org_id(db_admin: Any, user_id: str) -> str:
    """Caller must own an organization. Returns its id."""
    org = await db_admin.table("organizations").select("id").eq("owner_id", user_id).execute()
    if not org.data:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "NO_ORGANIZATION",
                "message": "You must own an organization to use EventShift",
            },
        )
    return org.data[0]["id"]


async def _assert_module_active(db_admin: Any, org_id: str) -> None:
    """Gate: 403 MODULE_NOT_ACTIVATED unless org has an enabled activation row."""
    result = await db_admin.rpc(
        "is_module_active_for_org",
        {"p_org_id": org_id, "p_slug": MODULE_SLUG},
    ).execute()
    if not result.data:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "MODULE_NOT_ACTIVATED",
                "message": "EventShift is not activated for this organization",
            },
        )


async def _org_gate(db_admin: SupabaseAdmin, user_id: CurrentUserId) -> str:
    """Dependency: returns org_id after ownership + activation checks."""
    org_id = await _resolve_org_id(db_admin, user_id)
    await _assert_module_active(db_admin, org_id)
    return org_id


OrgId = Annotated[str, Depends(_org_gate)]


async def _emit_event(
    db_admin: Any,
    *,
    user_id: str,
    org_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    """Best-effort character_events emission. Never blocks the response."""
    try:
        enriched = {"org_id": org_id, **payload}
        await (
            db_admin.table("character_events")
            .insert(
                {
                    "user_id": user_id,
                    "event_type": event_type,
                    "payload": enriched,
                    "source_product": SOURCE_PRODUCT,
                }
            )
            .execute()
        )
    except Exception as exc:  # noqa: BLE001 — event bus is best-effort
        logger.warning(
            "character_events emit failed (non-blocking)",
            event_type=event_type,
            error=str(exc),
        )


async def _assert_event_in_org(db_admin: Any, event_id: str, org_id: str) -> dict[str, Any]:
    row = (
        await db_admin.table("eventshift_events").select("*").eq("id", event_id).eq("org_id", org_id).single().execute()
    )
    if not row.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"},
        )
    return row.data


async def _assert_department_in_org(db_admin: Any, department_id: str, org_id: str) -> dict[str, Any]:
    row = (
        await db_admin.table("eventshift_departments")
        .select("*")
        .eq("id", department_id)
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not row.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "DEPARTMENT_NOT_FOUND", "message": "Department not found"},
        )
    return row.data


async def _assert_area_in_org(db_admin: Any, area_id: str, org_id: str) -> dict[str, Any]:
    row = await db_admin.table("eventshift_areas").select("*").eq("id", area_id).eq("org_id", org_id).single().execute()
    if not row.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "AREA_NOT_FOUND", "message": "Area not found"},
        )
    return row.data


async def _assert_unit_in_org(db_admin: Any, unit_id: str, org_id: str) -> dict[str, Any]:
    row = await db_admin.table("eventshift_units").select("*").eq("id", unit_id).eq("org_id", org_id).single().execute()
    if not row.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "UNIT_NOT_FOUND", "message": "Unit not found"},
        )
    return row.data


# ── Events ────────────────────────────────────────────────────────────────────


@router.get("/events", response_model=list[EventShiftEventResponse])
@limiter.limit(RATE_DISCOVERY)
async def list_events(
    request: Request,
    db_admin: SupabaseAdmin,
    org_id: OrgId,
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> list[EventShiftEventResponse]:
    """List events owned by the caller's organization."""
    q = db_admin.table("eventshift_events").select("*").eq("org_id", org_id)
    if status:
        q = q.eq("status", status)
    result = await q.order("start_at", desc=True).range(offset, offset + limit - 1).execute()
    return [EventShiftEventResponse(**row) for row in (result.data or [])]


@router.post("/events", response_model=EventShiftEventResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_event(
    request: Request,
    payload: EventShiftEventCreate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> EventShiftEventResponse:
    """Create an event (org owner only)."""
    if payload.end_at <= payload.start_at:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_TIMES", "message": "end_at must be after start_at"},
        )
    row = {"org_id": org_id, **payload.model_dump(mode="json")}
    result = await db_admin.table("eventshift_events").insert(row).execute()
    if not result.data:
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to create event"},
        )
    event = result.data[0]
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_event_created",
        payload={"event_id": event["id"], "slug": event["slug"], "status": event["status"]},
    )
    logger.info("eventshift event created", user_id=user_id, event_id=event["id"])
    return EventShiftEventResponse(**event)


@router.get("/events/{event_id}", response_model=EventShiftEventResponse)
@limiter.limit(RATE_DISCOVERY)
async def get_event(
    request: Request,
    event_id: str,
    db_admin: SupabaseAdmin,
    org_id: OrgId,
) -> EventShiftEventResponse:
    """Retrieve a single event by ID within the caller's organization."""
    _validate_uuid(event_id, "event_id")
    event = await _assert_event_in_org(db_admin, event_id, org_id)
    return EventShiftEventResponse(**event)


@router.put("/events/{event_id}", response_model=EventShiftEventResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_event(
    request: Request,
    event_id: str,
    payload: EventShiftEventUpdate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> EventShiftEventResponse:
    """Update mutable fields of an event (org owner only)."""
    _validate_uuid(event_id, "event_id")
    await _assert_event_in_org(db_admin, event_id, org_id)

    update_data = payload.model_dump(mode="json", exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail={"code": "NO_FIELDS", "message": "No fields to update"})

    if "start_at" in update_data or "end_at" in update_data:
        merged = {**(await _assert_event_in_org(db_admin, event_id, org_id)), **update_data}
        if datetime.fromisoformat(str(merged["end_at"]).replace("Z", "+00:00")) <= datetime.fromisoformat(
            str(merged["start_at"]).replace("Z", "+00:00")
        ):
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_TIMES", "message": "end_at must be after start_at"},
            )

    result = (
        await db_admin.table("eventshift_events").update(update_data).eq("id", event_id).eq("org_id", org_id).execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"},
        )
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_event_updated",
        payload={"event_id": event_id, "fields": list(update_data.keys())},
    )
    return EventShiftEventResponse(**result.data[0])


@router.delete("/events/{event_id}", status_code=204)
@limiter.limit(RATE_PROFILE_WRITE)
async def cancel_event(
    request: Request,
    event_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> None:
    """Soft-cancel an event (set status='cancelled')."""
    _validate_uuid(event_id, "event_id")
    result = (
        await db_admin.table("eventshift_events")
        .update({"status": "cancelled"})
        .eq("id", event_id)
        .eq("org_id", org_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"},
        )
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_event_cancelled",
        payload={"event_id": event_id},
    )
    logger.info("eventshift event cancelled", user_id=user_id, event_id=event_id)


# ── Departments ───────────────────────────────────────────────────────────────


@router.get("/events/{event_id}/departments", response_model=list[DepartmentResponse])
@limiter.limit(RATE_DISCOVERY)
async def list_departments(
    request: Request,
    event_id: str,
    db_admin: SupabaseAdmin,
    org_id: OrgId,
) -> list[DepartmentResponse]:
    """List all departments belonging to an event, ordered by sort_order."""
    _validate_uuid(event_id, "event_id")
    await _assert_event_in_org(db_admin, event_id, org_id)
    result = (
        await db_admin.table("eventshift_departments")
        .select("*")
        .eq("event_id", event_id)
        .eq("org_id", org_id)
        .order("sort_order")
        .execute()
    )
    return [DepartmentResponse(**row) for row in (result.data or [])]


@router.post("/events/{event_id}/departments", response_model=DepartmentResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_department(
    request: Request,
    event_id: str,
    payload: DepartmentCreate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> DepartmentResponse:
    """Create a new department under an event (org owner only)."""
    _validate_uuid(event_id, "event_id")
    await _assert_event_in_org(db_admin, event_id, org_id)
    row = {"org_id": org_id, "event_id": event_id, **payload.model_dump(mode="json")}
    result = await db_admin.table("eventshift_departments").insert(row).execute()
    if not result.data:
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to create department"},
        )
    dept = result.data[0]
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_department_created",
        payload={"event_id": event_id, "department_id": dept["id"], "name": dept["name"]},
    )
    return DepartmentResponse(**dept)


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_department(
    request: Request,
    department_id: str,
    payload: DepartmentUpdate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> DepartmentResponse:
    """Update mutable fields of a department (org owner only)."""
    _validate_uuid(department_id, "department_id")
    await _assert_department_in_org(db_admin, department_id, org_id)
    update_data = payload.model_dump(mode="json", exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail={"code": "NO_FIELDS", "message": "No fields to update"})
    result = (
        await db_admin.table("eventshift_departments")
        .update(update_data)
        .eq("id", department_id)
        .eq("org_id", org_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "DEPARTMENT_NOT_FOUND", "message": "Department not found"},
        )
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_department_updated",
        payload={"department_id": department_id, "fields": list(update_data.keys())},
    )
    return DepartmentResponse(**result.data[0])


@router.get("/departments/{department_id}/blueprint")
@limiter.limit(RATE_DISCOVERY)
async def get_department_blueprint(
    request: Request,
    department_id: str,
    db_admin: SupabaseAdmin,
    org_id: OrgId,
    section: str | None = Query(
        None, description="Filter: roles, sops, policies, faq, metrics, training, competencies"
    ),
) -> dict[str, Any]:
    """Return the operational blueprint (metadata) for a department.

    The WUF13 GSE seed stores roles, SOPs, policies, FAQ, metrics, training,
    and competencies inside department.metadata JSONB. This endpoint surfaces
    that structure to clients, optionally filtered by section.
    """
    _validate_uuid(department_id, "department_id")
    dept = await _assert_department_in_org(db_admin, department_id, org_id)
    meta = dept.get("metadata") or {}

    if section:
        allowed = {
            "roles",
            "sops",
            "policies",
            "faq",
            "metrics",
            "training",
            "competencies",
            "requirements",
            "kpis",
            "mission",
        }
        if section not in allowed:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_SECTION", "message": f"section must be one of {sorted(allowed)}"},
            )
        return {"department_id": department_id, "section": section, "data": meta.get(section)}

    return {"department_id": department_id, "blueprint": meta}


# ── Areas ─────────────────────────────────────────────────────────────────────


@router.get("/departments/{department_id}/areas", response_model=list[AreaResponse])
@limiter.limit(RATE_DISCOVERY)
async def list_areas(
    request: Request,
    department_id: str,
    db_admin: SupabaseAdmin,
    org_id: OrgId,
) -> list[AreaResponse]:
    """List all areas within a department, ordered by creation time."""
    _validate_uuid(department_id, "department_id")
    await _assert_department_in_org(db_admin, department_id, org_id)
    result = (
        await db_admin.table("eventshift_areas")
        .select("*")
        .eq("department_id", department_id)
        .eq("org_id", org_id)
        .order("created_at")
        .execute()
    )
    return [AreaResponse(**row) for row in (result.data or [])]


@router.post("/departments/{department_id}/areas", response_model=AreaResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_area(
    request: Request,
    department_id: str,
    payload: AreaCreate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> AreaResponse:
    """Create a new area under a department (org owner only)."""
    _validate_uuid(department_id, "department_id")
    await _assert_department_in_org(db_admin, department_id, org_id)
    row = {"org_id": org_id, "department_id": department_id, **payload.model_dump(mode="json")}
    result = await db_admin.table("eventshift_areas").insert(row).execute()
    if not result.data:
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to create area"},
        )
    area = result.data[0]
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_area_created",
        payload={"department_id": department_id, "area_id": area["id"], "name": area["name"]},
    )
    return AreaResponse(**area)


@router.put("/areas/{area_id}", response_model=AreaResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_area(
    request: Request,
    area_id: str,
    payload: AreaUpdate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> AreaResponse:
    """Update mutable fields of an area (org owner only)."""
    _validate_uuid(area_id, "area_id")
    await _assert_area_in_org(db_admin, area_id, org_id)
    update_data = payload.model_dump(mode="json", exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail={"code": "NO_FIELDS", "message": "No fields to update"})
    result = (
        await db_admin.table("eventshift_areas").update(update_data).eq("id", area_id).eq("org_id", org_id).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "AREA_NOT_FOUND", "message": "Area not found"})
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_area_updated",
        payload={"area_id": area_id, "fields": list(update_data.keys())},
    )
    return AreaResponse(**result.data[0])


# ── Units ─────────────────────────────────────────────────────────────────────


@router.get("/areas/{area_id}/units", response_model=list[UnitResponse])
@limiter.limit(RATE_DISCOVERY)
async def list_units(
    request: Request,
    area_id: str,
    db_admin: SupabaseAdmin,
    org_id: OrgId,
) -> list[UnitResponse]:
    """List all shift units within an area, ordered by shift start time."""
    _validate_uuid(area_id, "area_id")
    await _assert_area_in_org(db_admin, area_id, org_id)
    result = (
        await db_admin.table("eventshift_units")
        .select("*")
        .eq("area_id", area_id)
        .eq("org_id", org_id)
        .order("shift_start")
        .execute()
    )
    return [UnitResponse(**row) for row in (result.data or [])]


@router.post("/areas/{area_id}/units", response_model=UnitResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_unit(
    request: Request,
    area_id: str,
    payload: UnitCreate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> UnitResponse:
    """Create a new shift unit under an area (org owner only)."""
    _validate_uuid(area_id, "area_id")
    await _assert_area_in_org(db_admin, area_id, org_id)
    if payload.shift_end <= payload.shift_start:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_TIMES", "message": "shift_end must be after shift_start"},
        )
    row = {"org_id": org_id, "area_id": area_id, **payload.model_dump(mode="json")}
    result = await db_admin.table("eventshift_units").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create unit"})
    unit = result.data[0]
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_unit_created",
        payload={"area_id": area_id, "unit_id": unit["id"], "name": unit["name"]},
    )
    return UnitResponse(**unit)


@router.put("/units/{unit_id}", response_model=UnitResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_unit(
    request: Request,
    unit_id: str,
    payload: UnitUpdate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> UnitResponse:
    """Update mutable fields of a shift unit (org owner only)."""
    _validate_uuid(unit_id, "unit_id")
    await _assert_unit_in_org(db_admin, unit_id, org_id)
    update_data = payload.model_dump(mode="json", exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail={"code": "NO_FIELDS", "message": "No fields to update"})
    result = (
        await db_admin.table("eventshift_units").update(update_data).eq("id", unit_id).eq("org_id", org_id).execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "UNIT_NOT_FOUND", "message": "Unit not found"})
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_unit_updated",
        payload={"unit_id": unit_id, "fields": list(update_data.keys())},
    )
    return UnitResponse(**result.data[0])


# ── Unit assignments ──────────────────────────────────────────────────────────


@router.get("/units/{unit_id}/assignments", response_model=list[UnitAssignmentResponse])
@limiter.limit(RATE_DISCOVERY)
async def list_assignments(
    request: Request,
    unit_id: str,
    db_admin: SupabaseAdmin,
    org_id: OrgId,
) -> list[UnitAssignmentResponse]:
    """List all volunteer assignments for a unit, ordered by assignment time."""
    _validate_uuid(unit_id, "unit_id")
    await _assert_unit_in_org(db_admin, unit_id, org_id)
    result = (
        await db_admin.table("eventshift_unit_assignments")
        .select("*")
        .eq("unit_id", unit_id)
        .eq("org_id", org_id)
        .order("assigned_at")
        .execute()
    )
    return [UnitAssignmentResponse(**row) for row in (result.data or [])]


@router.post(
    "/units/{unit_id}/assignments",
    response_model=UnitAssignmentResponse,
    status_code=201,
)
@limiter.limit(RATE_PROFILE_WRITE)
async def create_assignment(
    request: Request,
    unit_id: str,
    payload: UnitAssignmentCreate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> UnitAssignmentResponse:
    """Assign a volunteer to a unit; returns 409 if already assigned."""
    _validate_uuid(unit_id, "unit_id")
    _validate_uuid(payload.user_id, "user_id")
    await _assert_unit_in_org(db_admin, unit_id, org_id)
    row = {
        "org_id": org_id,
        "unit_id": unit_id,
        **payload.model_dump(mode="json"),
    }
    try:
        result = await db_admin.table("eventshift_unit_assignments").insert(row).execute()
    except Exception as exc:  # duplicate (unit_id, user_id)
        logger.warning("assignment insert failed", error=str(exc))
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ALREADY_ASSIGNED",
                "message": "This user is already assigned to this unit",
            },
        ) from exc
    if not result.data:
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to assign user"},
        )
    assignment = result.data[0]
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_assignment_created",
        payload={
            "unit_id": unit_id,
            "assignment_id": assignment["id"],
            "assigned_user_id": payload.user_id,
            "role": assignment["role"],
        },
    )
    return UnitAssignmentResponse(**assignment)


@router.put("/assignments/{assignment_id}", response_model=UnitAssignmentResponse)
@limiter.limit(RATE_PROFILE_WRITE)
async def update_assignment(
    request: Request,
    assignment_id: str,
    payload: UnitAssignmentUpdate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> UnitAssignmentResponse:
    """Update role or status of a volunteer assignment (org owner only)."""
    _validate_uuid(assignment_id, "assignment_id")
    update_data = payload.model_dump(mode="json", exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=422, detail={"code": "NO_FIELDS", "message": "No fields to update"})
    result = (
        await db_admin.table("eventshift_unit_assignments")
        .update(update_data)
        .eq("id", assignment_id)
        .eq("org_id", org_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "Assignment not found"},
        )
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type="eventshift_assignment_updated",
        payload={"assignment_id": assignment_id, "fields": list(update_data.keys())},
    )
    return UnitAssignmentResponse(**result.data[0])


# ── Unit metrics ──────────────────────────────────────────────────────────────


@router.get("/units/{unit_id}/metrics", response_model=list[UnitMetricResponse])
@limiter.limit(RATE_DISCOVERY)
async def list_metrics(
    request: Request,
    unit_id: str,
    db_admin: SupabaseAdmin,
    org_id: OrgId,
    metric_type: str | None = Query(None),
    limit: int = Query(100, le=500),
) -> list[UnitMetricResponse]:
    """List recorded metrics for a unit, optionally filtered by metric_type."""
    _validate_uuid(unit_id, "unit_id")
    await _assert_unit_in_org(db_admin, unit_id, org_id)
    q = db_admin.table("eventshift_unit_metrics").select("*").eq("unit_id", unit_id).eq("org_id", org_id)
    if metric_type:
        q = q.eq("metric_type", metric_type)
    result = await q.order("recorded_at", desc=True).limit(limit).execute()
    return [UnitMetricResponse(**row) for row in (result.data or [])]


@router.post("/units/{unit_id}/metrics", response_model=UnitMetricResponse, status_code=201)
@limiter.limit(RATE_PROFILE_WRITE)
async def record_metric(
    request: Request,
    unit_id: str,
    payload: UnitMetricCreate,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
    org_id: OrgId,
) -> UnitMetricResponse:
    """Record a performance metric against a unit and emit a character event."""
    _validate_uuid(unit_id, "unit_id")
    await _assert_unit_in_org(db_admin, unit_id, org_id)
    row = {
        "org_id": org_id,
        "unit_id": unit_id,
        "recorded_by": user_id,
        "recorded_at": (payload.recorded_at or datetime.now(UTC)).isoformat(),
        "metric_type": payload.metric_type,
        "value": payload.value,
        "payload": payload.payload,
    }
    result = await db_admin.table("eventshift_unit_metrics").insert(row).execute()
    if not result.data:
        raise HTTPException(
            status_code=500,
            detail={"code": "CREATE_FAILED", "message": "Failed to record metric"},
        )
    metric = result.data[0]
    await _emit_event(
        db_admin,
        user_id=user_id,
        org_id=org_id,
        event_type=f"eventshift_metric_{payload.metric_type}",
        payload={
            "unit_id": unit_id,
            "metric_id": metric["id"],
            "metric_type": payload.metric_type,
            "value": payload.value,
        },
    )
    return UnitMetricResponse(**metric)


@router.get("/debug/activation-state")
@limiter.limit(RATE_DEFAULT)
async def debug_activation_state(
    request: Request,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> dict[str, Any]:
    """Diagnostic: returns org_id + activation status for the caller."""
    org_id = await _resolve_org_id(db_admin, user_id)
    active_result = await db_admin.rpc(
        "is_module_active_for_org",
        {"p_org_id": org_id, "p_slug": MODULE_SLUG},
    ).execute()
    return {
        "org_id": org_id,
        "module_slug": MODULE_SLUG,
        "active": bool(active_result.data),
    }
