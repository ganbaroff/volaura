"""Independent adversarial critique runner — Anthropic API only.

Used by Cowork-Atlas (sandbox-restricted to api.anthropic.com) to spawn
multi-persona red-team critique on a target document. Each persona gets
a FRESH context — no parent-context bleed (the failure mode of Agent-tool
subagents that returned "Prompt is too long" on trivial prompts).

Stdlib-only. No external deps. Reads ANTHROPIC_API_KEY from apps/api/.env
or environment. Writes one .md per persona + synthesis-input.json.

Usage:
    python scripts/critique.py \\
        --target docs/research/az-capital-crisis-2026/01-macro-scenarios.md \\
        --personas macro-economist,geopolitical-analyst \\
        --out docs/research/az-capital-crisis-2026/critiques \\
        --model opus

Personas: see scripts/critique_personas/*.md (one file per persona).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_TIMEOUT = 300.0
MAX_RETRIES = 3
COST_CEILING_USD = 3.0  # abort batch if estimated above

# Per-million pricing (USD) — claude.ai/api docs 2026-Q1
PRICING = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
}

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "scripts" / "critique_personas"
ENV_FILE = REPO_ROOT / "apps" / "api" / ".env"


def _load_env_key() -> str:
    """Read ANTHROPIC_API_KEY from environment first, then .env file.

    Handles CRLF in .env (strips \\r before parse) per INC-XXX 2026-04-14.
    """
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    if not ENV_FILE.exists():
        return ""
    try:
        text = ENV_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""
    text = text.replace("\r", "")
    for line in text.splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _load_persona(name: str) -> str:
    """Load persona system prompt from scripts/critique_personas/<name>.md."""
    path = PERSONAS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Persona file not found: {path}")
    return path.read_text(encoding="utf-8")


def _build_user_prompt(target_text: str, persona_name: str) -> str:
    """Wrap target document with red-team instructions."""
    return f"""# Target document for red-team critique

```markdown
{target_text}
```

# Your task

You are the {persona_name} persona. Apply your discipline rigorously to the document above. Identify:

1. The strongest argument against the document's central claim
2. The single most overlooked attack vector
3. The methodological weaknesses in evidence selection
4. Specific data, numbers, or assumptions that are wrong or unsupported

# Required output structure

End your critique with these mandatory sections:

## TOP_ATTACK
One paragraph naming the single strongest reason this document is wrong, weak, or misleading. Concrete and specific.

## FINAL_A
The strongest argument FOR the document's main thesis (steelman).

## FINAL_B
The strongest argument AGAINST the document's main thesis.

## FINAL_C
The most likely scenario the document fails to consider.

## FINAL_D
What evidence would change your verdict.

