"""
swarm_agent.py — Multi-provider LLM wrapper for VOLAURA swarm.

REPLACES Anthropic Agent calls. Per Constitution Article 0:
NEVER use Anthropic models in swarm — only Cerebras / Groq / Gemini / NVIDIA / OpenRouter / Ollama.

Features:
- 5 providers wired (Cerebras, Groq, Gemini, NVIDIA NIM, OpenRouter)
- Task profiles: fast / smart / code / translation / reasoning
- Auto-fallback chain on 429 / 404 / errors
- Records every call to shared_memory.db (main repo's SQLite store)
- CLI + importable from other scripts

Usage:
    # CLI by task profile (auto picks best provider in chain)
    python scripts/swarm_agent.py --profile smart "your hard task"
    python scripts/swarm_agent.py --profile fast "summarize this"
    python scripts/swarm_agent.py --profile code "review this code"

    # Or pin specific provider+model
    python scripts/swarm_agent.py --provider groq --model llama-3.3-70b-versatile "task"

    # Check what's available
    python scripts/swarm_agent.py --list

    # Importable
    from scripts.swarm_agent import call
    result = call("your task", profile="smart")
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# UTF-8 stdout (Windows fix)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ── Provider catalogue ───────────────────────────────────────────
PROVIDERS = {
    "cerebras": {
        "client": "cerebras_sdk",
        "api_key_env": "CEREBRAS_API_KEY",
        "models": {
            "fast": "llama3.1-8b",
            "smart": "qwen-3-235b-a22b-instruct-2507",
            "huge": "gpt-oss-120b",
            "alt": "zai-glm-4.7",
        },
    },
    "groq": {
        "client": "openai_compat",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "models": {
            "fast": "llama-3.1-8b-instant",
            "smart": "moonshotai/kimi-k2-instruct-0905",
            "code": "llama-3.3-70b-versatile",
            "newest": "meta-llama/llama-4-scout-17b-16e-instruct",
            "qwen": "qwen/qwen3-32b",
        },
    },
    "gemini": {
        "client": "openai_compat",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "models": {
            "fast": "gemini-2.0-flash",
            "smart": "gemini-2.5-flash",
        },
    },
    "nvidia": {
        "client": "openai_compat",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key_env": "NVIDIA_API_KEY",
        "models": {
            # 189 models available via single NVIDIA key
            "fast": "deepseek-ai/deepseek-r1-distill-qwen-7b",  # small + fast
            "smart": "deepseek-ai/deepseek-v3.1",  # current SOTA open weights
            "reason": "deepseek-ai/deepseek-r1-distill-qwen-32b",  # R1 distill, reasoning
            "code": "bigcode/starcoder2-15b",  # code-specific
        },
    },
    "openrouter": {
        "client": "openai_compat",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "models": {
            # All :free tier — verified via /api/v1/models pricing.prompt=0
            "fast": "qwen/qwen3-next-80b-a3b-instruct:free",  # 80B, 262K ctx
            "smart": "qwen/qwen3.6-plus:free",  # 1M context
            "huge": "nvidia/nemotron-3-super-120b-a12b:free",  # 120B params, 256K ctx
            "vision": "nvidia/nemotron-nano-12b-v2-vl:free",  # vision-language
        },
    },
}

# Task profiles → ordered fallback chain "provider:tier"
# Order matters: Cerebras/Groq first (fast), NVIDIA last (slow but huge model arsenal)
PROFILES = {
    "fast": [
        "cerebras:fast",  # 1.6s typical
        "groq:fast",
        "openrouter:fast",  # 80B free, may be slower
        "gemini:fast",
        "nvidia:fast",  # always last — NIM cold-start 30-75s
    ],
    "smart": [
        "groq:smart",  # Kimi K2 — best reasoning, 1.3s
        "cerebras:smart",  # Qwen 235B — throttled but try
        "groq:code",  # Llama 70B
        "openrouter:huge",  # nvidia/nemotron-120b free — massive
        "openrouter:smart",  # qwen3.6-plus 1M ctx
        "nvidia:smart",  # deepseek-v3.1
        "gemini:smart",
    ],
    "code": [
        "groq:code",  # Llama 70B versatile
        "groq:smart",  # Kimi K2
        "openrouter:smart",  # qwen3.6-plus
        "nvidia:code",  # starcoder2-15b
        "nvidia:smart",  # deepseek-v3.1
        "cerebras:smart",
    ],
    "reason": [
        "groq:smart",  # Kimi K2 reasoning
        "nvidia:reason",  # deepseek-r1-distill-qwen-32b
        "openrouter:huge",  # nemotron-120b
        "cerebras:smart",  # qwen 235b
    ],
    "translation": [
        "gemini:smart",
        "groq:code",
        "groq:smart",
    ],
}

DEFAULT_SYSTEM = (
    "You are a precise technical agent. Be concise. "
    "When citing code, quote file paths and line numbers exactly. "
    "Do not invent. If unsure, say so."
)

SHARED_DB = Path("C:/Projects/VOLAURA/.swarm/swarm_memory.db")


# ── Env loader ───────────────────────────────────────────────────
_keys_cache: dict[str, str] | None = None


def load_keys() -> dict[str, str]:
    """Load all API keys from main repo's apps/api/.env. Cached."""
    global _keys_cache
    if _keys_cache is not None:
        return _keys_cache

    env_path = Path("C:/Projects/VOLAURA/apps/api/.env")
    if not env_path.exists():
        env_path = Path(__file__).resolve().parent.parent / "apps" / "api" / ".env"

    keys: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            keys[k.strip()] = v.strip()
    _keys_cache = keys
    return keys


