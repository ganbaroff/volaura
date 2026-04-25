#!/bin/bash
# PRE-COMPACT HOOK: saves only session-local delta before context compaction.
# The post-compact hook re-injects this delta plus canonical source pointers.

MEMORY_DIR="$HOME/.claude/projects/C--Projects-VOLAURA/memory"
STATE_FILE="$MEMORY_DIR/context_checkpoint.md"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BREADCRUMB="$PROJECT_DIR/.claude/breadcrumb.md"
TODO_FILE="$PROJECT_DIR/.claude/todos.json"
PYTHON_BIN="$(command -v python 2>/dev/null || command -v python3 2>/dev/null || true)"

mkdir -p "$MEMORY_DIR"

if [ -n "$PYTHON_BIN" ]; then
  BAKU_TIME=$("$PYTHON_BIN" - <<'PY' 2>/dev/null
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    print(datetime.now(ZoneInfo("Asia/Baku")).strftime("%Y-%m-%d %H:%M %A"))
except Exception:
    print(datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
PY
  )
else
  BAKU_TIME=""
fi

if [ -z "$BAKU_TIME" ]; then
  BAKU_TIME="$(date '+%Y-%m-%d %H:%M')"
fi

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
MODIFIED_FILES=$(git diff --name-only 2>/dev/null | head -10)
if [ -z "$MODIFIED_FILES" ]; then
  MODIFIED_FILES="(none)"
fi

if [ -n "$PYTHON_BIN" ]; then
  BREADCRUMB_DELTA=$("$PYTHON_BIN" - "$BREADCRUMB" <<'PY' 2>/dev/null
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

path = pathlib.Path(sys.argv[1])
if not path.exists():
    print("LAST_ACTION=(breadcrumb missing)")
    print("NEXT_STEP=(breadcrumb missing)")
    raise SystemExit

text = path.read_text(encoding="utf-8")
lines = text.splitlines()
sections = {}
current = None
for line in lines:
    if line.startswith("## "):
        current = line[3:].strip().lower()
        sections[current] = []
    elif current is not None:
        sections[current].append(line)

def clean(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^\d+\.\s+", "", line)
    line = re.sub(r"^[-*]\s+", "", line)
    line = line.replace("**", "").replace("`", "").replace("~~", "")
    return " ".join(line.split())

def first_item(section_names):
    for section_name in section_names:
        for heading, section_lines in sections.items():
            if section_name in heading:
                for raw_line in section_lines:
                    stripped = raw_line.strip()
                    if not stripped:
                        continue
                    if re.match(r"^(?:[-*]|\d+\.)\s+", stripped):
                        value = clean(stripped)
                        if value:
                            return value
    return None

last_action = first_item(["completed this session", "round 2 summary"])
next_step = first_item(["what's next", "what’s next", "next"])

if last_action is None:
    match = re.search(r"\*\*Last update:\*\*\s*(.+)", text)
    if match:
        last_action = clean(match.group(1))

if next_step is None:
    next_step = "(no explicit next step found)"

if last_action is None:
    last_action = "(no explicit last action found)"

print(f"LAST_ACTION={last_action}")
print(f"NEXT_STEP={next_step}")
PY
  )
else
  BREADCRUMB_DELTA="LAST_ACTION=(python unavailable)
NEXT_STEP=(python unavailable)"
fi

LAST_ACTION=$(printf '%s\n' "$BREADCRUMB_DELTA" | sed -n 's/^LAST_ACTION=//p')
NEXT_STEP=$(printf '%s\n' "$BREADCRUMB_DELTA" | sed -n 's/^NEXT_STEP=//p')

if [ -z "$LAST_ACTION" ]; then
  LAST_ACTION="(no explicit last action found)"
fi

if [ -z "$NEXT_STEP" ]; then
  NEXT_STEP="(no explicit next step found)"
fi

if [ -n "$PYTHON_BIN" ]; then
  ACTIVE_HINTS=$("$PYTHON_BIN" - "$TODO_FILE" <<'PY' 2>/dev/null
import json
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

path = pathlib.Path(sys.argv[1])
if not path.exists():
    print("(none)")
    raise SystemExit

try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("(unparsed)")
    raise SystemExit

if isinstance(data, dict):
    if isinstance(data.get("todos"), list):
        items = data["todos"]
    elif isinstance(data.get("items"), list):
        items = data["items"]
    else:
        items = []
elif isinstance(data, list):
    items = data
else:
    items = []

parts = []
for item in items:
    if not isinstance(item, dict):
        continue
    status = item.get("status", "todo")
    if status not in {"in_progress", "todo", "blocked"}:
        continue
    title = item.get("title") or item.get("task") or item.get("text")
    if not title:
        continue
    parts.append(f"{status}: {title}")
    if len(parts) == 4:
        break

print(" ; ".join(parts) if parts else "(none)")
PY
  )
else
  ACTIVE_HINTS="(python unavailable)"
fi

if [ -z "$ACTIVE_HINTS" ]; then
  ACTIVE_HINTS="(none)"
fi

cat > "$STATE_FILE" <<CHECKPOINT
---
name: Session delta before compaction
description: Session-local delta only. Canonical sources are re-injected separately by post-compact-restore.sh.
type: project
---

# Session Delta — $BAKU_TIME

- Branch: $BRANCH
- Modified files:
$MODIFIED_FILES
- Last declared action: $LAST_ACTION
- Next step: $NEXT_STEP
- Active task hints: $ACTIVE_HINTS

Compact rule: continue from breadcrumb, do not restart the project from memory theater.
CHECKPOINT

echo "Pre-compact checkpoint saved to $STATE_FILE" >&2
exit 0
