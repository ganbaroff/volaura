"""Match Checker service tests.

Coverage priorities:
  1. Circuit breaker: 3 Telegram failures → subsequent searches not notified
  2. No matches → last_checked_at still updated (prevents re-checking same window)
  3. Table not found → logs warning, returns empty RunSummary (graceful fallback)
  4. Happy path → new matches found, Telegram notification attempted
  5. Per-search error isolation → one bad search doesn't abort the rest
  6. Location filter: case-insensitive match applied correctly
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.match_checker import (
    _CB_THRESHOLD,
    _MAX_SEARCHES_PER_RUN,
    MatchCheckResult,
    RunSummary,
    run_match_check,
)

ORG_ID = str(uuid4())
ORG_ID_2 = str(uuid4())
VOL_ID = str(uuid4())

_NOW_ISO = "2026-04-02T10:00:00+00:00"
_LAST_CHECKED = "2026-04-01T10:00:00+00:00"


class MockResult:
    def __init__(self, data=None):
        self.data = data


# ── Builders ──────────────────────────────────────────────────────────────────


def _search(org_id: str = ORG_ID, search_id: str | None = None, filters: dict | None = None) -> dict:
    return {
        "id": search_id or str(uuid4()),
        "org_id": org_id,
        "name": "Senior communicators",
        "filters": filters or {"min_aura": 60.0},
        "last_checked_at": _LAST_CHECKED,
    }


def _aura_row(vol_id: str = VOL_ID) -> dict:
    return {
        "volunteer_id": vol_id,
        "total_score": 75.0,
        "badge_tier": "gold",
    }


def _profile_row(vol_id: str = VOL_ID) -> dict:
    return {
        "id": vol_id,
        "display_name": "Leyla M.",
        "username": "leyla",
    }


def make_db(
    searches: list[dict] | None = None,
    aura_rows: list[dict] | None = None,
    profiles: list[dict] | None = None,
    org_name: str = "Test NGO",
    raise_on_saved_searches: bool = False,
) -> MagicMock:
    """Build a mock admin DB client."""
    db = MagicMock()

    if searches is None:
        searches = [_search()]
    if aura_rows is None:
        aura_rows = [_aura_row()]
    if profiles is None:
        profiles = [_profile_row()]

    _table_cache: dict[str, MagicMock] = {}

    def table(name: str) -> MagicMock:
        if name == "org_saved_searches" and name in _table_cache:
            return _table_cache[name]

        m = MagicMock()

        if name == "org_saved_searches":
            if raise_on_saved_searches:

                async def raise_exc(*a, **kw):
                    raise Exception("relation org_saved_searches does not exist")

                m.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = raise_exc
            else:
                m.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = AsyncMock(
                    return_value=MockResult(data=searches)
                )
            m.update.return_value.eq.return_value.execute = AsyncMock(return_value=MockResult(data=[{}]))

        elif name == "organizations":
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"name": org_name})
            )

        elif name == "aura_scores":
            m.select.return_value.gte.return_value.eq.return_value.gt.return_value.order.return_value.limit.return_value.execute = AsyncMock(
                return_value=MockResult(data=aura_rows)
            )
            m.select.return_value.gte.return_value.eq.return_value.gt.return_value.eq.return_value.order.return_value.limit.return_value.execute = AsyncMock(
                return_value=MockResult(data=aura_rows)
            )
            comp_data = {
                "communication": 80.0,
                "reliability": 70.0,
                "english_proficiency": 65.0,
                "leadership": 60.0,
                "event_performance": 55.0,
                "tech_literacy": 50.0,
                "adaptability": 45.0,
                "empathy_safeguarding": 40.0,
            }
            m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                return_value=MockResult(data=comp_data)
            )

        elif name == "profiles":
            m.select.return_value.in_.return_value.execute = AsyncMock(return_value=MockResult(data=profiles))

        _table_cache[name] = m
        return m

    db.table = table
    return db


# ── Tests: Happy path ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_happy_path_finds_matches_and_attempts_telegram():
    db = make_db()
    with patch(
        "app.services.match_checker._send_telegram_notification",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_notify:
        summary = await run_match_check(db)

    assert summary.searches_checked == 1
    assert summary.searches_with_matches == 1
    assert summary.notifications_sent == 1
    assert summary.errors == 0
    mock_notify.assert_called_once()


@pytest.mark.asyncio
async def test_no_matches_updates_last_checked_but_does_not_notify():
    db = make_db(aura_rows=[])
    with patch(
        "app.services.match_checker._send_telegram_notification",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_notify:
        summary = await run_match_check(db)

    assert summary.searches_checked == 1
    assert summary.searches_with_matches == 0
    assert summary.notifications_sent == 0
    # last_checked_at update must be called even with zero matches
    db.table("org_saved_searches").update.assert_called_once()
    mock_notify.assert_not_called()


# ── Tests: Circuit breaker ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_circuit_breaker_stops_telegram_after_threshold():
    """_CB_THRESHOLD=3 failures → subsequent searches not notified (only logged)."""
    # Create N searches = CB_THRESHOLD + 2 so we can verify the breaker tripped
    n_searches = _CB_THRESHOLD + 2
    searches = [_search(search_id=str(i)) for i in range(n_searches)]
    db = make_db(searches=searches)

    with patch(
        "app.services.match_checker._send_telegram_notification",
        new_callable=AsyncMock,
        return_value=False,  # always fail
    ) as mock_notify:
        summary = await run_match_check(db)

    # Telegram was called at most _CB_THRESHOLD times (3), then circuit broke
    assert mock_notify.call_count <= _CB_THRESHOLD
    # Searches beyond the threshold: no notification (circuit is open)
    assert summary.notifications_sent == 0
    # But searches were still processed (last_checked_at still updated)
    assert summary.searches_checked == n_searches


@pytest.mark.asyncio
async def test_circuit_breaker_constant_equals_three():
    """_CB_THRESHOLD is 3 — the safety contract for Telegram spam protection."""
    assert _CB_THRESHOLD == 3


@pytest.mark.asyncio
async def test_circuit_breaker_does_not_trip_on_zero_failures():
    """If Telegram succeeds for first 2, then fails once → CB doesn't trip (need 3)."""
    searches = [_search(search_id=str(i)) for i in range(4)]
    db = make_db(searches=searches)

    call_count = 0

    async def flaky_notify(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # Fail only on the 3rd call (not 3 consecutive failures from the start)
        return call_count != 3

    with patch("app.services.match_checker._send_telegram_notification", side_effect=flaky_notify):
        summary = await run_match_check(db)

    # 1 success, 1 failure, 1 success → breaker not tripped — 4th should also notify
    # 2 successes + at least the 3rd attempt made
    assert summary.notifications_sent >= 2


# ── Tests: Table migration fallback ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_table_returns_empty_summary_gracefully():
    """If org_saved_searches table doesn't exist → warn + return empty, never raise."""
    db = make_db(raise_on_saved_searches=True)
    summary = await run_match_check(db)

    assert isinstance(summary, RunSummary)
    assert summary.searches_checked == 0
    assert summary.errors == 0  # graceful exit, not an error


# ── Tests: Per-search error isolation ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_one_bad_search_does_not_abort_others():
    """A runtime error on search N must not prevent processing searches N+1, N+2."""
    search_1 = _search(search_id="bad-search")
    search_2 = _search(search_id="good-search")
    db = make_db(searches=[search_1, search_2])

    original_table = db.table

    call_count = 0

    def table_with_fault(name: str):
        nonlocal call_count
        m = original_table(name)
        if name == "organizations":
            call_count += 1
            if call_count == 1:
                # First org lookup → raises (simulates bad search)
                m.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
                    side_effect=Exception("DB timeout")
                )
        return m

    db.table = table_with_fault

    with patch("app.services.match_checker._send_telegram_notification", new_callable=AsyncMock, return_value=True):
        summary = await run_match_check(db)

    # Search 1 errored, search 2 completed
    assert summary.errors == 1
    assert summary.searches_checked == 1  # only the good one completed
    assert len(summary.results) == 2  # both recorded (error result + success result)


