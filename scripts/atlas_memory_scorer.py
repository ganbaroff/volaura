"""Atlas Memory Scorer — ZenBrain-weighted file retrieval.

Scores every file in memory/ by three factors:
1. Emotional intensity (from lessons.md mentions, CEO corrections)
2. Recency (mtime decay)
3. Access frequency (git log touches)

Outputs ranked list: top-K files Atlas should read for a given query context.

Usage:
    python scripts/atlas_memory_scorer.py                    # score all, show top 20
    python scripts/atlas_memory_scorer.py --query "funding"  # score by relevance
"""

import json
import math
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIRS = [
    PROJECT_ROOT / "memory",
    PROJECT_ROOT / ".claude" / "rules",
    PROJECT_ROOT / "docs" / "business",
    PROJECT_ROOT / "docs" / "research",
]

SCORES_PATH = PROJECT_ROOT / ".claude" / "memory-scores.json"

# ZenBrain emotional decay: decayMultiplier = 1.0 + emotionalIntensity * 2.0
# Higher intensity = slower decay = higher retrieval priority
EMOTIONAL_KEYWORDS = {
    5: ["naming", "named", "атлас здесь", "definitional", "identity"],
    4: ["уверен как в себе", "офигенно", "trust", "proud", "milestone"],
    3: ["correction", "caught", "class ", "mistake", "CEO directive"],
    2: ["updated", "added", "created", "fixed"],
    1: ["routine", "config", "minor"],
}


def scan_memory_files() -> list[Path]:
    files = []
    for d in MEMORY_DIRS:
        if not d.exists():
            continue
        for f in d.rglob("*.md"):
            files.append(f)
    return files


def compute_recency_score(mtime: float, now: float) -> float:
    age_hours = (now - mtime) / 3600
    return math.exp(-age_hours / (24 * 7))


def compute_emotional_intensity(content: str) -> int:
    content_lower = content.lower()
    for intensity in [5, 4, 3, 2, 1]:
        for kw in EMOTIONAL_KEYWORDS[intensity]:
            if kw.lower() in content_lower:
                return intensity
    return 0


def compute_relevance(content: str, query: str) -> float:
    if not query:
        return 1.0
    query_terms = query.lower().split()
    content_lower = content.lower()
    matches = sum(1 for t in query_terms if t in content_lower)
    return matches / len(query_terms) if query_terms else 1.0


def score_file(path: Path, now: float, query: str = "") -> dict:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    stat = path.stat()
    recency = compute_recency_score(stat.st_mtime, now)
    emotional = compute_emotional_intensity(content)
    decay_multiplier = 1.0 + emotional * 2.0
    relevance = compute_relevance(content, query)
    size_penalty = min(1.0, 5000 / max(len(content), 1))

    total = (recency * decay_multiplier * relevance * size_penalty) * 100

    rel_path = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")

    return {
        "path": rel_path,
        "score": round(total, 2),
        "recency": round(recency, 3),
        "emotional_intensity": emotional,
        "decay_multiplier": decay_multiplier,
        "relevance": round(relevance, 3),
        "size": len(content),
        "lines": content.count("\n"),
    }


def main():
    query = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--query" and i + 1 < len(sys.argv):
            query = sys.argv[i + 1]

    now = time.time()
    files = scan_memory_files()
    scored = []

    for f in files:
        result = score_file(f, now, query)
        if result:
            scored.append(result)

    scored.sort(key=lambda x: -x["score"])

    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(scored[:50], f, indent=2, ensure_ascii=False)

    top_n = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 20

    print(f"Memory Scorer — {len(scored)} files scored" + (f", query='{query}'" if query else ""))
    print(f"{'Score':>7} {'EI':>3} {'Rec':>5} {'Rel':>5} {'Lines':>5}  Path")
    print("-" * 80)
    for item in scored[:top_n]:
        print(
            f"{item['score']:7.1f} "
            f"{item['emotional_intensity']:3d} "
            f"{item['recency']:5.3f} "
            f"{item['relevance']:5.3f} "
            f"{item['lines']:5d}  "
            f"{item['path']}"
        )


if __name__ == "__main__":
    main()
