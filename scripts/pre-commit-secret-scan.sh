#!/usr/bin/env bash
# Pre-commit secret scanner (CVSS 9.8 per memory/swarm/research/elite-audit-session93-2026-04-12.md).
# Blocks commits that include obvious live secrets in STAGED content.
# Patterns are deliberately narrow — zero false-positives policy, because a noisy
# hook is a disabled hook. Widen only on a real incident, not on speculation.
#
# This file is NOT tracked (git hooks live in .git/). Install is manual:
#   cp scripts/pre-commit-secret-scan.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit

set -e

# Gather staged additions only (what this commit would publish).
STAGED=$(git diff --cached --diff-filter=ACM -U0 | grep -E '^\+' | grep -v '^\+\+\+' || true)

if [ -z "$STAGED" ]; then
    exit 0
fi

# Explicit, narrow patterns. Each must be unique enough that a match is almost
# certainly a real key, not a README example or a fixture.
HITS=""

check() {
    local name="$1" pattern="$2"
    if echo "$STAGED" | grep -E "$pattern" >/dev/null 2>&1; then
        HITS="$HITS\n  - $name"
    fi
}

# Core cloud / provider keys
check "OpenAI sk-proj-"            'sk-proj-[A-Za-z0-9_-]{40,}'
check "Anthropic sk-ant-api"       'sk-ant-api[A-Za-z0-9_-]{40,}'
check "Google/Gemini AIzaSy"       'AIzaSy[A-Za-z0-9_-]{33}'
check "Groq gsk_"                  'gsk_[A-Za-z0-9]{40,}'
check "OpenRouter sk-or-v1-"       'sk-or-v1-[A-Za-z0-9]{40,}'
check "NVIDIA nvapi-"              'nvapi-[A-Za-z0-9_-]{60,}'
check "DeepSeek sk-"               'sk-[a-f0-9]{32}'
# Supabase + auth
check "Supabase service-role JWT"  'eyJhbGciOiJIUzI1NiI[A-Za-z0-9_.-]+role\\"":\\""service_role'
check "Supabase sb_secret_"        'sb_secret_[A-Za-z0-9_-]{20,}'
# Stripe
check "Stripe sk_live_"            'sk_live_[A-Za-z0-9]{24,}'
check "Stripe whsec_"              'whsec_[A-Za-z0-9]{32,}'
# Railway / infra
check "Railway token"              'railway_[A-Za-z0-9]{40,}'
# Tavily / ElevenLabs / Azure / mem0
check "Tavily tvly-"               'tvly-[A-Za-z0-9_-]{20,}'
check "mem0 m0-"                   'm0-[A-Za-z0-9]{32,}'
check "Azure Entra ZUX"            'ZUX[A-Za-z0-9~._-]{35,}'
# GitHub
check "GitHub PAT gho_"            'gho_[A-Za-z0-9]{36,}'
check "GitHub PAT ghp_"            'ghp_[A-Za-z0-9]{36,}'
# Telegram
check "Telegram bot token"         '[0-9]{9,10}:AA[A-Za-z0-9_-]{33,}'

if [ -n "$HITS" ]; then
    echo "🛑 pre-commit: secret pattern(s) detected in staged content:"
    echo -e "$HITS"
    echo ""
    echo "If this is a false positive (e.g. a fixture or doc example):"
    echo "  git commit --no-verify"
    echo "Otherwise:"
    echo "  1. Rotate the leaked key immediately."
    echo "  2. Remove it from the staged diff."
    echo "  3. Re-stage and retry commit."
    exit 1
fi

# Extra guard: block apps/api/.env from ever being staged (belt + suspenders)
if git diff --cached --name-only | grep -E '^apps/api/\.env$' >/dev/null 2>&1; then
    echo "🛑 pre-commit: apps/api/.env is staged. That file is .gitignored on purpose."
    echo "  If you really need to commit it, use: git commit --no-verify"
    exit 1
fi

echo "🔒 pre-commit secret scan: clean."
exit 0
