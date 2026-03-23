"""
Abstract base class for all LLM providers.
Every provider implements evaluate(); safe_evaluate() wraps with timing, retry, error handling.
"""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from ..types import ProviderInfo

MAX_RETRIES = 2
RETRY_DELAY_S = 1.0


class LLMProvider(ABC):
    """Base class all LLM providers implement."""

    @abstractmethod
    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        """Send prompt to LLM, return parsed JSON dict. Raise on failure."""
        ...

    @abstractmethod
    def info(self) -> ProviderInfo:
        """Return provider metadata (name, model, cost, limits)."""
        ...

    def get_provider_name(self) -> str:
        return self.info().name

    def get_model_name(self) -> str:
        return self.info().model

    def get_cost_per_mtok(self) -> float:
        return self.info().cost_per_mtok_input

    def get_rate_limit_rpm(self) -> int:
        return self.info().rate_limit_rpm

    def is_free(self) -> bool:
        return self.info().is_free

    async def safe_evaluate(
        self, prompt: str, temperature: float = 0.7
    ) -> dict[str, Any]:
        """Wrapper: retry on transient errors, measure latency, validate JSON."""
        provider = self.get_provider_name()
        model = self.get_model_name()
        last_error = ""

        for attempt in range(MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                result = await self.evaluate(prompt, temperature)
                latency = int((time.monotonic() - start) * 1000)

                if not isinstance(result, dict):
                    return {
                        "error": f"Expected dict, got {type(result).__name__}",
                        "json_valid": False,
                        "latency_ms": latency,
                        "provider": provider,
                        "model": model,
                    }

                result["json_valid"] = True
                result["latency_ms"] = latency
                result["provider"] = provider
                result["model"] = model

                logger.debug(
                    "{p} ({m}) responded in {ms}ms (attempt {a})",
                    p=provider, m=model, ms=latency, a=attempt + 1,
                )
                return result

            except json.JSONDecodeError as e:
                latency = int((time.monotonic() - start) * 1000)
                last_error = f"JSON parse error: {e}"
                # JSON errors are not transient - don't retry
                break

            except Exception as e:
                latency = int((time.monotonic() - start) * 1000)
                last_error = str(e)[:500]
                err_str = str(e).lower()

                # Retry on transient errors (429 rate limit, 503 overloaded, timeout)
                is_transient = any(code in err_str for code in ["429", "503", "timeout", "overloaded"])

                if is_transient and attempt < MAX_RETRIES:
                    delay = RETRY_DELAY_S * (attempt + 1)
                    logger.info(
                        "{p} transient error (attempt {a}/{max}), retrying in {d}s: {e}",
                        p=provider, a=attempt + 1, max=MAX_RETRIES + 1,
                        d=delay, e=last_error[:100],
                    )
                    await asyncio.sleep(delay)
                    continue

                # Non-transient (401 auth, 404 not found, etc.) - don't retry
                break

        logger.warning(
            "{p} failed after {a} attempt(s): {e}",
            p=provider, a=attempt + 1, e=last_error[:200],
        )
        return {
            "error": last_error,
            "json_valid": False,
            "latency_ms": int((time.monotonic() - start) * 1000),
            "provider": provider,
            "model": model,
        }
