#!/bin/bash
# PERIODIC CHECKPOINT: Called by /loop every 30 minutes
# Saves incremental session state so context isn't lost even without compaction
# Usage: /loop 30m save session checkpoint

MEMORY_DIR="$HOME/.claude/projects/C--Projects-VOLAURA/memory"
PERIODIC_FILE="$MEMORY_DIR/session_periodic_state.md"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

mkdir -p "$MEMORY_DIR"

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
MODIFIED=$(git diff --stat 2>/dev/null | tail -1)

cat > "$PERIODIC_FILE" << STATE
# Session State — $TIMESTAMP (auto-checkpoint)
- Branch: $BRANCH
- Changes: $MODIFIED
- Last 3 commits: $(git log --oneline -3 2>/dev/null)
STATE

echo "Checkpoint saved at $TIMESTAMP" >&2
exit 0
