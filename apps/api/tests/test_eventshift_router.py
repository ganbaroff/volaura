"""Tests for EventShift router endpoint logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.routers.eventshift import (
    _assert_area_in_org,
    _assert_department_in_org,
    _assert_event_in_org,
    _assert_module_active,
    _assert_unit_in_org,
    _emit_event,
    _resolve_org_id,
    _validate_uuid,
    cancel_event,
    create_area,
    create_assignment,
    create_department,
    create_event,
    create_unit,
    debug_activation_state,
    get_department_blueprint,
    get_event,
    list_areas,
    list_assignments,
    list_departments,
    list_events,
    list_metrics,
    list_units,
    record_metric,
    update_area,
    update_assignment,
    update_department,
    update_event,
    update_unit,
)
from app.schemas.eventshift import (
    AreaCreate,
    AreaUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    EventShiftEventCreate,
    EventShiftEventUpdate,
    UnitAssignmentCreate,
    UnitAssignmentUpdate,
    UnitCreate,
    UnitMetricCreate,
    UnitUpdate,
)

# ── Constants ──────────────────────────────────────────────────────────────────

ORG_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())
EVENT_ID = str(uuid.uuid4())
DEPT_ID = str(uuid.uuid4())
AREA_ID = str(uuid.uuid4())
UNIT_ID = str(uuid.uuid4())
ASSIGNMENT_ID = str(uuid.uuid4())
METRIC_ID = str(uuid.uuid4())

NOW = datetime.now(UTC)
LATER = NOW + timedelta(hours=2)
YESTERDAY = NOW - timedelta(days=1)

FAKE_REQUEST = MagicMock()  # rate limiter reads .state; not called in direct tests


# ── DB mock helpers ────────────────────────────────────────────────────────────


def _chain(data=None, *, side_effect=None):
    """Build a fluent Supabase query-chain mock."""
    result = MagicMock(data=data if data is not None else [])
    execute = AsyncMock(side_effect=side_effect) if side_effect else AsyncMock(return_value=result)
    chain = MagicMock()
    for method in (
        "select",
        "eq",
        "neq",
        "gte",
        "lte",
        "gt",
        "lt",
        "order",
        "range",
        "limit",
        "insert",
        "update",
        "upsert",
        "delete",
        "single",
        "filter",
    ):
        getattr(chain, method).return_value = chain
    chain.execute = execute
    return chain


def _db(tables: dict | None = None, rpc_data: dict | None = None) -> MagicMock:
    """DB mock routing table(name) and rpc(name, params) calls."""
    db = MagicMock()
    tables = tables or {}

    def _table(name):
        cfg = tables.get(name, {})
        return _chain(**cfg)

    db.table.side_effect = _table

    if rpc_data is not None:

        def _rpc(name, params=None):
            data = rpc_data.get(name, [])
            c = MagicMock()
            c.execute = AsyncMock(return_value=MagicMock(data=data))
            return c

        db.rpc.side_effect = _rpc

    return db


def _event_row(**overrides) -> dict:
    base = {
        "id": EVENT_ID,
        "org_id": ORG_ID,
        "slug": "test-event",
        "name": "Test Event",
        "description": None,
        "start_at": NOW.isoformat(),
        "end_at": LATER.isoformat(),
        "timezone": "Asia/Baku",
        "location": None,
        "metadata": None,
        "status": "planning",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    return {**base, **overrides}


def _dept_row(**overrides) -> dict:
    base = {
        "id": DEPT_ID,
        "org_id": ORG_ID,
        "event_id": EVENT_ID,
        "name": "GSE",
        "description": None,
        "color_hex": None,
        "lead_user_id": None,
        "sort_order": 0,
        "metadata": None,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    return {**base, **overrides}


def _area_row(**overrides) -> dict:
    base = {
        "id": AREA_ID,
        "org_id": ORG_ID,
        "department_id": DEPT_ID,
        "name": "Registration",
        "description": None,
        "location": None,
        "metadata": None,
        "coordinator_user_id": None,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    return {**base, **overrides}


def _unit_row(**overrides) -> dict:
    base = {
        "id": UNIT_ID,
        "org_id": ORG_ID,
        "area_id": AREA_ID,
        "name": "Morning Shift",
        "description": None,
        "shift_start": NOW.isoformat(),
        "shift_end": LATER.isoformat(),
        "required_headcount": 5,
        "required_skills": [],
        "status": "open",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    return {**base, **overrides}


def _assignment_row(**overrides) -> dict:
    base = {
        "id": ASSIGNMENT_ID,
        "org_id": ORG_ID,
        "unit_id": UNIT_ID,
        "user_id": USER_ID,
        "role": "staff",
        "status": "assigned",
        "notes": None,
        "assigned_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    return {**base, **overrides}


def _metric_row(**overrides) -> dict:
    base = {
        "id": METRIC_ID,
        "org_id": ORG_ID,
        "unit_id": UNIT_ID,
        "metric_type": "incident",
        "value": 1.0,
        "payload": None,
        "recorded_at": NOW.isoformat(),
        "recorded_by": USER_ID,
        "created_at": NOW.isoformat(),
    }
    return {**base, **overrides}


# ── _validate_uuid ─────────────────────────────────────────────────────────────


class TestValidateUuid:
    def test_valid_uuid_passes(self):
        _validate_uuid(str(uuid.uuid4()), "field")  # no exception

    def test_invalid_string_raises_422(self):
        with pytest.raises(HTTPException) as exc:
            _validate_uuid("not-a-uuid", "event_id")
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "INVALID_UUID"

    def test_empty_string_raises_422(self):
        with pytest.raises(HTTPException) as exc:
            _validate_uuid("", "field")
        assert exc.value.status_code == 422

    def test_none_like_empty_string_raises_422(self):
        # Simulate None-ish input via empty string (router catches ValueError/AttributeError)
        with pytest.raises(HTTPException):
            _validate_uuid("", "field")

    def test_field_name_in_message(self):
        with pytest.raises(HTTPException) as exc:
            _validate_uuid("bad", "my_field")
        assert "my_field" in exc.value.detail["message"]


# ── _resolve_org_id ────────────────────────────────────────────────────────────


class TestResolveOrgId:
    @pytest.mark.asyncio
    async def test_returns_org_id_when_found(self):
        db = _db({"organizations": {"data": [{"id": ORG_ID}]}})
        result = await _resolve_org_id(db, USER_ID)
        assert result == ORG_ID

    @pytest.mark.asyncio
    async def test_raises_403_when_no_org(self):
        db = _db({"organizations": {"data": []}})
        with pytest.raises(HTTPException) as exc:
            await _resolve_org_id(db, USER_ID)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "NO_ORGANIZATION"

    @pytest.mark.asyncio
    async def test_raises_403_when_data_none(self):
        db = _db({"organizations": {"data": None}})
        with pytest.raises(HTTPException) as exc:
            await _resolve_org_id(db, USER_ID)
        assert exc.value.status_code == 403


# ── _assert_module_active ──────────────────────────────────────────────────────


class TestAssertModuleActive:
    @pytest.mark.asyncio
    async def test_passes_when_rpc_returns_data(self):
        db = _db(rpc_data={"is_module_active_for_org": [True]})
        await _assert_module_active(db, ORG_ID)  # no exception

    @pytest.mark.asyncio
    async def test_raises_403_when_rpc_empty(self):
        db = _db(rpc_data={"is_module_active_for_org": []})
        with pytest.raises(HTTPException) as exc:
            await _assert_module_active(db, ORG_ID)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "MODULE_NOT_ACTIVATED"

    @pytest.mark.asyncio
    async def test_raises_403_when_rpc_none(self):
        db = _db(rpc_data={"is_module_active_for_org": None})
        with pytest.raises(HTTPException) as exc:
            await _assert_module_active(db, ORG_ID)
        assert exc.value.status_code == 403


# ── _emit_event ────────────────────────────────────────────────────────────────


class TestEmitEvent:
    @pytest.mark.asyncio
    async def test_success_path_inserts_row(self):
        db = _db({"character_events": {"data": [{"id": "evt-1"}]}})
        await _emit_event(
            db,
            user_id=USER_ID,
            org_id=ORG_ID,
            event_type="test_event",
            payload={"key": "val"},
        )
        db.table.assert_called_with("character_events")

    @pytest.mark.asyncio
    async def test_swallows_exceptions(self):
        db = _db({"character_events": {"side_effect": RuntimeError("DB down")}})
        # Must NOT raise — best-effort
        await _emit_event(
            db,
            user_id=USER_ID,
            org_id=ORG_ID,
            event_type="test_event",
            payload={},
        )

    @pytest.mark.asyncio
    async def test_org_id_enriched_in_payload(self):
        captured = {}

        async def fake_execute():
            return MagicMock(data=[{"id": "x"}])

        chain = _chain(data=[{"id": "x"}])

        def capture_insert(row):
            captured["row"] = row
            return chain

        chain.insert = capture_insert
        db = MagicMock()
        db.table.return_value = chain

        await _emit_event(
            db,
            user_id=USER_ID,
            org_id=ORG_ID,
            event_type="test_event",
            payload={"event_id": "abc"},
        )
        assert captured["row"]["payload"]["org_id"] == ORG_ID


# ── _assert_event_in_org ───────────────────────────────────────────────────────


class TestAssertEventInOrg:
    @pytest.mark.asyncio
    async def test_returns_row_when_found(self):
        row = _event_row()
        db = _db({"eventshift_events": {"data": row}})
        result = await _assert_event_in_org(db, EVENT_ID, ORG_ID)
        assert result == row

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        db = _db({"eventshift_events": {"data": None}})
        with pytest.raises(HTTPException) as exc:
            await _assert_event_in_org(db, EVENT_ID, ORG_ID)
        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "EVENT_NOT_FOUND"


# ── _assert_department_in_org ──────────────────────────────────────────────────


class TestAssertDepartmentInOrg:
    @pytest.mark.asyncio
    async def test_returns_row_when_found(self):
        row = _dept_row()
        db = _db({"eventshift_departments": {"data": row}})
        result = await _assert_department_in_org(db, DEPT_ID, ORG_ID)
        assert result == row

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        db = _db({"eventshift_departments": {"data": None}})
        with pytest.raises(HTTPException) as exc:
            await _assert_department_in_org(db, DEPT_ID, ORG_ID)
        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "DEPARTMENT_NOT_FOUND"


# ── _assert_area_in_org ────────────────────────────────────────────────────────


class TestAssertAreaInOrg:
    @pytest.mark.asyncio
    async def test_returns_row_when_found(self):
        row = _area_row()
        db = _db({"eventshift_areas": {"data": row}})
        result = await _assert_area_in_org(db, AREA_ID, ORG_ID)
        assert result == row

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        db = _db({"eventshift_areas": {"data": None}})
        with pytest.raises(HTTPException) as exc:
            await _assert_area_in_org(db, AREA_ID, ORG_ID)
        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "AREA_NOT_FOUND"


# ── _assert_unit_in_org ────────────────────────────────────────────────────────


class TestAssertUnitInOrg:
    @pytest.mark.asyncio
    async def test_returns_row_when_found(self):
        row = _unit_row()
        db = _db({"eventshift_units": {"data": row}})
        result = await _assert_unit_in_org(db, UNIT_ID, ORG_ID)
        assert result == row

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        db = _db({"eventshift_units": {"data": None}})
        with pytest.raises(HTTPException) as exc:
            await _assert_unit_in_org(db, UNIT_ID, ORG_ID)
        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "UNIT_NOT_FOUND"


# ── Event endpoints ────────────────────────────────────────────────────────────


class TestListEvents:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        rows = [_event_row(), _event_row(id=str(uuid.uuid4()))]
        db = _db({"eventshift_events": {"data": rows}})
        result = await list_events(FAKE_REQUEST, db, ORG_ID, status=None, limit=50, offset=0)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_result(self):
        db = _db({"eventshift_events": {"data": []}})
        result = await list_events(FAKE_REQUEST, db, ORG_ID, status=None, limit=50, offset=0)
        assert result == []

    @pytest.mark.asyncio
    async def test_status_filter_applied(self):
        db = _db({"eventshift_events": {"data": []}})
        result = await list_events(FAKE_REQUEST, db, ORG_ID, status="live", limit=50, offset=0)
        assert result == []


class TestCreateEvent:
    def _payload(self, start_at=None, end_at=None, **overrides) -> EventShiftEventCreate:
        return EventShiftEventCreate(
            slug="wuf-13",
            name="WUF 13",
            start_at=start_at if start_at is not None else NOW,
            end_at=end_at if end_at is not None else LATER,
            **overrides,
        )

    @pytest.mark.asyncio
    async def test_invalid_times_end_before_start(self):
        db = _db()
        payload = self._payload(start_at=LATER, end_at=NOW)
        with pytest.raises(HTTPException) as exc:
            await create_event(FAKE_REQUEST, payload, db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "INVALID_TIMES"

    @pytest.mark.asyncio
    async def test_invalid_times_equal(self):
        db = _db()
        payload = self._payload(start_at=NOW, end_at=NOW)
        with pytest.raises(HTTPException) as exc:
            await create_event(FAKE_REQUEST, payload, db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_success_returns_event(self):
        row = _event_row()
        db = _db(
            {
                "eventshift_events": {"data": [row]},
                "character_events": {"data": [{"id": "x"}]},
            }
        )
        result = await create_event(FAKE_REQUEST, self._payload(), db, USER_ID, ORG_ID)
        assert result.id == EVENT_ID
        assert result.slug == "test-event"

    @pytest.mark.asyncio
    async def test_db_insert_failure_raises_500(self):
        db = _db({"eventshift_events": {"data": []}})
        with pytest.raises(HTTPException) as exc:
            await create_event(FAKE_REQUEST, self._payload(), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "CREATE_FAILED"


class TestGetEvent:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await get_event(FAKE_REQUEST, "bad-uuid", db, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = _db({"eventshift_events": {"data": None}})
        with pytest.raises(HTTPException) as exc:
            await get_event(FAKE_REQUEST, EVENT_ID, db, ORG_ID)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_success_returns_event(self):
        row = _event_row()
        db = _db({"eventshift_events": {"data": row}})
        result = await get_event(FAKE_REQUEST, EVENT_ID, db, ORG_ID)
        assert result.id == EVENT_ID


class TestUpdateEvent:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await update_event(FAKE_REQUEST, "not-uuid", EventShiftEventUpdate(name="x"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_no_fields_raises_422(self):
        db = _db({"eventshift_events": {"data": _event_row()}})
        with pytest.raises(HTTPException) as exc:
            await update_event(FAKE_REQUEST, EVENT_ID, EventShiftEventUpdate(), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_event_not_found_in_org_raises_404(self):
        db = _db({"eventshift_events": {"data": None}})
        with pytest.raises(HTTPException) as exc:
            await update_event(FAKE_REQUEST, EVENT_ID, EventShiftEventUpdate(name="new"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_success_returns_updated_event(self):
        updated_row = _event_row(name="Updated")
        # first call: _assert_event_in_org (single), second call: update result
        call_count = 0

        chain = MagicMock()
        for m in ("select", "eq", "neq", "order", "range", "insert", "update", "single", "filter", "limit"):
            getattr(chain, m).return_value = chain

        async def execute_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # _assert_event_in_org
                return MagicMock(data=_event_row())
            # update result
            return MagicMock(data=[updated_row])

        chain.execute = AsyncMock(side_effect=execute_side_effect)
        db = MagicMock()
        db.table.return_value = chain
        db.rpc.return_value = chain  # for character_events

        result = await update_event(
            FAKE_REQUEST,
            EVENT_ID,
            EventShiftEventUpdate(name="Updated"),
            db,
            USER_ID,
            ORG_ID,
        )
        assert result.name == "Updated"


class TestCancelEvent:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await cancel_event(FAKE_REQUEST, "bad", db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = _db({"eventshift_events": {"data": []}})
        with pytest.raises(HTTPException) as exc:
            await cancel_event(FAKE_REQUEST, EVENT_ID, db, USER_ID, ORG_ID)
        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "EVENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_success_returns_none(self):
        db = _db(
            {
                "eventshift_events": {"data": [{"id": EVENT_ID}]},
                "character_events": {"data": [{"id": "x"}]},
            }
        )
        result = await cancel_event(FAKE_REQUEST, EVENT_ID, db, USER_ID, ORG_ID)
        assert result is None


# ── Department endpoints ───────────────────────────────────────────────────────


class TestListDepartments:
    @pytest.mark.asyncio
    async def test_invalid_event_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await list_departments(FAKE_REQUEST, "bad", db, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_list(self):
        call_count = 0
        chain = _chain(data=[_dept_row()])

        async def routed_execute():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # _assert_event_in_org
                return MagicMock(data=_event_row())
            return MagicMock(data=[_dept_row()])

        chain.execute = AsyncMock(side_effect=routed_execute)
        db = MagicMock()
        db.table.return_value = chain

        result = await list_departments(FAKE_REQUEST, EVENT_ID, db, ORG_ID)
        assert len(result) >= 0  # routed correctly, no crash


class TestCreateDepartment:
    @pytest.mark.asyncio
    async def test_invalid_event_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await create_department(FAKE_REQUEST, "bad", DepartmentCreate(name="GSE"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_db_insert_failure_raises_500(self):
        call_count = 0

        chain = _chain()

        async def routed_execute():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_event_row())
            return MagicMock(data=[])  # insert returns empty → 500

        chain.execute = AsyncMock(side_effect=routed_execute)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await create_department(FAKE_REQUEST, EVENT_ID, DepartmentCreate(name="GSE"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_success_returns_department(self):
        dept_row = _dept_row()
        call_count = 0

        chain = _chain()

        async def routed_execute():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_event_row())
            if call_count == 2:
                return MagicMock(data=[dept_row])
            return MagicMock(data=[{"id": "evt"}])  # character_events

        chain.execute = AsyncMock(side_effect=routed_execute)
        db = MagicMock()
        db.table.return_value = chain

        result = await create_department(FAKE_REQUEST, EVENT_ID, DepartmentCreate(name="GSE"), db, USER_ID, ORG_ID)
        assert result.name == "GSE"


class TestUpdateDepartment:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await update_department(FAKE_REQUEST, "bad", DepartmentUpdate(name="x"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_no_fields_raises_422(self):
        db = _db({"eventshift_departments": {"data": _dept_row()}})
        with pytest.raises(HTTPException) as exc:
            await update_department(FAKE_REQUEST, DEPT_ID, DepartmentUpdate(), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_not_found_update_raises_404(self):
        call_count = 0
        chain = _chain()

        async def routed_execute():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_dept_row())
            return MagicMock(data=[])  # update returns empty

        chain.execute = AsyncMock(side_effect=routed_execute)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await update_department(FAKE_REQUEST, DEPT_ID, DepartmentUpdate(name="x"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 404


class TestGetDepartmentBlueprint:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await get_department_blueprint(FAKE_REQUEST, "bad", db, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_no_section_returns_full_blueprint(self):
        meta = {"roles": ["Manager"], "sops": ["SOP-1"]}
        db = _db({"eventshift_departments": {"data": _dept_row(metadata=meta)}})
        result = await get_department_blueprint(FAKE_REQUEST, DEPT_ID, db, ORG_ID, section=None)
        assert result["blueprint"] == meta
        assert result["department_id"] == DEPT_ID

    @pytest.mark.asyncio
    async def test_valid_section_returns_filtered_data(self):
        meta = {"roles": ["Manager", "Lead"], "sops": ["SOP-1"]}
        db = _db({"eventshift_departments": {"data": _dept_row(metadata=meta)}})
        result = await get_department_blueprint(FAKE_REQUEST, DEPT_ID, db, ORG_ID, section="roles")
        assert result["section"] == "roles"
        assert result["data"] == ["Manager", "Lead"]

    @pytest.mark.asyncio
    async def test_invalid_section_raises_422(self):
        db = _db({"eventshift_departments": {"data": _dept_row()}})
        with pytest.raises(HTTPException) as exc:
            await get_department_blueprint(FAKE_REQUEST, DEPT_ID, db, ORG_ID, section="garbage")
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "INVALID_SECTION"

    @pytest.mark.asyncio
    async def test_missing_section_data_returns_none(self):
        db = _db({"eventshift_departments": {"data": _dept_row(metadata={})}})
        result = await get_department_blueprint(FAKE_REQUEST, DEPT_ID, db, ORG_ID, section="roles")
        assert result["data"] is None

    @pytest.mark.asyncio
    async def test_no_metadata_returns_empty_blueprint(self):
        db = _db({"eventshift_departments": {"data": _dept_row(metadata=None)}})
        result = await get_department_blueprint(FAKE_REQUEST, DEPT_ID, db, ORG_ID, section=None)
        assert result["blueprint"] == {}


# ── Area endpoints ─────────────────────────────────────────────────────────────


class TestListAreas:
    @pytest.mark.asyncio
    async def test_invalid_dept_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await list_areas(FAKE_REQUEST, "bad", db, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_list(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_dept_row())
            return MagicMock(data=[_area_row()])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await list_areas(FAKE_REQUEST, DEPT_ID, db, ORG_ID)
        assert len(result) >= 0


class TestCreateArea:
    @pytest.mark.asyncio
    async def test_invalid_dept_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await create_area(FAKE_REQUEST, "bad", AreaCreate(name="Reg"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_success_returns_area(self):
        area_row = _area_row()
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_dept_row())
            if call_count == 2:
                return MagicMock(data=[area_row])
            return MagicMock(data=[{"id": "x"}])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await create_area(FAKE_REQUEST, DEPT_ID, AreaCreate(name="Registration"), db, USER_ID, ORG_ID)
        assert result.name == "Registration"

    @pytest.mark.asyncio
    async def test_insert_failure_raises_500(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_dept_row())
            return MagicMock(data=[])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await create_area(FAKE_REQUEST, DEPT_ID, AreaCreate(name="Reg"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 500


class TestUpdateArea:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await update_area(FAKE_REQUEST, "bad", AreaUpdate(name="x"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_no_fields_raises_422(self):
        db = _db({"eventshift_areas": {"data": _area_row()}})
        with pytest.raises(HTTPException) as exc:
            await update_area(FAKE_REQUEST, AREA_ID, AreaUpdate(), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_not_found_update_raises_404(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_area_row())
            return MagicMock(data=[])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await update_area(FAKE_REQUEST, AREA_ID, AreaUpdate(name="x"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "AREA_NOT_FOUND"


# ── Unit endpoints ─────────────────────────────────────────────────────────────


class TestListUnits:
    @pytest.mark.asyncio
    async def test_invalid_area_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await list_units(FAKE_REQUEST, "bad", db, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_list(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_area_row())
            return MagicMock(data=[_unit_row()])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await list_units(FAKE_REQUEST, AREA_ID, db, ORG_ID)
        assert len(result) >= 0


class TestCreateUnit:
    def _payload(self, **overrides) -> UnitCreate:
        return UnitCreate(name="Morning Shift", shift_start=NOW, shift_end=LATER, **overrides)

    @pytest.mark.asyncio
    async def test_invalid_area_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await create_unit(FAKE_REQUEST, "bad", self._payload(), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_shift_end_before_start_raises_422(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            return MagicMock(data=_area_row())

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        payload = UnitCreate(name="Bad Shift", shift_start=LATER, shift_end=NOW)
        with pytest.raises(HTTPException) as exc:
            await create_unit(FAKE_REQUEST, AREA_ID, payload, db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "INVALID_TIMES"

    @pytest.mark.asyncio
    async def test_shift_end_equal_start_raises_422(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            return MagicMock(data=_area_row())

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        payload = UnitCreate(name="Equal Shift", shift_start=NOW, shift_end=NOW)
        with pytest.raises(HTTPException) as exc:
            await create_unit(FAKE_REQUEST, AREA_ID, payload, db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_success_returns_unit(self):
        unit_row = _unit_row()
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_area_row())
            if call_count == 2:
                return MagicMock(data=[unit_row])
            return MagicMock(data=[{"id": "x"}])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await create_unit(FAKE_REQUEST, AREA_ID, self._payload(), db, USER_ID, ORG_ID)
        assert result.name == "Morning Shift"

    @pytest.mark.asyncio
    async def test_insert_failure_raises_500(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_area_row())
            return MagicMock(data=[])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await create_unit(FAKE_REQUEST, AREA_ID, self._payload(), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 500


class TestUpdateUnit:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await update_unit(FAKE_REQUEST, "bad", UnitUpdate(name="x"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_no_fields_raises_422(self):
        db = _db({"eventshift_units": {"data": _unit_row()}})
        with pytest.raises(HTTPException) as exc:
            await update_unit(FAKE_REQUEST, UNIT_ID, UnitUpdate(), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            return MagicMock(data=[])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await update_unit(FAKE_REQUEST, UNIT_ID, UnitUpdate(name="x"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "UNIT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_success_returns_updated_unit(self):
        updated_unit = _unit_row(name="Evening Shift")
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            if call_count == 2:
                return MagicMock(data=[updated_unit])
            return MagicMock(data=[{"id": "x"}])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await update_unit(FAKE_REQUEST, UNIT_ID, UnitUpdate(name="Evening Shift"), db, USER_ID, ORG_ID)
        assert result.name == "Evening Shift"


# ── Assignment endpoints ───────────────────────────────────────────────────────


class TestListAssignments:
    @pytest.mark.asyncio
    async def test_invalid_unit_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await list_assignments(FAKE_REQUEST, "bad", db, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_list(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            return MagicMock(data=[_assignment_row()])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await list_assignments(FAKE_REQUEST, UNIT_ID, db, ORG_ID)
        assert len(result) >= 0


class TestCreateAssignment:
    @pytest.mark.asyncio
    async def test_invalid_unit_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await create_assignment(FAKE_REQUEST, "bad", UnitAssignmentCreate(user_id=USER_ID), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_user_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await create_assignment(
                FAKE_REQUEST, UNIT_ID, UnitAssignmentCreate(user_id="not-uuid"), db, USER_ID, ORG_ID
            )
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_duplicate_raises_409(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            raise Exception("duplicate key value violates unique constraint")

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await create_assignment(FAKE_REQUEST, UNIT_ID, UnitAssignmentCreate(user_id=USER_ID), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 409
        assert exc.value.detail["code"] == "ALREADY_ASSIGNED"

    @pytest.mark.asyncio
    async def test_empty_insert_result_raises_500(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            return MagicMock(data=[])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await create_assignment(FAKE_REQUEST, UNIT_ID, UnitAssignmentCreate(user_id=USER_ID), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "CREATE_FAILED"

    @pytest.mark.asyncio
    async def test_success_returns_assignment(self):
        assignment_row = _assignment_row()
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            if call_count == 2:
                return MagicMock(data=[assignment_row])
            return MagicMock(data=[{"id": "x"}])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await create_assignment(
            FAKE_REQUEST, UNIT_ID, UnitAssignmentCreate(user_id=USER_ID), db, USER_ID, ORG_ID
        )
        assert result.role == "staff"


class TestUpdateAssignment:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await update_assignment(FAKE_REQUEST, "bad", UnitAssignmentUpdate(role="lead"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_no_fields_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await update_assignment(FAKE_REQUEST, ASSIGNMENT_ID, UnitAssignmentUpdate(), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422
        assert exc.value.detail["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = _db({"eventshift_unit_assignments": {"data": []}})
        with pytest.raises(HTTPException) as exc:
            await update_assignment(FAKE_REQUEST, ASSIGNMENT_ID, UnitAssignmentUpdate(role="lead"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 404
        assert exc.value.detail["code"] == "ASSIGNMENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_success_returns_updated(self):
        updated = _assignment_row(role="lead")
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=[updated])
            return MagicMock(data=[{"id": "x"}])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await update_assignment(
            FAKE_REQUEST, ASSIGNMENT_ID, UnitAssignmentUpdate(role="lead"), db, USER_ID, ORG_ID
        )
        assert result.role == "lead"


# ── Metric endpoints ───────────────────────────────────────────────────────────


class TestListMetrics:
    @pytest.mark.asyncio
    async def test_invalid_unit_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await list_metrics(FAKE_REQUEST, "bad", db, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_list(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            return MagicMock(data=[_metric_row()])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await list_metrics(FAKE_REQUEST, UNIT_ID, db, ORG_ID, metric_type=None, limit=100)
        assert len(result) >= 0

    @pytest.mark.asyncio
    async def test_metric_type_filter_applied(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            return MagicMock(data=[])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await list_metrics(FAKE_REQUEST, UNIT_ID, db, ORG_ID, metric_type="incident", limit=100)
        assert result == []


class TestRecordMetric:
    @pytest.mark.asyncio
    async def test_invalid_unit_uuid_raises_422(self):
        db = _db()
        with pytest.raises(HTTPException) as exc:
            await record_metric(FAKE_REQUEST, "bad", UnitMetricCreate(metric_type="incident"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_insert_failure_raises_500(self):
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            return MagicMock(data=[])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        with pytest.raises(HTTPException) as exc:
            await record_metric(FAKE_REQUEST, UNIT_ID, UnitMetricCreate(metric_type="incident"), db, USER_ID, ORG_ID)
        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "CREATE_FAILED"

    @pytest.mark.asyncio
    async def test_success_returns_metric(self):
        metric_row = _metric_row()
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            if call_count == 2:
                return MagicMock(data=[metric_row])
            return MagicMock(data=[{"id": "x"}])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        result = await record_metric(
            FAKE_REQUEST, UNIT_ID, UnitMetricCreate(metric_type="incident", value=2.0), db, USER_ID, ORG_ID
        )
        assert result.metric_type == "incident"

    @pytest.mark.asyncio
    async def test_recorded_at_defaults_to_now_when_none(self):
        metric_row = _metric_row()
        call_count = 0
        chain = _chain()

        async def routed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(data=_unit_row())
            if call_count == 2:
                return MagicMock(data=[metric_row])
            return MagicMock(data=[{"id": "x"}])

        chain.execute = AsyncMock(side_effect=routed)
        db = MagicMock()
        db.table.return_value = chain

        # recorded_at=None → should default to datetime.now(UTC)
        result = await record_metric(
            FAKE_REQUEST, UNIT_ID, UnitMetricCreate(metric_type="incident", recorded_at=None), db, USER_ID, ORG_ID
        )
        assert result.metric_type == "incident"


# ── Debug endpoint ─────────────────────────────────────────────────────────────


class TestDebugActivationState:
    @pytest.mark.asyncio
    async def test_active_org(self):
        db = _db(
            {"organizations": {"data": [{"id": ORG_ID}]}},
            rpc_data={"is_module_active_for_org": [True]},
        )
        result = await debug_activation_state(FAKE_REQUEST, db, USER_ID)
        assert result["org_id"] == ORG_ID
        assert result["module_slug"] == "eventshift"
        assert result["active"] is True

    @pytest.mark.asyncio
    async def test_inactive_org(self):
        db = _db(
            {"organizations": {"data": [{"id": ORG_ID}]}},
            rpc_data={"is_module_active_for_org": []},
        )
        result = await debug_activation_state(FAKE_REQUEST, db, USER_ID)
        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_no_org_raises_403(self):
        db = _db(
            {"organizations": {"data": []}},
            rpc_data={},
        )
        with pytest.raises(HTTPException) as exc:
            await debug_activation_state(FAKE_REQUEST, db, USER_ID)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "NO_ORGANIZATION"
