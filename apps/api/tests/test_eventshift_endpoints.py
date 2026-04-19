"""HTTP endpoint tests for the EventShift router.

Covers all ~20 CRUD endpoints:
- Events: list, create, get, update, cancel
- Departments: list, create, update, blueprint
- Areas: list, create, update
- Units: list, create, update
- Assignments: list, create, update
- Metrics: list, record
- Debug: activation-state

Gate coverage:
- _org_gate (NO_ORGANIZATION, MODULE_NOT_ACTIVATED)
- UUID validation (422 INVALID_UUID)
- Business logic (time ordering, no-fields, duplicate assignment 409)
- 401 when no auth header
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── Shared IDs ────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())
ORG_ID = str(uuid4())
EVENT_ID = str(uuid4())
DEPT_ID = str(uuid4())
AREA_ID = str(uuid4())
UNIT_ID = str(uuid4())
ASSIGN_ID = str(uuid4())
METRIC_ID = str(uuid4())
OTHER_USER_ID = str(uuid4())

AUTH = {"Authorization": "Bearer test-eventshift"}

# ── Fixture rows ──────────────────────────────────────────────────────────────

NOW = "2026-06-01T10:00:00+00:00"
LATER = "2026-06-01T18:00:00+00:00"

EVENT_ROW = {
    "id": EVENT_ID,
    "org_id": ORG_ID,
    "slug": "wuf13",
    "name": "WUF13 GSE",
    "description": None,
    "start_at": NOW,
    "end_at": LATER,
    "timezone": "Asia/Baku",
    "location": None,
    "metadata": None,
    "status": "planning",
    "created_at": NOW,
    "updated_at": NOW,
}

DEPT_ROW = {
    "id": DEPT_ID,
    "org_id": ORG_ID,
    "event_id": EVENT_ID,
    "name": "Logistics",
    "description": None,
    "color_hex": "#7C5CFC",
    "lead_user_id": None,
    "sort_order": 0,
    "metadata": None,
    "created_at": NOW,
    "updated_at": NOW,
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
    "created_at": NOW,
    "updated_at": NOW,
}

UNIT_ROW = {
    "id": UNIT_ID,
    "org_id": ORG_ID,
    "area_id": AREA_ID,
    "name": "Morning Shift",
    "description": None,
    "shift_start": NOW,
    "shift_end": LATER,
    "required_headcount": 3,
    "required_skills": [],
    "status": "open",
    "created_at": NOW,
    "updated_at": NOW,
}

ASSIGN_ROW = {
    "id": ASSIGN_ID,
    "org_id": ORG_ID,
    "unit_id": UNIT_ID,
    "user_id": OTHER_USER_ID,
    "role": "staff",
    "status": "assigned",
    "notes": None,
    "assigned_at": NOW,
    "updated_at": NOW,
}

METRIC_ROW = {
    "id": METRIC_ID,
    "org_id": ORG_ID,
    "unit_id": UNIT_ID,
    "metric_type": "attendance",
    "value": 5.0,
    "payload": None,
    "recorded_at": NOW,
    "recorded_by": USER_ID,
    "created_at": NOW,
}

# ── Mock helpers ──────────────────────────────────────────────────────────────


def make_chain(data=None, side_effect=None) -> MagicMock:
    """Build a fluent Supabase query chain mock."""
    result = MagicMock()
    result.data = data

    if side_effect:
        execute = AsyncMock(side_effect=side_effect)
    else:
        execute = AsyncMock(return_value=result)

    chain = MagicMock()
    for method in (
        "select",
        "eq",
        "order",
        "limit",
        "range",
        "update",
        "insert",
        "upsert",
        "single",
    ):
        getattr(chain, method).return_value = chain
    chain.execute = execute
    return chain


def make_rpc_chain(data=None) -> MagicMock:
    """RPC chain: db.rpc(...).execute()"""
    result = MagicMock()
    result.data = data
    rpc = MagicMock()
    rpc.execute = AsyncMock(return_value=result)
    return rpc


def make_db(
    tables: dict | None = None,
    rpc_data=None,
) -> MagicMock:
    """Build a db mock with configurable table and rpc responses."""
    db = MagicMock()
    tables = tables or {}

    def dispatch(name: str) -> MagicMock:
        cfg = tables.get(name, {})
        return make_chain(**cfg)

    db.table.side_effect = dispatch
    db.rpc.return_value = make_rpc_chain(data=rpc_data)
    return db


def make_activated_db(
    tables: dict | None = None,
    rpc_data=True,
) -> MagicMock:
    """DB where org lookup succeeds and module is active."""
    base_tables = {
        "organizations": {"data": [{"id": ORG_ID}]},
    }
    if tables:
        base_tables.update(tables)
    return make_db(tables=base_tables, rpc_data=rpc_data)


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def admin_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def user_id_dep(uid: str = USER_ID):
    async def _override():
        return uid

    return _override


# ── Context manager for dependency overrides ──────────────────────────────────


class _DepCtx:
    """Sets dependency_overrides on enter, clears on exit."""

    def __init__(self, db: MagicMock, uid: str = USER_ID):
        self.db = db
        self.uid = uid

    def __enter__(self):
        app.dependency_overrides[get_supabase_admin] = admin_dep(self.db)
        app.dependency_overrides[get_supabase_user] = admin_dep(self.db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(self.uid)
        return self

    def __exit__(self, *_):
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_supabase_user, None)
        app.dependency_overrides.pop(get_current_user_id, None)


# ── Gate helpers (shared patterns) ────────────────────────────────────────────


async def _assert_requires_auth(method: str, path: str) -> None:
    async def _fake_admin():
        yield AsyncMock()

    app.dependency_overrides[get_supabase_admin] = _fake_admin
    try:
        async with make_client() as c:
            r = await getattr(c, method)(path)
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)
    assert r.status_code == 401


async def _assert_no_org_403(method: str, path: str, json: dict | None = None) -> None:
    db = make_db(tables={"organizations": {"data": []}}, rpc_data=True)
    kwargs: dict = {"headers": AUTH}
    if json is not None:
        kwargs["json"] = json
    with _DepCtx(db):
        async with make_client() as c:
            r = await getattr(c, method)(path, **kwargs)
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "NO_ORGANIZATION"


async def _assert_module_inactive_403(method: str, path: str, json: dict | None = None) -> None:
    db = make_db(
        tables={"organizations": {"data": [{"id": ORG_ID}]}},
        rpc_data=False,
    )
    kwargs: dict = {"headers": AUTH}
    if json is not None:
        kwargs["json"] = json
    with _DepCtx(db):
        async with make_client() as c:
            r = await getattr(c, method)(path, **kwargs)
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "MODULE_NOT_ACTIVATED"


# ═══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestListEvents:
    @pytest.mark.asyncio
    async def test_returns_200_empty(self):
        db = make_activated_db(tables={"eventshift_events": {"data": []}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/events", headers=AUTH)
        assert r.status_code == 200
        assert r.json() == []

    @pytest.mark.asyncio
    async def test_returns_event_list(self):
        db = make_activated_db(tables={"eventshift_events": {"data": [EVENT_ROW]}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/events", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["slug"] == "wuf13"

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("get", "/api/eventshift/events")

    @pytest.mark.asyncio
    async def test_no_org_403(self):
        await _assert_no_org_403("get", "/api/eventshift/events")

    @pytest.mark.asyncio
    async def test_module_inactive_403(self):
        await _assert_module_inactive_403("get", "/api/eventshift/events")


class TestCreateEvent:
    VALID_PAYLOAD = {
        "slug": "wuf13",
        "name": "WUF13",
        "start_at": NOW,
        "end_at": LATER,
    }

    @pytest.mark.asyncio
    async def test_creates_event_201(self):
        db = make_activated_db(
            tables={
                "eventshift_events": {"data": [EVENT_ROW]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/eventshift/events", json=self.VALID_PAYLOAD, headers=AUTH)
        assert r.status_code == 201
        assert r.json()["slug"] == "wuf13"

    @pytest.mark.asyncio
    async def test_422_end_before_start(self):
        db = make_activated_db()
        payload = {**self.VALID_PAYLOAD, "start_at": LATER, "end_at": NOW}
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/eventshift/events", json=payload, headers=AUTH)
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_422_invalid_status(self):
        db = make_activated_db()
        payload = {**self.VALID_PAYLOAD, "status": "not_a_status"}
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/eventshift/events", json=payload, headers=AUTH)
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_422_missing_required_fields(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/eventshift/events", json={"slug": "x"}, headers=AUTH)
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_no_org_403(self):
        await _assert_no_org_403("post", "/api/eventshift/events", self.VALID_PAYLOAD)

    @pytest.mark.asyncio
    async def test_module_inactive_403(self):
        await _assert_module_inactive_403("post", "/api/eventshift/events", self.VALID_PAYLOAD)


class TestGetEvent:
    @pytest.mark.asyncio
    async def test_returns_event(self):
        db = make_activated_db(tables={"eventshift_events": {"data": EVENT_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(f"/api/eventshift/events/{EVENT_ID}", headers=AUTH)
        assert r.status_code == 200
        assert r.json()["id"] == EVENT_ID

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        db = make_activated_db(tables={"eventshift_events": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(f"/api/eventshift/events/{EVENT_ID}", headers=AUTH)
        assert r.status_code == 404
        assert r.json()["detail"]["code"] == "EVENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_422_invalid_uuid(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/events/not-a-uuid", headers=AUTH)
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "INVALID_UUID"


class TestUpdateEvent:
    @pytest.mark.asyncio
    async def test_updates_name(self):
        db = make_activated_db(
            tables={
                "eventshift_events": {"data": [{**EVENT_ROW, "name": "Updated"}]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        # _assert_event_in_org is called twice (once to verify, once for time merge)
        # single() chains must return a row; reuse same mock
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/events/{EVENT_ID}",
                    json={"name": "Updated"},
                    headers=AUTH,
                )
        assert r.status_code == 200
        assert r.json()["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_422_no_fields(self):
        db = make_activated_db(tables={"eventshift_events": {"data": EVENT_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/events/{EVENT_ID}",
                    json={},
                    headers=AUTH,
                )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_422_invalid_uuid(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    "/api/eventshift/events/not-uuid",
                    json={"name": "X"},
                    headers=AUTH,
                )
        assert r.status_code == 422


class TestCancelEvent:
    @pytest.mark.asyncio
    async def test_cancel_returns_204(self):
        db = make_activated_db(
            tables={
                "eventshift_events": {"data": [EVENT_ROW]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.delete(f"/api/eventshift/events/{EVENT_ID}", headers=AUTH)
        assert r.status_code == 204

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        db = make_activated_db(tables={"eventshift_events": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.delete(f"/api/eventshift/events/{EVENT_ID}", headers=AUTH)
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_422_invalid_uuid(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.delete("/api/eventshift/events/bad-id", headers=AUTH)
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# DEPARTMENTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestListDepartments:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        db = make_activated_db(
            tables={
                "eventshift_events": {"data": EVENT_ROW},
                "eventshift_departments": {"data": [DEPT_ROW]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(f"/api/eventshift/events/{EVENT_ID}/departments", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["name"] == "Logistics"

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("get", f"/api/eventshift/events/{EVENT_ID}/departments")

    @pytest.mark.asyncio
    async def test_event_not_found_404(self):
        db = make_activated_db(tables={"eventshift_events": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(f"/api/eventshift/events/{EVENT_ID}/departments", headers=AUTH)
        assert r.status_code == 404


class TestCreateDepartment:
    VALID_PAYLOAD = {"name": "Logistics"}

    @pytest.mark.asyncio
    async def test_creates_department_201(self):
        db = make_activated_db(
            tables={
                "eventshift_events": {"data": EVENT_ROW},
                "eventshift_departments": {"data": [DEPT_ROW]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/events/{EVENT_ID}/departments",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 201
        assert r.json()["name"] == "Logistics"

    @pytest.mark.asyncio
    async def test_422_missing_name(self):
        db = make_activated_db(tables={"eventshift_events": {"data": EVENT_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/events/{EVENT_ID}/departments",
                    json={},
                    headers=AUTH,
                )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_422_invalid_event_uuid(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    "/api/eventshift/events/not-a-uuid/departments",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "INVALID_UUID"


class TestUpdateDepartment:
    @pytest.mark.asyncio
    async def test_updates_department(self):
        db = make_activated_db(
            tables={
                "eventshift_departments": {"data": [{**DEPT_ROW, "name": "Ops"}]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/departments/{DEPT_ID}",
                    json={"name": "Ops"},
                    headers=AUTH,
                )
        assert r.status_code == 200
        assert r.json()["name"] == "Ops"

    @pytest.mark.asyncio
    async def test_422_no_fields(self):
        db = make_activated_db(tables={"eventshift_departments": {"data": DEPT_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/departments/{DEPT_ID}",
                    json={},
                    headers=AUTH,
                )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        db = make_activated_db(tables={"eventshift_departments": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/departments/{DEPT_ID}",
                    json={"name": "X"},
                    headers=AUTH,
                )
        assert r.status_code == 404


class TestGetDepartmentBlueprint:
    @pytest.mark.asyncio
    async def test_returns_full_blueprint(self):
        dept_with_meta = {
            **DEPT_ROW,
            "metadata": {"roles": ["lead", "staff"], "sops": ["check-in flow"]},
        }
        db = make_activated_db(tables={"eventshift_departments": {"data": dept_with_meta}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(
                    f"/api/eventshift/departments/{DEPT_ID}/blueprint",
                    headers=AUTH,
                )
        assert r.status_code == 200
        body = r.json()
        assert "blueprint" in body
        assert body["blueprint"]["roles"] == ["lead", "staff"]

    @pytest.mark.asyncio
    async def test_returns_filtered_section(self):
        dept_with_meta = {
            **DEPT_ROW,
            "metadata": {"roles": ["lead"], "sops": ["sop1"]},
        }
        db = make_activated_db(tables={"eventshift_departments": {"data": dept_with_meta}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(
                    f"/api/eventshift/departments/{DEPT_ID}/blueprint?section=roles",
                    headers=AUTH,
                )
        assert r.status_code == 200
        body = r.json()
        assert body["section"] == "roles"
        assert body["data"] == ["lead"]

    @pytest.mark.asyncio
    async def test_422_invalid_section(self):
        db = make_activated_db(tables={"eventshift_departments": {"data": DEPT_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(
                    f"/api/eventshift/departments/{DEPT_ID}/blueprint?section=invalid",
                    headers=AUTH,
                )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "INVALID_SECTION"

    @pytest.mark.asyncio
    async def test_404_department_not_found(self):
        db = make_activated_db(tables={"eventshift_departments": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(
                    f"/api/eventshift/departments/{DEPT_ID}/blueprint",
                    headers=AUTH,
                )
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# AREAS
# ═══════════════════════════════════════════════════════════════════════════════


class TestListAreas:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        db = make_activated_db(
            tables={
                "eventshift_departments": {"data": DEPT_ROW},
                "eventshift_areas": {"data": [AREA_ROW]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(
                    f"/api/eventshift/departments/{DEPT_ID}/areas",
                    headers=AUTH,
                )
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Gate A"

    @pytest.mark.asyncio
    async def test_422_invalid_dept_uuid(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(
                    "/api/eventshift/departments/not-a-uuid/areas",
                    headers=AUTH,
                )
        assert r.status_code == 422


class TestCreateArea:
    VALID_PAYLOAD = {"name": "Gate A"}

    @pytest.mark.asyncio
    async def test_creates_area_201(self):
        db = make_activated_db(
            tables={
                "eventshift_departments": {"data": DEPT_ROW},
                "eventshift_areas": {"data": [AREA_ROW]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/departments/{DEPT_ID}/areas",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 201
        assert r.json()["name"] == "Gate A"

    @pytest.mark.asyncio
    async def test_422_missing_name(self):
        db = make_activated_db(tables={"eventshift_departments": {"data": DEPT_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/departments/{DEPT_ID}/areas",
                    json={},
                    headers=AUTH,
                )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_dept_not_found_404(self):
        db = make_activated_db(tables={"eventshift_departments": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/departments/{DEPT_ID}/areas",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 404


class TestUpdateArea:
    @pytest.mark.asyncio
    async def test_updates_area(self):
        db = make_activated_db(
            tables={
                "eventshift_areas": {"data": [{**AREA_ROW, "name": "Gate B"}]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/areas/{AREA_ID}",
                    json={"name": "Gate B"},
                    headers=AUTH,
                )
        assert r.status_code == 200
        assert r.json()["name"] == "Gate B"

    @pytest.mark.asyncio
    async def test_422_no_fields(self):
        db = make_activated_db(tables={"eventshift_areas": {"data": AREA_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/areas/{AREA_ID}",
                    json={},
                    headers=AUTH,
                )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        db = make_activated_db(tables={"eventshift_areas": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/areas/{AREA_ID}",
                    json={"name": "X"},
                    headers=AUTH,
                )
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# UNITS
# ═══════════════════════════════════════════════════════════════════════════════


class TestListUnits:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        db = make_activated_db(
            tables={
                "eventshift_areas": {"data": AREA_ROW},
                "eventshift_units": {"data": [UNIT_ROW]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(f"/api/eventshift/areas/{AREA_ID}/units", headers=AUTH)
        assert r.status_code == 200
        assert r.json()[0]["name"] == "Morning Shift"

    @pytest.mark.asyncio
    async def test_422_invalid_area_uuid(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/areas/bad-uuid/units", headers=AUTH)
        assert r.status_code == 422


class TestCreateUnit:
    VALID_PAYLOAD = {
        "name": "Morning Shift",
        "shift_start": NOW,
        "shift_end": LATER,
    }

    @pytest.mark.asyncio
    async def test_creates_unit_201(self):
        db = make_activated_db(
            tables={
                "eventshift_areas": {"data": AREA_ROW},
                "eventshift_units": {"data": [UNIT_ROW]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/areas/{AREA_ID}/units",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 201
        assert r.json()["name"] == "Morning Shift"

    @pytest.mark.asyncio
    async def test_422_shift_end_before_start(self):
        db = make_activated_db(tables={"eventshift_areas": {"data": AREA_ROW}})
        payload = {**self.VALID_PAYLOAD, "shift_start": LATER, "shift_end": NOW}
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/areas/{AREA_ID}/units",
                    json=payload,
                    headers=AUTH,
                )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_422_invalid_status(self):
        db = make_activated_db(tables={"eventshift_areas": {"data": AREA_ROW}})
        payload = {**self.VALID_PAYLOAD, "status": "bad_status"}
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/areas/{AREA_ID}/units",
                    json=payload,
                    headers=AUTH,
                )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_area_not_found_404(self):
        db = make_activated_db(tables={"eventshift_areas": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/areas/{AREA_ID}/units",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 404


class TestUpdateUnit:
    @pytest.mark.asyncio
    async def test_updates_unit(self):
        db = make_activated_db(
            tables={
                "eventshift_units": {"data": [{**UNIT_ROW, "status": "staffed"}]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/units/{UNIT_ID}",
                    json={"status": "staffed"},
                    headers=AUTH,
                )
        assert r.status_code == 200
        assert r.json()["status"] == "staffed"

    @pytest.mark.asyncio
    async def test_422_no_fields(self):
        db = make_activated_db(tables={"eventshift_units": {"data": UNIT_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/units/{UNIT_ID}",
                    json={},
                    headers=AUTH,
                )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        db = make_activated_db(tables={"eventshift_units": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/units/{UNIT_ID}",
                    json={"name": "X"},
                    headers=AUTH,
                )
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# ASSIGNMENTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestListAssignments:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        db = make_activated_db(
            tables={
                "eventshift_units": {"data": UNIT_ROW},
                "eventshift_unit_assignments": {"data": [ASSIGN_ROW]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(f"/api/eventshift/units/{UNIT_ID}/assignments", headers=AUTH)
        assert r.status_code == 200
        assert r.json()[0]["role"] == "staff"

    @pytest.mark.asyncio
    async def test_422_invalid_unit_uuid(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/units/bad-uuid/assignments", headers=AUTH)
        assert r.status_code == 422


class TestCreateAssignment:
    VALID_PAYLOAD = {"user_id": OTHER_USER_ID, "role": "staff"}

    @pytest.mark.asyncio
    async def test_creates_assignment_201(self):
        db = make_activated_db(
            tables={
                "eventshift_units": {"data": UNIT_ROW},
                "eventshift_unit_assignments": {"data": [ASSIGN_ROW]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/units/{UNIT_ID}/assignments",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 201
        assert r.json()["role"] == "staff"

    @pytest.mark.asyncio
    async def test_409_duplicate_assignment(self):
        db = make_activated_db(
            tables={
                "eventshift_units": {"data": UNIT_ROW},
                "eventshift_unit_assignments": {"side_effect": RuntimeError("unique constraint")},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/units/{UNIT_ID}/assignments",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "ALREADY_ASSIGNED"

    @pytest.mark.asyncio
    async def test_422_invalid_role(self):
        db = make_activated_db(tables={"eventshift_units": {"data": UNIT_ROW}})
        payload = {**self.VALID_PAYLOAD, "role": "overlord"}
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/units/{UNIT_ID}/assignments",
                    json=payload,
                    headers=AUTH,
                )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_422_invalid_user_uuid(self):
        db = make_activated_db(tables={"eventshift_units": {"data": UNIT_ROW}})
        payload = {"user_id": "not-a-uuid", "role": "staff"}
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/units/{UNIT_ID}/assignments",
                    json=payload,
                    headers=AUTH,
                )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "INVALID_UUID"

    @pytest.mark.asyncio
    async def test_unit_not_found_404(self):
        db = make_activated_db(tables={"eventshift_units": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/units/{UNIT_ID}/assignments",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 404


class TestUpdateAssignment:
    @pytest.mark.asyncio
    async def test_updates_status(self):
        db = make_activated_db(
            tables={
                "eventshift_unit_assignments": {"data": [{**ASSIGN_ROW, "status": "checked_in"}]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/assignments/{ASSIGN_ID}",
                    json={"status": "checked_in"},
                    headers=AUTH,
                )
        assert r.status_code == 200
        assert r.json()["status"] == "checked_in"

    @pytest.mark.asyncio
    async def test_422_no_fields(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/assignments/{ASSIGN_ID}",
                    json={},
                    headers=AUTH,
                )
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_422_invalid_status(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/assignments/{ASSIGN_ID}",
                    json={"status": "flying"},
                    headers=AUTH,
                )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        db = make_activated_db(tables={"eventshift_unit_assignments": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.put(
                    f"/api/eventshift/assignments/{ASSIGN_ID}",
                    json={"role": "lead"},
                    headers=AUTH,
                )
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS
# ═══════════════════════════════════════════════════════════════════════════════


class TestListMetrics:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        db = make_activated_db(
            tables={
                "eventshift_units": {"data": UNIT_ROW},
                "eventshift_unit_metrics": {"data": [METRIC_ROW]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(f"/api/eventshift/units/{UNIT_ID}/metrics", headers=AUTH)
        assert r.status_code == 200
        assert r.json()[0]["metric_type"] == "attendance"

    @pytest.mark.asyncio
    async def test_filtered_by_metric_type(self):
        db = make_activated_db(
            tables={
                "eventshift_units": {"data": UNIT_ROW},
                "eventshift_unit_metrics": {"data": [METRIC_ROW]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get(
                    f"/api/eventshift/units/{UNIT_ID}/metrics?metric_type=attendance",
                    headers=AUTH,
                )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_422_invalid_unit_uuid(self):
        db = make_activated_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/units/bad-uuid/metrics", headers=AUTH)
        assert r.status_code == 422


class TestRecordMetric:
    VALID_PAYLOAD = {"metric_type": "attendance", "value": 5.0}

    @pytest.mark.asyncio
    async def test_records_metric_201(self):
        db = make_activated_db(
            tables={
                "eventshift_units": {"data": UNIT_ROW},
                "eventshift_unit_metrics": {"data": [METRIC_ROW]},
                "character_events": {"data": [{"id": "ce-1"}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/units/{UNIT_ID}/metrics",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 201
        assert r.json()["metric_type"] == "attendance"

    @pytest.mark.asyncio
    async def test_422_invalid_metric_type(self):
        db = make_activated_db(tables={"eventshift_units": {"data": UNIT_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/units/{UNIT_ID}/metrics",
                    json={"metric_type": "vibes"},
                    headers=AUTH,
                )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_unit_not_found_404(self):
        db = make_activated_db(tables={"eventshift_units": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    f"/api/eventshift/units/{UNIT_ID}/metrics",
                    json=self.VALID_PAYLOAD,
                    headers=AUTH,
                )
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# DEBUG
# ═══════════════════════════════════════════════════════════════════════════════


class TestDebugActivationState:
    @pytest.mark.asyncio
    async def test_returns_active_state(self):
        db = make_db(
            tables={"organizations": {"data": [{"id": ORG_ID}]}},
            rpc_data=True,
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/debug/activation-state", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["org_id"] == ORG_ID
        assert body["active"] is True
        assert body["module_slug"] == "eventshift"

    @pytest.mark.asyncio
    async def test_returns_inactive_state(self):
        db = make_db(
            tables={"organizations": {"data": [{"id": ORG_ID}]}},
            rpc_data=False,
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/debug/activation-state", headers=AUTH)
        assert r.status_code == 200
        assert r.json()["active"] is False

    @pytest.mark.asyncio
    async def test_403_when_no_org(self):
        db = make_db(tables={"organizations": {"data": []}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/eventshift/debug/activation-state", headers=AUTH)
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "NO_ORGANIZATION"

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("get", "/api/eventshift/debug/activation-state")
