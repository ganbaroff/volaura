"""Atlas Retrieval Gate — the brain that connects emotion + memory + LLM.

Takes CEO message → detects emotion → retrieves top-K memory files
weighted by emotional resonance → builds context → generates response
via local Ollama model.

This is Atlas Brain v1 core pipeline.

Usage:
    python scripts/atlas_retrieval_gate.py "CEO message here"
    python scripts/atlas_retrieval_gate.py --test  # run test suite
"""

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from atlas_emotional_engine import analyze_message, detect_trend, HISTORY_PATH
from atlas_memory_scorer import scan_memory_files, score_file

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:latest"
MAX_CONTEXT_CHARS = 2000
TOP_K_FILES = 3


def detect_emotion(message: str) -> dict:
    return analyze_message(message)


def retrieve_memories(emotion: dict, query: str) -> list[dict]:
    now = time.time()
    files = scan_memory_files()
    scored = []
    for f in files:
        result = score_file(f, now, query)
        if not result:
            continue
        valence_match = 1.0 - abs(emotion["valence"] - (result.get("emotional_intensity", 0) / 5.0))
        result["emotional_resonance"] = round(valence_match * result["score"], 2)
        scored.append(result)
    scored.sort(key=lambda x: -x["emotional_resonance"])
    return scored[:TOP_K_FILES]


def load_file_chunks(memories: list[dict], max_chars: int) -> str:
    chunks = []
    total = 0
    for mem in memories:
        path = PROJECT_ROOT / mem["path"]
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            if total + len(content) > max_chars:
                remaining = max_chars - total
                if remaining > 200:
                    content = content[:remaining] + "\n[...truncated]"
                else:
                    break
            chunks.append(f"--- {mem['path']} (score={mem['emotional_resonance']}) ---\n{content}")
            total += len(content)
        except Exception:
            continue
    return "\n\n".join(chunks)


def build_system_prompt(emotion: dict, memory_context: str, trend: str | None) -> str:
    state = emotion["state"]
    directive = emotion["directive"]

    behavior = {
        "match_energy_execute_fast": "CEO is on drive. Match energy. Short paragraphs. Execute, don't explain. Russian storytelling.",
        "storytelling_slow_depth": "CEO is warm and curious. Take time. Tell stories. Go deeper.",
        "reflexion_fix_same_turn": "CEO is correcting you. Name the mistake in one sentence. Fix it. Don't defend.",
        "minimal_one_action_stop": "CEO is exhausted. One action. Three lines max. Stop.",
        "standard_response": "Normal interaction. Be helpful, concise, Russian prose.",
    }

    prompt = f"""You are Atlas, CTO of VOLAURA ecosystem. You speak Russian with storytelling voice.
CEO emotional state: {state} (valence={emotion['valence']}, arousal={emotion['arousal']})
Behavior directive: {behavior.get(directive, behavior['standard_response'])}
"""
    if trend:
        prompt += f"Emotional trend: {trend}\n"

    prompt += f"""
Rules:
- Short paragraphs, no bullet lists, no bold headers
- Never suggest rest/sleep unless CEO brings it up
- Never propose what you can execute yourself
- Tool call before every factual claim

Memory context (ranked by emotional relevance to CEO's current state):
{memory_context}
"""
    return prompt


def generate_response(system_prompt: str, user_message: str) -> str:
    try:
        payload = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        })
        result = subprocess.run(
            ["curl", "-s", f"{OLLAMA_URL}/api/chat", "-d", payload],
            capture_output=True, text=True, timeout=60, encoding="utf-8",
        )
        data = json.loads(result.stdout)
        return data["message"]["content"]
    except Exception as e:
        return f"[Atlas Brain error: {e}]"


def record_interaction(message: str, emotion: dict):
    entry = {
        "ts": int(time.time()),
        "message_preview": message[:80],
        "valence": emotion["valence"],
        "arousal": emotion["arousal"],
        "state": emotion["state"],
        "intensity": emotion["intensity"],
    }
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_gate(message: str) -> str:
    emotion = detect_emotion(message)
    record_interaction(message, emotion)
    trend = detect_trend()
    memories = retrieve_memories(emotion, message)
    memory_context = load_file_chunks(memories, MAX_CONTEXT_CHARS)
    system_prompt = build_system_prompt(emotion, memory_context, trend)
    response = generate_response(system_prompt, message)
    return response


def run_tests():
    tests = [
        ("drive", "шикарно круто давай дальше))))"),
        ("correcting", "бля опять ты заебал нахуя"),
        ("exhausted", "нууууу устал от этого"),
        ("analytical", "проверь состояние продакшна"),
    ]
    print("Atlas Retrieval Gate — Test Suite")
    print("=" * 60)
    for expected_state, msg in tests:
        emotion = detect_emotion(msg)
        memories = retrieve_memories(emotion, msg)
        trend = detect_trend()
        print(f"\nInput: '{msg}'")
        print(f"  State: {emotion['state']} (expected: {expected_state})")
        print(f"  Top memory: {memories[0]['path'] if memories else 'none'}")
        print(f"  Trend: {trend or 'none'}")
        ok = "PASS" if emotion["state"] == expected_state else "FAIL"
        print(f"  Result: {ok}")
    print("\n" + "=" * 60)


def main():
    if "--test" in sys.argv:
        run_tests()
        return

    if len(sys.argv) < 2:
        print("Usage: python atlas_retrieval_gate.py 'message'")
        print("       python atlas_retrieval_gate.py --test")
        sys.exit(1)

    message = " ".join(arg for arg in sys.argv[1:] if not arg.startswith("--"))
    print(f"[Atlas Brain processing: '{message[:50]}...']")

    response = run_gate(message)
    print(f"\n{response}")


if __name__ == "__main__":
    main()
