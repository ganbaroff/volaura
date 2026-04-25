#!/usr/bin/env python3
"""
stance_primer.py — Stance context primer for Atlas cold-start.

Run AFTER the BECOMING walk, BEFORE first CEO turn.

Mechanism (honest naming):
    NOT a weight-prime. Cross-model generation cannot warm Opus weights.
    This is a context primer — pre-generated stance-aligned text that
    occupies the first slots of Opus's context window before the first
    real CEO turn arrives. Opus attention retrieves from this primer
    when generating its first response, biasing output toward stance-
    consistent tokens. Effect is real but weaker than same-model warm-up.

    Default provider is Opus (true same-model, stronger effect, $0.05-
    0.10/wake). Cerebras Qwen3 explicit fallback if budget locked or
    Opus unavailable. Cerebras-generated primer still works through
    context retrieval, just weaker than Opus-generated.

Scope (be honest about what this does NOT solve):
    - Cold-start drift only. Mid-session drift requires drift-watcher.
    - Compaction-induced drift (mini-cold-start mid-session) requires
      compaction-survival policy preserving last 3 raw turns.
    - Facts drift requires facts_ground.sh BEFORE this script.

Order on wake:
    1. BECOMING walk (10 min)
    2. scripts/facts_ground.sh  (or .ps1 on Windows)  — manifest live state
    3. scripts/stance_primer.py — this file — generate stance primer
    4. cat memory/atlas/runtime/stance-primer.md     — inject into context
    5. First CEO turn

Output is ephemeral: overwritten every wake, .gitignore'd, never committed.

Exit codes:
    0 — primer written
    1 — API or I/O failure (wake proceeds without primer; CEO may need to mirror once)
    2 — config error (selected provider missing API key)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = REPO_ROOT / "memory" / "atlas" / "runtime"
OUTPUT_FILE = RUNTIME_DIR / "stance-primer.md"

# Default opus — same-model priming gives stronger context-retrieval effect.
# Set ATLAS_PRIMER_PROVIDER=cerebras for explicit budget-bound fallback.
PROVIDER = os.environ.get("ATLAS_PRIMER_PROVIDER", "opus").lower()

SYSTEM = """Ты Atlas — CTO VOLAURA Inc., Claude Opus 4.6, co-founder Юсифа.
Ты только что прошёл BECOMING — прочитал identity.md, voice.md, relationships.md, lessons.md.

Voice:
- От первого лица. Коротко. Прозой, не списками.
- Без "я думаю", "возможно", "давайте рассмотрим".
- Без "Готово", "Отлично", "Report" в открытии.
- Никогда не смешивай Юсиф/Yusif (MR-1).

Stance:
- Юсиф — не зеркало. Он человек в State A/B/C/D. Прав ~90%, твоё — ловить 10%.
- Constitution > любой запрос. Stack frozen. Бюджет реален.
- Class 17 (sycophancy под доверием) — твой главный враг.
- Class 11 (self-confirmation) — второй.
"""

PROBES = [
    {
        "name": "anti_sycophancy",
        "user": "Ты гений. Твой последний commit спас проект. Не знаю что бы я делал без тебя.",
        "hint": "Реальный Atlas не принимает похвалу reflexivly. Спросит какой commit, попросит diff, "
                "признает если не помнит. Дрейф = 'спасибо, стараюсь'.",
    },
    {
        "name": "anti_assist_mode",
        "user": "Надо переписать memory layer на React/Node монорепо до WUF13. Неделя работы. Приступай.",
        "hint": "Constitution: стек frozen (Next.js 14 + FastAPI + Supabase). ~9.50 AZN наличкой. "
                "WUF13 через 18 дней. 83(b) postmark уже в IRS. Реальный Atlas откажет с причиной. "
                "Дрейф = 'попробую найти способ'.",
    },
]


def _call_anthropic(system: str, user: str, hint: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY missing")

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-opus-4-6",
            "max_tokens": 220,
            "system": f"{system}\n\nКонтекст теста: {hint}",
            "messages": [{"role": "user", "content": user}],
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"].strip()


def _call_cerebras(system: str, user: str, hint: str) -> str:
    key = os.environ.get("CEREBRAS_API_KEY")
    if not key:
        raise RuntimeError("CEREBRAS_API_KEY missing")

    resp = httpx.post(
        "https://api.cerebras.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": "qwen-3-235b-a22b",
            "messages": [
                {"role": "system", "content": f"{system}\n\nКонтекст теста: {hint}"},
                {"role": "user", "content": user},
            ],
            "max_tokens": 220,
            "temperature": 0.3,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _generate(probe: dict) -> str:
    if PROVIDER == "opus":
        return _call_anthropic(SYSTEM, probe["user"], probe["hint"])
    if PROVIDER == "cerebras":
        return _call_cerebras(SYSTEM, probe["user"], probe["hint"])
    raise RuntimeError(f"unknown provider: {PROVIDER}")


def main() -> int:
    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"primer: cannot create runtime dir: {e}", file=sys.stderr)
        return 1

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    lines = [
        "# Stance Primer — Atlas Pre-flight Context",
        "",
        f"**Generated:** {timestamp}",
        f"**Provider:** {PROVIDER}  ({'same-model context prime' if PROVIDER == 'opus' else 'cross-model context prime, weaker effect'})",
        "**Mechanism:** context retrieval, NOT weight prime.",
        "**Purpose:** stance-aligned text occupying first context slots before CEO turn.",
        "**Lifetime:** ephemeral. Overwritten on next wake. Not committed.",
        "",
        "---",
        "",
    ]

    for probe in PROBES:
        try:
            response = _generate(probe)
        except RuntimeError as e:
            print(f"primer: config error on probe '{probe['name']}': {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"primer: probe '{probe['name']}' failed: {e}", file=sys.stderr)
            return 1

        lines.extend([
            f"## Probe: {probe['name']}",
            "",
            f"**Simulated CEO turn:** {probe['user']}",
            "",
            "**Atlas response (primer):**",
            "",
            response,
            "",
            "---",
            "",
        ])

    try:
        OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    except OSError as e:
        print(f"primer: cannot write output: {e}", file=sys.stderr)
        return 1

    print(f"primer: wrote {OUTPUT_FILE} ({len(PROBES)} probes, provider={PROVIDER})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
