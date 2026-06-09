"""D-1 MIN_ITEMS gate — premature /complete force-completion is rejected.

Before this gate, POST /api/assessment/complete/{session_id} after a single
answer produced a publicly verifiable score + badge + crystals (fake-badge /
crystal-farm vector). The rule lives in engine.can_finalize (single source of
truth) and is enforced by a 409 route guard in /complete.

Engine-stopped sessions (max_items / se_threshold / no_items_left /
eap_degraded) are always allowed to finalise — /answer never marks
status=completed, so /complete is the only finalisation path for them.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.assessment.engine import CATState, ItemRecord, can_finalize
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
    """Mock supporting Supabase's fluent .table().select().eq().single().execute() pattern."""
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


def _state_with_items(n: int, *, stopped: bool = False, stop_reason: str | None = None) -> CATState:
    state = CATState(stopped=stopped, stop_reason=stop_reason)
    for i in range(n):
        state.items.append(
            ItemRecord(
                question_id=f"q{i}",
                irt_a=1.0,
                irt_b=0.0,
                irt_c=0.0,
                response=1,
                raw_score=1.0,
                response_time_ms=5000,
            )
        )
    return state


# ── engine.can_finalize unit tests ────────────────────────────────────────────


def test_blocked_below_min_full_energy():
    allowed, min_required = can_finalize(_state_with_items(4), energy_level="full")
    assert allowed is False
    assert min_required == 5


def test_blocked_at_one_answer_full_energy():
    """The original D-1 exploit shape: 1 answer, user calls /complete."""
    allowed, min_required = can_finalize(_state_with_items(1), energy_level="full")
    assert allowed is False
    assert min_required == 5


def test_allowed_at_min_full_energy():
    allowed, min_required = can_finalize(_state_with_items(5), energy_level="full")
    assert allowed is True
    assert min_required == 5


def test_allowed_when_engine_stopped_below_min():
    """no_items_left / eap_degraded below the floor must not deadlock the user."""
    state = _state_with_items(2, stopped=True, stop_reason="no_items_left")
    allowed, _ = can_finalize(state, energy_level="full")
    assert allowed is True


def test_energy_profiles_lower_the_floor():
    assert can_finalize(_state_with_items(4), energy_level="mid") == (True, 4)
    assert can_finalize(_state_with_items(3), energy_level="mid") == (False, 4)
    assert can_finalize(_state_with_items(3), energy_level="low") == (True, 3)
    assert can_finalize(_state_with_items(2), energy_level="low") == (False, 3)


def test_unknown_energy_falls_back_to_full():
    allowed, min_required = can_finalize(_state_with_items(4), energy_level="bogus")
    assert allowed is False
    assert min_required == 5


# ── /complete route guard tests ───────────────────────────────────────────────


def _session_row(*, answers: dict, metadata: dict | None = None) -> dict:
    return {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "in_progress",
        "theta_estimate": 0.5,
        "theta_se": 0.9,
        "answers": answers,
        "metadata": metadata or {},
        "completed_at": None,
    }


def _one_item_answers(*, stopped: bool) -> dict:
    return {
        "theta": 0.5,
        "theta_se": 0.9,
        "stopped": stopped,
        "stop_reason": "no_items_left" if stopped else None,
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
    }


@pytest.mark.asyncio
async def test_complete_rejects_premature_force_complete():
    """1 answered item, engine NOT stopped → 409 MIN_ITEMS_NOT_REACHED, no session write."""
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()
    mock_user.execute = AsyncMock(
        return_value=MagicMock(data=_session_row(answers=_one_item_answers(stopped=False)))
    )

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        with patch("app.routers.assessment.get_completion_job", new=AsyncMock(return_value=None)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/assessment/complete/{SESSION_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )

        assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
        detail = resp.json()["detail"]
        assert detail["code"] == "MIN_ITEMS_NOT_REACHED"
        assert detail["questions_answered"] == 1
        assert detail["min_required"] == 5
        # The session must not be force-completed: no UPDATE on assessment_sessions.
        assert not mock_admin.update.called, "Guard fired but session UPDATE still executed"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_respects_low_energy_floor():
    """Low energy profile (min 3): 1 answer still rejected, floor reported as 3."""
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()
    mock_user.execute = AsyncMock(
        return_value=MagicMock(
            data=_session_row(
                answers=_one_item_answers(stopped=False),
                metadata={"energy_level": "low"},
            )
        )
    )

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        with patch("app.routers.assessment.get_completion_job", new=AsyncMock(return_value=None)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/assessment/complete/{SESSION_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )

        assert resp.status_code == 409
        assert resp.json()["detail"]["min_required"] == 3
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_allows_engine_stopped_session_below_min():
    """Engine-stopped (no_items_left) with 1 item must still finalise (no deadlock)."""
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()
    mock_user.execute = AsyncMock(
        return_value=MagicMock(data=_session_row(answers=_one_item_answers(stopped=True)))
    )

    call_count = {"n": 0}

    async def admin_execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return MagicMock(data=[{"id": SESSION_ID}])  # force-complete UPDATE
        if call_count["n"] == 2:
            return MagicMock(data={"slug": "communication"})  # competency slug
        return MagicMock(data=True)

    mock_admin.execute = AsyncMock(side_effect=admin_execute_side_effect)

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    job_template = {
        "id": "job-1",
        "session_id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_slug": "communication",
        "status": "pending",
        "attempts": 0,
        "side_effects": {},
        "result_context": {},
        "last_error": None,
        "completed_at": None,
    }

    async def _save(_db, job, **kwargs):
        next_job = dict(job)
        next_job.update(kwargs)
        return next_job

    try:
        with (
            patch("app.routers.assessment.get_completion_job", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.ensure_completion_job", new=AsyncMock(return_value=job_template)),
            patch("app.routers.assessment.save_completion_job", new=AsyncMock(side_effect=_save)),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/assessment/complete/{SESSION_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )

        assert resp.status_code == 200, f"Engine-stopped session was blocked: {resp.status_code}: {resp.text}"
        assert resp.json()["session_id"] == SESSION_ID
        # The legitimate force-complete UPDATE must have run with status=completed
        # (later pipeline updates touch other columns — scan all calls).
        update_payloads = [c.args[0] for c in mock_admin.update.call_args_list if c.args]
        assert any(
            isinstance(p, dict) and p.get("status") == "completed" for p in update_payloads
        ), f"No status=completed UPDATE found in {update_payloads}"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_rejects_abandoned_session():
    """Review finding: user-settable status='abandoned' (RLS abandon policy) must
    never reach the scoring pipeline — 409 SESSION_NOT_COMPLETABLE, no side effects."""
    mock_admin = _build_chainable_mock()
    mock_user = _build_chainable_mock()
    abandoned = _session_row(answers=_one_item_answers(stopped=True))
    abandoned["status"] = "abandoned"
    mock_user.execute = AsyncMock(return_value=MagicMock(data=abandoned))

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _make_user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        with patch("app.routers.assessment.get_completion_job", new=AsyncMock(return_value=None)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/assessment/complete/{SESSION_ID}",
                    headers={"Authorization": "Bearer fake-token"},
                )

        assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
        assert resp.json()["detail"]["code"] == "SESSION_NOT_COMPLETABLE"
        assert not mock_admin.update.called
        assert not mock_admin.rpc.called
    finally:
        app.dependency_overrides.clear()
