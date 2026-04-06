"""
Dynamic provider factory — creates providers from discovered_models.json.
One file replaces all individual provider files for discovered models.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..swarm_types import ProviderInfo
from .base import LLMProvider


class GroqDynamicProvider(LLMProvider):
    """Any Groq-hosted model."""

    def __init__(self, api_key: str, model_id: str, family: str):
        from groq import AsyncGroq
        self._client = AsyncGroq(api_key=api_key)
        self._model = model_id
        self._family = family

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=f"groq:{self._model.split('/')[-1][:20]}",
            model=self._model,
            is_free=True,
            rate_limit_rpm=30,
            priority=1,
        )

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        r = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        return json.loads(r.choices[0].message.content.strip())


class GeminiDynamicProvider(LLMProvider):
    """Any Gemini model."""

    def __init__(self, api_key: str, model_id: str, family: str):
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model_id
        self._family = family

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=f"gemini:{self._model[:20]}",
            model=self._model,
            is_free=True,
            rate_limit_rpm=15,
            priority=2,
        )

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        from google.genai import types
        r = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=temperature,
                max_output_tokens=2048,
            ),
        )
        return json.loads(r.text.strip())


class DeepSeekDynamicProvider(LLMProvider):
    """DeepSeek API model."""

    def __init__(self, api_key: str, model_id: str, family: str):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self._model = model_id
        self._family = family

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=f"deepseek:{self._model[:20]}",
            model=self._model,
            is_free=False,
            cost_per_mtok_input=0.14,
            rate_limit_rpm=60,
            priority=10,
        )

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        from openai import AsyncOpenAI
        r = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        return json.loads(r.choices[0].message.content.strip())


class OllamaDynamicProvider(LLMProvider):
    """Local Ollama model — zero rate limit, zero cost, local GPU.

    Constitution provider hierarchy: Cerebras → Gemma4/Ollama → NVIDIA → Anthropic.
    Ollama runs at OLLAMA_URL (default http://localhost:11434).
    Uses OpenAI-compatible API (Ollama v0.1.29+).
    No API key required — controlled by OLLAMA_URL env var.
    """

    def __init__(self, base_url: str, model_id: str, family: str):
        from openai import AsyncOpenAI
        # Ollama OpenAI-compatible endpoint
        self._client = AsyncOpenAI(api_key="ollama", base_url=f"{base_url.rstrip('/')}/v1")
        self._model = model_id
        self._family = family
        self._base_url = base_url

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=f"ollama:{self._model[:20]}",
            model=self._model,
            is_free=True,
            rate_limit_rpm=999,  # local — effectively unlimited
            priority=0,          # highest priority: local GPU, zero cost, zero latency tax
        )

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        r = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        return json.loads(r.choices[0].message.content.strip())


_FACTORY = {
    "groq": GroqDynamicProvider,
    "gemini": GeminiDynamicProvider,
    "deepseek": DeepSeekDynamicProvider,
    "ollama": OllamaDynamicProvider,
}

_KEY_MAP = {
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    # ollama: no API key — uses OLLAMA_URL env var
}


def guess_family(model: str) -> str:
    m = model.lower()
    if "llama-4" in m or "scout" in m: return "Meta-Llama4"
    if "llama" in m: return "Meta-Llama3"
    if "qwen" in m: return "Alibaba-Qwen"
    if "gemini" in m: return "Google-Gemini"
    if "gemma" in m: return "Google-Gemma"
    if "gpt-oss" in m: return "OpenAI-OSS"
    if "deepseek" in m: return "DeepSeek"
    if "kimi" in m: return "Moonshot-Kimi"
    if "compound" in m: return "Groq-Compound"
    if "allam" in m: return "SDAIA-Allam"
    return "Unknown"


def load_discovered_providers(env: dict[str, str]) -> list[LLMProvider]:
    """Load all working providers from discovered_models.json.

    Special handling:
    - Ollama: no API key needed. Uses OLLAMA_URL env var (default http://localhost:11434).
      Skipped silently if OLLAMA_URL not set or Ollama not reachable.
    - All other providers: require matching API key in env.
    """
    discovered_path = Path(__file__).parent.parent / "discovered_models.json"
    if not discovered_path.exists():
        return []

    with open(discovered_path, "r", encoding="utf-8") as f:
        models = json.load(f)

    providers: list[LLMProvider] = []
    for m in models:
        model_id = m["model"]
        provider_type = m["provider"]

        factory = _FACTORY.get(provider_type)
        if not factory:
            continue

        # Ollama: local GPU — no API key, uses OLLAMA_URL
        if provider_type == "ollama":
            ollama_url = env.get("OLLAMA_URL", "http://localhost:11434").strip()
            family = guess_family(model_id)
            try:
                providers.append(OllamaDynamicProvider(ollama_url, model_id, family))
            except Exception:
                continue
            continue

        api_key = env.get(_KEY_MAP.get(provider_type, ""), "").strip()
        if not api_key:
            continue

        family = guess_family(model_id)
        try:
            providers.append(factory(api_key, model_id, family))
        except Exception:
            continue

    return providers
