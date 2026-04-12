#!/usr/bin/env python3
"""Recovery Strategies — Sprint 3: Adaptive Execution Loop.

Concrete implementations of each recovery strategy.
Called by AgentExecutionTracker after a failure is detected.

Strategies:
  retry      → Same approach, exponential backoff
  simplify   → Reduce task scope, attempt partial completion
  decompose  → Break task into subtasks, tackle one at a time
  escalate   → Write to escalations.md, require human attention

Usage:
    from swarm.recovery_strategies import apply_recovery_strategy

    outcome = apply_recovery_strategy(
        strategy="decompose",
        tracker=tracker,
        task=task_dict,
        project_root=project_root,
    )
    if outcome["next_action"] == "continue":
        # Retry with modified task
        modified_task = outcome["modified_task"]
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
ESCALATIONS_LOG = project_root / "memory" / "swarm" / "escalations.md"
DECOMPOSED_TASKS_LOG = project_root / "memory" / "swarm" / "decomposed-tasks.jsonl"


# ── Strategy dispatcher ────────────────────────────────────────────────────────

def apply_recovery_strategy(
    strategy: str,
    tracker: Any,               # AgentExecutionTracker (avoid circular import)
    task: dict[str, Any],
    project_root_override: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Apply recovery strategy and return next action.

    Args:
        strategy: One of "retry", "simplify", "decompose", "escalate"
        tracker: AgentExecutionTracker instance
        task: Task dict with title, description, expected_files etc.
        project_root_override: Override project root
        env: Environment variables

    Returns:
        {
            "next_action": "continue" | "abort",
            "wait_seconds": float,       # how long to wait before retry
            "modified_task": dict,       # modified task for next attempt (may be same as input)
            "subtasks": list[dict],      # if decompose: list of subtasks
            "escalation_written": bool,  # if escalate: whether file was written
            "message": str,              # human-readable outcome description
        }
    """
    root = project_root_override or project_root

    if strategy == "retry":
        return _strategy_retry(tracker, task)
    elif strategy == "simplify":
        return _strategy_simplify(tracker, task, root, env)
    elif strategy == "decompose":
        return _strategy_decompose(tracker, task, root, env)
    elif strategy == "escalate":
        return _strategy_escalate(tracker, task, root)
    else:
        return _strategy_escalate(tracker, task, root)


# ── Retry ─────────────────────────────────────────────────────────────────────

def _strategy_retry(tracker: Any, task: dict) -> dict:
    """Exponential backoff retry. No task modification.

    Backoff: attempt 1 → 5s, attempt 2 → 15s, attempt 3 → 45s
    """
    attempt = tracker.attempt
    wait = min(5 * (3 ** (attempt - 1)), 120)   # cap at 2 minutes

    time.sleep(wait)   # In GitHub Actions this is acceptable (cheap runner time)

    return {
        "next_action": "continue",
        "wait_seconds": wait,
        "modified_task": task,  # unchanged
        "subtasks": [],
        "escalation_written": False,
        "message": f"Retry after {wait}s backoff (attempt {attempt})",
    }


# ── Simplify ──────────────────────────────────────────────────────────────────

def _strategy_simplify(
    tracker: Any,
    task: dict,
    project_root: Path,
    env: dict | None,
) -> dict:
    """Reduce task scope. Remove optional expected_files, shorten description.

    Heuristic simplification (no LLM needed):
    - If expected_files has >1 item: try just the first
    - If description is long: truncate to first paragraph
    - Mark task as "partial completion acceptable"
    """
    modified = task.copy()

    # Reduce expected files to just the first (primary deliverable)
    expected = task.get("expected_files", [])
    if len(expected) > 1:
        modified["expected_files"] = expected[:1]
        modified["title"] = f"[SIMPLIFIED] {task.get('title', '')} — primary file only"
        message = f"Simplified: targeting {expected[0]} only (dropped {len(expected)-1} secondary files)"
    else:
        # Can't simplify files — try shortening description
        desc = task.get("description", "")
        if len(desc) > 300:
            short_desc = desc[:300].rsplit(". ", 1)[0] + "."
            modified["description"] = short_desc
            modified["title"] = f"[SIMPLIFIED] {task.get('title', '')}"
            message = f"Simplified: description shortened from {len(desc)} to {len(short_desc)} chars"
        else:
            # Nothing to simplify — fall through to decompose
            message = "Simplify: no obvious scope reduction possible — consider decompose"

    modified["partial_completion_ok"] = True

    return {
        "next_action": "continue",
        "wait_seconds": 2.0,
        "modified_task": modified,
        "subtasks": [],
        "escalation_written": False,
        "message": message,
    }


# ── Decompose ─────────────────────────────────────────────────────────────────

