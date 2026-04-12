#!/usr/bin/env python3
"""Execution State Tracker — Sprint 3: Adaptive Execution Loop.

Tracks agent task execution state across attempts. Serializable to JSON
so state can be resumed across context windows or GitHub Actions runs.

Based on ZEUS adaptive_executor.py pattern, ported for Linux/Railway compatibility
(no win32gui dependency — pure Python state machine).

States:
  IDLE       → task received, not started
  RUNNING    → currently executing attempt N
  RETRYING   → previous attempt failed, preparing retry
  RECOVERING → applying a recovery strategy before next attempt
  FAILED     → max retries exceeded, escalating
  SUCCESS    → task completed successfully

Usage:
    from swarm.execution_state import AgentExecutionTracker, ExecutionState

    tracker = AgentExecutionTracker(task_id="sprint3-3.1", task_title="...")
    tracker.start()
    try:
        result = do_work()
        tracker.succeed(result)
    except Exception as e:
        strategy = tracker.handle_failure(e)
        if strategy == "escalate":
            # write to escalations.md
            pass
        elif strategy == "decompose":
            # break task into subtasks
            pass
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


# ── State machine ──────────────────────────────────────────────────────────────

class ExecutionState(Enum):
    IDLE       = "idle"
    RUNNING    = "running"
    RETRYING   = "retrying"
    RECOVERING = "recovering"
    FAILED     = "failed"
    SUCCESS    = "success"


# Recovery strategy names (handled by recovery_strategies.py)
RECOVERY_STRATEGIES = ["retry", "simplify", "decompose", "escalate"]

# Valid state transitions
_TRANSITIONS: dict[ExecutionState, set[ExecutionState]] = {
    ExecutionState.IDLE:       {ExecutionState.RUNNING},
    ExecutionState.RUNNING:    {ExecutionState.SUCCESS, ExecutionState.RETRYING, ExecutionState.FAILED},
    ExecutionState.RETRYING:   {ExecutionState.RUNNING, ExecutionState.RECOVERING, ExecutionState.FAILED},
    ExecutionState.RECOVERING: {ExecutionState.RUNNING, ExecutionState.FAILED},
    ExecutionState.FAILED:     set(),   # terminal
    ExecutionState.SUCCESS:    set(),   # terminal
}


# ── Tracker ────────────────────────────────────────────────────────────────────

@dataclass
class AgentExecutionTracker:
    """Tracks a single task's execution across attempts.

    Attributes:
        task_id: Unique identifier for the task
        task_title: Human-readable task name
        max_retries: Maximum number of retry attempts before escalation
        state: Current ExecutionState
        attempt: Current attempt number (1-indexed)
        errors: List of error strings from failed attempts
        strategies_used: Recovery strategies tried so far
        result: Final result if succeeded
        started_at: ISO timestamp of first start
        completed_at: ISO timestamp of final success/failure
    """
    task_id: str
    task_title: str
    max_retries: int = 3
    state: ExecutionState = field(default=ExecutionState.IDLE)
    attempt: int = 0
    errors: list[str] = field(default_factory=list)
    strategies_used: list[str] = field(default_factory=list)
    result: Any = None
    started_at: str = ""
    completed_at: str = ""

    def _transition(self, new_state: ExecutionState) -> None:
        """Validate and apply state transition."""
        allowed = _TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition: {self.state.value} -> {new_state.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self.state = new_state

    def start(self) -> None:
        """Begin a new attempt."""
        if self.state == ExecutionState.IDLE:
            self.started_at = datetime.now(timezone.utc).isoformat()
        self._transition(ExecutionState.RUNNING)
        self.attempt += 1

    def succeed(self, result: Any = None) -> None:
        """Mark task as successfully completed."""
        self._transition(ExecutionState.SUCCESS)
        self.result = result
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def handle_failure(self, error: Exception | str) -> str:
        """Record failure and choose recovery strategy.

        Returns the recovery strategy name to apply:
            "retry"      → same approach, try again
            "simplify"   → reduce scope, partial completion
            "decompose"  → break into subtasks
            "escalate"   → give up, require human
        """
        error_str = str(error)
        self.errors.append(error_str)

        if self.attempt >= self.max_retries:
            self._transition(ExecutionState.FAILED)
            self.completed_at = datetime.now(timezone.utc).isoformat()
            return "escalate"

        # Choose strategy based on error type and attempt number
        strategy = _choose_strategy(error, self.attempt, self.strategies_used)
        self.strategies_used.append(strategy)

        if strategy == "escalate":
            self._transition(ExecutionState.FAILED)
            self.completed_at = datetime.now(timezone.utc).isoformat()
        else:
            self._transition(ExecutionState.RETRYING)

        return strategy

    def apply_recovery(self, strategy: str) -> None:
        """Transition to RECOVERING state before next attempt."""
        if self.state == ExecutionState.RETRYING:
            self._transition(ExecutionState.RECOVERING)

    @property
    def is_terminal(self) -> bool:
        return self.state in (ExecutionState.SUCCESS, ExecutionState.FAILED)

    @property
    def succeeded(self) -> bool:
        return self.state == ExecutionState.SUCCESS

    @property
    def failed(self) -> bool:
        return self.state == ExecutionState.FAILED

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict."""
        d = asdict(self)
        d["state"] = self.state.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AgentExecutionTracker":
        """Deserialize from dict."""
        data = data.copy()
        data["state"] = ExecutionState(data.get("state", "idle"))
        return cls(**data)

    def summary(self) -> str:
        """One-line human-readable status."""
        if self.succeeded:
            return f"[SUCCESS] {self.task_title} (attempt {self.attempt})"
        elif self.failed:
            return f"[FAILED] {self.task_title} after {self.attempt} attempts — last: {self.errors[-1][:80] if self.errors else 'unknown'}"
        else:
            return f"[{self.state.value.upper()}] {self.task_title} (attempt {self.attempt}/{self.max_retries})"


