"""LiteLLM adapter for the swarm provider interface.

Implements the same LLMProvider ABC as all existing providers,
routing through LiteLLM's Router for unified fallback semantics.

Enable via env var: SWARM_USE_LITELLM=1
Disable (default): unset or SWARM_USE_LITELLM=0

Fallback chain mirrors CLAUDE.md hierarchy:
  Cerebras Qwen3-235B → Ollama local → NVIDIA NIM → Anthropic Haiku (last resort)
"""

from __future__ import annotations

import json
import os
from typing import Any

from loguru import logger

from ..swarm_types import ProviderInfo
from .base import LLMProvider

# ── Lazy import: litellm is optional until SWARM_USE_LITELLM=1 ────────────────
try:
    import litellm
    from litellm import Router

    _LITELLM_AVAILABLE = True
except ImportError:
    _LITELLM_AVAILABLE = False
    Router = None  # type: ignore[assignment,misc]


def _build_router() -> "Router":
    """Build LiteLLM Router with VOLAURA fallback chain."""
    if not _LITELLM_AVAILABLE:
        raise ImportError("litellm is not installed. Run: pip install litellm>=1.50")

    model_list = []

    if os.environ.get("CEREBRAS_API_KEY"):
        model_list.append({
            "model_name": "primary",
            "litellm_params": {
                "model": "cerebras/qwen-3-235b-a22b-instruct",
                "api_key": os.environ["CEREBRAS_API_KEY"],
            },
        })

    # Ollama local — always attempt (no key needed, may be offline)
    model_list.append({
        "model_name": "ollama-fb",
        "litellm_params": {
            "model": "ollama/qwen2.5:32b",
            "api_base": os.environ.get("OLLAMA_API_BASE", "http://localhost:11434"),
        },
    })

    if os.environ.get("NVIDIA_API_KEY"):
        model_list.append({
            "model_name": "nvidia-fb",
            "litellm_params": {
                "model": "nvidia_nim/meta/llama-3.3-70b-instruct",
                "api_key": os.environ["NVIDIA_API_KEY"],
            },
        })

    # Haiku — always registered as last resort (CLAUDE.md: never use as swarm agent proactively)
    if os.environ.get("ANTHROPIC_API_KEY"):
        model_list.append({
            "model_name": "haiku-lr",
            "litellm_params": {
                "model": "anthropic/claude-haiku-4-5-20251001",
                "api_key": os.environ["ANTHROPIC_API_KEY"],
            },
        })

    if not model_list:
        raise RuntimeError("No LLM credentials found. Set at least one of: CEREBRAS_API_KEY, NVIDIA_API_KEY, ANTHROPIC_API_KEY")

    primary_name = model_list[0]["model_name"]
    fallback_names = [m["model_name"] for m in model_list[1:]]

    fallbacks = [{primary_name: fallback_names}] if fallback_names else []

    return Router(
        model_list=model_list,
        fallbacks=fallbacks,
        num_retries=2,
        retry_after=1,
    )


# Module-level router — built once, reused across calls
_router: "Router | None" = None


def get_router() -> "Router":
    global _router
    if _router is None:
        _router = _build_router()
    return _router


class LiteLLMProvider(LLMProvider):
    """Single provider that routes through LiteLLM's unified interface.

    Registered as 'litellm' in ProviderRegistry when SWARM_USE_LITELLM=1.
    Drop-in replacement for the legacy individual providers.
    """

    def __init__(self) -> None:
        self._router = get_router()

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="litellm",
            model="router/cerebras→ollama→nvidia→haiku",
            cost_per_mtok_input=0.0,
            cost_per_mtok_output=0.0,
            rate_limit_rpm=60,
            is_free=False,
            supports_json_mode=True,
            priority=0,
        )

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        """Route prompt through LiteLLM, parse JSON response."""
        primary_name = self._router.model_list[0]["model_name"] if self._router.model_list else "primary"

        response = await self._router.acompletion(
            model=primary_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        raw_text: str = response.choices[0].message.content or "{}"

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            # Attempt to extract JSON substring
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(raw_text[start:end])
            else:
                raise

        return parsed
