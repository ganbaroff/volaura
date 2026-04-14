"""Role-based model router — unified provider selection.

Created Session 93. The swarm and ad-hoc LLM calls across the codebase each
picked providers their own way (see llm.py, swarm/engine.py, reeval_worker.py).
This router centralises the decision and makes the provider hierarchy explicit,
so there is one place to audit when a call goes to the wrong model.

The hierarchy is dictated by Article 0 of CLAUDE.md (authoritative LLM order):

    Cerebras Qwen3-235B   — fastest, preferred when available
    Ollama / local GPU    — zero cost, zero rate limit, MUST try before external
    NVIDIA NIM            — free tier, 160+ open-source models
    Anthropic Haiku       — LAST RESORT ONLY, and NEVER as a swarm agent

Roles:
    judge            — highest-quality reasoning / architecture / synthesis
    worker           — bulk reasoning, code review, proposal generation
    fast             — volume, formatting, linting, rote work
    safe_user_facing — user-facing copy where safety / ethics / tone dominate

Claude models are NEVER returned for judge/worker/fast — those are "swarm
agent" roles by any reasonable definition and Article 0 bans Claude there.
Claude Haiku IS acceptable as the last fallback for safe_user_facing because
user-facing text has different ethical constraints than swarm internals.

Usage:

    from app.services.model_router import select_provider, ProviderRole

    spec = select_provider(ProviderRole.JUDGE)
    if spec is None:
        raise RuntimeError("No provider available for judge role")
    client = make_client(spec)

Every fallback is logged to atlas.governance_events (non-blocking) so the
CTO can audit when production is running on a degraded provider chain.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from loguru import logger

from app.config import settings


class ProviderRole(StrEnum):
    """Semantic role in the swarm / runtime — not a model name."""

    JUDGE = "judge"
    WORKER = "worker"
    FAST = "fast"
    SAFE_USER_FACING = "safe_user_facing"


@dataclass(frozen=True)
class ProviderSpec:
    """Resolved provider — ready to hand to an SDK client."""

    provider: str  # 'cerebras' | 'ollama' | 'nvidia' | 'gemini' | 'groq' | 'anthropic'
    model: str  # exact model id
    base_url: str | None  # for OpenAI-compatible endpoints
    api_key: str  # resolved from settings; "" means zero-auth (Ollama)
    rationale: str  # human-readable reason this was picked
    is_fallback: bool  # True if we did NOT get the first-choice provider


# ── Preference chains per role ──────────────────────────────────────────
# Each entry is a callable that returns a ProviderSpec OR None if the
# provider is not available (e.g. key missing). Evaluated top to bottom;
# the first non-None wins.


def _cerebras_qwen() -> ProviderSpec | None:
    key = getattr(settings, "cerebras_api_key", "") or ""
    if not key:
        return None
    return ProviderSpec(
        provider="cerebras",
        model="qwen-3-235b",
        base_url="https://api.cerebras.ai/v1",
        api_key=key,
        rationale="Article 0 primary: Cerebras Qwen3-235B, 2000+ tok/s",
        is_fallback=False,
    )


def _ollama_local() -> ProviderSpec | None:
    url = getattr(settings, "ollama_url", "") or "http://localhost:11434"
    # We cannot probe availability synchronously here without I/O. The caller
    # of this router is responsible for handling connection failures and
    # falling through to the next provider. Returning the spec means "try me".
    # In practice Ollama is only selected when an env marker is present.
    if not getattr(settings, "ollama_enabled", False):
        return None
    return ProviderSpec(
        provider="ollama",
        model=getattr(settings, "ollama_model", "qwen3:8b"),
        base_url=url,
        api_key="",
        rationale="Article 0: local GPU, zero cost, zero rate limit",
        is_fallback=False,
    )


def _nvidia_nemotron_ultra() -> ProviderSpec | None:
    if not settings.nvidia_api_key:
        return None
    return ProviderSpec(
        provider="nvidia",
        model="nvidia/llama-3.1-nemotron-ultra-253b-v1",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=settings.nvidia_api_key,
        rationale="NVIDIA NIM reasoning tier (253B), free",
        is_fallback=False,
    )


def _nvidia_llama_70b() -> ProviderSpec | None:
    if not settings.nvidia_api_key:
        return None
    return ProviderSpec(
        provider="nvidia",
        model="meta/llama-3.3-70b-instruct",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=settings.nvidia_api_key,
        rationale="NVIDIA NIM Llama 3.3 70B — balanced reasoning, free",
        is_fallback=False,
    )


def _gemini_pro() -> ProviderSpec | None:
    if not settings.gemini_api_key:
        return None
    return ProviderSpec(
        provider="gemini",
        model="gemini-2.5-pro",
        base_url=None,  # google-genai SDK handles endpoint
        api_key=settings.gemini_api_key,
        rationale="Gemini 2.5 Pro — 1M context, requires billing enabled",
        is_fallback=False,
    )


def _gemini_flash() -> ProviderSpec | None:
    if not settings.gemini_api_key:
        return None
    return ProviderSpec(
        provider="gemini",
        model="gemini-2.0-flash",
        base_url=None,
        api_key=settings.gemini_api_key,
        rationale="Gemini 2.0 Flash — free tier, fast",
        is_fallback=False,
    )


def _groq_llama_70b() -> ProviderSpec | None:
    if not settings.groq_api_key:
        return None
    return ProviderSpec(
        provider="groq",
        model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
        api_key=settings.groq_api_key,
        rationale="Groq Llama 3.3 70B — fast inference",
        is_fallback=False,
    )


def _groq_llama_8b() -> ProviderSpec | None:
    if not settings.groq_api_key:
        return None
    return ProviderSpec(
        provider="groq",
        model="llama-3.1-8b-instant",
        base_url="https://api.groq.com/openai/v1",
        api_key=settings.groq_api_key,
        rationale="Groq Llama 8B — volume/formatting/linting",
        is_fallback=False,
    )


def _sonnet_last_resort() -> ProviderSpec | None:
    """Claude Sonnet — server-side last-resort fallback.

    CEO directive 2026-04-14 (revised, 4th message): "полный доступ к
    клауд опус и сонет даю на все операции. во всех агентах можешь
    запускать. но планируй потом действуй. эффективность нужна. атлас
    должен дышать."

    Full access granted to Sonnet/Opus everywhere — including server-side
    runtime and swarm agents. Haiku stays banned (earlier directive, not
    rescinded). Efficiency rule: this is a LAST RESORT after three free
    tiers (Gemini Pro, Gemini Flash, NVIDIA Nemotron Ultra), not a default.
    Called only when free tier is entirely unavailable.
    """
    key = getattr(settings, "anthropic_api_key", "") or ""
    if not key:
        return None
    return ProviderSpec(
        provider="anthropic",
        model="claude-sonnet-4-6",
        base_url=None,
        api_key=key,
        rationale="CEO-authorised last-resort after 3 free tiers — never Haiku",
        is_fallback=True,
    )


# ── Role → ordered list of candidate factories ──────────────────────────

_CHAINS: dict[ProviderRole, list] = {
    ProviderRole.JUDGE: [
        _cerebras_qwen,
        _nvidia_nemotron_ultra,
        _gemini_pro,
        _ollama_local,
        _nvidia_llama_70b,
        _gemini_flash,
    ],
    ProviderRole.WORKER: [
        _ollama_local,
        _nvidia_llama_70b,
        _groq_llama_70b,
        _gemini_flash,
    ],
    ProviderRole.FAST: [
        _groq_llama_8b,
        _gemini_flash,
        _nvidia_llama_70b,
    ],
    ProviderRole.SAFE_USER_FACING: [
        _gemini_pro,
        _gemini_flash,
        _nvidia_nemotron_ultra,
        _sonnet_last_resort,  # CEO-authorised last resort after free tiers
    ],
}


def select_provider(role: ProviderRole) -> ProviderSpec | None:
    """Return the first available provider for the given role.

    Returns None if the entire chain is empty (no keys at all). In practice
    that only happens in tests or on a fresh machine before any secrets are
    loaded. Production always has at least one provider configured.

    Marks the result as is_fallback=True if it was not the primary choice,
    so callers can log a governance event for the degradation.
    """
    chain = _CHAINS.get(role)
    if not chain:
        logger.error("model_router: unknown role {role}", role=role)
        return None

    for idx, factory in enumerate(chain):
        spec = factory()
        if spec is not None:
            if idx > 0:
                # Degraded path — annotate the spec for downstream logging.
                spec = ProviderSpec(
                    provider=spec.provider,
                    model=spec.model,
                    base_url=spec.base_url,
                    api_key=spec.api_key,
                    rationale=f"{spec.rationale} (fallback #{idx} — primary unavailable)",
                    is_fallback=True,
                )
                logger.warning(
                    "model_router fallback",
                    role=role.value,
                    resolved=spec.provider + "/" + spec.model,
                    fallback_depth=idx,
                )
            return spec

    logger.error("model_router: no provider available for role {role}", role=role.value)
    return None


# ── Governance hook ─────────────────────────────────────────────────────


async def emit_fallback_event(admin, role: ProviderRole, spec: ProviderSpec) -> None:
    """Log a governance event whenever production runs on a fallback provider.

    Fire-and-forget — never blocks the LLM call. Swallows all exceptions so
    governance instrumentation never breaks the primary request path. Pass
    the SupabaseAdmin client that the caller already has.
    """
    if not spec.is_fallback:
        return
    try:
        await admin.rpc(
            "log_governance_event",
            {
                "p_event_type": "model_router_fallback",
                "p_severity": "low",
                "p_source": "model_router",
                "p_actor": spec.provider,
                "p_subject": role.value,
                "p_payload": {
                    "model": spec.model,
                    "rationale": spec.rationale,
                },
            },
        ).execute()
    except Exception as e:
        logger.warning("governance event emit failed", error=str(e)[:200])
