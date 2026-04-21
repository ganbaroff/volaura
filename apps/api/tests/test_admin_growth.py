"""Tests for GET /api/admin/growth — AdminGrowthFunnel endpoint (M2, 2026-04-18).

Schema tests for AdminGrowthFunnel are also here to keep growth feature coverage
together. If test_admin_schemas.py exists it can import the class-level tests separately.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.middleware.rate_limit import limiter
from app.schemas.admin import AdminGrowthFunnel

limiter.enabled = False

ADMIN_USER_ID = str(uuid4())
REGULAR_USER_ID = str(uuid4())


# ── Helpers ───────────────────────────────────────────────────────────────────


class MockResult:
    def __init__(self, data=None, count: int | None = None):
        self.data = data
        self.count = count


def _make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _make_admin_check_mock(is_admin: bool) -> MagicMock:
    """Minimal profiles mock that satisfies PlatformAdminId dep."""
    m = MagicMock()
    m.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=MockResult(data={"is_platform_admin": is_admin} if is_admin else None)
    )
    return m


def _make_growth_db(
    signups: int = 10,
    profiles: int = 8,
    started: int = 6,
    completed: int = 4,
    aura: int = 3,
    raise_on: str | None = None,
) -> MagicMock:
    """Build a mock SupabaseAdmin that returns configurable counts for the growth endpoint.

    Args:
        raise_on: table name that should raise an exception (fail-soft test).
    """
    db = MagicMock()

    counts = {
        "profiles_signups": signups,
        "profiles_created": profiles,
        "assessment_sessions_started": started,
        "assessment_sessions_completed": completed,
        "aura_scores": aura,
    }

    def mock_table(name: str) -> MagicMock:
        t = MagicMock()

        if name == "profiles":
            # Admin check chain: .select().eq().maybe_single().execute()
            admin_result = MockResult(data={"is_platform_admin": True})
            t.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=admin_result
            )

            # signups_7d: .select("id", count="exact").gte().execute()
            signups_result = MockResult(data=[], count=counts["profiles_signups"])

            # profiles_created_7d: .select().gte().not_.is_().execute()
            profiles_result = MockResult(data=[], count=counts["profiles_created"])

            def profiles_select(*args, **kwargs):
                sel = MagicMock()
                sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=admin_result)
                sel.gte.return_value.execute = AsyncMock(return_value=signups_result)
                sel.gte.return_value.not_ = MagicMock()
                sel.gte.return_value.not_.is_.return_value.execute = AsyncMock(return_value=profiles_result)
                return sel

            if raise_on == "profiles":

                def profiles_select_raise(*args, **kwargs):  # noqa: E306
                    sel = MagicMock()
                    sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=admin_result)

                    async def _raise():
                        raise RuntimeError("DB error")

                    sel.gte.return_value.execute = AsyncMock(side_effect=RuntimeError("DB error"))
                    sel.gte.return_value.not_ = MagicMock()
                    sel.gte.return_value.not_.is_.return_value.execute = AsyncMock(side_effect=RuntimeError("DB error"))
                    return sel

                t.select = profiles_select_raise
            else:
                t.select = profiles_select

        elif name == "assessment_sessions":
            started_result = MockResult(data=[], count=counts["assessment_sessions_started"])
            completed_result = MockResult(data=[], count=counts["assessment_sessions_completed"])

            if raise_on == "assessment_sessions":
                t.select.return_value.gte.return_value.execute = AsyncMock(side_effect=RuntimeError("DB error"))
                t.select.return_value.eq.return_value.gte.return_value.execute = AsyncMock(
                    side_effect=RuntimeError("DB error")
                )
            else:
                t.select.return_value.gte.return_value.execute = AsyncMock(return_value=started_result)
                t.select.return_value.eq.return_value.gte.return_value.execute = AsyncMock(
                    return_value=completed_result
                )

        elif name == "aura_scores":
            aura_result = MockResult(data=[], count=counts["aura_scores"])

            if raise_on == "aura_scores":
                t.select.return_value.gte.return_value.execute = AsyncMock(side_effect=RuntimeError("DB error"))
            else:
                t.select.return_value.gte.return_value.execute = AsyncMock(return_value=aura_result)

        return t

    db.table = mock_table
    return db


# ── Schema tests: AdminGrowthFunnel ──────────────────────────────────────────


class TestAdminGrowthFunnelSchema:
    NOW = datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)

    def _valid(self, **overrides) -> dict:
        base = {
            "signups_7d": 10,
            "profiles_created_7d": 8,
            "assessments_started_7d": 6,
            "assessments_completed_7d": 4,
            "aura_scores_7d": 3,
            "computed_at": self.NOW,
        }
        base.update(overrides)
        return base

    def test_construction_with_valid_data(self):
        f = AdminGrowthFunnel(**self._valid())
        assert f.signups_7d == 10
        assert f.profiles_created_7d == 8
        assert f.assessments_started_7d == 6
        assert f.assessments_completed_7d == 4
        assert f.aura_scores_7d == 3
        assert f.computed_at == self.NOW

    @pytest.mark.parametrize(
        "missing_field",
        [
            "signups_7d",
            "profiles_created_7d",
            "assessments_started_7d",
            "assessments_completed_7d",
            "aura_scores_7d",
            "computed_at",
        ],
    )
    def test_all_fields_required(self, missing_field: str):
        data = self._valid()
        del data[missing_field]
        with pytest.raises((TypeError, ValueError)):
            AdminGrowthFunnel(**data)

    @pytest.mark.parametrize(
        "field",
        [
            "signups_7d",
            "profiles_created_7d",
            "assessments_started_7d",
            "assessments_completed_7d",
            "aura_scores_7d",
        ],
    )
    def test_zero_values_accepted(self, field: str):
        f = AdminGrowthFunnel(**self._valid(**{field: 0}))
        assert getattr(f, field) == 0

    @pytest.mark.parametrize(
        "field",
        [
            "signups_7d",
            "profiles_created_7d",
            "assessments_started_7d",
            "assessments_completed_7d",
            "aura_scores_7d",
        ],
    )
    def test_large_values_accepted(self, field: str):
        f = AdminGrowthFunnel(**self._valid(**{field: 10_000_000}))
        assert getattr(f, field) == 10_000_000

    @pytest.mark.parametrize(
        "field",
        [
            "signups_7d",
            "profiles_created_7d",
            "assessments_started_7d",
            "assessments_completed_7d",
            "aura_scores_7d",
        ],
    )
    def test_negative_values_accepted_by_int_type(self, field: str):
        """int fields have no non-negative constraint; negative values parse without error."""
        f = AdminGrowthFunnel(**self._valid(**{field: -1}))
        assert getattr(f, field) == -1


# ── Endpoint tests: GET /api/admin/growth ────────────────────────────────────


class TestAdminGrowthEndpoint:
    @pytest.mark.asyncio
    async def test_non_admin_gets_403(self):
        non_admin_db = MagicMock()

        def mock_table_non_admin(name: str) -> MagicMock:
            t = MagicMock()
            if name == "profiles":

                def profiles_select(*args, **kwargs):
                    sel = MagicMock()
                    sel.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                        return_value=MockResult(data=None)
                    )
                    return sel

                t.select = profiles_select
            return t

        non_admin_db.table = mock_table_non_admin
        app.dependency_overrides[get_supabase_admin] = lambda: non_admin_db
        app.dependency_overrides[get_current_user_id] = lambda: REGULAR_USER_ID
        try:
            async with _make_client() as client:
                resp = await client.get("/api/admin/growth")
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NOT_PLATFORM_ADMIN"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_happy_path_returns_200_with_all_counts(self):
        db = _make_growth_db(signups=10, profiles=8, started=6, completed=4, aura=3)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with _make_client() as client:
                resp = await client.get("/api/admin/growth")
            assert resp.status_code == 200
            body = resp.json()
            assert body["signups_7d"] == 10
            assert body["profiles_created_7d"] == 8
            assert body["assessments_started_7d"] == 6
            assert body["assessments_completed_7d"] == 4
            assert body["aura_scores_7d"] == 3
            assert "computed_at" in body
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_response_includes_computed_at(self):
        db = _make_growth_db()
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with _make_client() as client:
                resp = await client.get("/api/admin/growth")
            assert resp.status_code == 200
            body = resp.json()
            assert "computed_at" in body
            # computed_at must be a parseable ISO datetime
            dt = datetime.fromisoformat(body["computed_at"])
            assert dt.tzinfo is not None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_all_zero_counts_return_200(self):
        db = _make_growth_db(signups=0, profiles=0, started=0, completed=0, aura=0)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with _make_client() as client:
                resp = await client.get("/api/admin/growth")
            assert resp.status_code == 200
            body = resp.json()
            assert body["signups_7d"] == 0
            assert body["assessments_completed_7d"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_fail_soft_assessment_sessions_exception_returns_0_not_500(self):
        db = _make_growth_db(raise_on="assessment_sessions")
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with _make_client() as client:
                resp = await client.get("/api/admin/growth")
            assert resp.status_code == 200
            body = resp.json()
            assert body["assessments_started_7d"] == 0
            assert body["assessments_completed_7d"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_fail_soft_aura_scores_exception_returns_0_not_500(self):
        db = _make_growth_db(raise_on="aura_scores")
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with _make_client() as client:
                resp = await client.get("/api/admin/growth")
            assert resp.status_code == 200
            body = resp.json()
            assert body["aura_scores_7d"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_response_shape_matches_admin_growth_funnel_schema(self):
        db = _make_growth_db(signups=5, profiles=4, started=3, completed=2, aura=1)
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: ADMIN_USER_ID
        try:
            async with _make_client() as client:
                resp = await client.get("/api/admin/growth")
            assert resp.status_code == 200
            body = resp.json()
            required_keys = {
                "signups_7d",
                "profiles_created_7d",
                "assessments_started_7d",
                "assessments_completed_7d",
                "aura_scores_7d",
                "computed_at",
            }
            assert required_keys.issubset(body.keys())
        finally:
            app.dependency_overrides.clear()
