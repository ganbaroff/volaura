"""LLM client with Gemini primary + OpenAI fallback chain.

Security: All LLM calls have a timeout to prevent request hangs during demos.
Agent innovation (Kimi-K2, architecture audit 2026-03-24): graceful fallback if LLM hangs.
"""

import asyncio
import json
from typing import Any

from loguru import logger

from app.config import settings

# Timeout for LLM calls — prevents demo-killing hangs
LLM_TIMEOUT_SECONDS = 15


async def evaluate_with_llm(
    prompt: str,
    *,
    response_format: str = "json",
    timeout: float = LLM_TIMEOUT_SECONDS,
) -> dict[str, Any] | str:
    """Call LLM with fallback chain: Gemini → OpenAI → error.

    Args:
        prompt: The full prompt to send.
        response_format: "json" for structured response, "text" for raw text.
        timeout: Max seconds per LLM call (default 15s). Prevents request hangs.

    Returns:
        Parsed JSON dict or raw text string.
    """
    # Try Gemini first (free tier)
    if settings.gemini_api_key:
        try:
            return await asyncio.wait_for(
                _call_gemini(prompt, response_format),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Gemini call timed out after {timeout}s, falling back to OpenAI")
        except Exception as e:
            logger.warning(f"Gemini call failed, falling back to OpenAI: {e}")

    # Fallback to OpenAI
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


async def _call_gemini(prompt: str, response_format: str) -> dict[str, Any] | str:
    """Call Gemini 2.5 Flash via google-genai SDK."""
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)

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
        return json.loads(text)
    return text


async def _call_openai(prompt: str, response_format: str) -> dict[str, Any] | str:
    """Call OpenAI GPT-4o-mini as fallback."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    kwargs: dict[str, Any] = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content or ""

    if response_format == "json":
        return json.loads(text)
    return text


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector via Gemini text-embedding-004.

    Returns 768-dimensional vector.
    """
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = await client.aio.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )
    return response.embeddings[0].values
