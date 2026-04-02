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


_FACTORY = {
    "groq": GroqDynamicProvider,
    "gemini": GeminiDynamicProvider,
    "deepseek": DeepSeekDynamicProvider,
}

_KEY_MAP = {
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
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
    """Load all working providers from discovered_models.json."""
    discovered_path = Path(__file__).parent.parent / "discovered_models.json"
    if not discovered_path.exists():
        return []

    with open(discovered_path, "r", encoding="utf-8") as f:
        models = json.load(f)

    providers: list[LLMProvider] = []
    for m in models:
        model_id = m["model"]
        provider_type = m["provider"]
        api_key = env.get(_KEY_MAP.get(provider_type, ""), "").strip()

        if not api_key:
            continue

        factory = _FACTORY.get(provider_type)
        if not factory:
            continue

        family = guess_family(model_id)
        try:
            providers.append(factory(api_key, model_id, family))
        except Exception:
            continue

    return providers
