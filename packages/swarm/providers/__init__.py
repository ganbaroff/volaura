"""
ProviderRegistry - auto-discovers available LLM providers from environment variables.
Optimized for 3-provider engine: Gemini (free) + Groq (free) + DeepSeek (cheap paid).
OpenAI available as optional fallback if key has billing.
"""

from __future__ import annotations

import os

from loguru import logger

from ..swarm_types import StakesLevel, DomainTag, ModelProfile
from .base import LLMProvider

# Provider discovery order: free first, then cheap paid, then expensive
# Groq key unlocks 3 model families (Llama, Gemma, Mixtral) = 3 providers from 1 key
_PROVIDER_MAP: list[tuple[str, str, str]] = [
    ("GEMINI_API_KEY", "providers.gemini", "GeminiProvider"),
    ("GROQ_API_KEY", "providers.groq_provider", "GroqProvider"),
    ("GROQ_API_KEY", "providers.groq_gemma", "GroqQwenProvider"),
    ("GROQ_API_KEY", "providers.groq_mixtral", "GroqGptOssProvider"),
    ("DEEPSEEK_API_KEY", "providers.deepseek", "DeepSeekProvider"),
    ("OPENAI_API_KEY", "providers.openai_provider", "OpenAIProvider"),
]

_STAKES_AGENTS: dict[StakesLevel, int] = {
    StakesLevel.LOW: 5,
    StakesLevel.MEDIUM: 7,
    StakesLevel.HIGH: 10,
    StakesLevel.CRITICAL: 15,
}


class ProviderRegistry:
    """Discovers available providers and allocates agents for swarm runs."""

    def discover(self, env: dict[str, str] | None = None) -> list[LLMProvider]:
        """Check each provider's env var. Return instances of available ones."""
        env = env or dict(os.environ)
        available: list[LLMProvider] = []

        for env_var, mod_path, cls_name in _PROVIDER_MAP:
            key = env.get(env_var, "").strip()
            if not key:
                logger.debug("Provider {c} skipped: {v} not set", c=cls_name, v=env_var)
                continue

            try:
                provider = _import_and_create(mod_path, cls_name, key)
                available.append(provider)
                free_tag = "FREE" if provider.is_free() else f"${provider.get_cost_per_mtok()}/MTok"
                logger.info(
                    "Provider discovered: {n} ({m}) [{f}]",
                    n=provider.get_provider_name(),
                    m=provider.get_model_name(),
                    f=free_tag,
                )
            except Exception as e:
                logger.warning(
                    "Failed to init {c}: {e}", c=cls_name, e=str(e)[:200]
                )

        if not available:
            logger.error("No LLM providers available. Set at least one API key.")

        return available

    def allocate_agents(
        self,
        stakes: StakesLevel,
        available: list[LLMProvider],
        profiles: dict[str, ModelProfile] | None = None,
        domain: DomainTag = DomainTag.GENERAL,
        max_agents: int = 15,
    ) -> list[tuple[LLMProvider, float, float]]:
        """Allocate agents across providers for a swarm run.

        Distribution strategy (optimized for Gemini + Groq + DeepSeek):
        - Gemini: quality, multilingual - gets ~40% of agents
        - Groq: speed, volume - gets ~40% of agents
        - DeepSeek: deep reasoning - gets ~20% (paid, use sparingly)
        - OpenAI: only if available and HIGH+ stakes
        """
        target = min(_STAKES_AGENTS.get(stakes, 7), max_agents)
        if not available:
            return []

        sorted_providers = sorted(available, key=lambda p: p.info().priority)

        # Domain-aware filtering via TeamLead (skip for GENERAL — use all providers)
        if domain != DomainTag.GENERAL:
            from ..team_leads import get_tilead_for_domain
            tilead = get_tilead_for_domain(domain)
            excluded = [p for p in sorted_providers if p not in tilead.filter_providers(sorted_providers)]
            sorted_providers = tilead.filter_providers(sorted_providers)
            if excluded:
                logger.info(
                    "TeamLead[{d}] excluded {n} provider(s) as dead weight: {names}",
                    d=domain.value,
                    n=len(excluded),
                    names=[p.get_provider_name() for p in excluded],
                )

        free_providers = [p for p in sorted_providers if p.is_free()]
        paid_providers = [p for p in sorted_providers if not p.is_free()]

        agents: list[tuple[LLMProvider, float, float]] = []
        temps = [0.5, 0.7, 0.9, 0.6, 0.8, 0.55, 0.75, 0.85]

        # Phase 1: fill with free providers (round-robin)
        free_target = target if not paid_providers else int(target * 0.8)
        round_idx = 0
        while len(agents) < free_target and free_providers:
            for provider in free_providers:
                if len(agents) >= free_target:
                    break
                temp = temps[len(agents) % len(temps)]
                weight = _get_weight(provider, profiles, domain)
                agents.append((provider, weight, temp))
            round_idx += 1
            if round_idx > 5:
                break

        # Phase 2: add paid providers for remaining slots
        if paid_providers and len(agents) < target:
            # For LOW stakes: skip paid. For MEDIUM+: add 1-2 paid agents.
            if stakes != StakesLevel.LOW:
                for provider in paid_providers:
                    if len(agents) >= target:
                        break
                    # DeepSeek: always add 1. OpenAI: only for HIGH+
                    if provider.get_provider_name() == "openai" and stakes not in (
                        StakesLevel.HIGH, StakesLevel.CRITICAL
                    ):
                        continue
                    temp = temps[len(agents) % len(temps)]
                    weight = _get_weight(provider, profiles, domain)
                    agents.append((provider, weight, temp))

        return agents


def _get_weight(
    provider: LLMProvider,
    profiles: dict[str, ModelProfile] | None,
    domain: DomainTag,
) -> float:
    """Get calibrated weight for a provider in a domain."""
    if not profiles:
        return 1.0
    model_name = provider.get_model_name()
    profile = profiles.get(model_name)
    if not profile:
        return 1.0
    return profile.get_weight(domain)


def _import_and_create(mod_path: str, cls_name: str, api_key: str) -> LLMProvider:
    """Lazily import a provider class and instantiate it."""
    import importlib

    full_path = f"packages.swarm.{mod_path}"
    try:
        module = importlib.import_module(full_path)
    except ModuleNotFoundError:
        from . import gemini, groq_provider, groq_gemma, groq_mixtral, deepseek, openai_provider

        module_map = {
            "providers.gemini": gemini,
            "providers.groq_provider": groq_provider,
            "providers.groq_gemma": groq_gemma,
            "providers.groq_mixtral": groq_mixtral,
            "providers.deepseek": deepseek,
            "providers.openai_provider": openai_provider,
        }
        module = module_map[mod_path]

    cls = getattr(module, cls_name)
    return cls(api_key=api_key)
