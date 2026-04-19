"""Unit tests for app/routers/eventshift.py.

Covers:
1. Router registration (prefix, tags, routes)
2. Helper _validate_uuid
3. Pydantic schemas (construction + validation)
4. Endpoint error paths: 403 NO_ORGANIZATION, 403 MODULE_NOT_ACTIVATED,
   404 EVENT_NOT_FOUND, 404 DEPARTMENT_NOT_FOUND, 404 AREA_NOT_FOUND,
   404 UNIT_NOT_FOUND, 422 INVALID_UUID, 422 INVALID_TIMES
5. Happy paths: list events, create event, get event, list departments
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.routers.eventshift import _validate_uuid, router
from app.schemas.eventshift import (
    AreaCreate,
    DepartmentCreate,
    EventShiftEventCreate,
    UnitAssignmentCreate,
    UnitCreate,
    UnitMetricCreate,
)

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = "aaaaaaaa-0001-0000-0000-000000000001"
ORG_ID = "bbbbbbbb-0001-0000-0000-000000000001"
EVENT_ID = str(uuid.uuid4())
DEPT_ID = str(uuid.uuid4())
AREA_ID = str(uuid.uuid4())
UNIT_ID = str(uuid.uuid4())

NOW = datetime.now(UTC)
NOW_ISO = NOW.isoformat()
FUTURE_ISO = (NOW + timedelta(days=7)).isoformat()
LATER_ISO = (NOW + timedelta(days=8)).isoformat()

EVENT_ROW = {
    "id": EVENT_ID,
    "org_id": ORG_ID,
    "slug": "test-event",
    "name": "Test Event",
    "description": None,
    "start_at": FUTURE_ISO,
    "end_at": LATER_ISO,
    "timezone": "Asia/Baku",
    "location": None,
    "metadata": None,
    "status": "planning",
    "created_at": NOW_ISO,
    "updated_at": NOW_ISO,
}

DEPT_ROW = {
    "id": DEPT_ID,
    "org_id": ORG_ID,
    "event_id": EVENT_ID,
    "name": "Operations",
    "description": None,
    "color_hex": None,
    "lead_user_id": None,
    "sort_order": 0,
    "metadata": None,
    "created_at": NOW_ISO,
    "updated_at": NOW_ISO,
}

AREA_ROW = {
    "id": AREA_ID,
    "org_id": ORG_ID,
    "department_id": DEPT_ID,
    "name": "Gate A",
    "description": None,
    "location": None,
    "metadata": None,
    "coordinator_user_id": None,
    "created_at": NOW_ISO,
    "updated_at": NOW_ISO,
}

UNIT_ROW = {
    "id": UNIT_ID,
    "org_id": ORG_ID,
    "area_id": AREA_ID,
    "name": "Morning Shift",
    "description": None,
    "shift_start": FUTURE_ISO,
    "shift_end": LATER_ISO,
    "required_headcount": 2,
    "required_skills": [],
    "status": "open",
    "created_at": NOW_ISO,
    "updated_at": NOW_ISO,
}


# ── Mock helpers ──────────────────────────────────────────────────────────────


def _admin_override(db):
    async def _dep():
        yield db

    return _dep


def _uid_override(uid: str):
    async def _dep():
        return uid

    return _dep


def _make_chain_mock(data=None, list_data=None) -> MagicMock:
    """Generic fluent-chain mock. execute() returns data."""
    t = MagicMock()
    for method in (
        "select",
        "eq",
        "neq",
        "in_",
        "insert",
        "update",
        "delete",
        "order",
        "limit",
        "range",
        "single",
        "maybe_single",
        "rpc",
    ):
        getattr(t, method).return_value = t
    result_data = list_data if list_data is not None else data
    t.execute = AsyncMock(return_value=MagicMock(data=result_data))
    return t


def _make_org_gate_db(
    *,
    has_org: bool = True,
    module_active: bool = True,
    event_data=None,
    dept_data=None,
    area_data=None,
    unit_data=None,
    insert_data=None,
    list_data=None,
) -> MagicMock:
    """Build a MagicMock db whose call sequence matches _org_gate + one endpoint."""

    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)
        for method in (
            "select",
            "eq",
            "neq",
            "in_",
            "insert",
            "update",
            "delete",
            "order",
            "limit",
            "range",
            "single",
            "maybe_single",
        ):
            getattr(t, method).return_value = t

        if table_name == "organizations":

            async def _exec(*_a, **_kw):
                return MagicMock(data=[{"id": ORG_ID}] if has_org else [])

            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "eventshift_events":

            async def _exec(*_a, **_kw):
                if insert_data is not None:
                    return MagicMock(data=[insert_data])
                if list_data is not None:
                    return MagicMock(data=list_data)
                return MagicMock(data=event_data)

            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "eventshift_departments":

            async def _exec(*_a, **_kw):
                n = call_counts["eventshift_departments"]
                call_counts["eventshift_departments"] += 1
                if insert_data is not None and n > 0:
                    return MagicMock(data=[insert_data])
                if list_data is not None and n > 0:
                    return MagicMock(data=list_data)
                return MagicMock(data=dept_data)

            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "eventshift_areas":

            async def _exec(*_a, **_kw):
                return MagicMock(data=area_data)

            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "eventshift_units":

            async def _exec(*_a, **_kw):
                return MagicMock(data=unit_data)

            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "character_events":
            t.execute = AsyncMock(return_value=MagicMock(data=[]))

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=[True] if module_active else []))

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    db.rpc = MagicMock(return_value=rpc_mock)
    return db


# ── 1. Router registration ─────────────────────────────────────────────────────


def test_router_prefix():
    assert router.prefix == "/eventshift"


def test_router_tags():
    assert "EventShift" in router.tags


def test_router_not_empty():
    assert len(router.routes) > 0


def test_router_has_events_route():
    paths = {r.path for r in router.routes}
    assert "/eventshift/events" in paths


def test_router_has_event_detail_route():
    paths = {r.path for r in router.routes}
    assert "/eventshift/events/{event_id}" in paths


def test_router_has_departments_route():
    paths = {r.path for r in router.routes}
    assert "/eventshift/events/{event_id}/departments" in paths


def test_router_has_areas_route():
    paths = {r.path for r in router.routes}
    assert "/eventshift/departments/{department_id}/areas" in paths


def test_router_has_units_route():
    paths = {r.path for r in router.routes}
    assert "/eventshift/areas/{area_id}/units" in paths


# ── 2. _validate_uuid ─────────────────────────────────────────────────────────


def test_validate_uuid_valid():
    _validate_uuid(str(uuid.uuid4()), "test_field")  # must not raise


def test_validate_uuid_invalid_raises_422():
    with pytest.raises(HTTPException) as exc_info:
        _validate_uuid("not-a-uuid", "event_id")
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "INVALID_UUID"


def test_validate_uuid_empty_string_raises_422():
    with pytest.raises(HTTPException) as exc_info:
        _validate_uuid("", "event_id")
    assert exc_info.value.status_code == 422


def test_validate_uuid_integer_string_raises_422():
    with pytest.raises(HTTPException) as exc_info:
        _validate_uuid("12345", "event_id")
    assert exc_info.value.status_code == 422


# ── 3. Pydantic schemas ───────────────────────────────────────────────────────


def test_event_create_valid():
    ev = EventShiftEventCreate(
        slug="my-event",
        name="My Event",
        start_at=NOW + timedelta(days=1),
        end_at=NOW + timedelta(days=2),
    )
    assert ev.slug == "my-event"
    assert ev.status == "planning"


def test_event_create_slug_normalized():
    ev = EventShiftEventCreate(
        slug="  UPPER-CASE  ",
        name="X",
        start_at=NOW + timedelta(days=1),
        end_at=NOW + timedelta(days=2),
    )
    assert ev.slug == "upper-case"


def test_event_create_invalid_status():
    with pytest.raises(ValidationError):
        EventShiftEventCreate(
            slug="x",
            name="X",
            start_at=NOW + timedelta(days=1),
            end_at=NOW + timedelta(days=2),
            status="invalid",
        )


def test_department_create_valid():
    dept = DepartmentCreate(name="Operations")
    assert dept.name == "Operations"
    assert dept.sort_order == 0


def test_area_create_valid():
    area = AreaCreate(name="Gate A")
    assert area.name == "Gate A"
    assert area.location is None


def test_unit_create_valid():
    unit = UnitCreate(
        name="Morning Shift",
        shift_start=NOW + timedelta(hours=1),
        shift_end=NOW + timedelta(hours=9),
    )
    assert unit.required_headcount == 1
    assert unit.status == "open"


def test_unit_create_invalid_status():
    with pytest.raises(ValidationError):
        UnitCreate(
            name="X",
            shift_start=NOW,
            shift_end=NOW + timedelta(hours=8),
            status="invalid",
        )


def test_unit_create_headcount_out_of_range():
    with pytest.raises(ValidationError):
        UnitCreate(
            name="X",
            shift_start=NOW,
            shift_end=NOW + timedelta(hours=8),
            required_headcount=0,
        )


def test_unit_assignment_create_valid():
    a = UnitAssignmentCreate(user_id=USER_ID, role="staff")
    assert a.role == "staff"


def test_unit_assignment_create_invalid_role():
    with pytest.raises(ValidationError):
        UnitAssignmentCreate(user_id=USER_ID, role="god")


def test_unit_metric_create_valid():
    m = UnitMetricCreate(metric_type="attendance", value=42.0)
    assert m.metric_type == "attendance"


def test_unit_metric_create_invalid_type():
    with pytest.raises(ValidationError):
        UnitMetricCreate(metric_type="unknown_metric")


# ── 4. 403 NO_ORGANIZATION ────────────────────────────────────────────────────


async def test_list_events_no_org_403():
    db = _make_org_gate_db(has_org=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/eventshift/events", headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NO_ORGANIZATION"


async def test_create_event_no_org_403():
    db = _make_org_gate_db(has_org=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/eventshift/events",
                json={
                    "slug": "e",
                    "name": "E",
                    "start_at": FUTURE_ISO,
                    "end_at": LATER_ISO,
                },
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NO_ORGANIZATION"


# ── 5. 403 MODULE_NOT_ACTIVATED ───────────────────────────────────────────────


async def test_list_events_module_not_activated_403():
    db = _make_org_gate_db(has_org=True, module_active=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/eventshift/events", headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "MODULE_NOT_ACTIVATED"


async def test_create_event_module_not_activated_403():
    db = _make_org_gate_db(has_org=True, module_active=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/eventshift/events",
                json={"slug": "e", "name": "E", "start_at": FUTURE_ISO, "end_at": LATER_ISO},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "MODULE_NOT_ACTIVATED"


# ── 6. GET /eventshift/events — happy path ────────────────────────────────────


async def test_list_events_returns_list():
    db = _make_org_gate_db(
        has_org=True,
        module_active=True,
        event_data=None,  # first call returns org
        list_data=[EVENT_ROW],
    )
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/eventshift/events", headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body[0]["slug"] == "test-event"


async def test_list_events_empty():
    db = _make_org_gate_db(has_org=True, module_active=True, list_data=[])
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/eventshift/events", headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == []


# ── 7. POST /eventshift/events — happy path ───────────────────────────────────


async def test_create_event_success():
    db = _make_org_gate_db(
        has_org=True,
        module_active=True,
        insert_data=EVENT_ROW,
    )
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/eventshift/events",
                json={
                    "slug": "test-event",
                    "name": "Test Event",
                    "start_at": FUTURE_ISO,
                    "end_at": LATER_ISO,
                },
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 201
    assert resp.json()["slug"] == "test-event"


async def test_create_event_invalid_times_422():
    db = _make_org_gate_db(has_org=True, module_active=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/eventshift/events",
                json={
                    "slug": "bad-times",
                    "name": "Bad Times",
                    "start_at": LATER_ISO,  # end before start
                    "end_at": FUTURE_ISO,
                },
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_TIMES"


# ── 8. GET /eventshift/events/{event_id} — happy path + 404 ──────────────────


async def test_get_event_success():
    db = _make_org_gate_db(has_org=True, module_active=True, event_data=EVENT_ROW)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/eventshift/events/{EVENT_ID}",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["id"] == EVENT_ID


async def test_get_event_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, event_data=None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/eventshift/events/{EVENT_ID}",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "EVENT_NOT_FOUND"


async def test_get_event_invalid_uuid_422():
    db = _make_org_gate_db(has_org=True, module_active=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/eventshift/events/not-a-uuid",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_UUID"


# ── 9. DELETE /eventshift/events/{event_id} ───────────────────────────────────


async def test_cancel_event_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, event_data=None)
    # cancel_event calls update().eq().eq().execute() and checks result.data
    # We need it to return empty data on the update call too
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.delete(
                f"/api/eventshift/events/{EVENT_ID}",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "EVENT_NOT_FOUND"


async def test_cancel_event_invalid_uuid_422():
    db = _make_org_gate_db(has_org=True, module_active=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.delete(
                "/api/eventshift/events/bad-id",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_UUID"


# ── 10. GET /eventshift/events/{event_id}/departments ─────────────────────────


async def test_list_departments_event_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, event_data=None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/eventshift/events/{EVENT_ID}/departments",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "EVENT_NOT_FOUND"


async def test_list_departments_invalid_uuid_422():
    db = _make_org_gate_db(has_org=True, module_active=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/eventshift/events/not-a-uuid/departments",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_UUID"


async def test_list_departments_success():
    """event exists + departments exist → 200 list."""
    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)
        for method in (
            "select",
            "eq",
            "order",
            "single",
            "maybe_single",
            "insert",
            "update",
            "delete",
            "limit",
            "range",
        ):
            getattr(t, method).return_value = t

        if table_name == "organizations":
            t.execute = AsyncMock(return_value=MagicMock(data=[{"id": ORG_ID}]))
        elif table_name == "eventshift_events":
            t.execute = AsyncMock(return_value=MagicMock(data=EVENT_ROW))
        elif table_name == "eventshift_departments":

            async def _exec(*_a, **_kw):
                call_counts["eventshift_departments"] += 1
                return MagicMock(data=[DEPT_ROW])

            t.execute = AsyncMock(side_effect=_exec)
        elif table_name == "character_events":
            t.execute = AsyncMock(return_value=MagicMock(data=[]))
        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))
        return t

    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=[True]))
    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    db.rpc = MagicMock(return_value=rpc_mock)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/eventshift/events/{EVENT_ID}/departments",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body[0]["name"] == "Operations"


# ── 11. Department 404 from update endpoint ───────────────────────────────────


async def test_update_department_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, dept_data=None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.put(
                f"/api/eventshift/departments/{DEPT_ID}",
                json={"name": "Updated"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "DEPARTMENT_NOT_FOUND"


async def test_update_department_invalid_uuid_422():
    db = _make_org_gate_db(has_org=True, module_active=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.put(
                "/api/eventshift/departments/bad-id",
                json={"name": "X"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_UUID"


# ── 12. Area 404 ──────────────────────────────────────────────────────────────


async def test_list_areas_department_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, dept_data=None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/eventshift/departments/{DEPT_ID}/areas",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "DEPARTMENT_NOT_FOUND"


async def test_update_area_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, area_data=None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.put(
                f"/api/eventshift/areas/{AREA_ID}",
                json={"name": "Updated"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "AREA_NOT_FOUND"


async def test_update_area_invalid_uuid_422():
    db = _make_org_gate_db(has_org=True, module_active=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.put(
                "/api/eventshift/areas/bad-id",
                json={"name": "X"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_UUID"


# ── 13. Unit 404 ──────────────────────────────────────────────────────────────


async def test_list_units_area_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, area_data=None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/eventshift/areas/{AREA_ID}/units",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "AREA_NOT_FOUND"


async def test_update_unit_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, unit_data=None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.put(
                f"/api/eventshift/units/{UNIT_ID}",
                json={"name": "Updated"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "UNIT_NOT_FOUND"


async def test_update_unit_invalid_uuid_422():
    db = _make_org_gate_db(has_org=True, module_active=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.put(
                "/api/eventshift/units/bad-id",
                json={"name": "X"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_UUID"


# ── 14. Assignments ───────────────────────────────────────────────────────────


async def test_list_assignments_unit_not_found_404():
    db = _make_org_gate_db(has_org=True, module_active=True, unit_data=None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/eventshift/units/{UNIT_ID}/assignments",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "UNIT_NOT_FOUND"


async def test_create_assignment_invalid_unit_uuid_422():
    db = _make_org_gate_db(has_org=True, module_active=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/eventshift/units/bad-uuid/assignments",
                json={"user_id": USER_ID},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_UUID"


# ── 15. Debug endpoint ────────────────────────────────────────────────────────


async def test_debug_activation_state_no_org_403():
    db = _make_org_gate_db(has_org=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/eventshift/debug/activation-state",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NO_ORGANIZATION"
