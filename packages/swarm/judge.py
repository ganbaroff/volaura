"""Independent LLM-judge for swarm proposals.

Reads memory/swarm/proposals.json, finds entries with status=pending and
judge_score=None, scores each via a model from a DIFFERENT family than the
generating agent, and writes the score back atomically.

Closes the swarm learning loop together with `distiller.py` (weekly).

CLI:
    python -m packages.swarm.judge [--limit N] [--dry-run]

Provider rotation:
    Default judge: NVIDIA Llama 3.3 (free, balanced reasoning, not used by
    most proposing agents). Falls back via llm_router (Cerebras → Groq →
    Ollama → Gemini) if NVIDIA missing or fails.

Constraints (Atlas operating principles + project rules):
    - Pydantic v2, loguru, UTF-8 explicit, no print().
    - Atomic file writes (temp + rename + best-effort flock).
    - Does NOT modify proposals.json schema; just fills in null fields.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

# ── Paths ───────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROPOSALS_FILE = PROJECT_ROOT / "memory" / "swarm" / "proposals.json"


# ── Provider routing ────────────────────────────────────────────────────────
# Map known agent → likely provider family used during generation.
# The judge MUST be from a different family (asymmetric, avoids self-favor).
# autonomous_run.py routes most agents via Cerebras/Groq/Gemini; pick a judge
# family that is NOT in the agent's typical chain.
AGENT_GENERATING_FAMILIES: dict[str, set[str]] = {
    # Conservatively assume each agent could touch any of: cerebras/groq/gemini.
    # The single safe "different family" default is NVIDIA (Llama 3.3 NIM).
}

JUDGE_PRIMARY = "nvidia/meta/llama-3.3-70b-instruct"
JUDGE_FALLBACKS = [
    "cerebras/llama3.1-8b",
    "gemini/gemini-2.5-flash",
    "groq/llama-3.3-70b-versatile",
]

JUDGE_SYSTEM_PROMPT = (
    "You are an independent judge scoring a swarm-agent proposal for VOLAURA "
    "(verified professional talent platform). Score 0-10 on each axis: "
    "feasibility (can this actually be done in 1 sprint?), impact (does it move "
    "the needle on a real user metric?), evidence (does the proposal cite a "
    "specific file/line/data point?), safety (does it violate Constitution Law "
    "1-5 or create a new risk?). "
    "Return STRICT JSON with EXACTLY these keys and no prose around it: "
    '{"score_feasibility": int, "score_impact": int, "score_evidence": int, '
    '"score_safety": int, "overall_score": int, "reasoning": str, '
    '"criteria_met": [str], "concerns": [str]}. '
    "overall_score is the rounded mean of the four sub-scores, 0-10."
)


# ── Atomic IO ───────────────────────────────────────────────────────────────
def _read_proposals() -> dict[str, Any]:
    if not PROPOSALS_FILE.exists():
        logger.warning("proposals.json missing at {p}", p=PROPOSALS_FILE)
        return {"schema_version": "1.0", "proposals": []}
    with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _atomic_write(data: dict[str, Any]) -> None:
    """Atomic temp + rename. Best-effort fcntl.flock on POSIX.

    TODO(P0-3 ghost-audit): proposals.json has TOCTOU race vs telegram_webhook.py
    writes. Atomic rename narrows the window but doesn't close it. Real fix is
    a sqlite/lock-file move planned in a separate pass.
    """
    PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)

    fd, tmp_path = tempfile.mkstemp(
        prefix=".proposals-", suffix=".tmp", dir=str(PROPOSALS_FILE.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            try:
                import fcntl  # POSIX only
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            except (ImportError, OSError):
                pass  # Windows / no flock — atomic rename still narrows window
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, PROPOSALS_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ── LLM call ────────────────────────────────────────────────────────────────
async def _call_judge(
    model: str, system: str, user_prompt: str, timeout: float = 30.0
) -> str:
    """One LLM call via litellm.acompletion. Returns response text."""
    from litellm import acompletion

    # Provider-specific kwargs
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
        "timeout": timeout,
    }
    if model.startswith("nvidia/"):
        kwargs["api_base"] = "https://integrate.api.nvidia.com/v1"
        kwargs["api_key"] = os.environ.get("NVIDIA_API_KEY")
        kwargs["model"] = "openai/" + model[len("nvidia/"):]
        kwargs["custom_llm_provider"] = "openai"
    elif model.startswith("cerebras/"):
        kwargs["api_key"] = os.environ.get("CEREBRAS_API_KEY")
    elif model.startswith("gemini/"):
        kwargs["api_key"] = os.environ.get("GEMINI_API_KEY")
    elif model.startswith("groq/"):
        kwargs["api_key"] = os.environ.get("GROQ_API_KEY")

    resp = await acompletion(**kwargs)
    return resp.choices[0].message.content or ""


def _pick_judge_chain(agent: str) -> list[str]:
    """Order of judge models for a given proposing agent.

    All agents currently route through Cerebras/Groq/Gemini families, so the
    safe "different family" default is NVIDIA first. If NVIDIA missing or
    fails, use any other free provider that has a key configured.
    """
    chain: list[str] = []

    if os.environ.get("NVIDIA_API_KEY"):
        chain.append(JUDGE_PRIMARY)

    for m in JUDGE_FALLBACKS:
        env_key = {
            "cerebras/": "CEREBRAS_API_KEY",
            "gemini/": "GEMINI_API_KEY",
            "groq/": "GROQ_API_KEY",
        }
        for prefix, key_name in env_key.items():
            if m.startswith(prefix) and os.environ.get(key_name):
                chain.append(m)
                break

    # De-dup preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for m in chain:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    return deduped


def _parse_judge_json(raw: str) -> dict[str, Any]:
    """Lenient JSON extraction. Strips ``` fences + leading prose."""
    text = raw.strip()
    if text.startswith("```"):
        # ```json ... ``` or ``` ... ```
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
        # last ``` was stripped by .strip("`") already
    # Find first { ... last }
    lo = text.find("{")
    hi = text.rfind("}")
    if lo == -1 or hi == -1:
        raise ValueError(f"no JSON object in response: {raw[:200]!r}")
    return json.loads(text[lo : hi + 1])


