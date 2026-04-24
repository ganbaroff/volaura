"""Tests for /api/assessment router — specifically the complete endpoint.

Validates that upsert_aura_score RPC is called with correct JSONB params
(p_competency_scores), not the old broken individual params.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

USER_ID = "00000000-1111-2222-3333-444444444444"
SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
COMPETENCY_ID = "comp-uuid-1234"


def _make_admin_override(mock_db):
    async def _override():
        yield mock_db

    return _override


def _make_user_override(mock_db):
    async def _override():
        yield mock_db

    return _override


def _make_user_id_override(user_id: str):
    async def _override():
        return user_id

    return _override


def _build_chainable_mock():
    """Build a mock that supports Supabase's fluent .table().select().eq().single().execute() pattern."""
    mock = MagicMock()
    mock.table = MagicMock(return_value=mock)
    mock.select = MagicMock(return_value=mock)
    mock.insert = MagicMock(return_value=mock)
    mock.update = MagicMock(return_value=mock)
    mock.eq = MagicMock(return_value=mock)
    mock.single = MagicMock(return_value=mock)
    mock.execute = AsyncMock(return_value=MagicMock(data=None))
    mock.rpc = MagicMock(return_value=mock)
    return mock


def _job_with_side_effects(*, status: str, overrides: dict | None = None, result_context: dict | None = None):
    base_effects = {
        "aura_sync": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "rewards": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "streak": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "analytics": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "email": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "ecosystem_events": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "aura_events": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "decision_log": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
    }
    if overrides:
        base_effects.update(overrides)
    return {
        "id": "job-1",
        "session_id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_slug": "communication",
        "status": status,
        "attempts": 1,
        "side_effects": base_effects,
        "result_context": result_context
        or {
            "competency_slug": "communication",
            "competency_score": 72.5,
            "questions_answered": 1,
            "stop_reason": "manual_complete",
            "gaming_flags": [],
            "completed_at": "2026-04-23T10:00:00Z",
            "aura_updated": True,
            "crystals_earned": 0,
            "energy_level": "full",
            "old_badge_tier": "bronze",
            "aura_snapshot": {
                "total_score": 72.5,
                "badge_tier": "silver",
                "competency_scores": {"communication": 72.5},
                "elite_status": False,
                "percentile_rank": 55.0,
            },
        },
        "last_error": None,
        "completed_at": None,
    }


def _save_job_side_effect_factory():
    async def _save(_db, job, **kwargs):
        next_job = dict(job)
        next_job.update(kwargs)
        return next_job

    return _save


