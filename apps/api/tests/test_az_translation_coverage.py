"""Coverage tests for app.services.az_translation.

Covers lines 53-84 (translate_en_to_az), 90-107 (_google_translation_llm),
112-143 (_gemini_az_translation), 161-167 (batch_translate_en_to_az).

asyncio_mode = "auto" in pyproject.toml — no @pytest.mark.asyncio needed.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.az_translation as az_mod
from app.services.az_translation import (
    _gemini_az_translation,
    _google_translation_llm,
    batch_translate_en_to_az,
    translate_en_to_az,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_AZ_TEXT = "Azerbaycan metni burada ez gu io ou uc sc bu uzun cumle saxlayir"
# Long text with enough AZ-specific chars to pass _has_az_characters
_AZ_TEXT_WITH_CHARS = "Azərbaycan mətni burada — ə ğ ı öü şç bu uzun cümlədir ki keçir"
_EN_TEXT = "This is an English sentence for testing purposes only."


def _make_settings(*, gcp: str | None = "my-gcp-proj", gemini: str | None = "gm-key") -> Any:
    s = MagicMock()
    s.gcp_project_id = gcp
    s.gemini_api_key = gemini
    return s


# ---------------------------------------------------------------------------
# GCP sys.modules injection helper
# The module uses lazy import: `from google.cloud import translate_v3`
# google-cloud-translate is NOT installed in test env, so inject via sys.modules.
# ---------------------------------------------------------------------------


@contextmanager
def _inject_gcp_module(
    translated_text: str = _AZ_TEXT_WITH_CHARS,
) -> Generator[MagicMock, None, None]:
    """Inject a fake google.cloud.translate_v3 into sys.modules."""
    translation = MagicMock()
    translation.translated_text = translated_text
    client_instance = MagicMock()
    client_instance.translate_text.return_value = MagicMock(translations=[translation])

    fake_v3 = MagicMock()
    fake_v3.TranslationServiceClient.return_value = client_instance
    fake_v3.TranslateTextRequest.side_effect = lambda **kw: kw

    # Preserve existing google / google.cloud entries
    orig_google = sys.modules.get("google")
    orig_cloud = sys.modules.get("google.cloud")
    orig_v3 = sys.modules.get("google.cloud.translate_v3")

    # Build minimal google.cloud namespace if not present
    if orig_google is None:
        google_mod = types.ModuleType("google")
        sys.modules["google"] = google_mod
    else:
        google_mod = orig_google

    if orig_cloud is None:
        cloud_mod = types.ModuleType("google.cloud")
        sys.modules["google.cloud"] = cloud_mod
    else:
        cloud_mod = orig_cloud

    sys.modules["google.cloud.translate_v3"] = fake_v3
    # Expose as attribute so `from google.cloud import translate_v3` works
    cloud_mod.translate_v3 = fake_v3  # type: ignore[attr-defined]

    try:
        yield client_instance
    finally:
        # Restore original state
        if orig_v3 is None:
            sys.modules.pop("google.cloud.translate_v3", None)
        else:
            sys.modules["google.cloud.translate_v3"] = orig_v3

        if orig_cloud is not None:
            sys.modules["google.cloud"] = orig_cloud
        elif "google.cloud" in sys.modules:
            sys.modules.pop("google.cloud", None)

        if orig_google is not None:
            sys.modules["google"] = orig_google
        elif "google" in sys.modules:
            sys.modules.pop("google", None)


# ---------------------------------------------------------------------------
# translate_en_to_az — early-return on empty/whitespace
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("", id="пустая_строка"),
        pytest.param("   ", id="только_пробелы"),
        pytest.param("\t\n", id="пробельные_символы"),
    ],
)
async def test_translate_empty_returns_unchanged(
    text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings())
    result = await translate_en_to_az(text)
    assert result == text


# ---------------------------------------------------------------------------
# translate_en_to_az — GCP happy path
# ---------------------------------------------------------------------------


async def test_translate_gcp_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """GCP returns valid AZ -> returned directly, Gemini not called."""
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp="proj-x", gemini=None))

    with _inject_gcp_module(_AZ_TEXT_WITH_CHARS), patch.object(az_mod, "_gemini_az_translation") as mock_gemini:
        result = await translate_en_to_az(_EN_TEXT)

    assert result == _AZ_TEXT_WITH_CHARS
    mock_gemini.assert_not_called()


# ---------------------------------------------------------------------------
# translate_en_to_az — GCP returns EN (no AZ chars), falls to Gemini
# ---------------------------------------------------------------------------


async def test_translate_gcp_returns_english_falls_to_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp="proj-x", gemini="gm-key"))

    en_only = "This is an English response with no AZ specific chars at all."

    with _inject_gcp_module(en_only), patch.object(
        az_mod,
        "_gemini_az_translation",
        AsyncMock(return_value=_AZ_TEXT_WITH_CHARS),
    ) as mock_gem:
        result = await translate_en_to_az(_EN_TEXT)

    assert result == _AZ_TEXT_WITH_CHARS
    mock_gem.assert_called_once_with(_EN_TEXT, None)


# ---------------------------------------------------------------------------
# translate_en_to_az — GCP raises, falls to Gemini
# ---------------------------------------------------------------------------


async def test_translate_gcp_raises_falls_to_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp="proj-x", gemini="gm-key"))

    with patch.object(
        az_mod, "_google_translation_llm", AsyncMock(side_effect=RuntimeError("gcp down"))
    ), patch.object(
        az_mod, "_gemini_az_translation", AsyncMock(return_value=_AZ_TEXT_WITH_CHARS)
    ) as mock_gem:
        result = await translate_en_to_az(_EN_TEXT)

    assert result == _AZ_TEXT_WITH_CHARS
    mock_gem.assert_called_once()


# ---------------------------------------------------------------------------
# translate_en_to_az — no GCP configured, Gemini directly
# ---------------------------------------------------------------------------


async def test_translate_no_gcp_uses_gemini_directly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))

    with patch.object(az_mod, "_google_translation_llm") as mock_gcp, patch.object(
        az_mod, "_gemini_az_translation", AsyncMock(return_value=_AZ_TEXT_WITH_CHARS)
    ):
        result = await translate_en_to_az(_EN_TEXT)

    assert result == _AZ_TEXT_WITH_CHARS
    mock_gcp.assert_not_called()


# ---------------------------------------------------------------------------
# translate_en_to_az — Gemini succeeds first attempt
# ---------------------------------------------------------------------------


async def test_translate_gemini_first_attempt_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))
    call_count = 0

    async def _once(text: str, context: str | None) -> str:
        nonlocal call_count
        call_count += 1
        return _AZ_TEXT_WITH_CHARS

    with patch.object(az_mod, "_gemini_az_translation", side_effect=_once):
        result = await translate_en_to_az(_EN_TEXT, max_retries=3)

    assert result == _AZ_TEXT_WITH_CHARS
    assert call_count == 1


# ---------------------------------------------------------------------------
# translate_en_to_az — lang-switch first attempt, success on second
# ---------------------------------------------------------------------------


async def test_translate_gemini_lang_switch_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """First attempt returns EN (lang-switch hallucination), second returns AZ."""
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))

    responses = [
        "This is still English output — language switch hallucination longer text here no AZ",
        _AZ_TEXT_WITH_CHARS,
    ]
    idx = 0

    async def _side(*_: Any) -> str:
        nonlocal idx
        r = responses[idx]
        idx += 1
        return r

    with patch.object(az_mod, "_gemini_az_translation", side_effect=_side):
        result = await translate_en_to_az(_EN_TEXT, max_retries=2)

    assert result == _AZ_TEXT_WITH_CHARS
    assert idx == 2


# ---------------------------------------------------------------------------
# translate_en_to_az — all retries fail validation -> EN fallback
# ---------------------------------------------------------------------------


async def test_translate_gemini_all_retries_fail_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))

    async def _bad(text: str, context: str | None) -> str:
        return "Still English output no AZ chars at all in this response whatsoever."

    with patch.object(az_mod, "_gemini_az_translation", side_effect=_bad):
        result = await translate_en_to_az(_EN_TEXT, max_retries=3)

    assert result == _EN_TEXT


# ---------------------------------------------------------------------------
# translate_en_to_az — Gemini raises all attempts -> EN fallback
# ---------------------------------------------------------------------------


async def test_translate_gemini_raises_all_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))

    async def _fail(*_: Any) -> str:
        raise RuntimeError("gemini unavailable")

    with patch.object(az_mod, "_gemini_az_translation", side_effect=_fail):
        result = await translate_en_to_az(_EN_TEXT, max_retries=2)

    assert result == _EN_TEXT


# ---------------------------------------------------------------------------
# translate_en_to_az — no keys at all -> immediate EN
# ---------------------------------------------------------------------------


async def test_translate_no_keys_returns_english(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini=None))
    result = await translate_en_to_az(_EN_TEXT)
    assert result == _EN_TEXT


# ---------------------------------------------------------------------------
# translate_en_to_az — context forwarded to Gemini
# ---------------------------------------------------------------------------


async def test_translate_context_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))
    ctx = "professional HR assessment question"

    with patch.object(
        az_mod, "_gemini_az_translation", AsyncMock(return_value=_AZ_TEXT_WITH_CHARS)
    ) as mock_gem:
        await translate_en_to_az(_EN_TEXT, context=ctx)

    mock_gem.assert_called_once_with(_EN_TEXT, ctx)


# ---------------------------------------------------------------------------
# _google_translation_llm — request payload structure
# ---------------------------------------------------------------------------


async def test_google_translation_llm_request_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies parent, source/target lang codes, mime_type, model suffix."""
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp="test-proj"))

    captured: list[dict] = []

    with _inject_gcp_module(_AZ_TEXT_WITH_CHARS):
        # Override TranslateTextRequest to capture kwargs
        import google.cloud.translate_v3 as fake_v3  # type: ignore[import]

        fake_v3.TranslateTextRequest.side_effect = lambda **kw: (captured.append(kw), kw)[1]
        result = await _google_translation_llm("Hello world")

    assert result == _AZ_TEXT_WITH_CHARS
    assert len(captured) == 1
    req = captured[0]
    assert req["source_language_code"] == "en"
    assert req["target_language_code"] == "az"
    assert req["mime_type"] == "text/plain"
    assert req["parent"] == "projects/test-proj/locations/global"
    assert "translation-llm" in req["model"]


