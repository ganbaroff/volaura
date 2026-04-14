"""Unit tests for app/services/ecosystem_events.py — cross-product event emitter.

These cover the three emitters (assessment_completed, aura_updated, badge_tier_changed)
and the invariants that matter for downstream consumers (MindShift / Life Sim / Atlas):
 • payload shape is stable — _schema_version: 1, source_product: "volaura"
 • badge_tier_changed skips when old == new (prevents spam)
 • any DB error is caught and logged — the assessment /complete flow never fails
   because of ecosystem noise (fire-and-forget contract)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ecosystem_events import (
    emit_assessment_completed,
    emit_aura_updated,
    emit_badge_tier_changed,
)


def _make_db_mock():
    """Build a supabase-async-like chain: db.table(...).insert(...).execute()."""
    execute = AsyncMock(return_value=MagicMock(data=[{"id": "x"}]))
    insert = MagicMock(return_value=MagicMock(execute=execute))
    table = MagicMock(return_value=MagicMock(insert=insert))
    db = MagicMock()
    db.table = table
    return db, insert


@pytest.mark.anyio
async def test_emit_assessment_completed_inserts_expected_row():
    db, insert = _make_db_mock()

    await emit_assessment_completed(
        db=db,
        user_id="user-1",
        competency_slug="communication",
        competency_score=72.345,
        items_answered=8,
        energy_level="mid",
        stop_reason="converged",
        gaming_flags=["slow"],
    )

    insert.assert_called_once()
    row = insert.call_args[0][0]
    assert row["user_id"] == "user-1"
    assert row["event_type"] == "assessment_completed"
    assert row["source_product"] == "volaura"
    assert row["payload"]["_schema_version"] == 1
    assert row["payload"]["competency_slug"] == "communication"
    assert row["payload"]["competency_score"] == 72.35  # rounded to 2
    assert row["payload"]["energy_level"] == "mid"
    assert row["payload"]["gaming_flags"] == ["slow"]


@pytest.mark.anyio
async def test_emit_aura_updated_rounds_competency_scores():
    db, insert = _make_db_mock()

    await emit_aura_updated(
        db=db,
        user_id="user-2",
        total_score=83.4567,
        badge_tier="gold",
        competency_scores={"communication": 72.345, "reliability": 88.111},
        elite_status=True,
        percentile_rank=95.66,
    )

    row = insert.call_args[0][0]
    assert row["event_type"] == "aura_updated"
    assert row["payload"]["total_score"] == 83.46
    assert row["payload"]["competency_scores"]["communication"] == 72.35
    assert row["payload"]["competency_scores"]["reliability"] == 88.11
    assert row["payload"]["badge_tier"] == "gold"
    assert row["payload"]["elite_status"] is True
    assert row["payload"]["percentile_rank"] == 95.7


@pytest.mark.anyio
async def test_emit_badge_tier_changed_skips_when_no_change():
    """Regression: silver -> silver must NOT emit an event."""
    db, insert = _make_db_mock()

    await emit_badge_tier_changed(
        db=db,
        user_id="user-3",
        old_tier="silver",
        new_tier="silver",
        total_score=66.5,
    )

    insert.assert_not_called()


@pytest.mark.anyio
async def test_emit_badge_tier_changed_emits_on_promotion():
    db, insert = _make_db_mock()

    await emit_badge_tier_changed(
        db=db,
        user_id="user-4",
        old_tier="bronze",
        new_tier="silver",
        total_score=62.0,
    )

    insert.assert_called_once()
    row = insert.call_args[0][0]
    assert row["event_type"] == "badge_tier_changed"
    assert row["payload"]["old_tier"] == "bronze"
    assert row["payload"]["new_tier"] == "silver"
    assert row["payload"]["total_score"] == 62.0


@pytest.mark.anyio
async def test_emitter_swallows_db_errors():
    """Fire-and-forget contract: ecosystem failures never bubble up."""
    db = MagicMock()
    db.table.return_value.insert.return_value.execute = AsyncMock(
        side_effect=RuntimeError("supabase exploded")
    )

    # None of these should raise
    await emit_assessment_completed(
        db=db,
        user_id="user-5",
        competency_slug="leadership",
        competency_score=40.0,
        items_answered=5,
        energy_level="full",
        stop_reason=None,
    )
    await emit_aura_updated(
        db=db,
        user_id="user-5",
        total_score=40.0,
        badge_tier="bronze",
        competency_scores={},
        elite_status=False,
        percentile_rank=None,
    )
    await emit_badge_tier_changed(
        db=db,
        user_id="user-5",
        old_tier=None,
        new_tier="bronze",
        total_score=40.0,
    )
