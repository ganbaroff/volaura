"""OpenAI provider — gpt-4o-mini, paid fallback with best structured output."""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from ..swarm_types import ProviderInfo
from .base import LLMProvider

OPENAI_MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = OPENAI_MODEL):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="openai",
            model=self._model,
            cost_per_mtok_input=0.15,
            cost_per_mtok_output=0.60,
            rate_limit_rpm=500,
            is_free=False,
            supports_json_mode=True,
            priority=20,  # most expensive = last resort
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
