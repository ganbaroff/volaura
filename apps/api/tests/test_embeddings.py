"""Unit tests for embeddings service.

Coverage:
  1. build_profile_text — minimal profile (no bio/location)
  2. build_profile_text — full profile with AURA + competencies
  3. build_profile_text — empty profile → empty string output
  4. build_profile_text — elite_status flag included in output
  5. build_profile_text — zero-score competencies excluded
  6. generate_embedding — success → returns list of 768 floats
  7. generate_embedding — empty string → returns None immediately (no API call)
  8. generate_embedding — API failure → returns None, logs warning
  9. generate_embedding — text truncated to 8000 chars before API call
  10. upsert_volunteer_embedding — embedding generated → upsert called
  11. upsert_volunteer_embedding — embedding None → returns False, no upsert
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.embeddings import build_profile_text, generate_embedding, upsert_volunteer_embedding

# ── build_profile_text ────────────────────────────────────────────────────────


def test_build_profile_text_minimal_profile():
    profile = {"display_name": "Leyla M."}
    result = build_profile_text(profile, aura=None)
    assert "Leyla M." in result
    assert result.startswith("Name:")


def test_build_profile_text_full_profile_with_aura():
    profile = {
        "display_name": "Kamal R.",
        "bio": "UX researcher",
        "location": "Baku",
        "languages": ["az", "en"],
    }
    aura = {
        "total_score": 80.0,
        "badge_tier": "gold",
        "elite_status": False,
        "competency_scores": {"communication": 90.0, "reliability": 70.0, "leadership": 0.0},
    }
    result = build_profile_text(profile, aura)
    assert "Kamal R." in result
    assert "UX researcher" in result
    assert "Baku" in result
    assert "az, en" in result
    assert "80.0" in result
    assert "gold" in result
    assert "communication: 90" in result
    assert "reliability: 70" in result
    # zero-score competency must NOT appear
    assert "leadership" not in result


def test_build_profile_text_empty_profile():
    result = build_profile_text({}, aura=None)
    assert result == ""


def test_build_profile_text_elite_status_included():
    profile = {"display_name": "Aynur H."}
    aura = {"total_score": 92.0, "badge_tier": "platinum", "elite_status": True}
    result = build_profile_text(profile, aura)
    assert "Elite volunteer" in result


def test_build_profile_text_zero_score_competencies_excluded():
    profile = {"display_name": "Rauf B."}
    aura = {
        "total_score": 45.0,
        "badge_tier": "bronze",
        "elite_status": False,
        "competency_scores": {"communication": 0.0, "reliability": 0.0},
    }
    result = build_profile_text(profile, aura)
    assert "Competencies" not in result


# ── generate_embedding ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_embedding_empty_string_returns_none_no_api_call():
    """Empty text → None immediately without calling Gemini."""
    with patch("app.services.embeddings.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        with patch("google.genai.Client") as mock_client_cls:
            result = await generate_embedding("   ")

    assert result is None
    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_generate_embedding_success_returns_768_floats():
    fake_values = [0.1] * 768
    mock_response = MagicMock()
    mock_response.embeddings = [MagicMock(values=fake_values)]

    mock_client = MagicMock()
    mock_client.aio.models.embed_content = AsyncMock(return_value=mock_response)

    with patch("app.services.embeddings.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        with patch("google.genai.Client", return_value=mock_client):
            result = await generate_embedding("Some profile text")

    assert result is not None
    assert len(result) == 768
    assert all(isinstance(v, float) for v in result)


@pytest.mark.asyncio
async def test_generate_embedding_api_failure_returns_none():
    mock_client = MagicMock()
    mock_client.aio.models.embed_content = AsyncMock(side_effect=Exception("Gemini 503 Service Unavailable"))

    with patch("app.services.embeddings.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        with patch("google.genai.Client", return_value=mock_client):
            result = await generate_embedding("Some profile text")

    assert result is None


@pytest.mark.asyncio
async def test_generate_embedding_text_truncated_to_8000():
    """Text over 8000 chars must be truncated before API call."""
    long_text = "x" * 10_000
    captured_call: list[str] = []

    async def fake_embed(model, contents):
        captured_call.append(contents)
        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=[0.0] * 768)]
        return mock_response

    mock_client = MagicMock()
    mock_client.aio.models.embed_content = fake_embed

    with patch("app.services.embeddings.settings") as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        with patch("google.genai.Client", return_value=mock_client):
            result = await generate_embedding(long_text)

    assert result is not None
    assert len(captured_call[0]) == 8000


# ── upsert_volunteer_embedding ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_volunteer_embedding_success():
    profile = {"display_name": "Leyla M.", "bio": "Researcher"}
    aura = {"total_score": 72.0, "badge_tier": "silver", "elite_status": False}

    fake_embedding = [0.5] * 768

    mock_db = MagicMock()
    mock_db.table.return_value.upsert.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[{"volunteer_id": "uid-1"}])
    )

    with patch("app.services.embeddings.generate_embedding", new_callable=AsyncMock, return_value=fake_embedding):
        result = await upsert_volunteer_embedding(mock_db, "uid-1", profile, aura)

    assert result is True
    mock_db.table.assert_called_with("volunteer_embeddings")


@pytest.mark.asyncio
async def test_upsert_volunteer_embedding_no_embedding_returns_false():
    """If generate_embedding returns None (API fail) → no upsert, return False."""
    mock_db = MagicMock()

    with patch("app.services.embeddings.generate_embedding", new_callable=AsyncMock, return_value=None):
        result = await upsert_volunteer_embedding(mock_db, "uid-1", {}, None)

    assert result is False
    mock_db.table.assert_not_called()