def _strategy_decompose(
    tracker: Any,
    task: dict,
    project_root: Path,
    env: dict | None,
) -> dict:
    """Break task into sequential subtasks.

    Rule-based decomposition:
    - Each expected_file becomes its own subtask
    - Dependencies are inferred from import patterns
    - Subtasks are written to decomposed-tasks.jsonl for the next run
    """
    expected_files = task.get("expected_files", [])
    task_title = task.get("title", "Unknown task")
    task_desc = task.get("description", "")

    if not expected_files:
        # No files to decompose — create 2 generic subtasks
        subtasks = [
            {
                "id": f"{task.get('id', 'unknown')}-sub1",
                "title": f"[SUBTASK 1/2] Research: {task_title}",
                "description": f"Read relevant existing files and understand the codebase before acting. Original task: {task_desc[:200]}",
                "expected_files": [],
                "parent_task_id": task.get("id", "unknown"),
                "order": 1,
            },
            {
                "id": f"{task.get('id', 'unknown')}-sub2",
                "title": f"[SUBTASK 2/2] Implement: {task_title}",
                "description": task_desc,
                "expected_files": task.get("expected_files", []),
                "parent_task_id": task.get("id", "unknown"),
                "order": 2,
            },
        ]
    else:
        # Each expected file becomes a subtask
        subtasks = []
        for i, file_path in enumerate(expected_files, 1):
            subtasks.append({
                "id": f"{task.get('id', 'unknown')}-sub{i}",
                "title": f"[SUBTASK {i}/{len(expected_files)}] Create {Path(file_path).name}",
                "description": f"Create {file_path}. Part of: {task_title}",
                "expected_files": [file_path],
                "check_imports": [file_path] if file_path.endswith(".py") else [],
                "parent_task_id": task.get("id", "unknown"),
                "order": i,
            })

    # Write subtasks to log for next run
    DECOMPOSED_TASKS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parent_task_id": task.get("id", "unknown"),
        "parent_title": task_title,
        "tracker_errors": tracker.errors,
        "subtasks": subtasks,
    }
    with open(DECOMPOSED_TASKS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return {
        "next_action": "continue",
        "wait_seconds": 1.0,
        "modified_task": subtasks[0] if subtasks else task,  # start with first subtask
        "subtasks": subtasks,
        "escalation_written": False,
        "message": f"Decomposed into {len(subtasks)} subtasks. Starting with: {subtasks[0]['title'] if subtasks else 'none'}",
    }


# ── Escalate ──────────────────────────────────────────────────────────────────

def _strategy_escalate(
    tracker: Any,
    task: dict,
    project_root: Path,
) -> dict:
    """Write to escalations.md. Require human attention.

    Format matches IMPLEMENTATION-ROADMAP.md spec:
      ## [timestamp] ESCALATION: [agent] → [task]
      - Attempts: N
      - Final error: [error]
      - Recovery strategies tried: [list]
      - Recommended action: [human-readable]
    """
    ESCALATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    agent = task.get("agent", tracker.task_id.split("-")[0] if hasattr(tracker, "task_id") else "unknown")
    task_title = task.get("title", tracker.task_title if hasattr(tracker, "task_title") else "Unknown")
    errors = getattr(tracker, "errors", [])
    strategies = getattr(tracker, "strategies_used", [])
    attempt = getattr(tracker, "attempt", 0)

    last_error = errors[-1] if errors else "unknown error"
    recommended = _recommend_human_action(last_error, strategies)

    escalation_text = f"""
## {timestamp} ESCALATION: {agent} -> {task_title}

- **Attempts:** {attempt}
- **Final error:** {last_error[:300]}
- **Recovery strategies tried:** {', '.join(strategies) if strategies else 'none'}
- **Recommended action:** {recommended}
- **Task description:** {task.get('description', '')[:200]}
- **Expected files:** {task.get('expected_files', [])}

---
"""

    # Append to escalations.md (create if doesn't exist)
    if not ESCALATIONS_LOG.exists():
        ESCALATIONS_LOG.write_text(
            "# Swarm Escalations Log\n\n"
            "Agents that exceeded max retries. Require human attention.\n\n",
            encoding="utf-8",
        )

    with open(ESCALATIONS_LOG, "a", encoding="utf-8") as f:
        f.write(escalation_text)

    return {
        "next_action": "abort",
        "wait_seconds": 0,
        "modified_task": task,
        "subtasks": [],
        "escalation_written": True,
        "message": f"Escalated to human after {attempt} attempts. See memory/swarm/escalations.md",
    }


def _recommend_human_action(last_error: str, strategies_tried: list[str]) -> str:
    """Generate a human-readable recommendation based on error pattern."""
    error_lower = last_error.lower()

    if "import" in error_lower or "module" in error_lower:
        return "Install missing dependency: check requirements.txt / pyproject.toml. Run: pip install <package>"
    elif "permission" in error_lower or "forbidden" in error_lower:
        return "Check file permissions or API key scopes. Verify environment variables are set correctly."
    elif "syntax" in error_lower:
        return "Fix syntax error in generated code. Run: python -m ast <file> to identify the issue."
    elif "timeout" in error_lower and "retry" in strategies_tried:
        return "External service is slow. Consider increasing timeout thresholds or using async approach."
    elif "not found" in error_lower or "404" in error_lower:
        return "Referenced resource doesn't exist. Verify file paths, API endpoints, or DB tables."
    elif "rate limit" in error_lower or "429" in error_lower:
        return "API rate limit hit. Add delay between calls or upgrade API tier."
    else:
        return "Review error details above. Check recent git changes for potential conflicts."


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from swarm.execution_state import AgentExecutionTracker

    task = {
        "id": "test-001",
        "title": "Test decompose strategy",
        "description": "Create two test files",
        "expected_files": ["packages/swarm/test_a.py", "packages/swarm/test_b.py"],
        "agent": "QA Engineer",
    }

    tracker = AgentExecutionTracker(task_id="test-001", task_title=task["title"], max_retries=3)
    tracker.start()
    tracker.handle_failure("FileNotFoundError: test_a.py not found")
    tracker.apply_recovery("decompose")

    result = apply_recovery_strategy("decompose", tracker, task)
    print(f"Strategy result: {result['next_action']}")
    print(f"Message: {result['message']}")
    print(f"Subtasks: {len(result['subtasks'])}")
    for st in result["subtasks"]:
        print(f"  - {st['title']}")
