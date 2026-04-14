"""Regression tests for tribe_matching None-response handling.

Bug history: Session 110 discovered 10+ days of daily CRON failures at 500
because `profile_result.data` crashed with AttributeError when
`.maybe_single().execute()` returned None (not a response object). The 500
was masked behind a 403 (missing CRON_SECRET) for weeks before surfacing.

These tests ensure the guard at tribe_matching.py:197 and :290 does not
regress if someone later "simplifies" the code.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.tribe_matching import _get_matching_candidates


@pytest.mark.asyncio
async def test_get_matching_candidates_handles_none_profile_result():
    """When .maybe_single().execute() returns None (no matching row),
    we must skip the candidate, not crash with AttributeError."""
    db = MagicMock()
    uid = str(uuid4())

    def table(name: str) -> MagicMock:
        m = MagicMock()
        if name == "tribe_members":
            # Nobody in active tribes — empty exclusion set.
            m.select.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        elif name == "aura_scores":
            # One candidate with a score.
            m.select.return_value.gt.return_value.gt.return_value.execute = AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "volunteer_id": uid,
                            "total_score": 72.5,
                            "last_updated": datetime.now(UTC).isoformat(),
                        }
                    ]
                )
            )
        elif name == "profiles":
            # visible_to_orgs filter returns None — the regression surface.
            m.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=None
            )
        elif name == "tribe_member_history":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        return m

    db.table = table

    result = await _get_matching_candidates(db, datetime.now(UTC))

    # Must not raise. Candidate is filtered out (no visible_to_orgs row), so empty list.
    assert result == []


@pytest.mark.asyncio
async def test_get_matching_candidates_handles_missing_data_attr():
    """When .maybe_single() returns a response object with data=None
    (alternate supabase-py shape), the candidate is still filtered out."""
    db = MagicMock()
    uid = str(uuid4())

    def table(name: str) -> MagicMock:
        m = MagicMock()
        if name == "tribe_members":
            m.select.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        elif name == "aura_scores":
            m.select.return_value.gt.return_value.gt.return_value.execute = AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "volunteer_id": uid,
                            "total_score": 50.0,
                            "last_updated": datetime.now(UTC).isoformat(),
                        }
                    ]
                )
            )
        elif name == "profiles":
            # Response object with data=None (older supabase-py shape).
            m.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MagicMock(data=None)
            )
        elif name == "tribe_member_history":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        return m

    db.table = table

    result = await _get_matching_candidates(db, datetime.now(UTC))
    assert result == []


@pytest.mark.asyncio
async def test_get_matching_candidates_passes_through_visible_candidate():
    """Smoke test: a visible_to_orgs candidate with a score must appear in the result."""
    db = MagicMock()
    uid = str(uuid4())

    def table(name: str) -> MagicMock:
        m = MagicMock()
        if name == "tribe_members":
            m.select.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        elif name == "aura_scores":
            m.select.return_value.gt.return_value.gt.return_value.execute = AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "volunteer_id": uid,
                            "total_score": 80.0,
                            "last_updated": datetime.now(UTC).isoformat(),
                        }
                    ]
                )
            )
        elif name == "profiles":
            # Happy path: profile exists AND visible_to_orgs=True.
            m.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MagicMock(data={"id": uid})
            )
        elif name == "tribe_member_history":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        return m

    db.table = table

    result = await _get_matching_candidates(db, datetime.now(UTC))
    assert len(result) == 1
    assert result[0]["user_id"] == uid
    assert result[0]["aura_score"] == 80.0
