"""LiteLLM unified completion — multi-provider with automatic fallback.

Provider hierarchy (ADR-013, 2026-05-09):
  NVIDIA NIM (Inception credits) → Ollama local (free) → Gemini Flash (free tier)
  → Groq (free tier, last resort)

Cerebras REMOVED entirely after $7.25 burn incident.

Setup: pip install litellm
       Set API keys in .env:
       - NVIDIA_API_KEY    (Inception credits — build.nvidia.com)
       - GEMINI_API_KEY    (250 RPD free — aistudio.google.com)
       - OLLAMA_URL        (default http://localhost:11434, unlimited)
       - GROQ_API_KEY      (rate-limited free — console.groq.com)
"""

import os

_router = None


def _get_router():
    """Lazy-init LiteLLM Router with fallback chain."""
    global _router
    if _router is not None:
        return _router

    try:
        from litellm import Router
    except ImportError:
        raise RuntimeError("pip install litellm")

    model_list = []

    # Priority 1: NVIDIA NIM (Inception credits, ADR-013 §a)
    if os.environ.get("NVIDIA_API_KEY"):
        model_list.append({
            "model_name": "swarm-llm",
            "litellm_params": {
                "model": "nvidia_nim/meta/llama-3.3-70b-instruct",
                "api_key": os.environ["NVIDIA_API_KEY"],
                "api_base": "https://integrate.api.nvidia.com/v1",
            },
        })

    # Priority 2: Ollama local (zero cost, zero rate limit)
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    model_list.append({
        "model_name": "swarm-llm",
        "litellm_params": {
            "model": "ollama_chat/qwen3:8b",
            "api_base": ollama_url,
        },
    })

    # Priority 3: Gemini Flash (Google free tier)
    if os.environ.get("GEMINI_API_KEY"):
        model_list.append({
            "model_name": "swarm-llm",
            "litellm_params": {
                "model": "gemini/gemini-2.5-flash",
                "api_key": os.environ["GEMINI_API_KEY"],
            },
        })

    # Priority 4: Groq (last resort free tier)
    if os.environ.get("GROQ_API_KEY"):
        model_list.append({
            "model_name": "swarm-llm",
            "litellm_params": {
                "model": "groq/llama-3.3-70b-versatile",
                "api_key": os.environ["GROQ_API_KEY"],
            },
        })

    # Cerebras removed — ADR-013 spend incident ($7.25 burn)

    if not model_list:
        raise RuntimeError("No LLM providers configured. Set at least one API key.")

    _router = Router(
        model_list=model_list,
        routing_strategy="simple-shuffle",
        num_retries=2,
        timeout=30,
    )
    return _router


async def llm_completion(
    prompt: str,
    system: str = "You are a helpful assistant.",
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """Call LLM with automatic provider fallback.

    Tries: NVIDIA → Ollama → Gemini → Groq (ADR-013).
    Returns the response text.
    """
    router = _get_router()
    response = await router.acompletion(
        model="swarm-llm",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    msg = response.choices[0].message
    # Qwen3 and similar models may put output in reasoning_content when
    # thinking mode is active, leaving content empty.
    text = msg.content or ""
    if not text and hasattr(msg, "reasoning_content") and msg.reasoning_content:
        text = str(msg.reasoning_content)
    return text


def llm_completion_sync(
    prompt: str,
    system: str = "You are a helpful assistant.",
    max_tokens: int = 1024,
) -> str:
    """Synchronous wrapper for agents that don't use asyncio."""
    import asyncio
    return asyncio.run(llm_completion(prompt, system, max_tokens))


# ── Backwards-compat aliases ────────────────────────────────────────────
# autonomous_run.py imports `complete` from this module as its final LiteLLM
# fallback. The function is really `llm_completion`; expose it under both
# names so the fallback chain resolves cleanly and 4 agents stop dying on
# 'cannot import name complete'.
complete = llm_completion
complete_sync = llm_completion_sync
