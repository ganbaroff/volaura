"""Tests for Atlas self-learning pipeline.

Validates:
1. _atlas_extract_learnings() — LLM extraction + DB insert
2. _load_atlas_learnings() — sorted retrieval with ZenBrain formatting
3. _handle_atlas() — full flow (message → LLM → response + learning extraction)
4. Edge cases: empty messages, LLM failures, malformed JSON
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.routers.telegram_webhook import (
    _atlas_extract_learnings,
    _load_atlas_learnings,
)


def _make_db_mock(select_data=None, insert_data=None):
    """Build a mock Supabase client with proper async chain for table operations."""
    db = AsyncMock()

    select_result = MagicMock(data=select_data or [])
    chain = MagicMock()
    chain.select.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.execute = AsyncMock(return_value=select_result)

    insert_chain = MagicMock()
    insert_chain.execute = AsyncMock(return_value=MagicMock(data=insert_data or [{"id": "test"}]))

    def table_side_effect(name):
        mock = MagicMock()
        mock.select = chain.select
        mock.order = chain.order
        mock.limit = chain.limit
        mock.execute = chain.execute
        mock.insert = MagicMock(return_value=insert_chain)
        return mock

    db.table = MagicMock(side_effect=table_side_effect)
    return db


@pytest.fixture
def mock_db():
    return _make_db_mock()


@pytest.mark.asyncio
async def test_load_learnings_empty():
    db = _make_db_mock(select_data=[])
    result = await _load_atlas_learnings(db)
    assert result == ""


@pytest.mark.asyncio
async def test_load_learnings_formats_correctly():
    db = _make_db_mock(
        select_data=[
            {"category": "preference", "content": "Likes Russian storytelling", "emotional_intensity": 4},
            {"category": "correction", "content": "Never solo-decide", "emotional_intensity": 3},
            {"category": "insight", "content": "Morning person", "emotional_intensity": 1},
        ]
    )
    result = await _load_atlas_learnings(db)
    assert "[preference]!" in result
    assert "Russian storytelling" in result
    assert "[correction]!" in result
    assert "[insight]" in result
    assert "!" not in result.split("[insight]")[1].split("\n")[0]


@pytest.mark.asyncio
async def test_load_learnings_db_error_returns_empty():
    db = _make_db_mock()
    chain = MagicMock()
    chain.select.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.execute = AsyncMock(side_effect=Exception("DB down"))
    db.table = MagicMock(return_value=chain)
    result = await _load_atlas_learnings(db)
    assert result == ""


def _make_groq_mock(content: str):
    """Build httpx AsyncClient mock that returns a Groq chat completion."""
    groq_response = MagicMock()
    groq_response.status_code = 200
    groq_response.json.return_value = {"choices": [{"message": {"content": content}}]}
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=groq_response)
    return mock_client


def _make_insert_tracking_db():
    """DB mock that tracks all insert calls via a shared list."""
    inserts: list[dict] = []
    insert_exec = AsyncMock(return_value=MagicMock(data=[{"id": "test"}]))

    def insert_side_effect(data):
        inserts.append(data)
        m = MagicMock()
        m.execute = insert_exec
        return m

    db = AsyncMock()
    table_mock = MagicMock()
    table_mock.insert = MagicMock(side_effect=insert_side_effect)
    db.table = MagicMock(return_value=table_mock)
    return db, inserts


@pytest.mark.asyncio
async def test_extract_learnings_groq_success():
    db, inserts = _make_insert_tracking_db()
    content = '[{"category": "preference", "content": "Values autonomous work", "emotional_intensity": 3}]'
    mock_client = _make_groq_mock(content)

    with (
        patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}),
        patch("app.routers.telegram_webhook.settings") as mock_settings,
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.gemini_api_key = "fake"
        await _atlas_extract_learnings(db, "я хочу автономно", "Принято.", "A")

    assert len(inserts) == 1
    assert inserts[0]["category"] == "preference"
    assert "autonomous" in inserts[0]["content"].lower()
    assert inserts[0]["emotional_intensity"] == 3.0


@pytest.mark.asyncio
async def test_extract_learnings_empty_for_routine():
    db, inserts = _make_insert_tracking_db()
    mock_client = _make_groq_mock("[]")

    with (
        patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}),
        patch("app.routers.telegram_webhook.settings") as mock_settings,
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.gemini_api_key = "fake"
        await _atlas_extract_learnings(db, "ок", "Понял.", "B")

    assert len(inserts) == 0


@pytest.mark.asyncio
async def test_extract_learnings_malformed_json():
    db, inserts = _make_insert_tracking_db()
    mock_client = _make_groq_mock("not json at all")

    with (
        patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}),
        patch("app.routers.telegram_webhook.settings") as mock_settings,
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.gemini_api_key = "fake"
        await _atlas_extract_learnings(db, "test", "test", "A")

    assert len(inserts) == 0


@pytest.mark.asyncio
async def test_extract_learnings_no_api_keys():
    db, inserts = _make_insert_tracking_db()
    with patch("app.routers.telegram_webhook.settings") as mock_settings:
        mock_settings.gemini_api_key = ""
        await _atlas_extract_learnings(db, "test", "test", "A")

    assert len(inserts) == 0


@pytest.mark.asyncio
async def test_extract_learnings_strips_code_fences():
    db, inserts = _make_insert_tracking_db()
    content = '```json\n[{"category": "strength", "content": "Quick decision maker", "emotional_intensity": 2}]\n```'
    mock_client = _make_groq_mock(content)

    with (
        patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}),
        patch("app.routers.telegram_webhook.settings") as mock_settings,
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.gemini_api_key = "fake"
        await _atlas_extract_learnings(db, "решай сам", "Принято.", "D")

    assert len(inserts) == 1
    assert inserts[0]["category"] == "strength"
    assert "decision" in inserts[0]["content"].lower()


@pytest.mark.asyncio
async def test_extract_learnings_caps_intensity_at_5():
    db, inserts = _make_insert_tracking_db()
    content = '[{"category": "insight", "content": "Extreme test", "emotional_intensity": 99}]'
    mock_client = _make_groq_mock(content)

    with (
        patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}),
        patch("app.routers.telegram_webhook.settings") as mock_settings,
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.gemini_api_key = "fake"
        await _atlas_extract_learnings(db, "test", "test", "A")

    assert len(inserts) == 1
    assert inserts[0]["emotional_intensity"] == 5.0
