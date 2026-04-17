"""AURA Reconciler tests — covers ghost-audit P0-2 root fix.

Coverage:
  1. Happy path: pending session → RPC succeeds → flag cleared, attempts reset
  2. RPC failure under retry cap: increments reconcile_attempts, leaves flag TRUE
  3. RPC failure at retry cap: clears flag, logs gave_up
  4. NULL competency_score: marks gave_up immediately (cannot resync without it)
  5. Missing slug for competency: marks gave_up
  6. Empty pending list: returns zero stats, no errors
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.aura_reconciler import (
    MAX_RECONCILE_ATTEMPTS,
    _reconcile_session,
    run_once,
)


def _mk_db_with_pending(pending_rows: list[dict], rpc_data=None, rpc_raises=None,
                       slug="communication", update_raises=False):
    """Build a chainable mock supabase client matching the reconciler's API usage.

    sessions_chain is shared so every update/select call lands on the same mock —
    `.update.call_args_list` then captures every update made by the reconciler.
    """
    db = MagicMock()

    # Shared chain for the assessment_sessions table — both select and update flow
    # through this single object so we can assert on .update.call_args_list later.
    sessions_chain = MagicMock()
    sessions_chain.select.return_value = sessions_chain
    sessions_chain.update.return_value = sessions_chain
    sessions_chain.eq.return_value = sessions_chain
    sessions_chain.order.return_value = sessions_chain
    sessions_chain.limit.return_value = sessions_chain
    if update_raises:
        sessions_chain.execute = AsyncMock(side_effect=RuntimeError("update fail"))
    else:
        sessions_chain.execute = AsyncMock(return_value=MagicMock(data=pending_rows))

    # competencies table — single() chain for slug lookup
    comp_chain = MagicMock()
    comp_chain.select.return_value = comp_chain
    comp_chain.eq.return_value = comp_chain
    comp_chain.single.return_value = comp_chain
    comp_chain.execute = AsyncMock(
        return_value=MagicMock(data={"slug": slug} if slug else None)
    )

    def table(name):
        if name == "competencies":
            return comp_chain
        if name == "assessment_sessions":
            return sessions_chain
        return MagicMock()

    db.table.side_effect = table

    if rpc_raises:
        db.rpc.return_value.execute = AsyncMock(side_effect=rpc_raises)
    else:
        db.rpc.return_value.execute = AsyncMock(return_value=MagicMock(data=rpc_data))

    return db, sessions_chain


@pytest.mark.asyncio
async def test_happy_path_clears_flag():
    row = {
        "id": str(uuid4()),
        "volunteer_id": str(uuid4()),
        "competency_id": str(uuid4()),
        "competency_score": 0.72,
        "reconcile_attempts": 1,
    }
    db, update_chain = _mk_db_with_pending([row], rpc_data=[{"ok": True}])

    outcome = await _reconcile_session(db, row)

    assert outcome == "ok"
    # Update was called with cleared flag and reset counter
    update_chain.update.assert_any_call({"pending_aura_sync": False, "reconcile_attempts": 0})


@pytest.mark.asyncio
async def test_rpc_failure_below_cap_increments_counter():
    row = {
        "id": str(uuid4()),
        "volunteer_id": str(uuid4()),
        "competency_id": str(uuid4()),
        "competency_score": 0.5,
        "reconcile_attempts": 0,
    }
    db, update_chain = _mk_db_with_pending(
        [row], rpc_raises=RuntimeError("Gemini timeout")
    )

    outcome = await _reconcile_session(db, row)

    assert outcome == "retry"
    # Counter incremented to 1, flag NOT cleared
    update_chain.update.assert_any_call({"reconcile_attempts": 1})


@pytest.mark.asyncio
async def test_rpc_failure_at_cap_marks_gave_up():
    row = {
        "id": str(uuid4()),
        "volunteer_id": str(uuid4()),
        "competency_id": str(uuid4()),
        "competency_score": 0.5,
        "reconcile_attempts": MAX_RECONCILE_ATTEMPTS - 1,  # next attempt hits cap
    }
    db, update_chain = _mk_db_with_pending(
        [row], rpc_raises=RuntimeError("permanent failure")
    )

    outcome = await _reconcile_session(db, row)

    assert outcome == "gave_up"
    # Flag must be cleared so reconciler stops picking it up
    update_chain.update.assert_any_call({"pending_aura_sync": False})


@pytest.mark.asyncio
async def test_null_competency_score_gives_up_immediately():
    row = {
        "id": str(uuid4()),
        "volunteer_id": str(uuid4()),
        "competency_id": str(uuid4()),
        "competency_score": None,
        "reconcile_attempts": 0,
    }
    db, update_chain = _mk_db_with_pending([row])

    outcome = await _reconcile_session(db, row)

    assert outcome == "gave_up"
    update_chain.update.assert_any_call({"pending_aura_sync": False})


@pytest.mark.asyncio
async def test_missing_slug_gives_up():
    row = {
        "id": str(uuid4()),
        "volunteer_id": str(uuid4()),
        "competency_id": str(uuid4()),
        "competency_score": 0.6,
        "reconcile_attempts": 0,
    }
    db, update_chain = _mk_db_with_pending([row], slug=None)

    outcome = await _reconcile_session(db, row)

    assert outcome == "gave_up"


@pytest.mark.asyncio
async def test_run_once_empty_returns_zero_stats():
    db, _ = _mk_db_with_pending([])
    with patch("app.services.aura_reconciler._admin", AsyncMock(return_value=db)):
        stats = await run_once()
    assert stats == {"found": 0, "ok": 0, "retry": 0, "gave_up": 0}


@pytest.mark.asyncio
async def test_run_once_mixed_batch():
    rows = [
        {"id": str(uuid4()), "volunteer_id": str(uuid4()), "competency_id": str(uuid4()),
         "competency_score": 0.9, "reconcile_attempts": 0},  # will succeed
        {"id": str(uuid4()), "volunteer_id": str(uuid4()), "competency_id": str(uuid4()),
         "competency_score": None, "reconcile_attempts": 0},  # gave_up
    ]
    db, _ = _mk_db_with_pending(rows, rpc_data=[{"ok": True}])
    with patch("app.services.aura_reconciler._admin", AsyncMock(return_value=db)):
        stats = await run_once()
    assert stats["found"] == 2
    assert stats["ok"] == 1
    assert stats["gave_up"] == 1
    assert stats["retry"] == 0
