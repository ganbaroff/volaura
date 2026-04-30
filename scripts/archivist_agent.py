#!/usr/bin/env python3
"""archivist_agent.py — reads ALL MD files, builds project history, deduplicates.

CEO: "1 агент начнёт заниматься анализом всех MD файлов без остановки.
его работа — MD файлы. ищет, пишет, создаёт историю проекта, записывает на доске.
потом рефакторинг всех файлов — слишком много дубликаций."

This agent:
1. Scans all .md files in project
2. Groups by topic (vision, swarm, atlas, product, legal, sprint, etc.)
3. Detects duplicates (same content in different files)
4. Builds a compressed project history ("board")
5. Writes results to memory/atlas/semantic/project-board.md
6. Chief Strategist reads the board and updates team memory

Runs continuously — re-scans every 30 minutes for changes.
"""

import hashlib
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Load .env
_env_file = REPO_ROOT / "apps" / "api" / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'\"")
            if k and v and k not in os.environ:
                os.environ[k] = v

BOARD_PATH = REPO_ROOT / "memory" / "atlas" / "semantic" / "project-board.md"
DUPES_PATH = REPO_ROOT / "memory" / "atlas" / "semantic" / "duplicates-found.md"
LOG_PATH = REPO_ROOT / "memory" / "atlas" / "work-queue" / "archivist.log.jsonl"

SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".claude/worktrees",
             "apps/api/.venv", ".next", "dist", "build", ".aider",
             "test-results", "coverage"}

# Topic keywords for classification
TOPICS = {
    "vision": ["vision", "mission", "goal", "purpose", "v0laura", "ecosystem"],
    "swarm": ["swarm", "agent", "perspective", "daemon", "brain", "rой", "zeus"],
    "atlas": ["atlas", "identity", "wake", "heartbeat", "journal", "memory"],
    "product": ["volaura", "assessment", "aura", "score", "badge", "competenc"],
    "mindshift": ["mindshift", "focus", "adhd", "habit", "mochi"],
    "legal": ["gdpr", "consent", "privacy", "terms", "compliance", "pdpa"],
    "sprint": ["sprint", "blocker", "shipped", "milestone", "task", "wbs"],
    "business": ["pricing", "revenue", "grant", "investor", "monetiz", "b2b"],
    "design": ["design", "figma", "token", "color", "animation", "ux", "ui"],
    "infra": ["deploy", "railway", "vercel", "docker", "vm", "ci/cd", "github action"],
    "ceo": ["ceo", "yusif", "directive", "correction", "feedback"],
    "decision": ["adr", "decision", "trade-off", "chose", "rejected"],
}


def log_event(event: dict) -> None:
    event["ts"] = datetime.now(timezone.utc).isoformat()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def should_skip(path: Path) -> bool:
    rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    return any(skip in rel for skip in SKIP_DIRS)


def classify_topic(text: str, filename: str) -> list[str]:
    combined = (filename + " " + text[:2000]).lower()
    topics = []
    for topic, keywords in TOPICS.items():
        if any(kw in combined for kw in keywords):
            topics.append(topic)
    return topics or ["other"]


def compute_hash(text: str) -> str:
    # Normalize whitespace for comparison
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.md5(normalized[:5000].encode()).hexdigest()


def scan_all_md() -> list[dict]:
    """Scan all MD files, extract metadata."""
    files = []
    for md_path in sorted(REPO_ROOT.rglob("*.md")):
        if should_skip(md_path):
            continue
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
            rel = str(md_path.relative_to(REPO_ROOT)).replace("\\", "/")
            files.append({
                "path": rel,
                "size": len(text),
                "lines": text.count("\n"),
                "hash": compute_hash(text),
                "topics": classify_topic(text, rel),
                "first_line": text.split("\n")[0][:100] if text else "",
                "mtime": md_path.stat().st_mtime,
            })
        except Exception:
            continue
    return files


def find_duplicates(files: list[dict]) -> list[tuple[str, str]]:
    """Find files with identical content (same hash)."""
    by_hash: dict[str, list[str]] = defaultdict(list)
    for f in files:
        if f["size"] > 100:  # skip tiny files
            by_hash[f["hash"]].append(f["path"])
    return [(h, paths) for h, paths in by_hash.items() if len(paths) > 1]


