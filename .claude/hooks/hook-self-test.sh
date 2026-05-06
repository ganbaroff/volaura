#!/bin/bash
# hook-self-test.sh — sprint-startable self-test for Atlas hooks.
#
# Synthetic-input runs each hook with crafted JSON, checks expected
# behavior:
#   - verification-evidence-check.sh: claim-without-tool input → flag written
#   - pre-mutation-context-gate.sh: critical mutation without prior Read →
#       stderr context emitted
#   - external-verdict-dispatcher.sh: critical mutation → inbox file created
#
# Run manually: bash .claude/hooks/hook-self-test.sh
# Exit 0 = all hooks fired correctly. Exit 1 = at least one regression.

set -u
PROJECT_DIR_BASH="$(cd "$(dirname "$0")/../.." && pwd)"
# pwd -W on Git Bash returns Windows path (C:/...), needed for Windows-native python
PROJECT_DIR_WIN="$(cd "$(dirname "$0")/../.." && pwd -W 2>/dev/null || pwd)"
PROJECT_DIR="$PROJECT_DIR_BASH"
HOOKS="$PROJECT_DIR/.claude/hooks"
TMP_DIR="$PROJECT_DIR/.claude/.hook-test-tmp.$$"
TMP_DIR_WIN="$PROJECT_DIR_WIN/.claude/.hook-test-tmp.$$"
mkdir -p "$TMP_DIR"
FAIL=0

cleanup() { rm -rf "$TMP_DIR" 2>/dev/null || true; }
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Test 1 — verification-evidence-check.sh: synth a transcript with claim
# words but no tool_use blocks, expect flag file written.
# ---------------------------------------------------------------------------
TR1_W="$TMP_DIR_WIN/transcript1.jsonl"
TR1="$TMP_DIR/transcript1.jsonl"
cat > "$TR1" <<'JSONL'
{"type":"user","message":{"content":"проверь rotation"}}
{"type":"assistant","message":{"content":[{"type":"text","text":"Rotation готов. Старый ключ deployed правильно. Все verified, инцидент closed."}]}}
JSONL

FLAG="$PROJECT_DIR/.claude/last-verification-gap.flag"
rm -f "$FLAG" 2>/dev/null

echo "{\"transcript_path\":\"$TR1_W\"}" | bash "$HOOKS/verification-evidence-check.sh" >/dev/null 2>&1

if [ -f "$FLAG" ]; then
    echo "[PASS] T1 verification-evidence-check: flag written for claim-without-tool"
    rm -f "$FLAG"
else
    echo "[FAIL] T1 verification-evidence-check: NO flag for claim-without-tool input"
    FAIL=1
fi

# Negative test — claims plus tool_use → no flag
TR1B_W="$TMP_DIR_WIN/transcript1b.jsonl"
TR1B="$TMP_DIR/transcript1b.jsonl"
cat > "$TR1B" <<'JSONL'
{"type":"user","message":{"content":"проверь rotation"}}
{"type":"assistant","message":{"content":[{"type":"text","text":"Rotation проверил."},{"type":"tool_use","id":"tu_1","name":"Bash","input":{"command":"curl"}}]}}
JSONL
echo "{\"transcript_path\":\"$TR1B_W\"}" | bash "$HOOKS/verification-evidence-check.sh" >/dev/null 2>&1
if [ ! -f "$FLAG" ]; then
    echo "[PASS] T1b verification-evidence-check: NO flag when tool_use present"
else
    echo "[FAIL] T1b verification-evidence-check: false-positive flag when tool_use present"
    rm -f "$FLAG"
    FAIL=1
fi

# ---------------------------------------------------------------------------
# Test 2 — pre-mutation-context-gate.sh: critical mutation without prior
# Read of lessons.md → stderr should contain "[PRE-MUTATION GATE]"
# ---------------------------------------------------------------------------
TR2_W="$TMP_DIR_WIN/transcript2.jsonl"
TR2="$TMP_DIR/transcript2.jsonl"
cat > "$TR2" <<'JSONL'
{"type":"user","message":{"content":"deploy now"}}
JSONL

