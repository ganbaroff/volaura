"""DeepSeek provider — cheapest paid reasoning model, OpenAI-compatible API."""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from ..swarm_types import ProviderInfo
from .base import LLMProvider

DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = DEEPSEEK_MODEL):
        self._client = AsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        self._model = model

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="deepseek",
            model=self._model,
            cost_per_mtok_input=0.14,
            cost_per_mtok_output=0.28,
            rate_limit_rpm=60,
            is_free=False,
            supports_json_mode=True,
            priority=10,  # paid = lower priority
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
