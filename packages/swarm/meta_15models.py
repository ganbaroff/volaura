"""
Meta-swarm: ALL 15 working models decide how to organize themselves.
Uses dynamic provider creation from discovered_models.json.
Each agent adds 1 innovation idea at the end.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.swarm.providers.base import LLMProvider
from packages.swarm.types import ProviderInfo

# -------------------------------------------------------
# Dynamic provider factory - creates providers from discovered_models.json
# -------------------------------------------------------

class GroqDynamicProvider(LLMProvider):
    def __init__(self, api_key: str, model_id: str, name: str, family: str):
        from groq import AsyncGroq
        self._client = AsyncGroq(api_key=api_key)
        self._model = model_id
        self._name = name
        self._family = family

    def info(self) -> ProviderInfo:
        return ProviderInfo(name=self._name, model=self._model, is_free=True,
                           rate_limit_rpm=30, priority=1)

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict:
        r = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature, max_tokens=2048,
            response_format={"type": "json_object"},
        )
        return json.loads(r.choices[0].message.content.strip())


class GeminiDynamicProvider(LLMProvider):
    def __init__(self, api_key: str, model_id: str, name: str, family: str):
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model_id
        self._name = name
        self._family = family

    def info(self) -> ProviderInfo:
        return ProviderInfo(name=self._name, model=self._model, is_free=True,
                           rate_limit_rpm=15, priority=2)

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict:
        from google.genai import types
        r = await self._client.aio.models.generate_content(
            model=self._model, contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=temperature, max_output_tokens=2048,
            ),
        )
        return json.loads(r.text.strip())


class DeepSeekDynamicProvider(LLMProvider):
    def __init__(self, api_key: str, model_id: str, name: str, family: str):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self._model = model_id
        self._name = name
        self._family = family

    def info(self) -> ProviderInfo:
        return ProviderInfo(name=self._name, model=self._model, is_free=False,
                           cost_per_mtok_input=0.14, rate_limit_rpm=60, priority=10)

    async def evaluate(self, prompt: str, temperature: float = 0.7) -> dict:
        r = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature, max_tokens=2048,
            response_format={"type": "json_object"},
        )
        return json.loads(r.choices[0].message.content.strip())


def load_all_providers() -> list[LLMProvider]:
    """Load ALL working providers from discovered_models.json."""
    discovered_path = Path(__file__).parent / "discovered_models.json"
    with open(discovered_path, "r", encoding="utf-8") as f:
        models = json.load(f)

    groq_key = os.environ.get("GROQ_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")

    providers = []
    for m in models:
        model_id = m["model"]
        provider = m["provider"]
        name = model_id.replace("/", "_").replace("-", "_")[:20]

        if provider == "groq" and groq_key:
            providers.append(GroqDynamicProvider(groq_key, model_id, name, "groq"))
        elif provider == "gemini" and gemini_key:
            providers.append(GeminiDynamicProvider(gemini_key, model_id, name, "gemini"))
        elif provider == "deepseek" and deepseek_key:
            providers.append(DeepSeekDynamicProvider(deepseek_key, model_id, name, "deepseek"))

    return providers


# -------------------------------------------------------
# Prompt with innovation field
# -------------------------------------------------------

QUESTION = """You are one of 15 AI models evaluating how to organize a multi-model swarm decision engine.

SITUATION:
We have 15 working AI models from 8 different families, all accessible via 3 API keys:
- GROQ (free, fast): llama-3.1-8b (182ms), llama-3.3-70b (311ms), allam-2-7b (389ms),
  gpt-oss-120b (443ms), kimi-k2 (452ms), llama-4-scout (465ms), compound-mini (519ms), compound (2361ms)
- GEMINI (free): flash-lite (877ms), 2.0-flash (1035ms), 2.5-flash-lite (1137ms),
  3.1-flash-lite (1603ms), 2.5-pro (2818ms)
- DEEPSEEK (paid $0.14/MTok): deepseek-chat (2659ms)

GOAL: Organize these 15 models into a tournament-style decision engine where:
1. Questions are split into topic GROUPS (security, cost, UX, speed, quality, etc.)
2. Each group has 3-5 models from DIFFERENT families
3. Within each group: models evaluate independently, then weighted vote picks winner
4. Cross-group: LLM synthesis combines group winners (MoA-style)
5. Over 10-20 sprints: track which model wins in which domain, evolutionary selection

CONSTRAINTS:
- Budget: $50/month total. Free tier primary.
- Groq rate limit: 30 RPM shared across all Groq models
- Gemini rate limit: 15 RPM shared across all Gemini models
- Not all 15 models on every question (rate limits). Need rotation strategy.
- Must be universal (any question, not project-specific)
- Tournament mode for HIGH+ stakes. Flat pool for LOW/MEDIUM.

QUESTION: How should we organize these 15 models into groups for the tournament?
Specifically:
1. How many groups? What topics?
2. Which models in which groups? (consider speed, family diversity, cost)
3. How to handle Groq 30 RPM limit when 9 of 15 models are Groq?
4. Rotation strategy: how to rotate models across groups over sprints?
5. How to handle the speed gap (182ms vs 2818ms)?

Respond with JSON:
{
  "evaluator": "your_model_name",
  "proposed_groups": [
    {"name": "group_name", "models": ["model1", "model2", "model3"], "topic": "what this group evaluates"}
  ],
  "rotation_strategy": "how to rotate models between groups across sprints",
  "rate_limit_strategy": "how to handle 30 RPM Groq + 15 RPM Gemini",
  "speed_strategy": "how to handle fast vs slow models",
  "total_agents_per_run": 0,
  "estimated_latency": "Xs",
  "winner_group_count": 0,
  "reason": "why this organization is optimal",
  "innovation": "ONE unexpected/creative idea for using 15 models that nobody asked about. Must be actionable in 1 session. Think outside the box.",
  "confidence": 0.0
}"""


async def run():
    print("=" * 70)
    print("ALL 15 MODELS: How should we organize ourselves?")
    print("=" * 70)

    providers = load_all_providers()
    print(f"Loaded {len(providers)} providers")
    for p in providers:
        print(f"  {p.get_model_name():45s} | {p.info().name}")

    # Dispatch ALL 15 in parallel
    print(f"\nLaunching {len(providers)} agents in parallel...")
    start = time.monotonic()

    tasks = [p.safe_evaluate(QUESTION, temperature=0.7) for p in providers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    total_ms = int((time.monotonic() - start) * 1000)

    print(f"\n{'=' * 70}")
    print(f"RESULTS ({total_ms}ms total)")
    print(f"{'=' * 70}")

    successes = []
    for provider, result in zip(providers, results):
        model = provider.get_model_name()
        if isinstance(result, Exception):
            print(f"  [x] {model:40s} | EXCEPTION: {str(result)[:60]}")
        elif isinstance(result, dict) and result.get("error"):
            print(f"  [x] {model:40s} | ERROR: {result['error'][:60]}")
        elif isinstance(result, dict) and result.get("json_valid"):
            ms = result.get("latency_ms", 0)
            print(f"  [+] {model:40s} | {ms:5d}ms | OK")
            successes.append({"model": model, "result": result, "ms": ms})
        else:
            print(f"  [?] {model:40s} | UNKNOWN: {str(result)[:60]}")

    print(f"\nSuccess: {len(successes)}/{len(providers)}")

    # Parse proposed groups from each agent
    print(f"\n{'=' * 70}")
    print("PROPOSED TOURNAMENT STRUCTURES")
    print(f"{'=' * 70}")

    group_proposals = {}
    innovations = []

    for s in successes:
        model = s["model"]
        r = s["result"]
        groups = r.get("proposed_groups", [])
        innovation = r.get("innovation", "")
        n_groups = len(groups)
        total_agents = r.get("total_agents_per_run", "?")
        reason = r.get("reason", "")[:120]

        print(f"\n--- {model} ({s['ms']}ms) ---")
        print(f"  Groups: {n_groups} | Agents/run: {total_agents}")
        print(f"  Reason: {reason}")

        for g in groups:
            gname = g.get("name", "?")
            models = g.get("models", [])
            topic = g.get("topic", "?")
            print(f"    [{gname}] ({topic}): {', '.join(str(m) for m in models[:5])}")

        if innovation:
            innovations.append({"model": model, "idea": innovation})
            print(f"  INNOVATION: {innovation[:150]}")

        rate_strat = r.get("rate_limit_strategy", "")
        if rate_strat:
            print(f"  Rate limit: {rate_strat[:120]}")

    # Innovation summary
    if innovations:
        print(f"\n{'=' * 70}")
        print(f"INNOVATION IDEAS ({len(innovations)} ideas from {len(successes)} models)")
        print(f"{'=' * 70}")
        for i, inn in enumerate(innovations, 1):
            print(f"\n  [{i}] {inn['model']}:")
            print(f"      {inn['idea'][:200]}")

    # Save full results
    out_path = Path(__file__).parent / "meta_15_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_models": len(providers),
            "successes": len(successes),
            "total_latency_ms": total_ms,
            "results": [s["result"] for s in successes],
            "innovations": innovations,
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    asyncio.run(run())
