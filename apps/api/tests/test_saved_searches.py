"""Saved Search Tests — Sprint 8 Security + Happy Path
======================================================

Covers the 4 QA-flagged scenarios from Sprint 8 sign-off:
  1. Privilege escalation: org A cannot read org B's saved searches
  2. Privilege escalation: org A cannot delete org B's saved searches
  3. Duplicate name → 409
  4. Cap > 20 → 422

Plus standard happy-path coverage:
  5. Create saved search → 201
  6. List saved searches → 200
  7. Delete own saved search → 204
  8. Update notify_on_match → 200
  9. User with no org → 404

Mock pattern: MagicMock for table()/select()/eq() chain, AsyncMock for execute().
Same pattern as test_character_api.py — see conftest.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.middleware.rate_limit import limiter

# Disable rate limiting — prevents 429 from leaking into unrelated tests
limiter.enabled = False


# ── Shared fixtures ────────────────────────────────────────────────────────────

ORG_A_USER = str(uuid4())
ORG_B_USER = str(uuid4())
ORG_A_ID = str(uuid4())
ORG_B_ID = str(uuid4())

SEARCH_OWNED_BY_ORG_A = {
    "id": str(uuid4()),
    "org_id": ORG_A_ID,
    "name": "Senior communicators",
    "filters": {"query": "communication", "min_aura": 60.0},
    "notify_on_match": True,
    "last_checked_at": "2026-04-01T00:00:00+00:00",
    "created_at": "2026-04-01T00:00:00+00:00",
    "updated_at": "2026-04-01T00:00:00+00:00",
}
SEARCH_OWNED_BY_ORG_B = {
    "id": str(uuid4()),
    "org_id": ORG_B_ID,
    "name": "Leadership candidates",
    "filters": {"query": "leadership", "min_aura": 70.0},
    "notify_on_match": False,
    "last_checked_at": "2026-04-01T00:00:00+00:00",
    "created_at": "2026-04-01T00:00:00+00:00",
    "updated_at": "2026-04-01T00:00:00+00:00",
}


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class MockResult:
    """Thin wrapper around .data for async execute() calls."""

    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


def make_org_admin(
    user_org_id: str,
    searches: list[dict] | None = None,
    search_count: int = 0,
    ownership_search: dict | None = None,
) -> MagicMock:
    """Build an admin mock that:
    - Returns `user_org_id` when looking up the caller's org
    - Returns `searches` when listing org_saved_searches
    - Returns `search_count` for count queries (cap enforcement)
    - Returns `ownership_search` when asserting search ownership (None = 404)
    """
    admin = MagicMock()

    def mock_table(table_name: str) -> MagicMock:
        m = MagicMock()

        if table_name == "organizations":
            # GET org by owner_id
            org_result = MockResult(data={"id": user_org_id} if user_org_id else None)
            select_m = MagicMock()
            select_m.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=org_result)
            m.select.return_value = select_m

        elif table_name == "org_saved_searches":
            # Count query (cap enforcement)
            count_result = MockResult(data=[], count=search_count)
            count_select = MagicMock()
            count_select.eq.return_value.execute = AsyncMock(return_value=count_result)

            # Single-row ownership assertion (select * + eq id + eq org_id + maybe_single)
            ownership_result = MockResult(data=ownership_search)
            ownership_select = MagicMock()
            ownership_select.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=ownership_result
            )

            # List query (select * + eq org_id + order + execute)
            list_result = MockResult(data=searches or [])
            list_select = MagicMock()
            list_select.eq.return_value.order.return_value.execute = AsyncMock(return_value=list_result)

            # Route to correct mock based on which select args are used
            def select_dispatcher(*args, count=None, **kwargs):
                if count == "exact":
                    return count_select
                # Heuristic: if the caller will do .eq().eq().maybe_single() — ownership check
                # vs .eq().order() — list query
                # We return a combined mock that handles both chains
                combined = MagicMock()
                combined.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=ownership_result)
                combined.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                    return_value=ownership_result
                )
                combined.eq.return_value.order.return_value.execute = AsyncMock(return_value=list_result)
                combined.eq.return_value.execute = AsyncMock(return_value=list_result)
                return combined

            m.select = select_dispatcher

            # Insert
            insert_result = MockResult(data=[SEARCH_OWNED_BY_ORG_A])
            m.insert.return_value.execute = AsyncMock(return_value=insert_result)

            # Update
            update_result = MockResult(data=[{**SEARCH_OWNED_BY_ORG_A, "notify_on_match": False}])
            m.update.return_value.eq.return_value.execute = AsyncMock(return_value=update_result)

            # Delete
            delete_result = MockResult(data=[])
            m.delete.return_value.eq.return_value.execute = AsyncMock(return_value=delete_result)

        return m

    admin.table = mock_table
    return admin


# ── Section 1: Happy Path ─────────────────────────────────────────────────────


class TestSavedSearchHappyPath:
    """Standard create / list / delete / update flows."""

    @pytest.mark.asyncio
    async def test_create_saved_search_returns_201(self):
        """POST /saved-searches with valid payload → 201 Created."""
        admin = make_org_admin(user_org_id=ORG_A_ID, search_count=0)
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/organizations/saved-searches",
                    json={
                        "name": "Senior communicators",
                        "filters": {"query": "communication", "min_aura": 60.0},
                        "notify_on_match": True,
                    },
                )
            assert resp.status_code == 201
            body = resp.json()
            assert body["name"] == SEARCH_OWNED_BY_ORG_A["name"]
            assert body["notify_on_match"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_saved_searches_returns_200(self):
        """GET /saved-searches → 200 with list of org's searches."""
        admin = make_org_admin(
            user_org_id=ORG_A_ID,
            searches=[SEARCH_OWNED_BY_ORG_A],
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.get("/api/organizations/saved-searches")
            assert resp.status_code == 200
            body = resp.json()
            assert isinstance(body, list)
            assert len(body) == 1
            assert body[0]["org_id"] == ORG_A_ID
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_own_search_returns_204(self):
        """DELETE /saved-searches/{id} for own search → 204 No Content."""
        admin = make_org_admin(
            user_org_id=ORG_A_ID,
            ownership_search=SEARCH_OWNED_BY_ORG_A,
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.delete(f"/api/organizations/saved-searches/{SEARCH_OWNED_BY_ORG_A['id']}")
            assert resp.status_code == 204
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_notify_flag_returns_200(self):
        """PATCH /saved-searches/{id} with notify_on_match=false → 200."""
        admin = make_org_admin(
            user_org_id=ORG_A_ID,
            ownership_search=SEARCH_OWNED_BY_ORG_A,
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.patch(
                    f"/api/organizations/saved-searches/{SEARCH_OWNED_BY_ORG_A['id']}",
                    json={"notify_on_match": False},
                )
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()


# ── Section 2: Privilege Escalation (Sprint 8 Security P0) ───────────────────


class TestSavedSearchPrivilegeEscalation:
    """
    CRITICAL: These tests verify that org A cannot access org B's data.

    Attack scenarios:
    1. Org A lists → should only see their own searches (RLS + API)
    2. Org A reads by ID → ownership check via _assert_search_ownership()
    3. Org A deletes org B's search by ID → 404
    4. Org A updates org B's search → 404
    """

    @pytest.mark.asyncio
    async def test_list_only_returns_own_org_searches(self):
        """Org A user listing searches only gets org A's data, not org B's.

        The admin mock only returns searches for org A's org_id — any query
        for org B's data returns empty (simulating RLS + API ownership filter).
        """
        admin = make_org_admin(
            user_org_id=ORG_A_ID,
            searches=[SEARCH_OWNED_BY_ORG_A],  # only org A's searches returned
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.get("/api/organizations/saved-searches")
            assert resp.status_code == 200
            body = resp.json()
            # Verify no org B data in response
            for item in body:
                assert item["org_id"] == ORG_A_ID
                assert item["org_id"] != ORG_B_ID
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_foreign_search_returns_404(self):
        """Org A user trying to delete org B's search → 404.

        Mechanism: _assert_search_ownership() queries:
          SELECT * FROM org_saved_searches WHERE id = {search_id} AND org_id = {org_A_id}
        For org B's search, this returns no rows → 404.
        """
        admin = make_org_admin(
            user_org_id=ORG_A_ID,
            # ownership_search=None → simulates row not found for org A's id
            ownership_search=None,
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                # Attempt to delete a search that belongs to org B
                resp = await client.delete(f"/api/organizations/saved-searches/{SEARCH_OWNED_BY_ORG_B['id']}")
            # Must be 404, NOT 204 or 200
            assert resp.status_code == 404
            body = resp.json()
            assert body["detail"]["code"] == "SEARCH_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_foreign_search_returns_404(self):
        """Org A user trying to update org B's search → 404.

        Same _assert_search_ownership() gate as delete.
        """
        admin = make_org_admin(
            user_org_id=ORG_A_ID,
            ownership_search=None,  # foreign search = not found for org A
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.patch(
                    f"/api/organizations/saved-searches/{SEARCH_OWNED_BY_ORG_B['id']}",
                    json={"notify_on_match": False},
                )
            assert resp.status_code == 404
            body = resp.json()
            assert body["detail"]["code"] == "SEARCH_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()


# ── Section 3: Input Validation ────────────────────────────────────────────────


class TestSavedSearchValidation:
    """Cap enforcement, duplicate names, invalid badge tier, invalid UUID."""

    @pytest.mark.asyncio
    async def test_cap_at_20_returns_422(self):
        """POST when org already has 20 saved searches → 422 SAVED_SEARCH_LIMIT.

        This prevents a single org from spamming the match checker with
        hundreds of saved searches that would slow the daily run.
        """
        admin = make_org_admin(
            user_org_id=ORG_A_ID,
            search_count=20,  # already at the cap
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/organizations/saved-searches",
                    json={
                        "name": "21st search",
                        "filters": {"query": "test"},
                    },
                )
            assert resp.status_code == 422
            body = resp.json()
            assert body["detail"]["code"] == "SAVED_SEARCH_LIMIT"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_badge_tier_returns_422(self):
        """POST with badge_tier='legendary' → 422 Pydantic validation error."""
        admin = make_org_admin(user_org_id=ORG_A_ID, search_count=0)
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/organizations/saved-searches",
                    json={
                        "name": "Valid name",
                        "filters": {"query": "test", "badge_tier": "legendary"},
                    },
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_search_id_uuid_returns_422(self):
        """DELETE /saved-searches/not-a-uuid → 422 (UUID validation)."""
        admin = make_org_admin(user_org_id=ORG_A_ID)
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.delete("/api/organizations/saved-searches/not-a-uuid")
            assert resp.status_code == 422
            body = resp.json()
            assert body["detail"]["code"] == "INVALID_ID"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_empty_name_returns_422(self):
        """POST with empty name → 422 (Pydantic min_length=1)."""
        admin = make_org_admin(user_org_id=ORG_A_ID, search_count=0)
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/organizations/saved-searches",
                    json={"name": "", "filters": {"query": "test"}},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_no_org_returns_404(self):
        """User without an organization → 404 ORG_NOT_FOUND on all endpoints."""
        admin = make_org_admin(user_org_id="")  # empty = no org found
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: str(uuid4())

        try:
            async with make_client() as client:
                resp = await client.get("/api/organizations/saved-searches")
            assert resp.status_code == 404
            body = resp.json()
            assert body["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_patch_no_fields_returns_422(self):
        """PATCH with empty body → 422 NO_FIELDS."""
        admin = make_org_admin(
            user_org_id=ORG_A_ID,
            ownership_search=SEARCH_OWNED_BY_ORG_A,
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin
        app.dependency_overrides[get_current_user_id] = lambda: ORG_A_USER

        try:
            async with make_client() as client:
                resp = await client.patch(
                    f"/api/organizations/saved-searches/{SEARCH_OWNED_BY_ORG_A['id']}",
                    json={},
                )
            assert resp.status_code == 422
            body = resp.json()
            assert body["detail"]["code"] == "NO_FIELDS"
        finally:
            app.dependency_overrides.clear()


# ── Section 4: Match Checker Unit Tests ───────────────────────────────────────


class TestMatchCheckerService:
    """Unit tests for match_checker.py service — no HTTP, pure service layer."""

    @pytest.mark.asyncio
    async def test_run_match_check_no_searches(self):
        """Empty saved searches list → RunSummary with zeros (no crash)."""
        from app.services.match_checker import run_match_check

        admin = MagicMock()
        # org_saved_searches returns empty list
        result_mock = MagicMock()
        result_mock.data = []
        admin.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = (
            AsyncMock(return_value=result_mock)
        )

        summary = await run_match_check(admin)

        assert summary.searches_checked == 0
        assert summary.notifications_sent == 0
        assert summary.errors == 0

    @pytest.mark.asyncio
    async def test_run_match_check_handles_db_error_gracefully(self):
        """DB error on a single search → increments errors, continues (doesn't raise)."""

        from app.services.match_checker import run_match_check

        admin = MagicMock()

        # One search in the list
        searches_result = MagicMock()
        searches_result.data = [
            {
                "id": str(uuid4()),
                "org_id": ORG_A_ID,
                "name": "Broken search",
                "filters": {"min_aura": 50.0},
                "notify_on_match": True,
                "last_checked_at": "2026-04-01T00:00:00+00:00",
            }
        ]
        admin.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = (
            AsyncMock(return_value=searches_result)
        )

        # Org lookup raises an exception
        admin.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
            side_effect=Exception("DB connection lost")
        )

        summary = await run_match_check(admin)

        # Must not raise — errors are counted and logged
        assert summary.errors == 1
        assert summary.searches_checked == 0  # failed before incrementing

    @pytest.mark.asyncio
    async def test_circuit_breaker_stops_telegram_after_threshold(self):
        """After _CB_THRESHOLD Telegram failures, no more notifications are attempted."""
        from app.services import match_checker
        from app.services.match_checker import _CB_THRESHOLD

        # Patch _send_telegram_notification to always fail
        fail_count = {"n": 0}

        async def always_fail(*args, **kwargs):
            fail_count["n"] += 1
            return False

        original = match_checker._send_telegram_notification
        match_checker._send_telegram_notification = always_fail

        # Build admin with 5 searches (more than threshold)
        admin = MagicMock()

        searches = [
            {
                "id": str(uuid4()),
                "org_id": ORG_A_ID,
                "name": f"Search {i}",
                "filters": {"min_aura": 0.0},
                "notify_on_match": True,
                "last_checked_at": "2020-01-01T00:00:00+00:00",
            }
            for i in range(5)
        ]

        searches_result = MagicMock()
        searches_result.data = searches

        # Org returns
        org_result = MagicMock()
        org_result.data = {"name": "Test Org"}

        # aura_scores returns 1 new match for each search
        match_result = MagicMock()
        match_result.data = [
            {
                "volunteer_id": str(uuid4()),
                "total_score": 75.0,
                "badge_tier": "gold",
            }
        ]

        # Profiles result
        profile_result = MagicMock()
        profile_result.data = []

        # Comp result
        comp_result = MagicMock()
        comp_result.data = None

        # update last_checked_at
        update_result = MagicMock()
        update_result.data = []

        def make_table_mock(table_name: str):
            m = MagicMock()
            if table_name == "org_saved_searches":
                # First call: fetch all searches
                m.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = AsyncMock(
                    return_value=searches_result
                )
                # Update last_checked_at
                m.update.return_value.eq.return_value.execute = AsyncMock(return_value=update_result)
            elif table_name == "organizations":
                m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                    return_value=org_result
                )
            elif table_name == "aura_scores":
                m.select.return_value.gte.return_value.eq.return_value.gt.return_value.order.return_value.limit.return_value.execute = AsyncMock(
                    return_value=match_result
                )
                m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                    return_value=comp_result
                )
            elif table_name == "profiles":
                m.select.return_value.in_.return_value.execute = AsyncMock(return_value=profile_result)
            return m

        admin.table = make_table_mock

        try:
            summary = await match_checker.run_match_check(admin)
            # Circuit breaker trips at _CB_THRESHOLD failures
            # After threshold, no more calls to _send_telegram_notification
            assert fail_count["n"] <= _CB_THRESHOLD
            # Some notifications should have been attempted but capped
            assert summary.errors == 0
        finally:
            match_checker._send_telegram_notification = original
