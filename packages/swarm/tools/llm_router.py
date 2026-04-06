"""LiteLLM unified completion — multi-provider with automatic fallback.

Provider hierarchy: Cerebras (fast) → Groq (backup) → Ollama (free) → Gemini (fallback)

Setup: pip install litellm
       Set API keys in .env (all have free tiers, no credit card needed):
       - CEREBRAS_API_KEY  (1M tokens/day free — cloud.cerebras.ai)
       - GROQ_API_KEY      (rate-limited free — console.groq.com)
       - GEMINI_API_KEY    (250 RPD free — aistudio.google.com)
       - OLLAMA_URL        (default http://localhost:11434, unlimited)
"""

import os
from typing import Optional

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

    # Priority 1: Cerebras (2000+ tok/sec, 1M tokens/day free)
    if os.environ.get("CEREBRAS_API_KEY"):
        model_list.append({
            "model_name": "swarm-llm",
            "litellm_params": {
                "model": "cerebras/llama3.1-8b",
                "api_key": os.environ["CEREBRAS_API_KEY"],
            },
        })

    # Priority 2: Groq (500+ tok/sec, rate-limited free)
    if os.environ.get("GROQ_API_KEY"):
        model_list.append({
            "model_name": "swarm-llm",
            "litellm_params": {
                "model": "groq/llama-3.3-70b-versatile",
                "api_key": os.environ["GROQ_API_KEY"],
            },
        })

    # Priority 3: Ollama local (zero cost, zero rate limit)
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    model_list.append({
        "model_name": "swarm-llm",
        "litellm_params": {
            "model": "ollama_chat/qwen3:8b",
            "api_base": ollama_url,
        },
    })

    # Priority 4: Gemini Flash (Google fallback)
    if os.environ.get("GEMINI_API_KEY"):
        model_list.append({
            "model_name": "swarm-llm",
            "litellm_params": {
                "model": "gemini/gemini-2.5-flash",
                "api_key": os.environ["GEMINI_API_KEY"],
            },
        })

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

    Tries: Cerebras → Groq → Ollama → Gemini.
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
    return response.choices[0].message.content


def llm_completion_sync(
    prompt: str,
    system: str = "You are a helpful assistant.",
    max_tokens: int = 1024,
) -> str:
    """Synchronous wrapper for agents that don't use asyncio."""
    import asyncio
    return asyncio.run(llm_completion(prompt, system, max_tokens))
