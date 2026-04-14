#!/usr/bin/env bash
# Install the repo-maintained pre-commit secret scanner into .git/hooks/.
# Re-run on fresh clone or after any upstream edit to the scanner.
#
# Rationale: .git/hooks/ is per-checkout, so the hook itself can't be tracked.
# We keep the canonical version here in scripts/ and copy on install.

set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$ROOT/scripts/pre-commit-secret-scan.sh"
DST="$ROOT/.git/hooks/pre-commit"

if [ ! -f "$SRC" ]; then
    echo "ERROR: $SRC missing. Commit the scanner to scripts/ first."
    exit 1
fi

cp "$SRC" "$DST"
chmod +x "$DST"
echo "✓ Pre-commit hook installed at .git/hooks/pre-commit"
echo "  Canonical source: scripts/pre-commit-secret-scan.sh"
echo "  Test with:  git diff --cached | head  (then try a commit)"
