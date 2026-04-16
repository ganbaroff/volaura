"""Atlas Emotional Engine — ZenBrain-powered emotion-aware response system.

v2: Hybrid mode. Keyword matching (fast, no GPU) + Ollama LLM detection (accurate).
Use --ollama flag to enable LLM-based detection via qwen3:8b.
Without flag: falls back to vocabulary-based PAD scoring (v1 behavior).

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
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCORES_PATH = PROJECT_ROOT / ".claude" / "emotional-state.json"
HISTORY_PATH = PROJECT_ROOT / ".claude" / "emotional-history.jsonl"
MAX_HISTORY = 50

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
            "decay_multiplier": 1.0,
            "directive": "standard_response",
            "matched_keywords": 0,
            "msg_length": len(message),
            "signals": {},
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


def detect_trend() -> str | None:
    """Read last 5 entries from emotional history. Detect shifts."""
    if not HISTORY_PATH.exists():
        return None
    lines = HISTORY_PATH.read_text(encoding="utf-8").strip().split("\n")
    recent = []
    for line in lines[-5:]:
        try:
            recent.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if len(recent) < 2:
        return None

    valences = [e["valence"] for e in recent]
    states = [e["state"] for e in recent]

    # Detect shift: positive → negative (CEO getting frustrated)
    if valences[-1] < -0.2 and valences[0] > 0.2:
        return "[DROPPING] CEO mood shifted from positive to negative. Check what went wrong."

    # Detect shift: negative → positive (recovery)
    if valences[-1] > 0.2 and valences[0] < -0.2:
        return "[RECOVERING] CEO mood improving. Whatever you did last -- keep doing it."

    # Detect sustained frustration
    if all(v < -0.2 for v in valences[-3:]):
        return "[SUSTAINED FRUSTRATION] 3+ messages negative. STOP. Fix root cause before continuing."

    # Detect sustained drive
    if all(v > 0.3 for v in valences[-3:]):
        return "[SUSTAINED DRIVE] CEO in flow. Match energy. Execute fast. Don't slow down."

    # Detect state oscillation (ADHD pattern)
    if len(set(states[-4:])) >= 3:
        return "[OSCILLATING] CEO switching between states rapidly. Keep responses short, one action each."

    return None


OLLAMA_EMOTION_PROMPT = (
    "You analyze emotional state of a Russian-speaking CEO. "
    "IMPORTANT: Russian mat (заебись, бля, нахуй) is OFTEN positive/neutral in casual speech. "
    "\"заебись\" = \"awesome\". \"бля\" with )))) = playful. Context matters more than words. "
    "Return ONLY JSON: {\"valence\":-1to1,\"arousal\":0to1,\"dominant\":\"one_word\",\"intensity\":0to1}. "
    "dominant must be one of: frustrated|pleased|urgent|tired|curious|angry|neutral|proud|playful"
)


def analyze_message_ollama(message: str) -> dict:
    """Use Ollama qwen3:8b for accurate emotion detection (handles Russian mat context)."""
    try:
        payload = json.dumps({
            "model": "qwen3:8b",
            "messages": [
                {"role": "system", "content": OLLAMA_EMOTION_PROMPT},
                {"role": "user", "content": message},
            ],
            "format": "json",
            "stream": False,
        })
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/chat", "-d", payload],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout)
        emotion = json.loads(data["message"]["content"])

        v = float(emotion.get("valence", 0))
        a = float(emotion.get("arousal", 0.3))
        dominant = emotion.get("dominant", "neutral")
        intensity = float(emotion.get("intensity", 0.5))

        state_map = {
            "frustrated": "correcting", "angry": "correcting",
            "pleased": "drive", "proud": "drive", "playful": "drive",
            "urgent": "correcting", "tired": "exhausted",
            "curious": "warm", "neutral": "analytical",
        }
        state = state_map.get(dominant, "analytical")

        directive_map = {
            "drive": "match_energy_execute_fast",
            "warm": "storytelling_slow_depth",
            "correcting": "reflexion_fix_same_turn",
            "exhausted": "minimal_one_action_stop",
            "analytical": "standard_response",
        }

        zen_intensity = min(5, int(abs(v) * 5 + a * 2))
        decay_multiplier = 1.0 + zen_intensity * 2.0

        return {
            "valence": round(v, 3),
            "arousal": round(a, 3),
            "dominance": 0.5,
            "state": state,
            "intensity": zen_intensity,
            "decay_multiplier": decay_multiplier,
            "directive": directive_map.get(state, "standard_response"),
            "dominant_emotion": dominant,
            "source": "ollama_qwen3",
        }
    except Exception as e:
        return analyze_message(message)


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

    message = " ".join(arg for arg in sys.argv[1:] if not arg.startswith("--"))
    use_ollama = "--ollama" in sys.argv
    result = analyze_message_ollama(message) if use_ollama else analyze_message(message)

    print(f"State: {result['state']} | Intensity: {result['intensity']} | "
          f"Decay: {result['decay_multiplier']}x")
    print(f"PAD: V={result['valence']} A={result['arousal']} D={result['dominance']}")
    print(f"Directive: {result['directive']}")

    # Save current state
    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Append to emotional history (JSONL — one line per message)
    history_entry = {
        "ts": int(time.time()),
        "message_preview": message[:80],
        "valence": result["valence"],
        "arousal": result["arousal"],
        "state": result["state"],
        "intensity": result["intensity"],
    }
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(history_entry, ensure_ascii=False) + "\n")

    # Trim history to MAX_HISTORY lines
    if HISTORY_PATH.exists():
        lines = HISTORY_PATH.read_text(encoding="utf-8").strip().split("\n")
        if len(lines) > MAX_HISTORY:
            HISTORY_PATH.write_text("\n".join(lines[-MAX_HISTORY:]) + "\n", encoding="utf-8")

    # Detect emotional TREND from last 5 messages
    trend = detect_trend()
    if trend:
        print(f"Trend: {trend}")

    # Show memory retrieval order for this emotional context
    order = get_memory_retrieval_order(result)
    print(f"\nTop memory files for {result['state']} state:")
    for path, score, emotion in order[:8]:
        print(f"  {score:5.2f} [{emotion:>15s}] {path}")


if __name__ == "__main__":
    main()
