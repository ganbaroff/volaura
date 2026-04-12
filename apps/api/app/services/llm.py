"""LLM client with Vertex Express primary + Gemini + Groq + OpenAI fallback chain.

Fallback chain (S-04/S-06 — BATCH-S 2026-03-31):
  Vertex AI Express (99.9% SLA, enterprise rate limits)
  → AI Studio Gemini (free tier, 15 RPM)
  → Groq (14,400 req/day free tier — cost buffer)
  → OpenAI GPT-4o-mini (paid fallback, last resort)
  → keyword fallback (in bars.py)

Observability: Langfuse tracing wraps every LLM call when LANGFUSE_PUBLIC_KEY +
LANGFUSE_SECRET_KEY are set. If keys are missing, tracing is silently disabled
(zero performance overhead — no import, no decorator, no network calls).

Security: All LLM calls have a timeout to prevent request hangs during demos.
Agent innovation (Kimi-K2, architecture audit 2026-03-24): graceful fallback if LLM hangs.
"""

import asyncio
import json
from typing import Any

from app.utils.pii_redactor import redact as redact_pii

from loguru import logger

from app.config import settings

# ---------------------------------------------------------------------------
# Langfuse observability — optional, graceful degradation
# ---------------------------------------------------------------------------
_langfuse_available = False

if settings.langfuse_public_key and settings.langfuse_secret_key:
    try:
        from langfuse.decorators import langfuse_context, observe

        _langfuse_available = True
        logger.info("Langfuse tracing enabled")
    except ImportError:
        logger.warning(
            "Langfuse keys are set but 'langfuse' package is not installed. "
            "Tracing disabled. Run: pip install langfuse"
        )
else:
    logger.debug("Langfuse keys not set — LLM tracing disabled")

# Timeout for LLM calls — prevents demo-killing hangs
LLM_TIMEOUT_SECONDS = 15


def _trace(*, name: str | None = None, as_type: str | None = None):
    """Conditional Langfuse decorator — no-op if Langfuse is not available.

    Args:
        name: Span name in Langfuse (e.g. "evaluate_with_llm").
        as_type: Langfuse span type — "generation" for LLM calls, None for generic spans.
    """
    def decorator(func):
        if not _langfuse_available:
            return func
        kwargs: dict[str, Any] = {}
        if name:
            kwargs["name"] = name
        if as_type:
            kwargs["as_type"] = as_type
        return observe(**kwargs)(func)
    return decorator

# Singleton clients — initialized once on first call, reused for connection pool efficiency.
# Architecture agent note: 880 RPM at activation wave = 880 client object creations/min
# without this pattern. Module-level state: tests must call reset_llm_clients() in teardown.
_vertex_client: Any | None = None
_gemini_client: Any | None = None


def reset_llm_clients() -> None:
    """Reset singleton clients. Call in test teardown to prevent cross-test pollution."""
    global _vertex_client, _gemini_client
    _vertex_client = None
    _gemini_client = None
    flush_langfuse()


def flush_langfuse() -> None:
    """Flush pending Langfuse traces. Call at shutdown or in test teardown.

    No-op if Langfuse is not active.
    """
    if _langfuse_available:
        try:
            langfuse_context.flush()
        except Exception as e:
            logger.debug(f"Langfuse flush error (non-critical): {e}")


def _update_trace_metadata(*, model: str, provider: str, input_text: str | None = None) -> None:
    """Update current Langfuse observation with model metadata.

    No-op if Langfuse is not active. Errors are swallowed to never break LLM calls.
    """
    if not _langfuse_available:
        return
    try:
        update_kwargs: dict[str, Any] = {"model": model, "metadata": {"provider": provider}}
        if input_text is not None:
            update_kwargs["input"] = redact_pii(input_text)
        langfuse_context.update_current_observation(**update_kwargs)
    except Exception:
        pass  # Never let tracing break LLM calls


def _get_vertex_client() -> Any:
    """Lazy-init Vertex AI Express client (singleton)."""
    global _vertex_client
    if _vertex_client is None:
        from google import genai
        # Vertex Express mode: vertexai=True + api_key — do NOT pass project/location
        # (that's the ADC path, mutually exclusive with Express key auth)
        _vertex_client = genai.Client(vertexai=True, api_key=settings.vertex_api_key)
    return _vertex_client


def _get_gemini_client() -> Any:
    """Lazy-init AI Studio Gemini client (singleton)."""
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


