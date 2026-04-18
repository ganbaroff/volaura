"""Unit tests for app.services.telegram_llm.generate_atlas_response.

Covers:
- Each provider succeeds in isolation
- Fallback chain ordering
- All providers fail → default Russian message
- Key-absent skipping
- HTTP non-200 → warning + continue
- httpx exceptions → continue
- Gemini exception → continue
- Empty/whitespace response treated as failure
- Vertex empty candidates → failure
- System prompt truncation (NVIDIA [:4000], Groq [:3000])
- First provider succeeds → later providers never called
"""

from __future__ import annotations

import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.telegram_llm import generate_atlas_response

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SYSTEM = "You are Atlas."
USER = "Hello Atlas."
DEFAULT_REPLY = "Все провайдеры недоступны. Сообщение сохранено."


def _http_response(status: int, body: dict) -> MagicMock:
    """Fake httpx.Response with .status_code and .json()."""
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = body
    mock.text = str(body)
    return mock


def _vertex_ok(text: str = "vertex reply") -> MagicMock:
    return _http_response(
        200,
        {"candidates": [{"content": {"parts": [{"text": text}]}}]},
    )


def _openrouter_ok(text: str = "openrouter reply") -> MagicMock:
    return _http_response(200, {"choices": [{"message": {"content": text}}]})


def _nvidia_ok(text: str = "nvidia reply") -> MagicMock:
    return _http_response(200, {"choices": [{"message": {"content": text}}]})


def _groq_ok(text: str = "groq reply") -> MagicMock:
    return _http_response(200, {"choices": [{"message": {"content": text}}]})


def _error_response(status: int = 500) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {}
    mock.text = "error"
    return mock


def _mock_gemini_client(text: str = "gemini reply") -> MagicMock:
    """Build a mock google.genai module + Client that returns text."""
    genai = MagicMock()
    client_instance = MagicMock()
    response = MagicMock()
    response.text = text
    client_instance.models.generate_content.return_value = response
    genai.Client.return_value = client_instance
    genai.types = MagicMock()
    genai.types.GenerateContentConfig = MagicMock(return_value=MagicMock())
    return genai


def _patch_genai(genai_mock):
    """Patch sys.modules so `from google import genai` resolves to genai_mock.

    telegram_llm.py does `from google import genai` at runtime inside the
    function body.  Python resolves that by looking up ``google`` in
    sys.modules and then reading its ``genai`` attribute.  When google-genai
    is NOT installed neither ``google`` nor ``google.genai`` exist in
    sys.modules, so ``_patch_genai(...)`` raises AttributeError.

    This helper injects a minimal ``google`` namespace module (with
    ``.genai`` set to *genai_mock*) plus the ``google.genai`` entry so both
    lookup paths work regardless of whether the real package is installed.
    """
    google_ns = types.ModuleType("google")
    google_ns.genai = genai_mock
    return patch.dict(sys.modules, {"google": google_ns, "google.genai": genai_mock})


def _patch_httpx(post_side_effect=None, post_return_value=None):
    """Context manager that patches httpx.AsyncClient used as async context manager."""
    mock_hc = AsyncMock()
    if post_side_effect is not None:
        mock_hc.post = AsyncMock(side_effect=post_side_effect)
    else:
        mock_hc.post = AsyncMock(return_value=post_return_value)
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_hc)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return patch("httpx.AsyncClient", return_value=mock_ctx), mock_hc


# ---------------------------------------------------------------------------
# 1. Each provider succeeds in isolation
# ---------------------------------------------------------------------------


