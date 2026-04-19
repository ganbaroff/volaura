"""HTTP endpoint tests for the profiles router.

Covers all endpoints:
- GET  /api/profiles/me               — get own profile
- POST /api/profiles/me               — create profile
- PUT  /api/profiles/me               — update profile
- GET  /api/profiles/me/views         — profile view counts
- GET  /api/profiles/me/verifications — coordinator verifications
- GET  /api/profiles/public           — org talent discovery
- GET  /api/profiles/{username}       — public profile by username
- POST /api/profiles/{username}/view  — record profile view
- POST /api/profiles/{pid}/verification-link — create verification link

Uses AsyncClient + app.dependency_overrides (same pattern as test_activity_endpoints.py).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())
ORG_USER_ID = str(uuid4())
AUTH_HEADERS = {"Authorization": "Bearer test-token-profiles"}

_PROFILE_ROW = {
    "id": USER_ID,
    "username": "testuser",
    "display_name": "Test User",
    "bio": "Hello world",
    "avatar_url": None,
    "location": "Baku",
    "languages": ["az", "en"],
    "account_type": "professional",
    "is_public": True,
    "visible_to_orgs": False,
    "org_type": None,
    "registration_number": None,
    "registration_tier": None,
    "subscription_status": "trial",
    "trial_started_at": None,
    "trial_ends_at": None,
    "subscription_started_at": None,
    "subscription_ends_at": None,
    "created_at": "2026-04-01T00:00:00+00:00",
    "updated_at": "2026-04-01T00:00:00+00:00",
    "age_confirmed": True,
    "terms_version": "1.0",
    "terms_accepted_at": "2026-04-01T00:00:00+00:00",
    "social_links": {},
}

_PUBLIC_PROFILE_ROW = {
    "id": USER_ID,
    "username": "testuser",
    "display_name": "Test User",
    "avatar_url": None,
    "bio": "Hello world",
    "location": "Baku",
    "languages": ["az", "en"],
    "badge_issued_at": None,
    "registration_number": None,
    "registration_tier": None,
}


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_chain(data=None, count=None, side_effect=None) -> MagicMock:
    """Supabase query chain mock covering all chaining patterns used in profiles.py."""
    result = MagicMock()
    result.data = data if data is not None else []
    result.count = count

    execute = AsyncMock(side_effect=side_effect) if side_effect else AsyncMock(return_value=result)

    chain = MagicMock()
    for method in (
        "select",
        "eq",
        "in_",
        "order",
        "limit",
        "range",
        "gte",
        "lt",
        "not_",
        "insert",
        "update",
        "is_",
    ):
        getattr(chain, method).return_value = chain
    chain.maybe_single.return_value = chain
    chain.not_.is_.return_value = chain
    chain.not_.return_value = chain
    chain.execute = execute
    return chain


def make_db(tables: dict | None = None) -> MagicMock:
    """Mock Supabase client dispatching per-table chains."""
    db = MagicMock()
    tables = tables or {}

    def dispatch(name: str) -> MagicMock:
        cfg = tables.get(name, {})
        return make_chain(**cfg)

    db.table.side_effect = dispatch
    return db


def user_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def admin_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def user_id_dep(uid: str = USER_ID):
    async def _override():
        return uid

    return _override


def _cleanup():
    app.dependency_overrides.pop(get_supabase_user, None)
    app.dependency_overrides.pop(get_supabase_admin, None)
    app.dependency_overrides.pop(get_current_user_id, None)


# ── GET /api/profiles/me ──────────────────────────────────────────────────────


class TestGetMyProfile:
    @pytest.mark.asyncio
    async def test_returns_200_with_profile(self):
        db = make_db({"profiles": {"data": _PROFILE_ROW}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["id"] == USER_ID
            assert body["username"] == "testuser"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me")
            assert r.status_code == 401
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_404_when_no_profile(self):
        db = make_db({"profiles": {"data": None}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me", headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "PROFILE_NOT_FOUND"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_404_on_db_exception(self):
        db = make_db({"profiles": {"side_effect": RuntimeError("DB timeout")}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me", headers=AUTH_HEADERS)
            assert r.status_code == 404
        finally:
            _cleanup()


# ── POST /api/profiles/me ─────────────────────────────────────────────────────


class TestCreateMyProfile:
    _payload = {
        "username": "newuser",
        "display_name": "New User",
        "bio": None,
        "location": None,
        "languages": [],
        "social_links": {},
        "is_public": True,
        "account_type": "professional",
        "visible_to_orgs": False,
        "org_type": None,
        "invited_by_org_id": None,
        "age_confirmed": True,
        "terms_version": "1.0",
    }

    @pytest.mark.asyncio
    async def test_creates_profile_returns_201(self):
        created_row = {**_PROFILE_ROW, "username": "newuser"}

        # profiles table: first call (username check) → empty, second call (insert) → row
        call_count = 0

        def dispatch(name: str) -> MagicMock:
            nonlocal call_count
            if name == "profiles":
                call_count += 1
                if call_count == 1:
                    # username uniqueness check — no existing user
                    return make_chain(data=[])
                else:
                    # insert result
                    return make_chain(data=[created_row])
            # aura_scores, expert_verifications etc. → empty
            return make_chain(data=[])

        user_db = MagicMock()
        user_db.table.side_effect = dispatch

        admin_db = MagicMock()
        admin_db.table.side_effect = lambda _: make_chain(data=[])
        # upsert_volunteer_embedding calls admin_db.table("volunteer_embeddings")
        # keep it silent

        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post("/api/profiles/me", json=self._payload, headers=AUTH_HEADERS)
            assert r.status_code == 201
            assert r.json()["username"] == "newuser"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        try:
            async with make_client() as client:
                r = await client.post("/api/profiles/me", json=self._payload)
            assert r.status_code == 401
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_409_when_username_taken(self):
        user_db = make_db({"profiles": {"data": [{"id": "other-user"}]}})
        admin_db = make_db()

        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post("/api/profiles/me", json=self._payload, headers=AUTH_HEADERS)
            assert r.status_code == 409
            assert r.json()["detail"]["code"] == "USERNAME_TAKEN"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_422_on_invalid_username(self):
        bad_payload = {**self._payload, "username": "x"}  # too short
        user_db = make_db()
        admin_db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post("/api/profiles/me", json=bad_payload, headers=AUTH_HEADERS)
            assert r.status_code == 422
        finally:
            _cleanup()


# ── PUT /api/profiles/me ──────────────────────────────────────────────────────


class TestUpdateMyProfile:
    _payload = {"display_name": "Updated Name", "bio": "New bio"}

    @pytest.mark.asyncio
    async def test_updates_profile_returns_200(self):
        updated_row = {**_PROFILE_ROW, "display_name": "Updated Name", "bio": "New bio"}

        user_db = make_db({"profiles": {"data": [updated_row]}})

        admin_db = MagicMock()
        # aura_scores query → None (no aura yet); embedding upsert → silent
        admin_db.table.side_effect = lambda _: make_chain(data=None)

        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.put("/api/profiles/me", json=self._payload, headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["display_name"] == "Updated Name"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        try:
            async with make_client() as client:
                r = await client.put("/api/profiles/me", json=self._payload)
            assert r.status_code == 401
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_422_when_no_fields_provided(self):
        user_db = make_db()
        admin_db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.put("/api/profiles/me", json={}, headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "NO_FIELDS"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_404_when_profile_not_found(self):
        user_db = make_db({"profiles": {"data": []}})
        admin_db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.put("/api/profiles/me", json=self._payload, headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "PROFILE_NOT_FOUND"
        finally:
            _cleanup()


# ── GET /api/profiles/me/views ────────────────────────────────────────────────


class TestGetMyProfileViews:
    @pytest.mark.asyncio
    async def test_returns_200_with_view_counts(self):
        db = make_db({"notifications": {"data": [], "count": 7}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me/views", headers=AUTH_HEADERS)
            assert r.status_code == 200
            data = r.json()["data"]
            assert "total_views" in data
            assert "week_views" in data
            assert "recent_viewers" in data
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me/views")
            assert r.status_code == 401
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_total_views_reflects_count(self):
        call_count = 0

        def dispatch(_: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            # First call: total count query, second: week count, third: recent list
            counts = [12, 3, 0]
            idx = min(call_count - 1, len(counts) - 1)
            return make_chain(data=[], count=counts[idx])

        db = MagicMock()
        db.table.side_effect = dispatch

        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me/views", headers=AUTH_HEADERS)
            assert r.status_code == 200
            data = r.json()["data"]
            assert data["total_views"] == 12
            assert data["week_views"] == 3
        finally:
            _cleanup()


# ── GET /api/profiles/me/verifications ────────────────────────────────────────


class TestGetMyVerifications:
    @pytest.mark.asyncio
    async def test_returns_200_with_empty_list(self):
        db = make_db(
            {
                "registrations": {"data": []},
                "events": {"data": []},
                "profiles": {"data": []},
            }
        )
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me/verifications", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["data"] == []
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me/verifications")
            assert r.status_code == 401
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_verifications_with_event_and_organizer(self):
        reg_row = {
            "id": "reg-1",
            "event_id": "ev-1",
            "coordinator_rating": 4,
            "coordinator_feedback": "Great work",
            "coordinator_rated_at": "2026-04-10T10:00:00Z",
        }
        event_row = {"title": "Hackathon", "organizer_id": "org-1"}
        org_row = {"display_name": "Org Name", "username": "orguser"}

        call_map: dict[str, list] = {
            "registrations": [reg_row],
            "events": [event_row],
            "profiles": [org_row],
        }
        call_counters: dict[str, int] = {}

        def dispatch(name: str) -> MagicMock:
            call_counters[name] = call_counters.get(name, 0) + 1
            rows = call_map.get(name, [])
            return make_chain(data=rows)

        db = MagicMock()
        db.table.side_effect = dispatch

        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me/verifications", headers=AUTH_HEADERS)
            assert r.status_code == 200
            verifications = r.json()["data"]
            assert len(verifications) == 1
            v = verifications[0]
            assert v["id"] == "reg-1"
            assert v["rating"] == 4
            assert v["comment"] == "Great work"
            assert v["competency_id"] == "event_performance"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_200_on_db_error(self):
        """DB error on registrations query → 200 with empty list (resilient)."""
        db = make_db({"registrations": {"side_effect": RuntimeError("DB down")}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/me/verifications", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["data"] == []
        finally:
            _cleanup()


# ── GET /api/profiles/public ──────────────────────────────────────────────────


class TestListPublicProfessionals:
    @pytest.mark.asyncio
    async def test_returns_403_for_non_org_caller(self):
        """Professional account → 403 ORG_REQUIRED."""
        admin_db = make_db(
            {
                "profiles": {
                    "data": {"account_type": "professional"},
                }
            }
        )
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/public", headers=AUTH_HEADERS)
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "ORG_REQUIRED"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/public")
            assert r.status_code == 401
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_org_caller_gets_list(self):
        """Organization account → 200 with list of professionals."""
        professional_row = {
            "id": str(uuid4()),
            "username": "pro1",
            "display_name": "Alice Smith",
            "avatar_url": None,
            "bio": "Expert volunteer",
            "location": "Baku",
            "languages": ["az"],
            "aura_scores": [{"total_score": 82.5, "badge_tier": "gold"}],
        }

        call_count = 0

        def dispatch(name: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: caller role check → org
                return make_chain(data={"account_type": "organization"})
            else:
                # Second call: professionals list
                return make_chain(data=[professional_row])

        admin_db = MagicMock()
        admin_db.table.side_effect = dispatch

        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ORG_USER_ID)
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/public", headers=AUTH_HEADERS)
            assert r.status_code == 200
            items = r.json()
            assert len(items) == 1
            # SEC-03: display_name must be anonymized
            assert items[0]["display_name"] == "Alice S."
            assert items[0]["total_score"] == 82.5
            assert items[0]["badge_tier"] == "gold"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_anonymizes_display_name(self):
        """_anonymize_name → 'First L.' format for all entries."""
        row = {
            "id": str(uuid4()),
            "username": "pro2",
            "display_name": "Leyla Aliyeva",
            "avatar_url": None,
            "bio": None,
            "location": None,
            "languages": [],
            "aura_scores": [],
        }

        call_count = 0

        def dispatch(_: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_chain(data={"account_type": "organization"})
            return make_chain(data=[row])

        admin_db = MagicMock()
        admin_db.table.side_effect = dispatch

        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ORG_USER_ID)
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/public", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()[0]["display_name"] == "Leyla A."
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_pagination_params_accepted(self):
        """limit and offset query params pass without 422."""
        call_count = 0

        def dispatch(_: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_chain(data={"account_type": "organization"})
            return make_chain(data=[])

        admin_db = MagicMock()
        admin_db.table.side_effect = dispatch

        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ORG_USER_ID)
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/public", params={"limit": 5, "offset": 10}, headers=AUTH_HEADERS)
            assert r.status_code == 200
        finally:
            _cleanup()


# ── GET /api/profiles/{username} ──────────────────────────────────────────────


class TestGetPublicProfile:
    @pytest.mark.asyncio
    async def test_returns_200_no_auth_required(self):
        """Public profile endpoint requires no auth."""
        admin_db = MagicMock()
        call_count = 0

        def dispatch(_: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_chain(data=_PUBLIC_PROFILE_ROW)
            # aura_scores and count queries
            return make_chain(data=None, count=0)

        admin_db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/testuser")
            assert r.status_code == 200
            body = r.json()
            assert body["username"] == "testuser"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_username(self):
        admin_db = make_db({"profiles": {"data": None}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/nobody")
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "PROFILE_NOT_FOUND"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_percentile_rank_when_aura_exists(self):
        """percentile_rank is computed from lower_count / total_count."""
        call_count = 0

        def dispatch(name: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # profile row
                return make_chain(data=_PUBLIC_PROFILE_ROW)
            if call_count == 2:
                # aura_scores for this user
                return make_chain(data={"total_score": 80.0})
            if call_count == 3:
                # lower count
                return make_chain(data=[], count=60)
            # total count
            return make_chain(data=[], count=100)

        admin_db = MagicMock()
        admin_db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/testuser")
            assert r.status_code == 200
            body = r.json()
            assert body["percentile_rank"] == 60.0
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_percentile_rank_none_when_no_aura(self):
        call_count = 0

        def dispatch(_: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_chain(data=_PUBLIC_PROFILE_ROW)
            return make_chain(data=None)

        admin_db = MagicMock()
        admin_db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        try:
            async with make_client() as client:
                r = await client.get("/api/profiles/testuser")
            assert r.status_code == 200
            assert r.json()["percentile_rank"] is None
        finally:
            _cleanup()


# ── POST /api/profiles/{username}/view ────────────────────────────────────────


class TestRecordProfileView:
    @pytest.mark.asyncio
    async def test_returns_204_for_org_viewer(self):
        """Org account viewing a professional → 204 (notification fired)."""
        org_row = {
            "account_type": "organization",
            "display_name": "ACME Corp",
            "username": "acme",
        }
        target_row = {"id": str(uuid4()), "display_name": "Pro User"}

        call_count = 0

        def dispatch(name: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_chain(data=org_row)  # caller check
            if call_count == 2:
                return make_chain(data=target_row)  # target profile
            if call_count == 3:
                return make_chain(data=[])  # dedup: no existing notification
            return make_chain(data=[{"id": "notif-1"}])  # notify insert

        admin_db = MagicMock()
        admin_db.table.side_effect = dispatch
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep(ORG_USER_ID)
        try:
            async with make_client() as client:
                r = await client.post("/api/profiles/somepro/view", headers=AUTH_HEADERS)
            assert r.status_code == 204
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_204_silently_for_non_org(self):
        """Non-org caller → 204 with no notification, no error."""
        non_org_row = {"account_type": "professional", "display_name": "Pro", "username": "pro"}
        admin_db = make_db({"profiles": {"data": non_org_row}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(admin_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post("/api/profiles/otherpro/view", headers=AUTH_HEADERS)
            assert r.status_code == 204
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        try:
            async with make_client() as client:
                r = await client.post("/api/profiles/someone/view")
            assert r.status_code == 401
        finally:
            _cleanup()


# ── POST /api/profiles/{professional_id}/verification-link ────────────────────


class TestCreateVerificationLink:
    _payload = {
        "verifier_name": "Dr. Smith",
        "verifier_org": "TechCorp",
        "competency_id": "communication",
    }

    @pytest.mark.asyncio
    async def test_creates_link_returns_201(self):
        profile_row = {"id": USER_ID}
        verification_row = {
            "id": "verif-1",
            "volunteer_id": USER_ID,
            "created_by": USER_ID,
            "verifier_name": "Dr. Smith",
            "verifier_org": "TechCorp",
            "competency_id": "communication",
            "token": "fake-token-abc",
            "token_expires_at": "2026-04-26T00:00:00+00:00",
        }

        call_count = 0

        def dispatch(name: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if name == "profiles":
                return make_chain(data=profile_row)
            if name == "expert_verifications":
                return make_chain(data=[verification_row])
            return make_chain(data=[])

        user_db = MagicMock()
        user_db.table.side_effect = dispatch

        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    f"/api/profiles/{USER_ID}/verification-link",
                    json=self._payload,
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 201
            body = r.json()
            assert "token" in body
            assert "verify_url" in body
            assert body["competency_id"] == "communication"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_403_when_requesting_for_other_user(self):
        """CRIT-02: cannot create verification link for another user."""
        user_db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        other_user_id = str(uuid4())
        try:
            async with make_client() as client:
                r = await client.post(
                    f"/api/profiles/{other_user_id}/verification-link",
                    json=self._payload,
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "FORBIDDEN"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_404_when_profile_not_found(self):
        user_db = make_db({"profiles": {"data": None}})
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    f"/api/profiles/{USER_ID}/verification-link",
                    json=self._payload,
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "PROFILE_NOT_FOUND"
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        try:
            async with make_client() as client:
                r = await client.post(
                    f"/api/profiles/{USER_ID}/verification-link",
                    json=self._payload,
                )
            assert r.status_code == 401
        finally:
            _cleanup()

    @pytest.mark.asyncio
    async def test_returns_422_on_invalid_competency(self):
        bad_payload = {**self._payload, "competency_id": "nonexistent_skill"}
        user_db = make_db({"profiles": {"data": {"id": USER_ID}}})
        app.dependency_overrides[get_supabase_user] = user_dep(user_db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    f"/api/profiles/{USER_ID}/verification-link",
                    json=bad_payload,
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
        finally:
            _cleanup()
