#!/bin/bash
# PRE-COMPACT HOOK: Saves session state BEFORE context compaction
# This runs automatically when Claude Code is about to compress conversation
# Everything saved here gets re-injected by post-compact-restore.sh

MEMORY_DIR="$HOME/.claude/projects/C--Projects-VOLAURA/memory"
STATE_FILE="$MEMORY_DIR/context_checkpoint.md"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

mkdir -p "$MEMORY_DIR"

# Get git state
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
RECENT_COMMITS=$(git log --oneline -5 2>/dev/null || echo "none")
MODIFIED_FILES=$(git diff --name-only 2>/dev/null | head -10)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | head -10)

# Get todo state if exists
TODO_STATE=""
if [ -f ".claude/todos.json" ]; then
  TODO_STATE=$(cat .claude/todos.json 2>/dev/null | head -20)
fi

cat > "$STATE_FILE" << CHECKPOINT
---
name: Pre-compaction checkpoint
description: Auto-saved before context compaction. Read by post-compact-restore.sh to re-inject context.
type: project
---

# Context Checkpoint — $TIMESTAMP

## Git State
- Branch: $BRANCH
- Recent commits:
$RECENT_COMMITS

## Modified Files (uncommitted)
$MODIFIED_FILES

## Untracked Files
$UNTRACKED

## Active Tasks
$TODO_STATE

## IMPORTANT: After reading this, immediately:
1. Read docs/ROADMAP.md for current priorities
2. Read docs/MANDATORY-RULES.md for 7 rules
3. Check memory/MEMORY.md for full context index
4. Continue work from where it was interrupted — do NOT start over
CHECKPOINT

echo "Pre-compact checkpoint saved to $STATE_FILE" >&2
exit 0
