"""Tests for /api/aura endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin, get_supabase_user, get_current_user_id

USER_ID = "uuid-aura-test"
NOW = datetime.utcnow().isoformat()

AURA_ROW = {
    "volunteer_id": USER_ID,
    "total_score": 78.5,
    "badge_tier": "gold",
    "elite_status": False,
    "competency_scores": {
        "communication": 82.0,
        "reliability": 75.0,
        "english_proficiency": 80.0,
        "leadership": 70.0,
        "event_performance": 0.0,
        "tech_literacy": 65.0,
        "adaptability": 72.0,
        "empathy_safeguarding": 90.0,
    },
    "reliability_score": 55.0,
    "reliability_status": "behavioral",
    "events_attended": 0,
    "events_no_show": 0,
    "aura_history": [],
    "last_updated": NOW,
    "visibility": "public",
    "percentile_rank": None,
    "effective_score": None,
}


def _admin_override(db):
    async def _dep():
        yield db
    return _dep


def _user_override(db):
    async def _dep():
        yield db
    return _dep


def _uid_override(uid=USER_ID):
    async def _dep():
        return uid
    return _dep


def _make_mock_db():
    db = MagicMock()
    db.table = MagicMock(return_value=db)
    db.select = MagicMock(return_value=db)
    db.eq = MagicMock(return_value=db)
    db.single = MagicMock(return_value=db)
    db.maybe_single = MagicMock(return_value=db)
    db.execute = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_my_aura_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=AURA_ROW))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["volunteer_id"] == USER_ID
    assert body["total_score"] == 78.5
    assert body["badge_tier"] == "gold"
    assert body["elite_status"] is False


@pytest.mark.asyncio
async def test_get_my_aura_not_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "AURA_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_aura_by_id_found():
    target_id = "uuid-other-volunteer"
    aura_row = {**AURA_ROW, "volunteer_id": target_id}

    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=aura_row))

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/aura/{target_id}")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["volunteer_id"] == target_id


@pytest.mark.asyncio
async def test_get_aura_by_id_not_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/uuid-nonexistent")

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "AURA_NOT_FOUND"


# ── BUG-012: has_pending_evaluations flag ─────────────────────────────────────

def _make_session_with_degraded_eval():
    return {
        "competency_id": "comp-uuid-1",
        "role_level": "volunteer",
        "completed_at": NOW,
        "answers": {
            "theta": 0.5,
            "theta_se": 0.3,
            "stopped": True,
            "stop_reason": "se_threshold",
            "eap_failures": 0,
            "prior_mean": 0.0,
            "prior_sd": 1.0,
            "items": [
                {
                    "question_id": "q-1",
                    "irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2,
                    "response": 1, "raw_score": 0.6,
                    "response_time_ms": 5000, "theta_at_answer": 0.0,
                    "evaluation_log": {
                        "evaluation_mode": "degraded",
                        "model_used": "keyword_fallback",
                        "methodology": "BARS",
                        "concept_scores": {"clarity": 0.6},
                    },
                }
            ],
        },
    }


def _make_session_with_llm_eval():
    return {
        "competency_id": "comp-uuid-2",
        "role_level": "volunteer",
        "completed_at": NOW,
        "answers": {
            "theta": 0.8,
            "theta_se": 0.2,
            "stopped": True,
            "stop_reason": "se_threshold",
            "eap_failures": 0,
            "prior_mean": 0.0,
            "prior_sd": 1.0,
            "items": [
                {
                    "question_id": "q-2",
                    "irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2,
                    "response": 1, "raw_score": 0.85,
                    "response_time_ms": 8000, "theta_at_answer": 0.3,
                    "evaluation_log": {
                        "evaluation_mode": "full_llm",
                        "model_used": "gemini-2.5-flash",
                        "methodology": "BARS",
                        "concept_scores": {"clarity": 0.85},
                    },
                }
            ],
        },
    }


@pytest.mark.asyncio
async def test_explanation_has_pending_when_degraded():
    """BUG-012: has_pending_evaluations=True when any answer has evaluation_mode=degraded."""
    db = _make_mock_db()
    db.order = MagicMock(return_value=db)
    db.limit = MagicMock(return_value=db)
    db.execute = AsyncMock(return_value=MagicMock(data=[_make_session_with_degraded_eval()]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/me/explanation", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["has_pending_evaluations"] is True
    assert body["pending_reeval_count"] == 1
    assert body["explanation_count"] == 1  # degraded eval still included


@pytest.mark.asyncio
async def test_explanation_no_pending_when_llm_eval():
    """BUG-012: has_pending_evaluations=False when all answers have full LLM evaluation."""
    db = _make_mock_db()
    db.order = MagicMock(return_value=db)
    db.limit = MagicMock(return_value=db)
    db.execute = AsyncMock(return_value=MagicMock(data=[_make_session_with_llm_eval()]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/me/explanation", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["has_pending_evaluations"] is False
    assert body["pending_reeval_count"] == 0
    assert body["evaluation_confidence"] if "evaluation_confidence" in body else True  # no assertion on nested


@pytest.mark.asyncio
async def test_explanation_mixed_sessions_counts_degraded():
    """BUG-012: pending_reeval_count reflects only degraded items, not all items."""
    db = _make_mock_db()
    db.order = MagicMock(return_value=db)
    db.limit = MagicMock(return_value=db)
    sessions = [_make_session_with_degraded_eval(), _make_session_with_llm_eval()]
    db.execute = AsyncMock(return_value=MagicMock(data=sessions))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/aura/me/explanation", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["has_pending_evaluations"] is True
    assert body["pending_reeval_count"] == 1  # only the degraded one
    assert body["explanation_count"] == 2
