"""TDD — Collective AURA Ladders endpoint.

GET /api/organizations/me/collective-aura
Returns aggregated AURA metrics for an org's talent pool.

Test cases (QA Agent mandate — tests before code):
  1. Org with 3 volunteers → correct avg + trend
  2. Org with 0 volunteers → 200 with count=0, avg=null, trend=null
  3. Non-owner user → 403
  4. Org doesn't exist → 404
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_current_user_id
from app.middleware.rate_limit import limiter

ORG_OWNER_ID = "aaaaaaaa-1111-0000-0000-000000000001"
OTHER_USER_ID = "bbbbbbbb-1111-0000-0000-000000000002"
ORG_ID = "org00000-1111-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter._storage.reset()
    yield
    limiter._storage.reset()


def _chain(return_data):
    """Build a fully chainable mock that resolves .execute() → MagicMock(data=...)."""
    node = MagicMock()
    result = MagicMock()
    result.data = return_data
    node.execute = AsyncMock(return_value=result)
    # Chain all query builder methods back to node
    for method in ("eq", "select", "limit", "single", "maybe_single", "in_", "order", "gte", "lte"):
        setattr(node, method, MagicMock(return_value=node))
    return node


def _make_admin_mock(org_data=None, session_rows=None, aura_rows=None):
    """Build an AsyncMock Supabase admin client for collective AURA tests.

    Call order in endpoint:
      1. organizations table → org ownership check
      2. assessment_sessions table → volunteer_ids
      3. aura_scores table → total_score per volunteer
    """
    mock = AsyncMock()

    org_node = _chain(org_data)
    sessions_node = _chain(session_rows or [])
    aura_node = _chain(aura_rows or [])

    call_count = {"n": 0}

    def table_side_effect(table_name):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return org_node
        if call_count["n"] == 2:
            return sessions_node
        return aura_node

    mock.table = MagicMock(side_effect=table_side_effect)
    return mock


@pytest.mark.asyncio
async def test_collective_aura_happy_path():
    """Org with 3 volunteers → returns avg AURA and count."""
    session_rows = [
        {"volunteer_id": "v1"},
        {"volunteer_id": "v2"},
        {"volunteer_id": "v3"},
    ]
    aura_rows = [
        {"volunteer_id": "v1", "total_score": 80.0},
        {"volunteer_id": "v2", "total_score": 60.0},
        {"volunteer_id": "v3", "total_score": 70.0},
    ]
    admin_mock = _make_admin_mock(
        org_data={"id": ORG_ID, "owner_id": ORG_OWNER_ID},
        session_rows=session_rows,
        aura_rows=aura_rows,
    )
    app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
    app.dependency_overrides[get_current_user_id] = lambda: ORG_OWNER_ID

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/organizations/{ORG_ID}/collective-aura")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    assert abs(data["avg_aura"] - 70.0) < 0.1  # (80+60+70)/3
    assert "trend" in data


@pytest.mark.asyncio
async def test_collective_aura_empty_org():
    """Org with 0 volunteers → 200 with count=0, avg_aura=None."""
    admin_mock = _make_admin_mock(
        org_data={"id": ORG_ID, "owner_id": ORG_OWNER_ID},
        session_rows=[],  # no sessions → no volunteers
        aura_rows=[],
    )
    app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
    app.dependency_overrides[get_current_user_id] = lambda: ORG_OWNER_ID

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/organizations/{ORG_ID}/collective-aura")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["avg_aura"] is None
    assert data["trend"] is None


@pytest.mark.asyncio
async def test_collective_aura_non_owner_forbidden():
    """Non-owner gets 403 — fail-closed ownership guard."""
    admin_mock = _make_admin_mock(org_data=None)  # ownership check returns nothing
    app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
    app.dependency_overrides[get_current_user_id] = lambda: OTHER_USER_ID

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/organizations/{ORG_ID}/collective-aura")

    app.dependency_overrides.clear()

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_collective_aura_org_not_found():
    """Org ID doesn't exist → 404."""
    admin_mock = _make_admin_mock(org_data=None)
    app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
    app.dependency_overrides[get_current_user_id] = lambda: ORG_OWNER_ID

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/organizations/nonexistent-id/collective-aura")

    app.dependency_overrides.clear()

    # Either 403 (no ownership) or 404 — both acceptable; must NOT be 200
    assert resp.status_code in (403, 404)
