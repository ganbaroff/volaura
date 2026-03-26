#!/bin/bash
# Stop hook — BLOCKING memory enforcement.
# exit 2 = block session end | exit 0 = allow
# v2.0 — 2026-03-26 — team-approved changes applied
# Changes: named constants, mistakes.md→WARN, patterns.md→WARN, cleaner output

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
STATE_FILE="$PROJECT_DIR/memory/context/sprint-state.md"
MISTAKES_FILE="$PROJECT_DIR/memory/context/mistakes.md"
PATTERNS_FILE="$PROJECT_DIR/memory/context/patterns.md"

SPRINT_STATE_GATE=14400   # 4 hours — BLOCKING (sprint-state.md must be updated)
MISTAKES_WARN=14400       # 4 hours — WARNING only (not blocking)
PATTERNS_WARN=86400       # 24 hours — WARNING only (not blocking)

get_mtime() {
  stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0
}

NOW=$(date +%s)
BLOCKED=0

# ── Gate 1: sprint-state.md — BLOCKING ──────────────────────────────────────
if [ ! -f "$STATE_FILE" ]; then
  echo "══════════════════════════════════════════════════════════════"
  echo "🚫 BLOCKED: sprint-state.md NOT FOUND"
  echo "══════════════════════════════════════════════════════════════"
  echo "Create memory/context/sprint-state.md before ending session."
  BLOCKED=1
else
  DIFF=$((NOW - $(get_mtime "$STATE_FILE")))
  if [ "$DIFF" -gt "$SPRINT_STATE_GATE" ]; then
    echo "══════════════════════════════════════════════════════════════"
    echo "🚫 BLOCKED: sprint-state.md not updated this session"
    echo "══════════════════════════════════════════════════════════════"
    echo "Last updated: ${DIFF}s ago (gate: ${SPRINT_STATE_GATE}s)"
    echo "Update sprint-state.md first, then end the session."
    echo "Mistakes #7, #23, #32, #42 = same pattern. Advisory failed. This blocks."
    BLOCKED=1
  fi
fi

# ── Gate 2: mistakes.md — WARNING only ──────────────────────────────────────
if [ -f "$MISTAKES_FILE" ]; then
  DIFF=$((NOW - $(get_mtime "$MISTAKES_FILE")))
  if [ "$DIFF" -gt "$MISTAKES_WARN" ]; then
    echo "⚠️  WARNING: mistakes.md not updated this session."
    echo "   Did any mistakes occur? If yes, document before closing."
  fi
fi

# ── Gate 3: patterns.md — WARNING only ──────────────────────────────────────
if [ -f "$PATTERNS_FILE" ]; then
  DIFF=$((NOW - $(get_mtime "$PATTERNS_FILE")))
  if [ "$DIFF" -gt "$PATTERNS_WARN" ]; then
    echo "⚠️  WARNING: patterns.md not updated in 24h."
    echo "   Any new patterns discovered this session?"
  fi
fi

[ "$BLOCKED" -eq 1 ] && exit 2
exit 0
