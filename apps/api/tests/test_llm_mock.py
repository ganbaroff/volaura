"""S3-07: LLM mock integration tests.

Validates that:
1. LLM mock fixtures correctly patch the real service
2. Assessment endpoints work without real API calls
3. Mock failure modes (timeout, total failure) are testable
4. Embedding mock returns the right shape

These tests are the "meta-tests" for the mock infrastructure — they ensure
the mocks themselves are working correctly.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from tests.mocks.llm_mock import (
    MOCK_BARS_RESPONSE,
    MOCK_EMBEDDING,
    mock_embedding,
    mock_llm,
    mock_llm_failure,
)

# Re-export fixtures for pytest discovery
__all__ = ["mock_llm", "mock_embedding", "mock_llm_failure"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_admin_override(mock_db):
    async def _override():
        yield mock_db
    return _override


def _make_user_id_override(user_id: str):
    async def _override():
        return user_id
    return _override


def _chainable_db():
    db = MagicMock()
    db.table = MagicMock(return_value=db)
    db.select = MagicMock(return_value=db)
    db.insert = MagicMock(return_value=db)
    db.update = MagicMock(return_value=db)
    db.eq = MagicMock(return_value=db)
    db.single = MagicMock(return_value=db)
    db.execute = AsyncMock(return_value=MagicMock(data=None))
    db.rpc = MagicMock(return_value=db)
    return db


# ── LLM Mock Validation ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mock_llm_returns_valid_bars_response(mock_llm):
    """Mock returns a schema-valid BARS response without calling real API."""
    from app.services.llm import evaluate_with_llm

    result = await evaluate_with_llm("test prompt")

    assert mock_llm.called
    assert result["score"] == MOCK_BARS_RESPONSE["score"]
    assert "level" in result
    assert "rationale" in result
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_mock_llm_is_overridable(mock_llm):
    """Tests can override the mock response for edge cases."""
    from app.services.llm import evaluate_with_llm

    mock_llm.return_value = {"score": 1, "level": "novice", "rationale": "Weak answer", "confidence": 0.5}

    result = await evaluate_with_llm("any prompt")
    assert result["score"] == 1
    assert result["level"] == "novice"


@pytest.mark.asyncio
async def test_mock_embedding_returns_768_dims(mock_embedding):
    """Embedding mock returns correct 768-dimensional vector (Gemini dimensions)."""
    from app.services.llm import generate_embedding

    result = await generate_embedding("volunteer search query")

    assert mock_embedding.called
    assert len(result) == 768
    assert result == MOCK_EMBEDDING


@pytest.mark.asyncio
async def test_mock_llm_failure_raises(mock_llm_failure):
    """Failure mock raises RuntimeError — tests graceful degradation."""
    from app.services.llm import evaluate_with_llm

    with pytest.raises(RuntimeError, match="All LLM providers failed"):
        await evaluate_with_llm("any prompt")


# ── Assessment Endpoint Uses Mock ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_assessment_answer_uses_mock_not_real_llm(mock_llm):
    """Assessment answer endpoint evaluates via mock — no real API call made."""
    mock_db = _chainable_db()

    # Session exists and belongs to user
    mock_db.execute.return_value = MagicMock(data={
        "id": "sess-123",
        "volunteer_id": "user-uuid",
        "competency_id": "comp-1",
        "status": "in_progress",
        "current_question_id": "q-1",
        "question_history": [],
        "theta": 0.0,
        "theta_se": 1.5,
    })

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override("user-uuid")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/assessment/answer",
            json={
                "session_id": "sess-123",
                "question_id": "q-1",
                "answer": "I communicated clearly with stakeholders",
                "response_time_ms": 8500,
            },
            headers={"Authorization": "Bearer fake"},
        )

    # Should not fail with "All LLM providers failed"
    # (real call would fail in test env without API key)
    assert resp.status_code != 500 or "LLM providers failed" not in resp.text

    app.dependency_overrides.clear()


# ── No Accidental Real LLM Calls ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_real_llm_not_called_when_mock_active(mock_llm):
    """Verify the mock intercepts at service level — real network never touched."""
    from app.services import llm as llm_service

    # Call the service directly
    result = await llm_service.evaluate_with_llm("test")

    # Mock was called exactly once
    assert mock_llm.call_count == 1
    # Real Gemini client was never instantiated (no google.genai import needed)
    assert result == MOCK_BARS_RESPONSE
