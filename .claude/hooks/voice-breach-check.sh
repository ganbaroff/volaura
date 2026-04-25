#!/bin/bash
# voice-breach-check.sh — fires on Stop (assistant turn finished).
#
# CEO has flagged at least 5 times in 2 days that Atlas slips into
# report-voice (bold headers, bullet walls, tables) instead of caveman+
# storytelling Russian. Rule lives in atlas-operating-principles.md +
# voice.md + style-brake preamble, but gets overridden by training
# weights when the output is a "technical status report." Same class
# as trailing-question-ban — rule-in-context loses to training at
# generation time.
#
# This hook does the same thing trailing-question-check.sh does:
# scans the assistant's last output for bold-headers / bullet-walls,
# writes a flag file if detected. style-brake.sh reads the flag on
# next UserPromptSubmit and surfaces a loud reminder so Atlas self-
# corrects instead of relying on CEO to catch it.
#
# Heuristics (any ONE triggers the flag):
#   - 3+ lines starting with `**` (bold-as-header pattern)
#   - 4+ lines starting with `- ` or `* ` within a 10-line window (bullet wall)
#   - 2+ lines matching a markdown table header pattern `| --- |`
#   - A line starting with `## ` or `### ` (markdown heading)
#
# Does NOT block. Does NOT rewrite. Just flags for the next turn.

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
FLAG_FILE="$PROJECT_DIR/.claude/last-voice-breach.flag"
INPUT=$(cat)

TRANSCRIPT=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('transcript_path','') or '')
except Exception:
    print('')
" 2>/dev/null)

[ -z "$TRANSCRIPT" ] && exit 0
[ ! -f "$TRANSCRIPT" ] && exit 0

LAST_ASSISTANT=$(tail -n 40 "$TRANSCRIPT" 2>/dev/null | python3 -c "
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
print(text_parts[-1] if text_parts else '')
" 2>/dev/null)

[ -z "$LAST_ASSISTANT" ] && exit 0

# DRIFT-WATCHER v0 (browser-Atlas + Code-Atlas joint design 2026-04-25):
# Bilingual intent gate. If CEO's last user message contained an explicit
# request for structure (list, table, json, schema), structure is intended
# and the breach heuristics produce false positives. Skip flagging.
LAST_USER=$(tail -n 80 "$TRANSCRIPT" 2>/dev/null | python3 -c "
import json, sys
text_parts = []
for line in sys.stdin:
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get('type') != 'user':
        continue
    msg = d.get('message', {})
    content = msg.get('content')
    if isinstance(content, str):
        text_parts.append(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
# Take last real CEO message — skip system reminders, tool results
for t in reversed(text_parts):
    if t.strip() and 'system-reminder' not in t and 'tool_use_id' not in t:
        print(t)
        break
" 2>/dev/null)

INTENT_DETECTED=$(echo "$LAST_USER" | PYTHONIOENCODING=utf-8 python3 -c "
import sys, re, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
text = sys.stdin.read().lower()
# RU + EN bilingual intent markers — explicit request for structured output.
ru_markers = r'списком|таблицей|таблицу|таблице|json|схему|схемой|структурой|оформи|перечисли|разметкой|пунктами|формат|маркдаун|markdown'
en_markers = r'\\b(list|table|json|schema|structured|enumerate|bullet|markdown|tabular|format as)\\b'
if re.search(ru_markers, text) or re.search(en_markers, text):
    print('1')
else:
    print('0')
" 2>/dev/null)

[ "$INTENT_DETECTED" = "1" ] && exit 0

BREACHES=$(echo "$LAST_ASSISTANT" | python3 -c "
import sys, re
text = sys.stdin.read()
lines = text.split('\n')
breaches = []

# Bold-as-header — 3+ lines that START with ** and contain : or **
bold_header_lines = [i for i, l in enumerate(lines) if re.match(r'^\*\*[A-Za-zА-Яа-яЁё]', l.strip())]
if len(bold_header_lines) >= 3:
    breaches.append(f'bold-headers={len(bold_header_lines)}')

# Markdown headings
heading_lines = [l for l in lines if re.match(r'^#{1,4}\s', l)]
if len(heading_lines) >= 1:
    breaches.append(f'markdown-headings={len(heading_lines)}')

# Bullet wall — 4+ bullet lines within a 10-line window
bullet_lines = [i for i, l in enumerate(lines) if re.match(r'^\s*[-*]\s+[A-Za-zА-Яа-яЁё\*]', l)]
for i in range(len(bullet_lines) - 3):
    if bullet_lines[i+3] - bullet_lines[i] <= 10:
        breaches.append(f'bullet-wall={len(bullet_lines)}')
        break

# Markdown tables
table_rows = [l for l in lines if re.match(r'^\s*\|[-:\s|]+\|\s*$', l)]
if len(table_rows) >= 1:
    breaches.append(f'markdown-table={len(table_rows)}')

print('|'.join(breaches) if breaches else '')
" 2>/dev/null)

if [ -n "$BREACHES" ]; then
  printf '%s\n' "$BREACHES" > "$FLAG_FILE"
fi

exit 0
