"""Atlas Filesystem Snapshot — pre-session awareness map.

Generates a compact snapshot of all project files with sizes and modification times.
On subsequent runs, diffs against previous snapshot to show what changed.
Designed to run as a session-start hook so Atlas knows the full terrain.

Usage:
    python scripts/atlas_filesystem_snapshot.py          # generate + diff
    python scripts/atlas_filesystem_snapshot.py --init   # first run, no diff
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = PROJECT_ROOT / ".claude" / "filesystem-snapshot.json"
DIFF_PATH = PROJECT_ROOT / ".claude" / "filesystem-diff.md"

SKIP_DIRS = {
    ".git", "node_modules", ".next", "__pycache__", ".turbo",
    ".vercel", "dist", "build", ".cache", ".pnpm-store",
    "models", ".ollama",
}

SKIP_EXTENSIONS = {".pyc", ".pyo", ".lock", ".tsbuildinfo"}


def scan_filesystem() -> dict:
    snapshot = {}
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = os.path.relpath(root, PROJECT_ROOT)
        for f in files:
            if any(f.endswith(ext) for ext in SKIP_EXTENSIONS):
                continue
            rel_path = os.path.join(rel_root, f).replace("\\", "/")
            if rel_path.startswith("./"):
                rel_path = rel_path[2:]
            full_path = os.path.join(root, f)
            try:
                stat = os.stat(full_path)
                snapshot[rel_path] = {
                    "size": stat.st_size,
                    "mtime": int(stat.st_mtime),
                }
            except OSError:
                continue
    return snapshot


def compute_diff(old: dict, new: dict) -> dict:
    added = {k: new[k] for k in new if k not in old}
    removed = {k: old[k] for k in old if k not in new}
    modified = {
        k: {"old_size": old[k]["size"], "new_size": new[k]["size"]}
        for k in new
        if k in old and (new[k]["size"] != old[k]["size"] or new[k]["mtime"] != old[k]["mtime"])
    }
    return {"added": added, "removed": removed, "modified": modified}


def format_diff_md(diff: dict, total_files: int) -> str:
    lines = [f"# Filesystem Diff — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"]
    lines.append(f"Total files: {total_files}")
    lines.append("")

    if not diff["added"] and not diff["removed"] and not diff["modified"]:
        lines.append("No changes since last snapshot.")
        return "\n".join(lines)

    if diff["added"]:
        lines.append(f"## Added ({len(diff['added'])} files)")
        for p in sorted(diff["added"])[:30]:
            lines.append(f"  + {p} ({diff['added'][p]['size']}B)")
        if len(diff["added"]) > 30:
            lines.append(f"  ... and {len(diff['added']) - 30} more")

    if diff["removed"]:
        lines.append(f"## Removed ({len(diff['removed'])} files)")
        for p in sorted(diff["removed"])[:30]:
            lines.append(f"  - {p}")
        if len(diff["removed"]) > 30:
            lines.append(f"  ... and {len(diff['removed']) - 30} more")

    if diff["modified"]:
        lines.append(f"## Modified ({len(diff['modified'])} files)")
        for p in sorted(diff["modified"])[:30]:
            m = diff["modified"][p]
            lines.append(f"  ~ {p} ({m['old_size']}B → {m['new_size']}B)")
        if len(diff["modified"]) > 30:
            lines.append(f"  ... and {len(diff['modified']) - 30} more")

    return "\n".join(lines)


def dir_summary(snapshot: dict) -> dict:
    dirs = {}
    for path in snapshot:
        parts = path.split("/")
        if len(parts) > 1:
            top = parts[0]
            dirs[top] = dirs.get(top, 0) + 1
    return dict(sorted(dirs.items(), key=lambda x: -x[1]))


def main():
    init_mode = "--init" in sys.argv

    new_snapshot = scan_filesystem()

    if SNAPSHOT_PATH.exists() and not init_mode:
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            old_snapshot = json.load(f)
        diff = compute_diff(old_snapshot, new_snapshot)
        diff_md = format_diff_md(diff, len(new_snapshot))
    else:
        diff = {"added": {}, "removed": {}, "modified": {}}
        diff_md = f"# Initial Filesystem Snapshot — {len(new_snapshot)} files\n"
        summary = dir_summary(new_snapshot)
        for d, count in list(summary.items())[:20]:
            diff_md += f"  {d}/: {count} files\n"

    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(new_snapshot, f)

    with open(DIFF_PATH, "w", encoding="utf-8") as f:
        f.write(diff_md)

    print(diff_md[:2000])

    a = len(diff["added"])
    r = len(diff["removed"])
    m = len(diff["modified"])
    if a or r or m:
        print(f"\nΔ +{a} -{r} ~{m} files changed since last snapshot")


if __name__ == "__main__":
    main()