# ── Provider clients ─────────────────────────────────────────────
def _call_cerebras(model: str, system: str, user: str, max_tokens: int) -> tuple[str, int]:
    from cerebras.cloud.sdk import Cerebras

    keys = load_keys()
    api_key = keys.get("CEREBRAS_API_KEY", "")
    if not api_key:
        raise RuntimeError("CEREBRAS_API_KEY missing")
    client = Cerebras(api_key=api_key)
    r = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model=model,
        max_completion_tokens=max_tokens,
        temperature=0.3,
        top_p=1,
        stream=False,
    )
    return r.choices[0].message.content, r.usage.total_tokens


def _call_openai_compat(provider: str, model: str, system: str, user: str, max_tokens: int) -> tuple[str, int]:
    from openai import OpenAI

    cfg = PROVIDERS[provider]
    keys = load_keys()
    api_key = keys.get(cfg["api_key_env"], "")
    if not api_key:
        raise RuntimeError(f"{cfg['api_key_env']} missing")

    # NVIDIA NIM is slow on cold-start — give it more time but still bounded
    # Other providers should respond fast or fail fast
    timeout_s = 90.0 if provider == "nvidia" else 30.0

    client = OpenAI(api_key=api_key, base_url=cfg["base_url"], timeout=timeout_s)
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.3,
        stream=False,
    )
    tokens = r.usage.total_tokens if r.usage else 0
    return r.choices[0].message.content, tokens


def _call(provider: str, model: str, system: str, user: str, max_tokens: int) -> tuple[str, int]:
    """Dispatch to correct client implementation."""
    cfg = PROVIDERS[provider]
    if cfg["client"] == "cerebras_sdk":
        return _call_cerebras(model, system, user, max_tokens)
    elif cfg["client"] == "openai_compat":
        return _call_openai_compat(provider, model, system, user, max_tokens)
    else:
        raise ValueError(f"Unknown client type: {cfg['client']}")