Total response length: 3000-5000 characters. Direct, no fluff, no apologies. Cite specific lines from the document where possible."""


def _post_anthropic(api_key: str, model: str, system: str, user: str, max_tokens: int = 3000) -> dict:
    """Single Anthropic API call with retry on 429/500/overloaded."""
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
        "User-Agent": "volaura-critique/1.0",
    }
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(ANTHROPIC_URL, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_text = ""
            try:
                err_text = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            if e.code in (429, 500, 502, 503, 529) and attempt < MAX_RETRIES - 1:
                wait = (2 ** attempt) * 5
                print(f"  [retry {attempt + 1}/{MAX_RETRIES}] HTTP {e.code} — wait {wait}s — {err_text[:200]}", file=sys.stderr)
                time.sleep(wait)
                last_err = f"HTTP {e.code}: {err_text}"
                continue
            raise RuntimeError(f"Anthropic HTTP {e.code}: {err_text}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < MAX_RETRIES - 1:
                wait = (2 ** attempt) * 5
                print(f"  [retry {attempt + 1}/{MAX_RETRIES}] {type(e).__name__} — wait {wait}s", file=sys.stderr)
                time.sleep(wait)
                last_err = str(e)
                continue
            raise
    raise RuntimeError(f"All retries exhausted: {last_err}")


def _calculate_cost(usage: dict, model: str) -> float:
    """USD cost from API usage block."""
    rates = PRICING.get(model, PRICING["claude-sonnet-4-6"])
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


def _critique_one(api_key: str, model: str, persona_name: str, target_text: str, out_dir: Path) -> dict:
    """Run one persona critique. Returns dict with status, cost, tokens, error."""
    out_path = out_dir / f"{persona_name}.md"
    err_path = out_dir / f"{persona_name}.err"
    started = time.time()
    try:
        system = _load_persona(persona_name)
        user = _build_user_prompt(target_text, persona_name)
        result = _post_anthropic(api_key, model, system, user)
        content = "".join(block.get("text", "") for block in result.get("content", []) if block.get("type") == "text")
        usage = result.get("usage", {})
        cost = _calculate_cost(usage, model)
        out_path.write_text(content, encoding="utf-8")
        return {
            "persona": persona_name,
            "status": "ok",
            "duration_s": round(time.time() - started, 1),
            "cost_usd": round(cost, 4),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "output_path": str(out_path.relative_to(REPO_ROOT)),
            "char_count": len(content),
            "top_attack": _extract_section(content, "TOP_ATTACK"),
        }
    except Exception as e:
        err_path.write_text(f"ERROR: {type(e).__name__}: {e}\n", encoding="utf-8")
        return {
            "persona": persona_name,
            "status": "error",
            "duration_s": round(time.time() - started, 1),
            "cost_usd": 0.0,
            "error": f"{type(e).__name__}: {str(e)[:300]}",
            "error_path": str(err_path.relative_to(REPO_ROOT)),
        }


def _extract_section(content: str, section_name: str) -> str:
    """Extract markdown section by header (## SECTION_NAME) up to next header or EOF."""
    pattern = rf"##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, content, flags=re.DOTALL)
    return m.group(1).strip()[:500] if m else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent adversarial critique runner (Anthropic API)")
    parser.add_argument("--target", required=True, help="Path to target .md file")
    parser.add_argument("--personas", required=True, help="Comma-separated persona names (see scripts/critique_personas/)")
    parser.add_argument("--out", required=True, help="Output directory for per-persona .md + synthesis-input.json")
    parser.add_argument("--model", default="sonnet", choices=["opus", "sonnet"], help="opus = claude-opus-4-6, sonnet = claude-sonnet-4-6")
    parser.add_argument("--workers", type=int, default=4, help="Parallel API workers (default 4)")
    parser.add_argument("--dry-run", action="store_true", help="Estimate cost only, no API calls")
    args = parser.parse_args()

    api_key = _load_env_key()
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not in env or apps/api/.env", file=sys.stderr)
        return 2

    target_path = Path(args.target)
    if not target_path.exists():
        print(f"ERROR: target not found: {target_path}", file=sys.stderr)
        return 2

    target_text = target_path.read_text(encoding="utf-8")
    personas = [p.strip() for p in args.personas.split(",") if p.strip()]
    if not personas:
        print("ERROR: no personas specified", file=sys.stderr)
        return 2

    model_id = "claude-opus-4-6" if args.model == "opus" else "claude-sonnet-4-6"
    rates = PRICING[model_id]
    # Conservative cost estimate: assume 5K input + 4K output per persona
    est_cost_per = (5000 * rates["input"] + 4000 * rates["output"]) / 1_000_000
    est_total = est_cost_per * len(personas)
    print(f"Cost estimate: ~${est_cost_per:.3f}/persona × {len(personas)} = ~${est_total:.2f} total")

    if est_total > COST_CEILING_USD:
        print(f"ABORT: estimate ${est_total:.2f} exceeds ceiling ${COST_CEILING_USD}", file=sys.stderr)
        return 3

    if args.dry_run:
        print("Dry-run mode — exiting before API calls")
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Validate all persona files exist before spending money
    for p in personas:
        if not (PERSONAS_DIR / f"{p}.md").exists():
            print(f"ERROR: persona file missing: scripts/critique_personas/{p}.md", file=sys.stderr)
            return 2

    started = time.time()
    print(f"Starting {len(personas)} critiques in parallel (workers={args.workers}, model={model_id})...")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_critique_one, api_key, model_id, p, target_text, out_dir): p for p in personas}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            status = "OK" if r["status"] == "ok" else "ERR"
            print(f"  [{status}] {r['persona']:30s} {r.get('duration_s', 0)}s  ${r.get('cost_usd', 0):.4f}")

    # Synthesis input
    synthesis = {
        "target": str(target_path.relative_to(REPO_ROOT)),
        "model": model_id,
        "started_at": datetime.now(UTC).isoformat(),
        "duration_s": round(time.time() - started, 1),
        "total_cost_usd": round(sum(r.get("cost_usd", 0) for r in results), 4),
        "personas": results,
        "attack_vectors": [r.get("top_attack", "") for r in results if r.get("status") == "ok"],
    }
    synthesis_path = out_dir / "synthesis-input.json"
    synthesis_path.write_text(json.dumps(synthesis, indent=2, ensure_ascii=False), encoding="utf-8")

    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"\nDone. {ok_count}/{len(results)} critiques succeeded. Total cost: ${synthesis['total_cost_usd']:.4f}")
    print(f"Synthesis input: {synthesis_path}")
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
