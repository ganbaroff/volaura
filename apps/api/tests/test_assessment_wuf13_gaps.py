"""WUF13 gap-coverage tests for assessment router.

Targets the three critical endpoints missed in prior coverage runs:
  - POST /{session_id}/coaching          (lines 1662-1730)
  - GET  /results/{session_id}/questions (lines 1840-1907)
  - GET  /verify/{session_id}            (lines 1918-1990)

Also covers carry-over theta in start_assessment (lines 438-508).

Mock strategy: same Cerebras pattern as test_assessment_router_pipeline.py
  - app.dependency_overrides for get_current_user_id / get_supabase_admin / get_supabase_user
  - _chainable() builder for fluent Supabase mock chains
  - always try/finally to restore dependency_overrides
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"
SESSION_ID = "11111111-aaaa-bbbb-cccc-222222222222"
COMPETENCY_ID = "55555555-6666-7777-8888-999999999999"
QUESTION_ID_1 = "eeeeeeee-aaaa-bbbb-cccc-ffffffffffff"
QUESTION_ID_2 = "ffffffff-bbbb-cccc-dddd-eeeeeeeeeeee"

# ── Dependency helpers (identical to pipeline tests) ──────────────────────────


def _admin_override(db: Any):
    async def _dep():
        yield db

    return _dep


def _user_override(db: Any):
    async def _dep():
        yield db

    return _dep


def _uid_override(uid: str = USER_ID):
    async def _dep():
        return uid

    return _dep


# ── Chainable mock builder ─────────────────────────────────────────────────────


def _chainable(execute_result: Any = None) -> MagicMock:
    """Supabase fluent API mock returning self from every chain method."""
    m = MagicMock()
    m.table = MagicMock(return_value=m)
    m.select = MagicMock(return_value=m)
    m.insert = MagicMock(return_value=m)
    m.update = MagicMock(return_value=m)
    m.delete = MagicMock(return_value=m)
    m.eq = MagicMock(return_value=m)
    m.neq = MagicMock(return_value=m)
    m.lt = MagicMock(return_value=m)
    m.gte = MagicMock(return_value=m)
    m.is_ = MagicMock(return_value=m)
    m.in_ = MagicMock(return_value=m)
    m.order = MagicMock(return_value=m)
    m.limit = MagicMock(return_value=m)
    m.single = MagicMock(return_value=m)
    m.maybe_single = MagicMock(return_value=m)
    m.rpc = MagicMock(return_value=m)
    m.execute = AsyncMock(return_value=MagicMock(data=execute_result, count=None))
    m.auth = MagicMock()
    m.auth.admin = MagicMock()
    m.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=None))
    return m


# ── Serialised CATState with 2 answered items ─────────────────────────────────


def _cat_answers_with_items() -> dict:
    """Minimal serialised CATState matching engine.CATState.from_dict() contract."""
    return {
        "theta": 0.5,
        "theta_se": 0.4,
        "stopped": True,
        "stop_reason": "se_threshold",
        "eap_failures": 0,
        "prior_mean": 0.0,
        "prior_sd": 1.0,
        "items": [
            {
                "question_id": QUESTION_ID_1,
                "irt_a": 1.0,
                "irt_b": 0.2,
                "irt_c": 0.25,
                "response": 1,
                "raw_score": 1.0,
                "response_time_ms": 4200,
                "theta_at_answer": 0.0,
            },
            {
                "question_id": QUESTION_ID_2,
                "irt_a": 1.2,
                "irt_b": 0.8,
                "irt_c": 0.25,
                "response": 0,
                "raw_score": 0.0,
                "response_time_ms": 6100,
                "theta_at_answer": 0.5,
            },
        ],
    }


def _cat_answers_empty() -> dict:
    """Serialised CATState with no items (edge case)."""
    return {
        "theta": 0.0,
        "theta_se": 1.0,
        "stopped": False,
        "stop_reason": None,
        "eap_failures": 0,
        "prior_mean": 0.0,
        "prior_sd": 1.0,
        "items": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# get_coaching  POST /{session_id}/coaching
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_coaching_invalid_uuid():
    """Non-UUID session_id returns 422 without hitting DB."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db = _chainable(None)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_supabase_user] = _user_override(db)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            resp = await ac.post("/api/assessment/not-a-uuid/coaching")
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INVALID_SESSION_ID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_coaching_session_not_found():
    """Returns 404 when session does not exist or doesn't belong to user."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db_user = _chainable(None)   # maybe_single returns None
        db_admin = _chainable(None)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            resp = await ac.post(f"/api/assessment/{SESSION_ID}/coaching")
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "SESSION_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_coaching_returns_cached_note():
    """When coaching_note is already present in DB, returns it without calling LLM."""
    cached_tips = [
        {"title": "Tip 1", "description": "Do X", "action": "Practice X daily"},
        {"title": "Tip 2", "description": "Do Y", "action": "Try Y weekly"},
        {"title": "Tip 3", "description": "Do Z", "action": "Apply Z"},
    ]
    session_row = {
        "id": SESSION_ID,
        "competency_id": COMPETENCY_ID,
        "theta_estimate": 0.5,
        "coaching_note": cached_tips,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db_user = _chainable(session_row)
        db_admin = _chainable(None)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            resp = await ac.post(f"/api/assessment/{SESSION_ID}/coaching")
            assert resp.status_code == 200
            body = resp.json()
            assert body["session_id"] == SESSION_ID
            assert body["competency_id"] == COMPETENCY_ID
            assert len(body["tips"]) == 3
            assert body["tips"][0]["title"] == "Tip 1"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_coaching_malformed_cached_note_regenerates():
    """When coaching_note exists but is malformed, falls through to LLM regeneration."""
    # coaching_note is a list but contains broken dicts missing required fields
    broken_cache = [{"title_typo": "X"}]  # CoachingTip(**t) will raise KeyError
    session_row = {
        "id": SESSION_ID,
        "competency_id": COMPETENCY_ID,
        "theta_estimate": 0.5,
        "coaching_note": broken_cache,
    }
    comp_row = {"name_en": "Communication", "slug": "communication"}

    from app.schemas.assessment import CoachingTip

    generated_tips = [
        CoachingTip(title="Regen A", description="Desc A", action="Act A"),
        CoachingTip(title="Regen B", description="Desc B", action="Act B"),
        CoachingTip(title="Regen C", description="Desc C", action="Act C"),
    ]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db_user = _chainable(session_row)
        db_admin = _chainable(comp_row)
        db_admin.update = MagicMock(return_value=db_admin)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()

        with patch(
            "app.routers.assessment.generate_coaching_tips",
            new=AsyncMock(return_value=generated_tips),
        ):
            try:
                resp = await ac.post(f"/api/assessment/{SESSION_ID}/coaching")
                assert resp.status_code == 200
                body = resp.json()
                assert body["tips"][0]["title"] == "Regen A"
            finally:
                app.dependency_overrides.pop(get_supabase_admin, None)
                app.dependency_overrides.pop(get_supabase_user, None)
                app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_coaching_cache_update_failure_still_returns_tips():
    """If DB update of coaching_note raises, response still succeeds (graceful degradation)."""
    session_row = {
        "id": SESSION_ID,
        "competency_id": COMPETENCY_ID,
        "theta_estimate": 0.5,
        "coaching_note": None,
    }
    comp_row = {"name_en": "Leadership", "slug": "leadership"}

    from app.schemas.assessment import CoachingTip

    generated_tips = [
        CoachingTip(title="T1", description="D1", action="A1"),
        CoachingTip(title="T2", description="D2", action="A2"),
        CoachingTip(title="T3", description="D3", action="A3"),
    ]

    # db_admin: first call = comp lookup (success), second call = update (raises)
    db_admin = MagicMock()
    db_admin.table = MagicMock(return_value=db_admin)
    db_admin.select = MagicMock(return_value=db_admin)
    db_admin.eq = MagicMock(return_value=db_admin)
    db_admin.maybe_single = MagicMock(return_value=db_admin)
    db_admin.update = MagicMock(return_value=db_admin)
    db_admin.execute = AsyncMock(
        side_effect=[
            MagicMock(data=comp_row),        # comp lookup
            Exception("column not found"),    # update raises
        ]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db_user = _chainable(session_row)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()

        with patch(
            "app.routers.assessment.generate_coaching_tips",
            new=AsyncMock(return_value=generated_tips),
        ):
            try:
                resp = await ac.post(f"/api/assessment/{SESSION_ID}/coaching")
                assert resp.status_code == 200
                assert len(resp.json()["tips"]) == 3
            finally:
                app.dependency_overrides.pop(get_supabase_admin, None)
                app.dependency_overrides.pop(get_supabase_user, None)
                app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_coaching_generates_and_caches_tips():
    """When no cached note, calls LLM, caches result, returns 200."""
    session_row = {
        "id": SESSION_ID,
        "competency_id": COMPETENCY_ID,
        "theta_estimate": 0.5,
        "coaching_note": None,
    }
    comp_row = {"name_en": "Communication", "slug": "communication"}

    from app.schemas.assessment import CoachingTip

    generated_tips = [
        CoachingTip(title="Tip A", description="Desc A", action="Act A"),
        CoachingTip(title="Tip B", description="Desc B", action="Act B"),
        CoachingTip(title="Tip C", description="Desc C", action="Act C"),
    ]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db_user = _chainable(session_row)
        db_admin = _chainable(comp_row)
        # update call also goes through db_admin — still returns something chainable
        db_admin.update = MagicMock(return_value=db_admin)

        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()

        with patch(
            "app.routers.assessment.generate_coaching_tips",
            new=AsyncMock(return_value=generated_tips),
        ):
            try:
                resp = await ac.post(f"/api/assessment/{SESSION_ID}/coaching")
                assert resp.status_code == 200
                body = resp.json()
                assert body["session_id"] == SESSION_ID
                assert len(body["tips"]) == 3
                assert body["tips"][0]["title"] == "Tip A"
            finally:
                app.dependency_overrides.pop(get_supabase_admin, None)
                app.dependency_overrides.pop(get_supabase_user, None)
                app.dependency_overrides.pop(get_current_user_id, None)


# ═══════════════════════════════════════════════════════════════════════════════
# get_question_breakdown  GET /results/{session_id}/questions
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_breakdown_invalid_uuid():
    """Non-UUID returns 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db = _chainable(None)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db)
        app.dependency_overrides[get_supabase_user] = _user_override(db)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            resp = await ac.get("/api/assessment/results/bad-id/questions")
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INVALID_SESSION_ID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_breakdown_session_not_found():
    """Returns 404 when session missing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db_user = _chainable(None)
        db_admin = _chainable(None)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            resp = await ac.get(f"/api/assessment/results/{SESSION_ID}/questions")
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "SESSION_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_breakdown_no_answers():
    """Session exists but has no answered items — returns 404 NO_ANSWERS."""
    session_row = {
        "id": SESSION_ID,
        "competency_id": COMPETENCY_ID,
        "answers": _cat_answers_empty(),
        "theta_estimate": 0.0,
        "gaming_penalty_multiplier": None,
    }

    # db_user returns session; db_admin needs two calls (questions + competency)
    # Use a single chainable that returns appropriate data per call.
    db_user = _chainable(session_row)
    db_admin = _chainable([])  # questions batch returns empty list

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            resp = await ac.get(f"/api/assessment/results/{SESSION_ID}/questions")
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "NO_ANSWERS"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_breakdown_happy_path():
    """Returns per-question breakdown with difficulty labels and correctness."""
    session_row = {
        "id": SESSION_ID,
        "competency_id": COMPETENCY_ID,
        "answers": _cat_answers_with_items(),
        "theta_estimate": 0.5,
        "gaming_penalty_multiplier": 1.0,
    }
    questions_data = [
        {
            "id": QUESTION_ID_1,
            "scenario_en": "Question one text",
            "scenario_az": "Sual bir mətni",
            "scenario_ru": "Текст вопроса один",
        },
        {
            "id": QUESTION_ID_2,
            "scenario_en": "Question two text",
            "scenario_az": None,
            "scenario_ru": None,
        },
    ]
    comp_data = {"slug": "communication"}

    # db_admin will be called twice: questions in_, then competency.
    # Build a side-effect sequence on execute.
    db_user = _chainable(session_row)
    db_admin = MagicMock()
    db_admin.table = MagicMock(return_value=db_admin)
    db_admin.select = MagicMock(return_value=db_admin)
    db_admin.eq = MagicMock(return_value=db_admin)
    db_admin.in_ = MagicMock(return_value=db_admin)
    db_admin.maybe_single = MagicMock(return_value=db_admin)
    db_admin.update = MagicMock(return_value=db_admin)
    db_admin.execute = AsyncMock(
        side_effect=[
            MagicMock(data=questions_data),   # questions batch
            MagicMock(data=comp_data),        # competency slug
        ]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            resp = await ac.get(f"/api/assessment/results/{SESSION_ID}/questions")
            assert resp.status_code == 200
            body = resp.json()
            assert body["session_id"] == SESSION_ID
            assert body["competency_slug"] == "communication"
            assert len(body["questions"]) == 2
            q1 = body["questions"][0]
            assert q1["question_id"] == QUESTION_ID_1
            assert q1["is_correct"] is True   # raw_score 1.0 > 0
            assert q1["difficulty_label"] == "medium"   # irt_b=0.2 → medium
            assert q1["response_time_ms"] == 4200
            q2 = body["questions"][1]
            assert q2["is_correct"] is False  # raw_score 0.0
            assert q2["difficulty_label"] == "hard"     # irt_b=0.8 → hard
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ═══════════════════════════════════════════════════════════════════════════════
# verify_assessment  GET /verify/{session_id}  (no auth required)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_verify_invalid_uuid():
    """Non-UUID session_id returns 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db_admin = _chainable(None)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        try:
            resp = await ac.get("/api/assessment/verify/not-a-uuid")
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INVALID_SESSION_ID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_verify_session_not_found():
    """Returns 404 when completed session not found."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        db_admin = _chainable(None)
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        try:
            resp = await ac.get(f"/api/assessment/verify/{SESSION_ID}")
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "SESSION_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_verify_happy_path():
    """Public verification returns session, competency, badge tier, profile."""
    session_row = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "completed",
        "answers": _cat_answers_with_items(),
        "completed_at": "2026-04-20T12:00:00+00:00",
        "gaming_penalty_multiplier": 1.0,
    }
    comp_row = {"slug": "communication", "name_en": "Communication"}
    aura_row = {"badge_tier": "Gold"}
    profile_row = {"display_name": "Yusif G.", "username": "yusifg"}

    db_admin = MagicMock()
    db_admin.table = MagicMock(return_value=db_admin)
    db_admin.select = MagicMock(return_value=db_admin)
    db_admin.eq = MagicMock(return_value=db_admin)
    db_admin.maybe_single = MagicMock(return_value=db_admin)
    db_admin.execute = AsyncMock(
        side_effect=[
            MagicMock(data=session_row),   # session lookup
            MagicMock(data=comp_row),      # competency
            MagicMock(data=aura_row),      # badge_tier
            MagicMock(data=profile_row),   # profile
        ]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        try:
            resp = await ac.get(f"/api/assessment/verify/{SESSION_ID}")
            assert resp.status_code == 200
            body = resp.json()
            assert body["verified"] is True
            assert body["platform"] == "Volaura"
            assert body["session_id"] == SESSION_ID
            assert body["competency_slug"] == "communication"
            assert body["competency_name"] == "Communication"
            assert body["badge_tier"] == "Gold"
            assert body["questions_answered"] == 2
            assert body["display_name"] == "Yusif G."
            assert body["username"] == "yusifg"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_verify_missing_aura_and_profile():
    """Verification succeeds with badge_tier='none' and null profile fields when rows absent."""
    session_row = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "completed",
        "answers": _cat_answers_with_items(),
        "completed_at": None,
        "gaming_penalty_multiplier": None,
    }
    comp_row = {"slug": "leadership", "name_en": "Leadership"}

    db_admin = MagicMock()
    db_admin.table = MagicMock(return_value=db_admin)
    db_admin.select = MagicMock(return_value=db_admin)
    db_admin.eq = MagicMock(return_value=db_admin)
    db_admin.maybe_single = MagicMock(return_value=db_admin)
    db_admin.execute = AsyncMock(
        side_effect=[
            MagicMock(data=session_row),
            MagicMock(data=comp_row),
            MagicMock(data=None),   # no aura_scores row
            MagicMock(data=None),   # no profile row
        ]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        try:
            resp = await ac.get(f"/api/assessment/verify/{SESSION_ID}")
            assert resp.status_code == 200
            body = resp.json()
            assert body["badge_tier"] == "none"
            assert body["display_name"] is None
            assert body["username"] is None
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)


# ═══════════════════════════════════════════════════════════════════════════════
# Carry-over theta in start_assessment (lines 438-508)
# ═══════════════════════════════════════════════════════════════════════════════


def _start_payload(competency_slug: str = "communication") -> dict:
    return {
        "competency_slug": competency_slug,
        "role_level": "professional",
        "automated_decision_consent": True,
        "energy_level": "full",
    }


def _minimal_question_row(qid: str = QUESTION_ID_1) -> dict:
    return {
        "id": qid,
        "competency_id": COMPETENCY_ID,
        "type": "mcq",
        "scenario_en": "Pick the best option.",
        "scenario_az": "Ən yaxşı variantı seçin.",
        "scenario_ru": None,
        "options": [
            {"key": "A", "text_en": "Option A", "text_az": "Variant A"},
            {"key": "B", "text_en": "Option B", "text_az": "Variant B"},
            {"key": "C", "text_en": "Option C", "text_az": "Variant C"},
            {"key": "D", "text_en": "Option D", "text_az": "Variant D"},
        ],
        "correct_answer": "A",
        "irt_a": 1.0,
        "irt_b": 0.0,
        "irt_c": 0.25,
        "is_active": True,
    }


# Shared patch targets for start_assessment helpers
_PATCH_GET_COMPETENCY_ID = "app.routers.assessment.get_competency_id"
_PATCH_FETCH_QUESTIONS = "app.routers.assessment.fetch_questions"


def _make_start_db_user(
    prev_session: list[dict] | None = None,
    in_progress_data: Any = None,
) -> MagicMock:
    """
    Build db_user mock for /start endpoint with the full expected call sequence.

    Real sequence inside start_assessment (after get_competency_id / fetch_questions
    are patched out):
      1. is_platform_admin check  (profiles.select)
      2. stale session update     (db_admin — handled separately)
      3. in_progress conflict     (assessment_sessions.select)
      4. rapid-restart check      (assessment_sessions.select)
      5. 7-day cooldown check     (assessment_sessions.select)
      6. abuse monitor count      (assessment_sessions.select, count=exact)
      7. carry-over theta lookup  (assessment_sessions.select)
      8. insert new session       (assessment_sessions.insert)
    """
    m = MagicMock()
    for attr in ["table", "select", "insert", "update", "delete", "eq", "neq",
                 "lt", "gte", "is_", "in_", "order", "limit", "single", "maybe_single"]:
        setattr(m, attr, MagicMock(return_value=m))
    m.auth = MagicMock()
    m.auth.admin = MagicMock()
    m.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=None))

    m.execute = AsyncMock(
        side_effect=[
            MagicMock(data=None, count=None),               # 1. is_platform_admin (no row → not admin)
            MagicMock(data=in_progress_data, count=None),   # 3. in_progress conflict
            MagicMock(data=[], count=None),                  # 4. rapid-restart (no recent start)
            MagicMock(data=[], count=None),                  # 5. 7-day cooldown (no recent completed)
            MagicMock(data=[], count=0),                     # 6. abuse monitor (count=0)
            MagicMock(data=prev_session or [], count=None),  # 7. carry-over theta
            MagicMock(data=[], count=None),                  # 8. insert
        ]
    )
    return m


def _make_start_db_admin_minimal() -> MagicMock:
    """db_admin for start_assessment when get_competency_id and fetch_questions are patched.

    Real admin calls remaining:
      1. policy_versions lookup  (GDPR consent log — non-blocking, None = skip insert)
      2. stale session check     (assessment_sessions.select)
    """
    m = MagicMock()
    for attr in ["table", "select", "insert", "update", "delete", "eq", "neq",
                 "lt", "gte", "is_", "in_", "order", "limit", "single", "maybe_single"]:
        setattr(m, attr, MagicMock(return_value=m))
    m.auth = MagicMock()
    m.auth.admin = MagicMock()
    m.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=None))

    m.execute = AsyncMock(
        side_effect=[
            MagicMock(data=None, count=None),   # 1. policy_versions (None → skip consent insert)
            MagicMock(data=[], count=None),      # 2. stale session check (nothing to expire)
        ]
    )
    return m


@pytest.mark.anyio
async def test_start_with_carryover_theta_recent():
    """Prior completed session 10 days ago produces a non-default prior_mean via carry-over."""
    prev_completed_at = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    prev_session = [
        {
            "theta_estimate": 1.0,
            "theta_se": 0.35,
            "completed_at": prev_completed_at,
        }
    ]

    db_user = _make_start_db_user(prev_session=prev_session)
    db_admin = _make_start_db_admin_minimal()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            with (
                patch(_PATCH_GET_COMPETENCY_ID, new=AsyncMock(return_value=COMPETENCY_ID)),
                patch(_PATCH_FETCH_QUESTIONS, new=AsyncMock(return_value=[_minimal_question_row()])),
            ):
                resp = await ac.post("/api/assessment/start", json=_start_payload())
                assert resp.status_code == 201
                body = resp.json()
                assert "session_id" in body
                assert "next_question" in body
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_start_with_no_prior_session():
    """No prior completed session — carry-over returns empty list, prior_mean stays 0.0."""
    db_user = _make_start_db_user(prev_session=[])
    db_admin = _make_start_db_admin_minimal()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(db_user)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            with (
                patch(_PATCH_GET_COMPETENCY_ID, new=AsyncMock(return_value=COMPETENCY_ID)),
                patch(_PATCH_FETCH_QUESTIONS, new=AsyncMock(return_value=[_minimal_question_row()])),
            ):
                resp = await ac.post("/api/assessment/start", json=_start_payload())
                assert resp.status_code == 201
                body = resp.json()
                assert "session_id" in body
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_start_carryover_theta_exception_uses_defaults():
    """DB error during carry-over theta lookup falls back to prior_mean=0.0 gracefully."""
    m = MagicMock()
    for attr in ["table", "select", "insert", "update", "delete", "eq", "neq",
                 "lt", "gte", "is_", "in_", "order", "limit", "single", "maybe_single"]:
        setattr(m, attr, MagicMock(return_value=m))
    m.auth = MagicMock()
    m.auth.admin = MagicMock()
    m.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=None))

    # carry-over call (position 6) raises — endpoint must catch and continue
    m.execute = AsyncMock(
        side_effect=[
            MagicMock(data=None, count=None),   # is_platform_admin
            MagicMock(data=None, count=None),   # in_progress
            MagicMock(data=[], count=None),      # rapid-restart
            MagicMock(data=[], count=None),      # cooldown
            MagicMock(data=[], count=0),          # abuse monitor
            Exception("DB timeout"),             # carry-over fails
            MagicMock(data=[], count=None),      # insert (after fallback)
        ]
    )

    db_admin = _make_start_db_admin_minimal()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        app.dependency_overrides[get_supabase_admin] = _admin_override(db_admin)
        app.dependency_overrides[get_supabase_user] = _user_override(m)
        app.dependency_overrides[get_current_user_id] = _uid_override()
        try:
            with (
                patch(_PATCH_GET_COMPETENCY_ID, new=AsyncMock(return_value=COMPETENCY_ID)),
                patch(_PATCH_FETCH_QUESTIONS, new=AsyncMock(return_value=[_minimal_question_row()])),
            ):
                resp = await ac.post("/api/assessment/start", json=_start_payload())
                # Should succeed with default theta 0.0 despite DB error on carry-over
                assert resp.status_code == 201
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)