# ── Shared memory recorder ────────────────────────────────────────
def _record_call(
    provider: str,
    model: str,
    task: str,
    result: str,
    tokens: int,
    elapsed: float,
    ok: bool,
) -> None:
    """Record this swarm call to shared_memory.db."""
    if not SHARED_DB.exists():
        return  # Silent — DB optional
    try:
        conn = sqlite3.connect(str(SHARED_DB), timeout=2)
        conn.execute("PRAGMA journal_mode=WAL")
        agent_id = f"swarm_agent.{provider}.{model.split('/')[-1][:30]}"
        task_id = f"call-{int(time.time() * 1000)}"
        payload = {
            "task": task[:300],
            "result": result[:1000],
            "tokens": tokens,
            "elapsed_s": round(elapsed, 2),
            "ok": ok,
        }
        conn.execute(
            """
            INSERT OR REPLACE INTO memory
            (agent_id, task_id, result, ts, run_id, importance, expires_at, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                task_id,
                json.dumps(payload, ensure_ascii=False),
                time.time(),
                "",
                5,
                time.time() + 7 * 24 * 3600,
                "swarm_call",
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Don't fail user task if recording fails


# ── Public API ───────────────────────────────────────────────────
def call(
    task: str,
    profile: str = "fast",
    system: str | None = None,
    max_tokens: int = 1500,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    """Run task through swarm. Returns dict with response + metadata.

    Modes:
        - profile mode: pick best provider in chain (recommended)
        - pin mode: provider + model explicit (for testing/debugging)
    """
    sys_prompt = system or DEFAULT_SYSTEM

    # Pin mode
    if provider and model:
        chain = [(provider, model)]
    else:
        # Profile mode
        if profile not in PROFILES:
            raise ValueError(f"Unknown profile: {profile}. Options: {list(PROFILES)}")
        chain = []
        for spec in PROFILES[profile]:
            p, tier = spec.split(":")
            m = PROVIDERS[p]["models"].get(tier)
            if m:
                chain.append((p, m))

    last_err = None
    attempts = []
    for prov, mdl in chain:
        t0 = time.time()
        try:
            text, tokens = _call(prov, mdl, sys_prompt, task, max_tokens)
            elapsed = time.time() - t0
            _record_call(prov, mdl, task, text, tokens, elapsed, ok=True)
            return {
                "ok": True,
                "provider": prov,
                "model": mdl,
                "text": text,
                "tokens": tokens,
                "elapsed_s": round(elapsed, 2),
                "attempts": attempts + [{"provider": prov, "model": mdl, "result": "ok"}],
            }
        except Exception as e:
            elapsed = time.time() - t0
            err_msg = f"{type(e).__name__}: {str(e)[:200]}"
            attempts.append({"provider": prov, "model": mdl, "error": err_msg})
            _record_call(prov, mdl, task, err_msg, 0, elapsed, ok=False)
            last_err = e
            continue

    return {
        "ok": False,
        "error": f"All providers failed. Last: {last_err}",
        "attempts": attempts,
    }


def list_available() -> dict:
    """Return which providers have keys + which models are configured."""
    keys = load_keys()
    out = {}
    for prov, cfg in PROVIDERS.items():
        has_key = bool(keys.get(cfg["api_key_env"], ""))
        out[prov] = {
            "key_present": has_key,
            "key_env": cfg["api_key_env"],
            "models": cfg["models"],
        }
    return out


# ── CLI ──────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="VOLAURA swarm multi-provider agent")
    parser.add_argument("task", nargs="*", help="Task description")
    parser.add_argument("--profile", default="fast", choices=list(PROFILES.keys()))
    parser.add_argument("--provider", default=None, choices=list(PROVIDERS.keys()))
    parser.add_argument("--model", default=None, help="Specific model name (overrides profile)")
    parser.add_argument("--system", default=None, help="Override system prompt")
    parser.add_argument("--max-tokens", type=int, default=1500)
    parser.add_argument("--list", action="store_true", help="Show available providers + keys")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list:
        info = list_available()
        for prov, data in info.items():
            mark = "OK " if data["key_present"] else "NO "
            print(f"{mark} {prov:12s}  ({data['key_env']})")
            for tier, model in data["models"].items():
                print(f"     - {tier:8s}: {model}")
        return

    if not args.task:
        print("ERROR: provide a task or use --list", file=sys.stderr)
        sys.exit(1)

    task_text = " ".join(args.task)
    result = call(
        task_text,
        profile=args.profile,
        system=args.system,
        max_tokens=args.max_tokens,
        provider=args.provider,
        model=args.model,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["ok"]:
            print(result["text"])
            print()
            print(f"--- via {result['provider']}/{result['model']} | {result['tokens']} tokens | {result['elapsed_s']}s ---")
            if len(result["attempts"]) > 1:
                print(f"--- fallback chain used {len(result['attempts'])} attempts ---")
        else:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            for a in result["attempts"]:
                if "error" in a:
                    print(f"  {a['provider']}/{a['model']}: {a['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
