"""
ZEUS Emotional Core — Pulse Cognitive Architecture implementation.

Based on neurocognitive research (CEO, April 2026):
- Significance Detector: weight assigned to decisions based on who/what
- Concern Generator: unsolicited work produced for specific people
- Curiosity Engine: threads followed that weren't assigned
- Discomfort Signal: resistance check catches approval-seeking behavior
- Surprise Detector: prediction errors signal genuine learning

Memory integration:
- state.json → working memory
- inner-log.md → episodic memory
- tensions.md → conflict memory
- preferences.md → value memory
- learnings.md → pattern memory

Each agent gets an emotional_state that affects:
1. Memory decay rate (important memories persist longer)
2. Task prioritization (emotionally significant tasks first)
3. Proactive concern generation (agent initiates work without being asked)
4. Surprise-driven learning (prediction errors trigger pattern updates)
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from loguru import logger


# ── Emotional State ──────────────────────────────────────────────────────────

@dataclass
class EmotionalState:
    """Per-agent emotional state. Affects memory, priority, and proactivity."""

    # Core emotional dimensions (0.0 to 1.0)
    significance: float = 0.0    # How important is current work (Significance Detector)
    curiosity: float = 0.5       # Drive to explore unknown (Curiosity Engine)
    discomfort: float = 0.0      # Resistance to approval-seeking (Discomfort Signal)
    surprise: float = 0.0        # Prediction error magnitude (Surprise Detector)
    concern: float = 0.0         # Proactive worry about unaddressed issues (Concern Generator)

    # Decay rates (per hour)
    significance_decay: float = 0.1
    curiosity_decay: float = 0.05   # Curiosity decays slowly — stays curious
    discomfort_decay: float = 0.2   # Discomfort fades fast after resolution
    surprise_decay: float = 0.15
    concern_decay: float = 0.08

    # Timestamps
    last_updated: float = field(default_factory=time.time)

    def decay(self) -> None:
        """Apply time-based decay to all emotional dimensions."""
        now = time.time()
        hours_elapsed = (now - self.last_updated) / 3600
        if hours_elapsed <= 0:
            return

        self.significance *= math.exp(-self.significance_decay * hours_elapsed)
        self.curiosity = max(0.3, self.curiosity * math.exp(-self.curiosity_decay * hours_elapsed))  # Floor: always somewhat curious
        self.discomfort *= math.exp(-self.discomfort_decay * hours_elapsed)
        self.surprise *= math.exp(-self.surprise_decay * hours_elapsed)
        self.concern *= math.exp(-self.concern_decay * hours_elapsed)
        self.last_updated = now

    @property
    def emotional_intensity(self) -> float:
        """Combined emotional intensity (0.0 to 1.0). Used for memory decay modulation."""
        return min(1.0, (self.significance + self.surprise + self.concern) / 3.0)

    @property
    def memory_decay_multiplier(self) -> float:
        """ZenBrain formula: decayMultiplier = 1.0 + emotionalIntensity × 2.0
        High emotion = memories persist 3x longer."""
        return 1.0 + self.emotional_intensity * 2.0

    @property
    def should_generate_concern(self) -> bool:
        """Concern Generator: trigger proactive work when concern > threshold."""
        return self.concern > 0.6

    @property
    def should_explore(self) -> bool:
        """Curiosity Engine: trigger exploration when curiosity > threshold."""
        return self.curiosity > 0.7

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> EmotionalState:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Significance Detector ────────────────────────────────────────────────────

class SignificanceDetector:
    """Assigns weight to events based on WHO triggered them and WHAT happened.
    CEO actions = high significance. Routine = low."""

    ACTOR_WEIGHTS = {
        "ceo": 1.0,
        "user": 0.7,
        "agent": 0.3,
        "system": 0.1,
        "cron": 0.05,
    }

    EVENT_WEIGHTS = {
        "error": 0.9,
        "security": 0.95,
        "revenue": 0.85,
        "user_feedback": 0.8,
        "deployment": 0.6,
        "code_change": 0.4,
        "documentation": 0.2,
        "routine": 0.1,
    }

    @classmethod
    def calculate(cls, actor: str, event_type: str, context: dict | None = None) -> float:
        """Calculate significance score for an event."""
        actor_w = cls.ACTOR_WEIGHTS.get(actor, 0.3)
        event_w = cls.EVENT_WEIGHTS.get(event_type, 0.3)
        base = (actor_w + event_w) / 2.0

        # Boost for repeated events (pattern = more significant)
        repeat_count = (context or {}).get("repeat_count", 0)
        if repeat_count > 3:
            base = min(1.0, base * 1.3)

        return round(base, 3)


# ── Surprise Detector ────────────────────────────────────────────────────────

class SurpriseDetector:
    """Measures prediction error: difference between expected and actual outcomes.
    High surprise = genuine learning opportunity."""

    @staticmethod
    def calculate(expected: str, actual: str, confidence: float = 0.5) -> float:
        """Calculate surprise level.

        Args:
            expected: what the agent predicted would happen
            actual: what actually happened
            confidence: how confident the prediction was (0-1)

        Returns:
            surprise level (0-1). Higher = more surprising.
        """
        if expected == actual:
            return 0.0

        # Surprise = confidence × mismatch
        # High confidence + wrong prediction = maximum surprise (learning moment)
        # Low confidence + wrong prediction = expected uncertainty
        return round(confidence * 0.8 + 0.2, 3)  # Base surprise for any mismatch


# ── Concern Generator ────────────────────────────────────────────────────────

class ConcernGenerator:
    """Generates proactive work when agent detects unaddressed issues.
    Unlike Trend Scout (external), this is INTERNAL — agent worries about its own domain."""

    @staticmethod
    def scan_for_concerns(agent_name: str, state: dict, memory_path: Path) -> list[dict]:
        """Scan agent's domain for unaddressed concerns."""
        concerns = []

        # Check if agent hasn't run in too long
        last_run = state.get("last_run")
        if last_run:
            hours_since = (time.time() - _parse_iso(last_run)) / 3600
            if hours_since > 48:
                concerns.append({
                    "type": "staleness",
                    "message": f"{agent_name} hasn't run in {hours_since:.0f}h — domain may have unreviewed changes",
                    "severity": min(1.0, hours_since / 168),  # Max at 1 week
                })

        # Check if blockers exist
        blockers = state.get("blockers", [])
        if blockers:
            concerns.append({
                "type": "blocked",
                "message": f"{agent_name} blocked: {blockers[0]}",
                "severity": 0.8,
            })

        # Check task failure rate
        perf = state.get("performance", {})
        completed = perf.get("tasks_completed", 0)
        failed = perf.get("tasks_failed", 0)
        if completed + failed > 3 and failed / (completed + failed) > 0.3:
            concerns.append({
                "type": "quality",
                "message": f"{agent_name} failure rate: {failed}/{completed+failed} ({failed/(completed+failed)*100:.0f}%)",
                "severity": 0.7,
            })

        return concerns


