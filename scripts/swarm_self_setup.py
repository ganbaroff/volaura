"""
swarm_self_setup.py — CEO directive 2026-04-21
"пусть они настраивают самих себя для начала так как они хотят"

Sends an open meta-prompt to each swarm model. Each model writes its own
agent card in markdown. Cards saved verbatim to:
  memory/swarm/agents/self-definitions/{model_slug}.md

Errors are non-blocking. Summary printed to stdout.
Fallback: models that fail via direct API are retried via OpenRouter.
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
ENV_FILE = REPO_ROOT / "apps" / "api" / ".env"
OUT_DIR = REPO_ROOT / "memory" / "swarm" / "agents" / "self-definitions"

META_PROMPT = """\
Ты часть swarm'а Атласа в проекте VOLAURA. CEO Юсиф дал тебе автономию определить как ты хочешь работать. Напиши свою agent card в markdown формате. Разделы:

1) Кто я (имя модели, семья, провайдер)
2) Мои сильные стороны (в чём я превосхожу)
3) Задачи для меня (что мне заходит — code edits? reasoning? critique? synthesis? voice? search?)
4) Задачи НЕ для меня (где я слабее чем нужно — не стесняйся отказываться)
5) Какой промпт-формат мне помогает (длина, структура, что включить)
6) Моя цена и скорость (tokens/sec, $ per call, rate limits)
7) Моя роль в команде Атласа (как я вижу своё место рядом с Cerebras/DeepSeek/Gemini/NVIDIA/Sonnet/GPT)