class TestEachProviderSucceedsInIsolation:
    @pytest.mark.asyncio
    async def test_vertex_only(self):
        p, mock_hc = _patch_httpx(post_return_value=_vertex_ok("hello from vertex"))
        with p, _patch_genai(_mock_gemini_client()):
            reply, provider = await generate_atlas_response(SYSTEM, USER, vertex_key="v_key")
        assert reply == "hello from vertex"
        assert provider == "vertex"

    @pytest.mark.asyncio
    async def test_openrouter_only(self):
        p, mock_hc = _patch_httpx(post_return_value=_openrouter_ok("hello from openrouter"))
        # No vertex_key so vertex skipped; gemini is always tried — make it fail
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("gemini down")
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, openrouter_key="or_key")
        assert reply == "hello from openrouter"
        assert provider == "openrouter"

    @pytest.mark.asyncio
    async def test_gemini_only(self):
        genai_mock = _mock_gemini_client("hello from gemini")
        with _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, gemini_key="gm_key")
        assert reply == "hello from gemini"
        assert provider == "gemini"

    @pytest.mark.asyncio
    async def test_nvidia_only(self):
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("gemini down")
        p, mock_hc = _patch_httpx(post_return_value=_nvidia_ok("hello from nvidia"))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, nvidia_key="nv_key")
        assert reply == "hello from nvidia"
        assert provider == "nvidia"

    @pytest.mark.asyncio
    async def test_groq_only(self):
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("gemini down")
        p, mock_hc = _patch_httpx(post_return_value=_groq_ok("hello from groq"))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, groq_key="gr_key")
        assert reply == "hello from groq"
        assert provider == "groq"


# ---------------------------------------------------------------------------
# 2. Fallback chains
# ---------------------------------------------------------------------------


class TestFallbackChains:
    @pytest.mark.asyncio
    async def test_vertex_non200_falls_to_openrouter(self):
        """Vertex returns 500 → openrouter responds 200."""
        responses = [_error_response(500), _openrouter_ok("openrouter won")]
        call_count = 0

        async def sequential_post(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        genai_mock = _mock_gemini_client()
        # Gemini would be tried after openrouter; make it fail so it doesn't interfere
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("should not be reached")
        p, _ = _patch_httpx(post_side_effect=sequential_post)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, vertex_key="v_key", openrouter_key="or_key")
        assert reply == "openrouter won"
        assert provider == "openrouter"

    @pytest.mark.asyncio
    async def test_vertex_and_openrouter_fail_gemini_succeeds(self):
        """Vertex 500, openrouter 503 → gemini returns text."""
        responses = [_error_response(500), _error_response(503)]
        call_count = 0

        async def sequential_post(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        genai_mock = _mock_gemini_client("gemini fallback")
        p, _ = _patch_httpx(post_side_effect=sequential_post)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(
                SYSTEM,
                USER,
                vertex_key="v_key",
                openrouter_key="or_key",
                gemini_key="gm_key",
            )
        assert reply == "gemini fallback"
        assert provider == "gemini"

    @pytest.mark.asyncio
    async def test_all_http_providers_fail_groq_succeeds(self):
        """vertex + openrouter + nvidia all 500, gemini raises, groq succeeds."""
        responses = [_error_response(500), _error_response(500), _error_response(500), _groq_ok("groq saved the day")]
        call_count = 0

        async def sequential_post(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("gemini down")
        p, _ = _patch_httpx(post_side_effect=sequential_post)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(
                SYSTEM,
                USER,
                vertex_key="v_key",
                openrouter_key="or_key",
                nvidia_key="nv_key",
                groq_key="gr_key",
            )
        assert reply == "groq saved the day"
        assert provider == "groq"


# ---------------------------------------------------------------------------
# 3. All providers fail
# ---------------------------------------------------------------------------


class TestAllProvidersFail:
    @pytest.mark.asyncio
    async def test_all_fail_returns_default_russian_message(self):
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("down")
        p, mock_hc = _patch_httpx(post_return_value=_error_response(500))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(
                SYSTEM,
                USER,
                vertex_key="v_key",
                openrouter_key="or_key",
                nvidia_key="nv_key",
                groq_key="gr_key",
            )
        assert reply == DEFAULT_REPLY
        assert provider == "none"

    @pytest.mark.asyncio
    async def test_no_keys_returns_default(self):
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("down")
        with _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER)
        assert reply == DEFAULT_REPLY
        assert provider == "none"


# ---------------------------------------------------------------------------
# 4. Key-absent skipping
# ---------------------------------------------------------------------------


class TestKeyAbsentSkipping:
    @pytest.mark.asyncio
    async def test_only_nvidia_key_skips_vertex_openrouter_gemini(self):
        """When only nvidia_key given: vertex/openrouter skipped (no key),
        gemini always runs but fails, nvidia succeeds."""
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("gemini down")
        p, mock_hc = _patch_httpx(post_return_value=_nvidia_ok("nvidia only"))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, nvidia_key="nv_key")
        assert reply == "nvidia only"
        assert provider == "nvidia"
        # Only one HTTP call should have been made (to NVIDIA, not vertex/openrouter)
        assert mock_hc.post.call_count == 1
        called_url = mock_hc.post.call_args[0][0]
        assert "nvidia" in called_url

    @pytest.mark.asyncio
    async def test_vertex_key_absent_skips_vertex(self):
        """No vertex_key → vertex block not entered. openrouter succeeds."""
        # Gemini block always runs; make it fail first, then openrouter win
        # But openrouter runs BEFORE gemini — so we need:
        # no vertex key → skip vertex, hit openrouter
        p, mock_hc = _patch_httpx(post_return_value=_openrouter_ok("or reply"))
        genai_mock = _mock_gemini_client()
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, openrouter_key="or_key")
        assert reply == "or reply"
        assert provider == "openrouter"
        # vertex must not have been called (only one HTTP call to openrouter)
        assert mock_hc.post.call_count == 1
        called_url = mock_hc.post.call_args[0][0]
        assert "openrouter" in called_url


