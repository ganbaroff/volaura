"""Comprehensive unit tests for admin router endpoints.

Covers: stats, overview, events/live, users, org approve/reject (404 paths),
swarm agents/proposals/decide/findings, ghosting-grace.
"""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.middleware.rate_limit import limiter

limiter.enabled = False

ADMIN_USER_ID = str(uuid4())
REGULAR_USER_ID = str(uuid4())
ORG_ID = str(uuid4())


class MockResult:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _admin_profiles_mock(is_admin: bool) -> MagicMock:
    """Return a profiles table mock that gates admin access."""
    m = MagicMock()
    admin_row = {"id": ADMIN_USER_ID, "is_platform_admin": is_admin}
    admin_result = MockResult(data=admin_row if is_admin else None)

    sel = MagicMock()
    sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=admin_result)
    # generic count queries
    count_result = MockResult(data=[], count=5)
    sel.execute = AsyncMock(return_value=count_result)
    sel.gte.return_value.execute = AsyncMock(return_value=count_result)
    sel.gte.return_value.lte.return_value.execute = AsyncMock(return_value=count_result)
    sel.gte.return_value.lte.return_value.gte.return_value.execute = AsyncMock(return_value=count_result)
    sel.order.return_value.range.return_value.execute = AsyncMock(
        return_value=MockResult(
            data=[
                {
                    "id": ADMIN_USER_ID,
                    "username": "admin",
                    "display_name": "Admin",
                    "account_type": "volunteer",
                    "subscription_status": "trial",
                    "is_platform_admin": True,
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            ],
            count=1,
        )
    )
    sel.eq.return_value.order.return_value.range.return_value.execute = AsyncMock(
        return_value=MockResult(data=[], count=0)
    )
    sel.in_.return_value.execute = AsyncMock(
        return_value=MockResult(data=[{"id": REGULAR_USER_ID, "username": "owner"}])
    )
    m.select = MagicMock(return_value=sel)
    return m


def make_full_db(is_admin: bool = True) -> MagicMock:
    """Build a full DB mock covering all tables used by admin endpoints."""
    db = MagicMock()

    profiles_mock = _admin_profiles_mock(is_admin)
    count_5 = MockResult(data=[], count=5)
    count_0 = MockResult(data=[], count=0)
    aura_mock = MockResult(data=[{"total_score": 80.0}, {"total_score": 60.0}])

    def mock_table(name: str) -> MagicMock:
        m = MagicMock()

        if name == "profiles":
            return profiles_mock

        if name == "organizations":
            m.select.return_value.eq.return_value.execute = AsyncMock(return_value=count_5)
            m.select.return_value.is_.return_value.eq.return_value.execute = AsyncMock(return_value=count_5)
            m.select.return_value.is_.return_value.eq.return_value.order.return_value.range.return_value.execute = (
                AsyncMock(
                    return_value=MockResult(
                        data=[
                            {
                                "id": ORG_ID,
                                "name": "Test NGO",
                                "description": None,
                                "website": None,
                                "owner_id": REGULAR_USER_ID,
                                "trust_score": None,
                                "verified_at": None,
                                "is_active": True,
                                "created_at": "2026-01-01T00:00:00+00:00",
                            }
                        ],
                        count=1,
                    )
                )
            )
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"id": ORG_ID})
            )
            m.update.return_value.eq.return_value.execute = AsyncMock(return_value=MockResult(data=[]))
            m.select.return_value.is_.return_value.eq.return_value.execute = AsyncMock(return_value=count_5)
            return m

        if name == "assessment_sessions":
            sel = MagicMock()
            sel.execute = AsyncMock(return_value=count_0)
            sel.eq.return_value.execute = AsyncMock(return_value=count_0)
            sel.eq.return_value.gte.return_value.execute = AsyncMock(return_value=count_0)
            sel.eq.return_value.eq.return_value.gte.return_value.execute = AsyncMock(return_value=count_0)
            sel.gte.return_value.execute = AsyncMock(return_value=count_0)
            sel.in_.return_value.gte.return_value.execute = AsyncMock(return_value=count_0)
            m.select = MagicMock(return_value=sel)
            return m

        if name == "aura_scores":
            sel = MagicMock()
            sel.execute = AsyncMock(return_value=aura_mock)
            sel.gte.return_value.execute = AsyncMock(return_value=count_0)
            m.select = MagicMock(return_value=sel)
            return m

        if name == "grievances":
            sel = MagicMock()
            sel.in_.return_value.execute = AsyncMock(return_value=count_0)
            sel.gte.return_value.execute = AsyncMock(return_value=count_0)
            m.select = MagicMock(return_value=sel)
            return m

        if name == "character_events":
            sel = MagicMock()
            sel.order.return_value.limit.return_value.execute = AsyncMock(
                return_value=MockResult(
                    data=[
                        {
                            "id": str(uuid4()),
                            "source_product": "volaura",
                            "event_type": "assessment_started",
                            "user_id": REGULAR_USER_ID,
                            "created_at": "2026-04-19T10:00:00+00:00",
                            "payload": {"step": 1},
                        }
                    ]
                )
            )
            m.select = MagicMock(return_value=sel)
            return m

        if name == "user_identity_map":
            sel = MagicMock()
            sel.execute = AsyncMock(
                return_value=MockResult(
                    data=[
                        {"shared_user_id": REGULAR_USER_ID, "source_product": "volaura"},
                    ]
                )
            )
            m.select = MagicMock(return_value=sel)
            return m

        # Default fallback
        m.select.return_value.execute = AsyncMock(return_value=count_0)
        return m

    db.table = mock_table
    return db