@pytest.mark.asyncio
async def test_complete_assessment_calls_rpc_with_jsonb_scores():
    """The P0 bug: upsert_aura_score was called with wrong params.

    Expected: p_competency_scores = {"communication": 72.5} (JSONB)
    Bug was:  p_competency_slug = "communication", p_competency_score = 72.5 (two params)
    """
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()

    # Session lookup returns an in_progress session (not yet completed).
    # Using status="in_progress" so the endpoint runs the full path:
    # gaming update → competency slug lookup → upsert_aura_score RPC.
    # A "completed" session would trigger the early-return path (no RPC call).
    completed_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "in_progress",
        "theta_estimate": 0.5,
        "theta_se": 0.3,
        "answers": {
            "theta": 0.5,
            "theta_se": 0.3,
            "stopped": True,
            "stop_reason": "se_threshold",
            "items": [
                {
                    "question_id": "q1",
                    "irt_a": 1.0,
                    "irt_b": 0.0,
                    "irt_c": 0.0,
                    "response": 1,
                    "raw_score": 0.8,
                    "response_time_ms": 5000,
                }
            ],
        },
        "completed_at": None,
    }

    # Configure mock_user for session lookup (.table("assessment_sessions").select().eq().eq().single().execute())
    mock_user.execute = AsyncMock(return_value=MagicMock(data=completed_session))

    # Configure mock_admin for competency slug lookup
    # The complete endpoint calls db_admin.table("competencies").select("slug").eq("id", ...).single().execute()
    # and also db_admin.rpc("upsert_aura_score", ...).execute()
    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=True))

    call_count = {"n": 0}

    async def admin_execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        # First admin execute = gaming columns UPDATE (assessment_sessions.update)
        # Second admin execute = competency slug lookup (competencies.select)
        if call_count["n"] == 1:
            return MagicMock(data=[{"id": SESSION_ID}])  # update result
        elif call_count["n"] == 2:
            return MagicMock(data={"slug": "communication"})
        return MagicMock(data=True)

    mock_admin.execute = AsyncMock(side_effect=admin_execute_side_effect)

    # Track rpc calls
    mock_admin.rpc = MagicMock(return_value=rpc_mock)

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()

        # Verify the RPC was called
        assert mock_admin.rpc.called, "upsert_aura_score RPC was never called"

        # Verify correct parameter names (THE BUG FIX)
        rpc_call_args = mock_admin.rpc.call_args
        assert rpc_call_args[0][0] == "upsert_aura_score"

        rpc_params = rpc_call_args[0][1]
        assert "p_volunteer_id" in rpc_params, "Missing p_volunteer_id"
        assert "p_competency_scores" in rpc_params, "Missing p_competency_scores — got wrong param names"
        assert "p_competency_slug" not in rpc_params, "OLD BUG: p_competency_slug should not exist"
        assert "p_competency_score" not in rpc_params, "OLD BUG: p_competency_score should not exist"

        # Verify JSONB format: {"slug": score}
        scores = rpc_params["p_competency_scores"]
        assert isinstance(scores, dict), f"p_competency_scores should be dict, got {type(scores)}"
        assert "communication" in scores, f"Expected 'communication' key in scores, got {scores}"
        assert isinstance(scores["communication"], float), "Score should be a float"

        # Verify response
        assert body["aura_updated"] is True
        assert body["competency_slug"] == "communication"
        assert body["session_id"] == SESSION_ID

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_assessment_skips_rpc_when_no_slug():
    """If competency slug lookup returns empty, RPC should NOT be called."""
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()

    completed_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "completed",
        "theta_estimate": 0.0,
        "theta_se": 1.0,
        "answers": {"theta": 0.0, "theta_se": 1.0, "stopped": True, "stop_reason": "manual_complete", "items": []},
        "completed_at": "2026-03-23T10:00:00Z",
    }

    mock_user.execute = AsyncMock(return_value=MagicMock(data=completed_session))

    # Competency slug lookup returns empty slug
    mock_admin.execute = AsyncMock(return_value=MagicMock(data={"slug": ""}))

    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock()
    mock_admin.rpc = MagicMock(return_value=rpc_mock)

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["aura_updated"] is False
        assert not mock_admin.rpc.called, "RPC should NOT be called when slug is empty"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_assessment_logs_automated_decision_for_human_review():
    """Successful completion should write a contestable automated decision row."""
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()
    mock_admin.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=None))

    session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "in_progress",
        "theta_estimate": 0.5,
        "theta_se": 0.3,
        "answers": {
            "theta": 0.5,
            "theta_se": 0.3,
            "stopped": True,
            "stop_reason": "se_threshold",
            "items": [
                {
                    "question_id": "q1",
                    "irt_a": 1.0,
                    "irt_b": 0.0,
                    "irt_c": 0.0,
                    "response": 1,
                    "raw_score": 0.8,
                    "response_time_ms": 5000,
                }
            ],
        },
        "completed_at": None,
        "metadata": {"energy_level": "full"},
    }
    mock_user.execute = AsyncMock(return_value=MagicMock(data=session))

    log_insert_spy = MagicMock()
    log_chain = MagicMock()
    log_chain.execute = AsyncMock(return_value=MagicMock(data=[{"id": "log-1"}]))
    log_insert_spy.return_value = log_chain

    def table_side_effect(name: str):
        if name == "automated_decision_log":
            chain = MagicMock()
            chain.insert = log_insert_spy
            return chain
        return mock_admin

    mock_admin.table = MagicMock(side_effect=table_side_effect)

    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=True))
    mock_admin.rpc = MagicMock(return_value=rpc_mock)

    call_count = {"n": 0}

    async def admin_execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return MagicMock(data=[{"id": SESSION_ID}])  # session update
        if call_count["n"] == 2:
            return MagicMock(data={"slug": "communication"})  # competency slug
        if call_count["n"] == 3:
            return MagicMock(data=None)  # previous aura
        if call_count["n"] == 4:
            return MagicMock(data=[{"id": SESSION_ID}])  # pre-flag
        if call_count["n"] == 5:
            return MagicMock(data=[{"id": SESSION_ID}])  # clear flag
        if call_count["n"] == 6:
            return MagicMock(
                data={
                    "total_score": 72.5,
                    "badge_tier": "silver",
                    "competency_scores": {"communication": 72.5},
                    "elite_status": False,
                    "percentile_rank": 55.0,
                }
            )
        return MagicMock(data=None)

    mock_admin.execute = AsyncMock(side_effect=admin_execute_side_effect)

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        with (
            patch("app.routers.assessment.emit_assessment_rewards", new=AsyncMock(return_value=0)),
            patch("app.routers.assessment.record_assessment_activity", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.track_event", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.send_aura_ready_email", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.emit_assessment_completed", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.emit_aura_updated", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.emit_badge_tier_changed", new=AsyncMock(return_value=None)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/assessment/complete/{SESSION_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert log_insert_spy.called, "automated_decision_log insert was never called"

        row = log_insert_spy.call_args[0][0]
        assert row["source_product"] == "volaura"
        assert row["decision_type"] == "assessment_completed"
        assert row["human_reviewable"] is True
        assert row["algorithm_version"] == "assessment-pipeline-v1"
        assert row["decision_output"]["competency_slug"] == "communication"
        assert row["decision_output"]["aura_updated"] is True
        assert row["decision_output"]["aura_snapshot"]["badge_tier"] == "silver"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_assessment_creates_durable_job_on_first_completion():
    """First completion should create/process a durable job instead of inline-only best effort."""
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()
    mock_admin.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=None))

    session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "in_progress",
        "theta_estimate": 0.5,
        "theta_se": 0.3,
        "answers": {
            "theta": 0.5,
            "theta_se": 0.3,
            "stopped": True,
            "stop_reason": "se_threshold",
            "items": [{"question_id": "q1", "response": 1, "response_time_ms": 5000}],
        },
        "completed_at": None,
        "metadata": {"energy_level": "full"},
    }
    mock_user.execute = AsyncMock(return_value=MagicMock(data=session))

    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=True))
    mock_admin.rpc = MagicMock(return_value=rpc_mock)

    call_count = {"n": 0}

    async def admin_execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return MagicMock(data=[{"id": SESSION_ID}])  # session completion update
        if call_count["n"] == 2:
            return MagicMock(data={"slug": "communication"})  # competency slug
        if call_count["n"] == 3:
            return MagicMock(data=None)  # old aura lookup
        if call_count["n"] == 4:
            return MagicMock(data=[{"id": SESSION_ID}])  # pending_aura_sync pre-flag
        if call_count["n"] == 5:
            return MagicMock(data=[{"id": SESSION_ID}])  # pending_aura_sync clear
        return MagicMock(data=None)

    mock_admin.execute = AsyncMock(side_effect=admin_execute_side_effect)

    job = _job_with_side_effects(
        status="pending",
        overrides={
            "aura_sync": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
            "rewards": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
            "streak": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
            "analytics": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
            "email": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
            "ecosystem_events": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
            "aura_events": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
            "decision_log": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        },
    )

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        with (
            patch("app.routers.assessment.get_completion_job", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.ensure_completion_job", new=AsyncMock(return_value=job)) as ensure_job,
            patch("app.routers.assessment.save_completion_job", new=AsyncMock(side_effect=_save_job_side_effect_factory())) as save_job,
            patch("app.routers.assessment.emit_assessment_rewards", new=AsyncMock(return_value=15)),
            patch("app.routers.assessment.record_assessment_activity", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.track_event", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.send_aura_ready_email", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.emit_assessment_completed", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.emit_aura_updated", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.emit_badge_tier_changed", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment._log_assessment_automated_decision", new=AsyncMock(return_value=True)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/assessment/complete/{SESSION_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert ensure_job.await_count == 1
        processing_call = next(
            call for call in save_job.await_args_list if call.kwargs.get("status") == "processing"
        )
        assert processing_call.kwargs["increment_attempts"] is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_assessment_retries_incomplete_job_for_completed_session():
    """Completed sessions with an incomplete durable job should resume pending side effects."""
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()

    session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "completed",
        "theta_estimate": 0.5,
        "theta_se": 0.3,
        "answers": {
            "theta": 0.5,
            "theta_se": 0.3,
            "stopped": True,
            "stop_reason": "manual_complete",
            "items": [{"question_id": "q1", "response": 1, "response_time_ms": 5000}],
        },
        "completed_at": "2026-04-23T10:00:00Z",
        "gaming_penalty_multiplier": 1.0,
        "gaming_flags": [],
        "metadata": {"energy_level": "full"},
    }
    mock_user.execute = AsyncMock(return_value=MagicMock(data=session))
    mock_admin.execute = AsyncMock(return_value=MagicMock(data={"slug": "communication"}))

    existing_job = _job_with_side_effects(
        status="partial",
        overrides={
            "rewards": {"status": "pending", "attempts": 0, "last_error": "worker_crash", "updated_at": "2026-04-23T00:00:00Z"}
        },
    )

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        with (
            patch("app.routers.assessment.get_completion_job", new=AsyncMock(return_value=existing_job)),
            patch("app.routers.assessment.ensure_completion_job", new=AsyncMock(return_value=existing_job)),
            patch("app.routers.assessment.save_completion_job", new=AsyncMock(side_effect=_save_job_side_effect_factory())) as save_job,
            patch("app.routers.assessment.emit_assessment_rewards", new=AsyncMock(return_value=25)) as rewards,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/assessment/complete/{SESSION_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert rewards.await_count == 1
        assert body["crystals_earned"] == 25
        assert any(call.kwargs.get("status") == "completed" for call in save_job.await_args_list)
    finally:
        app.dependency_overrides.clear()
