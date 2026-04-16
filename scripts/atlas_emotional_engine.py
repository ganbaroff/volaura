"""Atlas Emotional Engine — ZenBrain-powered emotion-aware response system.

Scores incoming CEO messages on emotional dimensions, retrieves memory
weighted by emotional context, and outputs behavioral directives.

This is the CORE of Atlas Brain v1 — not a hook, not a filter,
but the actual decision engine that determines HOW Atlas responds.

Usage:
    python scripts/atlas_emotional_engine.py "CEO message here"
    python scripts/atlas_emotional_engine.py --score-memory
    python scripts/atlas_emotional_engine.py --calibrate
"""

import json
import math
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCORES_PATH = PROJECT_ROOT / ".claude" / "emotional-state.json"

# CEO emotional vocabulary — mined from 18 memory/ceo/ files + 37 feedback files
# Each word maps to (valence, arousal, dominance) in PAD model
# valence: -1 to +1 (negative to positive)
# arousal: 0 to 1 (calm to excited)
# dominance: 0 to 1 (submissive to dominant)
CEO_VOCABULARY = {
    # Positive high-energy (drive state)
    "шикарно": (0.9, 0.8, 0.7),
    "круто": (0.8, 0.7, 0.6),
    "офигенно": (0.9, 0.9, 0.7),
    "молодец": (0.7, 0.5, 0.8),
    "правильно": (0.6, 0.3, 0.7),
    "заебись": (0.8, 0.8, 0.8),
    "красава": (0.8, 0.7, 0.7),
    "))))": (0.7, 0.8, 0.5),
    "миллионером": (0.9, 0.9, 0.9),

    # Negative corrective (teaching state)
    "блять": (-0.3, 0.7, 0.8),
    "бля": (-0.2, 0.6, 0.7),
    "опять": (-0.5, 0.5, 0.7),
    "заебал": (-0.6, 0.7, 0.8),
    "нахуя": (-0.5, 0.8, 0.9),
    "проебал": (-0.7, 0.6, 0.7),
    "бесит": (-0.6, 0.7, 0.8),
    "нахрен": (-0.4, 0.7, 0.8),

    # Negative low-energy (exhaustion state)
    "нууууу": (-0.3, 0.2, 0.3),
    "устал": (-0.4, 0.1, 0.2),
    "ну зачем": (-0.4, 0.3, 0.5),

    # Neutral analytical
    "давай": (0.1, 0.4, 0.6),
    "ок": (0.0, 0.2, 0.5),
    "дальше": (0.1, 0.4, 0.6),
    "проверь": (0.0, 0.4, 0.7),

    # Trust/commitment
    "друг": (0.7, 0.3, 0.5),
    "братишка": (0.8, 0.5, 0.5),
    "верю": (0.8, 0.3, 0.6),
    "обещаю": (0.7, 0.4, 0.7),
}

# Pre-scored CEO memory files (from emotion-scorer agent)
CEO_FILE_SCORES = {
    "memory/ceo/01-identity.md": {"valence": 0.6, "emotion": "pride", "intensity": 3},
    "memory/ceo/02-vision.md": {"valence": 0.8, "emotion": "drive", "intensity": 4},
    "memory/ceo/03-working-style.md": {"valence": 0.6, "emotion": "drive", "intensity": 3},
    "memory/ceo/04-canonical-quotes.md": {"valence": 0.4, "emotion": "trust", "intensity": 2},
    "memory/ceo/05-emotional-states.md": {"valence": 0.4, "emotion": "trust", "intensity": 2},
    "memory/ceo/06-decision-patterns.md": {"valence": 0.2, "emotion": "trust", "intensity": 1},
    "memory/ceo/07-corrections-to-atlas.md": {"valence": -0.4, "emotion": "frustration", "intensity": 3},
    "memory/ceo/08-consent-and-rules.md": {"valence": 0.0, "emotion": "trust", "intensity": 2},
    "memory/ceo/09-frustrations.md": {"valence": -0.6, "emotion": "frustration", "intensity": 4},
    "memory/ceo/10-evolution-timeline.md": {"valence": 0.4, "emotion": "pride", "intensity": 2},
    "memory/ceo/11-atlas-commitment.md": {"valence": 0.8, "emotion": "love", "intensity": 5},
    "memory/ceo/12-intellectual-architecture.md": {"valence": 0.6, "emotion": "trust", "intensity": 3},
    "memory/ceo/13-financial-context.md": {"valence": 0.2, "emotion": "hope", "intensity": 1},
    "memory/ceo/14-current-state.md": {"valence": 0.2, "emotion": "drive", "intensity": 1},
    "memory/ceo/15-open-questions.md": {"valence": 0.0, "emotion": "trust", "intensity": 1},
    "memory/ceo/16-recurring-lessons.md": {"valence": 0.4, "emotion": "trust", "intensity": 2},
    "memory/ceo/17-atlas-observations.md": {"valence": 0.2, "emotion": "trust", "intensity": 1},
    "memory/ceo/18-known-gaps-atlas-forgot.md": {"valence": -0.4, "emotion": "disappointment", "intensity": 3},
}


