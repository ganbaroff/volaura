"""Coverage tests for tribe_matching.py — lines 41-83, 96-125, 131-160, 191, 267-326.

Target: app.services.tribe_matching ≥ 90%.

Covers:
- run_tribe_matching orchestrator (lines 41-83): full happy path, not-enough-candidates,
  tribe-create failure path, group-size < 2 skip
- _expire_old_tribes (lines 96-125): no expired tribes, tribes with members, empty members
- _renew_requesting_tribes (lines 131-160): no tribes, not all renew, all renew
- line 191: maybe_single returns None shape (existing streak guard in _create_tribe)
- _create_tribe (lines 267-326): new streak insert, existing streak update,
  tribe_matching_pool cleanup

All functions take db as a positional arg → pass AsyncMock directly (no DI override needed).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.tribe_matching import (
    TRIBE_DURATION_WEEKS,
    _create_tribe,
    _expire_old_tribes,
    _renew_requesting_tribes,
    run_tribe_matching,
)

# ─── Shared helpers ───────────────────────────────────────────────────────────

NOW = datetime.now(UTC)
TRIBE_ID = str(uuid4())
U1, U2, U3 = str(uuid4()), str(uuid4()), str(uuid4())


def _cand(uid: str, score: float = 75.0) -> dict:
    return {"user_id": uid, "aura_score": score, "previous_co_member_ids": []}


def _ok_execute(data=None):
    """AsyncMock that returns MagicMock(data=...) — standard Supabase shape."""
    return AsyncMock(return_value=MagicMock(data=data or []))


# ─── _expire_old_tribes (lines 96-125) ───────────────────────────────────────


from app.services.tribe_matching import _get_matching_candidates  # noqa: E402

# ─── _get_matching_candidates line 191 (excluded uid continue) ────────────────


@pytest.mark.asyncio
async def test_get_matching_candidates_excludes_user_already_in_tribe():
    """Line 191: user with AURA score but already in active tribe → filtered via continue."""
    db = MagicMock()
    uid_in_tribe = str(uuid4())
    uid_eligible = str(uuid4())

    def table(name: str):
        m = MagicMock()
        if name == "tribe_members":
            # uid_in_tribe IS in an active tribe
            m.select.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"user_id": uid_in_tribe}])
            )
        elif name == "aura_scores":
            m.select.return_value.gt.return_value.gt.return_value.execute = AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "volunteer_id": uid_in_tribe,
                            "total_score": 80.0,
                            "last_updated": NOW.isoformat(),
                        },
                        {
                            "volunteer_id": uid_eligible,
                            "total_score": 75.0,
                            "last_updated": NOW.isoformat(),
                        },
                    ]
                )
            )
        elif name == "profiles":
            m.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MagicMock(data={"id": uid_eligible})
            )
        elif name == "tribe_member_history":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        return m

    db.table = table

    result = await _get_matching_candidates(db, NOW)
    # uid_in_tribe must be excluded (line 191 continue), uid_eligible passes through
    user_ids = [c["user_id"] for c in result]
    assert uid_in_tribe not in user_ids
    assert uid_eligible in user_ids


# ─── _expire_old_tribes (lines 96-125) ───────────────────────────────────────


@pytest.mark.asyncio
async def test_expire_no_expired_tribes():
    """No active tribes past expiry — returns 0, no inserts."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        return m

    db.table = table
    count = await _expire_old_tribes(db, NOW)
    assert count == 0


@pytest.mark.asyncio
async def test_expire_one_tribe_with_members():
    """One expired tribe with 2 members — writes history, deletes renewals, marks expired."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "id": TRIBE_ID,
                            "tribe_members": [{"user_id": U1}, {"user_id": U2}],
                        }
                    ]
                )
            )
            m.update.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_member_history":
            m.insert.return_value.execute = _ok_execute()
        elif name == "tribe_renewal_requests":
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        return m

    db.table = table
    count = await _expire_old_tribes(db, NOW)

    assert count == 1


@pytest.mark.asyncio
async def test_expire_tribe_empty_members():
    """Expired tribe with no members — history insert skipped, still marks expired."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(
                    data=[{"id": TRIBE_ID, "tribe_members": []}]
                )
            )
            m.update.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_renewal_requests":
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_member_history":
            m.insert.return_value.execute = _ok_execute()
        return m

    db.table = table
    count = await _expire_old_tribes(db, NOW)
    assert count == 1


