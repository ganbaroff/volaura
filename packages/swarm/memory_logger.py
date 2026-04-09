"""
Episodic Memory Logger for MiroFish swarm.

Architecture from Gemini Deep Research (2026-03-25):
- Layer 1: Episodic JSON logs per agent run (hippocampus equivalent)
- Layer 2: Sleep cycle daemon — consolidates high-value runs into Global_Context.md
- Layer 3: Context injection — all agents read Global_Context.md at init

Usage:
  # After each agent run:
  log_episodic_run("gemini-flash", prompt, response, score=0.9)

  # Periodic consolidation (run via cron or swarm daily job):
  sleep_cycle_consolidation(llm_client)

  # At agent init:
  full_prompt = inject_global_memory(base_system_prompt)
"""

from __future__ import annotations

import glob
import json
import os
import time
from pathlib import Path

from loguru import logger

# Paths
_INBOX_DIR = Path("packages/swarm/memory_inbox")
_GLOBAL_CONTEXT = Path("packages/swarm/memory/Global_Context.md")

# EDM thresholds: keep successes (≥0.8) and failures (≤0.2), discard noise in between
_KEEP_HIGH = 0.8
_KEEP_LOW = 0.2


def log_episodic_run(
    agent_id: str,
    prompt: str,
    response: str,
    score: float,
) -> None:
    """
    Non-blocking: write one agent run to the episodic inbox.
    Score 0.0–1.0 (from synthesis agent or eval):
      ≥ 0.8 = high-value success → consolidate
      ≤ 0.2 = failure → consolidate (for hindsight/ECHO)
      0.2–0.8 = noise → discard at next sleep cycle
    """
    _INBOX_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": time.time(),
        "agent": agent_id,
        "prompt": prompt[:500],  # cap to prevent bloat
        "response": response[:1000],
        "score": score,
    }

    safe_agent_id = agent_id.replace(":", "_").replace("/", "_").replace("\\", "_")
    filename = _INBOX_DIR / f"run_{int(time.time())}_{safe_agent_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    logger.debug("Episodic log written: {f} (score={s})", f=filename.name, s=score)


def sleep_cycle_consolidation(llm_client: object) -> int:
    """
    Sleep cycle daemon — run every 6 hours or after 50+ agent runs.

    SWS phase: extract generalized rules from successes.
    REM phase: extract corrected paths from failures (ECHO/hindsight).
    Prunes all processed logs after extraction.

    Returns number of insights written to Global_Context.md.
    """
    logs = glob.glob(str(_INBOX_DIR / "*.json"))
    if not logs:
        logger.info("Sleep cycle: inbox empty, nothing to consolidate.")
        return 0

    high_value: list[dict] = []
    noise_count = 0

    for filepath in logs:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            score = data.get("score", 0.5)
            if score >= _KEEP_HIGH or score <= _KEEP_LOW:
                high_value.append(data)
            else:
                noise_count += 1
        except Exception as e:
            logger.warning("Failed to read episodic log {f}: {e}", f=filepath, e=e)
        finally:
            os.remove(filepath)  # REM pruning — always delete after processing

    logger.info(
        "Sleep cycle: {h} high-value, {n} noise discarded.",
        h=len(high_value),
        n=noise_count,
    )

    if not high_value:
        return 0

    # SWS + ECHO: extract rules and hindsight corrections
    successes = [r for r in high_value if r["score"] >= _KEEP_HIGH]
    failures = [r for r in high_value if r["score"] <= _KEEP_LOW]

    insights_written = 0

    if successes:
        prompt = (
            f"Analyze these {len(successes)} successful agent interactions from the MiroFish swarm. "
            f"Extract 2-3 generalized, permanent rules that made these responses high quality. "
            f"Be specific. Format as bullet points.\n\n"
            f"Interactions: {json.dumps(successes[:5], ensure_ascii=False)}"
        )
        try:
            rules = _call_llm(llm_client, prompt)
            _append_to_global_context(f"## Success Patterns ({_ts()})\n{rules}")
            insights_written += 1
        except Exception as e:
            logger.error("Failed to consolidate successes: {e}", e=e)

    if failures:
        prompt = (
            f"Analyze these {len(failures)} failed agent interactions from the MiroFish swarm. "
            f"For each failure, state the corrected approach (hindsight optimization). "
            f"Extract 2-3 rules to prevent these failures. Format as bullet points.\n\n"
            f"Interactions: {json.dumps(failures[:5], ensure_ascii=False)}"
        )
        try:
            corrections = _call_llm(llm_client, prompt)
            _append_to_global_context(f"## Failure Corrections / ECHO ({_ts()})\n{corrections}")
            insights_written += 1
        except Exception as e:
            logger.error("Failed to consolidate failures: {e}", e=e)

    logger.info("Sleep cycle complete: {n} insight blocks written.", n=insights_written)
    return insights_written


def inject_global_memory(system_prompt_base: str) -> str:
    """
    Inject Global_Context.md into agent system prompt at init.
    Every agent reads consolidated neocortical state before executing.
    """
    try:
        with open(_GLOBAL_CONTEXT, "r", encoding="utf-8") as f:
            domain_memory = f.read().strip()
    except FileNotFoundError:
        domain_memory = ""

    if not domain_memory:
        return system_prompt_base

    return f"{system_prompt_base}\n\n---\nCRITICAL SWARM KNOWLEDGE (from memory consolidation):\n{domain_memory}"


def _append_to_global_context(content: str) -> None:
    """Append new insight block to Global_Context.md."""
    _GLOBAL_CONTEXT.parent.mkdir(parents=True, exist_ok=True)
    with open(_GLOBAL_CONTEXT, "a", encoding="utf-8") as f:
        f.write(f"\n{content}\n")


def _call_llm(llm_client: object, prompt: str) -> str:
    """Call the provided LLM client. Supports google-genai and basic .generate() interface."""
    # google-genai client
    if hasattr(llm_client, "models"):
        response = llm_client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
            contents=prompt,
        )
        return response.text

    # Generic .generate() interface
    if hasattr(llm_client, "generate"):
        return llm_client.generate(prompt)

    raise ValueError(f"Unsupported llm_client type: {type(llm_client)}")


def _ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M")
