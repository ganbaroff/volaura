"""HTTP endpoint tests for /api/organizations router.

Covers key HTTP paths (200/201, 404, 403, 409, 422) using FastAPI
dependency_overrides — no real DB calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_optional_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.middleware.rate_limit import limiter

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
ORG_ID = "bbbbbbbb-0000-0000-0000-000000000002"
VOL_ID = "cccccccc-0000-0000-0000-000000000003"
SEARCH_ID = str(uuid4())
AUTH_HEADERS = {"Authorization": "Bearer test-token"}

ORG_ROW = {
    "id": ORG_ID,
    "name": "Test Org",
    "description": "A test organization",
    "website": "https://example.com",
    "logo_url": None,
    "contact_email": "org@example.com",
    "type": "ngo",
    "is_active": True,
    "verified_at": None,
    "subscription_tier": None,
    "trust_score": None,
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
    "owner_id": USER_ID,
}

SAVED_SEARCH_ROW = {
    "id": SEARCH_ID,
    "org_id": ORG_ID,
    "name": "Top Engineers",
    "filters": {"query": "engineer", "min_aura": 0.0},
    "notify_on_match": True,
    "last_checked_at": "2026-01-01T00:00:00+00:00",
    "created_at": "2026-01-01T00:00:00+00:00",
}

INTRO_ROW = {
    "id": str(uuid4()),
    "org_id": USER_ID,
    "volunteer_id": VOL_ID,
    "project_name": "Health Initiative",
    "timeline": "normal",
    "message": "Join us",
    "status": "pending",
    "created_at": "2026-01-01T00:00:00+00:00",
}


# ── Rate-limiter reset ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter._storage.reset()
    yield
    limiter._storage.reset()


# ── Mock helpers ───────────────────────────────────────────────────────────────


def make_chain(data=None, count=None, side_effect=None):
    result = MagicMock()
    result.data = data if data is not None else []
    result.count = count
    execute = AsyncMock(side_effect=side_effect) if side_effect else AsyncMock(return_value=result)
    chain = MagicMock()
    for method in (
        "select",
        "eq",
        "order",
        "limit",
        "gte",
        "in_",
        "maybe_single",
        "insert",
        "update",
        "delete",
        "not_",
    ):
        getattr(chain, method).return_value = chain
    chain.execute = execute
    return chain


def make_db(tables=None):
    """Return a mock DB where each table name maps to a make_chain config dict."""
    db = MagicMock()
    tables = tables or {}

    def dispatch(name):
        cfg = tables.get(name, {})
        return make_chain(**cfg)

    db.table.side_effect = dispatch
    return db


def admin_dep(db):
    async def _override():
        yield db

    return _override


def user_dep(db):
    async def _override():
        yield db

    return _override


def uid_dep(uid=USER_ID):
    async def _override():
        return uid

    return _override


def optional_uid_dep(uid=None):
    async def _override():
        return uid

    return _override


def make_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ══════════════════════════════════════════════════════════════════════════════
# 1. GET /api/organizations
# ══════════════════════════════════════════════════════════════════════════════


class TestListOrganizations:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        db = make_db({"organizations": {"data": []}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_optional_user_id] = optional_uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations")
            assert r.status_code == 200
            assert r.json() == []
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_optional_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_org_list(self):
        db = make_db({"organizations": {"data": [ORG_ROW]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_optional_user_id] = optional_uid_dep(USER_ID)
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations")
            assert r.status_code == 200
            body = r.json()
            assert len(body) == 1
            assert body[0]["name"] == "Test Org"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_optional_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_multiple_orgs(self):
        second = {**ORG_ROW, "id": str(uuid4()), "name": "Second Org"}
        db = make_db({"organizations": {"data": [ORG_ROW, second]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_optional_user_id] = optional_uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations")
            assert r.status_code == 200
            assert len(r.json()) == 2
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_optional_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 2. GET /api/organizations/me
# ══════════════════════════════════════════════════════════════════════════════


class TestGetMyOrganization:
    @pytest.mark.asyncio
    async def test_returns_404_when_no_org(self):
        db = make_db({"organizations": {"data": None}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me", headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_my_org(self):
        db = make_db({"organizations": {"data": ORG_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["id"] == ORG_ID
            assert r.json()["name"] == "Test Org"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 3. POST /api/organizations
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateOrganization:
    PAYLOAD = {"name": "New Org", "description": "An org", "website": "https://neworg.com"}

    @pytest.mark.asyncio
    async def test_creates_org_201(self):
        admin_db = make_db({"organizations": {"data": []}})
        user_db = make_db({"organizations": {"data": [ORG_ROW]}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 201
            assert r.json()["name"] == "Test Org"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_409_when_org_exists(self):
        admin_db = make_db({"organizations": {"data": [ORG_ROW]}})
        user_db = make_db({})
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 409
            assert r.json()["detail"]["code"] == "ORG_EXISTS"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_500_when_insert_fails(self):
        admin_db = make_db({"organizations": {"data": []}})
        # user_db insert returns empty data -> triggers 500
        user_db = make_db({"organizations": {"data": []}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 500
            assert r.json()["detail"]["code"] == "CREATE_FAILED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_for_short_name(self):
        admin_db = make_db({"organizations": {"data": []}})
        user_db = make_db({})
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations", json={"name": "X"}, headers=AUTH_HEADERS)
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 4. PUT /api/organizations/me
# ══════════════════════════════════════════════════════════════════════════════


class TestUpdateMyOrganization:
    @pytest.mark.asyncio
    async def test_returns_422_no_fields(self):
        user_db = make_db({})
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.put("/api/organizations/me", json={}, headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "NO_FIELDS"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_org_not_found(self):
        user_db = make_db({"organizations": {"data": []}})
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.put("/api/organizations/me", json={"name": "Updated"}, headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_updates_org_200(self):
        updated = {**ORG_ROW, "name": "Updated Org"}
        user_db = make_db({"organizations": {"data": [updated]}})
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.put("/api/organizations/me", json={"name": "Updated Org"}, headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["name"] == "Updated Org"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 5. GET /api/organizations/{org_id}
# ══════════════════════════════════════════════════════════════════════════════


class TestGetOrganizationById:
    @pytest.mark.asyncio
    async def test_returns_org_200(self):
        db = make_db({"organizations": {"data": ORG_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_optional_user_id] = optional_uid_dep()
        try:
            async with make_client() as c:
                r = await c.get(f"/api/organizations/{ORG_ID}")
            assert r.status_code == 200
            assert r.json()["id"] == ORG_ID
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_optional_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self):
        db = make_db({"organizations": {"data": None}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_optional_user_id] = optional_uid_dep()
        try:
            async with make_client() as c:
                r = await c.get(f"/api/organizations/{ORG_ID}")
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_optional_user_id, None)

    @pytest.mark.asyncio
    async def test_public_access_no_auth(self):
        db = make_db({"organizations": {"data": ORG_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_optional_user_id] = optional_uid_dep()
        try:
            async with make_client() as c:
                r = await c.get(f"/api/organizations/{ORG_ID}")
            assert r.status_code == 200
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_optional_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 6. GET /api/organizations/{org_id}/collective-aura
# ══════════════════════════════════════════════════════════════════════════════


class TestCollectiveAura:
    def _make_multi_table_db(self, org_data, sessions_data=None, aura_data=None):
        """Build a multi-table-aware mock for collective-aura endpoint."""
        org_chain = make_chain(data=org_data)
        sessions_chain = make_chain(data=sessions_data or [])
        aura_chain = make_chain(data=aura_data or [])

        table_map = {
            "organizations": org_chain,
            "assessment_sessions": sessions_chain,
            "aura_scores": aura_chain,
        }

        db = MagicMock()
        db.table.side_effect = lambda name: table_map.get(name, make_chain())
        return db

    @pytest.mark.asyncio
    async def test_returns_403_when_not_owner(self):
        db = self._make_multi_table_db(org_data=None)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get(f"/api/organizations/{ORG_ID}/collective-aura", headers=AUTH_HEADERS)
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "NOT_ORG_OWNER"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_200_empty_count_no_sessions(self):
        db = self._make_multi_table_db(org_data={"id": ORG_ID}, sessions_data=[])
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get(f"/api/organizations/{ORG_ID}/collective-aura", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["org_id"] == ORG_ID
            assert body["count"] == 0
            assert body["avg_aura"] is None
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_200_with_aura_scores(self):
        sessions = [{"volunteer_id": VOL_ID}]
        aura_rows = [{"volunteer_id": VOL_ID, "total_score": 80.0}]
        db = self._make_multi_table_db(org_data={"id": ORG_ID}, sessions_data=sessions, aura_data=aura_rows)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get(f"/api/organizations/{ORG_ID}/collective-aura", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["count"] == 1
            assert body["avg_aura"] == 80.0
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 7. GET /api/organizations/me/dashboard
# ══════════════════════════════════════════════════════════════════════════════


class TestOrgDashboard:
    @pytest.mark.asyncio
    async def test_returns_404_when_no_org(self):
        db = MagicMock()

        def dispatch(name):
            return make_chain(data=None)

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me/dashboard", headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_200_empty_sessions(self):
        org_chain = make_chain(data={"id": ORG_ID, "name": "Test Org"})
        sessions_chain = make_chain(data=[])

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            return sessions_chain

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me/dashboard", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["org_id"] == ORG_ID
            assert body["total_assigned"] == 0
            assert body["total_completed"] == 0
            assert body["completion_rate"] == 0.0
            assert body["avg_aura_score"] is None
            assert body["top_professionals"] == []
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_200_with_completion_rate(self):
        org_chain = make_chain(data={"id": ORG_ID, "name": "Test Org"})
        sessions = [
            {"volunteer_id": VOL_ID, "status": "completed"},
            {"volunteer_id": VOL_ID, "status": "assigned"},
        ]
        sessions_chain = make_chain(data=sessions)
        aura_chain = make_chain(data=[])
        comp_sessions_chain = make_chain(data=[])

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            elif name == "assessment_sessions":
                call_seq["n"] += 1
                return sessions_chain if call_seq["n"] == 1 else comp_sessions_chain
            elif name == "aura_scores":
                return aura_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me/dashboard", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["total_assigned"] == 2
            assert body["total_completed"] == 1
            assert body["completion_rate"] == 0.5
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 8. GET /api/organizations/me/professionals
# ══════════════════════════════════════════════════════════════════════════════


class TestListOrgProfessionals:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        org_chain = make_chain(data={"id": ORG_ID})
        sessions_chain = make_chain(data=[])

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            return sessions_chain

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me/professionals", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json() == []
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_no_org(self):
        org_chain = make_chain(data=None)

        db = MagicMock()
        db.table.side_effect = lambda name: org_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me/professionals", headers=AUTH_HEADERS)
            assert r.status_code == 404
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_status(self):
        org_chain = make_chain(data={"id": ORG_ID})

        db = MagicMock()
        db.table.side_effect = lambda name: org_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me/professionals?status=invalid", headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "INVALID_STATUS"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_professionals_with_scores(self):
        org_chain = make_chain(data={"id": ORG_ID})
        sessions_chain = make_chain(data=[{"volunteer_id": VOL_ID, "status": "completed"}])
        profiles_chain = make_chain(data=[{"id": VOL_ID, "username": "john", "display_name": "John"}])
        aura_chain = make_chain(data=[{"volunteer_id": VOL_ID, "total_score": 75.0, "badge_tier": "gold"}])

        table_map = {
            "organizations": org_chain,
            "assessment_sessions": sessions_chain,
            "profiles": profiles_chain,
            "aura_scores": aura_chain,
        }

        db = MagicMock()
        db.table.side_effect = lambda name: table_map.get(name, make_chain())
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/me/professionals", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert len(body) == 1
            assert body[0]["username"] == "john"
            assert body[0]["overall_score"] == 75.0
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 9. GET /api/organizations/saved-searches
# ══════════════════════════════════════════════════════════════════════════════


class TestListSavedSearches:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        org_chain = make_chain(data={"id": ORG_ID})
        searches_chain = make_chain(data=[])

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            return searches_chain

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/saved-searches", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json() == []
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_saved_searches(self):
        org_chain = make_chain(data={"id": ORG_ID})
        searches_chain = make_chain(data=[SAVED_SEARCH_ROW])

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            return searches_chain

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/saved-searches", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert len(body) == 1
            assert body[0]["name"] == "Top Engineers"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_no_org(self):
        org_chain = make_chain(data=None)

        db = MagicMock()
        db.table.side_effect = lambda name: org_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.get("/api/organizations/saved-searches", headers=AUTH_HEADERS)
            assert r.status_code == 404
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 10. POST /api/organizations/saved-searches
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateSavedSearch:
    PAYLOAD = {
        "name": "Top Engineers",
        "filters": {"query": "engineer", "min_aura": 50.0},
        "notify_on_match": True,
    }

    @pytest.mark.asyncio
    async def test_creates_saved_search_201(self):
        org_chain = make_chain(data={"id": ORG_ID})
        count_chain = make_chain(data=[], count=0)
        insert_chain = make_chain(data=[SAVED_SEARCH_ROW])

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            elif name == "org_saved_searches":
                call_seq["n"] += 1
                # first call = count, second = insert
                return count_chain if call_seq["n"] == 1 else insert_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/saved-searches", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 201
            assert r.json()["name"] == "Top Engineers"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_when_cap_reached(self):
        org_chain = make_chain(data={"id": ORG_ID})
        count_chain = make_chain(data=[], count=20)

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            return count_chain

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/saved-searches", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "SAVED_SEARCH_LIMIT"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_409_on_duplicate_name(self):
        org_chain = make_chain(data={"id": ORG_ID})
        count_chain = make_chain(data=[], count=0)

        call_seq = {"n": 0}

        db = MagicMock()

        insert_chain = make_chain(side_effect=Exception("duplicate key value violates unique constraint"))

        def dispatch(name):
            if name == "organizations":
                return org_chain
            elif name == "org_saved_searches":
                call_seq["n"] += 1
                return count_chain if call_seq["n"] == 1 else insert_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/saved-searches", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 409
            assert r.json()["detail"]["code"] == "DUPLICATE_NAME"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_no_org(self):
        org_chain = make_chain(data=None)

        db = MagicMock()
        db.table.side_effect = lambda name: org_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/saved-searches", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 404
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 11. PATCH /api/organizations/saved-searches/{search_id}
# ══════════════════════════════════════════════════════════════════════════════


class TestUpdateSavedSearch:
    @pytest.mark.asyncio
    async def test_updates_saved_search_200(self):
        org_chain = make_chain(data={"id": ORG_ID})
        ownership_chain = make_chain(data=SAVED_SEARCH_ROW)
        updated_row = {**SAVED_SEARCH_ROW, "name": "Updated Name"}
        update_chain = make_chain(data=[updated_row])

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            elif name == "org_saved_searches":
                call_seq["n"] += 1
                # first = ownership check, second = update
                return ownership_chain if call_seq["n"] == 1 else update_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.patch(
                    f"/api/organizations/saved-searches/{SEARCH_ID}",
                    json={"name": "Updated Name"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 200
            assert r.json()["name"] == "Updated Name"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_uuid(self):
        org_chain = make_chain(data={"id": ORG_ID})

        db = MagicMock()
        db.table.side_effect = lambda name: org_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.patch(
                    "/api/organizations/saved-searches/not-a-uuid",
                    json={"name": "Updated"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "INVALID_ID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_no_fields(self):
        org_chain = make_chain(data={"id": ORG_ID})
        ownership_chain = make_chain(data=SAVED_SEARCH_ROW)

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            return ownership_chain

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.patch(
                    f"/api/organizations/saved-searches/{SEARCH_ID}",
                    json={},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "NO_FIELDS"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_search_not_found(self):
        org_chain = make_chain(data={"id": ORG_ID})
        ownership_chain = make_chain(data=None)

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            return ownership_chain

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.patch(
                    f"/api/organizations/saved-searches/{SEARCH_ID}",
                    json={"name": "Updated"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "SEARCH_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 12. DELETE /api/organizations/saved-searches/{search_id}
# ══════════════════════════════════════════════════════════════════════════════


class TestDeleteSavedSearch:
    @pytest.mark.asyncio
    async def test_deletes_saved_search_204(self):
        org_chain = make_chain(data={"id": ORG_ID})
        ownership_chain = make_chain(data=SAVED_SEARCH_ROW)
        delete_chain = make_chain(data=[])

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            elif name == "org_saved_searches":
                call_seq["n"] += 1
                if call_seq["n"] == 1:
                    return ownership_chain
                return delete_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.delete(f"/api/organizations/saved-searches/{SEARCH_ID}", headers=AUTH_HEADERS)
            assert r.status_code == 204
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_uuid(self):
        org_chain = make_chain(data={"id": ORG_ID})

        db = MagicMock()
        db.table.side_effect = lambda name: org_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.delete("/api/organizations/saved-searches/bad-id", headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "INVALID_ID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_search_not_found(self):
        org_chain = make_chain(data={"id": ORG_ID})
        ownership_chain = make_chain(data=None)

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            return ownership_chain

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.delete(f"/api/organizations/saved-searches/{SEARCH_ID}", headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "SEARCH_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 13. POST /api/organizations/intro-requests
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateIntroRequest:
    PAYLOAD = {
        "professional_id": VOL_ID,
        "project_name": "Health Initiative",
        "timeline": "normal",
        "message": "Join us",
    }

    ORG_CALLER_ROW = {
        "account_type": "organization",
        "display_name": "Test Org",
        "username": "testorg",
    }

    TARGET_ROW = {
        "id": VOL_ID,
        "display_name": "Jane Doe",
        "username": "janedoe",
        "visible_to_orgs": True,
        "account_type": "volunteer",
    }

    @pytest.mark.asyncio
    async def test_creates_intro_request_201(self):
        caller_chain = make_chain(data=self.ORG_CALLER_ROW)
        target_chain = make_chain(data=self.TARGET_ROW)
        intro_chain = make_chain(data=[INTRO_ROW])

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "profiles":
                call_seq["n"] += 1
                return caller_chain if call_seq["n"] == 1 else target_chain
            elif name == "intro_requests":
                return intro_chain
            return make_chain()

        db.table.side_effect = dispatch

        with patch("app.services.notification_service.notify", new_callable=AsyncMock):
            app.dependency_overrides[get_supabase_admin] = admin_dep(db)
            app.dependency_overrides[get_current_user_id] = uid_dep()
            try:
                async with make_client() as c:
                    r = await c.post("/api/organizations/intro-requests", json=self.PAYLOAD, headers=AUTH_HEADERS)
                assert r.status_code == 201
                assert r.json()["status"] == "pending"
            finally:
                app.dependency_overrides.pop(get_supabase_admin, None)
                app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_403_when_not_org_account(self):
        caller_chain = make_chain(data={"account_type": "volunteer", "display_name": "Jane"})

        db = MagicMock()
        db.table.side_effect = lambda name: caller_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/intro-requests", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "ORG_REQUIRED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_404_when_professional_not_found(self):
        caller_chain = make_chain(data=self.ORG_CALLER_ROW)
        target_chain = make_chain(data=None)

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "profiles":
                call_seq["n"] += 1
                return caller_chain if call_seq["n"] == 1 else target_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/intro-requests", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "PROFILE_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_403_when_professional_not_discoverable(self):
        caller_chain = make_chain(data=self.ORG_CALLER_ROW)
        target_chain = make_chain(data={**self.TARGET_ROW, "visible_to_orgs": False})

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "profiles":
                call_seq["n"] += 1
                return caller_chain if call_seq["n"] == 1 else target_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/intro-requests", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "NOT_DISCOVERABLE"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_when_target_is_org_account(self):
        caller_chain = make_chain(data=self.ORG_CALLER_ROW)
        target_chain = make_chain(data={**self.TARGET_ROW, "account_type": "organization", "visible_to_orgs": True})

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "profiles":
                call_seq["n"] += 1
                return caller_chain if call_seq["n"] == 1 else target_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/intro-requests", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "INVALID_TARGET"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_409_on_duplicate_request(self):
        caller_chain = make_chain(data=self.ORG_CALLER_ROW)
        target_chain = make_chain(data=self.TARGET_ROW)
        intro_chain = make_chain(side_effect=Exception("unique constraint violation"))

        call_seq = {"n": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "profiles":
                call_seq["n"] += 1
                return caller_chain if call_seq["n"] == 1 else target_chain
            elif name == "intro_requests":
                return intro_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/intro-requests", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 409
            assert r.json()["detail"]["code"] == "REQUEST_ALREADY_PENDING"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_invalid_timeline(self):
        db = MagicMock()
        db.table.side_effect = lambda name: make_chain()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post(
                    "/api/organizations/intro-requests",
                    json={**self.PAYLOAD, "timeline": "yesterday"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 14. POST /api/organizations/search/professionals
# ══════════════════════════════════════════════════════════════════════════════


class TestSearchProfessionals:
    PAYLOAD = {"query": "experienced engineer", "min_aura": 0.0}

    def _make_search_db(self, caller_data, org_data, rpc_data=None):
        """Build mock for search/professionals — caller check + org check + rpc."""
        caller_chain = make_chain(data=caller_data)
        org_chain = make_chain(data=org_data)
        rpc_chain = make_chain(data=rpc_data or [])

        call_seq = {"profiles": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "profiles":
                call_seq["profiles"] += 1
                return caller_chain
            elif name == "organizations":
                return org_chain
            elif name == "aura_scores":
                return make_chain(data=[])
            return make_chain()

        db.table.side_effect = dispatch
        db.rpc = MagicMock(return_value=rpc_chain)
        return db

    @pytest.mark.asyncio
    async def test_returns_403_when_not_org_account(self):
        db = self._make_search_db(caller_data={"account_type": "volunteer"}, org_data={"id": ORG_ID})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/search/professionals", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "ORG_REQUIRED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_403_when_no_org_row(self):
        db = self._make_search_db(caller_data={"account_type": "organization"}, org_data=None)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/search/professionals", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "ORG_REQUIRED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_for_empty_query(self):
        db = self._make_search_db(caller_data={"account_type": "organization"}, org_data={"id": ORG_ID})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/search/professionals", json={"query": "   "}, headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "QUERY_REQUIRED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_results(self):
        db = self._make_search_db(
            caller_data={"account_type": "organization"},
            org_data={"id": ORG_ID},
            rpc_data=[],
        )

        with patch("app.routers.organizations.generate_embedding", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = None  # triggers fallback path

            app.dependency_overrides[get_supabase_admin] = admin_dep(db)
            app.dependency_overrides[get_current_user_id] = uid_dep()
            try:
                async with make_client() as c:
                    r = await c.post("/api/organizations/search/professionals", json=self.PAYLOAD, headers=AUTH_HEADERS)
                assert r.status_code == 200
                assert r.json() == []
            finally:
                app.dependency_overrides.pop(get_supabase_admin, None)
                app.dependency_overrides.pop(get_current_user_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# 15. POST /api/organizations/assign-assessments
# ══════════════════════════════════════════════════════════════════════════════


class TestAssignAssessments:
    PAYLOAD = {
        "professional_ids": [VOL_ID],
        "competency_slugs": ["communication"],
        "deadline_days": 14,
    }

    @pytest.mark.asyncio
    async def test_returns_403_when_no_org(self):
        org_chain = make_chain(data=None)

        db = MagicMock()
        db.table.side_effect = lambda name: org_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/assign-assessments", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "NOT_ORG_OWNER"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_competency_slug(self):
        org_chain = make_chain(data={"id": ORG_ID, "name": "Test Org"})
        comp_chain = make_chain(data=[])  # no matching competencies

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            elif name == "competencies":
                return comp_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/assign-assessments", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "INVALID_COMPETENCY"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_assigns_successfully(self):
        org_chain = make_chain(data={"id": ORG_ID, "name": "Test Org"})
        comp_chain = make_chain(data=[{"slug": "communication", "id": str(uuid4())}])
        prof_chain = make_chain(data=[{"id": VOL_ID}])
        existing_chain = make_chain(data=[])  # no existing session
        insert_chain = make_chain(data=[{"id": str(uuid4())}])

        call_seq = {"sessions": 0}

        db = MagicMock()

        def dispatch(name):
            if name == "organizations":
                return org_chain
            elif name == "competencies":
                return comp_chain
            elif name == "profiles":
                return prof_chain
            elif name == "assessment_sessions":
                call_seq["sessions"] += 1
                return existing_chain if call_seq["sessions"] == 1 else insert_chain
            return make_chain()

        db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/assign-assessments", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["assigned_count"] == 1
            assert body["skipped_count"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_skips_duplicate_assignments(self):
        org_chain = make_chain(data={"id": ORG_ID, "name": "Test Org"})
        comp_chain = make_chain(data=[{"slug": "communication", "id": str(uuid4())}])
        prof_chain = make_chain(data=[{"id": VOL_ID}])
        existing_chain = make_chain(data=[{"id": str(uuid4())}])  # already assigned

        table_map = {
            "organizations": org_chain,
            "competencies": comp_chain,
            "profiles": prof_chain,
            "assessment_sessions": existing_chain,
        }
        db = MagicMock()
        db.table.side_effect = lambda name: table_map.get(name, make_chain())
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post("/api/organizations/assign-assessments", json=self.PAYLOAD, headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["assigned_count"] == 0
            assert body["skipped_count"] == 1
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_slug_format(self):
        db = MagicMock()
        db.table.side_effect = lambda name: make_chain()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = uid_dep()
        try:
            async with make_client() as c:
                r = await c.post(
                    "/api/organizations/assign-assessments",
                    json={**self.PAYLOAD, "competency_slugs": ["Invalid Slug!"]},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
