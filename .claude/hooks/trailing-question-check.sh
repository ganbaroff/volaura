#!/bin/bash
# trailing-question-check.sh — fires on Stop event (assistant turn finished).
#
# Detects when the assistant ended a response with a trailing "?" on a reversible/
# low-cost action. CEO has caught this 3+ times in a single session (2026-04-15).
# Text-rule in atlas-operating-principles.md loses to Anthropic training weights
# that bias toward "confirm before action." This hook turns the detection into
# a contextual flag that style-brake.sh reads on the NEXT UserPromptSubmit and
# injects a loud warning — much stronger than a silent rule in a file.
#
# Strategy: NOT a blocking hook (cannot rewrite a response that already landed).
# Instead: write a flag that the next turn's pre-prompt hook surfaces as a visible
# "YOU JUST BROKE THE RULE" reminder.

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
FLAG_FILE="$PROJECT_DIR/.claude/last-trailing-question.flag"
INPUT=$(cat)

# Stop-event payload contains transcript_path
TRANSCRIPT=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('transcript_path','') or '')
except:
    print('')
" 2>/dev/null)

[ -z "$TRANSCRIPT" ] && exit 0
[ ! -f "$TRANSCRIPT" ] && exit 0

# Pull last assistant text from transcript (JSONL). Last 20 lines is plenty —
# transcripts append sequentially.
LAST_ASSISTANT=$(tail -n 20 "$TRANSCRIPT" 2>/dev/null | python3 -c "
import json, sys
text_parts = []
for line in sys.stdin:
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get('type') != 'assistant':
        continue
    msg = d.get('message', {})
    content = msg.get('content', [])
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
# Keep only the last turn's text
print(text_parts[-1] if text_parts else '')
" 2>/dev/null)

[ -z "$LAST_ASSISTANT" ] && exit 0

# Strip trailing whitespace and get the last non-empty line
LAST_LINE=$(echo "$LAST_ASSISTANT" | python3 -c "
import sys
lines = [l.rstrip() for l in sys.stdin.read().split('\n') if l.rstrip()]
print(lines[-1] if lines else '')
" 2>/dev/null)

# Check: does the last non-empty line end with a "?" (possibly followed by
# typical emotive chars like )) )? Skip if line is clearly asking CEO for
# strategic input (long, ends with multiple options listed) — we only catch
# the short conversational "пушим?" / "сделать?" / "беру?" pattern.
#
# Heuristic: if last line is under 80 chars AND ends with ? (with optional
# trailing ) or !) → flag it.

IS_TRAILING=$(echo "$LAST_LINE" | python3 -c "
import sys, re
line = sys.stdin.read().strip()
if not line:
    print('0'); sys.exit()
# Skip if clearly a structured multi-option question (has '—' or '•' or numbered list)
if re.search(r'\b(какие варианты|option [a-d]|вариант [0-9]|or [A-D]:)\b', line, re.I):
    print('0'); sys.exit()
# Trigger: short line ending in ? with optional trailing ) ! .
m = re.search(r'\?[\)\!\.]*\s*$', line)
if m and len(line) < 100:
    print('1')
else:
    print('0')
" 2>/dev/null)

if [ "$IS_TRAILING" = "1" ]; then
  printf '%s\n' "$LAST_LINE" > "$FLAG_FILE"
fi

exit 0
