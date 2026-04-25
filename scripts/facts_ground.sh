#!/usr/bin/env bash
# facts_ground.sh — Atlas wake-time facts manifest.
#
# Order matters. pwd && hostname FIRST — catches sandbox-bleed at the
# moment of any "repo path" claim. If pwd returns /home/claude/* or a
# container-y root, you are in a Codex/claude.ai sandbox, NOT on Yusif's
# Windows machine. Refuse to make repo-state claims sourced from this
# environment.
#
# Add new live facts here as a single canonical block, never as scattered
# tool-calls in wake.md. Atlas reads the OUTPUT of this script before any
# first-turn assertion about repo state.
#
# Run on every wake BEFORE stance_primer.py.
# Windows host: see facts_ground.ps1 for PowerShell equivalent.

set -u

echo "=== ATLAS FACTS GROUND ==="
echo "ts: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "--- environment ---"
echo "pwd:      $(pwd)"
echo "hostname: $(hostname)"
echo "kernel:   $(uname -sr 2>/dev/null || echo unknown)"
echo "user:     $(whoami)"
echo

# Sandbox detection — refuse repo claims if true.
case "$(pwd)" in
  /home/claude/*|/runsc/*|/mnt/data/*)
    echo "!!! SANDBOX DETECTED — repo facts below describe sandbox clone, NOT live Atlas state. !!!"
    echo
    ;;
esac

echo "--- repo ---"
if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then
  echo "head:        $(git rev-parse --short HEAD 2>/dev/null)"
  echo "branch:      $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  echo "commits:     $(git rev-list --count HEAD 2>/dev/null)"
  echo "last_commit: $(git log -1 --format='%ci %s' 2>/dev/null)"
  echo "uncommitted: $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ') files"
else
  echo "(not a git repo at $(pwd))"
fi
echo

echo "--- markdown corpus ---"
md_total=$(find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/.next/*" 2>/dev/null | wc -l | tr -d ' ')
md_atlas=$(find ./memory/atlas -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
md_docs=$(find ./docs -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "total:       ${md_total}"
echo "memory/atlas:${md_atlas}"
echo "docs:        ${md_docs}"
echo

echo "--- breadcrumb (if present) ---"
if [ -f .claude/breadcrumb.md ]; then
  head -20 .claude/breadcrumb.md
else
  echo "(no .claude/breadcrumb.md)"
fi
echo

echo "--- runtime/ residue (should be empty/single file) ---"
if [ -d memory/atlas/runtime ]; then
  ls -la memory/atlas/runtime/ 2>/dev/null
else
  echo "(memory/atlas/runtime/ does not exist yet)"
fi
echo

echo "=== END FACTS GROUND ==="
