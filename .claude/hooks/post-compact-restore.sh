#!/bin/bash
# POST-COMPACT HOOK: re-injects only live canonical pointers plus session delta.
# Avoids stale restore text, dead file references, and hardcoded runtime drift.

MEMORY_DIR="$HOME/.claude/projects/C--Projects-VOLAURA/memory"
CHECKPOINT="$MEMORY_DIR/context_checkpoint.md"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
COMPACT_FLAG="$PROJECT_DIR/.claude/just-compacted.flag"

echo "========================================"
echo "ATLAS CONTEXT RESTORED AFTER COMPACTION"
echo "========================================"
echo ""

if [ -f "$CHECKPOINT" ]; then
  cat "$CHECKPOINT"
  echo ""
else
  echo "Session delta: checkpoint missing."
  echo ""
fi

echo "Canonical recovery spine (live authority order for this re-entry):"
echo "- memory/atlas/wake.md — wake protocol and continuity spine"
echo "- AGENTS.md — runtime/backend truth wins over older docs when they conflict"
echo "- .claude/breadcrumb.md — last declared action and next step"
echo "- docs/CURRENT-VS-TARGET-ARCHITECTURE-2026-04-21.md — current runtime truth vs historical target language"
echo ""
echo "Re-entry rule:"
echo "- Continue from breadcrumb."
echo "- Verify before claim."
echo "- Do not reset into audit/report mode just because compaction happened."
echo ""

printf 'compacted_at=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" > "$COMPACT_FLAG"

echo "One-shot compact re-entry marker armed: .claude/just-compacted.flag"
echo ""
echo "========================================"
echo "END OF RESTORED CONTEXT"
echo "========================================"

exit 0
