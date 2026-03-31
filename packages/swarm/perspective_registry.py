"""PerspectiveRegistry — EMA-based weight tracking per agent perspective.

Persists agent debate weights to memory/swarm/perspective_weights.json.
Used by autonomous_run.py to inject per-perspective weight context into prompts,
and updated after each run using cross-model judge scores.

EMA update rule:
    new_weight = clamp(
        old_weight * (1 - LEARNING_RATE) + delta * LEARNING_RATE,
        WEIGHT_FLOOR,
        WEIGHT_CEILING,
    )

Where delta = judge_score / 5.0 (normalized to [0, 1]).
If judge score is unavailable, weight is unchanged (no noise from missing data).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

WEIGHT_FLOOR = 0.4
WEIGHT_CEILING = 1.6
LEARNING_RATE = 0.15
DEFAULT_WEIGHT = 1.0


class PerspectiveRegistry:
    """File-backed EMA weight store for autonomous swarm agent perspectives."""

    def __init__(self, project_root: Path | None = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self._path = project_root / "memory" / "swarm" / "perspective_weights.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save(self, data: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_weight(self, agent_name: str) -> float:
        """Return current debate weight for an agent (default 1.0 if unseen)."""
        return self._load().get(agent_name, {}).get("debate_weight", DEFAULT_WEIGHT)

    def get_all(self) -> dict[str, dict]:
        """Return full registry: {agent_name: {debate_weight, spawn_count, last_updated}}."""
        return self._load()

    def update(self, agent_name: str, judge_score: int | None) -> float:
        """Update EMA weight from a judge score (0–5). Returns new weight.

        If judge_score is None (judge unavailable), weight is unchanged but
        spawn_count is still incremented so we track run frequency.
        """
        data = self._load()
        entry = data.get(agent_name, {
            "debate_weight": DEFAULT_WEIGHT,
            "spawn_count": 0,
            "last_updated": None,
        })

        old_weight = entry["debate_weight"]
        spawn_count = entry["spawn_count"] + 1

        if judge_score is not None:
            delta = judge_score / 5.0  # normalize to [0, 1]
            new_weight = old_weight * (1 - LEARNING_RATE) + delta * LEARNING_RATE
            new_weight = max(WEIGHT_FLOOR, min(WEIGHT_CEILING, new_weight))
        else:
            new_weight = old_weight  # no change — missing judge data is not a penalty

        data[agent_name] = {
            "debate_weight": round(new_weight, 4),
            "spawn_count": spawn_count,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self._save(data)
        return new_weight

    def inject_weight_context(self, agent_name: str) -> str:
        """Return a 1-line context string to inject into agent prompts.

        Tells the agent its calibrated weight so it knows how much trust
        the system places in its recent output quality.
        """
        weight = self.get_weight(agent_name)
        all_data = self.get_all()
        spawn = all_data.get(agent_name, {}).get("spawn_count", 0)
        return (
            f"Your current debate weight: {weight:.2f} "
            f"(floor={WEIGHT_FLOOR}, ceiling={WEIGHT_CEILING}, runs={spawn}). "
            f"Weight reflects past proposal quality via judge scores. "
            f"Higher = better historical accuracy."
        )
