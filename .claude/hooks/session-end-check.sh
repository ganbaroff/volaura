#!/bin/bash
# Stop hook (advisory) — reminds CTO to update memory before session ends.
# Does NOT block (exit 0 always) — advisory per team recommendation.
# stdout → Claude sees this reminder.

# Check if sprint-state.md was modified in the last 2 hours
STATE_FILE="memory/context/sprint-state.md"

if [ -f "$STATE_FILE" ]; then
  # Get file modification time (works on Git Bash / Windows)
  MOD_TIME=$(stat -c %Y "$STATE_FILE" 2>/dev/null || stat -f %m "$STATE_FILE" 2>/dev/null || echo 0)
  NOW=$(date +%s)
  DIFF=$((NOW - MOD_TIME))

  # If not modified in last 2 hours (7200 seconds), warn
  if [ "$DIFF" -gt 7200 ]; then
    cat <<'REMINDER'
══════════════════════════════════════════════════════════════
⚠️  SESSION END — MEMORY UPDATE CHECK
══════════════════════════════════════════════════════════════

sprint-state.md was NOT updated this session. Before ending:

□ Update memory/context/sprint-state.md (current position + next)
□ Update docs/DECISIONS.md (retrospective if sprint step done)
□ Update memory/context/mistakes.md (new mistakes if any)
□ Model recommendation for next session

This is advisory — session CAN end. But next session starts blind.
══════════════════════════════════════════════════════════════
REMINDER
  fi
fi

# Always allow session end (advisory, not blocking — per team review)
exit 0
