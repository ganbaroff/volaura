"""Tests for /api/assessment router — specifically the complete endpoint.

Validates that upsert_aura_score RPC is called with correct JSONB params
(p_competency_scores), not the old broken individual params.
"""

from unittest.mock import AsyncMock, MagicMock, call

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id


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


@pytest.mark.asyncio
async def test_complete_assessment_calls_rpc_with_jsonb_scores():
    """The P0 bug: upsert_aura_score was called with wrong params.

    Expected: p_competency_scores = {"communication": 72.5} (JSONB)
    Bug was:  p_competency_slug = "communication", p_competency_score = 72.5 (two params)
    """
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()

    # Session lookup returns a completed session with some answers
    completed_session = {
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
        "completed_at": "2026-03-23T10:00:00Z",
    }

    # Configure mock_user for session lookup (.table("assessment_sessions").select().eq().eq().single().execute())
    mock_user.execute = AsyncMock(return_value=MagicMock(data=completed_session))

    # Configure mock_admin for competency slug lookup
    # The complete endpoint calls db_admin.table("competencies").select("slug").eq("id", ...).single().execute()
    # and also db_admin.rpc("upsert_aura_score", ...).execute()
    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=True))

    call_count = {"n": 0}
    original_execute = mock_admin.execute

    async def admin_execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        # First admin execute = competency slug lookup
        if call_count["n"] == 1:
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
