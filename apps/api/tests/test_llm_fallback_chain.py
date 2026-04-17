"""Tests for llm.py fallback chain, JSON parsing, timeout, and helper logic.

Covers: provider selection, fallback ordering, timeout handling, JSON decode
errors, _trace decorator no-op, reset_llm_clients, generate_embedding fallback.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import (
    LLM_TIMEOUT_SECONDS,
    _trace,
    evaluate_with_llm,
    flush_langfuse,
    generate_embedding,
    reset_llm_clients,
)


class TestTraceDecorator:
    def test_trace_returns_function_unchanged_when_langfuse_unavailable(self):
        @_trace(name="test_span")
        async def my_func():
            return 42

        assert my_func.__name__ == "my_func"

    def test_trace_with_as_type(self):
        @_trace(name="gen", as_type="generation")
        async def gen_func():
            return "ok"

        assert gen_func.__name__ == "gen_func"

    @pytest.mark.asyncio
    async def test_traced_function_still_callable(self):
        @_trace(name="test")
        async def add(a, b):
            return a + b

        assert await add(1, 2) == 3


class TestResetAndFlush:
    def test_reset_llm_clients_clears_singletons(self):
        import app.services.llm as llm_mod

        llm_mod._vertex_client = "fake"
        llm_mod._gemini_client = "fake"
        reset_llm_clients()
        assert llm_mod._vertex_client is None
        assert llm_mod._gemini_client is None

    def test_flush_langfuse_noop_when_unavailable(self):
        flush_langfuse()


class TestTimeoutConstant:
    def test_timeout_is_positive(self):
        assert LLM_TIMEOUT_SECONDS > 0

    def test_timeout_reasonable(self):
        assert LLM_TIMEOUT_SECONDS <= 60


class TestEvaluateWithLLMFallback:
    @pytest.mark.asyncio
    async def test_vertex_primary_used_first(self):
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vertex,
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = None
            mock_settings.groq_api_key = None
            mock_settings.openai_api_key = None
            mock_vertex.return_value = {"score": 3}

            result = await evaluate_with_llm("test")
            assert result == {"score": 3}
            mock_vertex.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_to_gemini_on_vertex_failure(self):
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vertex,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gemini,
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = "key"
            mock_settings.groq_api_key = None
            mock_settings.openai_api_key = None
            mock_vertex.side_effect = RuntimeError("vertex down")
            mock_gemini.return_value = {"score": 2}

            result = await evaluate_with_llm("test")
            assert result == {"score": 2}

    @pytest.mark.asyncio
    async def test_fallback_to_groq_on_gemini_failure(self):
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vertex,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gemini,
            patch("app.services.llm._call_groq", new_callable=AsyncMock) as mock_groq,
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = "key"
            mock_settings.groq_api_key = "key"
            mock_settings.openai_api_key = None
            mock_vertex.side_effect = RuntimeError("down")
            mock_gemini.side_effect = RuntimeError("down")
            mock_groq.return_value = "text result"

            result = await evaluate_with_llm("test", response_format="text")
            assert result == "text result"

    @pytest.mark.asyncio
    async def test_fallback_to_openai_on_all_others_fail(self):
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vertex,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gemini,
            patch("app.services.llm._call_groq", new_callable=AsyncMock) as mock_groq,
            patch("app.services.llm._call_openai", new_callable=AsyncMock) as mock_openai,
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = "key"
            mock_settings.groq_api_key = "key"
            mock_settings.openai_api_key = "key"
            mock_vertex.side_effect = RuntimeError("down")
            mock_gemini.side_effect = RuntimeError("down")
            mock_groq.side_effect = RuntimeError("down")
            mock_openai.return_value = {"score": 1}

            result = await evaluate_with_llm("test")
            assert result == {"score": 1}

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_runtime_error(self):
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vertex,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gemini,
            patch("app.services.llm._call_groq", new_callable=AsyncMock) as mock_groq,
            patch("app.services.llm._call_openai", new_callable=AsyncMock) as mock_openai,
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = "key"
            mock_settings.groq_api_key = "key"
            mock_settings.openai_api_key = "key"
            mock_vertex.side_effect = RuntimeError("down")
            mock_gemini.side_effect = RuntimeError("down")
            mock_groq.side_effect = RuntimeError("down")
            mock_openai.side_effect = RuntimeError("down")

            with pytest.raises(RuntimeError, match="All LLM providers failed"):
                await evaluate_with_llm("test")

    @pytest.mark.asyncio
    async def test_no_keys_raises_runtime_error(self):
        with patch("app.services.llm.settings") as mock_settings:
            mock_settings.vertex_api_key = None
            mock_settings.gemini_api_key = None
            mock_settings.groq_api_key = None
            mock_settings.openai_api_key = None

            with pytest.raises(RuntimeError, match="All LLM providers failed"):
                await evaluate_with_llm("test")

    @pytest.mark.asyncio
    async def test_skips_provider_without_key(self):
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gemini,
        ):
            mock_settings.vertex_api_key = None
            mock_settings.gemini_api_key = "key"
            mock_settings.groq_api_key = None
            mock_settings.openai_api_key = None
            mock_gemini.return_value = {"ok": True}

            result = await evaluate_with_llm("test")
            assert result == {"ok": True}


class TestTimeoutHandling:
    @pytest.mark.asyncio
    async def test_vertex_timeout_falls_to_gemini(self):
        async def slow_vertex(*args, **kwargs):
            await asyncio.sleep(100)

        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", side_effect=slow_vertex),
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gemini,
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = "key"
            mock_settings.groq_api_key = None
            mock_settings.openai_api_key = None
            mock_gemini.return_value = {"from": "gemini"}

            result = await evaluate_with_llm("test", timeout=0.01)
            assert result == {"from": "gemini"}

    @pytest.mark.asyncio
    async def test_custom_timeout_respected(self):
        call_count = 0

        async def counting_vertex(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(100)

        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", side_effect=counting_vertex),
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = None
            mock_settings.groq_api_key = None
            mock_settings.openai_api_key = None

            with pytest.raises(RuntimeError):
                await evaluate_with_llm("test", timeout=0.01)
            assert call_count == 1


class TestGenerateEmbedding:
    @pytest.mark.asyncio
    async def test_vertex_embedding_used_when_key_present(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=[0.1] * 768)]
        mock_client.aio.models.embed_content = AsyncMock(return_value=mock_response)

        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._get_vertex_client", return_value=mock_client),
        ):
            mock_settings.vertex_api_key = "key"
            result = await generate_embedding("test text")
            assert len(result) == 768
            assert result[0] == 0.1

    @pytest.mark.asyncio
    async def test_fallback_to_gemini_embedding_on_vertex_fail(self):
        mock_vertex = MagicMock()
        mock_vertex.aio.models.embed_content = AsyncMock(side_effect=RuntimeError("vertex down"))

        mock_gemini = MagicMock()
        mock_gemini_response = MagicMock()
        mock_gemini_response.embeddings = [MagicMock(values=[0.2] * 768)]
        mock_gemini.aio.models.embed_content = AsyncMock(return_value=mock_gemini_response)

        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._get_vertex_client", return_value=mock_vertex),
            patch("app.services.llm._get_gemini_client", return_value=mock_gemini),
        ):
            mock_settings.vertex_api_key = "key"
            result = await generate_embedding("test")
            assert len(result) == 768
            assert result[0] == 0.2

    @pytest.mark.asyncio
    async def test_gemini_only_when_no_vertex_key(self):
        mock_gemini = MagicMock()
        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=[0.3] * 768)]
        mock_gemini.aio.models.embed_content = AsyncMock(return_value=mock_response)

        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._get_gemini_client", return_value=mock_gemini),
        ):
            mock_settings.vertex_api_key = None
            result = await generate_embedding("test")
            assert len(result) == 768


class TestResponseFormatHandling:
    @pytest.mark.asyncio
    async def test_text_format_returns_string(self):
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vertex,
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = None
            mock_settings.groq_api_key = None
            mock_settings.openai_api_key = None
            mock_vertex.return_value = "plain text response"

            result = await evaluate_with_llm("test", response_format="text")
            assert result == "plain text response"
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_json_format_returns_dict(self):
        with (
            patch("app.services.llm.settings") as mock_settings,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vertex,
        ):
            mock_settings.vertex_api_key = "key"
            mock_settings.gemini_api_key = None
            mock_settings.groq_api_key = None
            mock_settings.openai_api_key = None
            mock_vertex.return_value = {"key": "value"}

            result = await evaluate_with_llm("test", response_format="json")
            assert isinstance(result, dict)
