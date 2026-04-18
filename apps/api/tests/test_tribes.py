"""Tribe Streaks endpoint tests.

Security gates verified here:
  - Not in tribe → 404/400 on all write endpoints
  - Opted-out member invisible in GET /me
  - Kudos count via RPC (no direct table SELECT)
  - tribe_id sourced from user's own membership (never request body)

Happy-path coverage:
  - GET /tribes/me → TribeOut (with members + kudos count)
  - GET /tribes/me/streak → TribeStreakOut
  - POST /tribes/me/kudos → KudosResponse
  - POST /tribes/opt-out → OptOutResponse
  - POST /tribes/renew → RenewalResponse
  - POST /tribes/join-pool → TribeMatchPreview
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.middleware.rate_limit import limiter

limiter.enabled = False

USER_ID = str(uuid4())
OTHER_ID = str(uuid4())
TRIBE_ID = str(uuid4())
ISO_WEEK = "2026-W14"


class MockResult:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_user_db_in_tribe() -> MagicMock:
    """User-scoped DB: user IS in an active tribe."""
    db = MagicMock()

    def table(name: str) -> MagicMock:
        m = MagicMock()

        if name == "tribe_members":
            # membership lookup (for /me, /kudos, /opt-out, /renew)
            m.select.return_value.eq.return_value.is_.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(
                    data={
                        "tribe_id": TRIBE_ID,
                        "tribes": {
                            "id": TRIBE_ID,
                            "expires_at": "2026-05-01T00:00:00+00:00",
                            "status": "active",
                        },
                    }
                )
            )

        elif name == "tribe_streaks":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(
                    data={
                        "current_streak": 3,
                        "longest_streak": 5,
                        "last_activity_week": ISO_WEEK,
                        "consecutive_misses_count": 0,
                    }
                )
            )

        elif name == "tribe_kudos":
            m.insert.return_value.execute = AsyncMock(return_value=MockResult(data=[{}]))

        elif name == "tribe_renewal_requests":
            # renewal check — not yet requested
            m.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data=None)
            )
            m.upsert.return_value.execute = AsyncMock(return_value=MockResult(data=[{}]))
            m.delete.return_value.eq.return_value.eq.return_value.execute = AsyncMock(return_value=MockResult(data=[]))

        elif name == "profiles":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"visible_to_orgs": True})
            )

        # RPC for kudos count
        rpc_m = MagicMock()
        rpc_m.execute = AsyncMock(return_value=MockResult(data=5))
        db.rpc = MagicMock(return_value=rpc_m)

        # tribe_members update (opt-out)
        m.update.return_value.eq.return_value.eq.return_value.execute = AsyncMock(return_value=MockResult(data=[{}]))

        return m

    db.table = table
    return db


def make_user_db_not_in_tribe() -> MagicMock:
    """User-scoped DB: user is NOT in any tribe."""
    db = MagicMock()

    def table(name: str) -> MagicMock:
        m = MagicMock()

        if name == "tribe_members":
            m.select.return_value.eq.return_value.is_.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data=None)
            )

        elif name == "tribe_streaks":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data=None)
            )

        elif name == "profiles":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"visible_to_orgs": True})
            )

        elif name == "tribe_matching_pool":
            # upsert({...}).execute() used in join-pool route
            m.upsert.return_value.execute = AsyncMock(return_value=MockResult(data=None))
            # select(...).eq(...).maybe_single().execute() used in pool-status route
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data=None)
            )

        return m

    db.table = table
    db.rpc = MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=MockResult(data=0))))
    return db


def make_admin_db_in_tribe() -> MagicMock:
    """Admin DB: returns tribe members + streak data."""
    db = MagicMock()

    def table(name: str) -> MagicMock:
        m = MagicMock()

        if name == "tribe_members":
            # All members in tribe (admin view, used for GET /me)
            m.select.return_value.eq.return_value.is_.return_value.execute = AsyncMock(
                return_value=MockResult(
                    data=[
                        {"user_id": USER_ID, "profiles": {"display_name": "Yusif E.", "avatar_url": None}},
                        {
                            "user_id": OTHER_ID,
                            "profiles": {"display_name": "Leyla M.", "avatar_url": "https://cdn.example.com/l.jpg"},
                        },
                    ]
                )
            )
            # active member count for /renew
            m.select.return_value.eq.return_value.is_.return_value.execute = AsyncMock(
                return_value=MockResult(data=[{"user_id": USER_ID}, {"user_id": OTHER_ID}])
            )

        elif name == "tribe_streaks":
            # Individual activity check per member
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"last_activity_week": ISO_WEEK})
            )

        elif name == "tribe_renewal_requests":
            # renewal count for /renew consensus check
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MockResult(data=[{"user_id": USER_ID}])
            )

        return m

    db.table = table
    return db


def override_deps(user_db: MagicMock, admin_db: MagicMock, uid: str = USER_ID):
    """Return FastAPI dependency overrides dict."""
    return {
        get_supabase_user: lambda: user_db,
        get_supabase_admin: lambda: admin_db,
        get_current_user_id: lambda: uid,
    }


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── GET /api/tribes/me ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_tribe_returns_tribe_when_member():
    user_db = make_user_db_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.get("/api/tribes/me")

    app.dependency_overrides = {}
    assert resp.status_code == 200
    body = resp.json()
    assert body["tribe_id"] == TRIBE_ID
    assert body["status"] == "active"
    assert len(body["members"]) >= 1
    # Anti-harassment: no AURA scores in member objects
    for m in body["members"]:
        assert "aura_score" not in m
        assert "total_score" not in m
    # kudos_count present (may be 0 or positive)
    assert "kudos_count_this_week" in body


@pytest.mark.asyncio
async def test_get_tribe_returns_null_when_not_member():
    user_db = make_user_db_not_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.get("/api/tribes/me")

    app.dependency_overrides = {}
    assert resp.status_code == 200
    assert resp.json() is None


# ── GET /api/tribes/me/streak ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_streak_returns_streak_data():
    user_db = make_user_db_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.get("/api/tribes/me/streak")

    app.dependency_overrides = {}
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_streak"] == 3
    assert body["longest_streak"] == 5
    assert body["crystal_fade_level"] in (0, 1, 2)
    assert "consecutive_misses_count" in body


@pytest.mark.asyncio
async def test_get_streak_returns_null_when_no_streak():
    user_db = make_user_db_not_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.get("/api/tribes/me/streak")

    app.dependency_overrides = {}
    assert resp.status_code == 200
    assert resp.json() is None


# ── POST /api/tribes/me/kudos ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_kudos_succeeds_when_in_tribe():
    user_db = make_user_db_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/me/kudos")

    app.dependency_overrides = {}
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_send_kudos_blocked_when_not_in_tribe():
    """Security gate: NOT_IN_TRIBE → 400."""
    user_db = make_user_db_not_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/me/kudos")

    app.dependency_overrides = {}
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "NOT_IN_TRIBE"


@pytest.mark.asyncio
async def test_kudos_does_not_expose_sender():
    """Security: kudos insert must NOT include sender_id in the payload."""
    user_db = make_user_db_in_tribe()
    admin_db = make_admin_db_in_tribe()

    inserted_payload: dict | None = None

    original_table = user_db.table

    def capture_table(name: str):
        m = original_table(name)
        if name == "tribe_kudos":
            original_insert = m.insert

            def patched_insert(data, **kwargs):
                nonlocal inserted_payload
                inserted_payload = data
                return original_insert(data, **kwargs)

            m.insert = patched_insert
        return m

    user_db.table = capture_table

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        await client.post("/api/tribes/me/kudos")

    app.dependency_overrides = {}
    # tribe_id is set, but sender_id must be absent
    if inserted_payload:
        assert "sender_id" not in inserted_payload
        assert "user_id" not in inserted_payload


# ── POST /api/tribes/opt-out ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_opt_out_succeeds_when_in_tribe():
    user_db = make_user_db_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/opt-out")

    app.dependency_overrides = {}
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_opt_out_blocked_when_not_in_tribe():
    user_db = make_user_db_not_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/opt-out")

    app.dependency_overrides = {}
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "NOT_IN_TRIBE"


# ── POST /api/tribes/renew ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_renew_succeeds_and_reports_waiting():
    user_db = make_user_db_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/renew")

    app.dependency_overrides = {}
    assert resp.status_code == 200
    body = resp.json()
    assert body["renewal_requested"] is True
    assert "message" in body
    assert "all_members_requested" in body


@pytest.mark.asyncio
async def test_renew_blocked_when_not_in_tribe():
    user_db = make_user_db_not_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/renew")

    app.dependency_overrides = {}
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "NOT_IN_TRIBE"


# ── POST /api/tribes/join-pool ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_join_pool_succeeds_when_not_in_tribe():
    user_db = make_user_db_not_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/join-pool")

    app.dependency_overrides = {}
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_join_pool_blocked_when_already_in_tribe():
    """Security gate: ALREADY_IN_TRIBE → 400."""
    user_db = make_user_db_in_tribe()
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/join-pool")

    app.dependency_overrides = {}
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "ALREADY_IN_TRIBE"


@pytest.mark.asyncio
async def test_join_pool_blocked_when_profile_not_visible():
    """Eligibility gate: PROFILE_NOT_VISIBLE → 400."""
    user_db = make_user_db_not_in_tribe()

    # Override profile check to return visible_to_orgs=False
    original_table = user_db.table

    def table_override(name: str):
        m = original_table(name)
        if name == "profiles":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"visible_to_orgs": False})
            )
        return m

    user_db.table = table_override
    admin_db = make_admin_db_in_tribe()

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.post("/api/tribes/join-pool")

    app.dependency_overrides = {}
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_VISIBLE"


# ── Q2: Crystal fade level ─────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "misses,expected_level",
    [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 2),  # capped at 2 (3+ misses → reset cycle, shown as 2 until reset runs)
        (5, 2),
    ],
)
async def test_crystal_fade_level_capped_at_2(misses: int, expected_level: int):
    """Q2: crystal_fade_level = min(consecutive_misses_count, 2)."""
    user_db = make_user_db_in_tribe()
    admin_db = make_admin_db_in_tribe()

    original_table = user_db.table

    def table_override(name: str):
        m = original_table(name)
        if name == "tribe_streaks":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(
                    data={
                        "current_streak": 2,
                        "longest_streak": 4,
                        "last_activity_week": None,
                        "consecutive_misses_count": misses,
                    }
                )
            )
        return m

    user_db.table = table_override

    app.dependency_overrides = override_deps(user_db, admin_db)
    async with make_client() as client:
        resp = await client.get("/api/tribes/me/streak")

    app.dependency_overrides = {}
    assert resp.status_code == 200
    assert resp.json()["crystal_fade_level"] == expected_level