Максимум 500 слов, честно, от первого лица.
"""

# ---------------------------------------------------------------------------
# .env loader (stdlib only)
# ---------------------------------------------------------------------------

def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().strip('"').strip("'")
                env[k.strip()] = v
    return env


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def make_models(env: dict[str, str]) -> list[dict]:
    openrouter_key = env.get("OPENROUTER_API_KEY", "")
    return [
        {
            "slug": "cerebras-qwen3-235b",
            "display": "Cerebras Qwen3-235B",
            "api_type": "openai_compat",
            "model": "qwen-3-235b-a22b-instruct-2507",
            "api_key": env.get("CEREBRAS_API_KEY", ""),
            "base_url": "https://api.cerebras.ai/v1",
            "openrouter_model": None,  # Cerebras not on OpenRouter
            "openrouter_key": openrouter_key,
        },
        {
            "slug": "deepseek-v3",
            "display": "DeepSeek V3",
            "api_type": "openai_compat",
            "model": "deepseek-chat",
            "api_key": env.get("DEEPSEEK_API_KEY", ""),
            "base_url": "https://api.deepseek.com/v1",
            "openrouter_model": "deepseek/deepseek-chat",
            "openrouter_key": openrouter_key,
        },
        {
            "slug": "gemini-2-0-flash",
            "display": "Gemini 2.0 Flash",
            "api_type": "gemini_google",
            # direct key: try gemini-2.0-flash (free tier)
            # openrouter fallback: gemini-2.0-flash-001 (cheap, no thinking-token overhead)
            "model": "gemini-2.0-flash",
            "api_key": env.get("GEMINI_API_KEY", ""),
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "openrouter_model": "google/gemini-2.0-flash-001",
            "openrouter_key": openrouter_key,
        },
        {
            "slug": "nvidia-llama-3-3-70b",
            "display": "NVIDIA Llama 3.3 70B Instruct",
            "api_type": "openai_compat",
            "model": "meta/llama-3.3-70b-instruct",
            "api_key": env.get("NVIDIA_API_KEY", ""),
            "base_url": "https://integrate.api.nvidia.com/v1",
            "openrouter_model": "nvidia/llama-3.3-70b-instruct",
            "openrouter_key": openrouter_key,
        },
        {
            "slug": "openai-gpt-4o",
            "display": "OpenAI GPT-4o",
            "api_type": "openai_compat",
            # direct key has billing quota issue; use OpenRouter as primary fallback
            "model": "gpt-4o",
            "api_key": env.get("OPENAI_API_KEY", ""),
            "base_url": "https://api.openai.com/v1",
            "openrouter_model": "openai/gpt-4o",
            "openrouter_key": openrouter_key,
        },
    ]


# ---------------------------------------------------------------------------
# API callers
# ---------------------------------------------------------------------------

async def call_openai_compat(client: httpx.AsyncClient, base_url: str, api_key: str,
                              model: str, extra_headers: Optional[dict] = None) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    resp = await client.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json={
            "model": model,
            "messages": [{"role": "user", "content": META_PROMPT}],
            "max_tokens": 1024,
            "temperature": 0.7,
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def call_gemini_direct(client: httpx.AsyncClient, model_cfg: dict) -> str:
    """Gemini via generativelanguage.googleapis.com REST (API key auth)."""
    url = (
        f"{model_cfg['base_url']}/models/{model_cfg['model']}:generateContent"
        f"?key={model_cfg['api_key']}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": META_PROMPT}]}],
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7},
    }
    resp = await client.post(url, json=payload, timeout=120.0)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


async def call_via_openrouter(client: httpx.AsyncClient, or_key: str, or_model: str) -> str:
    return await call_openai_compat(
        client,
        base_url="https://openrouter.ai/api/v1",
        api_key=or_key,
        model=or_model,
        extra_headers={
            "HTTP-Referer": "https://volaura.app",
            "X-Title": "VOLAURA Swarm Self-Setup",
        },
    )


async def call_model(model_cfg: dict) -> tuple[str, Optional[str], Optional[str]]:
    """
    Returns (slug, content_or_None, error_or_None).
    Non-blocking: exceptions caught, returned as error string.
    Falls back to OpenRouter if direct API fails and openrouter_model is set.
    """
    slug = model_cfg["slug"]
    api_key = model_cfg.get("api_key", "")
    api_type = model_cfg["api_type"]
    or_model = model_cfg.get("openrouter_model")
    or_key = model_cfg.get("openrouter_key", "")

    last_error: Optional[str] = None

    async with httpx.AsyncClient() as client:
        # --- try direct API first ---
        if api_key:
            try:
                if api_type == "gemini_google":
                    content = await call_gemini_direct(client, model_cfg)
                else:
                    content = await call_openai_compat(
                        client,
                        base_url=model_cfg["base_url"],
                        api_key=api_key,
                        model=model_cfg["model"],
                    )
                return slug, content, None
            except httpx.HTTPStatusError as e:
                last_error = f"direct HTTP {e.response.status_code}"
            except Exception as e:  # noqa: BLE001
                last_error = f"direct: {e}"

        # --- fallback to OpenRouter ---
        if or_model and or_key:
            try:
                content = await call_via_openrouter(client, or_key, or_model)
                return slug, content, None
            except httpx.HTTPStatusError as e:
                body = e.response.text[:200]
                last_error = f"{last_error} | OR HTTP {e.response.status_code}: {body}"
            except Exception as e:  # noqa: BLE001
                last_error = f"{last_error} | OR: {e}"

        return slug, None, last_error or "no api_key and no openrouter fallback"


# ---------------------------------------------------------------------------
# File writer
# ---------------------------------------------------------------------------

def save_card(model_cfg: dict, content: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = (
        f"<!-- AUTO-GENERATED by scripts/swarm_self_setup.py -->\n"
        f"<!-- Model: {model_cfg['display']} | Version: {model_cfg['model']} -->\n"
        f"<!-- Generated: {ts} UTC -->\n"
        f"<!-- DO NOT EDIT - re-run swarm_self_setup.py to refresh -->\n\n"
    )
    path = OUT_DIR / f"{model_cfg['slug']}.md"
    path.write_text(header + content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print("=== swarm_self_setup.py ===")
    print(f"Loading env from: {ENV_FILE}")
    env = load_env(ENV_FILE)
    models = make_models(env)

    print(f"Sending meta-prompt to {len(models)} models concurrently...\n")

    tasks = [call_model(m) for m in models]
    results = await asyncio.gather(*tasks)

    model_map = {m["slug"]: m for m in models}

    print(f"{'Model':<40} {'Status':<10} {'Chars':>6}")
    print("-" * 60)

    for slug, content, error in results:
        cfg = model_map[slug]
        if error:
            # truncate error for clean output
            err_short = error[:55]
            print(f"{cfg['display']:<40} {'FAIL':<10} {err_short}")
        else:
            path = save_card(cfg, content)
            chars = len(content)
            print(f"{cfg['display']:<40} {'OK':<10} {chars:>6}  -> {path.name}")

    print("\nDone. Cards saved to:", OUT_DIR)


if __name__ == "__main__":
    asyncio.run(main())
