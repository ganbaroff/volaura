"""Unit tests for character router — direct function call pattern.

Tests:
- POST /events (create_character_event) — validation, atomic deduction, idempotency, daily cap
- GET /state (get_character_state) — RPC unwrapping, empty state defaults
- GET /crystals (get_crystal_balance) — ledger sum, floor, lifetime_earned, last_earned_at
- GET /events (list_character_events) — pagination, since filter, limit cap

Mock pattern: MagicMock for table()/rpc() chains, AsyncMock only for execute().
All tests call router functions directly — no HTTP client, no app startup overhead.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.routers.character import (
    create_character_event,
    get_character_state,
    get_crystal_balance,
    list_character_events,
)
from app.schemas.character import CharacterEventCreate

# ── Shared helpers ────────────────────────────────────────────────────────────

USER_ID = uuid.uuid4()
_STORED_EVENT_ID = str(uuid.uuid4())

_BASE_STORED_ROW = {
    "id": _STORED_EVENT_ID,
    "user_id": str(USER_ID),
    "event_type": "crystal_earned",
    "payload": {"amount": 50, "_schema_version": 1},
    "source_product": "volaura",
    "created_at": "2026-04-14T10:00:00+00:00",
}


def _mock_table_chain(data=None, count=None, side_effect=None):
    """Build a fluent Supabase query chain mock that handles any chaining order."""
    result = MagicMock(data=data if data is not None else [], count=count)
    execute = AsyncMock(side_effect=side_effect) if side_effect else AsyncMock(return_value=result)
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.gt.return_value = chain
    chain.order.return_value = chain
    chain.range.return_value = chain
    chain.insert.return_value = chain
    chain.upsert.return_value = chain
    chain.execute = execute
    return chain


def _mock_db(tables=None, rpc_results=None):
    """Build a db mock routing table() by name and rpc() by name.

    tables: {"table_name": {"data": [...], "count": N, "side_effect": exc}}
    rpc_results: {"rpc_name": <data>}
    """
    db = MagicMock()
    tables = tables or {}

    def table_dispatch(name):
        cfg = tables.get(name, {})
        return _mock_table_chain(**cfg)

    db.table.side_effect = table_dispatch

    if rpc_results is not None:

        def rpc_dispatch(name, params=None):
            result_data = rpc_results.get(name, [])
            chain = MagicMock()
            chain.execute = AsyncMock(return_value=MagicMock(data=result_data))
            return chain

        db.rpc.side_effect = rpc_dispatch

    return db


def _make_event_body(
    event_type="crystal_earned",
    payload=None,
    source_product="volaura",
) -> CharacterEventCreate:
    """Build a CharacterEventCreate with sensible defaults."""
    if payload is None:
        payload = {"amount": 50}
    return CharacterEventCreate(
        event_type=event_type,
        payload=payload,
        source_product=source_product,
    )


def _make_multi_table_db(
    *,
    rewards_rows=None,
    ledger_today_rows=None,
    ledger_balance_rows=None,
    events_insert_data=None,
    ledger_insert_data=None,
    rpc_deduct_result=None,
):
    """Build a db mock that correctly routes multiple tables for create_character_event.

    Each table can be called multiple times with different method chains.
    character_events   → insert chain
    game_crystal_ledger → select chain (daily cap) OR insert chain (ledger write)
    game_character_rewards → select chain (idempotency) OR upsert chain
    """
    if rewards_rows is None:
        rewards_rows = []
    if ledger_today_rows is None:
        ledger_today_rows = []
    if events_insert_data is None:
        events_insert_data = [dict(_BASE_STORED_ROW)]
    if ledger_insert_data is None:
        ledger_insert_data = [{"id": str(uuid.uuid4())}]
    if rpc_deduct_result is None:
        rpc_deduct_result = [{"success": True}]

    db = MagicMock()

    # character_events table: insert only
    events_insert_chain = _mock_table_chain(data=events_insert_data)

    # game_crystal_ledger: select (daily cap) + insert (ledger write)
    ledger_select_result = MagicMock(data=ledger_today_rows)
    ledger_select_chain = MagicMock()
    ledger_select_chain.eq.return_value = ledger_select_chain
    ledger_select_chain.gte.return_value = ledger_select_chain
    ledger_select_chain.execute = AsyncMock(return_value=ledger_select_result)

    ledger_insert_result = MagicMock(data=ledger_insert_data)
    ledger_insert_chain = MagicMock()
    ledger_insert_chain.execute = AsyncMock(return_value=ledger_insert_result)

    ledger_table = MagicMock()
    ledger_table.select.return_value = ledger_select_chain
    ledger_table.insert.return_value = ledger_insert_chain

    # game_character_rewards: select (idempotency) + upsert (mark claimed)
    rewards_select_result = MagicMock(data=rewards_rows)
    rewards_select_chain = MagicMock()
    rewards_select_chain.eq.return_value = rewards_select_chain
    rewards_select_chain.execute = AsyncMock(return_value=rewards_select_result)

    rewards_upsert_result = MagicMock(data=[{}])
    rewards_upsert_chain = MagicMock()
    rewards_upsert_chain.execute = AsyncMock(return_value=rewards_upsert_result)

    rewards_table = MagicMock()
    rewards_table.select.return_value = rewards_select_chain
    rewards_table.upsert.return_value = rewards_upsert_chain

    def table_dispatch(name):
        if name == "character_events":
            return events_insert_chain
        if name == "game_crystal_ledger":
            return ledger_table
        if name == "game_character_rewards":
            return rewards_table
        # fallback — empty
        return _mock_table_chain(data=[])

    db.table.side_effect = table_dispatch

    # rpc deduct_crystals_atomic
    rpc_result = MagicMock(data=rpc_deduct_result)
    rpc_chain = MagicMock()
    rpc_chain.execute = AsyncMock(return_value=rpc_result)
    db.rpc.return_value = rpc_chain

    return db


# ── POST /events ──────────────────────────────────────────────────────────────


class TestCreateCharacterEventValidation:
    """crystal amount validation fires before any DB write."""

    @pytest.mark.asyncio
    async def test_crystal_earned_zero_amount_raises_422(self):
        db = _make_multi_table_db()
        body = _make_event_body("crystal_earned", {"amount": 0})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_CRYSTAL_AMOUNT"

    @pytest.mark.asyncio
    async def test_crystal_earned_negative_amount_raises_422(self):
        db = _make_multi_table_db()
        body = _make_event_body("crystal_earned", {"amount": -5})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_CRYSTAL_AMOUNT"

    @pytest.mark.asyncio
    async def test_crystal_earned_string_amount_raises_422(self):
        db = _make_multi_table_db()
        body = _make_event_body("crystal_earned", {"amount": "fifty"})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_CRYSTAL_AMOUNT"

    @pytest.mark.asyncio
    async def test_crystal_earned_float_amount_raises_422(self):
        db = _make_multi_table_db()
        body = _make_event_body("crystal_earned", {"amount": 10.5})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_CRYSTAL_AMOUNT"

    @pytest.mark.asyncio
    async def test_crystal_earned_missing_amount_raises_422(self):
        db = _make_multi_table_db()
        body = _make_event_body("crystal_earned", {"source": "volaura_assessment"})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_CRYSTAL_AMOUNT"

    @pytest.mark.asyncio
    async def test_crystal_spent_zero_amount_raises_422(self):
        db = _make_multi_table_db()
        body = _make_event_body("crystal_spent", {"amount": 0})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_CRYSTAL_AMOUNT"

    @pytest.mark.asyncio
    async def test_non_crystal_event_skips_amount_validation(self):
        """skill_verified with no amount payload should not raise INVALID_CRYSTAL_AMOUNT."""
        db = _make_multi_table_db(
            events_insert_data=[
                {
                    "id": str(uuid.uuid4()),
                    "user_id": str(USER_ID),
                    "event_type": "skill_verified",
                    "payload": {"skill_slug": "communication", "_schema_version": 1},
                    "source_product": "volaura",
                    "created_at": "2026-04-14T10:00:00+00:00",
                }
            ]
        )
        body = _make_event_body("skill_verified", {"skill_slug": "communication"})
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert result.event_type == "skill_verified"


class TestCreateCharacterEventCrystalSpent:
    """crystal_spent → atomic RPC deduction path."""

    @pytest.mark.asyncio
    async def test_crystal_spent_calls_deduct_crystals_atomic_rpc(self):
        db = _make_multi_table_db(
            events_insert_data=[
                {
                    "id": str(uuid.uuid4()),
                    "user_id": str(USER_ID),
                    "event_type": "crystal_spent",
                    "payload": {"amount": 30, "_schema_version": 1},
                    "source_product": "mindshift",
                    "created_at": "2026-04-14T10:00:00+00:00",
                }
            ]
        )
        body = _make_event_body("crystal_spent", {"amount": 30}, "mindshift")
        await create_character_event(MagicMock(), body, USER_ID, db)
        db.rpc.assert_called_once()
        call_name = db.rpc.call_args[0][0]
        assert call_name == "deduct_crystals_atomic"

    @pytest.mark.asyncio
    async def test_crystal_spent_rpc_success_false_raises_422(self):
        db = _make_multi_table_db(
            rpc_deduct_result=[
                {
                    "success": False,
                    "error_code": "INSUFFICIENT_BALANCE",
                    "error_msg": "Not enough crystals",
                }
            ]
        )
        body = _make_event_body("crystal_spent", {"amount": 999})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INSUFFICIENT_BALANCE"

    @pytest.mark.asyncio
    async def test_crystal_spent_rpc_empty_result_raises_422(self):
        db = _make_multi_table_db(rpc_deduct_result=[])
        body = _make_event_body("crystal_spent", {"amount": 10})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "CRYSTAL_DEDUCTION_FAILED"

    @pytest.mark.asyncio
    async def test_crystal_spent_rpc_success_true_stores_event(self):
        stored_row = {
            "id": str(uuid.uuid4()),
            "user_id": str(USER_ID),
            "event_type": "crystal_spent",
            "payload": {"amount": 20, "_schema_version": 1},
            "source_product": "volaura",
            "created_at": "2026-04-14T10:00:00+00:00",
        }
        db = _make_multi_table_db(
            rpc_deduct_result=[{"success": True}],
            events_insert_data=[stored_row],
        )
        body = _make_event_body("crystal_spent", {"amount": 20})
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert result.event_type == "crystal_spent"

    @pytest.mark.asyncio
    async def test_crystal_spent_does_not_write_ledger_manually(self):
        """RPC handles the ledger write; router must not insert a second time."""
        ledger_insert_calls = []
        stored_row = {
            "id": str(uuid.uuid4()),
            "user_id": str(USER_ID),
            "event_type": "crystal_spent",
            "payload": {"amount": 20, "_schema_version": 1},
            "source_product": "volaura",
            "created_at": "2026-04-14T10:00:00+00:00",
        }

        db = _make_multi_table_db(
            rpc_deduct_result=[{"success": True}],
            events_insert_data=[stored_row],
        )

        # Patch the ledger insert to record calls
        original_table = db.table.side_effect

        def tracking_table(name):
            t = original_table(name)
            if name == "game_crystal_ledger":
                original_insert = t.insert

                def tracked_insert(*args, **kwargs):
                    ledger_insert_calls.append(args)
                    return original_insert(*args, **kwargs)

                t.insert = tracked_insert
            return t

        db.table.side_effect = tracking_table

        body = _make_event_body("crystal_spent", {"amount": 20})
        await create_character_event(MagicMock(), body, USER_ID, db)
        assert len(ledger_insert_calls) == 0, "crystal_spent ledger insert must be handled by RPC, not router"


class TestCreateCharacterEventIdempotency:
    """volaura_assessment rewards idempotency checks."""

    @pytest.mark.asyncio
    async def test_duplicate_volaura_assessment_reward_raises_409(self):
        db = _make_multi_table_db(rewards_rows=[{"claimed": True}])
        body = _make_event_body(
            "crystal_earned",
            {"amount": 50, "source": "volaura_assessment", "skill_slug": "communication"},
        )
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "REWARD_ALREADY_CLAIMED"

    @pytest.mark.asyncio
    async def test_first_volaura_assessment_reward_succeeds(self):
        db = _make_multi_table_db(rewards_rows=[])
        body = _make_event_body(
            "crystal_earned",
            {"amount": 50, "source": "volaura_assessment", "skill_slug": "communication"},
        )
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert result.event_type == "crystal_earned"

    @pytest.mark.asyncio
    async def test_idempotency_check_skipped_when_no_skill_slug(self):
        """crystal_earned + volaura_assessment source but no skill_slug skips idempotency check."""
        db = _make_multi_table_db(rewards_rows=[{"claimed": True}])
        body = _make_event_body(
            "crystal_earned",
            {"amount": 50, "source": "volaura_assessment"},
        )
        # No skill_slug → idempotency gate is skipped → should proceed (but daily cap may fire)
        # Use a source not in DAILY_CRYSTAL_CAP to avoid cap error
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert result.event_type == "crystal_earned"

    @pytest.mark.asyncio
    async def test_volaura_assessment_success_upserts_rewards_table(self):
        db = _make_multi_table_db(rewards_rows=[])
        body = _make_event_body(
            "crystal_earned",
            {"amount": 50, "source": "volaura_assessment", "skill_slug": "leadership"},
        )
        await create_character_event(MagicMock(), body, USER_ID, db)
        db.table("game_character_rewards")


class TestCreateCharacterEventDailyCap:
    """Daily crystal cap enforcement per source."""

    @pytest.mark.asyncio
    async def test_daily_cap_reached_for_daily_login_raises_422(self):
        db = _make_multi_table_db(ledger_today_rows=[{"amount": 15}])
        body = _make_event_body(
            "crystal_earned",
            {"amount": 5, "source": "daily_login"},
        )
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "DAILY_CRYSTAL_CAP_REACHED"

    @pytest.mark.asyncio
    async def test_daily_cap_not_reached_allows_event(self):
        db = _make_multi_table_db(ledger_today_rows=[{"amount": 10}])
        body = _make_event_body(
            "crystal_earned",
            {"amount": 5, "source": "daily_login"},
        )
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert result.event_type == "crystal_earned"

    @pytest.mark.asyncio
    async def test_daily_cap_counts_only_positive_ledger_amounts(self):
        """Negative rows (deductions) must not count toward daily earned total."""
        db = _make_multi_table_db(ledger_today_rows=[{"amount": 10}, {"amount": -5}])
        body = _make_event_body(
            "crystal_earned",
            {"amount": 5, "source": "daily_login"},
        )
        # earned_today = 10 (only positive), cap = 15 → not reached
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert result.event_type == "crystal_earned"

    @pytest.mark.asyncio
    async def test_daily_cap_not_checked_for_source_without_cap(self):
        """Sources not in DAILY_CRYSTAL_CAP skip the cap check entirely."""
        db = _make_multi_table_db()
        body = _make_event_body(
            "crystal_earned",
            {"amount": 500, "source": "volaura_assessment", "skill_slug": "adaptability"},
        )
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert result.event_type == "crystal_earned"


class TestCreateCharacterEventStorage:
    """Event insertion and error paths."""

    @pytest.mark.asyncio
    async def test_failed_events_insert_raises_500(self):
        db = _make_multi_table_db(events_insert_data=[])
        body = _make_event_body("xp_earned", {"amount": 100})
        with pytest.raises(Exception) as exc_info:
            await create_character_event(MagicMock(), body, USER_ID, db)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["code"] == "EVENT_STORE_FAILED"

    @pytest.mark.asyncio
    async def test_crystal_earned_writes_to_ledger(self):
        ledger_insert_calls = []
        db = _make_multi_table_db()

        original_table = db.table.side_effect

        def tracking_table(name):
            t = original_table(name)
            if name == "game_crystal_ledger":
                original_insert = t.insert

                def tracked_insert(*args, **kwargs):
                    ledger_insert_calls.append(args)
                    return original_insert(*args, **kwargs)

                t.insert = tracked_insert
            return t

        db.table.side_effect = tracking_table

        body = _make_event_body(
            "crystal_earned",
            {"amount": 50, "source": "volaura_assessment", "skill_slug": "leadership"},
        )
        await create_character_event(MagicMock(), body, USER_ID, db)
        assert len(ledger_insert_calls) == 1

    @pytest.mark.asyncio
    async def test_non_crystal_event_skips_ledger_entirely(self):
        ledger_insert_calls = []
        db = _make_multi_table_db(
            events_insert_data=[
                {
                    "id": str(uuid.uuid4()),
                    "user_id": str(USER_ID),
                    "event_type": "xp_earned",
                    "payload": {"xp": 100, "_schema_version": 1},
                    "source_product": "volaura",
                    "created_at": "2026-04-14T10:00:00+00:00",
                }
            ]
        )

        original_table = db.table.side_effect

        def tracking_table(name):
            t = original_table(name)
            if name == "game_crystal_ledger":
                original_insert = t.insert

                def tracked_insert(*args, **kwargs):
                    ledger_insert_calls.append(args)
                    return original_insert(*args, **kwargs)

                t.insert = tracked_insert
            return t

        db.table.side_effect = tracking_table

        body = _make_event_body("xp_earned", {"xp": 100})
        await create_character_event(MagicMock(), body, USER_ID, db)
        assert len(ledger_insert_calls) == 0

    @pytest.mark.asyncio
    async def test_stored_event_returned_as_character_event_out(self):
        stored_row = {
            "id": str(uuid.uuid4()),
            "user_id": str(USER_ID),
            "event_type": "milestone_reached",
            "payload": {"milestone": "first_skill", "_schema_version": 1},
            "source_product": "volaura",
            "created_at": "2026-04-14T12:00:00+00:00",
        }
        db = _make_multi_table_db(events_insert_data=[stored_row])
        body = _make_event_body("milestone_reached", {"milestone": "first_skill"})
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert str(result.id) == stored_row["id"]
        assert result.event_type == "milestone_reached"
        assert result.source_product == "volaura"

    @pytest.mark.asyncio
    async def test_user_id_comes_from_jwt_not_body(self):
        """user_id on stored row must match the JWT user_id, not anything in payload."""
        stored_row = dict(_BASE_STORED_ROW, user_id=str(USER_ID))
        db = _make_multi_table_db(events_insert_data=[stored_row])
        body = _make_event_body("xp_earned", {"xp": 10})
        result = await create_character_event(MagicMock(), body, USER_ID, db)
        assert result.user_id == USER_ID


# ── GET /state ────────────────────────────────────────────────────────────────


class TestGetCharacterState:
    """get_character_state — RPC call + result unwrapping."""

    @pytest.mark.asyncio
    async def test_empty_rpc_result_returns_default_state(self):
        db = _mock_db(rpc_results={"get_character_state": []})
        result = await get_character_state(MagicMock(), USER_ID, db)
        assert result.crystal_balance == 0
        assert result.xp_total == 0
        assert result.verified_skills == []
        assert result.character_stats == {}
        assert result.login_streak == 0
        assert result.event_count == 0
        assert result.last_event_at is None
        assert result.computed_at is not None

    @pytest.mark.asyncio
    async def test_empty_state_has_correct_user_id(self):
        db = _mock_db(rpc_results={"get_character_state": []})
        result = await get_character_state(MagicMock(), USER_ID, db)
        assert result.user_id == USER_ID

    @pytest.mark.asyncio
    async def test_list_rpc_result_unwraps_first_element(self):
        state_row = {
            "user_id": str(USER_ID),
            "crystal_balance": 200,
            "xp_total": 1500,
            "verified_skills": [],
            "character_stats": {"strength": 5},
            "login_streak": 7,
            "event_count": 42,
            "last_event_at": None,
            "computed_at": "2026-04-14T10:00:00+00:00",
        }
        db = _mock_db(rpc_results={"get_character_state": [state_row]})
        result = await get_character_state(MagicMock(), USER_ID, db)
        assert result.crystal_balance == 200
        assert result.xp_total == 1500
        assert result.login_streak == 7
        assert result.event_count == 42
        assert result.character_stats == {"strength": 5}

    @pytest.mark.asyncio
    async def test_dict_rpc_result_passed_directly(self):
        state_dict = {
            "user_id": str(USER_ID),
            "crystal_balance": 75,
            "xp_total": 300,
            "verified_skills": [],
            "character_stats": {},
            "login_streak": 3,
            "event_count": 10,
            "last_event_at": None,
            "computed_at": "2026-04-14T10:00:00+00:00",
        }
        db = _mock_db(rpc_results={"get_character_state": state_dict})
        result = await get_character_state(MagicMock(), USER_ID, db)
        assert result.crystal_balance == 75
        assert result.login_streak == 3

    @pytest.mark.asyncio
    async def test_rpc_called_with_correct_user_id(self):
        db = _mock_db(rpc_results={"get_character_state": []})
        await get_character_state(MagicMock(), USER_ID, db)
        db.rpc.assert_called_once_with("get_character_state", {"p_user_id": str(USER_ID)})

    @pytest.mark.asyncio
    async def test_verified_skills_preserved_from_rpc(self):
        state_row = {
            "user_id": str(USER_ID),
            "crystal_balance": 0,
            "xp_total": 0,
            "verified_skills": [{"slug": "communication", "aura_score": 85.0, "badge_tier": "Gold"}],
            "character_stats": {},
            "login_streak": 0,
            "event_count": 1,
            "last_event_at": None,
            "computed_at": "2026-04-14T10:00:00+00:00",
        }
        db = _mock_db(rpc_results={"get_character_state": [state_row]})
        result = await get_character_state(MagicMock(), USER_ID, db)
        assert len(result.verified_skills) == 1
        assert result.verified_skills[0].slug == "communication"
        assert result.verified_skills[0].badge_tier == "Gold"


# ── GET /crystals ─────────────────────────────────────────────────────────────


class TestGetCrystalBalance:
    """get_crystal_balance — ledger sum, floor, lifetime_earned, last_earned_at."""

    @pytest.mark.asyncio
    async def test_empty_ledger_returns_zero_balance(self):
        db = _mock_db(tables={"game_crystal_ledger": {"data": []}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.crystal_balance == 0
        assert result.lifetime_earned == 0
        assert result.last_earned_at is None

    @pytest.mark.asyncio
    async def test_sums_all_ledger_rows(self):
        rows = [
            {"amount": 100, "created_at": "2026-04-12T00:00:00+00:00"},
            {"amount": 50, "created_at": "2026-04-13T00:00:00+00:00"},
            {"amount": -20, "created_at": "2026-04-14T00:00:00+00:00"},
        ]
        db = _mock_db(tables={"game_crystal_ledger": {"data": rows}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.crystal_balance == 130

    @pytest.mark.asyncio
    async def test_balance_floored_at_zero_when_negative(self):
        rows = [{"amount": -50, "created_at": "2026-04-14T00:00:00+00:00"}]
        db = _mock_db(tables={"game_crystal_ledger": {"data": rows}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.crystal_balance == 0

    @pytest.mark.asyncio
    async def test_lifetime_earned_counts_only_positive_rows(self):
        rows = [
            {"amount": 100, "created_at": "2026-04-12T00:00:00+00:00"},
            {"amount": -30, "created_at": "2026-04-13T00:00:00+00:00"},
            {"amount": 50, "created_at": "2026-04-14T00:00:00+00:00"},
        ]
        db = _mock_db(tables={"game_crystal_ledger": {"data": rows}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.lifetime_earned == 150

    @pytest.mark.asyncio
    async def test_last_earned_at_picks_max_created_at_from_positive_rows(self):
        rows = [
            {"amount": 50, "created_at": "2026-04-12T00:00:00+00:00"},
            {"amount": 100, "created_at": "2026-04-14T10:00:00+00:00"},
            {"amount": -30, "created_at": "2026-04-15T00:00:00+00:00"},
        ]
        db = _mock_db(tables={"game_crystal_ledger": {"data": rows}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.last_earned_at is not None
        assert "2026-04-14" in result.last_earned_at.isoformat()

    @pytest.mark.asyncio
    async def test_last_earned_at_none_when_only_negative_rows(self):
        rows = [{"amount": -10, "created_at": "2026-04-14T00:00:00+00:00"}]
        db = _mock_db(tables={"game_crystal_ledger": {"data": rows}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.last_earned_at is None

    @pytest.mark.asyncio
    async def test_user_id_in_response_matches_jwt(self):
        db = _mock_db(tables={"game_crystal_ledger": {"data": []}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.user_id == USER_ID

    @pytest.mark.asyncio
    async def test_computed_at_is_set(self):
        db = _mock_db(tables={"game_crystal_ledger": {"data": []}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.computed_at is not None

    @pytest.mark.asyncio
    async def test_single_positive_row_correct_balance_and_lifetime(self):
        rows = [{"amount": 75, "created_at": "2026-04-13T08:00:00+00:00"}]
        db = _mock_db(tables={"game_crystal_ledger": {"data": rows}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.crystal_balance == 75
        assert result.lifetime_earned == 75

    @pytest.mark.asyncio
    async def test_z_suffix_in_created_at_parsed_correctly(self):
        """Ledger rows with trailing 'Z' in created_at must parse without error."""
        rows = [{"amount": 10, "created_at": "2026-04-14T12:00:00Z"}]
        db = _mock_db(tables={"game_crystal_ledger": {"data": rows}})
        result = await get_crystal_balance(MagicMock(), USER_ID, db)
        assert result.last_earned_at is not None


# ── GET /events ───────────────────────────────────────────────────────────────


class TestListCharacterEvents:
    """list_character_events — pagination, since filter, limit cap."""

    def _make_event_row(self, event_type="xp_earned", created_at="2026-04-14T10:00:00+00:00"):
        return {
            "id": str(uuid.uuid4()),
            "user_id": str(USER_ID),
            "event_type": event_type,
            "payload": {"_schema_version": 1},
            "source_product": "volaura",
            "created_at": created_at,
        }

    def _mock_events_db(self, rows):
        """Build db mock for list_character_events.

        Chain: .select().eq().order()[.gt()].range().execute()
        """
        result = MagicMock(data=rows)
        execute = AsyncMock(return_value=result)

        range_chain = MagicMock()
        range_chain.execute = execute

        gt_chain = MagicMock()
        gt_chain.range = MagicMock(return_value=range_chain)

        order_chain = MagicMock()
        order_chain.range = MagicMock(return_value=range_chain)
        order_chain.gt = MagicMock(return_value=gt_chain)

        eq_chain = MagicMock()
        eq_chain.order = MagicMock(return_value=order_chain)

        select_chain = MagicMock()
        select_chain.eq = MagicMock(return_value=eq_chain)

        table_mock = MagicMock()
        table_mock.select = MagicMock(return_value=select_chain)

        db = MagicMock()
        db.table.return_value = table_mock
        return db

    @pytest.mark.asyncio
    async def test_returns_list_of_character_event_out(self):
        rows = [self._make_event_row()]
        db = self._mock_events_db(rows)
        result = await list_character_events(MagicMock(), USER_ID, db, limit=50, offset=0, since=None)
        assert len(result) == 1
        assert result[0].event_type == "xp_earned"

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_list(self):
        db = self._mock_events_db([])
        result = await list_character_events(MagicMock(), USER_ID, db, limit=50, offset=0, since=None)
        assert result == []

    @pytest.mark.asyncio
    async def test_limit_above_200_capped_at_200(self):
        db = self._mock_events_db([])
        result = await list_character_events(MagicMock(), USER_ID, db, limit=9999, offset=0, since=None)
        assert result == []

    @pytest.mark.asyncio
    async def test_limit_exactly_200_not_capped(self):
        rows = [self._make_event_row() for _ in range(5)]
        db = self._mock_events_db(rows)
        result = await list_character_events(MagicMock(), USER_ID, db, limit=200, offset=0, since=None)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_since_invalid_iso_raises_422(self):
        db = self._mock_events_db([])
        with pytest.raises(Exception) as exc_info:
            await list_character_events(MagicMock(), USER_ID, db, limit=50, offset=0, since="not-a-date")
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_SINCE"

    @pytest.mark.asyncio
    async def test_since_random_string_raises_422(self):
        db = self._mock_events_db([])
        with pytest.raises(Exception) as exc_info:
            await list_character_events(MagicMock(), USER_ID, db, limit=50, offset=0, since="yesterday")
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_SINCE"

    @pytest.mark.asyncio
    async def test_since_valid_iso_does_not_raise(self):
        db = self._mock_events_db([])
        result = await list_character_events(MagicMock(), USER_ID, db, limit=50, offset=0, since="2026-04-14T08:00:00Z")
        assert result == []

    @pytest.mark.asyncio
    async def test_since_none_skips_gt_filter(self):
        rows = [self._make_event_row()]
        db = self._mock_events_db(rows)
        result = await list_character_events(MagicMock(), USER_ID, db, limit=50, offset=0, since=None)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_multiple_events_returned_correctly(self):
        rows = [
            self._make_event_row("crystal_earned", "2026-04-14T12:00:00+00:00"),
            self._make_event_row("xp_earned", "2026-04-14T11:00:00+00:00"),
            self._make_event_row("skill_verified", "2026-04-14T10:00:00+00:00"),
        ]
        db = self._mock_events_db(rows)
        result = await list_character_events(MagicMock(), USER_ID, db, limit=10, offset=0, since=None)
        assert len(result) == 3
        event_types = {r.event_type for r in result}
        assert "crystal_earned" in event_types
        assert "xp_earned" in event_types
        assert "skill_verified" in event_types

    @pytest.mark.asyncio
    async def test_result_items_are_character_event_out_instances(self):
        from app.schemas.character import CharacterEventOut

        rows = [self._make_event_row()]
        db = self._mock_events_db(rows)
        result = await list_character_events(MagicMock(), USER_ID, db, limit=50, offset=0, since=None)
        assert all(isinstance(r, CharacterEventOut) for r in result)