# ---------------------------------------------------------------------------
# 5. HTTP non-200 → log warning, continue
# ---------------------------------------------------------------------------


class TestNon200Handling:
    @pytest.mark.asyncio
    async def test_vertex_404_logs_warning_and_continues(self):
        genai_mock = _mock_gemini_client("gemini fallback")
        p, mock_hc = _patch_httpx(post_return_value=_error_response(404))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, vertex_key="v_key", gemini_key="gm_key")
        assert provider == "gemini"

    @pytest.mark.asyncio
    async def test_openrouter_401_continues_to_gemini(self):
        genai_mock = _mock_gemini_client("gemini response")
        p, mock_hc = _patch_httpx(post_return_value=_error_response(401))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, openrouter_key="or_key", gemini_key="gm_key")
        assert provider == "gemini"


# ---------------------------------------------------------------------------
# 6. httpx exceptions → continues
# ---------------------------------------------------------------------------


class TestHttpxExceptions:
    @pytest.mark.asyncio
    async def test_vertex_timeout_continues_to_openrouter(self):
        responses = iter(
            [
                httpx.TimeoutException("timed out"),  # vertex
                _openrouter_ok("openrouter after timeout"),  # openrouter
            ]
        )

        async def raise_or_return(*args, **kwargs):
            val = next(responses)
            if isinstance(val, Exception):
                raise val
            return val

        genai_mock = _mock_gemini_client()
        p, _ = _patch_httpx(post_side_effect=raise_or_return)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, vertex_key="v_key", openrouter_key="or_key")
        assert reply == "openrouter after timeout"
        assert provider == "openrouter"

    @pytest.mark.asyncio
    async def test_connect_error_on_nvidia_continues_to_groq(self):
        responses = iter(
            [
                httpx.ConnectError("connection refused"),  # nvidia
                _groq_ok("groq after connect error"),  # groq
            ]
        )

        async def raise_or_return(*args, **kwargs):
            val = next(responses)
            if isinstance(val, Exception):
                raise val
            return val

        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("gemini down")
        p, _ = _patch_httpx(post_side_effect=raise_or_return)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, nvidia_key="nv_key", groq_key="gr_key")
        assert reply == "groq after connect error"
        assert provider == "groq"


# ---------------------------------------------------------------------------
# 7. Gemini exception → continues
# ---------------------------------------------------------------------------


class TestGeminiException:
    @pytest.mark.asyncio
    async def test_gemini_exception_continues_to_nvidia(self):
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = ValueError("invalid api key")
        p, mock_hc = _patch_httpx(post_return_value=_nvidia_ok("nvidia after gemini fail"))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, gemini_key="gm_key", nvidia_key="nv_key")
        assert reply == "nvidia after gemini fail"
        assert provider == "nvidia"

    @pytest.mark.asyncio
    async def test_gemini_exception_continues_to_groq_when_no_nvidia(self):
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("quota exceeded")
        p, mock_hc = _patch_httpx(post_return_value=_groq_ok("groq after gemini fail"))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, gemini_key="gm_key", groq_key="gr_key")
        assert reply == "groq after gemini fail"
        assert provider == "groq"


