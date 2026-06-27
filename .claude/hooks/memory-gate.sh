#!/bin/bash
# Claude Code PreToolUse hook — Memory Gate (persistent check)
# Warns every 15 min if session >30 min with no episode/breadcrumb today.

PROJECT_DIR="C:/Projects/VOLAURA"
EPISODES_DIR="$PROJECT_DIR/memory/atlas/episodes"
BREADCRUMB="$PROJECT_DIR/.claude/breadcrumb.md"
SESSION_START_FILE="$PROJECT_DIR/.claude/.session-start.epoch"
LAST_CHECK_FILE="$PROJECT_DIR/.claude/.last-memory-gate.epoch"
CHECK_INTERVAL=900
WARN_THRESHOLD=30

TODAY=$(date +%Y-%m-%d)
NOW_EPOCH=$(date +%s)

if [ ! -f "$SESSION_START_FILE" ]; then
    echo "$NOW_EPOCH" > "$SESSION_START_FILE"
    exit 0
fi

if [ -f "$LAST_CHECK_FILE" ]; then
    LAST_CHECK=$(cat "$LAST_CHECK_FILE")
    ELAPSED=$((NOW_EPOCH - LAST_CHECK))
    if [ "$ELAPSED" -lt "$CHECK_INTERVAL" ]; then
        exit 0
    fi
fi
echo "$NOW_EPOCH" > "$LAST_CHECK_FILE"

SESSION_START=$(cat "$SESSION_START_FILE")
SESSION_MIN=$(( (NOW_EPOCH - SESSION_START) / 60 ))

TODAY_EPISODE=$(find "$EPISODES_DIR" -name "${TODAY}*" 2>/dev/null | wc -l)

BREADCRUMB_TODAY=0
if [ -f "$BREADCRUMB" ]; then
    BREADCRUMB_MTIME=$(stat -c %Y "$BREADCRUMB" 2>/dev/null || stat -f %m "$BREADCRUMB" 2>/dev/null || echo 0)
    BREADCRUMB_AGE=$(( NOW_EPOCH - BREADCRUMB_MTIME ))
    if [ "$BREADCRUMB_AGE" -lt 86400 ]; then
        BREADCRUMB_TODAY=1
    fi
fi

ANY_WRITE_BACK=$(( TODAY_EPISODE + BREADCRUMB_TODAY ))

if [ "$SESSION_MIN" -gt "$WARN_THRESHOLD" ] && [ "$ANY_WRITE_BACK" -eq 0 ]; then
    echo ""
    echo "MEMORY GATE — Session ${SESSION_MIN} min, no write-back detected."
    echo "Write breadcrumb or episode NOW. 56 days of amnesia proven."
    echo ""
fi

exit 0
