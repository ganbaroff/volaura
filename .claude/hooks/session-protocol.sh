#!/bin/bash
# UserPromptSubmit hook — injects protocol checklist + swarm inbox on first message.
# Fires BEFORE Claude reads the user's prompt.
# stdout → Claude sees this as injected context.

INPUT=$(cat)

# Extract session tracking from temp file
SESSION_MARKER="/tmp/volaura_session_active"

if [ ! -f "$SESSION_MARKER" ]; then
  # First prompt of this session — inject mandatory protocol + auto-read context files

  PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
  SPRINT_STATE="$PROJECT_DIR/memory/context/sprint-state.md"
  MISTAKES="$PROJECT_DIR/memory/context/mistakes.md"

  # HARD GATE: Reset protocol state so enforce hook blocks until new protocol cycle
  PROTOCOL_STATE="$PROJECT_DIR/.claude/protocol-state.json"
  if [ -f "$PROTOCOL_STATE" ]; then
    rm -f "$PROTOCOL_STATE"
  fi

  echo "══════════════════════════════════════════════════════════════"
  echo "PHASE A GATE — SESSION START — PROTOCOL v4.0"
  echo "══════════════════════════════════════════════════════════════"
  echo ""
  echo "YOU MUST PRODUCE THESE 3 LINES BEFORE ANY WORK:"
  echo "▶ Sprint [N], Step [X]. Date: $(date '+%Y-%m-%d'). Protocol v4.0 loaded."
  echo "▶ Last session ended with: [summary from sprint-state below]"
  echo "▶ This session I will NOT: [top 3 from mistakes below]"
  echo "WITHOUT THESE 3 LINES — NO WORK STARTS."
  echo ""

  # Auto-inject sprint-state.md (no need to remember to read it)
  if [ -f "$SPRINT_STATE" ]; then
    echo "── SPRINT STATE (auto-injected) ──────────────────────────────"
    head -40 "$SPRINT_STATE"
    echo ""
  else
    echo "⚠️  memory/context/sprint-state.md NOT FOUND — create it before proceeding."
    echo ""
  fi

  # Auto-inject mistakes.md
  if [ -f "$MISTAKES" ]; then
    echo "── MISTAKES / DO NOT REPEAT (auto-injected) ──────────────────"
    head -30 "$MISTAKES"
    echo ""
  else
    echo "⚠️  memory/context/mistakes.md NOT FOUND — create it before proceeding."
    echo ""
  fi

  # ── SHIPPED CODE (what exists in production — THE CRITICAL GAP FIX) ──
  # Root cause: CTO started Session 55 not knowing Session 51 built:
  # memory_consolidation.py, skill_evolution.py, skills.py router, Telegram bidirectional.
  # Fix: inject SHIPPED.md at every session start. If it's not here → CTO doesn't know.
  SHIPPED="$PROJECT_DIR/memory/swarm/SHIPPED.md"
  if [ -f "$SHIPPED" ]; then
    echo "── SHIPPED CODE LOG (auto-injected) ──────────────────────────"
    echo "⚠️  READ THIS: These are the Python files, routers, and features that EXIST."
    echo "    Do NOT recreate what is already here. Do NOT skip reading this."
    echo ""
    # Show last 2 sessions worth of entries (tail to get recent entries)
    tail -80 "$SHIPPED"
    echo ""
  else
    echo "⚠️  memory/swarm/SHIPPED.md NOT FOUND."
    echo "    Create it now: list all Python files in packages/swarm/ + API routers added since Session 1."
    echo ""
  fi

  echo "RULES (non-negotiable):"
  echo "- Plans >10 lines → agent review BEFORE presenting to Yusif"
  echo "- NO solo decisions — everything through agent review"
  echo "- Swarm = PRODUCT, not tooling"
  echo "- CEO sees outcomes only — no curl, no schemas, no logs"
  echo ""
  echo "CTO HEALTH CHECK (do BEFORE sprint work):"
  echo "- Update daily-log.md with today's standup"
  echo "- Check agent-roster.md scores (last updated?)"
  echo "- Check EXECUTION-PLAN.md is current"
  echo "- If sprint ended since last session → fill SPRINT-REVIEW-TEMPLATE.md"
  echo "══════════════════════════════════════════════════════════════"

  # ── STALENESS DETECTOR (added 2026-03-26, Lesson from Session 42) ──
  # If any memory/swarm file is older than 3 days → warn CTO
  echo ""
  STALE_FOUND=0
  NOW=$(date +%s)
  for dir in "$PROJECT_DIR/memory/context" "$PROJECT_DIR/memory/swarm" "$PROJECT_DIR/memory/projects"; do
    if [ -d "$dir" ]; then
      for f in "$dir"/*.md; do
        if [ -f "$f" ]; then
          FILE_MOD=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null)
          if [ -n "$FILE_MOD" ]; then
            DAYS_OLD=$(( (NOW - FILE_MOD) / 86400 ))
            if [ "$DAYS_OLD" -gt 3 ]; then
              if [ "$STALE_FOUND" -eq 0 ]; then
                echo "⚠️  STALE FILES DETECTED (>3 days old):"
                STALE_FOUND=1
              fi
              BASENAME=$(basename "$f")
              DIRNAME=$(basename "$(dirname "$f")")
              echo "  ⚠️  $DIRNAME/$BASENAME — ${DAYS_OLD} days old"
            fi
          fi
        fi
      done
    fi
  done
  if [ "$STALE_FOUND" -eq 1 ]; then
    echo "  → Review and update stale files BEFORE starting work."
    echo ""
  fi

  # Surface swarm inbox if proposals exist
  PROPOSALS_FILE="memory/swarm/proposals.json"
  if [ -f "$PROPOSALS_FILE" ]; then
    PENDING_COUNT=$(python3 -c "
import json, sys
try:
    with open('$PROPOSALS_FILE', 'r') as f:
        data = json.load(f)
    pending = [p for p in data.get('proposals', []) if p.get('status') == 'pending']
    escalations = [p for p in pending if p.get('escalate_to_ceo')]
    if pending:
        print('══════════════════════════════════════════════════════════════')
        print(f'SWARM INBOX: {len(pending)} pending proposal(s), {len(escalations)} escalation(s)')
        print('══════════════════════════════════════════════════════════════')
        for e in escalations[:3]:
            print(f'  🔴 [ESCALATE] {e[\"title\"]} (by {e[\"agent\"]})')
        non_esc = [p for p in pending if not p.get('escalate_to_ceo')]
        for p in non_esc[:5]:
            sev = p.get('severity', 'medium').upper()
            print(f'  [{sev}] {p[\"title\"]} (by {p[\"agent\"]})')
        print('══════════════════════════════════════════════════════════════')
        print('Read memory/swarm/proposals.json for full details.')
        print('Update status: act/dismiss/defer via InboxProtocol.')
except Exception as e:
    pass
" 2>/dev/null)
    if [ -n "$PENDING_COUNT" ]; then
      echo "$PENDING_COUNT"
    fi
  fi

  touch "$SESSION_MARKER"
fi

exit 0
