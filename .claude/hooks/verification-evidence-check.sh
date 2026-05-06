#!/bin/bash
# verification-evidence-check.sh — Stop event hook.
# Class 26/27/14 guard: scan last assistant message for verification claims
# (готов / done / verified / fixed / closed / passed / deployed / уверен).
# If 2+ claim words AND zero tool_use blocks in same turn → write flag.
# style-brake.sh on next UserPromptSubmit injects loud reminder.
# Does NOT block (cannot rewrite landed response).

set -u
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_DIR"
INPUT=$(cat 2>/dev/null || echo "{}")

echo "$INPUT" | python3 -c "
import json, sys, os, re

flag_path = '.claude/last-verification-gap.flag'
try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tp = payload.get('transcript_path', '') or ''
if not tp or not os.path.exists(tp):
    sys.exit(0)

CLAIM_RX = re.compile(
    r'\b(готов(?:о|ы)?|done|работает|works?|fixed|починил|проверил|'
    r'verified|закрыт|closed|успешно|deployed|live|healthy|passed|'
    r'completed|завершен)\b',
    re.IGNORECASE,
)
FP_RX = re.compile(
    r'(awaiting|pending|нужно|будет проверено|не проверял|untested|'
    r'не проверено|verified externally only|skip(?:ped)?|не выполнено)',
    re.IGNORECASE,
)

last_text = []
tool_uses = 0
seen = False
try:
    with open(tp, encoding='utf-8') as f:
        msgs = [json.loads(line) for line in f if line.strip()]
    for m in reversed(msgs):
        if m.get('type') == 'user':
            if seen:
                break
            continue
        if m.get('type') != 'assistant':
            continue
        seen = True
        content = m.get('message', {}).get('content', [])
        if isinstance(content, list):
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                if blk.get('type') == 'text':
                    last_text.append(blk.get('text', ''))
                elif blk.get('type') == 'tool_use':
                    tool_uses += 1
        elif isinstance(content, str):
            last_text.append(content)
except Exception:
    sys.exit(0)

text = '\n'.join(last_text)
if not text:
    sys.exit(0)

claims = len(CLAIM_RX.findall(text))
fps = len(FP_RX.findall(text))

if claims >= 2 and tool_uses == 0 and claims > fps:
    try:
        with open(flag_path, 'w', encoding='utf-8') as fh:
            fh.write(f'verification-gap claim_hits={claims} tool_uses=0 fp={fps}\n')
    except Exception:
        pass

sys.exit(0)
" 2>/dev/null
exit 0
