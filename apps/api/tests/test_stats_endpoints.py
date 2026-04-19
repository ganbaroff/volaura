"""HTTP-level integration tests for /api/stats router.

Covers:
- GET /api/stats/public  — no auth, public counts + avg AURA
- GET /api/stats/beta-funnel — auth + org-only guard
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app

ORG_USER_ID = str(uuid4())
PRO_USER_ID = str(uuid4())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MockResult:
    def __init__(self, data=None, count: int | None = None):
        self.data = data
        self.count = count


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _make_admin_db(
    *,
    profiles_count: int = 10,
    sessions_count: int = 5,
    completed_count: int = 3,
    abandoned_count: int = 1,
    events_count: int = 7,
    aura_rpc_data: float | None = 72.5,
    aura_scores_count: int = 4,
    caller_account_type: str = "organization",
) -> MagicMock:
    """Build a minimal admin DB mock covering all stats router table accesses."""
    db = MagicMock()

    def mock_table(name: str) -> MagicMock:
        m = MagicMock()

        if name == "profiles":
            sel = MagicMock()
            # caller profile lookup: .select("account_type").eq(...).maybe_single().execute()
            sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"account_type": caller_account_type})
            )
            # count all profiles
            sel.execute = AsyncMock(return_value=MockResult(data=[], count=profiles_count))
            m.select = MagicMock(return_value=sel)
            return m

        if name == "assessment_sessions":
            sel = MagicMock()
            # .eq("status", "completed").execute() → completed count
            completed_result = MockResult(data=[], count=completed_count)
            # .eq("status", "in_progress").lt("updated_at", ...).execute() → abandoned
            abandoned_result = MockResult(data=[], count=abandoned_count)
            # plain .execute() → started count
            started_result = MockResult(data=[], count=sessions_count)

            sel.execute = AsyncMock(return_value=started_result)
            sel.eq.return_value.execute = AsyncMock(return_value=completed_result)
            sel.eq.return_value.lt.return_value.execute = AsyncMock(return_value=abandoned_result)
            m.select = MagicMock(return_value=sel)
            return m

        if name == "events":
            sel = MagicMock()
            sel.execute = AsyncMock(return_value=MockResult(data=[], count=events_count))
            sel.neq.return_value.execute = AsyncMock(return_value=MockResult(data=[], count=events_count))
            m.select = MagicMock(return_value=sel)
            return m

        if name == "aura_scores":
            sel = MagicMock()
            sel.execute = AsyncMock(return_value=MockResult(data=[], count=aura_scores_count))
            m.select = MagicMock(return_value=sel)
            return m

        # fallback
        m.select.return_value.execute = AsyncMock(return_value=MockResult(data=[], count=0))
        return m

    db.table = mock_table

    # RPC for avg_aura_score
    rpc_result = MockResult(data=aura_rpc_data)
    db.rpc.return_value.execute = AsyncMock(return_value=rpc_result)

    return db


# ---------------------------------------------------------------------------
# GET /api/stats/public
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_stats_happy_path():
    db = _make_admin_db(
        profiles_count=10,
        sessions_count=5,
        completed_count=3,
        events_count=7,
        aura_rpc_data=72.5,
    )
    app.dependency_overrides[get_supabase_admin] = lambda: db
    try:
        async with make_client() as client:
            resp = await client.get("/api/stats/public")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_professionals"] == 10
        assert body["total_assessments"] == 3
        assert body["total_events"] == 7
        assert body["avg_aura_score"] == 72.5
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_stats_response_schema_keys():
    db = _make_admin_db()
    app.dependency_overrides[get_supabase_admin] = lambda: db
    try:
        async with make_client() as client:
            resp = await client.get("/api/stats/public")
        assert resp.status_code == 200
        keys = set(resp.json().keys())
        assert keys == {"total_professionals", "total_assessments", "total_events", "avg_aura_score"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_stats_zero_aura_when_rpc_returns_none():
    db = _make_admin_db(aura_rpc_data=None)
    app.dependency_overrides[get_supabase_admin] = lambda: db
    try:
        async with make_client() as client:
            resp = await client.get("/api/stats/public")
        assert resp.status_code == 200
        assert resp.json()["avg_aura_score"] == 0.0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_stats_fails_soft_when_profiles_db_errors():
    """DB errors on individual tables must not 500 — endpoint degrades gracefully."""
    db = _make_admin_db()
    orig_table = db.table

    def exploding_table(name: str):
        if name == "profiles":
            m = MagicMock()
            sel = MagicMock()
            sel.execute = AsyncMock(side_effect=Exception("connection reset"))
            # caller lookup must still work for public endpoint (no auth needed)
            sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(side_effect=Exception("connection reset"))
            m.select = MagicMock(return_value=sel)
            return m
        return orig_table(name)

    db.table = exploding_table
    app.dependency_overrides[get_supabase_admin] = lambda: db
    try:
        async with make_client() as client:
            resp = await client.get("/api/stats/public")
        assert resp.status_code == 200
        # professionals falls back to 0 on error
        assert resp.json()["total_professionals"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_stats_fails_soft_when_rpc_errors():
    db = _make_admin_db()
    db.rpc.return_value.execute = AsyncMock(side_effect=Exception("rpc unavailable"))
    app.dependency_overrides[get_supabase_admin] = lambda: db
    try:
        async with make_client() as client:
            resp = await client.get("/api/stats/public")
        assert resp.status_code == 200
        assert resp.json()["avg_aura_score"] == 0.0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_stats_no_auth_required():
    """Public endpoint must not require Authorization header."""
    db = _make_admin_db()
    app.dependency_overrides[get_supabase_admin] = lambda: db
    try:
        async with make_client() as client:
            # explicitly omit auth header
            resp = await client.get("/api/stats/public")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/stats/beta-funnel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_beta_funnel_happy_path_org_user():
    db = _make_admin_db(
        profiles_count=20,
        sessions_count=10,
        completed_count=6,
        abandoned_count=2,
        aura_scores_count=5,
        caller_account_type="organization",
    )
    app.dependency_overrides[get_supabase_admin] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: ORG_USER_ID
    try:
        async with make_client() as client:
            resp = await client.get(
                "/api/stats/beta-funnel",
                headers={"Authorization": f"Bearer fake-token-{ORG_USER_ID}"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["sessions_started"] == 10
        assert body["sessions_completed"] == 6
        assert body["sessions_abandoned"] == 2
        assert body["registrations"] == 20
        assert body["aura_scores_generated"] == 5
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_beta_funnel_response_schema_keys():
    db = _make_admin_db(caller_account_type="organization")
    app.dependency_overrides[get_supabase_admin] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: ORG_USER_ID
    try:
        async with make_client() as client:
            resp = await client.get(
                "/api/stats/beta-funnel",
                headers={"Authorization": "Bearer fake-token"},
            )
        assert resp.status_code == 200
        keys = set(resp.json().keys())
        expected = {
            "sessions_started",
            "sessions_completed",
            "sessions_abandoned",
            "completion_rate",
            "abandonment_rate",
            "registrations",
            "aura_scores_generated",
        }
        assert keys == expected
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_beta_funnel_completion_rate_computed():
    # started=10, completed=4 → rate=0.4
    db = _make_admin_db(
        sessions_count=10,
        completed_count=4,
        abandoned_count=1,
        caller_account_type="organization",
    )
    app.dependency_overrides[get_supabase_admin] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: ORG_USER_ID
    try:
        async with make_client() as client:
            resp = await client.get(
                "/api/stats/beta-funnel",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["completion_rate"] == pytest.approx(0.4, abs=0.001)
        assert body["abandonment_rate"] == pytest.approx(0.1, abs=0.001)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_beta_funnel_zero_division_when_no_sessions():
    """If started=0 completion_rate and abandonment_rate must be 0.0 (no ZeroDivisionError)."""
    db = _make_admin_db(
        sessions_count=0,
        completed_count=0,
        abandoned_count=0,
        caller_account_type="organization",
    )
    app.dependency_overrides[get_supabase_admin] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: ORG_USER_ID
    try:
        async with make_client() as client:
            resp = await client.get(
                "/api/stats/beta-funnel",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["completion_rate"] == 0.0
        assert body["abandonment_rate"] == 0.0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_beta_funnel_401_when_no_auth_header():
    """No Authorization header → 401 from get_supabase_user / get_current_user_id."""
    # We don't override get_current_user_id so the real dep fires
    db = _make_admin_db(caller_account_type="organization")
    app.dependency_overrides[get_supabase_admin] = lambda: db
    try:
        async with make_client() as client:
            resp = await client.get("/api/stats/beta-funnel")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_beta_funnel_403_for_professional_account():
    """Non-org account_type must be rejected with 403."""
    db = _make_admin_db(caller_account_type="professional")
    app.dependency_overrides[get_supabase_admin] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: PRO_USER_ID
    try:
        async with make_client() as client:
            resp = await client.get(
                "/api/stats/beta-funnel",
                headers={"Authorization": "Bearer fake-token"},
            )
        assert resp.status_code == 403
        body = resp.json()
        assert body["detail"]["code"] == "FORBIDDEN"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_beta_funnel_403_for_volunteer_account():
    db = _make_admin_db(caller_account_type="volunteer")
    app.dependency_overrides[get_supabase_admin] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: PRO_USER_ID
    try:
        async with make_client() as client:
            resp = await client.get(
                "/api/stats/beta-funnel",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_beta_funnel_403_when_profile_missing():
    """If caller profile row is absent, default to 'professional' → 403."""
    db = _make_admin_db()
    orig_table = db.table

    def patched_table(name: str):
        if name == "profiles":
            m = MagicMock()
            sel = MagicMock()
            # no profile row → data=None
            sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=MockResult(data=None))
            sel.execute = AsyncMock(return_value=MockResult(data=[], count=0))
            m.select = MagicMock(return_value=sel)
            return m
        return orig_table(name)

    db.table = patched_table
    app.dependency_overrides[get_supabase_admin] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: PRO_USER_ID
    try:
        async with make_client() as client:
            resp = await client.get(
                "/api/stats/beta-funnel",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_beta_funnel_degrades_gracefully_when_assessment_sessions_errors():
    """DB errors on sub-queries must not 500 — funnel counts fall back to 0."""
    db = _make_admin_db(caller_account_type="organization")
    orig_table = db.table

    def exploding_table(name: str):
        if name == "assessment_sessions":
            m = MagicMock()
            sel = MagicMock()
            sel.execute = AsyncMock(side_effect=Exception("timeout"))
            sel.eq.return_value.execute = AsyncMock(side_effect=Exception("timeout"))
            sel.eq.return_value.lt.return_value.execute = AsyncMock(side_effect=Exception("timeout"))
            m.select = MagicMock(return_value=sel)
            return m
        return orig_table(name)

    db.table = exploding_table
    app.dependency_overrides[get_supabase_admin] = lambda: db
    app.dependency_overrides[get_current_user_id] = lambda: ORG_USER_ID
    try:
        async with make_client() as client:
            resp = await client.get(
                "/api/stats/beta-funnel",
                headers={"Authorization": "Bearer fake"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["sessions_started"] == 0
        assert body["sessions_completed"] == 0
    finally:
        app.dependency_overrides.clear()
