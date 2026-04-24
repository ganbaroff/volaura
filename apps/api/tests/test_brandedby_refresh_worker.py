"""Tests for brandedby_refresh_worker.py — G3.3 personality refresh loop.

Coverage goals (target ≥90%):
  1. Happy path: stale twin → character state loaded → personality generated →
     apply called → refreshed=1
  2. No stale twins → refreshed=0, apply never called
  3. get_stale_twins RPC fails → returns empty stats (no crash)
  4. get_character_state fails → twin skipped, errors=1, other twins unaffected
  5. get_character_state returns empty dict → twin skipped (skipped=1)
  6. generate_twin_personality raises → errors=1, other twins still processed
  7. brandedby_apply_twin_personality fails → errors=1
  8. Multiple twins: fire-forward — one error doesn't block others
  9. RefreshStats dataclass defaults are zero
 10. Missing display_name in twin row → defaults to "Professional" (no crash)
 11. run_brandedby_refresh with injected db avoids _admin() (unit test, no creds)
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.brandedby_refresh_worker import (
    REFRESH_BATCH_SIZE,
    RefreshStats,
    run_brandedby_refresh,
)


# ── Fixtures & helpers ─────────────────────────────────────────────────────────


def _twin(
    twin_id: str | None = None,
    user_id: str | None = None,
    display_name: str = "Test User",
) -> dict:
    return {
        "id": twin_id or str(uuid4()),
        "user_id": user_id or str(uuid4()),
        "display_name": display_name,
    }


def _character_state(
    xp: int = 200,
    crystals: int = 50,
    skills: list | None = None,
) -> dict:
    return {
        "xp_total": xp,
        "crystal_balance": crystals,
        "login_streak": 3,
        "verified_skills": skills
        or [
            {"slug": "communication", "aura_score": 80.0, "badge_tier": "gold"},
        ],
    }


def _make_db(
    twins: list[dict] | None = None,
    character_state: dict | None = None,
    stale_twins_raises: Exception | None = None,
    character_state_raises: Exception | None = None,
    apply_raises: Exception | None = None,
):
    """Build a Supabase mock for refresh worker tests.

    The worker calls three RPCs in sequence per twin:
      1. brandedby_get_stale_twins  (once at top)
      2. get_character_state        (per twin)
      3. brandedby_apply_twin_personality (per twin)

    Each RPC call returns db.rpc(name, args).execute().
    We route by RPC name so each call path is independently controllable.
    """
    db = MagicMock()

    _twins = twins if twins is not None else []
    _state = character_state if character_state is not None else _character_state()

    def _rpc(name: str, params: dict):
        chain = MagicMock()
        if name == "brandedby_get_stale_twins":
            if stale_twins_raises:
                chain.execute = AsyncMock(side_effect=stale_twins_raises)
            else:
                chain.execute = AsyncMock(return_value=MagicMock(data=_twins))
        elif name == "get_character_state":
            if character_state_raises:
                chain.execute = AsyncMock(side_effect=character_state_raises)
            else:
                chain.execute = AsyncMock(return_value=MagicMock(data=_state))
        elif name == "brandedby_apply_twin_personality":
            if apply_raises:
                chain.execute = AsyncMock(side_effect=apply_raises)
            else:
                chain.execute = AsyncMock(return_value=MagicMock(data=None))
        else:
            chain.execute = AsyncMock(return_value=MagicMock(data=None))
        return chain

    db.rpc.side_effect = _rpc
    return db


_FAKE_PERSONALITY = "I am a professional with strong communication skills."


# ── Dataclass tests ────────────────────────────────────────────────────────────


def test_refresh_stats_defaults():
    s = RefreshStats()
    assert s.refreshed == 0
    assert s.skipped == 0
    assert s.errors == 0


def test_refresh_batch_size_default():
    """REFRESH_BATCH_SIZE defaults to 20 — free-tier safe."""
    assert REFRESH_BATCH_SIZE == 20


# ── Happy path ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_happy_path_one_twin_refreshed():
    """Full success path: stale twin → state loaded → personality → apply → refreshed=1."""
    twin = _twin()
    db = _make_db(twins=[twin])

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
        return_value=_FAKE_PERSONALITY,
    ) as mock_gen:
        stats = await run_brandedby_refresh(db)

    assert stats.refreshed == 1
    assert stats.skipped == 0
    assert stats.errors == 0

    # Personality generator called with correct args
    mock_gen.assert_called_once_with(twin["display_name"], _character_state())

    # apply RPC called with correct twin_id and personality
    apply_calls = [
        call
        for call in db.rpc.call_args_list
        if call.args[0] == "brandedby_apply_twin_personality"
    ]
    assert len(apply_calls) == 1
    assert apply_calls[0].args[1]["p_twin_id"] == twin["id"]
    assert apply_calls[0].args[1]["p_personality"] == _FAKE_PERSONALITY


# ── No stale twins ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_stale_twins_returns_zero_stats():
    """No stale twins → refreshed=0, apply never called."""
    db = _make_db(twins=[])

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
    ) as mock_gen:
        stats = await run_brandedby_refresh(db)

    assert stats.refreshed == 0
    assert stats.skipped == 0
    assert stats.errors == 0
    mock_gen.assert_not_called()

    # apply RPC never called
    apply_calls = [
        c for c in db.rpc.call_args_list
        if c.args[0] == "brandedby_apply_twin_personality"
    ]
    assert len(apply_calls) == 0


# ── get_stale_twins RPC failure ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stale_twins_rpc_failure_returns_empty_stats():
    """get_stale_twins RPC crash → empty stats returned, no exception propagated."""
    db = _make_db(
        twins=[_twin()],
        stale_twins_raises=RuntimeError("supabase connection error"),
    )

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
    ) as mock_gen:
        stats = await run_brandedby_refresh(db)

    assert stats.refreshed == 0
    assert stats.skipped == 0
    assert stats.errors == 0
    mock_gen.assert_not_called()


# ── get_character_state failure ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_character_state_rpc_failure_increments_errors():
    """get_character_state raises → errors=1, twin skipped."""
    twin = _twin()
    db = _make_db(
        twins=[twin],
        character_state_raises=RuntimeError("get_character_state timed out"),
    )

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
    ) as mock_gen:
        stats = await run_brandedby_refresh(db)

    assert stats.refreshed == 0
    assert stats.errors == 1
    assert stats.skipped == 0
    mock_gen.assert_not_called()


@pytest.mark.asyncio
async def test_empty_character_state_increments_skipped():
    """get_character_state returns empty dict → twin skipped (skipped=1, not error)."""
    twin = _twin()
    db = _make_db(twins=[twin], character_state={})

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
    ) as mock_gen:
        stats = await run_brandedby_refresh(db)

    assert stats.refreshed == 0
    assert stats.skipped == 1
    assert stats.errors == 0
    mock_gen.assert_not_called()


# ── generate_twin_personality raises ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_personality_generation_raises_increments_errors():
    """generate_twin_personality raises → errors=1, no apply called."""
    twin = _twin()
    db = _make_db(twins=[twin])

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LLM quota exceeded"),
    ):
        stats = await run_brandedby_refresh(db)

    assert stats.refreshed == 0
    assert stats.errors == 1

    apply_calls = [
        c for c in db.rpc.call_args_list
        if c.args[0] == "brandedby_apply_twin_personality"
    ]
    assert len(apply_calls) == 0


# ── apply_twin_personality failure ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_personality_failure_increments_errors():
    """brandedby_apply_twin_personality raises → errors=1."""
    twin = _twin()
    db = _make_db(twins=[twin], apply_raises=RuntimeError("update failed"))

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
        return_value=_FAKE_PERSONALITY,
    ):
        stats = await run_brandedby_refresh(db)

    assert stats.refreshed == 0
    assert stats.errors == 1


# ── Fire-forward: errors on one twin don't block others ───────────────────────


@pytest.mark.asyncio
async def test_fire_forward_one_error_does_not_block_others():
    """Error on twin 1 (character state fails) → twin 2 still processed."""
    twin_1 = _twin(twin_id=str(uuid4()), user_id="user-1")
    twin_2 = _twin(twin_id=str(uuid4()), user_id="user-2")

    db = MagicMock()
    call_count = {"state": 0, "apply": 0}

    def _rpc(name: str, params: dict):
        chain = MagicMock()
        if name == "brandedby_get_stale_twins":
            chain.execute = AsyncMock(
                return_value=MagicMock(data=[twin_1, twin_2])
            )
        elif name == "get_character_state":
            call_count["state"] += 1
            if call_count["state"] == 1:
                # First twin fails
                chain.execute = AsyncMock(
                    side_effect=RuntimeError("DB timeout for user-1")
                )
            else:
                # Second twin succeeds
                chain.execute = AsyncMock(
                    return_value=MagicMock(data=_character_state())
                )
        elif name == "brandedby_apply_twin_personality":
            call_count["apply"] += 1
            chain.execute = AsyncMock(return_value=MagicMock(data=None))
        else:
            chain.execute = AsyncMock(return_value=MagicMock(data=None))
        return chain

    db.rpc.side_effect = _rpc

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
        return_value=_FAKE_PERSONALITY,
    ):
        stats = await run_brandedby_refresh(db)

    assert stats.errors == 1    # twin_1 failed
    assert stats.refreshed == 1  # twin_2 succeeded
    assert stats.skipped == 0
    assert call_count["apply"] == 1  # only called for twin_2


@pytest.mark.asyncio
async def test_fire_forward_generate_error_does_not_block_sibling():
    """Personality generation fails for twin 1 → twin 2 still refreshed."""
    twin_1 = _twin(twin_id=str(uuid4()), user_id="user-a")
    twin_2 = _twin(twin_id=str(uuid4()), user_id="user-b")

    db = _make_db(twins=[twin_1, twin_2])

    gen_call_count = {"n": 0}

    async def flaky_gen(display_name: str, state: dict) -> str:
        gen_call_count["n"] += 1
        if gen_call_count["n"] == 1:
            raise RuntimeError("LLM unavailable")
        return _FAKE_PERSONALITY

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        side_effect=flaky_gen,
    ):
        stats = await run_brandedby_refresh(db)

    assert stats.errors == 1
    assert stats.refreshed == 1


# ── Missing display_name defaults gracefully ──────────────────────────────────


@pytest.mark.asyncio
async def test_missing_display_name_defaults_to_professional():
    """Twin row with display_name=None → defaults to 'Professional', no crash."""
    twin = _twin()
    twin["display_name"] = None  # simulate missing display_name
    db = _make_db(twins=[twin])

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
        return_value=_FAKE_PERSONALITY,
    ) as mock_gen:
        stats = await run_brandedby_refresh(db)

    assert stats.refreshed == 1
    # Called with "Professional" fallback
    mock_gen.assert_called_once_with("Professional", _character_state())


# ── get_stale_twins respects batch size ───────────────────────────────────────


@pytest.mark.asyncio
async def test_get_stale_twins_called_with_batch_size():
    """brandedby_get_stale_twins called with p_limit=REFRESH_BATCH_SIZE."""
    db = _make_db(twins=[])

    with patch(
        "app.services.brandedby_refresh_worker.generate_twin_personality",
        new_callable=AsyncMock,
    ):
        await run_brandedby_refresh(db)

    # First rpc call must be brandedby_get_stale_twins with correct p_limit
    first_call = db.rpc.call_args_list[0]
    assert first_call.args[0] == "brandedby_get_stale_twins"
    assert first_call.args[1]["p_limit"] == REFRESH_BATCH_SIZE


# ── Injected db avoids _admin() ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_injected_db_does_not_call_admin():
    """Passing db= directly means _admin() (real credentials) is never called."""
    db = _make_db(twins=[])

    with patch(
        "app.services.brandedby_refresh_worker._admin",
        new_callable=AsyncMock,
    ) as mock_admin:
        with patch(
            "app.services.brandedby_refresh_worker.generate_twin_personality",
            new_callable=AsyncMock,
        ):
            await run_brandedby_refresh(db)

    mock_admin.assert_not_called()


# ── _main() CLI entrypoint ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_main_calls_run_brandedby_refresh():
    """_main() invokes run_brandedby_refresh and logs the result."""
    from app.services.brandedby_refresh_worker import _main

    with patch(
        "app.services.brandedby_refresh_worker.run_brandedby_refresh",
        new_callable=AsyncMock,
        return_value=RefreshStats(refreshed=3, skipped=1, errors=0),
    ) as mock_run:
        await _main()

    mock_run.assert_called_once()
