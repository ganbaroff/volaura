"""HTTP endpoint tests for the Tribes router.

Covers all 9 endpoints:
- GET  /api/tribes/me              — get user's current tribe
- GET  /api/tribes/me/streak       — get personal streak
- POST /api/tribes/me/kudos        — send anonymous kudos
- POST /api/tribes/opt-out         — leave tribe silently
- POST /api/tribes/renew           — request renewal
- POST /api/tribes/join-pool       — join matching pool
- GET  /api/tribes/me/pool-status  — check pool status
- POST /api/tribes/cron/run-matching      — internal cron (secret-gated)
- POST /api/tribes/cron/run-streak-update — internal cron (secret-gated)

Coverage:
- 401 when no auth header
- 200/201 with proper mocks
- 400 NOT_IN_TRIBE, ALREADY_IN_TRIBE, PROFILE_NOT_VISIBLE
- 403 FORBIDDEN on cron endpoints (wrong / missing secret)
- Null returns when tribe/streak not found
- Cron success path via service mock
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── Shared IDs ────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())
TRIBE_ID = str(uuid4())
OTHER_USER_ID = str(uuid4())

AUTH = {"Authorization": "Bearer test-tribes"}
CRON_SECRET = "test-cron-secret-1234"

NOW_ISO = "2026-06-01T10:00:00+00:00"
EXPIRES_ISO = "2026-06-29T10:00:00+00:00"

# ── Fixture rows ──────────────────────────────────────────────────────────────

TRIBE_ROW = {
    "id": TRIBE_ID,
    "status": "active",
    "expires_at": EXPIRES_ISO,
}

MEMBERSHIP_ROW = {
    "tribe_id": TRIBE_ID,
    "tribes": TRIBE_ROW,
}

MEMBER_ROW = {
    "user_id": USER_ID,
    "profiles": {"display_name": "Alice", "avatar_url": None},
}

STREAK_ROW = {
    "user_id": USER_ID,
    "current_streak": 3,
    "longest_streak": 5,
    "last_activity_week": "2026-W22",
    "consecutive_misses_count": 0,
}

STREAK_ACTIVITY_ROW = {
    "last_activity_week": "2026-W22",
}

POOL_ROW = {
    "joined_at": NOW_ISO,
}


# ── Mock helpers ──────────────────────────────────────────────────────────────


def make_chain(data=None, side_effect=None) -> MagicMock:
    """Build a fluent Supabase query chain mock."""
    result = MagicMock()
    result.data = data

    if side_effect:
        execute = AsyncMock(side_effect=side_effect)
    else:
        execute = AsyncMock(return_value=result)

    chain = MagicMock()
    for method in (
        "select",
        "eq",
        "is_",
        "order",
        "limit",
        "update",
        "insert",
        "upsert",
        "delete",
        "maybe_single",
        "single",
    ):
        getattr(chain, method).return_value = chain
    chain.execute = execute
    return chain


def make_rpc_chain(data=None) -> MagicMock:
    """RPC chain: db.rpc(...).execute()"""
    result = MagicMock()
    result.data = data
    rpc = MagicMock()
    rpc.execute = AsyncMock(return_value=result)
    return rpc


def make_db(tables: dict | None = None, rpc_data=None) -> MagicMock:
    """Build a db mock with configurable table and rpc responses."""
    db = MagicMock()
    tables = tables or {}

    def dispatch(name: str) -> MagicMock:
        cfg = tables.get(name, {})
        return make_chain(**cfg)

    db.table.side_effect = dispatch
    db.rpc.return_value = make_rpc_chain(data=rpc_data)
    return db


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def admin_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def user_id_dep(uid: str = USER_ID):
    async def _override():
        return uid

    return _override


# ── Context manager for dependency overrides ──────────────────────────────────


class _DepCtx:
    """Sets dependency_overrides on enter, clears on exit."""

    def __init__(self, db: MagicMock, admin_db: MagicMock | None = None, uid: str = USER_ID):
        self.db = db
        self.admin_db = admin_db if admin_db is not None else db
        self.uid = uid

    def __enter__(self):
        app.dependency_overrides[get_supabase_user] = admin_dep(self.db)
        app.dependency_overrides[get_supabase_admin] = admin_dep(self.admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(self.uid)
        return self

    def __exit__(self, *_):
        app.dependency_overrides.pop(get_supabase_user, None)
        app.dependency_overrides.pop(get_supabase_admin, None)
        app.dependency_overrides.pop(get_current_user_id, None)


# ── Auth helper ───────────────────────────────────────────────────────────────


async def _assert_requires_auth(method: str, path: str) -> None:
    async with make_client() as c:
        r = await getattr(c, method)(path)
    assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/tribes/me
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetMyTribe:
    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("get", "/api/tribes/me")

    @pytest.mark.asyncio
    async def test_returns_null_when_no_membership(self):
        # membership query returns no data
        db = make_db(tables={"tribe_members": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me", headers=AUTH)
        assert r.status_code == 200
        assert r.json() is None

    @pytest.mark.asyncio
    async def test_returns_null_when_tribe_not_active(self):
        inactive_membership = {
            "tribe_id": TRIBE_ID,
            "tribes": {**TRIBE_ROW, "status": "expired"},
        }
        db = make_db(tables={"tribe_members": {"data": inactive_membership}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me", headers=AUTH)
        assert r.status_code == 200
        assert r.json() is None

    @pytest.mark.asyncio
    async def test_returns_tribe_with_members(self):
        # user db: membership query + kudos rpc + renewal check
        user_db = make_db(
            tables={
                "tribe_members": {"data": MEMBERSHIP_ROW},
                "tribe_renewal_requests": {"data": None},
            },
            rpc_data=2,
        )
        # admin db: members list + streak per member
        admin_db = make_db(
            tables={
                "tribe_members": {"data": [MEMBER_ROW]},
                "tribe_streaks": {"data": STREAK_ACTIVITY_ROW},
            }
        )
        with _DepCtx(user_db, admin_db=admin_db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["tribe_id"] == TRIBE_ID
        assert body["status"] == "active"
        assert isinstance(body["members"], list)
        assert body["kudos_count_this_week"] == 2
        assert body["renewal_requested"] is False

    @pytest.mark.asyncio
    async def test_renewal_requested_true(self):
        user_db = make_db(
            tables={
                "tribe_members": {"data": MEMBERSHIP_ROW},
                "tribe_renewal_requests": {"data": {"tribe_id": TRIBE_ID}},
            },
            rpc_data=0,
        )
        admin_db = make_db(
            tables={
                "tribe_members": {"data": [MEMBER_ROW]},
                "tribe_streaks": {"data": None},
            }
        )
        with _DepCtx(user_db, admin_db=admin_db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me", headers=AUTH)
        assert r.status_code == 200
        assert r.json()["renewal_requested"] is True

    @pytest.mark.asyncio
    async def test_kudos_failure_defaults_to_zero(self):
        # rpc raises → kudos_count should be 0 (fail silently)
        user_db = make_db(
            tables={
                "tribe_members": {"data": MEMBERSHIP_ROW},
                "tribe_renewal_requests": {"data": None},
            }
        )
        user_db.rpc.return_value.execute = AsyncMock(side_effect=RuntimeError("rpc fail"))
        admin_db = make_db(
            tables={
                "tribe_members": {"data": [MEMBER_ROW]},
                "tribe_streaks": {"data": None},
            }
        )
        with _DepCtx(user_db, admin_db=admin_db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me", headers=AUTH)
        assert r.status_code == 200
        assert r.json()["kudos_count_this_week"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/tribes/me/streak
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetMyStreak:
    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("get", "/api/tribes/me/streak")

    @pytest.mark.asyncio
    async def test_returns_null_when_no_streak(self):
        db = make_db(tables={"tribe_streaks": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me/streak", headers=AUTH)
        assert r.status_code == 200
        assert r.json() is None

    @pytest.mark.asyncio
    async def test_returns_streak_data(self):
        db = make_db(tables={"tribe_streaks": {"data": STREAK_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me/streak", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["current_streak"] == 3
        assert body["longest_streak"] == 5
        assert body["last_activity_week"] == "2026-W22"
        assert body["consecutive_misses_count"] == 0
        assert body["crystal_fade_level"] == 0

    @pytest.mark.asyncio
    async def test_crystal_fade_level_capped_at_2(self):
        streak_with_misses = {**STREAK_ROW, "consecutive_misses_count": 5}
        db = make_db(tables={"tribe_streaks": {"data": streak_with_misses}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me/streak", headers=AUTH)
        assert r.status_code == 200
        assert r.json()["crystal_fade_level"] == 2

    @pytest.mark.asyncio
    async def test_db_exception_returns_null(self):
        db = make_db(tables={"tribe_streaks": {"side_effect": RuntimeError("db down")}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me/streak", headers=AUTH)
        assert r.status_code == 200
        assert r.json() is None


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/tribes/me/kudos
# ═══════════════════════════════════════════════════════════════════════════════


class TestSendKudos:
    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("post", "/api/tribes/me/kudos")

    @pytest.mark.asyncio
    async def test_400_not_in_tribe(self):
        db = make_db(tables={"tribe_members": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/me/kudos", headers=AUTH)
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "NOT_IN_TRIBE"

    @pytest.mark.asyncio
    async def test_sends_kudos_successfully(self):
        db = make_db(
            tables={
                "tribe_members": {"data": {"tribe_id": TRIBE_ID}},
                "tribe_kudos": {"data": [{"tribe_id": TRIBE_ID}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/me/kudos", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["sent"] is True
        assert "message" in body


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/tribes/opt-out
# ═══════════════════════════════════════════════════════════════════════════════


class TestOptOut:
    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("post", "/api/tribes/opt-out")

    @pytest.mark.asyncio
    async def test_400_not_in_tribe(self):
        db = make_db(tables={"tribe_members": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/opt-out", headers=AUTH)
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "NOT_IN_TRIBE"

    @pytest.mark.asyncio
    async def test_opt_out_success(self):
        db = make_db(
            tables={
                "tribe_members": {"data": {"tribe_id": TRIBE_ID}},
                "tribe_renewal_requests": {"data": None},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/opt-out", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "message" in body


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/tribes/renew
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequestRenewal:
    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("post", "/api/tribes/renew")

    @pytest.mark.asyncio
    async def test_400_not_in_tribe(self):
        db = make_db(tables={"tribe_members": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/renew", headers=AUTH)
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "NOT_IN_TRIBE"

    @pytest.mark.asyncio
    async def test_renewal_partial(self):
        """Only 1 of 3 members requested — waiting message returned."""
        user_db = make_db(tables={"tribe_members": {"data": {"tribe_id": TRIBE_ID}}})
        user_db.table("tribe_renewal_requests").upsert.return_value = make_chain(data=[])
        # admin: 3 active members, 1 renewal
        admin_db = make_db(
            tables={
                "tribe_members": {
                    "data": [{"user_id": USER_ID}, {"user_id": OTHER_USER_ID}, {"user_id": str(uuid4())}]
                },
                "tribe_renewal_requests": {"data": [{"user_id": USER_ID}]},
            }
        )
        with _DepCtx(user_db, admin_db=admin_db):
            async with make_client() as c:
                r = await c.post("/api/tribes/renew", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["renewal_requested"] is True
        assert body["all_members_requested"] is False
        assert "Waiting" in body["message"]

    @pytest.mark.asyncio
    async def test_renewal_all_requested(self):
        """All 2 active members requested — tribe will be renewed."""
        user_db = make_db(tables={"tribe_members": {"data": {"tribe_id": TRIBE_ID}}})
        admin_db = make_db(
            tables={
                "tribe_members": {"data": [{"user_id": USER_ID}, {"user_id": OTHER_USER_ID}]},
                "tribe_renewal_requests": {"data": [{"user_id": USER_ID}, {"user_id": OTHER_USER_ID}]},
            }
        )
        with _DepCtx(user_db, admin_db=admin_db):
            async with make_client() as c:
                r = await c.post("/api/tribes/renew", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["all_members_requested"] is True
        assert "renewed" in body["message"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/tribes/join-pool
# ═══════════════════════════════════════════════════════════════════════════════


class TestJoinPool:
    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("post", "/api/tribes/join-pool")

    @pytest.mark.asyncio
    async def test_400_already_in_tribe(self):
        db = make_db(tables={"tribe_members": {"data": {"tribe_id": TRIBE_ID}}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/join-pool", headers=AUTH)
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "ALREADY_IN_TRIBE"

    @pytest.mark.asyncio
    async def test_400_profile_not_visible(self):
        db = make_db(
            tables={
                "tribe_members": {"data": None},
                "profiles": {"data": {"visible_to_orgs": False}},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/join-pool", headers=AUTH)
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "PROFILE_NOT_VISIBLE"

    @pytest.mark.asyncio
    async def test_400_profile_missing(self):
        db = make_db(
            tables={
                "tribe_members": {"data": None},
                "profiles": {"data": None},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/join-pool", headers=AUTH)
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "PROFILE_NOT_VISIBLE"

    @pytest.mark.asyncio
    async def test_joins_pool_successfully(self):
        db = make_db(
            tables={
                "tribe_members": {"data": None},
                "profiles": {"data": {"visible_to_orgs": True}},
                "tribe_matching_pool": {"data": [{"user_id": USER_ID}]},
            }
        )
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/join-pool", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["in_pool"] is True
        assert "estimated_wait" in body


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/tribes/me/pool-status
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetPoolStatus:
    @pytest.mark.asyncio
    async def test_requires_auth(self):
        await _assert_requires_auth("get", "/api/tribes/me/pool-status")

    @pytest.mark.asyncio
    async def test_not_in_pool(self):
        db = make_db(tables={"tribe_matching_pool": {"data": None}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me/pool-status", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["in_pool"] is False
        assert body["joined_at"] is None

    @pytest.mark.asyncio
    async def test_in_pool_with_joined_at(self):
        db = make_db(tables={"tribe_matching_pool": {"data": POOL_ROW}})
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.get("/api/tribes/me/pool-status", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["in_pool"] is True
        assert body["joined_at"] == NOW_ISO


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/tribes/cron/run-matching
# ═══════════════════════════════════════════════════════════════════════════════


class TestCronRunMatching:
    @pytest.mark.asyncio
    async def test_403_missing_secret(self):
        db = make_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/cron/run-matching")
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_403_wrong_secret(self):
        db = make_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    "/api/tribes/cron/run-matching",
                    headers={"x-cron-secret": "wrong-secret"},
                )
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_200_with_correct_secret(self):
        db = make_db()
        matching_result = {"tribes_created": 2, "users_matched": 6}
        with (
            _DepCtx(db),
            patch("app.config.settings.cron_secret", CRON_SECRET),
            patch(
                "app.routers.tribes.run_tribe_matching",
                new_callable=AsyncMock,
                return_value=matching_result,
            ),
        ):
            async with make_client() as c:
                r = await c.post(
                    "/api/tribes/cron/run-matching",
                    headers={"x-cron-secret": CRON_SECRET},
                )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["tribes_created"] == 2
        assert body["users_matched"] == 6


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/tribes/cron/run-streak-update
# ═══════════════════════════════════════════════════════════════════════════════


class TestCronRunStreakUpdate:
    @pytest.mark.asyncio
    async def test_403_missing_secret(self):
        db = make_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post("/api/tribes/cron/run-streak-update")
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_403_wrong_secret(self):
        db = make_db()
        with _DepCtx(db):
            async with make_client() as c:
                r = await c.post(
                    "/api/tribes/cron/run-streak-update",
                    headers={"x-cron-secret": "bad-secret"},
                )
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_200_with_correct_secret(self):
        db = make_db()
        streak_result = {"members_updated": 12, "streaks_reset": 1}
        with (
            _DepCtx(db),
            patch("app.config.settings.cron_secret", CRON_SECRET),
            patch(
                "app.routers.tribes.update_weekly_streaks",
                new_callable=AsyncMock,
                return_value=streak_result,
            ),
        ):
            async with make_client() as c:
                r = await c.post(
                    "/api/tribes/cron/run-streak-update",
                    headers={"x-cron-secret": CRON_SECRET},
                )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["members_updated"] == 12
        assert body["streaks_reset"] == 1