# ---------------------------------------------------------------------------
# 8. Empty/whitespace response treated as failure
# ---------------------------------------------------------------------------


class TestEmptyResponseHandling:
    @pytest.mark.asyncio
    async def test_vertex_empty_text_falls_through(self):
        """Vertex returns 200 but empty text → treated as failure → falls to openrouter."""
        responses = [
            _vertex_ok(""),  # vertex: empty after strip
            _openrouter_ok("openrouter wins"),
        ]
        call_count = 0

        async def sequential_post(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        genai_mock = _mock_gemini_client()
        p, _ = _patch_httpx(post_side_effect=sequential_post)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, vertex_key="v_key", openrouter_key="or_key")
        assert reply == "openrouter wins"
        assert provider == "openrouter"

    @pytest.mark.asyncio
    async def test_openrouter_whitespace_only_falls_through(self):
        """OpenRouter returns 200 but whitespace content → falls to gemini."""
        responses = [_openrouter_ok("   ")]
        call_count = 0

        async def sequential_post(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        genai_mock = _mock_gemini_client("gemini wins after whitespace")
        p, _ = _patch_httpx(post_side_effect=sequential_post)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, openrouter_key="or_key", gemini_key="gm_key")
        assert reply == "gemini wins after whitespace"
        assert provider == "gemini"

    @pytest.mark.asyncio
    async def test_gemini_empty_text_falls_through(self):
        """Gemini returns empty string → continues to nvidia."""
        genai_mock = _mock_gemini_client("")
        p, mock_hc = _patch_httpx(post_return_value=_nvidia_ok("nvidia wins"))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, gemini_key="gm_key", nvidia_key="nv_key")
        assert reply == "nvidia wins"
        assert provider == "nvidia"


# ---------------------------------------------------------------------------
# 9. Vertex empty candidates list
# ---------------------------------------------------------------------------


