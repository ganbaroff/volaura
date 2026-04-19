"""Unit tests for app/routers/organizations.py.

Covers:
1. Router registration (prefix, tags, routes, methods)
2. Helper functions (_get_org_id_for_user, _assert_search_ownership)
3. Key endpoint error paths: 404, 409, 403, 422, 500
4. Happy paths for major endpoints
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.routers.organizations import (
    _MAX_SAVED_SEARCHES_PER_ORG,
    _assert_search_ownership,
    _get_org_id_for_user,
    router,
)

# ── Constants ──────────────────────────────────────────────────────────────────

ORG_USER_ID = "aaaaaaaa-0001-0000-0000-000000000001"
ORG_ID = "bbbbbbbb-0001-0000-0000-000000000001"
VOL_ID = "cccccccc-0001-0000-0000-000000000001"
VOL_ID_2 = "dddddddd-0001-0000-0000-000000000002"
SEARCH_ID = str(uuid.uuid4())
NON_ORG_USER_ID = "eeeeeeee-0001-0000-0000-000000000001"

NOW_ISO = "2026-04-19T10:00:00+00:00"

SAVED_SEARCH_ROW = {
    "id": SEARCH_ID,
    "org_id": ORG_ID,
    "name": "Top Engineers",
    "filters": {"query": "backend", "min_aura": 60.0},
    "notify_on_match": True,
    "last_checked_at": NOW_ISO,
    "created_at": NOW_ISO,
}

ORG_ROW = {"id": ORG_ID, "name": "Test Corp"}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _admin_override(db):
    async def _dep():
        yield db

    return _dep


def _user_override(db):
    async def _dep():
        yield db

    return _dep


def _uid_override(uid: str):
    async def _dep():
        return uid

    return _dep


def _make_db(*_args, **_kwargs) -> MagicMock:
    """Simple generic mock DB — chain-returns self, execute returns empty."""
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.in_.return_value = t
    t.maybe_single.return_value = t
    t.insert.return_value = t
    t.update.return_value = t
    t.delete.return_value = t
    t.order.return_value = t
    t.limit.return_value = t
    t.gte.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data=None, count=0))
    db = MagicMock()
    db.table = MagicMock(return_value=t)
    return db


# ── 1. Router registration ─────────────────────────────────────────────────────


def test_router_prefix():
    assert router.prefix == "/organizations"


def test_router_tags():
    assert "Organizations" in router.tags


def test_router_has_expected_routes():
    paths = {r.path for r in router.routes}
    assert "/organizations" in paths
    assert "/organizations/me" in paths
    assert "/organizations/{org_id}" in paths
    assert "/organizations/search/professionals" in paths
    assert "/organizations/assign-assessments" in paths
    assert "/organizations/intro-requests" in paths
    assert "/organizations/saved-searches" in paths
    assert "/organizations/saved-searches/{search_id}" in paths


def test_router_route_methods():
    method_map: dict[str, set[str]] = {}
    for r in router.routes:
        method_map.setdefault(r.path, set()).update(r.methods or [])

    assert "GET" in method_map["/organizations"]
    assert "POST" in method_map["/organizations"]
    assert "GET" in method_map["/organizations/me"]
    assert "PUT" in method_map["/organizations/me"]
    assert "GET" in method_map["/organizations/{org_id}"]
    assert "POST" in method_map["/organizations/search/professionals"]
    assert "POST" in method_map["/organizations/assign-assessments"]
    assert "POST" in method_map["/organizations/intro-requests"]
    assert "POST" in method_map["/organizations/saved-searches"]
    assert "PATCH" in method_map["/organizations/saved-searches/{search_id}"]
    assert "DELETE" in method_map["/organizations/saved-searches/{search_id}"]


# ── 2. Module-level constant ───────────────────────────────────────────────────


def test_max_saved_searches_constant():
    assert _MAX_SAVED_SEARCHES_PER_ORG == 20


# ── 3. Helper: _get_org_id_for_user ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_org_id_for_user_found():
    db = MagicMock()
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.maybe_single.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data={"id": ORG_ID}))
    db.table.return_value = t

    result = await _get_org_id_for_user(db, ORG_USER_ID)
    assert result == ORG_ID


@pytest.mark.asyncio
async def test_get_org_id_for_user_not_found():
    db = MagicMock()
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.maybe_single.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data=None))
    db.table.return_value = t

    with pytest.raises(HTTPException) as exc_info:
        await _get_org_id_for_user(db, ORG_USER_ID)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "ORG_NOT_FOUND"


# ── 4. Helper: _assert_search_ownership ───────────────────────────────────────


@pytest.mark.asyncio
async def test_assert_search_ownership_found():
    db = MagicMock()
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.maybe_single.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data=SAVED_SEARCH_ROW))
    db.table.return_value = t

    row = await _assert_search_ownership(db, SEARCH_ID, ORG_ID)
    assert row == SAVED_SEARCH_ROW


@pytest.mark.asyncio
async def test_assert_search_ownership_not_found():
    db = MagicMock()
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.maybe_single.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data=None))
    db.table.return_value = t

    with pytest.raises(HTTPException) as exc_info:
        await _assert_search_ownership(db, SEARCH_ID, ORG_ID)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "SEARCH_NOT_FOUND"


# ── 5. GET /organizations — list_organizations ─────────────────────────────────


def _build_list_orgs_mock(orgs: list[dict]):
    t = MagicMock()
    t.select.return_value = t
    t.order.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data=orgs))
    db = MagicMock()
    db.table.return_value = t
    return db


@pytest.mark.asyncio
async def test_list_organizations_returns_list():
    orgs = [
        {"id": ORG_ID, "name": "Acme", "description": None, "logo_url": None, "type": None, "website": None, "is_active": True},
    ]
    db = _build_list_orgs_mock(orgs)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/organizations", headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body[0]["name"] == "Acme"


@pytest.mark.asyncio
async def test_list_organizations_empty():
    db = _build_list_orgs_mock([])
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/organizations", headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == []


# ── 6. GET /organizations/me ───────────────────────────────────────────────────


def _build_get_me_mock(org_data: dict | None):
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.maybe_single.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data=org_data))
    db = MagicMock()
    db.table.return_value = t
    return db


@pytest.mark.asyncio
async def test_get_my_organization_found():
    org_data = {
        "id": ORG_ID,
        "name": "My Corp",
        "description": None,
        "website": None,
        "logo_url": None,
        "contact_email": None,
        "type": None,
        "is_active": True,
        "verified_at": None,
        "subscription_tier": None,
        "trust_score": None,
        "created_at": None,
        "updated_at": None,
    }
    db = _build_get_me_mock(org_data)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/organizations/me", headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["name"] == "My Corp"


@pytest.mark.asyncio
async def test_get_my_organization_not_found():
    db = _build_get_me_mock(None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/organizations/me", headers={"Authorization": "Bearer fake"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"


# ── 7. POST /organizations — create_organization ──────────────────────────────


def _build_create_org_mock(existing: bool, created_row: dict | None = None):
    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                n = call_counts["organizations"]
                call_counts["organizations"] += 1
                if n == 0:
                    # existing check (admin)
                    return MagicMock(data=[{"id": ORG_ID}] if existing else [])
                else:
                    # insert (user db)
                    return MagicMock(data=[created_row] if created_row else [])
            t.select.return_value = t
            t.eq.return_value = t
            t.insert.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db_admin = MagicMock()
    db_admin.table = MagicMock(side_effect=make_table)
    db_user = MagicMock()
    db_user.table = MagicMock(side_effect=make_table)
    return db_admin, db_user


@pytest.mark.asyncio
async def test_create_organization_conflict():
    """User already has an org → 409 ORG_EXISTS."""
    db_admin, db_user = _build_create_org_mock(existing=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
    app.dependency_overrides[get_supabase_user] = _user_override(db_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations",
                json={"name": "New Corp"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "ORG_EXISTS"


@pytest.mark.asyncio
async def test_create_organization_success():
    created_row = {
        "id": ORG_ID,
        "name": "New Corp",
        "description": None,
        "website": None,
        "logo_url": None,
        "contact_email": None,
        "type": None,
        "is_active": True,
        "verified_at": None,
        "subscription_tier": None,
        "trust_score": None,
        "created_at": None,
        "updated_at": None,
    }
    db_admin, db_user = _build_create_org_mock(existing=False, created_row=created_row)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
    app.dependency_overrides[get_supabase_user] = _user_override(db_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations",
                json={"name": "New Corp"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 201
    assert resp.json()["name"] == "New Corp"


# ── 8. PUT /organizations/me ──────────────────────────────────────────────────


def _build_update_org_mock(updated_row: dict | None):
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.update.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data=[updated_row] if updated_row else []))
    db = MagicMock()
    db.table.return_value = t
    return db


@pytest.mark.asyncio
async def test_update_org_no_fields_422():
    db = _build_update_org_mock(None)
    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.put(
                "/api/organizations/me",
                json={},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "NO_FIELDS"


@pytest.mark.asyncio
async def test_update_org_not_found_404():
    db = _build_update_org_mock(None)
    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.put(
                "/api/organizations/me",
                json={"name": "Updated Corp"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"


# ── 9. GET /organizations/{org_id} ────────────────────────────────────────────


def _build_get_org_mock(org_data: dict | None):
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.maybe_single.return_value = t
    t.execute = AsyncMock(return_value=MagicMock(data=org_data))
    db = MagicMock()
    db.table.return_value = t
    return db


@pytest.mark.asyncio
async def test_get_organization_not_found():
    db = _build_get_org_mock(None)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/organizations/{ORG_ID}",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"


# ── 10. GET /organizations/{org_id}/collective-aura ───────────────────────────


def _build_collective_aura_mock(
    is_owner: bool = True,
    sessions: list[dict] | None = None,
    aura_rows: list[dict] | None = None,
):
    if sessions is None:
        sessions = []
    if aura_rows is None:
        aura_rows = []

    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID} if is_owner else None)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "assessment_sessions":
            async def _exec(*_a, **_kw):
                return MagicMock(data=sessions)
            t.select.return_value = t
            t.eq.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "aura_scores":
            async def _exec(*_a, **_kw):
                return MagicMock(data=aura_rows)
            t.select.return_value = t
            t.in_.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    return db


@pytest.mark.asyncio
async def test_collective_aura_non_owner_403():
    db = _build_collective_aura_mock(is_owner=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(NON_ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/organizations/{ORG_ID}/collective-aura",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NOT_ORG_OWNER"


@pytest.mark.asyncio
async def test_collective_aura_empty_pool():
    """Owner but no completed sessions → count=0, avg_aura=None."""
    db = _build_collective_aura_mock(is_owner=True, sessions=[], aura_rows=[])
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/organizations/{ORG_ID}/collective-aura",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["avg_aura"] is None


@pytest.mark.asyncio
async def test_collective_aura_with_scores():
    sessions = [
        {"volunteer_id": VOL_ID, "status": "completed"},
        {"volunteer_id": VOL_ID_2, "status": "completed"},
    ]
    aura_rows = [
        {"volunteer_id": VOL_ID, "total_score": 80.0},
        {"volunteer_id": VOL_ID_2, "total_score": 60.0},
    ]
    db = _build_collective_aura_mock(is_owner=True, sessions=sessions, aura_rows=aura_rows)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/organizations/{ORG_ID}/collective-aura",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert body["avg_aura"] == pytest.approx(70.0, abs=0.1)


# ── 11. POST /organizations/assign-assessments ────────────────────────────────


def _build_assign_mock(
    org_exists: bool = True,
    valid_slugs: dict | None = None,
    prof_ids: list[str] | None = None,
    existing_session: bool = False,
):
    if valid_slugs is None:
        valid_slugs = {"communication": "comp-uuid-001"}
    if prof_ids is None:
        prof_ids = [VOL_ID]

    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID, "name": "Test Corp"} if org_exists else None)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "competencies":
            async def _exec(*_a, **_kw):
                return MagicMock(data=[{"slug": k, "id": v} for k, v in valid_slugs.items()])
            t.select.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "profiles":
            async def _exec(*_a, **_kw):
                return MagicMock(data=[{"id": pid} for pid in prof_ids])
            t.select.return_value = t
            t.in_.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "assessment_sessions":
            async def _exec(*_a, **_kw):
                n = call_counts["assessment_sessions"]
                call_counts["assessment_sessions"] += 1
                # Odd calls = existing check; even calls = insert
                if n % 2 == 0:
                    return MagicMock(data=[{"id": "sess-x"}] if existing_session else [])
                else:
                    return MagicMock(data=[{"id": "sess-new"}])
            t.select.return_value = t
            t.eq.return_value = t
            t.insert.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    return db


@pytest.mark.asyncio
async def test_assign_assessments_no_org_403():
    db = _build_assign_mock(org_exists=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(NON_ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/assign-assessments",
                json={"professional_ids": [VOL_ID], "competency_slugs": ["communication"]},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "NOT_ORG_OWNER"


@pytest.mark.asyncio
async def test_assign_assessments_invalid_slug_422():
    db = _build_assign_mock(org_exists=True, valid_slugs={"communication": "comp-001"})
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/assign-assessments",
                json={"professional_ids": [VOL_ID], "competency_slugs": ["unknown_slug"]},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_COMPETENCY"


@pytest.mark.asyncio
async def test_assign_assessments_duplicate_skipped():
    """Existing in-progress session → assignment skipped, no error."""
    db = _build_assign_mock(org_exists=True, existing_session=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/assign-assessments",
                json={"professional_ids": [VOL_ID], "competency_slugs": ["communication"]},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["assigned_count"] == 0
    assert body["skipped_count"] == 1


@pytest.mark.asyncio
async def test_assign_assessments_success():
    db = _build_assign_mock(org_exists=True, existing_session=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/assign-assessments",
                json={"professional_ids": [VOL_ID], "competency_slugs": ["communication"]},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["assigned_count"] == 1
    assert body["skipped_count"] == 0
    assert len(body["assignments"]) == 1


# ── 12. POST /organizations/saved-searches ────────────────────────────────────


def _build_saved_search_create_mock(
    org_exists: bool = True,
    current_count: int = 0,
    duplicate_name: bool = False,
    result_row: dict | None = None,
):
    if result_row is None:
        result_row = SAVED_SEARCH_ROW

    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID} if org_exists else None)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "org_saved_searches":
            async def _exec(*_a, **_kw):
                n = call_counts["org_saved_searches"]
                call_counts["org_saved_searches"] += 1
                if n == 0:
                    # count query
                    return MagicMock(data=[], count=current_count)
                else:
                    # insert
                    if duplicate_name:
                        raise Exception("duplicate key value violates unique constraint")
                    return MagicMock(data=[result_row])
            t.select.return_value = t
            t.eq.return_value = t
            t.insert.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    return db


@pytest.mark.asyncio
async def test_create_saved_search_no_org_404():
    db = _build_saved_search_create_mock(org_exists=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/saved-searches",
                json={"name": "My Search", "filters": {}, "notify_on_match": True},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_saved_search_at_cap_422():
    db = _build_saved_search_create_mock(org_exists=True, current_count=20)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/saved-searches",
                json={"name": "My Search", "filters": {}, "notify_on_match": True},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "SAVED_SEARCH_LIMIT"


@pytest.mark.asyncio
async def test_create_saved_search_duplicate_name_409():
    db = _build_saved_search_create_mock(org_exists=True, current_count=0, duplicate_name=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/saved-searches",
                json={"name": "My Search", "filters": {}, "notify_on_match": True},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "DUPLICATE_NAME"


@pytest.mark.asyncio
async def test_create_saved_search_success():
    db = _build_saved_search_create_mock(org_exists=True, current_count=5)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/organizations/saved-searches",
                json={"name": "Top Engineers", "filters": {"query": "backend"}, "notify_on_match": True},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Top Engineers"
    assert "id" in body


# ── 13. PATCH /organizations/saved-searches/{search_id} ──────────────────────


def _build_patch_search_mock(
    org_exists: bool = True,
    search_exists: bool = True,
    updated_row: dict | None = None,
):
    if updated_row is None:
        updated_row = SAVED_SEARCH_ROW

    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID} if org_exists else None)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "org_saved_searches":
            async def _exec(*_a, **_kw):
                n = call_counts["org_saved_searches"]
                call_counts["org_saved_searches"] += 1
                if n == 0:
                    # ownership check
                    return MagicMock(data=SAVED_SEARCH_ROW if search_exists else None)
                else:
                    # update
                    return MagicMock(data=[updated_row])
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.update.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    return db


@pytest.mark.asyncio
async def test_patch_saved_search_invalid_uuid_422():
    db = _build_patch_search_mock()
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.patch(
                "/api/organizations/saved-searches/not-a-uuid",
                json={"name": "New Name"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_ID"


@pytest.mark.asyncio
async def test_patch_saved_search_no_org_404():
    db = _build_patch_search_mock(org_exists=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.patch(
                f"/api/organizations/saved-searches/{SEARCH_ID}",
                json={"name": "New Name"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"


@pytest.mark.asyncio
async def test_patch_saved_search_not_owned_404():
    db = _build_patch_search_mock(org_exists=True, search_exists=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.patch(
                f"/api/organizations/saved-searches/{SEARCH_ID}",
                json={"name": "New Name"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "SEARCH_NOT_FOUND"


@pytest.mark.asyncio
async def test_patch_saved_search_no_fields_422():
    db = _build_patch_search_mock(org_exists=True, search_exists=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.patch(
                f"/api/organizations/saved-searches/{SEARCH_ID}",
                json={},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "NO_FIELDS"


# ── 14. DELETE /organizations/saved-searches/{search_id} ─────────────────────


def _build_delete_search_mock(org_exists: bool = True, search_exists: bool = True):
    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID} if org_exists else None)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "org_saved_searches":
            async def _exec(*_a, **_kw):
                n = call_counts["org_saved_searches"]
                call_counts["org_saved_searches"] += 1
                if n == 0:
                    return MagicMock(data=SAVED_SEARCH_ROW if search_exists else None)
                else:
                    return MagicMock(data=None)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.delete.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    return db


@pytest.mark.asyncio
async def test_delete_saved_search_invalid_uuid_422():
    db = _build_delete_search_mock()
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.delete(
                "/api/organizations/saved-searches/bad-id",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_ID"


@pytest.mark.asyncio
async def test_delete_saved_search_not_found_404():
    db = _build_delete_search_mock(org_exists=True, search_exists=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.delete(
                f"/api/organizations/saved-searches/{SEARCH_ID}",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "SEARCH_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_saved_search_success():
    db = _build_delete_search_mock(org_exists=True, search_exists=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.delete(
                f"/api/organizations/saved-searches/{SEARCH_ID}",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 204


# ── 15. GET /organizations/saved-searches ────────────────────────────────────


def _build_list_searches_mock(searches: list[dict]):
    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID})
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "org_saved_searches":
            async def _exec(*_a, **_kw):
                return MagicMock(data=searches)
            t.select.return_value = t
            t.eq.return_value = t
            t.order.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    return db


@pytest.mark.asyncio
async def test_list_saved_searches_returns_list():
    db = _build_list_searches_mock([SAVED_SEARCH_ROW])
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/organizations/saved-searches",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["name"] == "Top Engineers"


# ── 16. list_org_talent invalid status ───────────────────────────────────────


def _build_list_talent_mock(org_exists: bool = True):
    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID} if org_exists else None)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)
        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))
        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    return db


@pytest.mark.asyncio
async def test_list_org_talent_invalid_status_422():
    db = _build_list_talent_mock(org_exists=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/organizations/me/professionals?status=invalid_status",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_STATUS"


@pytest.mark.asyncio
async def test_list_org_talent_no_org_404():
    db = _build_list_talent_mock(org_exists=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/organizations/me/professionals",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"


@pytest.mark.parametrize("status", ["assigned", "completed", "in_progress"])
@pytest.mark.asyncio
async def test_list_org_talent_valid_statuses(status: str):
    """All valid status values accepted without 422."""
    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)
        if table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID})
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)
        elif table_name == "assessment_sessions":
            async def _exec(*_a, **_kw):
                return MagicMock(data=[])
            t.select.return_value = t
            t.eq.return_value = t
            t.limit.return_value = t
            t.execute = AsyncMock(side_effect=_exec)
        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))
        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/organizations/me/professionals?status={status}",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == []


# ── 17. search_talent — org role checks ─────────────────────────────────────


def _build_search_talent_mock(is_org_account: bool = True, org_exists: bool = True):
    call_counts: dict[str, int] = {}

    def make_table(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "profiles":
            async def _exec(*_a, **_kw):
                n = call_counts["profiles"]
                call_counts["profiles"] += 1
                if n == 0:
                    return MagicMock(data={"account_type": "organization" if is_org_account else "volunteer"})
                return MagicMock(data=[])
            t.select.return_value = t
            t.eq.return_value = t
            t.in_.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "organizations":
            async def _exec(*_a, **_kw):
                return MagicMock(data={"id": ORG_ID} if org_exists else None)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        elif table_name == "aura_scores":
            async def _exec(*_a, **_kw):
                return MagicMock(data=[])
            t.select.return_value = t
            t.eq.return_value = t
            t.gte.return_value = t
            t.in_.return_value = t
            t.limit.return_value = t
            t.execute = AsyncMock(side_effect=_exec)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table)
    return db


SEARCH_PAYLOAD = {"query": "python developer", "min_aura": 0.0, "limit": 10}


@pytest.mark.asyncio
async def test_search_talent_non_org_account_403():
    db = _build_search_talent_mock(is_org_account=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(NON_ORG_USER_ID)
    try:
        with patch("app.routers.organizations.generate_embedding", new=AsyncMock(side_effect=TimeoutError())):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/organizations/search/professionals",
                    json=SEARCH_PAYLOAD,
                    headers={"Authorization": "Bearer fake"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "ORG_REQUIRED"


@pytest.mark.asyncio
async def test_search_talent_org_account_no_org_row_403():
    db = _build_search_talent_mock(is_org_account=True, org_exists=False)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        with patch("app.routers.organizations.generate_embedding", new=AsyncMock(side_effect=TimeoutError())):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/organizations/search/professionals",
                    json=SEARCH_PAYLOAD,
                    headers={"Authorization": "Bearer fake"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "ORG_REQUIRED"


@pytest.mark.asyncio
async def test_search_talent_empty_query_422():
    db = _build_search_talent_mock(is_org_account=True, org_exists=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        with patch("app.routers.organizations.generate_embedding", new=AsyncMock(side_effect=TimeoutError())):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/organizations/search/professionals",
                    json={"query": "   ", "min_aura": 0.0},
                    headers={"Authorization": "Bearer fake"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "QUERY_REQUIRED"


@pytest.mark.asyncio
async def test_search_talent_empty_results():
    """Valid org + query + no matching professionals → 200 empty list."""
    db = _build_search_talent_mock(is_org_account=True, org_exists=True)
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        with patch("app.routers.organizations.generate_embedding", new=AsyncMock(side_effect=TimeoutError())):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/organizations/search/professionals",
                    json=SEARCH_PAYLOAD,
                    headers={"Authorization": "Bearer fake"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == []
