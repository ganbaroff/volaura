"""
Auto-discover ALL available models from all providers.
Tests each one with a simple JSON prompt. Keeps what works.
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

# Load .env from apps/api/.env (same pattern as all other swarm scripts)
_env_path = project_root / "apps" / "api" / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

TEST_PROMPT = """You are evaluating a simple test. Respond ONLY with valid JSON:
{"status": "ok", "model_works": true, "can_json": true}"""

# -------------------------------------------------------
# GROQ: list all models via API, test each
# -------------------------------------------------------
async def discover_groq(api_key: str) -> list[dict]:
    from groq import AsyncGroq
    client = AsyncGroq(api_key=api_key)

    # List all models
    print("\n[GROQ] Fetching model list...")
    models = await client.models.list()
    all_models = [m.id for m in models.data if m.id and "whisper" not in m.id and "tts" not in m.id and "vision" not in m.id.lower()]
    print(f"[GROQ] Found {len(all_models)} text models: {', '.join(sorted(all_models))}")

    # Test each in parallel
    results = await asyncio.gather(*[
        _test_groq(client, model_id) for model_id in all_models
    ], return_exceptions=True)

    working = []
    for model_id, result in zip(all_models, results):
        if isinstance(result, dict) and result.get("ok"):
            working.append(result)
            print(f"  [+] {model_id:45s} | {result['ms']:5d}ms | JSON OK")
        else:
            err = str(result)[:80] if isinstance(result, Exception) else result.get("error", "?")[:80] if isinstance(result, dict) else "?"
            print(f"  [x] {model_id:45s} | FAILED: {err}")

    return working


async def _test_groq(client, model_id: str) -> dict:
    start = time.monotonic()
    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": TEST_PROMPT}],
            temperature=0.1,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        ms = int((time.monotonic() - start) * 1000)
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        return {"ok": True, "model": model_id, "provider": "groq", "ms": ms, "response": parsed}
    except Exception as e:
        ms = int((time.monotonic() - start) * 1000)
        return {"ok": False, "model": model_id, "provider": "groq", "ms": ms, "error": str(e)[:200]}


# -------------------------------------------------------
# GEMINI: list models via API, test each
# -------------------------------------------------------
async def discover_gemini(api_key: str) -> list[dict]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    print("\n[GEMINI] Fetching model list...")
    models_response = await client.aio.models.list(config={"page_size": 100})
    all_models = []
    async for m in models_response:
        name = m.name.replace("models/", "") if m.name else ""
        if name and "embed" not in name and "aqa" not in name and "bison" not in name and "imagen" not in name:
            all_models.append(name)

    print(f"[GEMINI] Found {len(all_models)} generative models: {', '.join(sorted(all_models))}")

    results = await asyncio.gather(*[
        _test_gemini(client, model_id) for model_id in all_models
    ], return_exceptions=True)

    working = []
    for model_id, result in zip(all_models, results):
        if isinstance(result, dict) and result.get("ok"):
            working.append(result)
            print(f"  [+] {model_id:45s} | {result['ms']:5d}ms | JSON OK")
        else:
            err = str(result)[:80] if isinstance(result, Exception) else result.get("error", "?")[:80] if isinstance(result, dict) else "?"
            print(f"  [x] {model_id:45s} | FAILED: {err}")

    return working


async def _test_gemini(client, model_id: str) -> dict:
    from google.genai import types
    start = time.monotonic()
    try:
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=TEST_PROMPT,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=100,
            ),
        )
        ms = int((time.monotonic() - start) * 1000)
        raw = response.text.strip()
        parsed = json.loads(raw)
        return {"ok": True, "model": model_id, "provider": "gemini", "ms": ms, "response": parsed}
    except Exception as e:
        ms = int((time.monotonic() - start) * 1000)
        return {"ok": False, "model": model_id, "provider": "gemini", "ms": ms, "error": str(e)[:200]}


# -------------------------------------------------------
# DEEPSEEK: only has 2 models, test both
# -------------------------------------------------------
async def discover_deepseek(api_key: str) -> list[dict]:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    models = ["deepseek-chat", "deepseek-reasoner"]
    print(f"\n[DEEPSEEK] Testing {len(models)} models...")

    results = await asyncio.gather(*[
        _test_openai_compat(client, model_id, "deepseek") for model_id in models
    ], return_exceptions=True)

    working = []
    for model_id, result in zip(models, results):
        if isinstance(result, dict) and result.get("ok"):
            working.append(result)
            print(f"  [+] {model_id:45s} | {result['ms']:5d}ms | JSON OK")
        else:
            err = str(result)[:80] if isinstance(result, Exception) else result.get("error", "?")[:80] if isinstance(result, dict) else "?"
            print(f"  [x] {model_id:45s} | FAILED: {err}")

    return working


async def _test_openai_compat(client, model_id: str, provider: str) -> dict:
    start = time.monotonic()
    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": TEST_PROMPT}],
            temperature=0.1,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        ms = int((time.monotonic() - start) * 1000)
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        return {"ok": True, "model": model_id, "provider": provider, "ms": ms, "response": parsed}
    except Exception as e:
        ms = int((time.monotonic() - start) * 1000)
        return {"ok": False, "model": model_id, "provider": provider, "ms": ms, "error": str(e)[:200]}


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
async def main():
    print("=" * 70)
    print("MODEL DISCOVERY: Testing ALL available models from ALL providers")
    print("=" * 70)

    all_working: list[dict] = []

    groq_key = os.environ.get("GROQ_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")

    # Run all providers in parallel
    tasks = []
    if groq_key:
        tasks.append(("groq", discover_groq(groq_key)))
    if gemini_key:
        tasks.append(("gemini", discover_gemini(gemini_key)))
    if deepseek_key:
        tasks.append(("deepseek", discover_deepseek(deepseek_key)))

    results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

    for (name, _), result in zip(tasks, results):
        if isinstance(result, list):
            all_working.extend(result)
        elif isinstance(result, Exception):
            print(f"\n[{name.upper()}] Discovery failed: {result}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {len(all_working)} working models found")
    print(f"{'=' * 70}")

    # Sort by speed
    all_working.sort(key=lambda x: x["ms"])

    print(f"\n{'Model':45s} | {'Provider':10s} | {'Speed':>7s} | Family")
    print(f"{'-'*45} | {'-'*10} | {'-'*7} | {'-'*20}")
    for w in all_working:
        family = _guess_family(w["model"])
        print(f"{w['model']:45s} | {w['provider']:10s} | {w['ms']:5d}ms | {family}")

    # Save results
    out_path = Path(__file__).parent / "discovered_models.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_working, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {out_path}")

    # Recommend top 5-10 diverse models
    print(f"\n{'=' * 70}")
    print("RECOMMENDED: Top models by family diversity + speed")
    print(f"{'=' * 70}")
    seen_families: set[str] = set()
    recommended = []
    for w in all_working:
        family = _guess_family(w["model"])
        if family not in seen_families:
            seen_families.add(family)
            recommended.append(w)
            print(f"  [{len(recommended)}] {w['model']:40s} | {w['provider']:8s} | {w['ms']:5d}ms | {family}")
        if len(recommended) >= 8:
            break

    print(f"\n{len(recommended)} unique model families available for swarm diversity.")


def _guess_family(model: str) -> str:
    m = model.lower()
    if "llama" in m and "scout" in m: return "Meta-Llama4"
    if "llama-4" in m: return "Meta-Llama4"
    if "llama" in m: return "Meta-Llama3"
    if "qwen" in m: return "Alibaba-Qwen"
    if "gemini" in m: return "Google-Gemini"
    if "gemma" in m: return "Google-Gemma"
    if "gpt-oss" in m: return "OpenAI-OSS"
    if "deepseek" in m: return "DeepSeek"
    if "mistral" in m or "mixtral" in m: return "Mistral"
    if "kimi" in m: return "Moonshot-Kimi"
    if "compound" in m: return "Groq-Compound"
    return "Unknown"


if __name__ == "__main__":
    asyncio.run(main())