async def test_google_translation_llm_uses_run_in_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """translate_text is invoked via asyncio.get_event_loop().run_in_executor."""
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp="proj-y"))

    translation = MagicMock()
    translation.translated_text = _AZ_TEXT_WITH_CHARS

    with _inject_gcp_module(_AZ_TEXT_WITH_CHARS), patch("asyncio.get_event_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(
            return_value=MagicMock(translations=[translation])
        )
        mock_get_loop.return_value = mock_loop
        await _google_translation_llm("Hello")

    mock_loop.run_in_executor.assert_called_once()
    args = mock_loop.run_in_executor.call_args[0]
    assert args[0] is None  # default executor (no custom pool)


async def test_google_translation_llm_returns_translated_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp="proj-z"))
    with _inject_gcp_module(_AZ_TEXT_WITH_CHARS):
        result = await _google_translation_llm("Test input")
    assert result == _AZ_TEXT_WITH_CHARS


# ---------------------------------------------------------------------------
# _gemini_az_translation — prompt construction
# ---------------------------------------------------------------------------


async def test_gemini_az_translation_prompt_has_critical_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gemini="gm-key"))

    captured: list[str] = []
    response = MagicMock()
    response.text = _AZ_TEXT_WITH_CHARS
    instance = MagicMock()

    async def _capture(model: str, contents: str) -> Any:
        captured.append(contents)
        return response

    instance.aio.models.generate_content = _capture

    with patch("google.genai.Client", return_value=instance):
        await _gemini_az_translation("Hello", context=None)

    assert captured
    assert "CRITICAL RULES" in captured[0]