@_trace(name="evaluate_with_llm")
async def evaluate_with_llm(
    prompt: str,
    *,
    response_format: str = "json",
    timeout: float = LLM_TIMEOUT_SECONDS,
) -> dict[str, Any] | str:
    """Call LLM with fallback chain: Vertex → Gemini → Groq → OpenAI.

    Args:
        prompt: The full prompt to send.
        response_format: "json" for structured response, "text" for raw text.
        timeout: Max seconds per LLM call (default 15s). Prevents request hangs.

    Returns:
        Parsed JSON dict or raw text string.
    """
    # Vertex AI Express — primary (enterprise SLA, same $100/mo budget)
    if settings.vertex_api_key:
        try:
            return await asyncio.wait_for(
                _call_vertex(prompt, response_format),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Vertex call timed out, falling back to Gemini", timeout=timeout)
        except Exception as e:
            logger.warning("Vertex call failed, falling back to Gemini", error=str(e)[:200])

    # AI Studio Gemini — secondary (free tier, 15 RPM cap)
    if settings.gemini_api_key:
        try:
            return await asyncio.wait_for(
                _call_gemini(prompt, response_format),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Gemini call timed out, falling back to Groq", timeout=timeout)
        except Exception as e:
            logger.warning("Gemini call failed, falling back to Groq", error=str(e)[:200])

    # Groq — tertiary (14,400 req/day free tier — cost buffer before paid OpenAI)
    if settings.groq_api_key:
        try:
            return await asyncio.wait_for(
                _call_groq(prompt, response_format),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(f"Groq fallback timed out after {timeout}s")
        except Exception as e:
            logger.error(f"Groq fallback failed: {e}")

    # OpenAI — last resort (paid, ~$240/day at activation wave — only if all else fails)
    if settings.openai_api_key:
        try:
            return await asyncio.wait_for(
                _call_openai(prompt, response_format),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(f"OpenAI fallback timed out after {timeout}s")
        except Exception as e:
            logger.error(f"OpenAI fallback also failed: {e}")

    raise RuntimeError("All LLM providers failed or timed out. Check API keys and rate limits.")


@_trace(name="llm_vertex", as_type="generation")
async def _call_vertex(prompt: str, response_format: str) -> dict[str, Any] | str:
    """Call Gemini via Vertex AI Express (99.9% SLA, enterprise rate limits)."""
    _update_trace_metadata(model="gemini-2.5-flash", provider="vertex-express", input_text=prompt[:500])
    client = _get_vertex_client()

    config: dict[str, Any] = {}
    if response_format == "json":
        config["response_mime_type"] = "application/json"

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )

    text = response.text or ""

    if response_format == "json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Vertex returned invalid JSON: {e} — raw: {text[:200]}")
            return {}
    return text


@_trace(name="llm_gemini", as_type="generation")
async def _call_gemini(prompt: str, response_format: str) -> dict[str, Any] | str:
    """Call Gemini 2.5 Flash via AI Studio (free tier fallback)."""
    _update_trace_metadata(model="gemini-2.5-flash", provider="google-ai-studio", input_text=prompt[:500])
    client = _get_gemini_client()

    config: dict[str, Any] = {}
    if response_format == "json":
        config["response_mime_type"] = "application/json"

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )

    text = response.text or ""

    if response_format == "json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Gemini returned invalid JSON: {e} — raw: {text[:200]}")
            return {}
    return text


@_trace(name="llm_groq", as_type="generation")
async def _call_groq(prompt: str, response_format: str) -> dict[str, Any] | str:
    """Call Groq (llama-3.3-70b) — free tier cost buffer (14,400 req/day)."""
    _update_trace_metadata(model="llama-3.3-70b-versatile", provider="groq", input_text=prompt[:500])
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)

    kwargs: dict[str, Any] = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
    }
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    if not response.choices:
        raise RuntimeError("Groq returned empty choices list")
    text = response.choices[0].message.content or ""

    if response_format == "json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Groq returned invalid JSON: {e} — raw: {text[:200]}")
            return {}
    return text


@_trace(name="llm_openai", as_type="generation")
async def _call_openai(prompt: str, response_format: str) -> dict[str, Any] | str:
    """Call OpenAI GPT-4o-mini — last-resort paid fallback."""
    _update_trace_metadata(model="gpt-4o-mini", provider="openai", input_text=prompt[:500])
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    kwargs: dict[str, Any] = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    if not response.choices:
        logger.error("OpenAI returned empty choices list")
        raise RuntimeError("OpenAI returned empty response")
    text = response.choices[0].message.content or ""

    if response_format == "json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"OpenAI returned invalid JSON: {e} — raw: {text[:200]}")
            return {}
    return text


@_trace(name="generate_embedding")
async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector via Gemini text-embedding-004.

    Returns 768-dimensional vector. Uses Vertex if available, falls back to AI Studio.
    """
    if settings.vertex_api_key:
        try:
            client = _get_vertex_client()
            response = await client.aio.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.warning(f"Vertex embedding failed, falling back to Gemini: {e}")

    from google import genai
    client = _get_gemini_client()
    response = await client.aio.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )
    return response.embeddings[0].values