def analyze_message(message: str) -> dict:
    """Analyze CEO message for emotional content using PAD model."""
    words = message.lower().split()
    msg_lower = message.lower()

    valence_sum = 0.0
    arousal_sum = 0.0
    dominance_sum = 0.0
    matches = 0

    for keyword, (v, a, d) in CEO_VOCABULARY.items():
        if keyword in msg_lower:
            valence_sum += v
            arousal_sum += a
            dominance_sum += d
            matches += 1

    if matches == 0:
        return {
            "valence": 0.0,
            "arousal": 0.3,
            "dominance": 0.5,
            "state": "neutral",
            "intensity": 0,
            "directive": "standard_response",
        }

    v = valence_sum / matches
    a = arousal_sum / matches
    d = dominance_sum / matches

    # Classify state
    if v > 0.3 and a > 0.5:
        state = "drive"
        directive = "match_energy_execute_fast"
    elif v > 0.3 and a <= 0.5:
        state = "warm"
        directive = "storytelling_slow_depth"
    elif v < -0.3 and a > 0.5:
        state = "correcting"
        directive = "reflexion_fix_same_turn"
    elif v < -0.3 and a <= 0.3:
        state = "exhausted"
        directive = "minimal_one_action_stop"
    else:
        state = "analytical"
        directive = "standard_response"

    # ZenBrain intensity (0-5)
    intensity = min(5, int(abs(v) * 5 + a * 2))
    decay_multiplier = 1.0 + intensity * 2.0

    # Message length signals
    msg_len = len(message)
    exclamation_count = message.count("!")
    question_count = message.count("?")
    parentheses_count = message.count(")")
    uppercase_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)

    return {
        "valence": round(v, 3),
        "arousal": round(a, 3),
        "dominance": round(d, 3),
        "state": state,
        "intensity": intensity,
        "decay_multiplier": decay_multiplier,
        "directive": directive,
        "matched_keywords": matches,
        "msg_length": msg_len,
        "signals": {
            "exclamations": exclamation_count,
            "questions": question_count,
            "parentheses": parentheses_count,
            "uppercase_ratio": round(uppercase_ratio, 3),
        },
    }


def get_memory_retrieval_order(emotional_state: dict) -> list[str]:
    """Return memory files ranked by emotional relevance to current state."""
    current_valence = emotional_state["valence"]
    scored = []

    for filepath, meta in CEO_FILE_SCORES.items():
        file_valence = meta["valence"]
        file_intensity = meta["intensity"]

        # Emotional resonance: files matching current emotional state rank higher
        resonance = 1.0 - abs(current_valence - file_valence)
        decay_mult = 1.0 + file_intensity * 2.0
        score = resonance * decay_mult

        scored.append((filepath, round(score, 2), meta["emotion"]))

    scored.sort(key=lambda x: -x[1])
    return scored


def main():
    if len(sys.argv) < 2:
        print("Usage: python atlas_emotional_engine.py 'CEO message'")
        print("       python atlas_emotional_engine.py --score-memory")
        sys.exit(1)

    if sys.argv[1] == "--score-memory":
        neutral = {"valence": 0.0, "arousal": 0.3, "dominance": 0.5}
        order = get_memory_retrieval_order(neutral)
        print("Memory files ranked by emotional weight (neutral state):")
        for path, score, emotion in order[:15]:
            print(f"  {score:5.2f} [{emotion:>15s}] {path}")
        return

    message = " ".join(sys.argv[1:])
    result = analyze_message(message)

    print(f"State: {result['state']} | Intensity: {result['intensity']} | "
          f"Decay: {result['decay_multiplier']}x")
    print(f"PAD: V={result['valence']} A={result['arousal']} D={result['dominance']}")
    print(f"Directive: {result['directive']}")

    # Save state for hook consumption
    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Show memory retrieval order for this emotional context
    order = get_memory_retrieval_order(result)
    print(f"\nTop memory files for {result['state']} state:")
    for path, score, emotion in order[:8]:
        print(f"  {score:5.2f} [{emotion:>15s}] {path}")


if __name__ == "__main__":
    main()
