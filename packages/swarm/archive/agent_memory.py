"""
Agent Memory — each model remembers its past decisions, what worked, what didn't.
Builds expertise profiles over time.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger


class AgentMemory:
    """Per-model memory: tracks experiences, learns from mistakes."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = (data_dir or Path.home() / ".swarm") / "agent_logs"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def log_experience(
        self,
        model: str,
        task_summary: str,
        skill_used: str | None,
        skill_helpful: bool | None,
        chose_winner: str,
        was_correct: bool | None,  # None if not yet calibrated
        self_note: str = "",
        full_prompt: str = "",
        full_response: str = "",
    ) -> None:
        """Record one experience for a model.

        full_prompt / full_response are stored for WRONG entries so that
        get_context_for_agent() can surface the exact failure trace (Reflexion pattern,
        arXiv:2303.11366). Agents that see "You wrote X, correct was Y" stop repeating
        the same mistake vs agents that only see the lesson label.
        """
        path = self._model_path(model)
        logs = self._load(path)

        entry: dict = {
            "task": task_summary[:200],
            "skill": skill_used,
            "skill_helpful": skill_helpful,
            "winner": chose_winner,
            "correct": was_correct,
            "note": self_note[:300],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        # Only persist full traces for wrong/uncalibrated entries (saves space)
        if full_prompt:
            entry["full_prompt"] = full_prompt[:500]
        if full_response:
            entry["full_response"] = full_response[:500]

        logs.append(entry)

        # Keep last 100 experiences per model
        if len(logs) > 100:
            logs = logs[-100:]

        self._save(path, logs)

    def get_context_for_agent(self, model: str, max_entries: int = 5) -> str:
        """Build a brief experience summary to inject into agent prompt."""
        path = self._model_path(model)
        logs = self._load(path)

        if not logs:
            return ""

        recent = logs[-max_entries:]
        lines = ["YOUR PAST EXPERIENCE (learn from this):"]
        for entry in recent:
            correct_tag = ""
            if entry.get("correct") is True:
                correct_tag = " [CORRECT]"
            elif entry.get("correct") is False:
                correct_tag = " [WRONG - learn from this]"

            note = entry.get("note", "")
            line = (
                f"- Task: {entry['task'][:80]} | Chose: {entry['winner']}{correct_tag}"
                + (f" | Note: {note[:80]}" if note else "")
            )
            lines.append(line)

            # Reflexion trace: for WRONG entries, show exactly what was said and what was right.
            # "You wrote X. The correct answer was Y." — 91% vs 80% HumanEval (arXiv:2303.11366).
            if entry.get("correct") is False:
                full_resp = entry.get("full_response", "")
                if full_resp:
                    lines.append(f"  You wrote: {full_resp[:200]}")
                if note:
                    lines.append(f"  Correct was: {note[:200]}")

        return "\n".join(lines)

    def get_model_stats(self, model: str) -> dict[str, Any]:
        """Get aggregated stats for a model."""
        path = self._model_path(model)
        logs = self._load(path)

        if not logs:
            return {"total": 0, "correct": 0, "wrong": 0, "pending": 0}

        correct = sum(1 for l in logs if l.get("correct") is True)
        wrong = sum(1 for l in logs if l.get("correct") is False)
        pending = sum(1 for l in logs if l.get("correct") is None)

        return {
            "total": len(logs),
            "correct": correct,
            "wrong": wrong,
            "pending": pending,
            "accuracy": correct / max(correct + wrong, 1),
        }

    def log_trajectory(
        self,
        model: str,
        task: str,
        full_prompt: str,
        full_response: str,
        outcome: str,  # "correct" | "wrong" | "pending"
        skill_used: str | None = None,
    ) -> None:
        """Append a raw task trajectory to agent-trajectories.jsonl.

        EvoSkill (sentient-agi/EvoSkill) pattern: skill evolution works from
        raw failed trajectory logs, not distilled summaries. Each line is one
        JSON object — append-only, never overwritten.

        skill_evolution.py reads this file alongside agent-feedback-distilled.md
        to close the gap between our engine and EvoSkill/VOYAGER state-of-the-art.
        """
        traj_path = self.data_dir.parent / "agent-trajectories.jsonl"
        record = {
            "model": model,
            "task": task[:300],
            "prompt": full_prompt[:800],
            "response": full_response[:800],
            "outcome": outcome,
            "skill": skill_used,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(traj_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def mark_calibration(self, model: str, decision_id: str, was_correct: bool) -> None:
        """After calibration, update past experiences with correct/wrong."""
        path = self._model_path(model)
        logs = self._load(path)

        # Find most recent uncalibrated entry and mark it
        for entry in reversed(logs):
            if entry.get("correct") is None:
                entry["correct"] = was_correct
                break

        self._save(path, logs)

    def _model_path(self, model: str) -> Path:
        safe_name = model.replace("/", "_").replace(":", "_")
        return self.data_dir / f"{safe_name}.json"

    def _load(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, path: Path, data: list[dict]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
