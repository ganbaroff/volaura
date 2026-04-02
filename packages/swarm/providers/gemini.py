"""Gemini 2.5 Flash provider via google-genai SDK."""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types

from ..swarm_types import ProviderInfo
from .base import LLMProvider

GEMINI_MODEL = "gemini-2.0-flash"


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = GEMINI_MODEL):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="gemini",
            model=self._model,
            cost_per_mtok_input=0.075,
            cost_per_mtok_output=0.30,
            rate_limit_rpm=15,
            is_free=True,
            supports_json_mode=True,
            priority=0,
        )

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=temperature,
                max_output_tokens=2048,
            ),
        )
        raw = response.text.strip()
        return json.loads(raw)