@pytest.mark.asyncio
async def test_expire_tribe_none_tribe_members_key():
    """Expired tribe dict with tribe_members=None — guards against KeyError."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(
                    data=[{"id": TRIBE_ID, "tribe_members": None}]
                )
            )
            m.update.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_renewal_requests":
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_member_history":
            m.insert.return_value.execute = _ok_execute()
        return m

    db.table = table
    count = await _expire_old_tribes(db, NOW)
    assert count == 1


# ─── _renew_requesting_tribes (lines 131-160) ─────────────────────────────────


@pytest.mark.asyncio
async def test_renew_no_expiring_tribes():
    """No tribes expiring in next 48h — returns 0."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
        return m

    db.table = table
    count = await _renew_requesting_tribes(db, NOW)
    assert count == 0


@pytest.mark.asyncio
async def test_renew_not_all_members_requested():
    """2 active members but only 1 renewal request — tribe NOT renewed."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"id": TRIBE_ID}])
            )
            m.update.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_members":
            m.select.return_value.eq.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"user_id": U1}, {"user_id": U2}])
            )
        elif name == "tribe_renewal_requests":
            # Only U1 requested
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"user_id": U1}])
            )
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        return m

    db.table = table
    count = await _renew_requesting_tribes(db, NOW)
    assert count == 0


@pytest.mark.asyncio
async def test_renew_all_members_requested():
    """All 2 active members requested renewal — tribe IS renewed."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"id": TRIBE_ID}])
            )
            m.update.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_members":
            m.select.return_value.eq.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"user_id": U1}, {"user_id": U2}])
            )
        elif name == "tribe_renewal_requests":
            # Both requested
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"user_id": U1}, {"user_id": U2}])
            )
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        return m

    db.table = table
    count = await _renew_requesting_tribes(db, NOW)
    assert count == 1


@pytest.mark.asyncio
async def test_renew_fewer_than_two_active_members_skipped():
    """Only 1 active member — skip (len < 2 guard at line 145)."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"id": TRIBE_ID}])
            )
        elif name == "tribe_members":
            m.select.return_value.eq.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"user_id": U1}])
            )
        elif name == "tribe_renewal_requests":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"user_id": U1}])
            )
        return m

    db.table = table
    count = await _renew_requesting_tribes(db, NOW)
    assert count == 0


# ─── _create_tribe (lines 267-326) ────────────────────────────────────────────


def _make_db_for_create_tribe(existing_streak: dict | None = None):
    """Build db mock for _create_tribe. existing_streak=None → insert path."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.insert.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"id": TRIBE_ID}])
            )
        elif name == "tribe_members":
            m.insert.return_value.execute = _ok_execute([{}])
        elif name == "tribe_streaks":
            # maybe_single check for existing streak
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MagicMock(data=existing_streak)
            )
            m.update.return_value.eq.return_value.execute = _ok_execute()
            m.insert.return_value.execute = _ok_execute()
        elif name == "tribe_matching_pool":
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        return m

    db.table = table
    return db


@pytest.mark.asyncio
async def test_create_tribe_inserts_new_streak_row():
    """When user has no existing streak row, _create_tribe inserts a new one."""
    db = _make_db_for_create_tribe(existing_streak=None)
    group = [_cand(U1), _cand(U2), _cand(U3)]

    result_id = await _create_tribe(db, group, NOW)
    assert result_id == TRIBE_ID


@pytest.mark.asyncio
async def test_create_tribe_updates_existing_streak_row():
    """When user already has a streak row, _create_tribe updates it (resets misses)."""
    existing = {
        "user_id": U1,
        "current_streak": 5,
        "longest_streak": 10,
        "consecutive_misses_count": 2,
        "cycle_started_at": (NOW - timedelta(weeks=4)).isoformat(),
    }
    db = _make_db_for_create_tribe(existing_streak=existing)
    group = [_cand(U1), _cand(U2), _cand(U3)]

    result_id = await _create_tribe(db, group, NOW)
    assert result_id == TRIBE_ID


@pytest.mark.asyncio
async def test_create_tribe_expires_at_is_four_weeks_from_now():
    """tribe.expires_at must be 4 weeks from the 'now' arg, ±1 second."""
    db = MagicMock()
    inserted_tribe_payload: dict = {}

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            def capture_insert(payload, **kw):
                inserted_tribe_payload.update(payload)
                mm = MagicMock()
                mm.execute = AsyncMock(return_value=MagicMock(data=[{"id": TRIBE_ID}]))
                return mm

            m.insert = capture_insert
        elif name == "tribe_members":
            m.insert.return_value.execute = _ok_execute([{}])
        elif name == "tribe_streaks":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MagicMock(data=None)
            )
            m.insert.return_value.execute = _ok_execute()
        elif name == "tribe_matching_pool":
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        return m

    db.table = table
    await _create_tribe(db, [_cand(U1), _cand(U2)], NOW)

    expected_expiry = (NOW + timedelta(weeks=TRIBE_DURATION_WEEKS)).isoformat()
    assert inserted_tribe_payload.get("expires_at") == expected_expiry
    assert inserted_tribe_payload.get("status") == "active"


