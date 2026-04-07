#!/bin/bash
# Stop hook — BLOCKS unverified claims.
# v3.0: Scans ENTIRE TURN (not just last msg). Debug log: /tmp/volaura-nuc.log
#
# Fix for v2 bug: last assistant-msg was often a tool_use with no text.
# Real claim words live in earlier msgs of the same turn.
#
# exit 2 = BLOCK | exit 0 = allow

# ── 1. Capture STDIN ─────────────────────────────────────────────
STDIN=$(cat)
DEBUG_LOG="/tmp/volaura-nuc.log"

{
  echo ""
  echo "══════════ $(date '+%H:%M:%S') HOOK FIRED ══════════"
  echo "STDIN_PREVIEW=${STDIN:0:200}"
} >> "$DEBUG_LOG"

echo "$STDIN" > /tmp/nuc-last-stdin.json 2>/dev/null

# ── 2. Extract transcript path ───────────────────────────────────
TRANSCRIPT=$(echo "$STDIN" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('transcript_path') or d.get('transcriptPath') or '')
except:
    print('')
" 2>>"$DEBUG_LOG")

echo "TRANSCRIPT=[$TRANSCRIPT]" >> "$DEBUG_LOG"

if [ -z "$TRANSCRIPT" ]; then
  echo "NO_TRANSCRIPT → allow" >> "$DEBUG_LOG"
  exit 0
fi

# ── 3. Verify file exists ────────────────────────────────────────
# Use bash -f (works for both POSIX and Windows paths via Git Bash)
if [ ! -f "$TRANSCRIPT" ]; then
  # Fallback: try Python (handles Windows paths that bash -f might miss)
  FILE_OK=$(python3 -c "import os; print('yes' if os.path.isfile(r'$TRANSCRIPT') else 'no')" 2>/dev/null)
  if [ "$FILE_OK" != "yes" ]; then
    echo "FILE_NOT_FOUND → allow" >> "$DEBUG_LOG"
    exit 0
  fi
fi

# ── 4. Analysis script ───────────────────────────────────────────
PYFILE=$(python3 -c "import tempfile; print(tempfile.mktemp(suffix='.py'))" 2>/dev/null)
[ -z "$PYFILE" ] && PYFILE="/tmp/nuc_analysis_$$.py"

cat > "$PYFILE" << 'PYEOF'
import json, sys, re

transcript_path = sys.argv[1]
debug_log = sys.argv[2] if len(sys.argv) > 2 else '/dev/null'

def dbg(msg):
    with open(debug_log, 'a', encoding='utf-8') as f:
        f.write(str(msg) + '\n')

# Read transcript
try:
    with open(transcript_path, 'r', encoding='utf-8', errors='replace') as f:
        raw_lines = [l.strip() for l in f if l.strip()]
    dbg(f"LINES={len(raw_lines)}")
except Exception as e:
    dbg(f"READ_ERROR={e}")
    print("has_claims=False"); print("has_verify=False")
    sys.exit(0)

# Parse JSONL
messages = []
for line in raw_lines:
    try:
        messages.append(json.loads(line))
    except:
        pass
dbg(f"PARSED={len(messages)}")

def get_role(msg):
    inner = msg.get("message") if isinstance(msg.get("message"), dict) else msg
    return inner.get("role", "")

def get_content(msg):
    inner = msg.get("message") if isinstance(msg.get("message"), dict) else msg
    return inner.get("content", [])

def is_tool_result_msg(msg):
    """True if this user message is a tool result (not a real human prompt)"""
    if msg.get("toolUseResult") is not None:
        return True
    content = get_content(msg)
    if isinstance(content, list):
        return any(
            isinstance(b, dict) and b.get("type") == "tool_result"
            for b in content
        )
    return False

# Find turn boundary: last user message that is NOT a tool result
turn_start_idx = 0
for i in range(len(messages) - 1, -1, -1):
    msg = messages[i]
    if get_role(msg) == "user" and not is_tool_result_msg(msg):
        turn_start_idx = i + 1  # current turn starts after this user message
        dbg(f"TURN_BOUNDARY at [{i}], turn starts at [{turn_start_idx}]")
        break

# Collect all text + tools from current turn's assistant messages
turn_text = ""
turn_tools = []

for msg in messages[turn_start_idx:]:
    if get_role(msg) != "assistant":
        continue
    content = get_content(msg)
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")
            if btype == "text":
                turn_text += block.get("text", "")
            elif btype == "tool_use":
                name = block.get("name", "")
                if name and name not in turn_tools:
                    turn_tools.append(name)
    elif isinstance(content, str):
        turn_text += content

dbg(f"TURN_TEXT_LEN={len(turn_text)}")
dbg(f"TURN_TEXT_PREVIEW={repr(turn_text[:200])}")
dbg(f"TURN_TOOLS={turn_tools}")

# Claim words check
CLAIM_RE = re.compile(
    r'готово|работает|задеплоен|проверен|проверено|verified|deployed'
    r'|done|ready|works|confirmed|✅|успешно|запущен|published|shipped',
    re.IGNORECASE
)
has_claims = bool(CLAIM_RE.search(turn_text))

# Verification tools check
VERIFY_PREFIXES = [
    'Bash', 'Read', 'mcp__supabase', 'mcp__playwright',
    'mcp__Claude_Preview', 'mcp__Claude_in_Chrome',
    'mcp__a4a42010', 'WebFetch', 'WebSearch'
]
has_verify = any(any(p in t for p in VERIFY_PREFIXES) for t in turn_tools)

dbg(f"has_claims={has_claims} | has_verify={has_verify}")
print(f"has_claims={has_claims}")
print(f"has_verify={has_verify}")
PYEOF

# ── 5. Run analysis ──────────────────────────────────────────────
ANALYSIS=$(python3 "$PYFILE" "$TRANSCRIPT" "$DEBUG_LOG" 2>>"$DEBUG_LOG")
PY_EXIT=$?
rm -f "$PYFILE"

echo "ANALYSIS=[$ANALYSIS] PY_EXIT=$PY_EXIT" >> "$DEBUG_LOG"

# ── 6. Decision ──────────────────────────────────────────────────
HAS_CLAIMS=$(echo "$ANALYSIS" | grep -c "has_claims=True")
HAS_VERIFY=$(echo "$ANALYSIS" | grep -c "has_verify=True")

echo "DECISION: HAS_CLAIMS=$HAS_CLAIMS HAS_VERIFY=$HAS_VERIFY" >> "$DEBUG_LOG"

if [ "$HAS_CLAIMS" -gt 0 ] && [ "$HAS_VERIFY" -eq 0 ]; then
  echo "OUTCOME=BLOCK" >> "$DEBUG_LOG"
  echo "══════════════════════════════════════════════════════════════"
  echo "🚫 BLOCKED: Unverified claim detected"
  echo "══════════════════════════════════════════════════════════════"
  echo ""
  echo "Your response contains claim words (готово/done/✅/works) but"
  echo "no verification tool was called (Bash/Read/MCP/WebFetch)."
  echo ""
  echo "PROVE IT or REMOVE THE CLAIM."
  echo "══════════════════════════════════════════════════════════════"
  exit 2
fi

echo "OUTCOME=ALLOW" >> "$DEBUG_LOG"
exit 0
