#!/bin/bash
# POST-COMPACT HOOK: Re-injects critical context AFTER compaction
# stdout from this script is added directly to Claude's context
# This is how we survive context loss

MEMORY_DIR="$HOME/.claude/projects/C--Projects-VOLAURA/memory"
CHECKPOINT="$MEMORY_DIR/context_checkpoint.md"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "========================================"
echo "CONTEXT RESTORED AFTER COMPACTION"
echo "========================================"
echo ""

# Re-inject checkpoint if it exists
if [ -f "$CHECKPOINT" ]; then
  cat "$CHECKPOINT"
  echo ""
fi

# Re-inject current sprint position from roadmap
if [ -f "$PROJECT_DIR/docs/ROADMAP.md" ]; then
  echo "## Current Roadmap (NOW section):"
  # Extract NOW section only
  sed -n '/^## NOW/,/^## NEXT/p' "$PROJECT_DIR/docs/ROADMAP.md" | head -30
  echo ""
fi

# Re-inject mandatory rules summary
echo "## Mandatory Rules (7 — read full file if needed):"
echo "1. No solo decisions — agents review FIRST"
echo "2. Memory recovery must produce visible output"
echo "3. Test on PRODUCTION URL (modest-happiness, not volauraapi)"
echo "4. Schema verification before deployment"
echo "5. Delegate first, do last"
echo "6. Sprint retrospective mandatory and structured"
echo "7. State persisted during work, not after"
echo ""

# Re-inject key behavioral rules
echo "## CEO Communication Rules:"
echo "- Report OUTCOMES only, no technical details"
echo "- Match Yusif's language (Russian -> Russian, English -> English)"
echo "- Never ask operational questions — use ROADMAP.md for priorities"
echo "- Never show: curl output, schemas, deployment logs, git diffs"
echo ""

echo "## Production URLs:"
echo "- API: https://modest-happiness-production.up.railway.app"
echo "- Frontend: https://volaura.app"
echo "- WRONG (never use): volauraapi-production.up.railway.app"
echo ""

echo "========================================"
echo "END OF RESTORED CONTEXT"
echo "========================================"

exit 0