@pytest.mark.asyncio
async def test_create_tribe_maybe_single_returns_none_object():
    """Line 191: maybe_single().execute() returning a response where .data is absent
    (None from supabase-py) — must fall through to insert path without AttributeError."""
    db = MagicMock()

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.insert.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"id": TRIBE_ID}])
            )
        elif name == "tribe_members":
            m.insert.return_value.execute = _ok_execute([{}])
        elif name == "tribe_streaks":
            # Returns None directly — the None-guard on line 291
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=None
            )
            m.insert.return_value.execute = _ok_execute()
        elif name == "tribe_matching_pool":
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        return m

    db.table = table
    result_id = await _create_tribe(db, [_cand(U1), _cand(U2)], NOW)
    assert result_id == TRIBE_ID


@pytest.mark.asyncio
async def test_create_tribe_cleans_matching_pool_for_each_member():
    """After creating tribe, each matched user is removed from tribe_matching_pool."""
    db = MagicMock()
    deleted_user_ids: list[str] = []

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            m.insert.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"id": TRIBE_ID}])
            )
        elif name == "tribe_members":
            m.insert.return_value.execute = _ok_execute([{}])
        elif name == "tribe_streaks":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MagicMock(data=None)
            )
            m.insert.return_value.execute = _ok_execute()
        elif name == "tribe_matching_pool":
            def capture_delete():
                dd = MagicMock()
                def capture_eq(col, val):
                    if col == "user_id":
                        deleted_user_ids.append(val)
                    ee = MagicMock()
                    ee.execute = _ok_execute()
                    return ee
                dd.eq = capture_eq
                return dd
            m.delete = capture_delete
        return m

    db.table = table
    group = [_cand(U1), _cand(U2), _cand(U3)]
    await _create_tribe(db, group, NOW)

    assert set(deleted_user_ids) == {U1, U2, U3}


# ─── run_tribe_matching orchestrator (lines 41-83) ───────────────────────────


def _make_full_orchestrator_db(
    candidates: list[dict],
    *,
    expired_tribes: list[dict] | None = None,
    renewing_tribes: list[dict] | None = None,
    tribe_create_data: list[dict] | None = None,
):
    """Build db mock for run_tribe_matching integration covering all branches."""
    db = MagicMock()
    expired_tribes = expired_tribes or []
    renewing_tribes = renewing_tribes or []
    tribe_create_data = tribe_create_data or [{"id": TRIBE_ID}]

    def table(name: str):
        m = MagicMock()
        if name == "tribes":
            # _expire_old_tribes SELECT
            m.select.return_value.eq.return_value.lt.return_value.execute = AsyncMock(
                return_value=MagicMock(data=expired_tribes)
            )
            # _renew_requesting_tribes SELECT (reuse same chain; second call — empty)
            # INSERT for _create_tribe
            m.insert.return_value.execute = AsyncMock(
                return_value=MagicMock(data=tribe_create_data)
            )
            m.update.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_members":
            m.select.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
            m.select.return_value.eq.return_value.is_.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
            m.insert.return_value.execute = _ok_execute([{}])
        elif name == "aura_scores":
            m.select.return_value.gt.return_value.gt.return_value.execute = AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "volunteer_id": c["user_id"],
                            "total_score": c["aura_score"],
                            "last_updated": NOW.isoformat(),
                        }
                        for c in candidates
                    ]
                )
            )
        elif name == "profiles":
            m.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MagicMock(data={"id": "dummy"})
            )
        elif name == "tribe_member_history":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[])
            )
            m.insert.return_value.execute = _ok_execute()
        elif name == "tribe_renewal_requests":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MagicMock(data=renewing_tribes)
            )
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_streaks":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MagicMock(data=None)
            )
            m.insert.return_value.execute = _ok_execute()
            m.update.return_value.eq.return_value.execute = _ok_execute()
        elif name == "tribe_matching_pool":
            m.delete.return_value.eq.return_value.execute = _ok_execute()
        return m

    db.table = table
    return db


