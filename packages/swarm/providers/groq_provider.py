"""Groq provider — ultra-fast inference via LPU."""

from __future__ import annotations

import json
from typing import Any

from groq import AsyncGroq

from ..swarm_types import ProviderInfo
from .base import LLMProvider

GROQ_MODEL = "llama-3.3-70b-versatile"


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = GROQ_MODEL):
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="groq",
            model=self._model,
            cost_per_mtok_input=0.59,
            cost_per_mtok_output=0.79,
            rate_limit_rpm=30,
            is_free=True,
            supports_json_mode=True,
            priority=1,
        )

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
