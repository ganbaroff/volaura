"""Reflexion injection — agents learn from their past mistakes and successes.

Reads agent-trajectories.jsonl (53 entries: 33 correct, 20 wrong) and
injects relevant reflexions into agent prompts before each task.

CEO research (Session 88, section 5.1):
"Логи рефлексии уже есть, но не используются. В system prompt каждого агента
добавить секцию 'Relevant self-criticisms from past tasks'."

RefleXion pattern: agent sees its own past failures → avoids repeating them.
Research shows significant accuracy improvement on recurring task types.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger


_TRAJECTORIES_PATH = Path.home() / ".swarm" / "agent-trajectories.jsonl"
_DECISION_HISTORY_PATH = Path.home() / ".swarm" / "decision_history.json"


def _load_trajectories() -> list[dict[str, Any]]:
    """Load all trajectories from JSONL file."""
    if not _TRAJECTORIES_PATH.exists():
        return []
    entries = []
    try:
        with open(_TRAJECTORIES_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception as e:
        logger.debug("Failed to load trajectories: {e}", e=str(e)[:100])
    return entries


def get_reflexions_for_model(model_name: str, max_entries: int = 5) -> str:
    """Get past reflexions (failures + successes) for a specific model.

    Returns formatted text block for injection into agent system prompt.
    Prioritizes recent failures (they're more instructive than successes).
    """
    entries = _load_trajectories()
    if not entries:
        return ""

    # Filter by model
    model_entries = [e for e in entries if e.get("model", "") == model_name]
    if not model_entries:
        # Try partial match (model names vary between providers)
        model_short = model_name.split("/")[-1].split(":")[0]
        model_entries = [e for e in entries if model_short in e.get("model", "")]

    if not model_entries:
        return ""

    # Separate failures and successes
    failures = [e for e in model_entries if e.get("outcome") == "wrong"]
    successes = [e for e in model_entries if e.get("outcome") == "correct"]

    # Take recent failures first (more instructive), then successes
    selected = failures[-max_entries:] + successes[-(max_entries // 2):]

    if not selected:
        return ""

    lines = ["## YOUR PAST PERFORMANCE (learn from these)\n"]

    for entry in selected[-max_entries:]:
        outcome = entry.get("outcome", "?")
        task_summary = entry.get("task", "")[:150]
        response_summary = entry.get("response", "")[:200]
        emoji = "FAIL" if outcome == "wrong" else "OK"

        lines.append(f"[{emoji}] Task: {task_summary}")
        if outcome == "wrong":
            lines.append("  Your response was rejected. Avoid this pattern.")
        lines.append("")

    failure_rate = len(failures) / max(len(model_entries), 1)
    lines.append(f"Your stats: {len(model_entries)} tasks, {len(failures)} failures ({failure_rate:.0%} error rate)")
    if failure_rate > 0.3:
        lines.append("WARNING: High error rate. Focus on producing valid JSON and referencing specific files.")

    return "\n".join(lines)


def get_reflexions_for_task(task_keywords: str, max_entries: int = 3) -> str:
    """Get reflexions relevant to a specific task type (keyword matching).

    This helps agents avoid repeating mistakes on similar tasks.
    """
    entries = _load_trajectories()
    if not entries:
        return ""

    keywords = set(task_keywords.lower().split())
    scored = []

    for entry in entries:
        task_text = entry.get("task", "").lower()
        overlap = sum(1 for kw in keywords if kw in task_text)
        if overlap > 0:
            scored.append((overlap, entry))

    scored.sort(key=lambda x: -x[0])
    top = [e for _, e in scored[:max_entries]]

    if not top:
        return ""

    lines = ["## SIMILAR PAST TASKS (context)\n"]
    for entry in top:
        outcome = entry.get("outcome", "?")
        task = entry.get("task", "")[:120]
        lines.append(f"[{outcome.upper()}] {task}")

    return "\n".join(lines)


def get_decision_history_context(max_entries: int = 3) -> str:
    """Get recent swarm decision outcomes for context.

    Reads decision_history.json to show agents what the swarm decided recently.
    """
    if not _DECISION_HISTORY_PATH.exists():
        return ""

    try:
        with open(_DECISION_HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return ""

    # decision_history.json is a dict with decision IDs as keys
    decisions = list(data.values()) if isinstance(data, dict) else data
    if not decisions:
        return ""

    recent = decisions[-max_entries:]
    lines = ["## RECENT SWARM DECISIONS\n"]

    for d in recent:
        winner = d.get("winner", "?")
        score = d.get("winner_score", 0)
        question = d.get("question", "")[:100] if isinstance(d.get("question"), str) else str(d.get("config", {}).get("question", ""))[:100]
        lines.append(f"- Winner: {winner} ({score}/50) — {question}")

    return "\n".join(lines)
