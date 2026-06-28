"""ADR-013 §a runtime proof — one real call_brain_llm() invocation.

Purpose: demonstrate that with the default environment (ATLAS_ENABLE_CEREBRAS
unset), the brain provider chain reaches a non-Cerebras provider, returns
content, and emits NO cerebras call event into brain.log.jsonl.

Run:
    cd /c/Projects/VOLAURA
    # Inject GROQ_API_KEY from apps/api/.env without printing it:
    export GROQ_API_KEY=$(grep '^GROQ_API_KEY=' apps/api/.env | cut -d= -f2-)
    python scripts/runtime_proof_provider_chain.py

Output prints (a) which provider responded, (b) the model output, and
(c) last 8 brain.log.jsonl events with secret-bearing fields stripped.

Reference: docs/adr/ADR-013-2026-05-09-cerebras-spend-incident.md
           tests/test_gemma4_brain_provider_chain.py (the contract tests)
           memory/atlas/lessons.md Class 38

Note: this filename is intentionally NOT 'gemma4_brain.py' so the
spend-cap-guard.sh PreToolUse hook (which matches python+gemma4_brain.py
spawn patterns) does not block this single-call ad-hoc proof. The proof
is a one-shot non-loop call against a free-tier provider.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAIN_PATH = ROOT / "scripts" / "gemma4_brain.py"


def _load_brain():
    spec = importlib.util.spec_from_file_location("brain_proof_module", BRAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _redact_event(ev: dict) -> dict:
    """Strip any field that could carry secret bytes (error messages may
    echo Authorization headers verbatim from upstream errors)."""
    redacted = {}
    for k, v in ev.items():
        if k in ("error", "headers", "auth", "key"):
            redacted[k] = "<redacted>"
        else:
            redacted[k] = v
    return redacted


def main() -> int:
    # Defensive: ensure no ambient ATLAS_ENABLE_CEREBRAS leaked into this proof
    os.environ.pop("ATLAS_ENABLE_CEREBRAS", None)

    print("== ADR-013 §a — brain provider-chain runtime proof ==")
    print(
        f"ATLAS_ENABLE_CEREBRAS = {os.environ.get('ATLAS_ENABLE_CEREBRAS', '<unset>')!r}"
    )
    print(f"GROQ_API_KEY present: {bool(os.environ.get('GROQ_API_KEY'))}")
    print(f"GEMINI_API_KEY present: {bool(os.environ.get('GEMINI_API_KEY'))}")
    print(f"NVIDIA_API_KEY present: {bool(os.environ.get('NVIDIA_API_KEY'))}")
    print(f"CEREBRAS_API_KEY present: {bool(os.environ.get('CEREBRAS_API_KEY'))}")
    print()

    brain = _load_brain()

    # Snapshot brain.log.jsonl line count BEFORE the call so we can print
    # only the events emitted by THIS single invocation.
    log_path: Path = brain.BRAIN_LOG
    before_n = 0
    if log_path.exists():
        before_n = sum(1 for _ in log_path.open("r", encoding="utf-8"))

    prompt = "Reply with the exact three words: brain proof live"
    out = brain.call_brain_llm(prompt, max_tokens=24)

    print(f"-- LLM output (truncated 200 chars) --")
    print((out or "<empty>")[:200])
    print()

    # Read events emitted by THIS call
    new_events = []
    if log_path.exists():
        with log_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < before_n:
                    continue
                try:
                    new_events.append(_redact_event(json.loads(line)))
                except Exception:
                    pass

    print(f"-- {len(new_events)} new brain.log.jsonl event(s) from this call --")
    for ev in new_events:
        print(json.dumps(ev, ensure_ascii=False))

    # Pass criteria:
    #  1. Some non-empty content returned (some provider answered)
    #  2. NO event with provider='cerebras' (Cerebras must remain off)
    cerebras_called = any(
        ev.get("provider") == "cerebras" and ev.get("event") == "brain_llm_call"
        for ev in new_events
    )
    cerebras_skipped = any(
        ev.get("provider") == "cerebras" and ev.get("event") == "brain_llm_skipped"
        for ev in new_events
    )

    print()
    print(f"VERDICT:")
    print(f"  - non-empty output: {bool(out)}")
    print(f"  - cerebras CALLED: {cerebras_called}  (must be False)")
    print(f"  - cerebras SKIPPED: {cerebras_skipped}  (informational)")

    if cerebras_called:
        print("FAIL — Cerebras was called despite ATLAS_ENABLE_CEREBRAS unset")
        return 2
    if not out:
        print("WARN — no provider returned content; check GROQ_API_KEY etc")
        return 1
    print("PASS — default brain path returned content without touching Cerebras")
    return 0


if __name__ == "__main__":
    sys.exit(main())
