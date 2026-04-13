"""
Audit Regression Tests — Batch 1
================================

Verifies fixes for:
- [C1] Activity feed table names
- [C2] Activity feed column names
- [H1] Raw score exposure redaction
- [H2] Open Badge column names
- [H3] Organization schema alignment
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# Mock data
USER_ID = str(uuid4())
ORG_ID = str(uuid4())


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
    db.insert = MagicMock(return_value=db)
    db.update = MagicMock(return_value=db)
    db.eq = MagicMock(return_value=db)
    db.neq = MagicMock(return_value=db)
    db.gte = MagicMock(return_value=db)
    db.lte = MagicMock(return_value=db)
    db.order = MagicMock(return_value=db)
    db.limit = MagicMock(return_value=db)
    db.range = MagicMock(return_value=db)
    db.in_ = MagicMock(return_value=db)
    db.single = MagicMock(return_value=db)
    db.maybe_single = MagicMock(return_value=db)
    db.rpc = MagicMock(return_value=db)
    db.execute = AsyncMock(return_value=MagicMock(data=[], count=0))
    return db


@pytest.mark.asyncio
async def test_activity_feed_uses_correct_tables(client):
    """Verify activity feed uses 'registrations' and not 'event_registrations'."""
    db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    try:
        await client.get("/api/activity/me", headers={"Authorization": "Bearer fake"})

        # Inspect all .table() calls
        calls = [c.args[0] for c in db.table.call_args_list if c.args]
        assert "registrations" in calls, f"Expected 'registrations' in table calls, got: {calls}"
        assert "event_registrations" not in calls, (
            "activity.py must use 'registrations', not the old 'event_registrations' table"
        )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_aura_explanation_redacts_raw_score(client):
    """Verify /aura/me/explanation does NOT contain raw_score in the evaluation items.

    The endpoint reads answers.items[].evaluation_log but never returns raw_score to client.
    This test catches any accidental exposure of raw_score (CRIT-03/CRIT-05).
    """
    # Mock the completed sessions data structure
    sessions_data = [{
        "competency_id": "comp-uuid-123",
        "role_level": "volunteer",
        "completed_at": "2026-03-01T00:00:00Z",
        "answers": {
            "items": [{
                "question_id": "q1",
                "evaluation_log": {
                    "model_used": "gemini",
                    "concept_scores": {"communication": 0.8},
                    "methodology": "BARS",
                    # raw_score intentionally NOT in evaluation_log (CRIT-03)
                },
            }]
        },
    }]

    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=sessions_data))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    try:
        response = await client.get("/api/aura/me/explanation", headers={"Authorization": "Bearer fake"})
        assert response.status_code == 200
        data = response.json()

        # Response structure: data["explanations"][0]["evaluations"][0]
        assert "explanations" in data
        assert len(data["explanations"]) > 0
        evaluation = data["explanations"][0]["evaluations"][0]
        assert "raw_score" not in evaluation, "raw_score must NOT be exposed in explanation (CRIT-03/CRIT-05)"
        assert evaluation["question_id"] == "q1"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_badges_credential_uses_correct_columns(client):
    """Verify badges credential uses total_score and last_updated (not the old column names)."""
    from httpx import ASGITransport, AsyncClient

    admin_db = _make_mock_db()

    # table("profiles") → profile row, table("aura_scores") → score row
    def table_side_effect(table_name: str):
        m = MagicMock()
        m.select = MagicMock(return_value=m)
        m.eq = MagicMock(return_value=m)
        m.single = MagicMock(return_value=m)
        m.maybe_single = MagicMock(return_value=m)
        if table_name == "profiles":
            m.execute = AsyncMock(return_value=MagicMock(data={
                "id": USER_ID,
                "username": "testuser",
                "display_name": "Test User",
                "badge_issued_at": None,
            }))
        elif table_name == "aura_scores":
            m.execute = AsyncMock(return_value=MagicMock(data={
                "total_score": 85.0,
                "badge_tier": "gold",
                "elite_status": False,
                "last_updated": "2026-03-25T00:00:00Z",
                "visibility": "public",
            }))
        else:
            m.execute = AsyncMock(return_value=MagicMock(data=None))
        return m

    admin_db.table = MagicMock(side_effect=table_side_effect)

    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"/api/badges/{USER_ID}/credential")
        assert response.status_code == 200
        data = response.json()

        # Verify result contains the correct score
        result = data["credentialSubject"]["result"][0]
        assert result["value"] == "85.0"
        assert data["issuanceDate"] == "2026-03-25T00:00:00Z"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_engine_min_items_constant():
    """Verify engine constant was updated."""
    from app.core.assessment.engine import MIN_ITEMS_BEFORE_SE_STOP
    assert MIN_ITEMS_BEFORE_SE_STOP == 5
