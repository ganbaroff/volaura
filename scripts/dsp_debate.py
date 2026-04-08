"""
dsp_debate.py — Decision Simulation Process: 3 models propose, then critique each other.

Replaces single-model agent calls. Forces diverse perspectives.
Per Constitution: never Anthropic in swarm — only Cerebras / Groq / Gemini / etc.

Round 1: 3 models independently propose solutions to a task
Round 2: Each model critiques the OTHER 2 proposals (cross-critique)
Output: All proposals + all critiques printed for human synthesis

Usage:
    python scripts/dsp_debate.py --task "task description" --context "code or context"

    # With custom file context:
    python scripts/dsp_debate.py --task "fix this bug" --context-file path/to/code.tsx
"""

from __future__ import annotations

import argparse
import concurrent.futures
import io
import os
import sys
import time
from pathlib import Path

# UTF-8 stdout (Windows fix)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ── Provider configs ──────────────────────────────────────────────
PARTICIPANTS = [
    {
        "name": "Cerebras-Llama8B",
        "provider": "cerebras",
        "model": "llama3.1-8b",
        "lens": "speed and pragmatic minimalism",
    },
    {
        "name": "Groq-Llama70B",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "lens": "thorough analysis and edge cases",
    },
    {
        "name": "Groq-KimiK2",
        "provider": "groq",
        "model": "moonshotai/kimi-k2-instruct-0905",
        "lens": "deep reasoning and architectural impact",
    },
]


def load_keys() -> dict[str, str]:
    """Load API keys from apps/api/.env."""
    env_path = Path(__file__).resolve().parent.parent / "apps" / "api" / ".env"
    if not env_path.exists():
        env_path = Path("C:/Projects/VOLAURA/apps/api/.env")
    keys = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            keys[k.strip()] = v.strip()
    return keys


