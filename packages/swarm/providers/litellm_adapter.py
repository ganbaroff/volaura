"""LiteLLM adapter for the swarm provider interface.

Implements the same LLMProvider ABC as all existing providers,
routing through LiteLLM's Router for unified fallback semantics.

Enable via env var: SWARM_USE_LITELLM=1
Disable (default): unset or SWARM_USE_LITELLM=0

Fallback chain mirrors CLAUDE.md hierarchy:
  Cerebras Qwen3-235B → Ollama local → NVIDIA NIM

Constitution Article 0 (atlas_swarm_daemon.py:19): Anthropic Claude is FORBIDDEN
as a swarm agent. The adapter MUST NOT route any prompt to anthropic/* models,
even if ANTHROPIC_API_KEY is present in the environment. Enforced by
``_build_model_list`` and covered by tests/test_litellm_adapter.py.
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


_FORBIDDEN_MODEL_PREFIXES: tuple[str, ...] = ("anthropic/",)
"""Model prefixes that are forbidden by Constitution Article 0.

Any entry returned by ``_build_model_list`` whose ``litellm_params.model``
begins with one of these prefixes is rejected before the Router is built.
Tests in ``tests/test_litellm_adapter.py`` assert this invariant even when
``ANTHROPIC_API_KEY`` is set in the environment.
"""


def _build_model_list(env: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Construct the LiteLLM model_list from environment.

    Pure function — does not require litellm to be importable. Easy to test
    without instantiating ``Router``. Constitution Article 0 is enforced here:
    no anthropic/* model can ever land in the returned list, regardless of
    whether ``ANTHROPIC_API_KEY`` is set.
    """
    env = env if env is not None else dict(os.environ)
    model_list: list[dict[str, Any]] = []

    if env.get("CEREBRAS_API_KEY"):
        model_list.append({
            "model_name": "primary",
            "litellm_params": {
                "model": "cerebras/qwen-3-235b-a22b-instruct",
                "api_key": env["CEREBRAS_API_KEY"],
            },
        })

    # Ollama local — always attempt (no key needed, may be offline).
    # Model is configurable via OLLAMA_MODEL because operators frequently pull
    # different local models. Default `ollama/qwen3:8b` matches the model that
    # is actually present on VOLAURA's primary workstation as of 2026-05-08
    # (`curl localhost:11434/api/tags` -> qwen3:8b, gemma4:latest). Without
    # this env-override the fallback path 404s on `qwen2.5:32b not found`,
    # which previously masqueraded as "Ollama broken" when the real cause was
    # a hardcoded model name. See codex-loop.md Phase B2.5 for receipts.
    ollama_model = env.get("OLLAMA_MODEL", "ollama/qwen3:8b")
    if not ollama_model.startswith("ollama/"):
        ollama_model = f"ollama/{ollama_model}"
    model_list.append({
        "model_name": "ollama-fb",
        "litellm_params": {
            "model": ollama_model,
            "api_base": env.get("OLLAMA_API_BASE", "http://localhost:11434"),
        },
    })

    if env.get("NVIDIA_API_KEY"):
        model_list.append({
            "model_name": "nvidia-fb",
            "litellm_params": {
                "model": "nvidia_nim/meta/llama-3.3-70b-instruct",
                "api_key": env["NVIDIA_API_KEY"],
            },
        })

    # Constitution Article 0 enforcement: drop any anthropic/* even if a future
    # author re-introduces it above. Belt + suspenders.
    safe_list = [
        m for m in model_list
        if not str(m.get("litellm_params", {}).get("model", "")).startswith(_FORBIDDEN_MODEL_PREFIXES)
    ]

    if len(safe_list) != len(model_list):
        dropped = [m for m in model_list if m not in safe_list]
        logger.warning(
            "litellm_adapter dropped {n} forbidden model(s) per Constitution Article 0: {names}",
            n=len(dropped),
            names=[m.get("model_name") for m in dropped],
        )

    return safe_list


def _build_router() -> "Router":
    """Build LiteLLM Router with VOLAURA fallback chain."""
    if not _LITELLM_AVAILABLE:
        raise ImportError("litellm is not installed. Run: pip install litellm>=1.50")

    model_list = _build_model_list()

    if not model_list:
        raise RuntimeError("No LLM credentials found. Set at least one of: CEREBRAS_API_KEY, NVIDIA_API_KEY")

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
            model="router/cerebras→ollama→nvidia",
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
