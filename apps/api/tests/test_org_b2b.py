"""QA-03 — Org B2B test coverage.

Covers the 3 endpoints with zero prior test coverage:
  1. GET /api/organizations/me/dashboard  → OrgDashboardStats
  2. GET /api/organizations/me/volunteers → list[OrgVolunteerRow]
  3. POST /api/organizations/search/volunteers → list[VolunteerSearchResult]

All tests use dependency_overrides + AsyncMock (same pattern as test_intro_request.py).
No real DB connections. Self-contained.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_current_user_id
from app.middleware.rate_limit import limiter


# ── Constants ─────────────────────────────────────────────────────────────────

ORG_USER_ID = "aaaaaaaa-1111-0000-0000-000000000001"
ORG_ID = "org00000-1111-0000-0000-000000000001"
VOL_ID_1 = "vol00001-1111-0000-0000-000000000001"
VOL_ID_2 = "vol00002-1111-0000-0000-000000000002"
VOL_ID_3 = "vol00003-1111-0000-0000-000000000003"
NON_ORG_USER_ID = "cccccccc-1111-0000-0000-000000000001"


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Prevent test cross-contamination via in-memory rate limiter."""
    limiter._storage.reset()
    yield
    limiter._storage.reset()


def _admin_override(db):
    async def _dep():
        yield db
    return _dep


def _uid_override(uid: str):
    async def _dep():
        return uid
    return _dep


# ── Dashboard helpers ─────────────────────────────────────────────────────────

def _build_dashboard_mock(
    org_exists: bool = True,
    sessions: list[dict] | None = None,
    aura_rows: list[dict] | None = None,
    profiles: list[dict] | None = None,
):
    """
    Build a mock DB for GET /api/organizations/me/dashboard.

    DB call sequence in get_org_dashboard:
      1. organizations → select owner's org (maybe_single)
      2. assessment_sessions → select sessions (assigned_by_org_id)
      3. aura_scores → select scores for completed volunteers (if any)
      4. profiles → select top volunteer profiles (if any)
      5. assessment_sessions → count completed per volunteer (if any)
    """
    if sessions is None:
        sessions = []
    if aura_rows is None:
        aura_rows = []
    if profiles is None:
        profiles = []

    org_row = {"id": ORG_ID, "name": "Test Org"} if org_exists else None

    # Counters to sequence same-table calls
    table_call_counts: dict[str, int] = {}

    def make_table_mock(table_name: str) -> MagicMock:
        t = MagicMock()
        table_call_counts.setdefault(table_name, 0)

        if table_name == "organizations":
            async def _execute(*_a, **_kw):
                return MagicMock(data=org_row)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        elif table_name == "assessment_sessions":
            async def _execute(*_a, **_kw):
                n = table_call_counts["assessment_sessions"]
                table_call_counts["assessment_sessions"] += 1
                # Call 0: get all sessions for org
                # Call 1: get completed sessions for comp count
                return MagicMock(data=sessions if n == 0 else [s for s in sessions if s.get("status") == "completed"])
            t.select.return_value = t
            t.eq.return_value = t
            t.limit.return_value = t  # SEC-Q4: .limit(_DASHBOARD_SESSION_CAP) added to call 0
            t.execute = AsyncMock(side_effect=_execute)

        elif table_name == "aura_scores":
            async def _execute(*_a, **_kw):
                return MagicMock(data=aura_rows)
            t.select.return_value = t
            t.in_.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        elif table_name == "profiles":
            async def _execute(*_a, **_kw):
                return MagicMock(data=profiles)
            t.select.return_value = t
            t.in_.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table_mock)
    return db