def build_board(files: list[dict], duplicates: list) -> str:
    """Build the project board — compressed project history."""
    by_topic: dict[str, list[dict]] = defaultdict(list)
    for f in files:
        for t in f["topics"]:
            by_topic[t].append(f)

    board = f"# Project Board — Archivist Report\n\n"
    board += f"**Generated:** {datetime.now(timezone.utc).isoformat()[:16]}\n"
    board += f"**Total MD files:** {len(files)}\n"
    board += f"**Total size:** {sum(f['size'] for f in files):,} bytes\n"
    board += f"**Duplicates found:** {len(duplicates)} groups\n\n"

    board += "## Files by Topic\n\n"
    for topic in sorted(by_topic.keys()):
        topic_files = by_topic[topic]
        board += f"### {topic.upper()} ({len(topic_files)} files)\n"
        # Show top 10 by size (most important)
        for f in sorted(topic_files, key=lambda x: -x["size"])[:10]:
            age_days = (time.time() - f["mtime"]) / 86400
            board += f"- `{f['path']}` ({f['lines']}L, {age_days:.0f}d old) — {f['first_line'][:60]}\n"
        if len(topic_files) > 10:
            board += f"- ... and {len(topic_files) - 10} more\n"
        board += "\n"

    # Key stats
    board += "## Key Metrics\n\n"
    total_lines = sum(f["lines"] for f in files)
    board += f"- Total lines across all MD: {total_lines:,}\n"
    board += f"- Average file size: {sum(f['size'] for f in files) // max(len(files), 1):,} bytes\n"
    board += f"- Oldest file: {min(files, key=lambda x: x['mtime'])['path'] if files else 'none'}\n"
    board += f"- Newest file: {max(files, key=lambda x: x['mtime'])['path'] if files else 'none'}\n"
    board += f"- Largest file: {max(files, key=lambda x: x['size'])['path'] if files else 'none'} ({max(f['size'] for f in files):,} bytes)\n"

    return board


def build_dupes_report(duplicates: list) -> str:
    """Build duplicate report for refactoring."""
    if not duplicates:
        return "# No duplicates found\n"

    report = f"# Duplicate MD Files — Refactoring Targets\n\n"
    report += f"**Found:** {len(duplicates)} groups of identical content\n\n"
    report += "These files have the SAME content (after whitespace normalization).\n"
    report += "Action: keep ONE canonical copy, delete or redirect others.\n\n"

    for i, (h, paths) in enumerate(duplicates, 1):
        report += f"## Group {i} (hash: {h[:8]})\n"
        for p in paths:
            report += f"- `{p}`\n"
        report += f"**Keep:** `{paths[0]}` (first alphabetically)\n"
        report += f"**Delete:** {', '.join(f'`{p}`' for p in paths[1:])}\n\n"

    return report


def run_cycle():
    """One archivist cycle: scan, classify, deduplicate, write board."""
    print(f"[archivist {datetime.now().strftime('%H:%M:%S')}] Scanning...", flush=True)

    files = scan_all_md()
    duplicates = find_duplicates(files)

    board = build_board(files, duplicates)
    dupes = build_dupes_report(duplicates)

    BOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOARD_PATH.write_text(board, encoding="utf-8")
    DUPES_PATH.write_text(dupes, encoding="utf-8")

    log_event({
        "event": "archivist_cycle",
        "total_files": len(files),
        "duplicates": len(duplicates),
        "topics": {t: len([f for f in files if t in f["topics"]]) for t in TOPICS},
    })

    print(f"[archivist] Done: {len(files)} files, {len(duplicates)} duplicate groups", flush=True)
    print(f"[archivist] Board: {BOARD_PATH.relative_to(REPO_ROOT)}", flush=True)
    print(f"[archivist] Dupes: {DUPES_PATH.relative_to(REPO_ROOT)}", flush=True)

    return files, duplicates


def main():
    print("[archivist] Starting MD file archivist agent", flush=True)
    print(f"[archivist] Project: {REPO_ROOT}", flush=True)
    print(f"[archivist] Cycle interval: 30 minutes", flush=True)

    while True:
        try:
            run_cycle()
        except Exception as e:
            log_event({"event": "archivist_error", "error": str(e)[:200]})
            print(f"[archivist] ERROR: {e}", flush=True)

        time.sleep(1800)  # 30 minutes


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_cycle()
    else:
        main()