INPUT2=$(printf '{"tool_name":"Bash","tool_input":{"command":"railway redeploy --service @volaura/api"},"transcript_path":"%s"}' "$TR2_W")
ERR2=$(echo "$INPUT2" | bash "$HOOKS/pre-mutation-context-gate.sh" 2>&1 >/dev/null)
if echo "$ERR2" | grep -q "PRE-MUTATION GATE"; then
    echo "[PASS] T2 pre-mutation-context-gate: gate fired without prior Read"
else
    echo "[FAIL] T2 pre-mutation-context-gate: gate did NOT fire (got: ${ERR2:0:100})"
    FAIL=1
fi

# Positive control — same mutation but transcript HAS Read of lessons.md → no gate
TR2B_W="$TMP_DIR_WIN/transcript2b.jsonl"
TR2B="$TMP_DIR/transcript2b.jsonl"
cat > "$TR2B" <<'JSONL'
{"type":"user","message":{"content":"deploy now"}}
{"type":"assistant","message":{"content":[{"type":"tool_use","id":"tu_a","name":"Read","input":{"file_path":"memory/atlas/lessons.md"}}]}}
JSONL
INPUT2B=$(printf '{"tool_name":"Bash","tool_input":{"command":"railway redeploy --service @volaura/api"},"transcript_path":"%s"}' "$TR2B_W")
ERR2B=$(echo "$INPUT2B" | bash "$HOOKS/pre-mutation-context-gate.sh" 2>&1 >/dev/null)
if ! echo "$ERR2B" | grep -q "PRE-MUTATION GATE"; then
    echo "[PASS] T2b pre-mutation-context-gate: gate silent when lessons.md read"
else
    echo "[FAIL] T2b pre-mutation-context-gate: false-positive when lessons.md was read"
    FAIL=1
fi

# Negative test — non-critical Bash command should not trigger gate
INPUT2C='{"tool_name":"Bash","tool_input":{"command":"ls -la"},"transcript_path":""}'
ERR2C=$(echo "$INPUT2C" | bash "$HOOKS/pre-mutation-context-gate.sh" 2>&1 >/dev/null)
if ! echo "$ERR2C" | grep -q "PRE-MUTATION GATE"; then
    echo "[PASS] T2c pre-mutation-context-gate: no gate on non-critical Bash"
else
    echo "[FAIL] T2c pre-mutation-context-gate: gate fired on non-critical ls"
    FAIL=1
fi

# ---------------------------------------------------------------------------
# Test 3 — external-verdict-dispatcher.sh: critical mutation should write
# inbox file (or skip silently if no NVIDIA key). Smoke check: hook exits 0
# with no stderr panic.
# ---------------------------------------------------------------------------
INPUT3='{"tool_name":"Bash","tool_input":{"command":"railway up --service @volaura/api --detach"},"tool_response":{"output":"Indexing... Uploading...","error":""}}'
ERR3=$(echo "$INPUT3" | bash "$HOOKS/external-verdict-dispatcher.sh" 2>&1)
RC3=$?
if [ "$RC3" = "0" ]; then
    echo "[PASS] T3 external-verdict-dispatcher: exit 0 on critical mutation"
else
    echo "[FAIL] T3 external-verdict-dispatcher: exit $RC3 (stderr: ${ERR3:0:100})"
    FAIL=1
fi

# ---------------------------------------------------------------------------
# Sentinel: existing hooks still parse without syntax errors
# ---------------------------------------------------------------------------
for h in voice-breach-check.sh trailing-question-check.sh style-brake.sh \
         session-protocol.sh; do
    if bash -n "$HOOKS/$h" 2>/dev/null; then
        echo "[PASS] syntax-check $h"
    else
        echo "[FAIL] syntax-check $h"
        FAIL=1
    fi
done

# ---------------------------------------------------------------------------
echo
if [ "$FAIL" = "0" ]; then
    echo "✅ hook-self-test: all hooks fired correctly"
    exit 0
else
    echo "❌ hook-self-test: at least one regression detected — read [FAIL] lines above"
    exit 1
fi
