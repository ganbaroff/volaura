"""Unit tests for app.services.llm — provider-level behaviour.

Complements test_llm_fallback_chain.py (which covers evaluate_with_llm dispatch)
by going one layer deeper:

- _call_vertex / _call_gemini / _call_groq / _call_openai JSON & text modes
- Invalid JSON → {} fallback per provider
- Empty choices guard for Groq and OpenAI
- Singleton client lazy-init and reset_llm_clients()
- generate_embedding — Vertex primary, Gemini fallback, no-Vertex path
- _update_trace_metadata — no-op when langfuse unavailable
- _trace decorator — no-op identity when langfuse unavailable
- flush_langfuse — no-op when langfuse unavailable
- Timeout on all four providers falls through to next
- All providers absent → RuntimeError

Mocking strategy
----------------
google.genai, groq, openai are injected via sys.modules to avoid requiring
the real packages.  Individual provider functions are patched at the
app.services.llm module boundary with AsyncMock for fast, isolated tests.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.llm as llm_mod
from app.services.llm import (
    LLM_TIMEOUT_SECONDS,
    _trace,
    _update_trace_metadata,
    evaluate_with_llm,
    flush_langfuse,
    generate_embedding,
    reset_llm_clients,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_genai_mock(text: str = '{"score": 5}', embeddings: list[float] | None = None) -> MagicMock:
    """Build a minimal google.genai stand-in that returns *text* from generate_content
    and *embeddings* from embed_content."""
    genai = MagicMock()
    client_inst = MagicMock()

    # generate_content response
    gen_response = MagicMock()
    gen_response.text = text
    client_inst.aio.models.generate_content = AsyncMock(return_value=gen_response)

    # embed_content response
    embed_vals = embeddings if embeddings is not None else [0.1] * 768
    embed_response = MagicMock()
    embed_response.embeddings = [MagicMock(values=embed_vals)]
    client_inst.aio.models.embed_content = AsyncMock(return_value=embed_response)

    genai.Client.return_value = client_inst
    return genai


def _patch_genai(genai_mock: MagicMock):
    """Inject genai_mock so `from google import genai` resolves correctly."""
    google_ns = types.ModuleType("google")
    google_ns.genai = genai_mock
    return patch.dict(sys.modules, {"google": google_ns, "google.genai": genai_mock})


def _groq_mock_module(text: str = '{"score": 3}', empty_choices: bool = False) -> MagicMock:
    """Return a mock groq module whose AsyncGroq.chat.completions.create resolves."""
    groq_mod = MagicMock()
    client_inst = MagicMock()

    if empty_choices:
        choices = []
    else:
        msg = MagicMock()
        msg.content = text
        choice = MagicMock()
        choice.message = msg
        choices = [choice]

    response = MagicMock()
    response.choices = choices
    client_inst.chat.completions.create = AsyncMock(return_value=response)
    groq_mod.AsyncGroq.return_value = client_inst
    return groq_mod


def _openai_mock_module(text: str = '{"score": 2}', empty_choices: bool = False) -> MagicMock:
    """Return a mock openai module whose AsyncOpenAI.chat.completions.create resolves."""
    openai_mod = MagicMock()
    client_inst = MagicMock()

    if empty_choices:
        choices = []
    else:
        msg = MagicMock()
        msg.content = text
        choice = MagicMock()
        choice.message = msg
        choices = [choice]

    response = MagicMock()
    response.choices = choices
    client_inst.chat.completions.create = AsyncMock(return_value=response)
    openai_mod.AsyncOpenAI.return_value = client_inst
    return openai_mod


# ---------------------------------------------------------------------------
# Autouse teardown — prevent singleton pollution across tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_singletons():
    reset_llm_clients()
    yield
    reset_llm_clients()


# ---------------------------------------------------------------------------
# 1. _trace decorator
# ---------------------------------------------------------------------------


class TestTraceDecorator:
    def test_no_op_returns_original_function(self):
        @_trace(name="span")
        async def fn():
            return 99

        assert fn.__name__ == "fn"

    def test_no_op_with_as_type(self):
        @_trace(name="gen", as_type="generation")
        async def gen_fn():
            return "ok"

        assert gen_fn.__name__ == "gen_fn"

    @pytest.mark.asyncio
    async def test_decorated_function_still_executes(self):
        @_trace(name="x")
        async def add(a: int, b: int) -> int:
            return a + b

        assert await add(3, 4) == 7

    def test_no_args_decorator(self):
        @_trace()
        async def bare_fn():
            pass

        assert callable(bare_fn)


# ---------------------------------------------------------------------------
# 2. flush_langfuse + _update_trace_metadata — no-op paths
# ---------------------------------------------------------------------------


class TestLangfuseNoOp:
    def test_flush_langfuse_no_exception_when_unavailable(self):
        flush_langfuse()  # must not raise

    def test_update_trace_metadata_no_exception_when_unavailable(self):
        _update_trace_metadata(model="gemini-2.5-flash", provider="vertex-express")

    def test_update_trace_metadata_with_input_no_exception(self):
        _update_trace_metadata(
            model="gpt-4o-mini",
            provider="openai",
            input_text="hello world",
        )


# ---------------------------------------------------------------------------
# 3. reset_llm_clients + singleton lazy-init
# ---------------------------------------------------------------------------


class TestSingletonClients:
    def test_reset_clears_vertex_client(self):
        llm_mod._vertex_client = object()
        reset_llm_clients()
        assert llm_mod._vertex_client is None

    def test_reset_clears_gemini_client(self):
        llm_mod._gemini_client = object()
        reset_llm_clients()
        assert llm_mod._gemini_client is None

    def test_get_vertex_client_lazy_init(self):
        genai_mock = _make_genai_mock()
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.vertex_api_key = "vkey"
            from app.services.llm import _get_vertex_client

            reset_llm_clients()
            client = _get_vertex_client()
            assert client is not None
            # Second call returns same singleton
            assert _get_vertex_client() is client

    def test_get_gemini_client_lazy_init(self):
        genai_mock = _make_genai_mock()
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.gemini_api_key = "gkey"
            from app.services.llm import _get_gemini_client

            reset_llm_clients()
            client = _get_gemini_client()
            assert client is not None
            assert _get_gemini_client() is client

    def test_reset_then_reinit_creates_new_client(self):
        genai_mock = _make_genai_mock()
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.vertex_api_key = "vkey"
            from app.services.llm import _get_vertex_client

            reset_llm_clients()
            _get_vertex_client()
            reset_llm_clients()
            _get_vertex_client()
            # After reset a fresh Client() call must occur
            assert genai_mock.Client.call_count >= 2


# ---------------------------------------------------------------------------
# 4. _call_vertex — JSON and text modes
# ---------------------------------------------------------------------------


class TestCallVertex:
    @pytest.mark.asyncio
    async def test_json_mode_returns_parsed_dict(self):
        genai_mock = _make_genai_mock(text='{"score": 7}')
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.vertex_api_key = "vkey"
            reset_llm_clients()
            from app.services.llm import _call_vertex

            result = await _call_vertex("prompt", "json")
        assert result == {"score": 7}

    @pytest.mark.asyncio
    async def test_json_mode_invalid_json_returns_empty_dict(self):
        genai_mock = _make_genai_mock(text="not valid json {{{")
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.vertex_api_key = "vkey"
            reset_llm_clients()
            from app.services.llm import _call_vertex

            result = await _call_vertex("prompt", "json")
        assert result == {}

    @pytest.mark.asyncio
    async def test_text_mode_returns_raw_string(self):
        genai_mock = _make_genai_mock(text="raw text output")
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.vertex_api_key = "vkey"
            reset_llm_clients()
            from app.services.llm import _call_vertex

            result = await _call_vertex("prompt", "text")
        assert result == "raw text output"

    @pytest.mark.asyncio
    async def test_none_text_treated_as_empty_string_in_text_mode(self):
        genai_mock = _make_genai_mock(text=None)
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.vertex_api_key = "vkey"
            reset_llm_clients()
            from app.services.llm import _call_vertex

            result = await _call_vertex("prompt", "text")
        assert result == ""

    @pytest.mark.asyncio
    async def test_json_mode_sets_mime_type_in_config(self):
        genai_mock = _make_genai_mock(text='{"ok": true}')
        client_inst = genai_mock.Client.return_value
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.vertex_api_key = "vkey"
            reset_llm_clients()
            from app.services.llm import _call_vertex

            await _call_vertex("p", "json")
        call_kwargs = client_inst.aio.models.generate_content.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config", {})
        assert config.get("response_mime_type") == "application/json"


# ---------------------------------------------------------------------------
# 5. _call_gemini — JSON and text modes
# ---------------------------------------------------------------------------


class TestCallGemini:
    @pytest.mark.asyncio
    async def test_json_mode_returns_parsed_dict(self):
        genai_mock = _make_genai_mock(text='{"level": "gold"}')
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.gemini_api_key = "gkey"
            reset_llm_clients()
            from app.services.llm import _call_gemini

            result = await _call_gemini("prompt", "json")
        assert result == {"level": "gold"}

    @pytest.mark.asyncio
    async def test_json_mode_invalid_json_returns_empty_dict(self):
        genai_mock = _make_genai_mock(text="[broken")
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.gemini_api_key = "gkey"
            reset_llm_clients()
            from app.services.llm import _call_gemini

            result = await _call_gemini("prompt", "json")
        assert result == {}

    @pytest.mark.asyncio
    async def test_text_mode_returns_raw_string(self):
        genai_mock = _make_genai_mock(text="gemini prose")
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.gemini_api_key = "gkey"
            reset_llm_clients()
            from app.services.llm import _call_gemini

            result = await _call_gemini("prompt", "text")
        assert result == "gemini prose"

    @pytest.mark.asyncio
    async def test_none_text_returns_empty_string_in_json_mode(self):
        """response.text = None → empty string → JSONDecodeError → {}."""
        genai_mock = _make_genai_mock(text=None)
        with _patch_genai(genai_mock), patch("app.services.llm.settings") as s:
            s.gemini_api_key = "gkey"
            reset_llm_clients()
            from app.services.llm import _call_gemini

            result = await _call_gemini("p", "json")
        assert result == {}


# ---------------------------------------------------------------------------
# 6. _call_groq — JSON, text, empty choices
# ---------------------------------------------------------------------------


class TestCallGroq:
    @pytest.mark.asyncio
    async def test_json_mode_returns_parsed_dict(self):
        groq_mod = _groq_mock_module(text='{"score": 4}')
        with patch.dict(sys.modules, {"groq": groq_mod}), patch("app.services.llm.settings") as s:
            s.groq_api_key = "grkey"
            from app.services.llm import _call_groq

            result = await _call_groq("prompt", "json")
        assert result == {"score": 4}

    @pytest.mark.asyncio
    async def test_json_mode_invalid_json_returns_empty_dict(self):
        groq_mod = _groq_mock_module(text="oops not json")
        with patch.dict(sys.modules, {"groq": groq_mod}), patch("app.services.llm.settings") as s:
            s.groq_api_key = "grkey"
            from app.services.llm import _call_groq

            result = await _call_groq("prompt", "json")
        assert result == {}

    @pytest.mark.asyncio
    async def test_text_mode_returns_raw_string(self):
        groq_mod = _groq_mock_module(text="groq text answer")
        with patch.dict(sys.modules, {"groq": groq_mod}), patch("app.services.llm.settings") as s:
            s.groq_api_key = "grkey"
            from app.services.llm import _call_groq

            result = await _call_groq("prompt", "text")
        assert result == "groq text answer"

    @pytest.mark.asyncio
    async def test_empty_choices_raises_runtime_error(self):
        groq_mod = _groq_mock_module(empty_choices=True)
        with patch.dict(sys.modules, {"groq": groq_mod}), patch("app.services.llm.settings") as s:
            s.groq_api_key = "grkey"
            from app.services.llm import _call_groq

            with pytest.raises(RuntimeError, match="empty choices"):
                await _call_groq("prompt", "json")

    @pytest.mark.asyncio
    async def test_json_format_kwarg_passed_to_groq(self):
        groq_mod = _groq_mock_module(text='{"x": 1}')
        client_inst = groq_mod.AsyncGroq.return_value
        with patch.dict(sys.modules, {"groq": groq_mod}), patch("app.services.llm.settings") as s:
            s.groq_api_key = "grkey"
            from app.services.llm import _call_groq

            await _call_groq("p", "json")
        call_kwargs = client_inst.chat.completions.create.call_args.kwargs
        assert call_kwargs.get("response_format") == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_text_format_no_response_format_kwarg(self):
        groq_mod = _groq_mock_module(text="plain")
        client_inst = groq_mod.AsyncGroq.return_value
        with patch.dict(sys.modules, {"groq": groq_mod}), patch("app.services.llm.settings") as s:
            s.groq_api_key = "grkey"
            from app.services.llm import _call_groq

            await _call_groq("p", "text")
        call_kwargs = client_inst.chat.completions.create.call_args.kwargs
        assert "response_format" not in call_kwargs


# ---------------------------------------------------------------------------
# 7. _call_openai — JSON, text, empty choices
# ---------------------------------------------------------------------------


class TestCallOpenAI:
    @pytest.mark.asyncio
    async def test_json_mode_returns_parsed_dict(self):
        openai_mod = _openai_mock_module(text='{"verdict": "pass"}')
        with patch.dict(sys.modules, {"openai": openai_mod}), patch("app.services.llm.settings") as s:
            s.openai_api_key = "okey"
            from app.services.llm import _call_openai

            result = await _call_openai("prompt", "json")
        assert result == {"verdict": "pass"}

    @pytest.mark.asyncio
    async def test_json_mode_invalid_json_returns_empty_dict(self):
        openai_mod = _openai_mock_module(text="```json{broken}")
        with patch.dict(sys.modules, {"openai": openai_mod}), patch("app.services.llm.settings") as s:
            s.openai_api_key = "okey"
            from app.services.llm import _call_openai

            result = await _call_openai("prompt", "json")
        assert result == {}

    @pytest.mark.asyncio
    async def test_text_mode_returns_raw_string(self):
        openai_mod = _openai_mock_module(text="openai text result")
        with patch.dict(sys.modules, {"openai": openai_mod}), patch("app.services.llm.settings") as s:
            s.openai_api_key = "okey"
            from app.services.llm import _call_openai

            result = await _call_openai("prompt", "text")
        assert result == "openai text result"

    @pytest.mark.asyncio
    async def test_empty_choices_raises_runtime_error(self):
        openai_mod = _openai_mock_module(empty_choices=True)
        with patch.dict(sys.modules, {"openai": openai_mod}), patch("app.services.llm.settings") as s:
            s.openai_api_key = "okey"
            from app.services.llm import _call_openai

            with pytest.raises(RuntimeError, match="empty response"):
                await _call_openai("prompt", "json")

    @pytest.mark.asyncio
    async def test_json_format_kwarg_passed_to_openai(self):
        openai_mod = _openai_mock_module(text='{"y": 2}')
        client_inst = openai_mod.AsyncOpenAI.return_value
        with patch.dict(sys.modules, {"openai": openai_mod}), patch("app.services.llm.settings") as s:
            s.openai_api_key = "okey"
            from app.services.llm import _call_openai

            await _call_openai("p", "json")
        call_kwargs = client_inst.chat.completions.create.call_args.kwargs
        assert call_kwargs.get("response_format") == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_text_format_no_response_format_kwarg(self):
        openai_mod = _openai_mock_module(text="text")
        client_inst = openai_mod.AsyncOpenAI.return_value
        with patch.dict(sys.modules, {"openai": openai_mod}), patch("app.services.llm.settings") as s:
            s.openai_api_key = "okey"
            from app.services.llm import _call_openai

            await _call_openai("p", "text")
        call_kwargs = client_inst.chat.completions.create.call_args.kwargs
        assert "response_format" not in call_kwargs


# ---------------------------------------------------------------------------
# 8. evaluate_with_llm — timeout triggers fallback
# ---------------------------------------------------------------------------


class TestEvaluateWithLLMTimeout:
    @pytest.mark.asyncio
    async def test_vertex_timeout_falls_through_to_gemini(self):
        import asyncio

        async def slow(*_):
            await asyncio.sleep(100)

        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._call_vertex", side_effect=slow),
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gem,
        ):
            s.vertex_api_key = "v"
            s.gemini_api_key = "g"
            s.groq_api_key = None
            s.openai_api_key = None
            mock_gem.return_value = {"fallback": True}

            result = await evaluate_with_llm("p", timeout=0.01)
        assert result == {"fallback": True}

    @pytest.mark.asyncio
    async def test_gemini_timeout_falls_through_to_groq(self):
        import asyncio

        async def slow(*_):
            await asyncio.sleep(100)

        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vtx,
            patch("app.services.llm._call_gemini", side_effect=slow),
            patch("app.services.llm._call_groq", new_callable=AsyncMock) as mock_groq,
        ):
            s.vertex_api_key = "v"
            s.gemini_api_key = "g"
            s.groq_api_key = "gr"
            s.openai_api_key = None
            mock_vtx.side_effect = RuntimeError("vertex down")
            mock_groq.return_value = {"from": "groq"}

            result = await evaluate_with_llm("p", timeout=0.01)
        assert result == {"from": "groq"}

    @pytest.mark.asyncio
    async def test_all_timeout_raises_runtime_error(self):
        import asyncio

        async def slow(*_):
            await asyncio.sleep(100)

        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._call_vertex", side_effect=slow),
        ):
            s.vertex_api_key = "v"
            s.gemini_api_key = None
            s.groq_api_key = None
            s.openai_api_key = None

            with pytest.raises(RuntimeError, match="All LLM providers failed"):
                await evaluate_with_llm("p", timeout=0.01)


# ---------------------------------------------------------------------------
# 9. evaluate_with_llm — provider key absent skips provider
# ---------------------------------------------------------------------------


class TestProviderKeyAbsent:
    @pytest.mark.asyncio
    async def test_vertex_skipped_when_no_key(self):
        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vtx,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gem,
        ):
            s.vertex_api_key = None
            s.gemini_api_key = "g"
            s.groq_api_key = None
            s.openai_api_key = None
            mock_gem.return_value = {"ok": 1}

            result = await evaluate_with_llm("p")
        mock_vtx.assert_not_called()
        assert result == {"ok": 1}

    @pytest.mark.asyncio
    async def test_groq_skipped_when_no_key(self):
        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vtx,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gem,
            patch("app.services.llm._call_groq", new_callable=AsyncMock) as mock_groq,
            patch("app.services.llm._call_openai", new_callable=AsyncMock) as mock_oai,
        ):
            s.vertex_api_key = "v"
            s.gemini_api_key = "g"
            s.groq_api_key = None
            s.openai_api_key = "o"
            mock_vtx.side_effect = RuntimeError("down")
            mock_gem.side_effect = RuntimeError("down")
            mock_oai.return_value = {"final": True}

            result = await evaluate_with_llm("p")
        mock_groq.assert_not_called()
        assert result == {"final": True}

    @pytest.mark.asyncio
    async def test_openai_skipped_when_no_key(self):
        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._call_openai", new_callable=AsyncMock) as mock_oai,
        ):
            s.vertex_api_key = None
            s.gemini_api_key = None
            s.groq_api_key = None
            s.openai_api_key = None

            with pytest.raises(RuntimeError):
                await evaluate_with_llm("p")
        mock_oai.assert_not_called()


# ---------------------------------------------------------------------------
# 10. generate_embedding
# ---------------------------------------------------------------------------


class TestGenerateEmbedding:
    @pytest.mark.asyncio
    async def test_vertex_primary_returns_768_dims(self):
        mock_client = MagicMock()
        embed_resp = MagicMock()
        embed_resp.embeddings = [MagicMock(values=[0.5] * 768)]
        mock_client.aio.models.embed_content = AsyncMock(return_value=embed_resp)

        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._get_vertex_client", return_value=mock_client),
        ):
            s.vertex_api_key = "v"
            result = await generate_embedding("some text")

        assert len(result) == 768
        assert result[0] == 0.5

    @pytest.mark.asyncio
    async def test_vertex_failure_falls_to_gemini(self):
        vtx_client = MagicMock()
        vtx_client.aio.models.embed_content = AsyncMock(side_effect=RuntimeError("vertex down"))

        gem_client = MagicMock()
        embed_resp = MagicMock()
        embed_resp.embeddings = [MagicMock(values=[0.9] * 768)]
        gem_client.aio.models.embed_content = AsyncMock(return_value=embed_resp)

        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._get_vertex_client", return_value=vtx_client),
            patch("app.services.llm._get_gemini_client", return_value=gem_client),
        ):
            s.vertex_api_key = "v"
            result = await generate_embedding("text")

        assert len(result) == 768
        assert result[0] == 0.9

    @pytest.mark.asyncio
    async def test_no_vertex_key_uses_gemini_directly(self):
        gem_client = MagicMock()
        embed_resp = MagicMock()
        embed_resp.embeddings = [MagicMock(values=[0.3] * 768)]
        gem_client.aio.models.embed_content = AsyncMock(return_value=embed_resp)

        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._get_gemini_client", return_value=gem_client),
        ):
            s.vertex_api_key = None
            result = await generate_embedding("query")

        assert len(result) == 768
        gem_client.aio.models.embed_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_text_embedding_004_model(self):
        gem_client = MagicMock()
        embed_resp = MagicMock()
        embed_resp.embeddings = [MagicMock(values=[0.1] * 768)]
        gem_client.aio.models.embed_content = AsyncMock(return_value=embed_resp)

        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._get_gemini_client", return_value=gem_client),
        ):
            s.vertex_api_key = None
            await generate_embedding("hello")

        call_kwargs = gem_client.aio.models.embed_content.call_args.kwargs
        assert call_kwargs.get("model") == "text-embedding-004"

    @pytest.mark.asyncio
    async def test_vertex_embedding_uses_text_embedding_004_model(self):
        vtx_client = MagicMock()
        embed_resp = MagicMock()
        embed_resp.embeddings = [MagicMock(values=[0.1] * 768)]
        vtx_client.aio.models.embed_content = AsyncMock(return_value=embed_resp)

        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._get_vertex_client", return_value=vtx_client),
        ):
            s.vertex_api_key = "v"
            await generate_embedding("embed this")

        call_kwargs = vtx_client.aio.models.embed_content.call_args.kwargs
        assert call_kwargs.get("model") == "text-embedding-004"


# ---------------------------------------------------------------------------
# 11. LLM_TIMEOUT_SECONDS constant
# ---------------------------------------------------------------------------


class TestTimeoutConstant:
    def test_timeout_is_positive(self):
        assert LLM_TIMEOUT_SECONDS > 0

    def test_timeout_at_most_60_seconds(self):
        assert LLM_TIMEOUT_SECONDS <= 60

    def test_timeout_is_numeric(self):
        assert isinstance(LLM_TIMEOUT_SECONDS, (int, float))


# ---------------------------------------------------------------------------
# 12. evaluate_with_llm — first successful provider short-circuits chain
# ---------------------------------------------------------------------------


class TestEarlyExit:
    @pytest.mark.asyncio
    async def test_vertex_success_skips_gemini_groq_openai(self):
        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vtx,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gem,
            patch("app.services.llm._call_groq", new_callable=AsyncMock) as mock_groq,
            patch("app.services.llm._call_openai", new_callable=AsyncMock) as mock_oai,
        ):
            s.vertex_api_key = "v"
            s.gemini_api_key = "g"
            s.groq_api_key = "gr"
            s.openai_api_key = "o"
            mock_vtx.return_value = {"winner": "vertex"}

            result = await evaluate_with_llm("p")

        assert result == {"winner": "vertex"}
        mock_gem.assert_not_called()
        mock_groq.assert_not_called()
        mock_oai.assert_not_called()

    @pytest.mark.asyncio
    async def test_groq_success_skips_openai(self):
        with (
            patch("app.services.llm.settings") as s,
            patch("app.services.llm._call_vertex", new_callable=AsyncMock) as mock_vtx,
            patch("app.services.llm._call_gemini", new_callable=AsyncMock) as mock_gem,
            patch("app.services.llm._call_groq", new_callable=AsyncMock) as mock_groq,
            patch("app.services.llm._call_openai", new_callable=AsyncMock) as mock_oai,
        ):
            s.vertex_api_key = "v"
            s.gemini_api_key = "g"
            s.groq_api_key = "gr"
            s.openai_api_key = "o"
            mock_vtx.side_effect = RuntimeError("down")
            mock_gem.side_effect = RuntimeError("down")
            mock_groq.return_value = {"winner": "groq"}

            result = await evaluate_with_llm("p")

        assert result == {"winner": "groq"}
        mock_oai.assert_not_called()
