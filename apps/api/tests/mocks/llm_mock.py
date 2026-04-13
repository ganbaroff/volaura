"""LLM mock fixtures — S3-07.

These fixtures patch the real LLM service so tests:
  1. Never call real Gemini/OpenAI APIs (no cost, no network dependency)
  2. Return deterministic, schema-valid responses
  3. Can be configured per-test for edge cases

Usage:
    from tests.mocks.llm_mock import mock_llm, mock_embedding

    async def test_something(mock_llm):  # just include the fixture
        # app.services.llm.evaluate_with_llm is now patched
        ...

    # Override response for a specific test:
    async def test_edge_case(mock_llm):
        mock_llm.return_value = {"score": 1, "level": "novice", "rationale": "..."}
        ...
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

# ── Default mock responses ─────────────────────────────────────────────────────

MOCK_BARS_RESPONSE = {
    "score": 3,
    "level": "practitioner",
    "rationale": "The answer demonstrates solid understanding of core concepts with practical examples.",
    "strengths": ["Clear structure", "Relevant examples"],
    "gaps": ["Could elaborate on edge cases"],
    "confidence": 0.85,
}

MOCK_EMBEDDING: list[float] = [0.01] * 768  # 768-dim zero vector (Gemini dimensions)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_llm():
    """Patch evaluate_with_llm to return MOCK_BARS_RESPONSE.

    Yields the AsyncMock so tests can override return_value or check call_args.
    """
    with patch(
        "app.services.llm.evaluate_with_llm",
        new_callable=AsyncMock,
        return_value=MOCK_BARS_RESPONSE,
    ) as mock:
        yield mock


@pytest.fixture
def mock_embedding():
    """Patch generate_embedding to return a 768-dim deterministic vector."""
    with patch(
        "app.services.llm.generate_embedding",
        new_callable=AsyncMock,
        return_value=MOCK_EMBEDDING,
    ) as mock:
        yield mock


@pytest.fixture
def mock_llm_failure():
    """Simulate LLM total failure — all providers unavailable.

    Use to test graceful degradation paths.
    """
    with patch(
        "app.services.llm.evaluate_with_llm",
        new_callable=AsyncMock,
        side_effect=RuntimeError("All LLM providers failed or timed out."),
    ) as mock:
        yield mock


@pytest.fixture
def mock_llm_timeout():
    """Simulate LLM timeout — tests that slow LLM doesn't block assessment."""
    import asyncio

    async def _slow(*args, **kwargs):
        await asyncio.sleep(100)  # never returns in test

    with patch("app.services.llm.evaluate_with_llm", side_effect=_slow) as mock:
        yield mock