def call_model(participant: dict, system: str, user: str, max_tokens: int = 1500) -> tuple[str, float, int]:
    """Call one provider/model. Returns (response_text, elapsed_seconds, total_tokens)."""
    keys = load_keys()
    t0 = time.time()

    if participant["provider"] == "cerebras":
        from cerebras.cloud.sdk import Cerebras
        client = Cerebras(api_key=keys["CEREBRAS_API_KEY"])
        r = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            model=participant["model"],
            max_completion_tokens=max_tokens,
            temperature=0.3,
            top_p=1,
            stream=False,
        )
        return r.choices[0].message.content, time.time() - t0, r.usage.total_tokens

    elif participant["provider"] == "groq":
        from openai import OpenAI
        client = OpenAI(api_key=keys["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
        r = client.chat.completions.create(
            model=participant["model"],
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            stream=False,
        )
        return r.choices[0].message.content, time.time() - t0, r.usage.total_tokens

    elif participant["provider"] == "gemini":
        from openai import OpenAI
        client = OpenAI(api_key=keys["GEMINI_API_KEY"], base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        r = client.chat.completions.create(
            model=participant["model"],
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            stream=False,
        )
        return r.choices[0].message.content, time.time() - t0, r.usage.total_tokens

    else:
        raise ValueError(f"Unknown provider: {participant['provider']}")


def round1_propose(task: str, context: str) -> list[dict]:
    """Each model independently proposes a solution."""
    system = """You are a senior engineer. The task: review the bug + propose ONE concrete fix.
Output format (4 sections, no marketing):
ROOT CAUSE: 1 sentence
FIX (the change): exact code diff or before/after
WHY THIS FIX: 2 sentences
ALTERNATIVES CONSIDERED: 1 sentence on what you rejected and why
RISK: 1 sentence on what could go wrong
Be concrete. Quote line numbers when possible. No filler."""

    user = f"TASK: {task}\n\nCONTEXT:\n```\n{context}\n```"

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(PARTICIPANTS)) as ex:
        futures = {
            ex.submit(call_model, p, system, user, 1200): p for p in PARTICIPANTS
        }
        for f in concurrent.futures.as_completed(futures):
            p = futures[f]
            try:
                text, elapsed, tokens = f.result()
                results.append({
                    "name": p["name"],
                    "lens": p["lens"],
                    "text": text,
                    "elapsed": elapsed,
                    "tokens": tokens,
                    "ok": True,
                })
            except Exception as e:
                results.append({
                    "name": p["name"],
                    "lens": p["lens"],
                    "text": f"ERROR: {e}",
                    "elapsed": 0,
                    "tokens": 0,
                    "ok": False,
                })
    # Sort by name for stable order
    results.sort(key=lambda r: r["name"])
    return results


def round2_critique(proposals: list[dict], task: str) -> list[dict]:
    """Each model critiques the OTHER 2 proposals."""
    system = """You are a senior engineer reviewing two peer proposals.
Be brutally honest. No soft language. No "great idea but..."
Output format (3 sections):
PROPOSAL A WEAKNESSES: bullet list, max 3 items
PROPOSAL B WEAKNESSES: bullet list, max 3 items
WINNER: A or B (one word) + one-sentence reason
If both have fatal flaws, say "BOTH BROKEN" and propose your own 3-line fix."""

    results = []

    def critique_for(participant: dict) -> dict:
        # Get the OTHER 2 proposals
        others = [p for p in proposals if p["name"] != participant["name"] and p["ok"]]
        if len(others) < 2:
            return {"name": participant["name"], "text": "skipped (not enough peers)", "ok": False, "elapsed": 0, "tokens": 0}
        prop_a, prop_b = others[0], others[1]
        user = (
            f"TASK: {task}\n\n"
            f"=== PROPOSAL A (from {prop_a['name']}) ===\n{prop_a['text']}\n\n"
            f"=== PROPOSAL B (from {prop_b['name']}) ===\n{prop_b['text']}\n\n"
            f"Now critique both. Pick a winner. Be brutal."
        )
        try:
            text, elapsed, tokens = call_model(participant, system, user, 800)
            return {
                "name": participant["name"],
                "text": text,
                "elapsed": elapsed,
                "tokens": tokens,
                "ok": True,
            }
        except Exception as e:
            return {
                "name": participant["name"],
                "text": f"ERROR: {e}",
                "elapsed": 0,
                "tokens": 0,
                "ok": False,
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(PARTICIPANTS)) as ex:
        futures = [ex.submit(critique_for, p) for p in PARTICIPANTS]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
    results.sort(key=lambda r: r["name"])
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="DSP debate: 3 models propose + cross-critique")
    parser.add_argument("--task", required=True, help="Task description")
    parser.add_argument("--context", default="", help="Code or context as string")
    parser.add_argument("--context-file", default=None, help="Path to file containing context")
    args = parser.parse_args()

    context = args.context
    if args.context_file:
        context = Path(args.context_file).read_text(encoding="utf-8")

    print("=" * 70)
    print(f"DSP DEBATE — TASK: {args.task[:120]}")
    print(f"Participants: {', '.join(p['name'] for p in PARTICIPANTS)}")
    print("=" * 70)
    print()

    print("ROUND 1: PROPOSALS (each model proposes independently)")
    print("-" * 70)
    proposals = round1_propose(args.task, context)
    for p in proposals:
        print(f"\n### {p['name']} ({p['lens']}) — {p['elapsed']:.1f}s, {p['tokens']} tokens")
        print(p["text"])
        print()

    print()
    print("=" * 70)
    print("ROUND 2: CROSS-CRITIQUE (each model critiques the other 2)")
    print("-" * 70)
    critiques = round2_critique(proposals, args.task)
    for c in critiques:
        print(f"\n### {c['name']} critique — {c['elapsed']:.1f}s, {c['tokens']} tokens")
        print(c["text"])
        print()

    print()
    print("=" * 70)
    total_tokens = sum(r["tokens"] for r in proposals + critiques if r["ok"])
    total_time = max(r["elapsed"] for r in proposals if r["ok"]) + max(r["elapsed"] for r in critiques if r["ok"])
    print(f"DEBATE COMPLETE — total tokens: {total_tokens}, max wall-clock: {total_time:.1f}s")
    print("Human (CTO/Opus) now synthesizes final decision.")
    print("=" * 70)


if __name__ == "__main__":
    main()
