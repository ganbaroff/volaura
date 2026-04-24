"""Proof tests for ecosystem_consumer.py — first real downstream event loop.

Coverage:
  1. Happy path: cursor NULL (first run) → events fetched → ai_twins marked stale
     → cursor advanced.  Proves: emit event → downstream state changes.
  2. Idempotency: running twice on the same events → second run finds no events
     (cursor is past them) → no duplicate twin updates.
  3. User without an AI twin: handler succeeds (returns True) even when RPC returns
     0 — doesn't block cursor.
  4. Handler DB error: stats.errors increments, stats.handled still counts other
     events, cursor advances.
  5. Missing cursor row: returns zero-stats without crashing.
  6. Empty event table: returns found=0, cursor stays put.
  7. process_brandedby_events with injected db avoids _admin() being called
     (unit test, no real credentials needed).

Implementation note:
  _handle_brandedby_event uses db.rpc("ecosystem_mark_twin_stale", ...) — NOT
  db.schema("brandedby").table("ai_twins").update() — because the brandedby schema
  is not exposed via PostgREST.  The RPC is a SECURITY DEFINER function in public
  that crosses the schema boundary at the postgres layer.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call, patch
from uuid import uuid4

import pytest

from app.services.ecosystem_consumer import (
    BRANDEDBY_EVENTS,
    _advance_cursor,
    _fetch_events,
    _handle_brandedby_event,
    _load_cursor,
    process_brandedby_events,
)


# ── Mock helpers ──────────────────────────────────────────────────────────────


def _fake_event(
    event_type: str = "aura_updated",
    user_id: str | None = None,
    created_at: str = "2026-04-24T10:00:00+00:00",
) -> dict:
    return {
        "id": str(uuid4()),
        "user_id": user_id or str(uuid4()),
        "event_type": event_type,
        "payload": {"_schema_version": 1},
        "created_at": created_at,
    }


def _make_db(
    cursor_row: dict | None = None,
    events: list[dict] | None = None,
    rpc_returns: int | None = None,
    rpc_raises: Exception | None = None,
):
    """Build a chainable Supabase mock for ecosystem_consumer tests.

    cursor_row   — row returned from ecosystem_event_cursors (None = no row)
    events       — list of character_events returned from fetch
    rpc_returns  — INT returned from ecosystem_mark_twin_stale RPC
                   (0 = no twin, 1+ = rows updated)
    rpc_raises   — exception to raise on RPC call
    """
    db = MagicMock()

    # --- ecosystem_event_cursors chain ---
    cursor_chain = MagicMock()
    cursor_chain.select.return_value = cursor_chain
    cursor_chain.update.return_value = cursor_chain
    cursor_chain.eq.return_value = cursor_chain
    cursor_chain.limit.return_value = cursor_chain
    # First execute call = SELECT (load), second = UPDATE (advance)
    select_data = [cursor_row] if cursor_row is not None else []
    cursor_chain.execute = AsyncMock(
        side_effect=[
            MagicMock(data=select_data),  # _load_cursor SELECT
            MagicMock(data=[]),           # _advance_cursor UPDATE
        ]
    )

    # --- character_events chain ---
    events_chain = MagicMock()
    events_chain.select.return_value = events_chain
    events_chain.in_.return_value = events_chain
    events_chain.gt.return_value = events_chain
    events_chain.order.return_value = events_chain
    events_chain.limit.return_value = events_chain
    events_chain.execute = AsyncMock(return_value=MagicMock(data=events or []))

    def _table(name: str):
        if name == "ecosystem_event_cursors":
            return cursor_chain
        if name == "character_events":
            return events_chain
        return MagicMock()

    db.table.side_effect = _table

    # --- ecosystem_mark_twin_stale RPC ---
    # Production code: db.rpc("ecosystem_mark_twin_stale", {...}).execute()
    # Returns INT (row count), not a list of rows.
    rpc_chain = MagicMock()
    count = rpc_returns if rpc_returns is not None else 1
    if rpc_raises:
        rpc_chain.execute = AsyncMock(side_effect=rpc_raises)
    else:
        rpc_chain.execute = AsyncMock(return_value=MagicMock(data=count))
    db.rpc.return_value = rpc_chain

    return db, cursor_chain, events_chain, rpc_chain


# ── Unit tests for internal helpers ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_cursor_returns_row():
    db, cursor_chain, _, _ = _make_db(cursor_row={"product": "brandedby", "last_processed_at": None})
    result = await _load_cursor(db, "brandedby")
    assert result is not None
    assert result["product"] == "brandedby"


@pytest.mark.asyncio
async def test_load_cursor_returns_none_when_missing():
    db, cursor_chain, _, _ = _make_db(cursor_row=None)
    # Override to return empty list
    cursor_chain.execute = AsyncMock(return_value=MagicMock(data=[]))
    result = await _load_cursor(db, "brandedby")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_events_passes_gt_filter_when_cursor_set():
    db, _, events_chain, _ = _make_db(events=[])
    await _fetch_events(db, BRANDEDBY_EVENTS, "2026-04-24T09:00:00+00:00", 100)
    events_chain.gt.assert_called_once_with("created_at", "2026-04-24T09:00:00+00:00")


@pytest.mark.asyncio
async def test_fetch_events_no_filter_when_cursor_null():
    db, _, events_chain, _ = _make_db(events=[])
    await _fetch_events(db, BRANDEDBY_EVENTS, None, 100)
    events_chain.gt.assert_not_called()


@pytest.mark.asyncio
async def test_handle_brandedby_event_marks_twin_stale():
    """RPC is called with correct args; returns True on success."""
    event = _fake_event("aura_updated", user_id="user-abc")
    db, _, _, rpc_chain = _make_db(rpc_returns=1)

    ok = await _handle_brandedby_event(db, event)

    assert ok is True
    db.rpc.assert_called_once_with(
        "ecosystem_mark_twin_stale",
        {"p_user_id": "user-abc", "p_reason": "aura_updated"},
    )


@pytest.mark.asyncio
async def test_handle_brandedby_event_returns_true_when_no_twin():
    """User not in BrandedBy — RPC returns 0 — still succeeds (not an error)."""
    event = _fake_event("badge_tier_changed")
    db, _, _, rpc_chain = _make_db(rpc_returns=0)

    ok = await _handle_brandedby_event(db, event)
    assert ok is True


@pytest.mark.asyncio
async def test_handle_brandedby_event_returns_false_on_db_error():
    event = _fake_event("aura_updated")
    db, _, _, rpc_chain = _make_db(rpc_raises=RuntimeError("connection reset"))

    ok = await _handle_brandedby_event(db, event)
    assert ok is False


# ── process_brandedby_events integration-level tests ─────────────────────────


@pytest.mark.asyncio
async def test_happy_path_marks_twin_and_advances_cursor():
    """Core proof: event emitted → downstream state changes → cursor advances."""
    user_id = str(uuid4())
    event = _fake_event("aura_updated", user_id=user_id, created_at="2026-04-24T10:00:00+00:00")

    db, cursor_chain, events_chain, rpc_chain = _make_db(
        cursor_row={
            "product": "brandedby",
            "last_processed_at": None,
            "events_processed_total": 0,
        },
        events=[event],
        rpc_returns=1,
    )

    stats = await process_brandedby_events(db)

    assert stats["found"] == 1
    assert stats["handled"] == 1
    assert stats["errors"] == 0
    assert stats["cursor_at"] == 1

    # Cursor was advanced with the event's created_at and id
    cursor_chain.update.assert_called_once_with(
        {
            "last_event_id": event["id"],
            "last_processed_at": event["created_at"],
            "events_processed_total": 1,
        }
    )

    # RPC called with correct user_id and reason
    db.rpc.assert_called_once_with(
        "ecosystem_mark_twin_stale",
        {"p_user_id": user_id, "p_reason": "aura_updated"},
    )


@pytest.mark.asyncio
async def test_idempotency_second_run_finds_no_events():
    """Second run: cursor is past the event → no new events → cursor stays put."""
    event = _fake_event("aura_updated", created_at="2026-04-24T10:00:00+00:00")

    db, cursor_chain, events_chain, _ = _make_db(
        cursor_row={
            "product": "brandedby",
            "last_processed_at": event["created_at"],  # already processed
            "events_processed_total": 1,
        },
        events=[],  # gt filter returns nothing
    )

    stats = await process_brandedby_events(db)

    assert stats["found"] == 0
    assert stats["cursor_at"] == 0
    # cursor UPDATE was NOT called — nothing to advance
    cursor_chain.update.assert_not_called()


@pytest.mark.asyncio
async def test_missing_cursor_row_returns_zero_stats():
    db, cursor_chain, _, _ = _make_db(cursor_row=None)
    cursor_chain.execute = AsyncMock(return_value=MagicMock(data=[]))

    stats = await process_brandedby_events(db)

    assert stats == {"found": 0, "handled": 0, "errors": 0, "cursor_at": 0}


@pytest.mark.asyncio
async def test_user_without_twin_still_advances_cursor():
    """No twin for user → handled still increments (RPC returned 0 = not an error), cursor advances."""
    event = _fake_event("badge_tier_changed", created_at="2026-04-24T11:00:00+00:00")

    db, cursor_chain, _, _ = _make_db(
        cursor_row={"product": "brandedby", "last_processed_at": None, "events_processed_total": 0},
        events=[event],
        rpc_returns=0,  # no rows matched — user not in BrandedBy
    )

    stats = await process_brandedby_events(db)

    assert stats["found"] == 1
    assert stats["handled"] == 1  # True was returned (no-twin is not an error)
    assert stats["errors"] == 0
    assert stats["cursor_at"] == 1


@pytest.mark.asyncio
async def test_handler_error_counted_cursor_still_advances():
    """Handler errors increment stats.errors but cursor still advances (no infinite loop)."""
    event = _fake_event("aura_updated", created_at="2026-04-24T12:00:00+00:00")

    db, cursor_chain, _, _ = _make_db(
        cursor_row={"product": "brandedby", "last_processed_at": None, "events_processed_total": 5},
        events=[event],
        rpc_raises=RuntimeError("brandedby schema unavailable"),
    )

    stats = await process_brandedby_events(db)

    assert stats["found"] == 1
    assert stats["handled"] == 0
    assert stats["errors"] == 1
    assert stats["cursor_at"] == 1  # cursor advanced despite error

    # events_processed_total = prior(5) + handled(0) = 5 (errors don't count)
    cursor_chain.update.assert_called_once_with(
        {
            "last_event_id": event["id"],
            "last_processed_at": event["created_at"],
            "events_processed_total": 5,
        }
    )


@pytest.mark.asyncio
async def test_multiple_events_last_one_sets_cursor():
    """With N events, cursor is advanced to the LAST event in the batch."""
    events = [
        _fake_event("aura_updated", created_at=f"2026-04-24T1{i}:00:00+00:00")
        for i in range(3)
    ]

    db, cursor_chain, _, _ = _make_db(
        cursor_row={"product": "brandedby", "last_processed_at": None, "events_processed_total": 0},
        events=events,
    )

    stats = await process_brandedby_events(db)

    assert stats["found"] == 3
    assert stats["handled"] == 3

    # last event's id and created_at used for cursor
    cursor_chain.update.assert_called_once_with(
        {
            "last_event_id": events[-1]["id"],
            "last_processed_at": events[-1]["created_at"],
            "events_processed_total": 3,
        }
    )