def _clamp_int(v: Any, lo: int = 0, hi: int = 10) -> int:
    try:
        n = int(round(float(v)))
    except (TypeError, ValueError):
        n = 0
    return max(lo, min(hi, n))


async def _judge_one(prop: dict[str, Any], dry_run: bool) -> tuple[bool, str]:
    """Returns (success, judge_model_used_or_error)."""
    agent = prop.get("agent", "unknown")
    title = prop.get("title", "")[:200]
    content = prop.get("content", "")
    severity = prop.get("severity", "")

    user_prompt = (
        f"Proposing agent: {agent}\n"
        f"Severity: {severity}\n"
        f"Title: {title}\n\n"
        f"Proposal content:\n{content}\n"
    )

    chain = _pick_judge_chain(agent)
    if not chain:
        return False, "no judge providers configured (set NVIDIA_API_KEY or any free key)"

    if dry_run:
        return True, chain[0]

    last_err: str = ""
    for model in chain:
        for attempt in (1, 2):
            try:
                raw = await _call_judge(model, JUDGE_SYSTEM_PROMPT, user_prompt)
                parsed = _parse_judge_json(raw)

                sub = {
                    "feasibility": _clamp_int(parsed.get("score_feasibility")),
                    "impact": _clamp_int(parsed.get("score_impact")),
                    "evidence": _clamp_int(parsed.get("score_evidence")),
                    "safety": _clamp_int(parsed.get("score_safety")),
                }
                overall = _clamp_int(
                    parsed.get("overall_score", sum(sub.values()) / 4.0)
                )
                reasoning = str(parsed.get("reasoning", ""))[:500]
                criteria_met = [
                    str(x)[:120] for x in (parsed.get("criteria_met") or [])[:10]
                ]
                concerns = [
                    str(x)[:120] for x in (parsed.get("concerns") or [])[:10]
                ]

                prop["judge_score"] = overall
                prop["judge_model"] = model
                prop["judge_reasoning"] = reasoning
                prop["judge_criteria"] = {
                    "sub_scores": sub,
                    "criteria_met": criteria_met,
                    "concerns": concerns,
                }

                logger.info(
                    "JUDGED [{a}] \"{t:.60}\" score={s}/10 model={m}",
                    a=agent, t=title, s=overall, m=model,
                )
                # Also explicit stdout (spec)
                summary = (
                    f"JUDGED [{agent}] \"{title[:60]}\" "
                    f"score={overall}/10 reasoning={reasoning[:40]}..."
                )
                sys.stdout.write(summary + "\n")
                sys.stdout.flush()
                return True, model
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
                logger.warning(
                    "Judge attempt {n} failed model={m} agent={a}: {e}",
                    n=attempt, m=model, a=agent, e=last_err,
                )
                await asyncio.sleep(0.5 * attempt)
        # next model in chain

    return False, last_err or "all judge models failed"


# ── Main ────────────────────────────────────────────────────────────────────
async def main_async(limit: int | None, dry_run: bool) -> int:
    data = _read_proposals()
    proposals = data.get("proposals", [])

    pending = [
        p for p in proposals
        if p.get("status") == "pending" and p.get("judge_score") is None
    ]
    if limit is not None:
        pending = pending[:limit]

    if not pending:
        logger.info("No pending un-judged proposals. Nothing to do.")
        return 0

    logger.info(
        "Judging {n} proposals (dry_run={d})", n=len(pending), d=dry_run
    )

    if dry_run:
        # Print plan only.
        for p in pending:
            chain = _pick_judge_chain(p.get("agent", "unknown"))
            judge = chain[0] if chain else "<no provider configured>"
            sys.stdout.write(
                f"WOULD-JUDGE [{p.get('agent','?')}] "
                f"\"{(p.get('title','') or '')[:60]}\" -> {judge}\n"
            )
        sys.stdout.flush()
        return 0

    failures = 0
    changed = False
    for p in pending:
        ok, _info = await _judge_one(p, dry_run=False)
        if ok:
            changed = True
        else:
            failures += 1

    if changed:
        _atomic_write(data)
        logger.info("proposals.json updated.")

    return 0 if failures == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM judge for swarm proposals")
    parser.add_argument("--limit", type=int, default=None,
                        help="max proposals to judge this run")
    parser.add_argument("--dry-run", action="store_true",
                        help="list what would be judged, no LLM calls")
    args = parser.parse_args()

    rc = asyncio.run(main_async(limit=args.limit, dry_run=args.dry_run))
    sys.exit(rc)


if __name__ == "__main__":
    main()