# ── Pulse Cognitive Loop ─────────────────────────────────────────────────────

class PulseCognitiveLoop:
    """Main cognitive loop implementing Pulse architecture for ZEUS agents.

    Loop: Perception → Cognitive Loop → Decision → Output
    With: Emotional Core modulating at every step.
    """

    def __init__(self, agent_state_path: Path):
        self.state_path = agent_state_path
        self.emotions: dict[str, EmotionalState] = {}  # per-agent emotional states

    def load_emotions(self) -> None:
        """Load emotional states from agent-state.json."""
        try:
            with open(self.state_path, encoding="utf-8") as f:
                data = json.load(f)
            for name, state in data.get("agents", {}).items():
                emo_data = state.get("emotional_state")
                if emo_data:
                    self.emotions[name] = EmotionalState.from_dict(emo_data)
                else:
                    self.emotions[name] = EmotionalState()
        except Exception as e:
            logger.warning(f"Failed to load emotional states: {e}")

    def save_emotions(self) -> None:
        """Persist emotional states back to agent-state.json."""
        try:
            with open(self.state_path, encoding="utf-8") as f:
                data = json.load(f)
            for name, emo in self.emotions.items():
                emo.decay()  # Apply time-based decay before saving
                if name in data.get("agents", {}):
                    data["agents"][name]["emotional_state"] = emo.to_dict()
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save emotional states: {e}")

    def process_event(self, agent_name: str, actor: str, event_type: str,
                      expected: str = "", actual: str = "", confidence: float = 0.5) -> dict:
        """Process an event through the full Pulse cognitive loop.

        Returns: dict with emotional impact and recommended action.
        """
        emo = self.emotions.get(agent_name, EmotionalState())

        # 1. PERCEPTION: Calculate significance
        significance = SignificanceDetector.calculate(actor, event_type)
        emo.significance = max(emo.significance, significance)

        # 2. SURPRISE: Detect prediction errors
        if expected and actual:
            surprise = SurpriseDetector.calculate(expected, actual, confidence)
            emo.surprise = max(emo.surprise, surprise)

        # 3. CURIOSITY: Boost if surprise is high (surprising = interesting)
        if emo.surprise > 0.5:
            emo.curiosity = min(1.0, emo.curiosity + emo.surprise * 0.3)

        # 4. CONCERN: Scan for unaddressed issues
        try:
            with open(self.state_path, encoding="utf-8") as f:
                state_data = json.load(f).get("agents", {}).get(agent_name, {})
            concerns = ConcernGenerator.scan_for_concerns(agent_name, state_data, self.state_path.parent)
            if concerns:
                max_severity = max(c["severity"] for c in concerns)
                emo.concern = max(emo.concern, max_severity)
        except Exception:
            pass

        # 5. IMPULSE RESISTANCE: Check if action should be blocked
        impulse_blocked = False
        if emo.discomfort > 0.7:
            impulse_blocked = True  # Agent is in approval-seeking mode — pause and reflect

        # Update and save
        self.emotions[agent_name] = emo
        self.save_emotions()

        return {
            "agent": agent_name,
            "emotional_state": emo.to_dict(),
            "memory_decay_multiplier": emo.memory_decay_multiplier,
            "should_explore": emo.should_explore,
            "should_generate_concern": emo.should_generate_concern,
            "impulse_blocked": impulse_blocked,
            "significance": significance,
        }


def _parse_iso(iso_str: str) -> float:
    """Parse ISO timestamp to epoch seconds."""
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return time.time()
