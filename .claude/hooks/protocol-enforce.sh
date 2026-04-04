#!/bin/bash
# protocol-enforce.sh — BLOCKING PreToolUse hook v1.0
# Blocks Edit/Write/Bash on production code until protocol Step 6 complete.
#
# MECHANISM:
#   Claude writes .claude/protocol-state.json via Write tool after each step.
#   This hook reads that file before allowing production code changes.
#   current_step >= 6 = Final Plan done = production edits allowed.
#
# STATE FILE: .claude/protocol-state.json
#   {"current_step": 6, "task": "...", "session_start": "...", "exception": null}
#   exception: null | "hotfix" | "typo"
#
# PROTECTED PATHS: apps/api/ apps/web/ supabase/migrations/ .github/workflows/
# NOT protected: docs/ memory/ .claude/protocol-state.json (state writes always allowed)
#
# exit 0 = allow
# exit 2 = BLOCK

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); p=d.get('tool_input',{}); print(p.get('file_path',''))" 2>/dev/null)

# Use Python os.getcwd() to get Windows-compatible path (Git Bash paths like /c/... fail in Python on Windows)
STATE_FILE=$(python3 -c "import os; print(os.path.join(os.getcwd(), '.claude', 'protocol-state.json'))" 2>/dev/null)

# Only enforce on Edit and Write — not Bash (command strings are unreliable to pattern-match)
if [ "$TOOL_NAME" != "Edit" ] && [ "$TOOL_NAME" != "Write" ]; then
  exit 0
fi

# Protected production paths
PROTECTED_PATTERNS=(
  "apps/api/"
  "apps/web/"
  "supabase/migrations/"
  ".github/workflows/"
)

IS_PROTECTED=0
for PATTERN in "${PROTECTED_PATTERNS[@]}"; do
  if echo "$FILE_PATH" | grep -q "$PATTERN"; then
    IS_PROTECTED=1
    break
  fi
done

# Only enforce on protected paths
if [ "$IS_PROTECTED" -eq 0 ]; then
  exit 0
fi

# ── State file missing ──────────────────────────────────────────
if [ ! -f "$STATE_FILE" ]; then
  cat <<'EOF'
════════════════════════════════════════════════════════
🚫 PROTOCOL ENFORCER: Task not initialized
════════════════════════════════════════════════════════

No .claude/protocol-state.json found.
Production code is locked until protocol is started.

REQUIRED STEPS:
  1. Open: docs/TASK-PROTOCOL-CHECKLIST.md
  2. Copy the template
  3. Fill in Step 0 (Skills) → write state.json {"current_step": 0}
  4. Fill in Step 0.5 (Context) → write state.json {"current_step": 1}
  5. Fill in Step 1 (Scope Lock) → write state.json {"current_step": 2}
  6. Continue to Step 6 (Final Plan) → production edits unlocked

════════════════════════════════════════════════════════
EOF
  exit 2
fi

# ── Staleness check: state older than 4 hours = expired ────────
STATE_AGE_SECONDS=$(python3 -c "
import json, os, time
f = os.path.join(os.getcwd(), '.claude', 'protocol-state.json')
try:
    with open(f) as fh:
        s = json.load(fh)
    e = s.get('started_at_epoch', 0)
    print(int(time.time() - e) if e else 999999)
except:
    print(999999)
" 2>/dev/null)

IS_EXPIRED=$(python3 -c "print('yes' if int('${STATE_AGE_SECONDS}') > 14400 else 'no')" 2>/dev/null)
if [ "$IS_EXPIRED" = "yes" ]; then
  cat <<'EOF'
════════════════════════════════════════════════════════
⚠️ PROTOCOL STATE EXPIRED (>4 hours old)
════════════════════════════════════════════════════════

State file is stale. Deleting and blocking.
Follow TASK-PROTOCOL.md from Step 0 (Flow Detection).

════════════════════════════════════════════════════════
EOF
  rm -f "$STATE_FILE"
  exit 2
fi

# ── Read state ──────────────────────────────────────────────────
CURRENT_STEP=$(python3 -c "
import json, os
f = os.path.join(os.getcwd(), '.claude', 'protocol-state.json')
try:
    with open(f) as fh:
        s = json.load(fh)
    print(s.get('current_step', 0))
except:
    print(0)
" 2>/dev/null)

EXCEPTION=$(python3 -c "
import json, os
f = os.path.join(os.getcwd(), '.claude', 'protocol-state.json')
try:
    with open(f) as fh:
        s = json.load(fh)
    print(s.get('exception') or '')
except:
    print('')
" 2>/dev/null)

TASK=$(python3 -c "
import json, os
f = os.path.join(os.getcwd(), '.claude', 'protocol-state.json')
try:
    with open(f) as fh:
        s = json.load(fh)
    print(s.get('task', 'Unknown'))
except:
    print('Unknown')
" 2>/dev/null)

# ── Exception: hotfix or typo bypass ────────────────────────────
if [ "$EXCEPTION" = "hotfix" ] || [ "$EXCEPTION" = "typo" ]; then
  echo "✅ PROTOCOL: Exception active ($EXCEPTION) — production edits allowed"
  exit 0
fi

# ── Step gate: require Step 6 before production edits ───────────
if [ "$CURRENT_STEP" -lt 6 ]; then
  STEP_NAMES=("Step 0: Skills" "Step 0.5: Context" "Step 1: Scope Lock" "Step 2: Plan" "Step 3: Swarm Critique" "Step 4: Response Table" "Step 5: Counter-Critique" "Step 6: Final Plan")
  CURRENT_NAME="${STEP_NAMES[$CURRENT_STEP]:-Step $CURRENT_STEP}"
  REMAINING=$((6 - CURRENT_STEP))

  cat <<EOF
════════════════════════════════════════════════════════
🚫 PROTOCOL ENFORCER: Sequence violation
════════════════════════════════════════════════════════

Task:     $TASK
Current:  $CURRENT_NAME
Required: Step 6 (Final Plan) to edit production code
Gap:      $REMAINING step(s) remaining

Blocked:  $FILE_PATH

Complete the checklist first: docs/TASK-PROTOCOL-CHECKLIST.md
Each step writes to: .claude/protocol-state.json

════════════════════════════════════════════════════════
EOF
  exit 2
fi

# Step 6+ → allow
exit 0
