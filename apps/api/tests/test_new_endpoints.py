"""
New Endpoint Tests — Public Stats, Coaching
============================================

Tests for:
- GET /api/stats/public — public platform statistics
- POST /api/assessment/{session_id}/coaching — authenticated, LLM-backed
- Verification endpoints
- Security checks

Leaderboard tests removed 2026-04-16 per Constitution G9 + G46 + Crystal Law 5
(no competitive framing, no scoreboard comparisons). Router, hook, and tests
all removed in the same commit.

Mock pattern: MagicMock for table() (sync), AsyncMock only for execute().
Dependency overrides are cleaned up in finally blocks to prevent test pollution.
"""

import json
from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── Helpers ────────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())


def make_client() -> AsyncClient:
    """Return a fresh async test client."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── CLASS 2: TestPublicStats ──────────────────────────────────────────────────


class TestPublicStats:
    """GET /api/stats/public — public endpoint, no auth."""

    def _make_stats_admin_mock(
        self,
        volunteer_count: int = 150,
        assessment_count: int = 320,
        event_count: int = 18,
        avg_scores: list[float] | None = None,
    ) -> MagicMock:
        """Build a mock for the stats endpoint's DB calls.

        The endpoint uses:
          - db.table("profiles").select(...).execute()       → count
          - db.table("assessment_sessions").select(...).execute() → count
          - db.table("events").select(...).execute()         → count
          - db.rpc("avg_aura_score").execute()               → single float
        """
        if avg_scores is None:
            avg_scores = [73.4, 81.2, 65.0]

        avg_value = sum(avg_scores) / len(avg_scores) if avg_scores else 0.0

        admin_mock = MagicMock()

        def mock_table(table_name):
            m = MagicMock()

            if table_name == "profiles":
                result = MagicMock()
                result.count = volunteer_count
                result.data = []
                m.select.return_value.execute = AsyncMock(return_value=result)

            elif table_name == "assessment_sessions":
                result = MagicMock()
                result.count = assessment_count
                result.data = []
                m.select.return_value.eq.return_value.execute = AsyncMock(return_value=result)

            elif table_name == "events":
                result = MagicMock()
                result.count = event_count
                result.data = []
                m.select.return_value.neq.return_value.execute = AsyncMock(return_value=result)

            return m

        admin_mock.table.side_effect = mock_table

        # RPC mock: avg_aura_score() returns a single float
        rpc_result = MagicMock()
        rpc_result.data = avg_value
        rpc_mock = MagicMock()
        rpc_mock.execute = AsyncMock(return_value=rpc_result)
        admin_mock.rpc = MagicMock(return_value=rpc_mock)

        return admin_mock

    @pytest.mark.asyncio
    async def test_stats_returns_200(self):
        """GET /api/stats/public returns 200."""
        admin_mock = self._make_stats_admin_mock()

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.get("/api/stats/public")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_stats_has_required_fields(self):
        """Response must have total_professionals, total_assessments, total_events, avg_aura_score."""
        admin_mock = self._make_stats_admin_mock()

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.get("/api/stats/public")
            body = response.json()
            assert "total_professionals" in body, "'total_professionals' missing from stats response"
            assert "total_assessments" in body, "'total_assessments' missing from stats response"
            assert "total_events" in body, "'total_events' missing from stats response"
            assert "avg_aura_score" in body, "'avg_aura_score' missing from stats response"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_stats_no_auth_required(self):
        """GET /api/stats/public without Authorization header returns 200."""
        admin_mock = self._make_stats_admin_mock()

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.get("/api/stats/public")
            assert response.status_code == 200, f"Public stats must not require auth — got {response.status_code}"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_stats_returns_numeric_values(self):
        """All stat values must be int or float >= 0."""
        admin_mock = self._make_stats_admin_mock(
            volunteer_count=42,
            assessment_count=99,
            event_count=5,
            avg_scores=[60.0, 80.0],
        )

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.get("/api/stats/public")
            body = response.json()
            assert isinstance(body["total_professionals"], int) and body["total_professionals"] >= 0
            assert isinstance(body["total_assessments"], int) and body["total_assessments"] >= 0
            assert isinstance(body["total_events"], int) and body["total_events"] >= 0
            assert isinstance(body["avg_aura_score"], (int, float)) and body["avg_aura_score"] >= 0
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_stats_avg_aura_rounds_to_one_decimal(self):
        """avg_aura_score must be rounded to 1 decimal place."""
        # 73.456789 + 73.456789 + 73.456789 / 3 = 73.456789 → rounds to 73.5
        admin_mock = self._make_stats_admin_mock(avg_scores=[73.456789, 73.456789, 73.456789])

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.get("/api/stats/public")
            body = response.json()
            avg = body["avg_aura_score"]
            # Check it's rounded to 1 decimal — no more than 1 decimal digit
            avg_str = str(avg)
            decimal_part = avg_str.split(".")[-1] if "." in avg_str else ""
            assert len(decimal_part) <= 1, f"avg_aura_score should be rounded to 1 decimal, got {avg}"
            assert avg == 73.5, f"Expected 73.5 for input 73.456789, got {avg}"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)


# ── CLASS 3: TestCoachingEndpoint ─────────────────────────────────────────────


class TestCoachingEndpoint:
    """POST /api/assessment/{session_id}/coaching"""

    SESSION_ID = str(uuid4())
    COMPETENCY_ID = str(uuid4())

    def _make_session_data(
        self,
        session_id: str | None = None,
        coaching_note: list | None = None,
        theta_estimate: float = 0.5,
    ) -> dict:
        return {
            "id": session_id or self.SESSION_ID,
            "competency_id": self.COMPETENCY_ID,
            "volunteer_id": USER_ID,
            "theta_estimate": theta_estimate,
            "coaching_note": coaching_note,
        }

    def _make_user_mock(self, session_data: dict | None = None) -> MagicMock:
        """Mock for db_user (SupabaseUser) — returns session from assessment_sessions."""
        user_mock = MagicMock()
        result = MagicMock()
        result.data = session_data

        user_mock.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
            return_value=result
        )
        return user_mock

    @staticmethod
    def _user_dep_override(user_mock: MagicMock):
        """Return a FastAPI dependency override for get_supabase_user.

        get_supabase_user is defined as `async def get_supabase_user(request: Request)`
        and is an async generator. The override must be an async generator that
        accepts no arguments (FastAPI resolves Request automatically for the real dep,
        but since we fully replace the dependency, we skip request entirely).
        """

        async def override():
            yield user_mock

        return override

    def _make_admin_mock(self, comp_slug: str = "communication") -> MagicMock:
        """Mock for db_admin (SupabaseAdmin) — returns competency + handles update."""
        admin_mock = MagicMock()

        def mock_table(table_name):
            m = MagicMock()
            if table_name == "competencies":
                result = MagicMock()
                result.data = {"name": "Communication", "slug": comp_slug}
                m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(return_value=result)
            elif table_name == "assessment_sessions":
                # For the coaching_note cache update
                update_result = MagicMock()
                update_result.data = [{"id": self.SESSION_ID}]
                m.update.return_value.eq.return_value.execute = AsyncMock(return_value=update_result)
            return m

        admin_mock.table.side_effect = mock_table
        return admin_mock

    @pytest.mark.asyncio
    async def test_coaching_requires_auth(self):
        """POST /api/assessment/{session_id}/coaching without JWT returns 401.

        Note: get_current_user_id depends on get_supabase_admin. FastAPI resolves
        admin dep BEFORE the auth check can short-circuit — so we must provide a
        minimal admin mock to avoid acreate_client(supabase_key=None) crash in CI.
        """
        admin_mock = self._make_admin_mock()

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        valid_session_id = str(uuid4())
        try:
            async with make_client() as client:
                response = await client.post(
                    f"/api/assessment/{valid_session_id}/coaching"
                    # intentionally no Authorization header
                )
            assert response.status_code == 401, f"Coaching endpoint must require auth — got {response.status_code}"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_coaching_session_not_found_returns_404(self):
        """When session doesn't exist or doesn't belong to user, return 404."""
        user_mock = self._make_user_mock(session_data=None)
        admin_mock = self._make_admin_mock()

        async def override_admin():
            yield admin_mock

        async def override_user_id():
            return USER_ID

        app.dependency_overrides[get_supabase_admin] = override_admin
        app.dependency_overrides[get_supabase_user] = self._user_dep_override(user_mock)
        app.dependency_overrides[get_current_user_id] = override_user_id
        try:
            async with make_client() as client:
                response = await client.post(
                    f"/api/assessment/{self.SESSION_ID}/coaching",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert response.status_code == 404, f"Expected 404 for missing session, got {response.status_code}"
            body = response.json()
            assert "detail" in body
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_coaching_returns_tips(self):
        """With a completed session and working Gemini, returns 200 with 3 tips."""
        session_data = self._make_session_data(coaching_note=None)
        user_mock = self._make_user_mock(session_data=session_data)
        admin_mock = self._make_admin_mock(comp_slug="communication")

        async def override_admin():
            yield admin_mock

        async def override_user():
            yield user_mock

        async def override_user_id():
            return USER_ID

        gemini_response = json.dumps(
            {
                "tips": [
                    {"title": "Tip 1", "description": "Desc 1", "action": "Do this 1"},
                    {"title": "Tip 2", "description": "Desc 2", "action": "Do this 2"},
                    {"title": "Tip 3", "description": "Desc 3", "action": "Do this 3"},
                ]
            }
        )

        app.dependency_overrides[get_supabase_admin] = override_admin
        app.dependency_overrides[get_supabase_user] = override_user
        app.dependency_overrides[get_current_user_id] = override_user_id
        try:
            with patch("app.routers.assessment.settings") as mock_settings:
                mock_settings.gemini_api_key = "fake-key"

                # Patch google.genai.Client inside the router
                with patch(
                    "app.services.assessment.coaching_service.asyncio.wait_for", new_callable=AsyncMock
                ) as mock_wait:
                    mock_wait.return_value = gemini_response

                    async with make_client() as client:
                        response = await client.post(
                            f"/api/assessment/{self.SESSION_ID}/coaching",
                            headers={"Authorization": "Bearer fake-token"},
                        )
            assert response.status_code == 200, (
                f"Expected 200 with valid session + Gemini, got {response.status_code}: {response.text}"
            )
            body = response.json()
            assert "tips" in body
            assert len(body["tips"]) == 3
            for tip in body["tips"]:
                assert "title" in tip
                assert "description" in tip
                assert "action" in tip
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_coaching_returns_fallback_tips_on_gemini_failure(self):
        """When Gemini raises an exception, fallback tips are returned (not empty, not 500)."""
        session_data = self._make_session_data(coaching_note=None)
        user_mock = self._make_user_mock(session_data=session_data)
        admin_mock = self._make_admin_mock(comp_slug="reliability")

        async def override_admin():
            yield admin_mock

        async def override_user():
            yield user_mock

        async def override_user_id():
            return USER_ID

        app.dependency_overrides[get_supabase_admin] = override_admin
        app.dependency_overrides[get_supabase_user] = override_user
        app.dependency_overrides[get_current_user_id] = override_user_id
        try:
            with patch("app.routers.assessment.settings") as mock_settings:
                mock_settings.gemini_api_key = "fake-key"

                with patch(
                    "app.services.assessment.coaching_service.asyncio.wait_for", new_callable=AsyncMock
                ) as mock_wait:
                    mock_wait.side_effect = Exception("Gemini API unavailable")

                    async with make_client() as client:
                        response = await client.post(
                            f"/api/assessment/{self.SESSION_ID}/coaching",
                            headers={"Authorization": "Bearer fake-token"},
                        )
            assert response.status_code == 200, (
                f"Fallback should return 200, not {response.status_code}: {response.text}"
            )
            body = response.json()
            assert "tips" in body
            assert len(body["tips"]) > 0, "Fallback must return at least 1 tip, not empty list"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_coaching_cached_result_returned_on_second_call(self):
        """If coaching_note is already cached in session, return it without calling Gemini."""
        cached_tips = [
            {"title": "Cached Tip 1", "description": "Cached desc 1", "action": "Cached action 1"},
            {"title": "Cached Tip 2", "description": "Cached desc 2", "action": "Cached action 2"},
            {"title": "Cached Tip 3", "description": "Cached desc 3", "action": "Cached action 3"},
        ]
        session_data = self._make_session_data(coaching_note=cached_tips)
        user_mock = self._make_user_mock(session_data=session_data)
        admin_mock = self._make_admin_mock()

        async def override_admin():
            yield admin_mock

        async def override_user():
            yield user_mock

        async def override_user_id():
            return USER_ID

        app.dependency_overrides[get_supabase_admin] = override_admin
        app.dependency_overrides[get_supabase_user] = override_user
        app.dependency_overrides[get_current_user_id] = override_user_id
        try:
            with patch(
                "app.services.assessment.coaching_service.asyncio.wait_for", new_callable=AsyncMock
            ) as mock_gemini:
                mock_gemini.side_effect = Exception("Should not be called for cached sessions")

                async with make_client() as client:
                    response = await client.post(
                        f"/api/assessment/{self.SESSION_ID}/coaching",
                        headers={"Authorization": "Bearer fake-token"},
                    )

            # Gemini must NOT have been called
            mock_gemini.assert_not_called()

            assert response.status_code == 200
            body = response.json()
            assert body["tips"][0]["title"] == "Cached Tip 1", (
                "Cached tip not returned — Gemini was called instead of using cache"
            )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_coaching_invalid_session_id_format(self):
        """POST with a non-UUID session_id returns 422 (not 500)."""

        async def override_user_id():
            return USER_ID

        app.dependency_overrides[get_current_user_id] = override_user_id

        # Also need user mock to prevent real DB call
        user_mock = MagicMock()
        admin_mock = MagicMock()

        async def override_admin():
            yield admin_mock

        async def override_user():
            yield user_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        app.dependency_overrides[get_supabase_user] = override_user
        try:
            async with make_client() as client:
                response = await client.post(
                    "/api/assessment/not-a-uuid/coaching",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert response.status_code in (422, 404), (
                f"Invalid UUID session_id should return 422 or 404, got {response.status_code}"
            )
        finally:
            app.dependency_overrides.pop(get_current_user_id, None)
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)

    @pytest.mark.asyncio
    async def test_coaching_other_users_session_returns_404(self):
        """Session that exists but belongs to another user returns 404."""
        # Mock returns None because the .eq("volunteer_id", user_id) filter excludes foreign sessions
        user_mock = self._make_user_mock(session_data=None)
        admin_mock = self._make_admin_mock()

        async def override_admin():
            yield admin_mock

        async def override_user():
            yield user_mock

        async def override_user_id():
            return USER_ID

        app.dependency_overrides[get_supabase_admin] = override_admin
        app.dependency_overrides[get_supabase_user] = override_user
        app.dependency_overrides[get_current_user_id] = override_user_id
        try:
            async with make_client() as client:
                response = await client.post(
                    f"/api/assessment/{self.SESSION_ID}/coaching",
                    headers={"Authorization": "Bearer fake-token"},
                )
            assert response.status_code == 404, (
                f"Session belonging to another user should return 404, got {response.status_code}"
            )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── CLASS 4: TestSecurityEndpoints ────────────────────────────────────────────


class TestSecurityEndpoints:
    """Security checks for new endpoints."""

    @pytest.mark.asyncio
    async def test_stats_no_sensitive_data_leaked(self):
        """Stats response must not expose emails, volunteer_ids, or raw score arrays."""
        admin_mock = MagicMock()

        def mock_table(table_name):
            m = MagicMock()
            if table_name == "profiles":
                result = MagicMock()
                result.count = 100
                result.data = []
                m.select.return_value.execute = AsyncMock(return_value=result)
            elif table_name == "assessment_sessions":
                result = MagicMock()
                result.count = 200
                result.data = []
                m.select.return_value.eq.return_value.execute = AsyncMock(return_value=result)
            elif table_name == "events":
                result = MagicMock()
                result.count = 10
                result.data = []
                m.select.return_value.neq.return_value.execute = AsyncMock(return_value=result)
            elif table_name == "aura_scores":
                result = MagicMock()
                result.data = [{"total_score": 75.0}]
                m.select.return_value.not_.is_.return_value.execute = AsyncMock(return_value=result)
            return m

        admin_mock.table.side_effect = mock_table

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.get("/api/stats/public")
            body = response.json()
            response_str = json.dumps(body)

            # Must not contain individual volunteer identifiers
            assert "volunteer_id" not in response_str, "Stats must not expose volunteer_ids"
            assert "@" not in response_str, "Stats must not expose email addresses"
            # scores should be aggregated, not a raw list
            assert not isinstance(body.get("avg_aura_score"), list), (
                "avg_aura_score must be a scalar, not a raw scores array"
            )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)


# ── CLASS 6: TestVerificationEndpoint ──────────────────────────────────────────


class TestVerificationEndpoint:
    """QA-M03 — POST /api/verify/{token} marks token used and blends AURA.

    Covers:
    - Happy path: valid token → 201 SubmitVerificationResponse
    - Already-used token → 409 TOKEN_ALREADY_USED
    - Expired token → 410 TOKEN_EXPIRED
    - Missing token → 404 TOKEN_INVALID
    - AURA blend math: rating=4 on existing 75.0 → blended 77.0
    """

    def _make_admin_mock(
        self,
        *,
        token_used: bool = False,
        expires_delta_days: int = 1,
        existing_aura_score: float | None = 75.0,
    ) -> tuple[MagicMock, str, str]:
        """Build admin mock for the full verification flow.

        Returns (admin_mock, token_str, volunteer_id).
        """
        from datetime import datetime, timedelta

        token_str = "test_token_abc123"
        volunteer_id = str(uuid4())
        competency_id = "communication"

        expires_at = (datetime.now(UTC) + timedelta(days=expires_delta_days)).isoformat()

        token_row = {
            "id": str(uuid4()),
            "token_used": token_used,
            "token_expires_at": expires_at,
            "competency_id": competency_id,
            "verifier_name": "Expert Jane",
            "verifier_org": "TechCorp AZ",
            "volunteer_id": volunteer_id,
            "profiles": {
                "display_name": "Test Volunteer",
                "username": "testvolunteer",
                "avatar_url": None,
            },
        }

        admin_mock = MagicMock()

        # expert_verifications table mock
        verif_mock = MagicMock()
        get_result = MagicMock()
        get_result.data = token_row
        verif_mock.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(return_value=get_result)
        update_result = MagicMock()
        update_result.data = [token_row]
        verif_mock.update.return_value.eq.return_value.eq.return_value.execute = AsyncMock(return_value=update_result)

        # aura_scores table mock
        aura_mock = MagicMock()
        aura_result = MagicMock()
        if existing_aura_score is not None:
            aura_result.data = {"competency_scores": {competency_id: existing_aura_score}}
        else:
            aura_result.data = None
        aura_mock.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(return_value=aura_result)

        def mock_table(table_name: str) -> MagicMock:
            if table_name == "expert_verifications":
                return verif_mock
            if table_name == "aura_scores":
                return aura_mock
            return MagicMock()

        admin_mock.table.side_effect = mock_table

        rpc_result = MagicMock()
        rpc_result.data = {"success": True}
        rpc_mock = MagicMock()
        rpc_mock.execute = AsyncMock(return_value=rpc_result)
        admin_mock.rpc = MagicMock(return_value=rpc_mock)

        return admin_mock, token_str, volunteer_id

    @pytest.mark.asyncio
    async def test_submit_verification_returns_201(self):
        """Happy path: valid token + rating=4 → 201 with status='verified'."""
        admin_mock, token, _ = self._make_admin_mock()

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.post(
                    f"/api/verify/{token}",
                    json={"rating": 4, "comment": "Great communicator"},
                    headers={"X-Forwarded-For": "10.2.0.1"},
                )
            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
            body = response.json()
            assert body["status"] == "verified"
            assert body["rating"] == 4
            assert body["competency_id"] == "communication"
            assert "professional_display_name" in body
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_submit_verification_already_used_returns_409(self):
        """Token that was already used → 409 TOKEN_ALREADY_USED."""
        admin_mock, token, _ = self._make_admin_mock(token_used=True)

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.post(
                    f"/api/verify/{token}",
                    json={"rating": 3},
                    headers={"X-Forwarded-For": "10.2.0.2"},
                )
            assert response.status_code == 409, f"Used token must return 409, got {response.status_code}"
            body = response.json()
            assert body["detail"]["code"] == "TOKEN_ALREADY_USED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_submit_verification_expired_returns_410(self):
        """Expired token (expires_delta_days=-1) → 410 TOKEN_EXPIRED."""
        admin_mock, token, _ = self._make_admin_mock(expires_delta_days=-1)

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.post(
                    f"/api/verify/{token}",
                    json={"rating": 5},
                    headers={"X-Forwarded-For": "10.2.0.3"},
                )
            assert response.status_code == 410, f"Expired token must return 410, got {response.status_code}"
            body = response.json()
            assert body["detail"]["code"] == "TOKEN_EXPIRED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_submit_verification_invalid_token_returns_404(self):
        """Unknown token → 404 TOKEN_INVALID."""
        admin_mock = MagicMock()

        get_result = MagicMock()
        get_result.data = None
        verif_mock = MagicMock()
        verif_mock.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(return_value=get_result)
        admin_mock.table.side_effect = lambda t: verif_mock if t == "expert_verifications" else MagicMock()

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.post(
                    "/api/verify/does_not_exist_xyz",
                    json={"rating": 3},
                    headers={"X-Forwarded-For": "10.2.0.4"},
                )
            assert response.status_code == 404, f"Invalid token must return 404, got {response.status_code}"
            body = response.json()
            assert body["detail"]["code"] == "TOKEN_INVALID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_submit_verification_blends_aura_score(self):
        """Verify rating=4 blends into existing communication score of 75.0.

        Blend formula: existing * 0.6 + verification_score * 0.4
        rating=4 → verification_score = (4/5) * 100 = 80.0
        blended = 75.0 * 0.6 + 80.0 * 0.4 = 45.0 + 32.0 = 77.0

        Confirms upsert_aura_score RPC is called with the correct blended value.
        """
        admin_mock, token, volunteer_id = self._make_admin_mock(existing_aura_score=75.0)

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        try:
            async with make_client() as client:
                response = await client.post(
                    f"/api/verify/{token}",
                    json={"rating": 4},
                    headers={"X-Forwarded-For": "10.2.0.5"},
                )
            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

            admin_mock.rpc.assert_called_once()
            rpc_name = admin_mock.rpc.call_args[0][0]
            rpc_params = admin_mock.rpc.call_args[0][1]

            assert rpc_name == "upsert_aura_score", f"Wrong RPC: {rpc_name}"
            assert rpc_params["p_volunteer_id"] == volunteer_id

            blended_scores = rpc_params["p_competency_scores"]
            assert "communication" in blended_scores
            expected = round(75.0 * 0.6 + 80.0 * 0.4, 2)  # 77.0
            assert blended_scores["communication"] == expected, (
                f"Blend wrong: expected {expected}, got {blended_scores['communication']}"
            )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
