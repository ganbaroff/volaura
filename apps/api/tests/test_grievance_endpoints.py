"""HTTP endpoint tests for the grievance router.

Covers:
- POST /api/aura/grievance               — file a grievance
- GET  /api/aura/grievance               — list own grievances
- GET  /api/aura/grievance/admin/pending  — admin: list pending
- GET  /api/aura/grievance/admin/history  — admin: list closed
- PATCH /api/aura/grievance/admin/{id}   — admin: transition status
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, require_platform_admin
from app.main import app

USER_ID = str(uuid4())
ADMIN_ID = str(uuid4())
GRIEVANCE_ID = str(uuid4())
AUTH_HEADERS = {"Authorization": "Bearer test-token"}

GRIEVANCE_ROW = {
    "id": GRIEVANCE_ID,
    "user_id": USER_ID,
    "subject": "Unfair communication score",
    "description": "My score of 40 does not reflect my work at all.",
    "related_competency_slug": "communication",
    "related_session_id": None,
    "status": "pending",
    "resolution": None,
    "admin_notes": None,
    "created_at": "2026-04-15T10:00:00Z",
    "updated_at": "2026-04-15T10:00:00Z",
    "resolved_at": None,
}


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_chain(data=None, side_effect=None) -> MagicMock:
    result = MagicMock()
    result.data = data
    result.count = None

    execute = AsyncMock(side_effect=side_effect) if side_effect else AsyncMock(return_value=result)

    chain = MagicMock()
    for method in ("select", "eq", "neq", "in_", "order", "limit", "update", "insert", "upsert"):
        getattr(chain, method).return_value = chain
    chain.maybe_single.return_value = chain
    chain.execute = execute
    return chain


def make_db(tables: dict | None = None) -> MagicMock:
    db = MagicMock()
    tables = tables or {}

    def dispatch(name: str) -> MagicMock:
        cfg = tables.get(name, {})
        return make_chain(**cfg)

    db.table.side_effect = dispatch
    return db


def user_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def admin_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def user_id_dep(uid: str = USER_ID):
    async def _override():
        return uid

    return _override


def platform_admin_dep(uid: str = ADMIN_ID):
    async def _override():
        return uid

    return _override


# ── POST /api/aura/grievance ──────────────────────────────────────────────────


class TestFileGrievance:
    @pytest.mark.asyncio
    async def test_creates_grievance_returns_201(self):
        db = make_db({"grievances": {"data": [GRIEVANCE_ROW]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    "/api/aura/grievance",
                    json={
                        "subject": "Unfair communication score",
                        "description": "My score of 40 does not reflect my work at all.",
                    },
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 201
            body = r.json()
            assert body["status"] == "pending"
            assert body["subject"] == "Unfair communication score"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_grievance_with_competency_slug(self):
        row = {**GRIEVANCE_ROW, "related_competency_slug": "leadership"}
        db = make_db({"grievances": {"data": [row]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    "/api/aura/grievance",
                    json={
                        "subject": "Leadership assessment unfair",
                        "description": "The assessment does not reflect my leadership skills.",
                        "related_competency_slug": "leadership",
                    },
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 201
            assert r.json()["related_competency_slug"] == "leadership"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_subject_too_short_returns_422(self):
        db = make_db()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    "/api/aura/grievance",
                    json={"subject": "Hi", "description": "This description is long enough."},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_description_too_short_returns_422(self):
        db = make_db()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    "/api/aura/grievance",
                    json={"subject": "Valid subject", "description": "Short"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_db_error_returns_500(self):
        db = make_db({"grievances": {"side_effect": Exception("DB down")}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    "/api/aura/grievance",
                    json={
                        "subject": "Valid subject here",
                        "description": "Valid description that is long enough.",
                    },
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 500
            assert r.json()["detail"]["code"] == "GRIEVANCE_FAILED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        async with make_client() as client:
            r = await client.post(
                "/api/aura/grievance",
                json={"subject": "Test subject here", "description": "Long enough description."},
            )
        assert r.status_code == 401


# ── GET /api/aura/grievance ───────────────────────────────────────────────────


class TestListOwnGrievances:
    @pytest.mark.asyncio
    async def test_returns_own_grievances(self):
        db = make_db({"grievances": {"data": [GRIEVANCE_ROW]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/grievance", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert "data" in body
            assert len(body["data"]) == 1
            assert body["data"][0]["id"] == GRIEVANCE_ID
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_grievances(self):
        db = make_db({"grievances": {"data": []}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/grievance", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["data"] == []
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        async with make_client() as client:
            r = await client.get("/api/aura/grievance")
        assert r.status_code == 401


# ── GET /api/aura/grievance/admin/pending ─────────────────────────────────────


class TestAdminListPending:
    @pytest.mark.asyncio
    async def test_admin_can_list_pending(self):
        db = make_db({"grievances": {"data": [GRIEVANCE_ROW]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/grievance/admin/pending", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert "data" in body
            assert body["data"][0]["user_id"] == USER_ID
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

    @pytest.mark.asyncio
    async def test_non_admin_returns_403(self):
        db = make_db()
        # Provide user dep but NOT platform_admin override — require_platform_admin will run its DB check
        # Instead simulate it raising 403
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()

        # Override require_platform_admin to raise 403
        from fastapi import HTTPException as FastHTTPException

        def non_admin_dep():
            async def _override():
                raise FastHTTPException(
                    status_code=403,
                    detail={"code": "NOT_PLATFORM_ADMIN", "message": "Platform admin access required"},
                )

            return _override

        app.dependency_overrides[require_platform_admin] = non_admin_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/grievance/admin/pending", headers=AUTH_HEADERS)
            assert r.status_code == 403
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none_pending(self):
        db = make_db({"grievances": {"data": []}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/grievance/admin/pending", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["data"] == []
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)


# ── GET /api/aura/grievance/admin/history ─────────────────────────────────────


class TestAdminListHistory:
    @pytest.mark.asyncio
    async def test_admin_can_list_history(self):
        resolved_row = {**GRIEVANCE_ROW, "status": "resolved", "resolution": "Score was correct."}
        db = make_db({"grievances": {"data": [resolved_row]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/grievance/admin/history", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["data"][0]["status"] == "resolved"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)


# ── PATCH /api/aura/grievance/admin/{id} ─────────────────────────────────────


class TestAdminTransitionGrievance:
    @pytest.mark.asyncio
    async def test_transition_to_reviewing(self):
        row = {**GRIEVANCE_ROW, "status": "reviewing"}
        db = make_db({"grievances": {"data": [row]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "reviewing"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 200
            assert r.json()["status"] == "reviewing"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

    @pytest.mark.asyncio
    async def test_resolve_requires_resolution_text(self):
        db = make_db()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "resolved"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "RESOLUTION_REQUIRED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

    @pytest.mark.asyncio
    async def test_reject_requires_resolution_text(self):
        db = make_db()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "rejected"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "RESOLUTION_REQUIRED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

    @pytest.mark.asyncio
    async def test_resolve_with_resolution_succeeds(self):
        row = {**GRIEVANCE_ROW, "status": "resolved", "resolution": "Score was recalculated."}
        db = make_db({"grievances": {"data": [row]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "resolved", "resolution": "Score was recalculated."},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 200
            assert r.json()["status"] == "resolved"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

    @pytest.mark.asyncio
    async def test_grievance_not_found_returns_404(self):
        db = make_db({"grievances": {"data": []}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "reviewing"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "GRIEVANCE_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)

    @pytest.mark.asyncio
    async def test_invalid_status_returns_422(self):
        db = make_db()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ADMIN_ID)
        app.dependency_overrides[require_platform_admin] = platform_admin_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    f"/api/aura/grievance/admin/{GRIEVANCE_ID}",
                    json={"status": "invalid_status"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(require_platform_admin, None)
