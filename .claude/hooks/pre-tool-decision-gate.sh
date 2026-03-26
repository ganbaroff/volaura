#!/bin/bash
# PreToolUse hook — decision gate v1 (warn-only).
# Fires BEFORE Edit/Write/Bash on protected paths.
# Reminds CTO to complete Step 5.5 (Agent Routing Check) before modifying critical files.
# v1.0 — 2026-03-26 — team-recommended (both review agents, Session 33)
# exit 0 = allow (always — this is warn-only v1)
# exit 2 = block (reserved for future v2 with session state tracking)

INPUT=$(cat)

# Extract tool name and file path from hook input JSON
TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); p=d.get('tool_input',{}); print(p.get('file_path', p.get('command', '')))" 2>/dev/null)

# Protected path patterns — changes here affect production or enforcement
PROTECTED_PATTERNS=(
  "apps/api/"
  "apps/web/"
  "supabase/migrations/"
  ".claude/hooks/"
  ".github/workflows/"
)

IS_PROTECTED=0
MATCHED_PATTERN=""

for PATTERN in "${PROTECTED_PATTERNS[@]}"; do
  if echo "$FILE_PATH" | grep -q "$PATTERN"; then
    IS_PROTECTED=1
    MATCHED_PATTERN="$PATTERN"
    break
  fi
done

if [ "$IS_PROTECTED" -eq 1 ]; then
  echo "──────────────────────────────────────────────────────────────"
  echo "⚠️  PRE-DECISION GATE: Protected path detected"
  echo "   Tool: $TOOL_NAME"
  echo "   Path matches: $MATCHED_PATTERN"
  echo ""
  echo "   Before proceeding — confirm Step 5.5 complete:"
  echo "   □ Agent Routing Check done (memory/swarm/agent-roster.md)"
  echo "   □ If match found → agents consulted BEFORE this edit"
  echo "   □ If no match → reason documented (1 line)"
  echo ""
  echo "   Skipping this = Mistake #14/#22/#31/#41 class (solo execution)"
  echo "──────────────────────────────────────────────────────────────"
fi

# Always allow — v1 is warn-only
exit 0