# ── Strategy selection (simple, deterministic) ────────────────────────────────

def _choose_strategy(
    error: Exception | str,
    attempt: int,
    already_used: list[str],
) -> str:
    """Map error type + attempt number to recovery strategy.

    Priority:
      1. Error-type specific rules
      2. Attempt-number escalation (2nd failure → simplify, 3rd → decompose)
      3. Never repeat a strategy
    """
    error_str = str(error).lower()
    error_type = type(error).__name__ if isinstance(error, Exception) else "unknown"

    # Error-type rules
    if error_type == "FileNotFoundError" or "no such file" in error_str:
        strategy = "decompose"  # file missing → break task into discovery + action
    elif error_type in ("TimeoutError", "asyncio.TimeoutError") or "timeout" in error_str:
        strategy = "simplify"   # timeout → reduce scope
    elif "rate limit" in error_str or "429" in error_str or "quota" in error_str:
        strategy = "retry"      # rate limit → wait and retry
    elif error_type in ("ImportError", "ModuleNotFoundError"):
        strategy = "escalate"   # import error → human must fix dependencies
    elif error_type == "SyntaxError":
        strategy = "escalate"   # syntax error → human must fix
    elif "permission" in error_str or "forbidden" in error_str:
        strategy = "escalate"   # permission error → infra issue
    else:
        # Fallback: escalate by attempt number
        fallback = ["retry", "simplify", "decompose", "escalate"]
        strategy = fallback[min(attempt - 1, len(fallback) - 1)]

    # Never repeat a strategy — pick the next one not yet used
    if strategy in already_used:
        remaining = [s for s in RECOVERY_STRATEGIES if s not in already_used]
        strategy = remaining[0] if remaining else "escalate"

    return strategy


# ── Session log ───────────────────────────────────────────────────────────────

def log_execution(tracker: AgentExecutionTracker, log_path: Path) -> None:
    """Append tracker state to execution log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = tracker.to_dict()
    entry["logged_at"] = datetime.now(timezone.utc).isoformat()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Demo: simulate a task that fails twice then succeeds
    tracker = AgentExecutionTracker(
        task_id="demo-001",
        task_title="Demo task: simulate retry flow",
        max_retries=3,
    )

    attempts = [
        ("TimeoutError: operation timed out", False),
        ("FileNotFoundError: apps/api/app/missing.py not found", False),
        (None, True),  # success on 3rd attempt
    ]

    for error, success in attempts:
        tracker.start()
        print(f"Attempt {tracker.attempt}: {tracker.state.value}")
        if success:
            tracker.succeed("result data")
        else:
            strategy = tracker.handle_failure(error)
            print(f"  Failed: {error}")
            print(f"  Strategy: {strategy}")
            if strategy != "escalate":
                tracker.apply_recovery(strategy)

    print(f"\nFinal: {tracker.summary()}")
    print(f"Strategies used: {tracker.strategies_used}")