# ── Dashboard tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_org_dashboard_returns_stats_for_active_org():
    """Happy path: org with 2 completed volunteers → correct stats in response."""
    sessions = [
        {"volunteer_id": VOL_ID_1, "status": "completed"},
        {"volunteer_id": VOL_ID_2, "status": "completed"},
        {"volunteer_id": VOL_ID_3, "status": "assigned"},
    ]
    aura_rows = [
        {"volunteer_id": VOL_ID_1, "total_score": 82.0, "badge_tier": "gold"},
        {"volunteer_id": VOL_ID_2, "total_score": 65.0, "badge_tier": "silver"},
    ]
    profiles = [
        {"id": VOL_ID_1, "username": "alice", "display_name": "Alice A"},
        {"id": VOL_ID_2, "username": "bob", "display_name": "Bob B"},
    ]

    db = _build_dashboard_mock(
        org_exists=True,
        sessions=sessions,
        aura_rows=aura_rows,
        profiles=profiles,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/organizations/me/dashboard",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Schema field presence
    assert body["org_id"] == ORG_ID
    assert body["org_name"] == "Test Org"
    assert body["total_assigned"] == 3
    assert body["total_completed"] == 2
    assert body["completion_rate"] == pytest.approx(0.667, abs=0.001)
    assert body["avg_aura_score"] == pytest.approx(73.5, abs=0.1)

    # Badge distribution
    bd = body["badge_distribution"]
    assert bd["gold"] == 1
    assert bd["silver"] == 1
    assert bd["platinum"] == 0

    # Top volunteers populated
    assert len(body["top_volunteers"]) == 2
    top_usernames = {v["username"] for v in body["top_volunteers"]}
    assert "alice" in top_usernames


@pytest.mark.asyncio
async def test_org_dashboard_empty_org():
    """Org has no volunteers yet — all counts 0, no 404."""
    db = _build_dashboard_mock(org_exists=True, sessions=[], aura_rows=[], profiles=[])

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/organizations/me/dashboard",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_assigned"] == 0
    assert body["total_completed"] == 0
    assert body["completion_rate"] == 0.0
    assert body["avg_aura_score"] is None
    assert body["top_volunteers"] == []
    assert body["badge_distribution"]["platinum"] == 0


@pytest.mark.asyncio
async def test_org_dashboard_no_org_returns_404():
    """User has no organization row → 404 ORG_NOT_FOUND (not 500)."""
    db = _build_dashboard_mock(org_exists=False)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/organizations/me/dashboard",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"


# ── Volunteer list helpers ────────────────────────────────────────────────────

def _build_volunteers_mock(
    org_exists: bool = True,
    sessions: list[dict] | None = None,
    profiles: list[dict] | None = None,
    aura_rows: list[dict] | None = None,
):
    """
    Build a mock DB for GET /api/organizations/me/volunteers.

    DB call sequence in list_org_volunteers:
      1. organizations → owner org lookup (maybe_single)
      2. assessment_sessions → sessions for org (with optional status filter)
      3. profiles → volunteer profiles (.in_)
      4. aura_scores → volunteer AURA scores (.in_)
    """
    if sessions is None:
        sessions = []
    if profiles is None:
        profiles = []
    if aura_rows is None:
        aura_rows = []

    org_row = {"id": ORG_ID} if org_exists else None

    def make_table_mock(table_name: str) -> MagicMock:
        t = MagicMock()

        if table_name == "organizations":
            async def _execute(*_a, **_kw):
                return MagicMock(data=org_row)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        elif table_name == "assessment_sessions":
            async def _execute(*_a, **_kw):
                return MagicMock(data=sessions)
            t.select.return_value = t
            t.eq.return_value = t
            t.limit.return_value = t  # SEC-Q4: .limit(_LIST_SESSION_CAP) added to query
            t.execute = AsyncMock(side_effect=_execute)

        elif table_name == "profiles":
            async def _execute(*_a, **_kw):
                return MagicMock(data=profiles)
            t.select.return_value = t
            t.in_.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        elif table_name == "aura_scores":
            async def _execute(*_a, **_kw):
                return MagicMock(data=aura_rows)
            t.select.return_value = t
            t.in_.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table_mock)
    return db


# ── Volunteer list tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_org_volunteers_returns_paginated_results():
    """Org with 3 volunteers → returns rows with profile + AURA data."""
    sessions = [
        {"volunteer_id": VOL_ID_1, "status": "completed"},
        {"volunteer_id": VOL_ID_2, "status": "completed"},
        {"volunteer_id": VOL_ID_3, "status": "assigned"},
    ]
    profiles = [
        {"id": VOL_ID_1, "username": "alice", "display_name": "Alice A"},
        {"id": VOL_ID_2, "username": "bob", "display_name": "Bob B"},
        {"id": VOL_ID_3, "username": "charlie", "display_name": "Charlie C"},
    ]
    aura_rows = [
        {"volunteer_id": VOL_ID_1, "total_score": 82.0, "badge_tier": "gold"},
        {"volunteer_id": VOL_ID_2, "total_score": 65.0, "badge_tier": "silver"},
    ]

    db = _build_volunteers_mock(
        org_exists=True,
        sessions=sessions,
        profiles=profiles,
        aura_rows=aura_rows,
    )

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/organizations/me/volunteers",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert isinstance(body, list)
    assert len(body) == 3

    # Verify OrgVolunteerRow schema fields present
    row = body[0]
    assert "volunteer_id" in row
    assert "username" in row
    assert "competencies_completed" in row

    # alice has score 82 — should appear (sort: high score first)
    usernames = [r["username"] for r in body]
    assert "alice" in usernames
    assert "bob" in usernames
    assert "charlie" in usernames


