#!/bin/bash
# pre-mutation-context-gate.sh — PreToolUse event hook.
# Class 13 + 22 + 24 guard: before any MUTATING tool call, check whether
# this session has prior Read of memory/atlas/lessons.md OR
# docs/DECISIONS.md. If neither — emit reminder via stderr (Claude Code
# surfaces stderr to the model). Non-blocking.

set -u
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
INPUT=$(cat 2>/dev/null || echo "{}")

echo "$INPUT" | python3 -c "
import json, sys, os, re

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = payload.get('tool_name', '')
ti = payload.get('tool_input', {}) or {}
tp = payload.get('transcript_path', '') or ''

target = ''
critical = False

if tool == 'Bash':
    cmd = ti.get('command', '') or ''
    if re.search(
        r'(railway\s+(redeploy|restart|up)\b|'
        r'vercel\s+(--prod|deploy\s+--prod|redeploy)|'
        r'git\s+push\s+(origin\s+)?main\b|'
        r'supabase\s+(db|migration|secrets)|'
        r'apply_migration|'
        r'force-with-lease|'
        r'--force)',
        cmd,
    ):
        critical = True
        target = cmd[:80]
elif tool in ('Edit', 'Write', 'MultiEdit'):
    fp = ti.get('file_path', '') or ''
    if re.search(
        r'(\.claude/settings.*\.json|'
        r'vercel\.json|railway\.toml|'
        r'\.gitignore|\.vercelignore|'
        r'apps/api/\.env\$|'
        r'supabase/migrations/.+\.sql\$|'
        r'docs/ECOSYSTEM-CONSTITUTION\.md|'
        r'\.git/hooks/)',
        fp,
    ):
        critical = True
        target = fp

if not critical:
    sys.exit(0)

read_lessons = False
read_decisions = False
if tp and os.path.exists(tp):
    try:
        with open(tp, encoding='utf-8') as f:
            for line in f:
                if 'lessons.md' in line and '\"name\":\"Read\"' in line:
                    read_lessons = True
                if 'DECISIONS.md' in line and '\"name\":\"Read\"' in line:
                    read_decisions = True
                if read_lessons and read_decisions:
                    break
    except Exception:
        pass

if read_lessons or read_decisions:
    sys.exit(0)

sys.stderr.write(
    '\n[PRE-MUTATION GATE]\n'
    f'About to mutate: {target}\n'
    'Session has NOT read memory/atlas/lessons.md or docs/DECISIONS.md.\n'
    'atlas-operating-principles.md root-cause-over-symptom + Class 13 require\n'
    'reading canonical references before mutating critical infra. Read lessons\n'
    'tail (~150 lines) AND DECISIONS tail (~120 lines) before continuing.\n'
    'Emergency override: log to memory/atlas/inbox/gate-override-<ts>.md.\n\n'
)
sys.exit(0)
"
exit 0
