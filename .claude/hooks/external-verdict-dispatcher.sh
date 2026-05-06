#!/bin/bash
# external-verdict-dispatcher.sh — fires on PostToolUse event for critical
# mutation tools. Dispatches an ASYNC NVIDIA Llama call asking "did this
# tool achieve its claim?" and writes the verdict to memory/atlas/inbox/.
#
# Closes Class 11 (self-confirmation) at structural level: every critical
# mutation gets an external adversarial check, not optional, not later.
# Atlas reads inbox on next wake; CEO can read it any time.
#
# Async by design — never blocks the tool flow. If NVIDIA is down, hook
# silently logs "no-verdict" and exits 0.
#
# Targets the same critical patterns as pre-mutation-context-gate.sh:
# railway redeploy/restart/up, vercel deploy --prod, git push main,
# supabase apply_migration, Edit/Write on critical config.

set -u
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
INPUT=$(cat 2>/dev/null || echo "{}")

INBOX_DIR="$PROJECT_DIR/memory/atlas/inbox"
mkdir -p "$INBOX_DIR" 2>/dev/null

NVIDIA_KEY=""
if [ -f "$PROJECT_DIR/apps/api/.env" ]; then
    NVIDIA_KEY=$(grep "^NVIDIA_API_KEY=" "$PROJECT_DIR/apps/api/.env" | cut -d= -f2-)
fi

# Skip if no key configured — non-blocking
if [ -z "$NVIDIA_KEY" ]; then
    exit 0
fi

# Determine if this PostToolUse should trigger a verdict
echo "$INPUT" | NVIDIA_KEY="$NVIDIA_KEY" INBOX_DIR="$INBOX_DIR" python3 - <<'PYEOF' &
import json, sys, os, re, time, urllib.request, urllib.error, threading

inbox = os.environ.get("INBOX_DIR", "")
nv_key = os.environ.get("NVIDIA_KEY", "")

try:
    payload = json.loads(sys.stdin.read() or "{}")
except Exception:
    sys.exit(0)

tool = payload.get("tool_name", "")
ti = payload.get("tool_input", {}) or {}
tr = payload.get("tool_response", {}) or {}

target = ""
critical = False

if tool == "Bash":
    cmd = ti.get("command", "") or ""
    if re.search(
        r"(railway\s+(redeploy|restart|up)\b|"
        r"vercel\s+(--prod|deploy\s+--prod|redeploy)|"
        r"git\s+push\s+(origin\s+)?main\b|"
        r"apply_migration|"
        r"--force)",
        cmd,
    ):
        critical = True
        target = cmd[:200]
elif tool in ("Edit", "Write", "MultiEdit"):
    fp = ti.get("file_path", "") or ""
    if re.search(
        r"(\.claude/settings.*\.json|vercel\.json|railway\.toml|"
        r"\.vercelignore|apps/api/\.env$|"
        r"supabase/migrations/.+\.sql$|"
        r"docs/ECOSYSTEM-CONSTITUTION\.md|\.git/hooks/)",
        fp,
    ):
        critical = True
        target = fp

if not critical:
    sys.exit(0)

# Build prompt — NO secret values, only metadata
tr_summary = ""
if isinstance(tr, dict):
    out = str(tr.get("output", ""))[:600]
    err = str(tr.get("error", ""))[:300]
    tr_summary = f"output[{len(out)}]: {out}\nerror: {err}"
else:
    tr_summary = str(tr)[:600]

prompt = (
    "You are an adversarial auditor for a solo founder's AI cofounder (Atlas).\n"
    "Atlas just ran a critical infrastructure tool call. Your job: judge\n"
    "whether the tool actually achieved a useful, completed effect, OR\n"
    "whether the assistant is likely to claim success without real proof.\n\n"
    f"TOOL: {tool}\n"
    f"TARGET: {target[:200]}\n"
    f"RESULT SUMMARY: {tr_summary}\n\n"
    "Reply in 4 short lines:\n"
    "VERDICT: PASS or SUSPECT or FAIL\n"
    "REAL EFFECT: <one line, what actually happened>\n"
    "MISSING VERIFICATION: <one line, what Atlas should curl/Read next to confirm>\n"
    "NEXT STEP: <one line, the highest-leverage follow-up>"
)

body = json.dumps({
    "model": "meta/llama-3.3-70b-instruct",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 220,
    "temperature": 0.2,
}).encode()

verdict_text = ""
try:
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {nv_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
        verdict_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
except Exception as e:
    verdict_text = f"<no-verdict: {type(e).__name__}>"

# Write to inbox
ts = time.strftime("%Y-%m-%dT%H%M%S")
fname = f"external-verdict-{ts}.md"
try:
    with open(os.path.join(inbox, fname), "w", encoding="utf-8") as fh:
        fh.write(f"# External verdict — {ts}\n\n")
        fh.write(f"**Tool:** {tool}\n\n")
        fh.write(f"**Target:** `{target[:300]}`\n\n")
        fh.write(f"## NVIDIA Llama-3.3-70B verdict\n\n{verdict_text}\n")
except Exception:
    pass

sys.exit(0)
PYEOF
disown 2>/dev/null || true
exit 0