@pytest.mark.asyncio
async def test_list_org_volunteers_empty():
    """Org with no assigned volunteers → 200 with empty list (not 500)."""
    db = _build_volunteers_mock(org_exists=True, sessions=[], profiles=[], aura_rows=[])

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/organizations/me/volunteers",
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    assert resp.json() == []


# ── Search helpers ────────────────────────────────────────────────────────────

def _build_search_mock(
    is_org_account: bool = True,
    org_exists: bool = True,
    aura_rows: list[dict] | None = None,
    visibility_ids: list[str] | None = None,
    profiles: list[dict] | None = None,
    embedding_timeout: bool = False,
):
    """
    Build a mock DB for POST /api/organizations/search/volunteers.

    DB call sequence (rule-based fallback path):
      1. profiles → caller account_type check (maybe_single)
      2. organizations → org ownership check (maybe_single)
      3. aura_scores → rule-based filter (.gte, .eq, .limit)
      4. aura_scores → public visibility post-filter (.eq("visibility","public").in_)
      5. profiles → enrich volunteer profiles (.in_)
    """
    if aura_rows is None:
        aura_rows = [
            {"volunteer_id": VOL_ID_1, "total_score": 75.0, "badge_tier": "gold", "elite_status": False},
        ]
    if visibility_ids is None:
        visibility_ids = [r["volunteer_id"] for r in aura_rows]
    if profiles is None:
        profiles = [{"id": VOL_ID_1, "username": "alice", "display_name": "Alice A", "location": "Baku", "languages": ["az", "en"]}]

    caller_profile = (
        {"account_type": "organization"}
        if is_org_account
        else {"account_type": "volunteer"}
    )
    org_row = {"id": ORG_ID} if org_exists else None

    # Track call counts per table to sequence them correctly
    table_call_counts: dict[str, int] = {}

    def make_table_mock(table_name: str) -> MagicMock:
        t = MagicMock()
        table_call_counts.setdefault(table_name, 0)

        if table_name == "profiles":
            async def _execute(*_a, **_kw):
                n = table_call_counts["profiles"]
                table_call_counts["profiles"] += 1
                if n == 0:
                    # First call: caller account_type check (maybe_single)
                    return MagicMock(data=caller_profile if is_org_account else caller_profile)
                else:
                    # Later calls: enrich volunteer profiles (.in_)
                    return MagicMock(data=profiles)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.in_.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        elif table_name == "organizations":
            async def _execute(*_a, **_kw):
                return MagicMock(data=org_row)
            t.select.return_value = t
            t.eq.return_value = t
            t.maybe_single.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        elif table_name == "aura_scores":
            async def _execute(*_a, **_kw):
                n = table_call_counts["aura_scores"]
                table_call_counts["aura_scores"] += 1
                if n == 0:
                    # Rule-based filter
                    return MagicMock(data=aura_rows)
                else:
                    # Visibility post-filter
                    return MagicMock(data=[{"volunteer_id": vid} for vid in visibility_ids])
            t.select.return_value = t
            t.eq.return_value = t
            t.gte.return_value = t
            t.in_.return_value = t
            t.limit.return_value = t
            t.execute = AsyncMock(side_effect=_execute)

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table_mock)
    return db


SEARCH_PAYLOAD = {"query": "experienced communicator", "min_aura": 0.0, "limit": 10}


# ── Search tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_volunteers_rule_based_fallback():
    """Embedding service times out → rule-based fallback returns results (not 500).

    Patches generate_embedding to raise asyncio.TimeoutError.
    The endpoint catches this and proceeds with rule-based filtering.
    """
    db = _build_search_mock(is_org_account=True, org_exists=True)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)
    try:
        with patch(
            "app.routers.organizations.generate_embedding",
            new=AsyncMock(side_effect=asyncio.TimeoutError()),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/organizations/search/volunteers",
                    json=SEARCH_PAYLOAD,
                    headers={"Authorization": "Bearer fake"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    # Rule-based fallback should return results (1 volunteer in mock)
    assert len(body) >= 1
    result = body[0]
    # Verify VolunteerSearchResult schema fields
    assert "volunteer_id" in result
    assert "username" in result
    assert "overall_score" in result
    assert "badge_tier" in result
    assert "elite_status" in result


@pytest.mark.asyncio
async def test_search_volunteers_requires_org():
    """Non-org account calls search → 403 ORG_REQUIRED."""
    db = _build_search_mock(is_org_account=False)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(NON_ORG_USER_ID)
    try:
        with patch(
            "app.routers.organizations.generate_embedding",
            new=AsyncMock(return_value=None),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/organizations/search/volunteers",
                    json=SEARCH_PAYLOAD,
                    headers={"Authorization": "Bearer fake"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "ORG_REQUIRED"
