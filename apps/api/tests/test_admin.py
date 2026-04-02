"""Admin panel endpoint tests.

Security-focused: every test verifies the fail-closed gate.
Pattern: non-admin user → 403. Admin user → expected data.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_current_user_id
from app.middleware.rate_limit import limiter

limiter.enabled = False

ADMIN_USER_ID = str(uuid4())
REGULAR_USER_ID = str(uuid4())
ORG_ID = str(uuid4())


class MockResult:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


def make_admin_db(is_admin: bool = True) -> MagicMock:
    """Build a mock admin DB that returns is_platform_admin based on the flag."""
    db = MagicMock()

    def mock_table(name: str) -> MagicMock:
        m = MagicMock()

        if name == "profiles":
            admin_result = MockResult(data={"is_platform_admin": is_admin} if is_admin else None)
            users_result = MockResult(
                data=[{
                    "id": ADMIN_USER_ID,
                    "username": "yusif",
                    "display_name": "Yusif E.",
                    "account_type": "volunteer",
                    "subscription_status": "trial",
                    "is_platform_admin": True,
                    "created_at": "2026-01-01T00:00:00+00:00",
                }],
                count=1,
            )
            # owner username lookup via .in_()
            username_result = MockResult(data=[{"id": REGULAR_USER_ID, "username": "testowner"}])

            def profiles_select(*args, **kwargs):
                sel = MagicMock()
                # is_platform_admin check: .eq().maybe_single().execute()
                sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=admin_result)
                # users list: .order().range().execute() or .eq().order().range().execute()
                sel.order.return_value.range.return_value.execute = AsyncMock(return_value=users_result)
                sel.eq.return_value.order.return_value.range.return_value.execute = AsyncMock(return_value=users_result)
                # username lookup: .in_().execute()
                sel.in_.return_value.execute = AsyncMock(return_value=username_result)
                # stats count: .execute()
                sel.execute = AsyncMock(return_value=MockResult(data=[], count=1))
                return sel

            m.select = profiles_select

        elif name == "organizations":
            pending_result = MockResult(data=[
                {
                    "id": ORG_ID,
                    "name": "Test NGO",
                    "description": "A test org",
                    "website": None,
                    "owner_id": REGULAR_USER_ID,
                    "trust_score": None,
                    "verified_at": None,
                    "is_active": True,
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            ], count=1)
            m.select.return_value.is_.return_value.eq.return_value.order.return_value.range.return_value.execute = AsyncMock(
                return_value=pending_result
            )
            # org existence check for approve/reject
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"id": ORG_ID})
            )
            m.update.return_value.eq.return_value.execute = AsyncMock(
                return_value=MockResult(data=[])
            )
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MockResult(data=[], count=0)
            )

        elif name == "assessment_sessions":
            m.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute = AsyncMock(
                return_value=MockResult(data=[], count=0)
            )

        elif name == "aura_scores":
            m.select.return_value.execute = AsyncMock(
                return_value=MockResult(data=[{"total_score": 72.5}])
            )

        return m

    db.table = mock_table
    return db


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── Gate: non-admin is blocked ────────────────────────────────────────────────

class TestAdminGate:
    """All admin endpoints return 403 for non-admin users (fail-closed)."""

    @pytest.mark.asyncio
    async def test_ping_non_admin_returns_403(self):
        db = make_admin_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/ping")
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NOT_PLATFORM_ADMIN"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_users_non_admin_returns_403(self):
        db = make_admin_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/users")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_org_approve_non_admin_returns_403(self):
        db = make_admin_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.post(f"/api/admin/organizations/{ORG_ID}/approve")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── Happy path: admin access ──────────────────────────────────────────────────

class TestAdminHappyPath:

    @pytest.mark.asyncio
    async def test_ping_admin_returns_200(self):
        db = make_admin_db(is_admin=True)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/ping")
            assert resp.status_code == 200
            assert resp.json()["ok"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_pending_orgs_returns_list(self):
        db = make_admin_db(is_admin=True)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/organizations/pending")
            assert resp.status_code == 200
            body = resp.json()
            assert isinstance(body, list)
            assert body[0]["name"] == "Test NGO"
            assert body[0]["verified_at"] is None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_approve_org_returns_200(self):
        db = make_admin_db(is_admin=True)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.post(f"/api/admin/organizations/{ORG_ID}/approve")
            assert resp.status_code == 200
            body = resp.json()
            assert body["action"] == "approved"
            assert body["org_id"] == ORG_ID
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_reject_org_returns_200(self):
        db = make_admin_db(is_admin=True)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.post(f"/api/admin/organizations/{ORG_ID}/reject")
            assert resp.status_code == 200
            body = resp.json()
            assert body["action"] == "rejected"
        finally:
            app.dependency_overrides.clear()