async def test_gemini_az_translation_context_included(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gemini="gm-key"))
    captured: list[str] = []
    response = MagicMock()
    response.text = _AZ_TEXT_WITH_CHARS
    instance = MagicMock()

    async def _capture(model: str, contents: str) -> Any:
        captured.append(contents)
        return response

    instance.aio.models.generate_content = _capture

    with patch("google.genai.Client", return_value=instance):
        await _gemini_az_translation("Hello", context="HR manager context")

    assert "HR manager context" in captured[0]


async def test_gemini_az_translation_context_excluded_when_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gemini="gm-key"))
    captured: list[str] = []
    response = MagicMock()
    response.text = _AZ_TEXT_WITH_CHARS
    instance = MagicMock()

    async def _capture(model: str, contents: str) -> Any:
        captured.append(contents)
        return response

    instance.aio.models.generate_content = _capture

    with patch("google.genai.Client", return_value=instance):
        await _gemini_az_translation("Hello", context=None)

    assert "\nContext:" not in captured[0]


async def test_gemini_az_translation_strips_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model echoes prefix 'Azerbaijani translation:' -> stripped."""
    monkeypatch.setattr(az_mod, "settings", _make_settings(gemini="gm-key"))

    response = MagicMock()
    response.text = f"Azerbaijani translation: {_AZ_TEXT_WITH_CHARS}"
    instance = MagicMock()
    instance.aio.models.generate_content = AsyncMock(return_value=response)

    with patch("google.genai.Client", return_value=instance):
        result = await _gemini_az_translation("Hello", context=None)

    assert result == _AZ_TEXT_WITH_CHARS
    assert "Azerbaijani translation:" not in result


async def test_gemini_az_translation_no_prefix_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gemini="gm-key"))

    response = MagicMock()
    response.text = f"  {_AZ_TEXT_WITH_CHARS}  "
    instance = MagicMock()
    instance.aio.models.generate_content = AsyncMock(return_value=response)

    with patch("google.genai.Client", return_value=instance):
        result = await _gemini_az_translation("Hello", context=None)

    assert result == _AZ_TEXT_WITH_CHARS


async def test_gemini_az_translation_calls_correct_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gemini="gm-key"))

    response = MagicMock()
    response.text = _AZ_TEXT_WITH_CHARS
    instance = MagicMock()
    instance.aio.models.generate_content = AsyncMock(return_value=response)

    with patch("google.genai.Client", return_value=instance):
        await _gemini_az_translation("Hello", context=None)

    call_kwargs = instance.aio.models.generate_content.call_args
    model_used = call_kwargs.kwargs.get("model") or (
        call_kwargs.args[0] if call_kwargs.args else None
    )
    assert model_used == "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# batch_translate_en_to_az — size and order
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texts, expected_count",
    [
        pytest.param([], 0, id="пустой_список"),
        pytest.param(["Hello"], 1, id="один_элемент"),
        pytest.param(["Hello", "World", "Test"], 3, id="три_элемента"),
    ],
)
async def test_batch_translate_size(
    texts: list[str],
    expected_count: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))

    async def _mock(text: str, context: str | None = None, max_retries: int = 2) -> str:
        return f"az_{text}"

    with patch.object(az_mod, "translate_en_to_az", side_effect=_mock):
        results = await batch_translate_en_to_az(texts)

    assert len(results) == expected_count


async def test_batch_translate_preserves_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))
    texts = ["first", "second", "third", "fourth", "fifth"]

    async def _mock(text: str, context: str | None = None, max_retries: int = 2) -> str:
        return f"az_{text}"

    with patch.object(az_mod, "translate_en_to_az", side_effect=_mock):
        results = await batch_translate_en_to_az(texts)

    assert results == [f"az_{t}" for t in texts]


async def test_batch_translate_concurrency_semaphore(monkeypatch: pytest.MonkeyPatch) -> None:
    """Max concurrent calls must not exceed concurrency parameter."""
    import asyncio

    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))

    concurrency = 2
    active = 0
    max_active = 0

    async def _slow(text: str, context: str | None = None, max_retries: int = 2) -> str:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0)
        active -= 1
        return f"az_{text}"

    texts = ["a", "b", "c", "d", "e", "f"]
    with patch.object(az_mod, "translate_en_to_az", side_effect=_slow):
        results = await batch_translate_en_to_az(texts, concurrency=concurrency)

    assert len(results) == len(texts)
    assert max_active <= concurrency


async def test_batch_translate_context_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(az_mod, "settings", _make_settings(gcp=None, gemini="gm-key"))
    ctx = "batch context string"
    received: list[str | None] = []

    async def _mock(text: str, context: str | None = None, max_retries: int = 2) -> str:
        received.append(context)
        return _AZ_TEXT_WITH_CHARS

    with patch.object(az_mod, "translate_en_to_az", side_effect=_mock):
        await batch_translate_en_to_az(["Hello", "World"], context=ctx)

    assert all(c == ctx for c in received)