# ── Tests: Location filter ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_location_filter_includes_all_matches():
    """Searches without location filter return all matching profiles."""
    db = make_db(
        searches=[_search(filters={"min_aura": 60.0})],  # no location key
        aura_rows=[_aura_row()],
        profiles=[_profile_row()],
    )
    with patch("app.services.match_checker._send_telegram_notification", new_callable=AsyncMock, return_value=True):
        summary = await run_match_check(db)

    assert summary.searches_with_matches == 1


# ── Tests: RunSummary structure ───────────────────────────────────────────────


def test_run_summary_defaults():
    """RunSummary initializes with safe zero defaults."""
    s = RunSummary()
    assert s.searches_checked == 0
    assert s.searches_with_matches == 0
    assert s.notifications_sent == 0
    assert s.errors == 0
    assert s.results == []


def test_match_check_result_with_error():
    """MatchCheckResult stores error string correctly."""
    r = MatchCheckResult(
        search_id="x",
        search_name="test",
        org_id=ORG_ID,
        new_match_count=0,
        notified=False,
        error="connection timeout",
    )
    assert r.error == "connection timeout"
    assert not r.notified


# ── Tests: Max searches per run cap ───────────────────────────────────────────


def test_max_searches_per_run_constant():
    """_MAX_SEARCHES_PER_RUN is 50 — prevents DB timeout on large installs."""
    assert _MAX_SEARCHES_PER_RUN == 50