# ── GET /api/admin/stats ───────────────────────────────────────────────────────


class TestAdminStats:
    @pytest.mark.asyncio
    async def test_stats_returns_200_with_schema(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/stats")
            assert resp.status_code == 200
            body = resp.json()
            assert "total_users" in body
            assert "total_organizations" in body
            assert "pending_org_approvals" in body
            assert "assessments_today" in body
            assert "pending_grievances" in body
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stats_avg_aura_computed(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/stats")
            assert resp.status_code == 200
            body = resp.json()
            # avg of [80.0, 60.0] = 70.0
            assert body["avg_aura_score"] == 70.0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stats_avg_aura_none_when_no_scores(self):
        db = make_full_db()
        # Override aura_scores to return empty
        orig_table = db.table

        def patched_table(name: str):
            if name == "aura_scores":
                m = MagicMock()
                m.select.return_value.execute = AsyncMock(return_value=MockResult(data=[]))
                m.select.return_value.gte.return_value.execute = AsyncMock(return_value=MockResult(data=[], count=0))
                return m
            return orig_table(name)

        db.table = patched_table
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/stats")
            assert resp.status_code == 200
            assert resp.json()["avg_aura_score"] is None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stats_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/stats")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── GET /api/admin/stats/overview ─────────────────────────────────────────────


class TestAdminOverview:
    @pytest.mark.asyncio
    async def test_overview_returns_200_with_schema(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/stats/overview")
            assert resp.status_code == 200
            body = resp.json()
            assert "activation_rate_24h" in body
            assert "dau_wau_ratio" in body
            assert "errors_24h" in body
            assert "presence" in body
            assert "funnels" in body
            assert len(body["funnels"]) == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_overview_runway_from_env(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            with patch.dict(os.environ, {"PLATFORM_RUNWAY_MONTHS": "18.5"}):
                async with make_client() as client:
                    resp = await client.get("/api/admin/stats/overview")
            assert resp.status_code == 200
            assert resp.json()["runway_months"] == 18.5
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_overview_runway_none_when_env_missing(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            env = {k: v for k, v in os.environ.items() if k != "PLATFORM_RUNWAY_MONTHS"}
            with patch.dict(os.environ, env, clear=True):
                async with make_client() as client:
                    resp = await client.get("/api/admin/stats/overview")
            assert resp.status_code == 200
            assert resp.json()["runway_months"] is None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_overview_fail_soft_on_db_error(self):
        db = make_full_db()
        orig_table = db.table

        def exploding_table(name: str):
            if name == "grievances":
                m = MagicMock()
                # Make all select chains raise
                m.select.return_value.gte.return_value.execute = AsyncMock(side_effect=Exception("DB down"))
                m.select.return_value.in_.return_value.execute = AsyncMock(side_effect=Exception("DB down"))
                return m
            return orig_table(name)

        db.table = exploding_table
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/stats/overview")
            # Should not 500 — fail-soft pattern
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_overview_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/stats/overview")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── GET /api/admin/events/live ────────────────────────────────────────────────


class TestAdminEventsLive:
    @pytest.mark.asyncio
    async def test_live_events_returns_list(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/events/live")
            assert resp.status_code == 200
            body = resp.json()
            assert isinstance(body, list)
            assert len(body) == 1
            assert body[0]["product"] == "volaura"
            assert body[0]["event_type"] == "assessment_started"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_live_events_truncates_payload(self):
        db = make_full_db()
        orig_table = db.table

        long_payload = {"key": "x" * 200}

        def patched_table(name: str):
            if name == "character_events":
                m = MagicMock()
                m.select.return_value.order.return_value.limit.return_value.execute = AsyncMock(
                    return_value=MockResult(
                        data=[
                            {
                                "id": str(uuid4()),
                                "source_product": "volaura",
                                "event_type": "test",
                                "user_id": REGULAR_USER_ID,
                                "created_at": "2026-04-19T10:00:00+00:00",
                                "payload": long_payload,
                            }
                        ]
                    )
                )
                return m
            return orig_table(name)

        db.table = patched_table
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/events/live")
            assert resp.status_code == 200
            summary = resp.json()[0]["payload_summary"]
            assert len(summary) <= 120
            assert summary.endswith("...")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_live_events_empty_list_on_db_error(self):
        db = make_full_db()
        orig_table = db.table

        def exploding_table(name: str):
            if name == "character_events":
                m = MagicMock()
                m.select.return_value.order.return_value.limit.return_value.execute = AsyncMock(
                    side_effect=Exception("timeout")
                )
                return m
            return orig_table(name)

        db.table = exploding_table
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/events/live")
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_live_events_limit_param(self):
        db = make_full_db()
        captured = {}
        orig_table = db.table

        def patched_table(name: str):
            if name == "character_events":
                m = MagicMock()

                def fake_limit(n):
                    captured["limit"] = n
                    inner = MagicMock()
                    inner.execute = AsyncMock(return_value=MockResult(data=[]))
                    return inner

                m.select.return_value.order.return_value.limit = fake_limit
                return m
            return orig_table(name)

        db.table = patched_table
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/events/live?limit=10")
            assert resp.status_code == 200
            assert captured["limit"] == 10
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_live_events_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/events/live")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── GET /api/admin/users ──────────────────────────────────────────────────────


class TestAdminUsers:
    @pytest.mark.asyncio
    async def test_users_returns_list(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/users")
            assert resp.status_code == 200
            body = resp.json()
            assert isinstance(body, list)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_users_account_type_filter(self):
        db = make_full_db()
        orig_table = db.table

        captured = {}

        def patched_table(name):
            if name == "profiles":
                m = MagicMock()
                profiles_result = MockResult(data=[], count=0)

                def profiles_select(*args, **kwargs):
                    sel = MagicMock()
                    # admin gate: .eq("id", ...).maybe_single().execute()
                    admin_result = MockResult(data={"id": ADMIN_USER_ID, "is_platform_admin": True})
                    sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=admin_result)

                    # users list with account_type filter:
                    # query chain: .order().range().eq("account_type", val).execute()
                    def fake_order(*args, **kwargs):
                        order_m = MagicMock()

                        def fake_range(*args, **kwargs):
                            range_m = MagicMock()

                            def fake_eq(field, val):
                                if field == "account_type":
                                    captured["account_type"] = val
                                inner = MagicMock()
                                inner.execute = AsyncMock(return_value=profiles_result)
                                return inner

                            range_m.eq = fake_eq
                            range_m.execute = AsyncMock(return_value=profiles_result)
                            return range_m

                        order_m.range = fake_range
                        return order_m

                    sel.order = fake_order
                    return sel

                m.select = profiles_select
                return m
            return orig_table(name)

        db.table = patched_table
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/users?account_type=org_admin")
            assert resp.status_code == 200
            assert captured.get("account_type") == "org_admin"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_users_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/users")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── POST /api/admin/organizations/{id}/approve — 404 path ─────────────────────


class TestOrgApprove404:
    @pytest.mark.asyncio
    async def test_approve_org_not_found_returns_404(self):
        db = make_full_db()
        orig_table = db.table

        def patched_table(name: str):
            if name == "organizations":
                m = MagicMock()
                m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                    return_value=MockResult(data=None)
                )
                return m
            return orig_table(name)

        db.table = patched_table
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.post(f"/api/admin/organizations/{uuid4()}/approve")
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()


# ── POST /api/admin/organizations/{id}/reject — 404 path ──────────────────────


class TestOrgReject404:
    @pytest.mark.asyncio
    async def test_reject_org_not_found_returns_404(self):
        db = make_full_db()
        orig_table = db.table

        def patched_table(name: str):
            if name == "organizations":
                m = MagicMock()
                m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                    return_value=MockResult(data=None)
                )
                return m
            return orig_table(name)

        db.table = patched_table
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with make_client() as client:
                resp = await client.post(f"/api/admin/organizations/{uuid4()}/reject")
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()


# ── GET /api/admin/swarm/agents ───────────────────────────────────────────────


class TestSwarmAgents:
    def _setup_admin(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID

    @pytest.mark.asyncio
    async def test_agents_returns_list_from_file(self):
        self._setup_admin()
        agent_state = {
            "agents": {
                "research-agent": {
                    "status": "idle",
                    "last_task": "market research",
                    "last_run": "2026-04-19T08:00:00",
                    "next_scheduled": None,
                    "blockers": [],
                    "performance": {"tasks_completed": 5, "tasks_failed": 1},
                }
            },
            "_uninitialized_count": 47,
        }
        try:
            with (
                patch(
                    "builtins.open",
                    MagicMock(
                        return_value=MagicMock(
                            __enter__=MagicMock(
                                return_value=MagicMock(read=MagicMock(return_value=json.dumps(agent_state)))
                            ),
                            __exit__=MagicMock(return_value=False),
                        )
                    ),
                ),
                patch("json.load", return_value=agent_state),
            ):
                async with make_client() as client:
                    resp = await client.get("/api/admin/swarm/agents")
            assert resp.status_code == 200
            body = resp.json()
            assert "data" in body
            assert "agents" in body["data"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_agents_file_not_found_returns_empty(self):
        self._setup_admin()
        try:
            with patch("builtins.open", side_effect=FileNotFoundError("no file")):
                async with make_client() as client:
                    resp = await client.get("/api/admin/swarm/agents")
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["agents"] == []
            assert body["data"]["total_tracked"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_agents_json_parse_error_returns_empty(self):
        self._setup_admin()
        try:
            with patch("builtins.open", side_effect=ValueError("bad json")):
                async with make_client() as client:
                    resp = await client.get("/api/admin/swarm/agents")
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["agents"] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_agents_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/swarm/agents")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── GET /api/admin/swarm/proposals ────────────────────────────────────────────


class TestSwarmProposals:
    def _setup_admin(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID

    @pytest.mark.asyncio
    async def test_proposals_returns_list(self):
        self._setup_admin()
        try:
            with patch("builtins.open", side_effect=FileNotFoundError()):
                async with make_client() as client:
                    resp = await client.get("/api/admin/swarm/proposals")
            assert resp.status_code == 200
            body = resp.json()
            assert "data" in body
            assert body["data"]["proposals"] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_proposals_status_filter(self):
        self._setup_admin()
        try:
            with patch("builtins.open", side_effect=FileNotFoundError()):
                async with make_client() as client:
                    resp = await client.get("/api/admin/swarm/proposals?status=pending")
            assert resp.status_code == 200
            # File not found → empty list returned regardless of filter
            assert resp.json()["data"]["proposals"] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_proposals_file_not_found_returns_empty(self):
        self._setup_admin()
        try:
            with patch("builtins.open", side_effect=FileNotFoundError()):
                async with make_client() as client:
                    resp = await client.get("/api/admin/swarm/proposals")
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["proposals"] == []
            assert body["data"]["summary"]["pending"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_proposals_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/swarm/proposals")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── POST /api/admin/swarm/proposals/{id}/decide ────────────────────────────────


class TestSwarmProposalDecide:
    def _setup_admin(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID

    @pytest.mark.asyncio
    async def test_decide_invalid_action_returns_400(self):
        self._setup_admin()
        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/admin/swarm/proposals/p1/decide",
                    json={"action": "delete"},
                )
            assert resp.status_code == 400
            assert resp.json()["detail"]["code"] == "INVALID_ACTION"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_decide_proposal_not_found_returns_404(self):
        self._setup_admin()
        proposals_data = {"proposals": [{"id": "other-id", "status": "pending"}]}
        try:
            with patch("builtins.open", MagicMock()) as mock_open:
                mock_open.return_value.__enter__.return_value = MagicMock()
                with patch("json.load", return_value=proposals_data):
                    async with make_client() as client:
                        resp = await client.post(
                            "/api/admin/swarm/proposals/nonexistent/decide",
                            json={"action": "approve"},
                        )
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "PROPOSAL_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_decide_approve_writes_back(self):
        self._setup_admin()
        proposal_id = "abc123"
        proposals_data = {"proposals": [{"id": proposal_id, "status": "pending", "timestamp": "2026-04-19T09:00:00"}]}
        try:
            with (
                patch("builtins.open", MagicMock()),
                patch("json.load", return_value=proposals_data),
                patch("json.dump"),
                patch("os.replace"),
                patch("tempfile.mkstemp", return_value=(0, "/tmp/fake.json")),
                patch("os.fdopen", return_value=MagicMock().__enter__),
            ):
                async with make_client() as client:
                    resp = await client.post(
                        f"/api/admin/swarm/proposals/{proposal_id}/decide",
                        json={"action": "approve"},
                    )
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["action"] == "approve"
            assert body["data"]["status"] == "approved"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_decide_dismiss_action(self):
        self._setup_admin()
        proposal_id = "xyz789"
        proposals_data = {"proposals": [{"id": proposal_id, "status": "pending", "timestamp": "2026-04-19T09:00:00"}]}
        try:
            with (
                patch("builtins.open", MagicMock()),
                patch("json.load", return_value=proposals_data),
                patch("json.dump"),
                patch("os.replace"),
                patch("tempfile.mkstemp", return_value=(0, "/tmp/fake.json")),
                patch("os.fdopen", return_value=MagicMock().__enter__),
            ):
                async with make_client() as client:
                    resp = await client.post(
                        f"/api/admin/swarm/proposals/{proposal_id}/decide",
                        json={"action": "dismiss"},
                    )
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "rejected"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_decide_defer_action(self):
        self._setup_admin()
        proposal_id = "def456"
        proposals_data = {"proposals": [{"id": proposal_id, "status": "pending", "timestamp": "2026-04-19T09:00:00"}]}
        try:
            with (
                patch("builtins.open", MagicMock()),
                patch("json.load", return_value=proposals_data),
                patch("json.dump"),
                patch("os.replace"),
                patch("tempfile.mkstemp", return_value=(0, "/tmp/fake.json")),
                patch("os.fdopen", return_value=MagicMock().__enter__),
            ):
                async with make_client() as client:
                    resp = await client.post(
                        f"/api/admin/swarm/proposals/{proposal_id}/decide",
                        json={"action": "defer"},
                    )
            assert resp.status_code == 200
            assert resp.json()["data"]["status"] == "deferred"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_decide_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/admin/swarm/proposals/p1/decide",
                    json={"action": "approve"},
                )
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── GET /api/admin/swarm/findings ─────────────────────────────────────────────


class TestSwarmFindings:
    def _setup_admin(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID

    @pytest.mark.asyncio
    async def test_findings_import_error_graceful_fallback(self):
        self._setup_admin()
        # Setting the module to None in sys.modules causes ImportError on `from swarm... import`
        try:
            with patch.dict("sys.modules", {"swarm": None, "swarm.shared_memory": None}):
                async with make_client() as client:
                    resp = await client.get("/api/admin/swarm/findings")
            assert resp.status_code == 200
            body = resp.json()
            assert "data" in body
            assert "findings" in body["data"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_findings_returns_200(self):
        self._setup_admin()
        try:
            # The endpoint does a sys.path manipulation + import; mock the whole inner block
            mock_shared_memory = MagicMock()
            mock_path = MagicMock()
            mock_path.exists.return_value = False  # DB doesn't exist → returns empty

            with patch.dict("sys.modules", {"swarm": MagicMock(), "swarm.shared_memory": mock_shared_memory}):
                mock_shared_memory._DB_PATH = mock_path
                mock_shared_memory.get_all_recent = MagicMock(return_value=[])
                async with make_client() as client:
                    resp = await client.get("/api/admin/swarm/findings")
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_findings_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.get("/api/admin/swarm/findings")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ── POST /api/admin/ghosting-grace/run ────────────────────────────────────────


class TestGhostingGrace:
    def _setup_admin(self):
        db = make_full_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID

    @pytest.mark.asyncio
    async def test_ghosting_grace_returns_summary(self):
        self._setup_admin()
        summary = {
            "candidates": 5,
            "sent": 3,
            "marked": 3,
            "errors": 0,
            "skipped_kill_switch": 0,
        }
        try:
            with patch(
                "app.routers.admin.process_ghosting_grace",
                AsyncMock(return_value=summary),
            ):
                async with make_client() as client:
                    resp = await client.post("/api/admin/ghosting-grace/run")
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["candidates"] == 5
            assert body["data"]["sent"] == 3
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_ghosting_grace_kill_switch_active(self):
        self._setup_admin()
        summary = {
            "candidates": 10,
            "sent": 0,
            "marked": 0,
            "errors": 0,
            "skipped_kill_switch": 10,
        }
        try:
            with patch(
                "app.routers.admin.process_ghosting_grace",
                AsyncMock(return_value=summary),
            ):
                async with make_client() as client:
                    resp = await client.post("/api/admin/ghosting-grace/run")
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["skipped_kill_switch"] == 10
            assert body["data"]["sent"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_ghosting_grace_403_for_non_admin(self):
        db = make_full_db(is_admin=False)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with make_client() as client:
                resp = await client.post("/api/admin/ghosting-grace/run")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()
