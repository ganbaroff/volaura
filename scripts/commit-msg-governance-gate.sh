#!/usr/bin/env bash
# Atlas memory governance gate — commit-msg hook.
# Source-of-truth: scripts/commit-msg-governance-gate.sh
# Active hook path: .githooks/commit-msg (repo uses core.hooksPath = .githooks).
# .githooks/commit-msg is a thin wrapper that delegates to this script.
# Manual reinstall (only if .githooks/commit-msg is lost):
#   cp scripts/commit-msg-governance-gate.sh .githooks/commit-msg
#   chmod +x .githooks/commit-msg
#
# Blocks three failure modes documented in
# memory/atlas/lessons.md (Class 18 grenade-launcher, Class 19 lesson-without-write,
# Class 21 closure-without-ledger):
#   1. New root-level memory/atlas/*.md files without [canonical-new] tag.
#   2. Edits to identity.md / atlas-debts-to-ceo.md without Ratified-by: line.
#   3. Closure words (done/recorded/verified/fixed) in messages with zero staged files.
#
# Override (use sparingly, only when the gate is genuinely wrong):
#   git commit --no-verify

set -e

MSG_FILE="$1"
if [ -z "$MSG_FILE" ] || [ ! -f "$MSG_FILE" ]; then
    # No message file argument — git itself or another hook will surface this.
    exit 0
fi

MSG=$(cat "$MSG_FILE")

# Strip comment lines (# ...) and trailing whitespace for the analysis.
MSG_BODY=$(echo "$MSG" | grep -v '^#' || true)

# Discover what the commit would touch. During commit-msg phase, the index
# reflects what is staged for this commit.
NEW_ROOT_MD=$(git diff --cached --name-only --diff-filter=A 2>/dev/null \
    | grep -E '^memory/atlas/[^/]+\.md$' || true)

MOD_PROTECTED=$(git diff --cached --name-only --diff-filter=M 2>/dev/null \
    | grep -E '^memory/atlas/(identity\.md|atlas-debts-to-ceo\.md)$' || true)

ALL_STAGED_COUNT=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')

VIOLATIONS=""

# Check 1: new root-level memory/atlas/*.md must carry [canonical-new] tag.
if [ -n "$NEW_ROOT_MD" ]; then
    if ! echo "$MSG_BODY" | grep -qE '\[canonical-new'; then
        VIOLATIONS="${VIOLATIONS}
  - new MD at memory/atlas/ root without [canonical-new] tag in commit message:
$(echo "$NEW_ROOT_MD" | sed 's/^/      /')"
    fi
fi

# Check 2: edits to identity.md / atlas-debts-to-ceo.md require Ratified-by: line.
if [ -n "$MOD_PROTECTED" ]; then
    if ! echo "$MSG_BODY" | grep -qE '^Ratified-by:'; then
        VIOLATIONS="${VIOLATIONS}
  - edit to canonical file(s) without 'Ratified-by:' in commit body:
$(echo "$MOD_PROTECTED" | sed 's/^/      /')"
    fi
fi

# Check 3: closure word in message but zero staged files.
if [ "$ALL_STAGED_COUNT" -eq 0 ]; then
    if echo "$MSG_BODY" | grep -qiE '\b(done|recorded|verified|fixed)\b'; then
        VIOLATIONS="${VIOLATIONS}
  - commit message contains closure word (done/recorded/verified/fixed) but zero files staged"
    fi
fi

if [ -n "$VIOLATIONS" ]; then
    echo "🛑 commit-msg governance gate REJECTED:${VIOLATIONS}"
    echo ""
    echo "  Override (last resort, must be intentional): git commit --no-verify"
    echo "  Source: scripts/commit-msg-governance-gate.sh"
    exit 1
fi

# Quiet success — only print on rejection. Match the secret-scanner's silent-pass style.
exit 0