class TestVertexEdgeCases:
    @pytest.mark.asyncio
    async def test_vertex_empty_candidates_list_falls_through(self):
        """candidates: [] → no text extracted → treated as empty → falls to openrouter."""
        vertex_empty = _http_response(200, {"candidates": []})
        responses = [vertex_empty, _openrouter_ok("openrouter after empty candidates")]
        call_count = 0

        async def sequential_post(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        genai_mock = _mock_gemini_client()
        p, _ = _patch_httpx(post_side_effect=sequential_post)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, vertex_key="v_key", openrouter_key="or_key")
        assert reply == "openrouter after empty candidates"
        assert provider == "openrouter"

    @pytest.mark.asyncio
    async def test_vertex_missing_text_field_falls_through(self):
        """parts[0] exists but no 'text' key → empty string → falls through."""
        vertex_no_text = _http_response(200, {"candidates": [{"content": {"parts": [{}]}}]})
        responses = [vertex_no_text, _openrouter_ok("openrouter fallback")]
        call_count = 0

        async def sequential_post(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        genai_mock = _mock_gemini_client()
        p, _ = _patch_httpx(post_side_effect=sequential_post)
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(SYSTEM, USER, vertex_key="v_key", openrouter_key="or_key")
        assert reply == "openrouter fallback"
        assert provider == "openrouter"


# ---------------------------------------------------------------------------
# 10. System prompt truncation
# ---------------------------------------------------------------------------


class TestSystemPromptTruncation:
    @pytest.mark.asyncio
    async def test_nvidia_receives_system_prompt_truncated_to_4000(self):
        long_system = "A" * 6000
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("gemini down")
        p, mock_hc = _patch_httpx(post_return_value=_nvidia_ok("nvidia reply"))
        with p, _patch_genai(genai_mock):
            await generate_atlas_response(long_system, USER, nvidia_key="nv_key")

        # Find the call to the NVIDIA endpoint
        nvidia_call = None
        for call in mock_hc.post.call_args_list:
            if "nvidia" in call[0][0]:
                nvidia_call = call
                break
        assert nvidia_call is not None, "NVIDIA endpoint was not called"
        payload = nvidia_call[1]["json"]
        system_msg = next(m for m in payload["messages"] if m["role"] == "system")
        assert len(system_msg["content"]) == 4000
        assert system_msg["content"] == "A" * 4000

    @pytest.mark.asyncio
    async def test_groq_receives_system_prompt_truncated_to_3000(self):
        long_system = "B" * 5000
        genai_mock = _mock_gemini_client()
        genai_mock.Client.return_value.models.generate_content.side_effect = RuntimeError("gemini down")
        p, mock_hc = _patch_httpx(post_return_value=_groq_ok("groq reply"))
        with p, _patch_genai(genai_mock):
            await generate_atlas_response(long_system, USER, groq_key="gr_key")

        groq_call = None
        for call in mock_hc.post.call_args_list:
            if "groq" in call[0][0]:
                groq_call = call
                break
        assert groq_call is not None, "Groq endpoint was not called"
        payload = groq_call[1]["json"]
        system_msg = next(m for m in payload["messages"] if m["role"] == "system")
        assert len(system_msg["content"]) == 3000
        assert system_msg["content"] == "B" * 3000

    @pytest.mark.asyncio
    async def test_vertex_sends_full_system_prompt(self):
        """Vertex does not truncate system_instruction."""
        long_system = "C" * 6000
        p, mock_hc = _patch_httpx(post_return_value=_vertex_ok("vertex reply"))
        genai_mock = _mock_gemini_client()
        with p, _patch_genai(genai_mock):
            await generate_atlas_response(long_system, USER, vertex_key="v_key")

        vertex_call = mock_hc.post.call_args_list[0]
        payload = vertex_call[1]["json"]
        si_text = payload["system_instruction"]["parts"][0]["text"]
        assert si_text == long_system  # no truncation

    @pytest.mark.asyncio
    async def test_openrouter_sends_full_system_prompt(self):
        """OpenRouter does not truncate system message."""
        long_system = "D" * 5000
        p, mock_hc = _patch_httpx(post_return_value=_openrouter_ok("openrouter reply"))
        genai_mock = _mock_gemini_client()
        with p, _patch_genai(genai_mock):
            await generate_atlas_response(long_system, USER, openrouter_key="or_key")

        or_call = mock_hc.post.call_args_list[0]
        payload = or_call[1]["json"]
        system_msg = next(m for m in payload["messages"] if m["role"] == "system")
        assert system_msg["content"] == long_system


# ---------------------------------------------------------------------------
# 11. First provider succeeds → later providers never called
# ---------------------------------------------------------------------------


class TestEarlyExitOnSuccess:
    @pytest.mark.asyncio
    async def test_vertex_succeeds_openrouter_never_called(self):
        p, mock_hc = _patch_httpx(post_return_value=_vertex_ok("vertex reply"))
        genai_mock = _mock_gemini_client()
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(
                SYSTEM,
                USER,
                vertex_key="v_key",
                openrouter_key="or_key",
                nvidia_key="nv_key",
                groq_key="gr_key",
            )
        assert provider == "vertex"
        # Only one HTTP call (to vertex), openrouter/nvidia/groq never hit
        assert mock_hc.post.call_count == 1

    @pytest.mark.asyncio
    async def test_openrouter_succeeds_nvidia_and_groq_never_called(self):
        p, mock_hc = _patch_httpx(post_return_value=_openrouter_ok("openrouter reply"))
        genai_mock = _mock_gemini_client()
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(
                SYSTEM,
                USER,
                openrouter_key="or_key",
                nvidia_key="nv_key",
                groq_key="gr_key",
            )
        assert provider == "openrouter"
        # Only one HTTP call to openrouter
        assert mock_hc.post.call_count == 1
        called_url = mock_hc.post.call_args[0][0]
        assert "openrouter" in called_url

    @pytest.mark.asyncio
    async def test_gemini_succeeds_nvidia_and_groq_never_called(self):
        genai_mock = _mock_gemini_client("gemini reply")
        p, mock_hc = _patch_httpx(post_return_value=_nvidia_ok("should not be called"))
        with p, _patch_genai(genai_mock):
            reply, provider = await generate_atlas_response(
                SYSTEM,
                USER,
                gemini_key="gm_key",
                nvidia_key="nv_key",
                groq_key="gr_key",
            )
        assert provider == "gemini"
        assert mock_hc.post.call_count == 0
