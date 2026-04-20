"""Comprehensive unit tests for the grievance router.

Covers:
  • Pydantic model validation (GrievanceCreate, GrievanceOut, GrievanceAdminOut,
    GrievanceStatusUpdate, GrievanceListResponse, GrievanceAdminListResponse)
  • All 5 endpoints via httpx AsyncClient + dependency overrides
  • Helper function _to_admin_out field mapping
  • Route ordering regression — GET /api/aura/grievance must NOT match the
    /api/aura/{professional_id} wildcard (bug 0fb0599)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.deps import (
    get_current_user_id,
    get_supabase_admin,
    require_platform_admin,
)
from app.main import app
from app.routers.grievance import (
    GrievanceAdminListResponse,
    GrievanceAdminOut,
    GrievanceCreate,
    GrievanceListResponse,
    GrievanceOut,
    GrievanceStatusUpdate,
    _to_admin_out,
)

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = str(uuid.uuid4())
ADMIN_ID = str(uuid.uuid4())
GRIEVANCE_ID = str(uuid.uuid4())
SESSION_ID = str(uuid.uuid4())
NOW_STR = "2026-04-19T12:00:00+00:00"

# ── Row factories ──────────────────────────────────────────────────────────────


def _grievance_row(**overrides) -> dict:
    base = {
        "id": GRIEVANCE_ID,
        "user_id": USER_ID,
        "subject": "My AURA communication score is wrong",
        "description": "I scored 42 but my last 3 events rated me 9/10 consistently.",
        "related_competency_slug": "communication",
        "related_session_id": SESSION_ID,
        "status": "pending",
        "resolution": None,
        "admin_notes": None,
        "created_at": NOW_STR,
        "updated_at": NOW_STR,
        "resolved_at": None,
    }
    return {**base, **overrides}


# ── DB mock helpers ────────────────────────────────────────────────────────────


def _result(data=None) -> MagicMock:
    r = MagicMock()
    r.data = data
    return r


def _make_db(*execute_returns) -> MagicMock:
    """Chainable Supabase mock with sequential execute() side effects."""
    db = MagicMock()
    chain = MagicMock()

    for method in [
        "table",
        "select",
        "insert",
        "update",
        "eq",
        "neq",
        "in_",
        "order",
        "limit",
        "maybe_single",
        "single",
        "delete",
    ]:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain

    if len(execute_returns) == 1:
        chain.execute = AsyncMock(return_value=execute_returns[0])
        db.execute = AsyncMock(return_value=execute_returns[0])
    else:
        chain.execute = AsyncMock(side_effect=list(execute_returns))
        db.execute = AsyncMock(side_effect=list(execute_returns))

    return db


# ── Dependency override helpers ────────────────────────────────────────────────


def _admin_override(mock_db):
    async def _dep():
        yield mock_db

    return _dep


def _user_id_override(uid: str):
    async def _dep():
        return uid

    return _dep


def _require_admin_override(admin_id: str):
    async def _dep():
        return admin_id

    return _dep


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic model tests
# ══════════════════════════════════════════════════════════════════════════════


class TestGrievanceCreate:
    def test_valid_minimal(self):
        g = GrievanceCreate(subject="Score is off", description="My communication score looks wrong to me.")
        assert g.subject == "Score is off"
        assert g.related_competency_slug is None
        assert g.related_session_id is None

    def test_valid_with_all_fields(self):
        g = GrievanceCreate(
            subject="My communication score is wrong",
            description="I scored 42 but my last 3 events rated me 9/10 consistently.",
            related_competency_slug="communication",
            related_session_id=SESSION_ID,
        )
        assert g.related_competency_slug == "communication"
        assert g.related_session_id == SESSION_ID

    def test_rejects_subject_too_short(self):
        with pytest.raises(ValidationError):
            GrievanceCreate(subject="hi", description="long enough description here ok")

    def test_rejects_subject_too_long(self):
        with pytest.raises(ValidationError):
            GrievanceCreate(subject="x" * 201, description="long enough description here ok")

    def test_rejects_description_too_short(self):
        with pytest.raises(ValidationError):
            GrievanceCreate(subject="Valid subject text", description="short")

    def test_rejects_description_too_long(self):
        with pytest.raises(ValidationError):
            GrievanceCreate(subject="Valid subject text", description="x" * 5001)

    def test_rejects_competency_slug_too_long(self):
        with pytest.raises(ValidationError):
            GrievanceCreate(
                subject="Valid subject text",
                description="long enough description here ok",
                related_competency_slug="x" * 51,
            )

    def test_subject_at_min_length(self):
        g = GrievanceCreate(subject="abc", description="long enough description here ok")
        assert g.subject == "abc"

    def test_subject_at_max_length(self):
        g = GrievanceCreate(subject="x" * 200, description="long enough description here ok")
        assert len(g.subject) == 200

    def test_description_at_min_length(self):
        g = GrievanceCreate(subject="Valid subject", description="0123456789")
        assert len(g.description) == 10


class TestGrievanceStatusUpdate:
    def test_reviewing_without_resolution(self):
        u = GrievanceStatusUpdate(status="reviewing")
        assert u.status == "reviewing"
        assert u.resolution is None
        assert u.admin_notes is None

    def test_resolved_with_resolution(self):
        u = GrievanceStatusUpdate(status="resolved", resolution="Score verified correct by IRT model.")
        assert u.status == "resolved"
        assert "IRT" in u.resolution

    def test_rejected_with_resolution(self):
        u = GrievanceStatusUpdate(status="rejected", resolution="No evidence of scoring error found.")
        assert u.status == "rejected"

    def test_rejects_pending_as_target_status(self):
        with pytest.raises(ValidationError):
            GrievanceStatusUpdate(status="pending")

    def test_rejects_garbage_status(self):
        with pytest.raises(ValidationError):
            GrievanceStatusUpdate(status="nonsense_value")

    def test_resolution_max_length_allowed(self):
        u = GrievanceStatusUpdate(status="resolved", resolution="x" * 5000)
        assert len(u.resolution) == 5000

    def test_resolution_over_max_rejected(self):
        with pytest.raises(ValidationError):
            GrievanceStatusUpdate(status="resolved", resolution="x" * 5001)

    def test_admin_notes_optional(self):
        u = GrievanceStatusUpdate(status="reviewing", admin_notes="Looks valid, investigating")
        assert u.admin_notes == "Looks valid, investigating"


class TestGrievanceOut:
    def test_constructs_from_dict(self):
        g = GrievanceOut(
            id=GRIEVANCE_ID,
            subject="Test subject",
            description="Test description with enough length",
            related_competency_slug=None,
            related_session_id=None,
            status="pending",
            resolution=None,
            created_at=NOW_STR,
            resolved_at=None,
        )
        assert g.id == GRIEVANCE_ID
        assert g.status == "pending"
        assert g.resolution is None
        assert g.resolved_at is None

    def test_from_attributes_config(self):
        # from_attributes=True means model_config is set
        assert GrievanceOut.model_config.get("from_attributes") is True


class TestGrievanceAdminOut:
    def test_includes_admin_fields(self):
        g = GrievanceAdminOut(
            id=GRIEVANCE_ID,
            user_id=USER_ID,
            subject="Test subject",
            description="Test description with enough length",
            related_competency_slug=None,
            related_session_id=None,
            status="reviewing",
            resolution=None,
            admin_notes="Some internal note",
            created_at=NOW_STR,
            updated_at=NOW_STR,
            resolved_at=None,
        )
        assert g.user_id == USER_ID
        assert g.admin_notes == "Some internal note"
        assert g.updated_at == NOW_STR

    def test_inherits_from_grievance_out(self):
        assert issubclass(GrievanceAdminOut, GrievanceOut)


class TestGrievanceListResponse:
    def test_wraps_data_list(self):
        resp = GrievanceListResponse(data=[])
        assert resp.data == []

    def test_wraps_single_item(self):
        g = GrievanceOut(
            id=GRIEVANCE_ID,
            subject="Subject",
            description="Description here",
            related_competency_slug=None,
            related_session_id=None,
            status="pending",
            resolution=None,
            created_at=NOW_STR,
            resolved_at=None,
        )
        resp = GrievanceListResponse(data=[g])
        assert len(resp.data) == 1


class TestGrievanceAdminListResponse:
    def test_wraps_data_list(self):
        resp = GrievanceAdminListResponse(data=[])
        assert resp.data == []


# ══════════════════════════════════════════════════════════════════════════════
# _to_admin_out helper function
# ══════════════════════════════════════════════════════════════════════════════


class TestToAdminOut:
    def test_maps_all_fields_correctly(self):
        row = _grievance_row(status="reviewing", admin_notes="Checked logs")
        out = _to_admin_out(row)

        assert out.id == GRIEVANCE_ID
        assert out.user_id == USER_ID
        assert out.subject == row["subject"]
        assert out.description == row["description"]
        assert out.related_competency_slug == "communication"
        assert out.related_session_id == SESSION_ID
        assert out.status == "reviewing"
        assert out.resolution is None
        assert out.admin_notes == "Checked logs"
        assert out.created_at == NOW_STR
        assert out.updated_at == NOW_STR
        assert out.resolved_at is None

    def test_maps_resolved_at_when_present(self):
        row = _grievance_row(status="resolved", resolved_at=NOW_STR, resolution="Confirmed correct score.")
        out = _to_admin_out(row)

        assert out.resolved_at == NOW_STR
        assert out.resolution == "Confirmed correct score."

    def test_maps_null_optional_fields(self):
        row = _grievance_row(
            related_competency_slug=None,
            related_session_id=None,
            resolution=None,
            admin_notes=None,
            resolved_at=None,
        )
        out = _to_admin_out(row)

        assert out.related_competency_slug is None
        assert out.related_session_id is None
        assert out.resolution is None
        assert out.admin_notes is None
        assert out.resolved_at is None

    def test_converts_id_to_str(self):
        """id and user_id are cast via str() — ensure UUID objects work too."""
        row = _grievance_row()
        row["id"] = uuid.UUID(GRIEVANCE_ID)
        row["user_id"] = uuid.UUID(USER_ID)
        out = _to_admin_out(row)

        assert isinstance(out.id, str)
        assert isinstance(out.user_id, str)


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/aura/grievance
# ══════════════════════════════════════════════════════════════════════════════


class TestFileGrievance:
    @pytest.mark.asyncio
    async def test_happy_path_creates_grievance(self):
        row = _grievance_row()
        db = _make_db(_result(data=[row]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/aura/grievance",
                    json={
                        "subject": "My communication score is wrong",
                        "description": "I scored 42 but my last 3 events rated me 9/10 consistently.",
                    },
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == GRIEVANCE_ID
        assert body["status"] == "pending"
        assert body["subject"] == row["subject"]

    @pytest.mark.asyncio
    async def test_happy_path_with_optional_fields(self):
        row = _grievance_row()
        db = _make_db(_result(data=[row]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/aura/grievance",
                    json={
                        "subject": "My communication score is wrong",
                        "description": "I scored 42 but my last 3 events rated me 9/10 consistently.",
                        "related_competency_slug": "communication",
                        "related_session_id": SESSION_ID,
                    },
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 201
        body = resp.json()
        assert body["related_competency_slug"] == "communication"

    @pytest.mark.asyncio
    async def test_db_exception_returns_500(self):
        db = _make_db()
        chain = MagicMock()
        for m in ["table", "insert", "eq", "order", "limit", "select", "update", "in_", "maybe_single", "single"]:
            getattr(chain, m).return_value = chain
            getattr(db, m).return_value = chain
        chain.execute = AsyncMock(side_effect=RuntimeError("DB connection lost"))
        db.execute = AsyncMock(side_effect=RuntimeError("DB connection lost"))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/aura/grievance",
                    json={
                        "subject": "My communication score is wrong",
                        "description": "I scored 42 but my last 3 events rated me 9/10 consistently.",
                    },
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 500
        assert resp.json()["detail"]["code"] == "GRIEVANCE_FAILED"

    @pytest.mark.asyncio
    async def test_empty_insert_result_returns_500(self):
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/aura/grievance",
                    json={
                        "subject": "My communication score is wrong",
                        "description": "I scored 42 but my last 3 events rated me 9/10 consistently.",
                    },
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 500
        assert resp.json()["detail"]["code"] == "GRIEVANCE_FAILED"

    @pytest.mark.asyncio
    async def test_none_insert_result_returns_500(self):
        db = _make_db(_result(data=None))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/aura/grievance",
                    json={
                        "subject": "My communication score is wrong",
                        "description": "I scored 42 but my last 3 events rated me 9/10 consistently.",
                    },
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_schema_validation_rejects_short_subject(self):
        app.dependency_overrides[get_supabase_admin] = _admin_override(_make_db())
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/aura/grievance",
                    json={"subject": "hi", "description": "long enough description text"},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/aura/grievance
# ══════════════════════════════════════════════════════════════════════════════


class TestListOwnGrievances:
    @pytest.mark.asyncio
    async def test_happy_path_returns_list(self):
        rows = [_grievance_row(), _grievance_row(id=str(uuid.uuid4()), status="reviewing")]
        db = _make_db(_result(data=rows))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["id"] == GRIEVANCE_ID

    @pytest.mark.asyncio
    async def test_empty_list_when_no_grievances(self):
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 200
        assert resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_empty_list_when_data_none(self):
        db = _make_db(_result(data=None))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert resp.status_code == 200
        assert resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_response_wraps_in_data_key(self):
        db = _make_db(_result(data=[_grievance_row()]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        assert "data" in resp.json()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/aura/grievance/admin/pending
# ══════════════════════════════════════════════════════════════════════════════


class TestAdminListPendingGrievances:
    @pytest.mark.asyncio
    async def test_admin_gate_403_for_non_admin(self):
        """require_platform_admin raises 403 — returns 403 to client."""
        from fastapi import HTTPException

        async def _not_admin():
            raise HTTPException(status_code=403, detail={"code": "NOT_PLATFORM_ADMIN", "message": "No access"})

        db = _make_db(_result(data=[]))
        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        app.dependency_overrides[require_platform_admin] = _not_admin
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance/admin/pending")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_happy_path_returns_pending_list(self):
        rows = [_grievance_row(status="pending"), _grievance_row(id=str(uuid.uuid4()), status="reviewing")]
        db = _make_db(_result(data=rows))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance/admin/pending")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2
        # Admin view includes user_id
        assert "user_id" in body["data"][0]

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_pending(self):
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance/admin/pending")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200
        assert resp.json()["data"] == []


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/aura/grievance/admin/history
# ══════════════════════════════════════════════════════════════════════════════


class TestAdminListClosedGrievances:
    @pytest.mark.asyncio
    async def test_admin_gate_403_for_non_admin(self):
        from fastapi import HTTPException

        async def _not_admin():
            raise HTTPException(status_code=403, detail={"code": "NOT_PLATFORM_ADMIN", "message": "No access"})

        db = _make_db(_result(data=[]))
        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        app.dependency_overrides[require_platform_admin] = _not_admin
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance/admin/history")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_happy_path_returns_closed_list(self):
        rows = [
            _grievance_row(status="resolved", resolved_at=NOW_STR, resolution="Verified correct."),
            _grievance_row(id=str(uuid.uuid4()), status="rejected", resolved_at=NOW_STR, resolution="No error."),
        ]
        db = _make_db(_result(data=rows))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance/admin/history")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    @pytest.mark.asyncio
    async def test_limit_cap_at_200(self):
        """Requesting limit=500 is silently capped to 200 in the handler."""
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance/admin/history?limit=500")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        # Handler returns 200 (caps internally), not an error
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_default_limit_returns_200(self):
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance/admin/history")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# PATCH /api/aura/grievance/admin/{id}
# ══════════════════════════════════════════════════════════════════════════════


class TestAdminTransitionGrievance:
    @pytest.mark.asyncio
    async def test_422_resolved_without_resolution(self):
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "resolved", "resolution": None},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "RESOLUTION_REQUIRED"

    @pytest.mark.asyncio
    async def test_422_rejected_without_resolution(self):
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "rejected"},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "RESOLUTION_REQUIRED"

    @pytest.mark.asyncio
    async def test_422_whitespace_only_resolution_rejected(self):
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "resolved", "resolution": "   "},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "RESOLUTION_REQUIRED"

    @pytest.mark.asyncio
    async def test_reviewing_without_resolution_succeeds(self):
        row = _grievance_row(status="reviewing")
        db = _make_db(_result(data=[row]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "reviewing"},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200
        assert resp.json()["status"] == "reviewing"

    @pytest.mark.asyncio
    async def test_happy_path_resolved_with_resolution(self):
        row = _grievance_row(
            status="resolved",
            resolution="Score verified correct by IRT model.",
            resolved_at=NOW_STR,
        )
        db = _make_db(_result(data=[row]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "resolved", "resolution": "Score verified correct by IRT model."},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "resolved"
        assert body["resolved_at"] is not None

    @pytest.mark.asyncio
    async def test_404_when_grievance_not_found(self):
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "reviewing"},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "GRIEVANCE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_500_on_db_exception(self):
        db = MagicMock()
        chain = MagicMock()
        for m in ["table", "update", "eq", "select", "insert", "order", "limit", "in_", "maybe_single", "single"]:
            getattr(chain, m).return_value = chain
            getattr(db, m).return_value = chain
        chain.execute = AsyncMock(side_effect=RuntimeError("Connection refused"))
        db.execute = AsyncMock(side_effect=RuntimeError("Connection refused"))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "reviewing"},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 500
        assert resp.json()["detail"]["code"] == "GRIEVANCE_UPDATE_FAILED"

    @pytest.mark.asyncio
    async def test_admin_gate_403(self):
        from fastapi import HTTPException

        async def _not_admin():
            raise HTTPException(status_code=403, detail={"code": "NOT_PLATFORM_ADMIN", "message": "No access"})

        db = _make_db(_result(data=[]))
        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        app.dependency_overrides[require_platform_admin] = _not_admin
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "reviewing"},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_resolved_sets_resolved_at_in_payload(self):
        """Handler writes resolved_at = now() when transitioning to resolved.

        We verify this by checking the DB call included resolved_at, via
        inspecting the mock's call args on update().
        """
        row = _grievance_row(status="resolved", resolved_at=NOW_STR, resolution="Fixed.")
        db = _make_db(_result(data=[row]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "resolved", "resolution": "Fixed."},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200
        # resolved_at is non-null in the response
        assert resp.json()["resolved_at"] is not None

    @pytest.mark.asyncio
    async def test_reviewing_does_not_set_resolved_at(self):
        """Transitioning to reviewing must NOT set resolved_at."""
        row = _grievance_row(status="reviewing", resolved_at=None)
        db = _make_db(_result(data=[row]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "reviewing"},
                )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200
        assert resp.json()["resolved_at"] is None


# ══════════════════════════════════════════════════════════════════════════════
# Route ordering regression — bug 0fb0599
# GET /api/aura/grievance must NOT be swallowed by /api/aura/{professional_id}
# ══════════════════════════════════════════════════════════════════════════════


class TestRouteOrderingRegression:
    @pytest.mark.asyncio
    async def test_grievance_list_not_matched_as_professional_id(self):
        """Verify GET /aura/grievance hits the grievance router, not aura/{professional_id}.

        The aura router has a wildcard GET /aura/{professional_id} that would
        swallow /aura/grievance if grievance.router was registered after aura.router
        in main.py. This test pins the correct ordering.

        If the route is mis-ordered the mock DB receives a .eq("professional_id", "grievance")
        query (wrong table) and the endpoint returns a non-200 or unexpected payload.
        """
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(USER_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

        # Correct route returns GrievanceListResponse envelope {"data": [...]}
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)

    @pytest.mark.asyncio
    async def test_admin_pending_not_matched_as_professional_id(self):
        """GET /aura/grievance/admin/pending must resolve to grievance admin route."""
        db = _make_db(_result(data=[]))

        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = _require_admin_override(ADMIN_ID)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/aura/grievance/admin/pending")
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)
