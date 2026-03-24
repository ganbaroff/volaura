"""Smoke test: full assessment flow — start → answer → complete → results.

Tests the critical beta user path end-to-end using mocked Supabase + LLM.
Catches: column name regressions, RPC param bugs, wrong DB field reads.

Run: pytest apps/api/tests/test_smoke_assessment.py -v
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id


# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = "00000001-0000-0000-0000-000000000001"
SESSION_ID = "00000002-0000-0000-0000-000000000002"
COMP_ID = "11111111-1111-1111-1111-111111111111"
COMP_SLUG = "communication"
Q_MCQ_ID = "00000003-0000-0000-0000-000000000003"
Q_OPEN_ID = "00000004-0000-0000-0000-000000000004"

MCQ_QUESTION = {
    "id": Q_MCQ_ID,
    "competency_id": COMP_ID,
    "type": "mcq",
    "scenario_en": "A volunteer misses their shift. What do you do?",
    "scenario_az": "Könüllü növbəsini qaçırır. Nə edərsiniz?",
    "options": [
        {"key": "A", "text_en": "Ignore it", "text_az": "Nəzərə alma"},
        {"key": "B", "text_en": "Contact them", "text_az": "Əlaqə saxla"},
        {"key": "C", "text_en": "Report to manager", "text_az": "Rəhbərə bildir"},
        {"key": "D", "text_en": "Cover their shift", "text_az": "Növbəni örtün"},
    ],
    "correct_answer": "B",
    "expected_concepts": None,
    "irt_a": 1.2,
    "irt_b": 0.0,
    "irt_c": 0.2,
    "difficulty": "medium",
    "is_active": True,
}

OPEN_QUESTION = {
    "id": Q_OPEN_ID,
    "competency_id": COMP_ID,
    "type": "open_ended",
    "scenario_en": "Describe a situation where you led a team.",
    "scenario_az": "Komandaya rəhbərlik etdiyiniz bir vəziyyəti təsvir edin.",
    "options": None,
    "correct_answer": None,
    "expected_concepts": [
        {"name": "leadership", "weight": 0.5, "keywords": ["lead", "team", "decision"]},
        {"name": "communication", "weight": 0.5, "keywords": ["communicate", "listen", "clear"]},
    ],
    "irt_a": 1.0,
    "irt_b": 0.5,
    "irt_c": 0.0,
    "difficulty": "hard",
    "is_active": True,
}

# ── Mock helpers ───────────────────────────────────────────────────────────────

def _make_dep_override(value):
    async def _override():
        yield value
    return _override


def _make_user_id_override(user_id: str):
    async def _override():
        return user_id
    return _override


def _build_chainable(execute_side_effects: list):
    """Build a Supabase-like chainable mock with a sequence of execute() responses."""
    mock = MagicMock()
    mock.table = MagicMock(return_value=mock)
    mock.select = MagicMock(return_value=mock)
    mock.insert = MagicMock(return_value=mock)
    mock.update = MagicMock(return_value=mock)
    mock.eq = MagicMock(return_value=mock)
    mock.single = MagicMock(return_value=mock)
    mock.rpc = MagicMock(return_value=mock)

    responses = iter(execute_side_effects)

    async def _execute(*args, **kwargs):
        try:
            val = next(responses)
            return MagicMock(data=val)
        except StopIteration:
            return MagicMock(data=None)

    mock.execute = AsyncMock(side_effect=_execute)
    return mock


# ── Test 1: Full happy path — MCQ only session ─────────────────────────────────

@pytest.mark.asyncio
async def test_start_assessment_returns_first_question():
    """POST /api/assessment/start → 201 with a question."""
    admin = _build_chainable([
        {"id": COMP_ID},          # competency id lookup
        [MCQ_QUESTION],            # questions list
    ])
    user = _build_chainable([
        [],                        # no existing in-progress session
        {"id": SESSION_ID},        # insert session
    ])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json={"competency_slug": COMP_SLUG},
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "session_id" in body
        assert body["is_complete"] is False
        nq = body.get("next_question")
        assert nq is not None, "Expected a first question"
        # Verify correct field names are returned (catches column name regressions)
        assert "question_type" in nq, "Missing question_type — DB column name mismatch?"
        assert "question_en" in nq, "Missing question_en — DB column name mismatch?"
        assert nq["question_type"] == "mcq"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_correct_mcq_answer():
    """POST /api/assessment/answer with correct MCQ → raw_score 1.0."""
    # Session has no items answered yet
    in_progress_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
        "status": "in_progress",
        "current_question_id": Q_MCQ_ID,
        "answers": {"theta": 0.0, "theta_se": 1.0, "stopped": False, "items": []},
        "theta_estimate": 0.0,
        "theta_se": 1.0,
    }

    # After 1 answer the session is still in_progress (not enough to stop)
    # Admin returns: question detail, then questions list, then competency slug
    admin = _build_chainable([
        MCQ_QUESTION,              # question detail lookup
        [MCQ_QUESTION],            # remaining questions for next item selection
        {"slug": COMP_SLUG},       # competency slug for response
    ])
    user = _build_chainable([
        in_progress_session,       # session lookup
        {"id": SESSION_ID},        # session update
    ])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/answer",
                json={
                    "session_id": SESSION_ID,
                    "question_id": Q_MCQ_ID,
                    "answer": "B",              # correct answer
                    "response_time_ms": 5000,
                },
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["raw_score"] == 1.0, f"Correct MCQ should score 1.0, got {body['raw_score']}"
        assert body["question_id"] == Q_MCQ_ID
        assert "session" in body
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_wrong_mcq_answer():
    """POST /api/assessment/answer with wrong MCQ → raw_score 0.0."""
    in_progress_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
        "status": "in_progress",
        "current_question_id": Q_MCQ_ID,
        "answers": {"theta": 0.0, "theta_se": 1.0, "stopped": False, "items": []},
        "theta_estimate": 0.0,
        "theta_se": 1.0,
    }

    admin = _build_chainable([
        MCQ_QUESTION,
        [MCQ_QUESTION],
        {"slug": COMP_SLUG},
    ])
    user = _build_chainable([
        in_progress_session,
        {"id": SESSION_ID},
    ])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/answer",
                json={
                    "session_id": SESSION_ID,
                    "question_id": Q_MCQ_ID,
                    "answer": "A",              # wrong answer
                    "response_time_ms": 5000,
                },
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["raw_score"] == 0.0, f"Wrong MCQ should score 0.0, got {body['raw_score']}"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_open_ended_uses_keyword_fallback():
    """Open-ended answer with LLM disabled → keyword fallback still returns 0.0–1.0."""
    in_progress_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
        "status": "in_progress",
        "current_question_id": Q_OPEN_ID,
        "answers": {"theta": 0.0, "theta_se": 1.0, "stopped": False, "items": []},
        "theta_estimate": 0.0,
        "theta_se": 1.0,
    }

    admin = _build_chainable([
        OPEN_QUESTION,
        [OPEN_QUESTION],
        {"slug": COMP_SLUG},
    ])
    user = _build_chainable([
        in_progress_session,
        {"id": SESSION_ID},
    ])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    # Disable LLM — force keyword fallback
    with patch("app.core.assessment.bars._try_gemini", AsyncMock(return_value=None)), \
         patch("app.core.assessment.bars._try_openai", AsyncMock(return_value=None)):

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/assessment/answer",
                    json={
                        "session_id": SESSION_ID,
                        "question_id": Q_OPEN_ID,
                        # Contains keywords that match concepts
                        "answer": "I lead the team by communicating clearly and making decisions together.",
                        "response_time_ms": 8000,
                    },
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert 0.0 <= body["raw_score"] <= 1.0, f"Score out of range: {body['raw_score']}"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_assessment_returns_aura_score():
    """POST /api/assessment/complete/{session_id} → score in [0, 100]."""
    completed_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
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
                    "question_id": Q_MCQ_ID,
                    "irt_a": 1.2,
                    "irt_b": 0.0,
                    "irt_c": 0.2,
                    "response": 1,
                    "raw_score": 1.0,
                    "response_time_ms": 5000,
                }
            ],
        },
        "completed_at": "2026-03-24T12:00:00Z",
    }

    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=True))

    admin = _build_chainable([
        {"slug": COMP_SLUG},      # competency slug lookup
    ])
    admin.rpc = MagicMock(return_value=rpc_mock)

    user = _build_chainable([
        completed_session,         # session lookup
    ])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
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
        assert 0 <= body["competency_score"] <= 100, f"Score out of range: {body['competency_score']}"
        assert body["session_id"] == SESSION_ID
        assert body["competency_slug"] == COMP_SLUG
        assert body["aura_updated"] is True
        # theta/theta_se must NOT be in response (security P1)
        assert "theta" not in body, "theta must not be exposed to client (security P1)"
        assert "theta_se" not in body, "theta_se must not be exposed to client (security P1)"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_results_returns_same_score():
    """GET /api/assessment/results/{session_id} → same structure as complete."""
    completed_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
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
                    "question_id": Q_MCQ_ID,
                    "irt_a": 1.2,
                    "irt_b": 0.0,
                    "irt_c": 0.2,
                    "response": 1,
                    "raw_score": 1.0,
                    "response_time_ms": 5000,
                }
            ],
        },
        "completed_at": "2026-03-24T12:00:00Z",
    }

    admin = _build_chainable([
        {"slug": COMP_SLUG},
    ])
    user = _build_chainable([
        completed_session,
    ])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                f"/api/assessment/results/{SESSION_ID}",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert 0 <= body["competency_score"] <= 100
        assert body["competency_slug"] == COMP_SLUG
        assert "theta" not in body
        assert "theta_se" not in body
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cannot_answer_wrong_question():
    """Submitting a different question_id than current_question_id → 422."""
    in_progress_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
        "status": "in_progress",
        "current_question_id": Q_MCQ_ID,  # expects MCQ question
        "answers": {"theta": 0.0, "theta_se": 1.0, "stopped": False, "items": []},
        "theta_estimate": 0.0,
        "theta_se": 1.0,
    }

    user = _build_chainable([in_progress_session])
    admin = _build_chainable([])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/answer",
                json={
                    "session_id": SESSION_ID,
                    "question_id": Q_OPEN_ID,  # wrong question id
                    "answer": "B",
                    "response_time_ms": 5000,
                },
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 422, f"Expected 422 for wrong question, got {resp.status_code}"
        body = resp.json()
        assert body["detail"]["code"] == "WRONG_QUESTION"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cannot_start_duplicate_session():
    """Starting a second session for same competency while one is in_progress → 409."""
    admin = _build_chainable([
        {"id": COMP_ID},  # competency lookup
    ])
    user = _build_chainable([
        [{"id": "existing-session-id"}],  # existing in-progress session found
    ])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json={"competency_slug": COMP_SLUG},
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 409, f"Expected 409 for duplicate session, got {resp.status_code}"
        body = resp.json()
        assert body["detail"]["code"] == "SESSION_IN_PROGRESS"
        assert "session_id" in body["detail"]
    finally:
        app.dependency_overrides.clear()