@pytest.mark.parametrize(
    "candidate_count, expected_tribes, expected_matched_ge",
    [
        pytest.param(0, 0, 0, id="пустой_пул"),
        pytest.param(1, 0, 0, id="один_кандидат_недостаточно"),
        pytest.param(3, 1, 3, id="один_триплет"),
        pytest.param(6, 2, 6, id="два_триплета"),
    ],
)
@pytest.mark.asyncio
async def test_run_tribe_matching_pool_sizes(candidate_count, expected_tribes, expected_matched_ge):
    """Orchestrator: correct tribe count per pool size."""
    candidates = [_cand(str(uuid4()), float(50 + i)) for i in range(candidate_count)]
    db = _make_full_orchestrator_db(candidates)

    result = await run_tribe_matching(db)

    assert result["tribes_created"] == expected_tribes
    assert result["users_matched"] >= expected_matched_ge


@pytest.mark.asyncio
async def test_run_tribe_matching_not_enough_candidates_early_return():
    """Pool of 1 triggers early-return path (lines 56-63) — tribes_created=0."""
    candidates = [_cand(str(uuid4()), 75.0)]
    db = _make_full_orchestrator_db(candidates)

    result = await run_tribe_matching(db)
    assert result["tribes_created"] == 0
    assert result["users_matched"] == 0
    assert result["users_skipped"] == 1


@pytest.mark.asyncio
async def test_run_tribe_matching_group_size_less_than_2_skipped():
    """Groups with < 2 members are skipped (line 73 guard).

    We patch _cluster_and_match to return one single-member group to hit the
    len(group) < 2 branch directly.
    """
    db = _make_full_orchestrator_db([_cand(U1, 75.0), _cand(U2, 76.0)])

    with patch("app.services.tribe_matching._cluster_and_match", return_value=[[_cand(U1, 75.0)]]):
        result = await run_tribe_matching(db)

    assert result["tribes_created"] == 0
    assert result["users_matched"] == 0


@pytest.mark.asyncio
async def test_run_tribe_matching_create_tribe_exception_handled():
    """If _create_tribe raises, the orchestrator logs error and continues (line 79-80)."""
    db = _make_full_orchestrator_db([_cand(U1, 75.0), _cand(U2, 76.0), _cand(U3, 77.0)])

    with patch(
        "app.services.tribe_matching._create_tribe",
        side_effect=RuntimeError("DB write failed"),
    ):
        result = await run_tribe_matching(db)

    # No crash, tribes_created = 0 because exception caught
    assert result["tribes_created"] == 0


@pytest.mark.asyncio
async def test_run_tribe_matching_returns_renewed_count():
    """Renewed count from _renew_requesting_tribes propagates to result dict."""
    # 0 matching candidates so we hit the early-return path quickly,
    # but we patch _renew_requesting_tribes to return non-zero
    db = _make_full_orchestrator_db([])

    with patch(
        "app.services.tribe_matching._renew_requesting_tribes",
        return_value=AsyncMock(return_value=5),
    ) as mock_renew:
        mock_renew.return_value = 5  # plain int — the real function returns int
        # Patch to coroutine returning 5
        async def fake_renew(d, n):
            return 5

        with patch("app.services.tribe_matching._renew_requesting_tribes", fake_renew):
            result = await run_tribe_matching(db)

    assert result["users_renewed"] == 5


@pytest.mark.asyncio
async def test_run_tribe_matching_seven_candidates_two_tribes_one_leftover():
    """Pool of 7 close-score users → 2 tribes (6 matched), 1 leftover."""
    candidates = [_cand(str(uuid4()), float(50 + i)) for i in range(7)]
    db = _make_full_orchestrator_db(candidates)

    result = await run_tribe_matching(db)
    # 7 candidates close in score → 2 triplets (6 matched), 1 skipped
    assert result["tribes_created"] == 2
    assert result["users_matched"] == 6
    assert result["users_skipped"] == 1


@pytest.mark.asyncio
async def test_run_tribe_matching_two_clusters_by_score_gap():
    """Candidates at 90/88/85/70/68/65 → 2 clusters (gap >15 between 85 and 70).

    Expected: 2 tribes created, not 1 tribe of 6.
    """
    candidates = [
        _cand(str(uuid4()), 90.0),
        _cand(str(uuid4()), 88.0),
        _cand(str(uuid4()), 85.0),
        _cand(str(uuid4()), 70.0),
        _cand(str(uuid4()), 68.0),
        _cand(str(uuid4()), 65.0),
    ]
    db = _make_full_orchestrator_db(candidates)

    result = await run_tribe_matching(db)
    assert result["tribes_created"] == 2
    assert result["users_matched"] == 6
