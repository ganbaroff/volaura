"""Unit tests for EventShift schemas + pure helper functions.

Covers Pydantic v2 validators (status, slug, role, headcount, metric_type)
and the _validate_uuid helper from the router.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.eventshift import (
    ASSIGNMENT_ROLES,
    ASSIGNMENT_STATUSES,
    EVENT_STATUSES,
    METRIC_TYPES,
    UNIT_STATUSES,
    AreaCreate,
    DepartmentCreate,
    EventShiftEventCreate,
    EventShiftEventUpdate,
    UnitAssignmentCreate,
    UnitAssignmentUpdate,
    UnitCreate,
    UnitMetricCreate,
)

NOW = datetime.now(tz=UTC)


# ── EventShiftEventCreate ───────────────────────────────────────────────────


class TestEventCreate:
    def test_valid_minimal(self):
        e = EventShiftEventCreate(slug="wuf-13", name="WUF 13", start_at=NOW, end_at=NOW)
        assert e.slug == "wuf-13"
        assert e.status == "planning"

    def test_slug_stripped_lowered(self):
        e = EventShiftEventCreate(slug="  WUF-13  ", name="x", start_at=NOW, end_at=NOW)
        assert e.slug == "wuf-13"

    def test_slug_too_long(self):
        with pytest.raises(ValidationError, match="slug must be 1-64"):
            EventShiftEventCreate(slug="a" * 65, name="x", start_at=NOW, end_at=NOW)

    def test_slug_empty(self):
        with pytest.raises(ValidationError, match="slug must be 1-64"):
            EventShiftEventCreate(slug="   ", name="x", start_at=NOW, end_at=NOW)

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            EventShiftEventCreate(slug="x", name="x", start_at=NOW, end_at=NOW, status="invalid")

    def test_all_valid_statuses(self):
        for s in EVENT_STATUSES:
            e = EventShiftEventCreate(slug="x", name="x", start_at=NOW, end_at=NOW, status=s)
            assert e.status == s


class TestEventUpdate:
    def test_none_status_allowed(self):
        u = EventShiftEventUpdate()
        assert u.status is None

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            EventShiftEventUpdate(status="nope")

    def test_valid_status(self):
        u = EventShiftEventUpdate(status="live")
        assert u.status == "live"


# ── UnitCreate ───────────────────────────────────────────────────────────────


class TestUnitCreate:
    def test_valid_minimal(self):
        u = UnitCreate(name="Morning shift", shift_start=NOW, shift_end=NOW)
        assert u.status == "open"
        assert u.required_headcount == 1
        assert u.required_skills == []

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            UnitCreate(name="x", shift_start=NOW, shift_end=NOW, status="bad")

    def test_all_valid_statuses(self):
        for s in UNIT_STATUSES:
            u = UnitCreate(name="x", shift_start=NOW, shift_end=NOW, status=s)
            assert u.status == s

    def test_headcount_zero(self):
        with pytest.raises(ValidationError, match="required_headcount must be 1..1000"):
            UnitCreate(name="x", shift_start=NOW, shift_end=NOW, required_headcount=0)

    def test_headcount_over_1000(self):
        with pytest.raises(ValidationError, match="required_headcount must be 1..1000"):
            UnitCreate(name="x", shift_start=NOW, shift_end=NOW, required_headcount=1001)

    def test_headcount_boundary_1(self):
        u = UnitCreate(name="x", shift_start=NOW, shift_end=NOW, required_headcount=1)
        assert u.required_headcount == 1

    def test_headcount_boundary_1000(self):
        u = UnitCreate(name="x", shift_start=NOW, shift_end=NOW, required_headcount=1000)
        assert u.required_headcount == 1000


# ── UnitAssignmentCreate ─────────────────────────────────────────────────────


class TestAssignmentCreate:
    def test_default_role(self):
        a = UnitAssignmentCreate(user_id="abc")
        assert a.role == "staff"

    def test_invalid_role(self):
        with pytest.raises(ValidationError, match="role must be one of"):
            UnitAssignmentCreate(user_id="abc", role="boss")

    def test_all_valid_roles(self):
        for r in ASSIGNMENT_ROLES:
            a = UnitAssignmentCreate(user_id="abc", role=r)
            assert a.role == r


class TestAssignmentUpdate:
    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            UnitAssignmentUpdate(status="wrong")

    def test_all_valid_statuses(self):
        for s in ASSIGNMENT_STATUSES:
            u = UnitAssignmentUpdate(status=s)
            assert u.status == s

    def test_none_allowed(self):
        u = UnitAssignmentUpdate()
        assert u.role is None
        assert u.status is None


# ── UnitMetricCreate ─────────────────────────────────────────────────────────


class TestMetricCreate:
    def test_valid(self):
        m = UnitMetricCreate(metric_type="incident", value=1.0)
        assert m.metric_type == "incident"

    def test_invalid_type(self):
        with pytest.raises(ValidationError, match="metric_type must be one of"):
            UnitMetricCreate(metric_type="unknown")

    def test_all_valid_types(self):
        for t in METRIC_TYPES:
            m = UnitMetricCreate(metric_type=t)
            assert m.metric_type == t


# ── DepartmentCreate / AreaCreate (no custom validators, sanity check) ───────


def test_department_create_defaults():
    d = DepartmentCreate(name="GSE")
    assert d.sort_order == 0
    assert d.description is None


def test_area_create_minimal():
    a = AreaCreate(name="Registration")
    assert a.description is None
    assert a.location is None


# ── _validate_uuid (router helper, pure function) ───────────────────────────


def test_validate_uuid_valid():
    from app.routers.eventshift import _validate_uuid

    _validate_uuid("550e8400-e29b-41d4-a716-446655440000", "test")


def test_validate_uuid_invalid():
    from fastapi import HTTPException

    from app.routers.eventshift import _validate_uuid

    with pytest.raises(HTTPException) as exc_info:
        _validate_uuid("not-a-uuid", "field_x")
    assert exc_info.value.status_code == 422
    assert "INVALID_UUID" in str(exc_info.value.detail)


def test_validate_uuid_empty():
    from fastapi import HTTPException

    from app.routers.eventshift import _validate_uuid

    with pytest.raises(HTTPException):
        _validate_uuid("", "field")