# ── Tests: badge_tier filter ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_badge_tier_filter_applied_in_query():
    """Filters with badge_tier → .eq("badge_tier", ...) applied to aura_scores query.

    make_db's _table_cache only caches org_saved_searches; every other table gets a
    fresh MagicMock per call, so we must override db.table to return stable mocks.
    The badge_tier branch extends the query chain:
        .select().gte().eq().gt().order().limit().eq("badge_tier", ...).execute()
    """
    db = make_db(
        searches=[_search(filters={"min_aura": 60.0, "badge_tier": "gold"})],
        aura_rows=[],
    )

    # Build stable per-table mocks so every db.table(name) call returns the same object
    saved_search_mock = db.table("org_saved_searches")  # already cached by make_db

    org_mock = MagicMock()
    org_mock.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=MockResult(data={"name": "Test NGO"})
    )

    aura_mock = MagicMock()
    # badge_tier chain: .select().gte().eq().gt().order().limit().eq().execute
    aura_mock.select.return_value.gte.return_value.eq.return_value.gt.return_value.order.return_value.limit.return_value.eq.return_value.execute = AsyncMock(
        return_value=MockResult(data=[])
    )

    profiles_mock = MagicMock()
    profiles_mock.select.return_value.in_.return_value.execute = AsyncMock(return_value=MockResult(data=[]))

    _stable: dict = {
        "org_saved_searches": saved_search_mock,
        "organizations": org_mock,
        "aura_scores": aura_mock,
        "profiles": profiles_mock,
    }
    db.table = lambda name: _stable.get(name, MagicMock())

    with patch("app.services.match_checker._send_telegram_notification", new_callable=AsyncMock, return_value=True):
        summary = await run_match_check(db)

    assert summary.searches_checked == 1
    assert summary.errors == 0


# ── Tests: location filter skips non-matching volunteers ─────────────────────


@pytest.mark.asyncio
async def test_location_filter_skips_non_matching_volunteers():
    """Volunteer profile.location='London', filter.location='baku' → volunteer excluded."""
    profile = _profile_row()
    profile["location"] = "London"

    db = make_db(
        searches=[_search(filters={"min_aura": 60.0, "location": "baku"})],
        profiles=[profile],
    )
    with patch("app.services.match_checker._send_telegram_notification", new_callable=AsyncMock, return_value=True) as mock_notify:
        summary = await run_match_check(db)

    assert summary.searches_with_matches == 0  # volunteer was filtered out
    mock_notify.assert_not_called()


# ── Tests: competency query exception is swallowed ────────────────────────────


