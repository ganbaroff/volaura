"""
Character API Tests — Crystal Balance & Character State
========================================================

Tests for:
- GET /api/character/crystals — lightweight crystal balance
- GET /api/character/state   — full character state via RPC

Mock pattern: MagicMock for table()/rpc() (sync chain), AsyncMock only for execute().
No response envelope: character router returns Pydantic models directly.
Auth 401 pattern: provide generator admin override (resolves before auth check in CI).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id
from app.middleware.rate_limit import limiter


# Disable rate limiting for tests — prevents 429 across test suite
limiter.enabled = False


# ── Helpers ───────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_ledger_admin(ledger_rows: list[dict]) -> MagicMock:
    """Admin mock with game_crystal_ledger returning given rows."""
    admin_mock = MagicMock()

    def mock_table(table_name: str):
        m = MagicMock()
        if table_name == "game_crystal_ledger":
            result = MagicMock()
            result.data = ledger_rows
            # Chain: .select().eq().execute()
            m.select.return_value.eq.return_value.execute = AsyncMock(return_value=result)
        return m

    admin_mock.table = mock_table
    return admin_mock


def make_state_admin(state_rows: list[dict]) -> MagicMock:
    """Admin mock with get_character_state RPC returning given rows."""
    admin_mock = MagicMock()

    rpc_result = MagicMock()
    rpc_result.data = state_rows
    admin_mock.rpc.return_value.execute = AsyncMock(return_value=rpc_result)

    return admin_mock


# ── Section 1: GET /api/character/crystals ────────────────────────────────────


class TestCrystalBalance:
    """GET /api/character/crystals — crystal ledger sum."""

    @pytest.mark.asyncio
    async def test_crystals_sums_ledger_entries(self):
        """Rows [50, 100, -20] → crystal_balance == 130."""
        ledger_rows = [{"amount": 50}, {"amount": 100}, {"amount": -20}]
        admin_mock = make_ledger_admin(ledger_rows)
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.get("/api/character/crystals")

            assert resp.status_code == 200
            body = resp.json()
            assert body["crystal_balance"] == 130
            assert body["user_id"] == USER_ID
            assert body["computed_at"] is not None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_crystals_returns_zero_for_new_user(self):
        """Empty ledger → crystal_balance == 0 (not null, not negative)."""
        admin_mock = make_ledger_admin([])
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.get("/api/character/crystals")

            assert resp.status_code == 200
            body = resp.json()
            assert body["crystal_balance"] == 0
            assert body["crystal_balance"] is not None
            assert body["crystal_balance"] >= 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_crystals_floors_at_zero(self):
        """Net negative ledger (defensive case) → crystal_balance == 0, never -50."""
        admin_mock = make_ledger_admin([{"amount": -50}])
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.get("/api/character/crystals")

            assert resp.status_code == 200
            body = resp.json()
            assert body["crystal_balance"] == 0
            assert body["crystal_balance"] != -50
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_crystals_requires_auth(self):
        """GET /api/character/crystals without JWT returns 401.

        Note: get_current_user_id depends on get_supabase_admin. FastAPI resolves
        the admin dep BEFORE the auth check can short-circuit — so we must provide
        a minimal admin mock to avoid acreate_client(supabase_key=None) crash in CI.
        """
        admin_mock = MagicMock()

        async def override_admin():
            yield admin_mock

        app.dependency_overrides[get_supabase_admin] = override_admin
        app.dependency_overrides[get_supabase_user] = override_admin
        # Intentionally do NOT override get_current_user_id — let auth fail.

        try:
            async with make_client() as client:
                resp = await client.get(
                    "/api/character/crystals"
                    # intentionally no Authorization header
                )
            assert resp.status_code == 401, (
                f"Crystal endpoint must require auth — got {resp.status_code}"
            )
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)


# ── Section 2: GET /api/character/state ──────────────────────────────────────


class TestCharacterState:
    """GET /api/character/state — full state via get_character_state RPC."""

    @pytest.mark.asyncio
    async def test_state_returns_full_state(self):
        """RPC returns a state row → endpoint returns it correctly."""
        state_row = {
            "user_id": USER_ID,
            "crystal_balance": 100,
            "xp_total": 500,
            "verified_skills": [],
            "character_stats": {},
            "login_streak": 5,
            "event_count": 20,
            "last_event_at": None,
            "computed_at": "2026-03-29T00:00:00Z",
        }
        admin_mock = make_state_admin([state_row])
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.get("/api/character/state")

            assert resp.status_code == 200
            body = resp.json()
            assert body["crystal_balance"] == 100
            assert body["xp_total"] == 500
            assert body["login_streak"] == 5
            assert body["event_count"] == 20
            # Confirm RPC was called with correct user_id
            admin_mock.rpc.assert_called_once_with(
                "get_character_state", {"p_user_id": USER_ID}
            )
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_state_returns_empty_for_new_user(self):
        """RPC returns [] (new user with no events) → default zero state returned."""
        admin_mock = make_state_admin([])
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.get("/api/character/state")

            assert resp.status_code == 200
            body = resp.json()
            assert body["crystal_balance"] == 0
            assert body["xp_total"] == 0
            assert body["verified_skills"] == []
            assert body["login_streak"] == 0
            assert body["event_count"] == 0
            assert body["computed_at"] is not None
        finally:
            app.dependency_overrides.clear()


# ── Section 3: POST /api/character/events ─────────────────────────────────────


def make_post_mock(
    *,
    rewards_rows: list[dict] | None = None,
    ledger_today_rows: list[dict] | None = None,
    rpc_deduct_result: list[dict] | None = None,
) -> MagicMock:
    """Build an admin mock for POST /api/character/events.

    Routes different table names to the correct mock chain:
    - character_events   → insert().execute()  (stores the event)
    - game_crystal_ledger → select()/insert()
    - game_character_rewards → select()/upsert()
    - rpc("deduct_crystals_atomic") → execute()

    All defaults produce a happy-path result unless overridden by kwargs.
    """
    if rewards_rows is None:
        rewards_rows = []
    if ledger_today_rows is None:
        ledger_today_rows = []
    if rpc_deduct_result is None:
        rpc_deduct_result = [{"success": True}]

    admin_mock = MagicMock()

    # ── character_events INSERT mock ─────────────────────────────────────────
    events_insert_result = MagicMock()
    events_insert_result.data = [
        {
            "id": str(uuid4()),
            "user_id": USER_ID,
            "event_type": "crystal_earned",
            "payload": {"amount": 50, "source": "volaura_assessment", "_schema_version": 1},
            "source_product": "volaura",
            "created_at": "2026-03-29T00:00:00Z",
        }
    ]

    # ── game_crystal_ledger INSERT mock ──────────────────────────────────────
    ledger_insert_result = MagicMock()
    ledger_insert_result.data = [{"id": str(uuid4())}]

    # ── game_crystal_ledger SELECT mock (daily cap check) ────────────────────
    # Chain: .select().eq().eq().gte().execute()
    ledger_select_result = MagicMock()
    ledger_select_result.data = ledger_today_rows
    ledger_select_chain = MagicMock()
    ledger_select_chain.eq.return_value.eq.return_value.gte.return_value.execute = AsyncMock(
        return_value=ledger_select_result
    )

    # ── game_crystal_ledger table mock: routes select vs insert ──────────────
    ledger_table_mock = MagicMock()
    ledger_table_mock.select.return_value = ledger_select_chain
    ledger_table_mock.insert.return_value.execute = AsyncMock(return_value=ledger_insert_result)

    # ── game_character_rewards SELECT mock (idempotency) ─────────────────────
    # Chain: .select().eq().eq().execute()
    rewards_select_result = MagicMock()
    rewards_select_result.data = rewards_rows
    rewards_select_chain = MagicMock()
    rewards_select_chain.eq.return_value.eq.return_value.execute = AsyncMock(
        return_value=rewards_select_result
    )

    # ── game_character_rewards UPSERT mock ───────────────────────────────────
    rewards_upsert_result = MagicMock()
    rewards_upsert_result.data = [{}]

    rewards_table_mock = MagicMock()
    rewards_table_mock.select.return_value = rewards_select_chain
    rewards_table_mock.upsert.return_value.execute = AsyncMock(return_value=rewards_upsert_result)

    # ── Route table() calls by name ──────────────────────────────────────────
    def mock_table(table_name: str):
        if table_name == "character_events":
            m = MagicMock()
            m.insert.return_value.execute = AsyncMock(return_value=events_insert_result)
            return m
        if table_name == "game_crystal_ledger":
            return ledger_table_mock
        if table_name == "game_character_rewards":
            return rewards_table_mock
        # Fallback for any other table — empty data
        fallback = MagicMock()
        fallback_result = MagicMock()
        fallback_result.data = []
        fallback.select.return_value.eq.return_value.execute = AsyncMock(return_value=fallback_result)
        fallback.insert.return_value.execute = AsyncMock(return_value=fallback_result)
        return fallback

    admin_mock.table = mock_table

    # ── rpc("deduct_crystals_atomic") mock ───────────────────────────────────
    rpc_result = MagicMock()
    rpc_result.data = rpc_deduct_result
    admin_mock.rpc.return_value.execute = AsyncMock(return_value=rpc_result)

    return admin_mock


class TestCharacterEventWrite:
    """POST /api/character/events — P0-2 validation, P0-3 atomic deduction,
    P0-3 idempotency, and P1-6 daily cap enforcement."""

    # ── P0-2: Crystal amount validation ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_crystal_event_invalid_amount_zero(self):
        """payload.amount == 0 → 422 INVALID_CRYSTAL_AMOUNT (zero is not positive)."""
        admin_mock = make_post_mock()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/character/events",
                    json={
                        "event_type": "crystal_earned",
                        "payload": {"amount": 0, "source": "volaura_assessment"},
                        "source_product": "volaura",
                    },
                )

            assert resp.status_code == 422
            body = resp.json()
            detail = body["detail"]
            assert detail["code"] == "INVALID_CRYSTAL_AMOUNT"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_crystal_event_invalid_amount_negative(self):
        """payload.amount == -10 → 422 INVALID_CRYSTAL_AMOUNT (negative is not positive)."""
        admin_mock = make_post_mock()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/character/events",
                    json={
                        "event_type": "crystal_earned",
                        "payload": {"amount": -10, "source": "volaura_assessment"},
                        "source_product": "volaura",
                    },
                )

            assert resp.status_code == 422
            body = resp.json()
            detail = body["detail"]
            assert detail["code"] == "INVALID_CRYSTAL_AMOUNT"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_crystal_event_invalid_amount_string(self):
        """payload.amount == "fifty" → 422 INVALID_CRYSTAL_AMOUNT (string is not int)."""
        admin_mock = make_post_mock()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/character/events",
                    json={
                        "event_type": "crystal_earned",
                        "payload": {"amount": "fifty", "source": "volaura_assessment"},
                        "source_product": "volaura",
                    },
                )

            assert resp.status_code == 422
            body = resp.json()
            detail = body["detail"]
            assert detail["code"] == "INVALID_CRYSTAL_AMOUNT"
        finally:
            app.dependency_overrides.clear()

    # ── Happy path: crystal_earned succeeds ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_crystal_earned_succeeds(self):
        """Valid crystal_earned with skill_slug → 201, event_type matches."""
        admin_mock = make_post_mock()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/character/events",
                    json={
                        "event_type": "crystal_earned",
                        "payload": {
                            "amount": 50,
                            "source": "volaura_assessment",
                            "skill_slug": "communication",
                        },
                        "source_product": "volaura",
                    },
                )

            assert resp.status_code == 201
            body = resp.json()
            assert body["event_type"] == "crystal_earned"
            assert body["user_id"] == USER_ID
            assert "id" in body
        finally:
            app.dependency_overrides.clear()

    # ── P0-3: crystal_spent — insufficient balance ────────────────────────────

    @pytest.mark.asyncio
    async def test_crystal_spent_insufficient_balance(self):
        """RPC returns success=False with INSUFFICIENT_BALANCE → 422 with that code."""
        admin_mock = make_post_mock(
            rpc_deduct_result=[
                {
                    "success": False,
                    "error_code": "INSUFFICIENT_BALANCE",
                    "error_msg": "Not enough crystals",
                }
            ]
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/character/events",
                    json={
                        "event_type": "crystal_spent",
                        "payload": {"amount": 100, "source": "mindshift_boost"},
                        "source_product": "mindshift",
                    },
                )

            assert resp.status_code == 422
            body = resp.json()
            detail = body["detail"]
            assert detail["code"] == "INSUFFICIENT_BALANCE"
        finally:
            app.dependency_overrides.clear()

    # ── P0-3: Idempotency — reward already claimed ────────────────────────────

    @pytest.mark.asyncio
    async def test_reward_already_claimed_idempotency(self):
        """game_character_rewards has a row for this skill → 409 REWARD_ALREADY_CLAIMED."""
        admin_mock = make_post_mock(
            rewards_rows=[{"claimed": True}]
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/character/events",
                    json={
                        "event_type": "crystal_earned",
                        "payload": {
                            "amount": 50,
                            "source": "volaura_assessment",
                            "skill_slug": "communication",
                        },
                        "source_product": "volaura",
                    },
                )

            assert resp.status_code == 409
            body = resp.json()
            detail = body["detail"]
            assert detail["code"] == "REWARD_ALREADY_CLAIMED"
        finally:
            app.dependency_overrides.clear()

    # ── P1-6: Daily crystal cap ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_daily_cap_reached(self):
        """Ledger already has 15 crystals from daily_login today → 422 DAILY_CRYSTAL_CAP_REACHED."""
        # DAILY_CRYSTAL_CAP["daily_login"] == 15; returning a row with amount=15 means cap is hit
        admin_mock = make_post_mock(
            ledger_today_rows=[{"amount": 15}]
        )
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_supabase_user] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            async with make_client() as client:
                resp = await client.post(
                    "/api/character/events",
                    json={
                        "event_type": "crystal_earned",
                        "payload": {"amount": 5, "source": "daily_login"},
                        "source_product": "volaura",
                    },
                )

            assert resp.status_code == 422
            body = resp.json()
            detail = body["detail"]
            assert detail["code"] == "DAILY_CRYSTAL_CAP_REACHED"
        finally:
            app.dependency_overrides.clear()
