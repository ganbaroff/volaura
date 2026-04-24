"""Smoke test: full assessment flow — start → answer → complete → results.

Tests the critical beta user path end-to-end using mocked Supabase + LLM.
Catches: column name regressions, RPC param bugs, wrong DB field reads.

Run: pytest apps/api/tests/test_smoke_assessment.py -v
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.services.assessment.helpers import clear_question_cache

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
    mock.delete = MagicMock(return_value=mock)
    mock.eq = MagicMock(return_value=mock)
    mock.neq = MagicMock(return_value=mock)
    mock.gte = MagicMock(return_value=mock)
    mock.lte = MagicMock(return_value=mock)
    mock.gt = MagicMock(return_value=mock)
    mock.lt = MagicMock(return_value=mock)
    mock.order = MagicMock(return_value=mock)
    mock.limit = MagicMock(return_value=mock)
    mock.range = MagicMock(return_value=mock)
    mock.filter = MagicMock(return_value=mock)
    mock.not_ = MagicMock(return_value=mock)
    mock.in_ = MagicMock(return_value=mock)
    mock.single = MagicMock(return_value=mock)
    mock.maybe_single = MagicMock(return_value=mock)
    mock.rpc = MagicMock(return_value=mock)

    responses = iter(execute_side_effects)

    async def _execute(*args, **kwargs):
        try:
            val = next(responses)
            # Pre-built MagicMock (e.g. for count queries) — pass through directly
            if isinstance(val, MagicMock):
                return val
            return MagicMock(data=val)
        except StopIteration:
            return MagicMock(data=None)

    mock.execute = AsyncMock(side_effect=_execute)
    return mock


# ── Test 1: Full happy path — MCQ only session ─────────────────────────────────


@pytest.mark.asyncio
async def test_start_assessment_returns_first_question():
    """POST /api/assessment/start → 201 with a question."""
    admin = _build_chainable(
        [
            {"id": COMP_ID},  # competency id lookup
            [],  # stale session check (none found)
            [MCQ_QUESTION],  # questions list
        ]
    )
    user = _build_chainable(
        [
            # paywall check removed — PAYMENT_ENABLED=False (beta mode), gate is skipped
            {"is_platform_admin": False},  # admin lookup — FIRST (commit f2ce68f reorder)
            [],  # no existing in-progress session
            [],  # rapid-restart cooldown check (no recent abandoned sessions)
            [],  # retest cooldown check (no completed sessions)
            MagicMock(data=[], count=0),  # abuse monitoring count query
            [],  # carry-over theta (no prior completed session)
            {"id": SESSION_ID},  # insert session
        ]
    )

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json={"competency_slug": COMP_SLUG, "automated_decision_consent": True},
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
    admin = _build_chainable(
        [
            MCQ_QUESTION,  # question detail lookup
            [MCQ_QUESTION],  # remaining questions for next item selection
            {"slug": COMP_SLUG},  # competency slug for response
        ]
    )
    user = _build_chainable(
        [
            in_progress_session,  # session lookup
            {"id": SESSION_ID},  # session update
        ]
    )

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
                    "answer": "B",  # correct answer
                    "response_time_ms": 5000,
                },
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        # raw_score removed from response (CRIT-03 security fix — prevents calibration attacks)
        assert "raw_score" not in body, "raw_score must NOT be in response (CRIT-03)"
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

    admin = _build_chainable(
        [
            MCQ_QUESTION,
            [MCQ_QUESTION],
            {"slug": COMP_SLUG},
        ]
    )
    user = _build_chainable(
        [
            in_progress_session,
            {"id": SESSION_ID},
        ]
    )

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
                    "answer": "A",  # wrong answer
                    "response_time_ms": 5000,
                },
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "raw_score" not in body, "raw_score must NOT be in response (CRIT-03)"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_open_ended_uses_keyword_fallback():
    """Open-ended answer with LLM disabled → keyword fallback still returns 0.0–1.0."""
    # Clear module-level caches so all DB calls flow through the mock in a
    # deterministic order regardless of which tests ran before this one.
    clear_question_cache()

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

    # Admin call order for degraded (keyword fallback) path:
    # 1. question detail
    # 2. daily LLM cap check (assessment_sessions for today — open-ended path only)
    # 3. competency slug for re-eval queue (degraded path)
    # 4. enqueue_degraded_answer insert into evaluation_queue
    # 5. fetch_questions (next item selection)
    # 6. update session (db_admin; optimistic locking)
    # 7. competency slug for make_session_out (or cache hit after call 3)
    admin = _build_chainable(
        [
            OPEN_QUESTION,  # 1. question detail
            [],  # 2. daily LLM cap check (no sessions today)
            {"slug": COMP_SLUG},  # 3. competency slug for re-eval queue
            [{"id": "queue-row-1"}],  # 4. evaluation_queue insert result (truthy)
            [OPEN_QUESTION],  # 5. fetch_questions
            [{"id": SESSION_ID}],  # 6. update session result (must be truthy)
            {"slug": COMP_SLUG},  # 7. competency slug for make_session_out
        ]
    )
    user = _build_chainable(
        [
            in_progress_session,  # session lookup
        ]
    )

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    # Disable all LLMs — force keyword fallback
    with (
        patch("app.core.assessment.bars._try_gemini", AsyncMock(return_value=(None, None))),
        patch("app.core.assessment.bars._try_groq", AsyncMock(return_value=(None, None))),
        patch("app.core.assessment.bars._try_openai", AsyncMock(return_value=(None, None))),
    ):
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
            assert "raw_score" not in body, "raw_score must NOT be in response (CRIT-03)"
            assert "session" in body
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_assessment_returns_aura_score():
    """POST /api/assessment/complete/{session_id} → score in [0, 100]."""
    # status="in_progress" — forces the full pipeline path:
    # gaming update → slug lookup → upsert_aura_score RPC → aura_updated=True.
    # A "completed" session would hit the early-return path (aura_updated=False).
    completed_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
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
        "completed_at": None,
    }

    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=True))

    # Admin call order: 1. update gaming columns, 2. competency slug lookup, 3. rpc (overridden)
    admin = _build_chainable(
        [
            [{"id": SESSION_ID}],  # 1. update gaming columns (truthy = no exception)
            {"slug": COMP_SLUG},  # 2. competency slug lookup
        ]
    )
    admin.rpc = MagicMock(return_value=rpc_mock)

    user = _build_chainable(
        [
            completed_session,  # session lookup
        ]
    )

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    _smoke_job = {
        "id": "smoke-job-1",
        "session_id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_slug": COMP_SLUG,
        "status": "pending",
        "attempts": 0,
        "side_effects": {
            k: {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-24T00:00:00Z"}
            for k in (
                "aura_sync",
                "rewards",
                "streak",
                "analytics",
                "email",
                "ecosystem_events",
                "aura_events",
                "decision_log",
            )
        },
        "result_context": {
            "competency_slug": COMP_SLUG,
            "competency_score": 72.5,
            "questions_answered": 1,
            "stop_reason": "se_threshold",
            "gaming_flags": [],
            "completed_at": "2026-04-24T10:00:00Z",
            "aura_updated": False,
            "crystals_earned": 0,
            "energy_level": "full",
            "old_badge_tier": None,
            "aura_snapshot": None,
        },
        "last_error": None,
        "completed_at": None,
    }

    async def _smoke_save_job(_db, job, **kwargs):
        next_job = dict(job)
        next_job.update(kwargs)
        return next_job

    try:
        with (
            patch("app.routers.assessment.get_completion_job", new=AsyncMock(return_value=None)),
            patch("app.routers.assessment.ensure_completion_job", new=AsyncMock(return_value=_smoke_job)),
            patch("app.routers.assessment.save_completion_job", new=AsyncMock(side_effect=_smoke_save_job)),
        ):
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

    admin = _build_chainable(
        [
            {"slug": COMP_SLUG},
        ]
    )
    user = _build_chainable(
        [
            completed_session,
        ]
    )

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
    admin = _build_chainable(
        [
            {"id": COMP_ID},  # competency lookup
            [],  # stale session check (none found)
        ]
    )
    user = _build_chainable(
        [
            # paywall check removed — PAYMENT_ENABLED=False (beta mode), gate is skipped
            {"is_platform_admin": False},  # admin lookup — FIRST (commit f2ce68f reorder)
            [{"id": "existing-session-id"}],  # in-progress session found → triggers 409
        ]
    )

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(user)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/start",
                json={"competency_slug": COMP_SLUG, "automated_decision_consent": True},
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 409, f"Expected 409 for duplicate session, got {resp.status_code}"
        body = resp.json()
        assert body["detail"]["code"] == "SESSION_IN_PROGRESS"
        assert "session_id" in body["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_answer_returns_410_when_session_expired():
    """POST /api/assessment/answer with a past expires_at → 410 SESSION_EXPIRED.

    Covers assessment.py lines 325-336:
        expires_at_str = session.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(...)
            if expires_at and now_utc > expires_at:
                raise HTTPException(status_code=410, detail={"code": "SESSION_EXPIRED", ...})
    """
    expired_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
        "status": "in_progress",
        "current_question_id": Q_MCQ_ID,
        "answers": {"theta": 0.0, "theta_se": 1.0, "stopped": False, "items": []},
        "theta_estimate": 0.0,
        "theta_se": 1.0,
        "expires_at": "2020-01-01T00:00:00+00:00",  # far in the past
    }

    user = _build_chainable([expired_session])
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
                    "question_id": Q_MCQ_ID,
                    "answer": "B",
                    "response_time_ms": 5000,
                },
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 410, (
            f"Expected 410 SESSION_EXPIRED for expired session, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["detail"]["code"] == "SESSION_EXPIRED", f"Expected code SESSION_EXPIRED, got: {body['detail']}"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_complete_assessment_returns_410_when_session_expired():
    """POST /api/assessment/complete/{session_id} with a past expires_at → 410 SESSION_EXPIRED.

    Covers assessment.py lines 564-572:
        expires_at_str = session.get("expires_at")
        if expires_at_str and session.get("status") == "in_progress":
            expires_at = datetime.fromisoformat(...)
            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(status_code=410, detail={"code": "SESSION_EXPIRED", ...})
    """
    expired_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
        "status": "in_progress",  # must be in_progress — completed sessions skip this gate
        "theta_estimate": 0.5,
        "theta_se": 0.3,
        "answers": {"theta": 0.5, "theta_se": 0.3, "stopped": False, "items": []},
        "completed_at": None,
        "expires_at": "2020-01-01T00:00:00+00:00",  # far in the past
    }

    user = _build_chainable([expired_session])
    admin = _build_chainable([])

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

        assert resp.status_code == 410, (
            f"Expected 410 SESSION_EXPIRED for expired session, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["detail"]["code"] == "SESSION_EXPIRED", f"Expected code SESSION_EXPIRED, got: {body['detail']}"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_answer_returns_409_on_version_conflict():
    """answer_version optimistic lock fires when concurrent submit beats us.

    Covers assessment.py lines 488-496:
        update_result = await db_admin.table("assessment_sessions").update(...)
            .eq("answer_version", current_version).execute()
        if not update_result.data:
            raise HTTPException(status_code=409, detail={"code": "CONCURRENT_SUBMIT", ...})

    The winning concurrent submit already incremented answer_version in the DB,
    so our UPDATE's .eq("answer_version", current_version) matches nothing → data=[].
    """
    # Clear module-level caches so all DB calls flow through the mock in a
    # deterministic order regardless of which tests ran before this one.
    clear_question_cache()

    in_progress_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMP_ID,
        "status": "in_progress",
        "current_question_id": Q_MCQ_ID,
        "answers": {"theta": 0.0, "theta_se": 1.0, "stopped": False, "items": []},
        "theta_estimate": 0.0,
        "theta_se": 1.0,
        # answer_version present — concurrent submit will have incremented this
        "answer_version": 3,
    }

    # Admin call order (MCQ path, no LLM, caches cleared):
    #   1. question detail lookup       (.single())
    #   2. fetch_questions list         (next item selection — cache miss)
    #   3. UPDATE with optimistic lock  → returns [] (version mismatch = concurrent submit)
    admin = _build_chainable(
        [
            MCQ_QUESTION,  # 1. question detail
            [MCQ_QUESTION],  # 2. fetch_questions (cache cleared, so DB hit)
            [],  # 3. UPDATE returns empty list — optimistic lock version conflict
        ]
    )
    user = _build_chainable(
        [
            in_progress_session,  # session fetch
        ]
    )

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
                    "answer": "B",
                    "response_time_ms": 5000,
                },
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 409, f"Expected 409 CONCURRENT_SUBMIT, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["detail"]["code"] == "CONCURRENT_SUBMIT", f"Expected code CONCURRENT_SUBMIT, got: {body['detail']}"
        assert "already submitted" in body["detail"]["message"].lower(), (
            f"Expected user-facing message about duplicate submit, got: {body['detail']['message']}"
        )
    finally:
        app.dependency_overrides.clear()
        clear_question_cache()  # leave caches clean for subsequent tests
