"""Comprehensive unit tests for app.services.error_watcher.

Uses unittest.mock.AsyncMock to stub the Supabase admin client that is imported
inside run_error_watcher / _emit_anomaly via `from app.deps import get_admin_client`.

Patching target: `app.services.error_watcher.get_admin_client`

Signal contract:
  results["stuck_sessions"]  — count or -1 on error
  results["orphan_events"]   — count or -1 on error
  results["error_rate_1h"]   — count or -1 on error
  results["ecosystem_event_failures_1h"] — count or -1 on error
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.error_watcher import (
    ERROR_RATE_THRESHOLD_PER_HOUR,
    FAILURE_WATCH_WINDOW_HOURS,
    STUCK_SESSION_THRESHOLD_MINUTES,
    WATCHER_USER_ID,
    _emit_anomaly,
    run_error_watcher,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def make_count_result(count: int) -> MagicMock:
    """Supabase response mock that exposes .count attribute."""
    r = MagicMock()
    r.count = count
    return r


def make_data_result(data) -> MagicMock:
    r = MagicMock()
    r.data = data
    return r


def _chain_mock(final_result) -> AsyncMock:
    """Return an AsyncMock that chains .table().select()...execute() → final_result."""
    execute = AsyncMock(return_value=final_result)
    chain = MagicMock()
    chain.execute = execute
    chain.select = MagicMock(return_value=chain)
    chain.eq = MagicMock(return_value=chain)
    chain.lt = MagicMock(return_value=chain)
    chain.gt = MagicMock(return_value=chain)
    chain.is_ = MagicMock(return_value=chain)
    chain.update = MagicMock(return_value=chain)
    chain.insert = MagicMock(return_value=chain)
    return chain


def _build_full_db_mock(
    stuck_count: int = 0,
    orphan_data=0,
    fail_count: int = 0,
    dlq_count: int = 0,
) -> AsyncMock:
    """Build a Supabase-like db mock for the four-signal happy path.

    assessment_sessions is called in two distinct patterns:
      - select + count (stuck query, then error_rate query)
      - update (heal — only when stuck_count > 0)

    We distinguish them by inspecting which builder method is called first on
    the returned chain: select → query chain; update → heal chain.
    """

    # We use a dispatcher chain that routes based on first builder call.
    def _smart_session_chain(select_result, heal_result=None):
        """Chain that returns select_result on select(), heal_result on update()."""
        select_chain = _chain_mock(select_result)
        heal_chain_inner = _chain_mock(heal_result or MagicMock())

        dispatcher = MagicMock()
        dispatcher.select = MagicMock(return_value=select_chain)
        dispatcher.update = MagicMock(return_value=heal_chain_inner)
        # Propagate other builder methods to select_chain by default
        dispatcher.eq = MagicMock(return_value=select_chain)
        dispatcher.lt = MagicMock(return_value=select_chain)
        dispatcher.gt = MagicMock(return_value=select_chain)
        return dispatcher

    # Two separate dispatcher chains for the two select queries
    stuck_dispatcher = _smart_session_chain(make_count_result(stuck_count))
    fail_dispatcher = _smart_session_chain(make_count_result(fail_count))
    dlq_chain = _chain_mock(make_count_result(dlq_count))

    emit_chain = _chain_mock(MagicMock())

    db = AsyncMock()
    session_call_idx = [0]

    def table_side_effect(name: str):
        if name == "character_events":
            return emit_chain
        if name == "assessment_sessions":
            session_call_idx[0] += 1
            # 1st call → stuck query/heal dispatcher
            # 2nd call → error_rate query dispatcher
            # (when stuck_count=0, no heal update, so 2nd call IS the fail query)
            if session_call_idx[0] == 1:
                return stuck_dispatcher
            return fail_dispatcher
        if name == "ecosystem_event_failures":
            return dlq_chain
        return MagicMock()

    db.table = MagicMock(side_effect=table_side_effect)
    rpc_chain = _chain_mock(make_data_result(orphan_data))
    db.rpc = MagicMock(return_value=rpc_chain)

    return db


# ── _emit_anomaly ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_emit_anomaly_insert_payload_shape():
    """_emit_anomaly must insert with correct keys: user_id, event_type, payload, source_product."""
    insert_chain = _chain_mock(MagicMock())
    db = MagicMock()
    db.table = MagicMock(return_value=insert_chain)

    await _emit_anomaly(db, "stuck_sessions", 3, {"severity": "warn"})

    db.table.assert_called_once_with("character_events")
    insert_chain.insert.assert_called_once()
    inserted = insert_chain.insert.call_args[0][0]

    assert inserted["user_id"] == WATCHER_USER_ID
    assert inserted["event_type"] == "metric_anomaly_stuck_sessions"
    assert inserted["source_product"] == "volaura"
    assert "payload" in inserted
    assert inserted["payload"]["value"] == 3
    assert inserted["payload"]["severity"] == "warn"


@pytest.mark.asyncio
async def test_emit_anomaly_event_type_includes_anomaly_type():
    insert_chain = _chain_mock(MagicMock())
    db = MagicMock()
    db.table = MagicMock(return_value=insert_chain)

    await _emit_anomaly(db, "orphan_events", 1, {})
    inserted = insert_chain.insert.call_args[0][0]
    assert inserted["event_type"] == "metric_anomaly_orphan_events"


@pytest.mark.asyncio
async def test_emit_anomaly_payload_merges_extra_fields():
    insert_chain = _chain_mock(MagicMock())
    db = MagicMock()
    db.table = MagicMock(return_value=insert_chain)

    await _emit_anomaly(db, "error_rate_high", 10, {"window_hours": 1, "threshold": 5})
    inserted = insert_chain.insert.call_args[0][0]
    assert inserted["payload"]["value"] == 10
    assert inserted["payload"]["window_hours"] == 1
    assert inserted["payload"]["threshold"] == 5


@pytest.mark.asyncio
async def test_emit_anomaly_swallows_db_exception():
    """DB failure must NOT raise — best-effort only."""
    db = MagicMock()
    insert_chain = MagicMock()
    execute = AsyncMock(side_effect=RuntimeError("db down"))
    insert_chain.execute = execute
    insert_chain.insert = MagicMock(return_value=insert_chain)
    db.table = MagicMock(return_value=insert_chain)

    # Must not raise
    await _emit_anomaly(db, "stuck_sessions", 5, {"severity": "warn"})


@pytest.mark.asyncio
async def test_emit_anomaly_user_id_is_watcher_sentinel():
    insert_chain = _chain_mock(MagicMock())
    db = MagicMock()
    db.table = MagicMock(return_value=insert_chain)

    await _emit_anomaly(db, "test_type", 0, {})
    inserted = insert_chain.insert.call_args[0][0]
    assert inserted["user_id"] == "00000000-0000-0000-0000-000000000000"


# ── run_error_watcher — return shape ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_error_watcher_returns_dict():
    db = _build_full_db_mock()
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_run_error_watcher_has_expected_keys():
    db = _build_full_db_mock()
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()
    assert "stuck_sessions" in result
    assert "orphan_events" in result
    assert "error_rate_1h" in result
    assert "ecosystem_event_failures_1h" in result


# ── stuck_sessions signal ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stuck_sessions_zero_count_skips_emit():
    """count=0 must NOT call _emit_anomaly and NOT call heal update."""
    db = _build_full_db_mock(stuck_count=0)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        result = await run_error_watcher()

    assert result["stuck_sessions"] == 0
    # emit not called for stuck_sessions
    for c in mock_emit.call_args_list:
        assert c.args[1] != "stuck_sessions"


@pytest.mark.asyncio
async def test_stuck_sessions_nonzero_triggers_emit():
    db = _build_full_db_mock(stuck_count=3)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        result = await run_error_watcher()

    assert result["stuck_sessions"] == 3
    emit_types = [c.args[1] for c in mock_emit.call_args_list]
    assert "stuck_sessions" in emit_types


@pytest.mark.asyncio
async def test_stuck_sessions_nonzero_triggers_heal_update():
    """count>0 must issue an update(.status=abandoned) call."""
    db = _build_full_db_mock(stuck_count=2)
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        await run_error_watcher()

    # db.table("assessment_sessions") must have been called for the update
    table_calls = [c.args[0] for c in db.table.call_args_list]
    assert table_calls.count("assessment_sessions") >= 2  # select + update


@pytest.mark.asyncio
async def test_stuck_sessions_count_in_result():
    db = _build_full_db_mock(stuck_count=7)
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()
    assert result["stuck_sessions"] == 7


@pytest.mark.asyncio
async def test_stuck_sessions_exception_returns_minus_one():
    db = AsyncMock()
    db.table = MagicMock(side_effect=RuntimeError("timeout"))
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()
    assert result["stuck_sessions"] == -1


# ── orphan_events signal ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_orphan_events_rpc_called():
    db = _build_full_db_mock(orphan_data=0)
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        await run_error_watcher()
    db.rpc.assert_called_once()
    rpc_name = db.rpc.call_args.args[0]
    assert rpc_name == "count_orphan_character_events"


@pytest.mark.asyncio
async def test_orphan_events_rpc_passes_since_ts():
    db = _build_full_db_mock(orphan_data=0)
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        await run_error_watcher()
    kwargs = db.rpc.call_args.args[1] if len(db.rpc.call_args.args) > 1 else db.rpc.call_args.kwargs
    assert "since_ts" in kwargs


@pytest.mark.asyncio
async def test_orphan_events_int_data_in_result():
    db = _build_full_db_mock(orphan_data=4)
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()
    assert result["orphan_events"] == 4


@pytest.mark.asyncio
async def test_orphan_events_non_int_data_defaults_to_zero():
    """RPC returning a non-int (e.g. list) must result in 0, not crash."""
    db = _build_full_db_mock(orphan_data=[{"count": 5}])  # non-int
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()
    assert result["orphan_events"] == 0


@pytest.mark.asyncio
async def test_orphan_events_none_data_defaults_to_zero():
    db = _build_full_db_mock(orphan_data=None)
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()
    assert result["orphan_events"] == 0


@pytest.mark.asyncio
async def test_orphan_events_exception_returns_minus_one():
    """RPC not found or DB error → -1, does NOT propagate exception."""

    class _FakeChain:
        def execute(self):
            raise RuntimeError("rpc not found")

    db = AsyncMock()
    stuck_chain = _chain_mock(make_count_result(0))
    fail_chain = _chain_mock(make_count_result(0))
    _call_idx = [0]

    def _table(name):
        if name == "assessment_sessions":
            _call_idx[0] += 1
            return stuck_chain if _call_idx[0] == 1 else fail_chain
        return MagicMock()

    db.table = MagicMock(side_effect=_table)
    rpc_chain = MagicMock()
    rpc_chain.execute = AsyncMock(side_effect=RuntimeError("rpc missing"))
    db.rpc = MagicMock(return_value=rpc_chain)

    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()

    assert result["orphan_events"] == -1


@pytest.mark.asyncio
async def test_orphan_events_triggers_emit_when_nonzero():
    db = _build_full_db_mock(orphan_data=2)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        await run_error_watcher()

    emit_types = [c.args[1] for c in mock_emit.call_args_list]
    assert "orphan_events" in emit_types


# ── error_rate signal ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_error_rate_below_threshold_skips_emit():
    below = ERROR_RATE_THRESHOLD_PER_HOUR - 1
    db = _build_full_db_mock(fail_count=below)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        result = await run_error_watcher()

    assert result["error_rate_1h"] == below
    emit_types = [c.args[1] for c in mock_emit.call_args_list]
    assert "error_rate_high" not in emit_types


@pytest.mark.asyncio
async def test_error_rate_at_threshold_triggers_emit():
    db = _build_full_db_mock(fail_count=ERROR_RATE_THRESHOLD_PER_HOUR)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        result = await run_error_watcher()

    assert result["error_rate_1h"] == ERROR_RATE_THRESHOLD_PER_HOUR
    emit_types = [c.args[1] for c in mock_emit.call_args_list]
    assert "error_rate_high" in emit_types


@pytest.mark.asyncio
async def test_error_rate_warn_severity_at_threshold():
    """fail_count == threshold → severity must be 'warn', not 'crit'."""
    db = _build_full_db_mock(fail_count=ERROR_RATE_THRESHOLD_PER_HOUR)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        await run_error_watcher()

    rate_calls = [c for c in mock_emit.call_args_list if c.args[1] == "error_rate_high"]
    assert len(rate_calls) == 1
    payload = rate_calls[0].args[3]
    assert payload["severity"] == "warn"


@pytest.mark.asyncio
async def test_error_rate_crit_severity_at_double_threshold():
    """fail_count >= threshold*2 → severity must be 'crit'."""
    db = _build_full_db_mock(fail_count=ERROR_RATE_THRESHOLD_PER_HOUR * 2)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        await run_error_watcher()

    rate_calls = [c for c in mock_emit.call_args_list if c.args[1] == "error_rate_high"]
    assert len(rate_calls) == 1
    payload = rate_calls[0].args[3]
    assert payload["severity"] == "crit"


@pytest.mark.asyncio
async def test_error_rate_exception_returns_minus_one():
    db = AsyncMock()

    stuck_chain = _chain_mock(make_count_result(0))
    _call_idx = [0]

    def _table(name):
        if name == "assessment_sessions":
            _call_idx[0] += 1
            if _call_idx[0] == 1:
                return stuck_chain
            # Second call (error_rate query) raises
            bad = MagicMock()
            bad.select = MagicMock(return_value=bad)
            bad.eq = MagicMock(return_value=bad)
            bad.gt = MagicMock(return_value=bad)
            bad.execute = AsyncMock(side_effect=RuntimeError("fail"))
            return bad
        return MagicMock()

    db.table = MagicMock(side_effect=_table)
    rpc_chain = _chain_mock(make_data_result(0))
    db.rpc = MagicMock(return_value=rpc_chain)

    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()

    assert result["error_rate_1h"] == -1


# ── ecosystem_event_failures signal ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_ecosystem_event_failures_zero_skips_emit():
    db = _build_full_db_mock(dlq_count=0)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        result = await run_error_watcher()

    assert result["ecosystem_event_failures_1h"] == 0
    emit_types = [c.args[1] for c in mock_emit.call_args_list]
    assert "ecosystem_event_failures" not in emit_types


@pytest.mark.asyncio
async def test_ecosystem_event_failures_nonzero_triggers_emit():
    db = _build_full_db_mock(dlq_count=2)
    with (
        patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True),
        patch("app.services.error_watcher._emit_anomaly", AsyncMock()) as mock_emit,
    ):
        result = await run_error_watcher()

    assert result["ecosystem_event_failures_1h"] == 2
    dlq_calls = [c for c in mock_emit.call_args_list if c.args[1] == "ecosystem_event_failures"]
    assert len(dlq_calls) == 1
    payload = dlq_calls[0].args[3]
    assert payload["window_hours"] == FAILURE_WATCH_WINDOW_HOURS
    assert payload["status"] == "unresolved"
    assert payload["source_table"] == "ecosystem_event_failures"
    assert payload["severity"] == "warn"


@pytest.mark.asyncio
async def test_ecosystem_event_failures_filters_unresolved_last_hour():
    db = _build_full_db_mock(dlq_count=1)
    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        await run_error_watcher()

    dlq_chain = db.table("ecosystem_event_failures")
    dlq_chain.is_.assert_called_once_with("resolved_at", "null")
    dlq_chain.gt.assert_called_once()
    assert dlq_chain.gt.call_args.args[0] == "last_failed_at"


@pytest.mark.asyncio
async def test_ecosystem_event_failures_exception_returns_minus_one():
    db = AsyncMock()

    stuck_dispatcher = _chain_mock(make_count_result(0))
    fail_dispatcher = _chain_mock(make_count_result(0))
    dlq_chain = MagicMock()
    dlq_chain.select = MagicMock(return_value=dlq_chain)
    dlq_chain.is_ = MagicMock(return_value=dlq_chain)
    dlq_chain.gt = MagicMock(return_value=dlq_chain)
    dlq_chain.execute = AsyncMock(side_effect=RuntimeError("relation missing"))
    session_call_idx = [0]

    def _table(name):
        if name == "assessment_sessions":
            session_call_idx[0] += 1
            return stuck_dispatcher if session_call_idx[0] == 1 else fail_dispatcher
        if name == "ecosystem_event_failures":
            return dlq_chain
        return MagicMock()

    db.table = MagicMock(side_effect=_table)
    db.rpc = MagicMock(return_value=_chain_mock(make_data_result(0)))

    with patch("app.deps.get_admin_client", AsyncMock(return_value=db), create=True):
        result = await run_error_watcher()

    assert result["ecosystem_event_failures_1h"] == -1


# ── constants sanity ──────────────────────────────────────────────────────────


def test_watcher_user_id_is_zero_uuid():
    assert WATCHER_USER_ID == "00000000-0000-0000-0000-000000000000"


def test_stuck_session_threshold_positive():
    assert STUCK_SESSION_THRESHOLD_MINUTES > 0


def test_error_rate_threshold_positive():
    assert ERROR_RATE_THRESHOLD_PER_HOUR > 0


def test_failure_watch_window_positive():
    assert FAILURE_WATCH_WINDOW_HOURS > 0
