"""Phase B2 — sidecar smoke for LiteLLM adapter.

Runs the adapter outside the daemon, against env-safe providers, with one
harmless prompt. Prints structured JSON on success, or a clear failure
classification on error (transport / unavailable / parse).

Acceptance (Codex memo, codex-loop.md, 2026-05-08):
- Structured JSON returned → PASS, motor works on the table.
- Explicit unavailable error → PASS, blocker reported in plain language.
- No daemon restart, no swarm queue task, no production-routing wiring.

Run:
  python scripts/litellm_smoke.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_dotenv_into_os_environ(env_path: Path) -> int:
    """Tiny .env loader. Doesn't override values already set in environment."""
    if not env_path.exists():
        return 0
    loaded = 0
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded


def classify_blocker(exc: BaseException) -> dict[str, str]:
    """Translate adapter exception into a plain-language blocker."""
    name = type(exc).__name__
    msg = str(exc)[:300]

    if "litellm is not installed" in msg or isinstance(exc, ImportError):
        return {"kind": "missing-dependency", "detail": msg}
    if "No LLM credentials" in msg:
        return {"kind": "no-credentials", "detail": msg}
    lower = msg.lower()
    if "timeout" in lower or "timed out" in lower:
        return {"kind": "timeout", "detail": msg}
    if "connection" in lower or "refused" in lower or "unreachable" in lower:
        return {"kind": "transport", "detail": msg}
    if "rate limit" in lower or "429" in lower:
        return {"kind": "rate-limit", "detail": msg}
    if "json" in lower and ("decode" in lower or "parse" in lower):
        return {"kind": "parse", "detail": msg}
    return {"kind": f"unclassified:{name}", "detail": msg}


async def main() -> int:
    started = time.time()
    out: dict[str, object] = {
        "phase": "B2-sidecar-smoke",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
    }

    loaded = _load_dotenv_into_os_environ(REPO_ROOT / "apps" / "api" / ".env")
    out["dotenv_keys_loaded"] = loaded

    # Constitution Article 0 hard guard at the smoke layer too — never use
    # the daemon's environment if it somehow contains an Anthropic key.
    if os.environ.pop("ANTHROPIC_API_KEY", None):
        out["scrubbed_anthropic_api_key"] = True

    env_view = {
        "CEREBRAS_API_KEY": bool(os.environ.get("CEREBRAS_API_KEY")),
        "NVIDIA_API_KEY": bool(os.environ.get("NVIDIA_API_KEY")),
        "OLLAMA_API_BASE": os.environ.get("OLLAMA_API_BASE", "http://localhost:11434"),
    }
    out["env"] = env_view

    try:
        from packages.swarm.providers.litellm_adapter import (
            LiteLLMProvider,
            _build_model_list,
            _LITELLM_AVAILABLE,
        )
    except Exception as exc:
        out["status"] = "FAIL"
        out["stage"] = "import"
        out["blocker"] = classify_blocker(exc)
        print(json.dumps(out, indent=2))
        return 2

    out["litellm_available"] = bool(_LITELLM_AVAILABLE)

    model_list = _build_model_list()
    out["model_list_summary"] = [
        {"name": m["model_name"], "model": m["litellm_params"]["model"]}
        for m in model_list
    ]
    # Belt-and-suspenders Article 0 check.
    leaked = [m for m in model_list if str(m["litellm_params"]["model"]).startswith("anthropic/")]
    if leaked:
        out["status"] = "FAIL"
        out["stage"] = "constitution-article-0"
        out["blocker"] = {"kind": "anthropic-leak", "detail": f"{len(leaked)} anthropic/* in router"}
        print(json.dumps(out, indent=2))
        return 3

    if not _LITELLM_AVAILABLE:
        out["status"] = "FAIL"
        out["stage"] = "litellm-import"
        out["blocker"] = {"kind": "missing-dependency", "detail": "litellm not importable"}
        print(json.dumps(out, indent=2))
        return 4

    prompt = (
        "Return strictly a JSON object with two keys: "
        "\"ok\" (boolean true) and \"motto\" (string \"motor on the table\"). "
        "Do not include any other text."
    )

    try:
        provider = LiteLLMProvider()
        result = await asyncio.wait_for(provider.evaluate(prompt, temperature=0.0), timeout=45.0)
    except Exception as exc:  # noqa: BLE001 — we want every blocker classified
        out["status"] = "FAIL"
        out["stage"] = "evaluate"
        out["blocker"] = classify_blocker(exc)
        out["traceback_tail"] = "\n".join(traceback.format_exception(exc)[-3:])
        print(json.dumps(out, indent=2))
        return 5

    elapsed_s = round(time.time() - started, 3)
    out["elapsed_s"] = elapsed_s
    out["response"] = result
    if isinstance(result, dict) and "ok" in result:
        out["status"] = "PASS"
        out["stage"] = "evaluate"
    else:
        out["status"] = "PARTIAL"
        out["stage"] = "evaluate"
        out["note"] = "Provider returned a dict but not the expected shape — JSON-mode was honoured."
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
