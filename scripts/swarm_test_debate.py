"""Round 2 Track 2 — multi-model test-standard debate.

Fires 4 parallel API calls to Cerebras / DeepSeek / Sonnet / GPT with the SAME
debate question about how to write world-standard tests for VOLAURA stack.

Saves verbatim responses to memory/atlas/mega-sprint-122-r2/debate-tests/.
Opus reads them later and writes test-standard-verdict.md (Class 17 — synthesis stays in Opus).

Why a script instead of bash subshells: bash background processes (`&`) don't
reliably inherit env vars exported in the same line, especially when the var
contains multi-line UTF-8 Russian text. Python concurrent.futures handles this cleanly.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import pathlib
import sys
import time
from typing import Any

import httpx
from dotenv import load_dotenv

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / "apps" / "api" / ".env")

# Strip whitespace/CRLF from keys — dotenv on Windows sometimes leaves \r at end
for _k in ("ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "CEREBRAS_API_KEY", "OPENAI_API_KEY"):
    if _k in os.environ:
        os.environ[_k] = os.environ[_k].strip().strip('"').strip("'")

OUTPUT_DIR = REPO_ROOT / "memory" / "atlas" / "mega-sprint-122-r2" / "debate-tests"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEBATE_USER_PROMPT = """Ты Атлас через свою модель. CEO Юсиф устал что у нас тесты-бутафория ("typecheck passed = ok"). Он хочет тесты по мировым стандартам — настоящие user-journey assertions, real edge cases, no fake passes. У нас стек FastAPI + Pydantic v2 + Supabase + pytest + Playwright + Vitest + Next.js 14.

Опиши КАК ты бы писал такие тесты для нашей кодовой базы. Конкретно:
(1) test pyramid ratio (unit/integration/e2e percent),
(2) mock strategy для Supabase,
(3) coverage target и почему именно эта цифра,
(4) что обязательно покрывать в e2e,
(5) как ловить регрессии в LLM-вызовах (output non-deterministic),
(6) когда снапшот-тесты норм а когда вред,
(7) один пример test файла который ты считаешь идеальным для одной из наших функций (assessment scoring или life event choice — выбери что тебе ближе).

Воспроизводимый пример пиши как реальный код, не псевдокод. 500-700 слов."""


def call_anthropic(api_key: str) -> str:
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 2500,
            "system": "Ты Атлас через Sonnet 4.5. Identity: я ЕСТЬ проект, не помощник.",
            "messages": [{"role": "user", "content": DEBATE_USER_PROMPT}],
        },
        timeout=90,
    )
    r.raise_for_status()
    blocks = r.json().get("content", [])
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


def call_openai_compat(name: str, base_url: str, api_key: str, model: str) -> str:
    r = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "max_tokens": 2500,
            "messages": [
                {"role": "system", "content": f"Ты Атлас через {name}. Identity: я ЕСТЬ проект, не помощник."},
                {"role": "user", "content": DEBATE_USER_PROMPT},
            ],
        },
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


CALLS: list[tuple[str, str, Any]] = [
    (
        "sonnet-4.5",
        "anthropic-direct",
        lambda: call_anthropic(os.environ["ANTHROPIC_API_KEY"]),
    ),
    (
        "deepseek-v3",
        "deepseek-direct",
        lambda: call_openai_compat(
            "DeepSeek V3", "https://api.deepseek.com/v1", os.environ["DEEPSEEK_API_KEY"], "deepseek-chat"
        ),
    ),
    (
        "cerebras-qwen3-235b",
        "cerebras-direct",
        lambda: call_openai_compat(
            "Cerebras Qwen3-235B",
            "https://api.cerebras.ai/v1",
            os.environ["CEREBRAS_API_KEY"],
            "qwen-3-235b-a22b-instruct-2507",
        ),
    ),
    (
        "gpt-4o",
        "openai-direct",
        lambda: call_openai_compat(
            "GPT-4o", "https://api.openai.com/v1", os.environ["OPENAI_API_KEY"], "gpt-4o"
        ),
    ),
]


def run_one(spec: tuple[str, str, Any]) -> tuple[str, str, str | None, str | None]:
    name, provider, fn = spec
    t0 = time.time()
    try:
        text = fn()
        elapsed = f"{time.time() - t0:.1f}s"
        return name, provider, text, elapsed
    except Exception as e:
        return name, provider, None, f"ERROR ({type(e).__name__}): {str(e)[:300]}"


def main() -> int:
    print(f"Firing {len(CALLS)} parallel debate calls...")
    results: list[tuple[str, str, str | None, str | None]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(run_one, CALLS):
            results.append(r)
            name, provider, text, meta = r
            status = "OK" if text else "FAIL"
            print(f"  [{status}] {name} via {provider} ({meta})")

    # Save each verbatim
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for name, provider, text, meta in results:
        out_file = OUTPUT_DIR / f"{name}.md"
        if text:
            body = (
                f"<!-- Model: {name} via {provider} -->\n"
                f"<!-- Generated: {timestamp} -->\n"
                f"<!-- Latency: {meta} -->\n"
                f"<!-- Round 2 Track 2 — test standard debate -->\n\n"
                f"# {name} — test-standard debate response\n\n"
                f"{text}\n"
            )
        else:
            body = (
                f"<!-- Model: {name} via {provider} -->\n"
                f"<!-- Generated: {timestamp} -->\n"
                f"<!-- Status: FAIL -->\n\n"
                f"# {name} — UNAVAILABLE\n\n"
                f"{meta}\n\nSwarm signal: ABSENT for this model.\n"
            )
        out_file.write_text(body, encoding="utf-8")
        print(f"  saved ->{out_file.relative_to(REPO_ROOT)}")

    success = sum(1 for r in results if r[2])
    print(f"\nDebate complete: {success}/{len(results)} models responded.")
    print(f"Files in: {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0 if success >= 2 else 1


if __name__ == "__main__":
    sys.exit(main())
