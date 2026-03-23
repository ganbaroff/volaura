"""
Persistent memory — decision history, model profiles, calibration log.
Stores as JSON files in ~/.swarm/ (configurable).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from loguru import logger

from .types import (
    CalibrationEntry,
    DomainTag,
    ModelProfile,
    SwarmReport,
)


class DecisionMemory:
    """JSON-file persistence for decision history and model calibration."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path.home() / ".swarm"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._profiles_path = self.data_dir / "model_profiles.json"
        self._history_path = self.data_dir / "decision_history.json"
        self._calibration_path = self.data_dir / "calibration_log.json"

    # ── Model Profiles ─────────────────────────────────

    def get_model_profiles(self) -> dict[str, ModelProfile]:
        """Load all model profiles. Key = model_name."""
        data = self._read_json(self._profiles_path, default={})
        return {k: ModelProfile(**v) for k, v in data.items()}

    def update_after_run(
        self,
        model_name: str,
        provider: str,
        latency_ms: float,
        json_valid: bool,
    ) -> None:
        """Update profile stats after a swarm evaluation (before calibration)."""
        profiles = self.get_model_profiles()
        profile = profiles.get(
            model_name,
            ModelProfile(model_name=model_name, provider=provider),
        )

        profile.total_evaluations += 1
        n = profile.total_evaluations

        # Exponential moving average for latency
        alpha = 2 / (n + 1)
        profile.avg_latency_ms = (
            alpha * latency_ms + (1 - alpha) * profile.avg_latency_ms
        )

        # JSON compliance rate
        compliance = 1.0 if json_valid else 0.0
        profile.avg_json_compliance = (
            alpha * compliance + (1 - alpha) * profile.avg_json_compliance
        )

        profile.last_updated = datetime.now(timezone.utc).isoformat()
        profiles[model_name] = profile
        self._write_json(self._profiles_path, {k: v.model_dump() for k, v in profiles.items()})

    # ── Decision History ───────────────────────────────

    def store_decision(self, report: SwarmReport) -> str:
        """Store a decision report. Returns decision_id."""
        decision_id = f"dsp-{uuid.uuid4().hex[:8]}"
        report.decision_id = decision_id

        history = self._read_json(self._history_path, default=[])
        history.append(report.model_dump())

        # Keep last 200 decisions
        if len(history) > 200:
            history = history[-200:]

        self._write_json(self._history_path, history)
        logger.info("Decision stored: {id}", id=decision_id)
        return decision_id

    # ── Calibration ────────────────────────────────────

    def calibrate(
        self,
        decision_id: str,
        actual_outcome: str,
    ) -> CalibrationEntry | None:
        """Compare prediction vs actual. Update model weights.

        actual_outcome: "better" | "worse" | "as_expected"
        Returns CalibrationEntry or None if decision not found.
        """
        history = self._read_json(self._history_path, default=[])
        decision = None
        for d in history:
            if d.get("decision_id") == decision_id:
                decision = d
                break

        if not decision:
            logger.warning("Decision {id} not found", id=decision_id)
            return None

        predicted_winner = decision.get("winner", "")
        domain_str = decision.get("config", {}).get("domain", "general")
        domain = DomainTag(domain_str) if domain_str in DomainTag.__members__.values() else DomainTag.GENERAL

        # Find which models predicted the winner
        models_correct: list[str] = []
        models_wrong: list[str] = []

        for agent in decision.get("agent_results", []):
            model = agent.get("model", "unknown")
            if agent.get("error"):
                continue
            if agent.get("winner") == predicted_winner:
                models_correct.append(model)
            else:
                models_wrong.append(model)

        # Update weights
        profiles = self.get_model_profiles()
        weight_up = 1.05
        weight_down = 0.95

        if actual_outcome == "worse":
            # The predicted winner was wrong — penalize models that chose it
            models_correct, models_wrong = models_wrong, models_correct

        for model_name in models_correct:
            if model_name in profiles:
                p = profiles[model_name]
                w = p.domain_weights.get(domain.value, p.base_weight)
                p.domain_weights[domain.value] = min(w * weight_up, 2.0)
                p.correct_predictions += 1
                p.accuracy = p.correct_predictions / max(p.total_evaluations, 1)

        for model_name in models_wrong:
            if model_name in profiles:
                p = profiles[model_name]
                w = p.domain_weights.get(domain.value, p.base_weight)
                p.domain_weights[domain.value] = max(w * weight_down, 0.3)

        self._write_json(
            self._profiles_path,
            {k: v.model_dump() for k, v in profiles.items()},
        )

        entry = CalibrationEntry(
            decision_id=decision_id,
            domain=domain,
            predicted_winner=predicted_winner,
            predicted_score=decision.get("winner_score", 0.0),
            actual_outcome=actual_outcome,
            models_correct=models_correct,
            models_wrong=models_wrong,
        )

        # Append to calibration log
        log = self._read_json(self._calibration_path, default=[])
        log.append(entry.model_dump())
        self._write_json(self._calibration_path, log)

        logger.info(
            "Calibrated {id}: {correct} correct, {wrong} wrong",
            id=decision_id,
            correct=len(models_correct),
            wrong=len(models_wrong),
        )
        return entry

    def get_competency_matrix(self) -> dict[str, dict[str, float]]:
        """Return model -> domain -> weight matrix."""
        profiles = self.get_model_profiles()
        return {
            name: profile.domain_weights
            for name, profile in profiles.items()
            if profile.domain_weights
        }

    # ── File I/O ───────────────────────────────────────

    def _read_json(self, path: Path, default: list | dict) -> list | dict:
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default

    def _write_json(self, path: Path, data: list | dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