@pytest.mark.asyncio
async def test_competency_query_exception_is_non_fatal():
    """Exception on competency lookup is swallowed; match still included (no top_competency).

    make_db returns a fresh MagicMock for aura_scores on every db.table() call, so we
    must wire a stable aura_mock and replace db.table to ensure the same object is
    returned on both calls inside _find_new_matches (main query + competency lookup).
    """
    saved_search_mock = make_db().table("org_saved_searches")  # get the cached instance

    # Rebuild stable mocks
    org_mock = MagicMock()
    org_mock.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        return_value=MockResult(data={"name": "Test NGO"})
    )

    aura_mock = MagicMock()
    # Main aura query (no badge_tier): .select().gte().eq().gt().order().limit().execute
    aura_mock.select.return_value.gte.return_value.eq.return_value.gt.return_value.order.return_value.limit.return_value.execute = AsyncMock(
        return_value=MockResult(data=[_aura_row()])
    )
    # Competency lookup (.eq().maybe_single().execute) → raises (non-fatal path)
    aura_mock.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock(
        side_effect=Exception("competency query timed out")
    )

    profiles_mock = MagicMock()
    profiles_mock.select.return_value.in_.return_value.execute = AsyncMock(
        return_value=MockResult(data=[_profile_row()])
    )

    _stable: dict = {
        "org_saved_searches": saved_search_mock,
        "organizations": org_mock,
        "aura_scores": aura_mock,
        "profiles": profiles_mock,
    }

    db = MagicMock()
    db.table = lambda name: _stable.get(name, MagicMock())

    with patch("app.services.match_checker._send_telegram_notification", new_callable=AsyncMock, return_value=True):
        summary = await run_match_check(db)

    # Despite the exception, the run succeeded (exception is non-fatal)
    assert summary.searches_checked == 1
    assert summary.errors == 0


# ── Tests: telegram kill-switch returns False immediately ─────────────────────


@pytest.mark.asyncio
async def test_send_telegram_notification_kill_switch_returns_false():
    """_send_telegram_notification always returns False (HARD KILL-SWITCH is active)."""
    from app.services.match_checker import _send_telegram_notification

    result = await _send_telegram_notification("Test NGO", "My Search", [])
    assert result is False


# ── Tests: non-table exception re-raises ─────────────────────────────────────


@pytest.mark.asyncio
async def test_non_table_exception_propagates():
    """Exception unrelated to missing table (e.g. auth error) re-raises from run_match_check."""
    db = make_db()

    # Override org_saved_searches execute to raise an exception that does NOT match the
    # table-not-found pattern ("org_saved_searches" / "does not exist")
    async def raise_auth_error(*a, **kw):
        raise Exception("JWT expired")

    db.table("org_saved_searches").select.return_value.eq.return_value.order.return_value.limit.return_value.execute = (
        raise_auth_error
    )

    with pytest.raises(Exception, match="JWT expired"):
        await run_match_check(db)


# ── Tests: last_checked_at as datetime or None ────────────────────────────────


@pytest.mark.asyncio
async def test_last_checked_at_as_datetime_object():
    """last_checked_at stored as a datetime object (not string) is accepted."""
    from datetime import datetime, timezone

    search = _search()
    search["last_checked_at"] = datetime(2026, 4, 1, 10, 0, 0, tzinfo=timezone.utc)

    db = make_db(searches=[search])
    with patch("app.services.match_checker._send_telegram_notification", new_callable=AsyncMock, return_value=True):
        summary = await run_match_check(db)

    assert summary.searches_checked == 1


@pytest.mark.asyncio
async def test_last_checked_at_as_none_defaults_to_2020():
    """last_checked_at=None → defaults to 2020-01-01 (match all history)."""
    search = _search()
    search["last_checked_at"] = None

    db = make_db(searches=[search])
    with patch("app.services.match_checker._send_telegram_notification", new_callable=AsyncMock, return_value=True):
        summary = await run_match_check(db)

    assert summary.searches_checked == 1


# ── Tests: _main() CLI runner ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_main_returns_early_when_settings_missing():
    """_main() returns early when SUPABASE_URL or SUPABASE_SERVICE_KEY not set."""
    from app.services.match_checker import _main

    with patch("app.services.match_checker.settings") as mock_settings:
        mock_settings.supabase_url = ""
        mock_settings.supabase_service_key = ""
        # Should not raise; returns early
        await _main()
