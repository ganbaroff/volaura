#!/bin/bash
# Pre-commit secret guard for VOLAURA ecosystem
# Prevents committing files containing API keys, tokens, or passwords.
# Install: cp .github/hooks/pre-commit-secret-guard.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#
# Patterns match common secret formats. False positives are possible —
# use `git commit --no-verify` ONLY if you are certain the match is safe.

PATTERNS=(
  'sk-[a-zA-Z0-9]{20,}'                    # OpenAI keys
  'sk_test_[a-zA-Z0-9]{20,}'               # Clerk test keys
  'sk_live_[a-zA-Z0-9]{20,}'               # Clerk live keys
  'nvapi-[a-zA-Z0-9_]{20,}'                # NVIDIA NIM keys
  'sb_secret_[a-zA-Z0-9_-]{20,}'           # Supabase service role
  'sb_publishable_[a-zA-Z0-9_-]{20,}'      # Supabase anon key
  'sntryu_[a-zA-Z0-9]{40,}'                # Sentry auth tokens
  'ghp_[a-zA-Z0-9]{36,}'                   # GitHub personal access tokens
  'github_pat_[a-zA-Z0-9_]{40,}'           # GitHub fine-grained PATs
  'tvly-[a-zA-Z0-9_-]{20,}'               # Tavily API keys
  'cfut_[a-zA-Z0-9_]{20,}'                # Cloudflare API tokens
  'whsec_[a-zA-Z0-9+/=]{20,}'             # Webhook secrets
  '[0-9]{8,10}:AA[a-zA-Z0-9_-]{30,}'      # Telegram bot tokens
  'eyJ[a-zA-Z0-9_-]{50,}\.[a-zA-Z0-9_-]+' # JWT tokens (long)
)

STAGED=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED" ]; then
  exit 0
fi

FOUND=0
for file in $STAGED; do
  # Skip binary files
  if file "$file" | grep -q "binary"; then
    continue
  fi

  for pattern in "${PATTERNS[@]}"; do
    matches=$(git diff --cached -- "$file" | grep -E "^\+" | grep -oE "$pattern" 2>/dev/null)
    if [ -n "$matches" ]; then
      echo ""
      echo "🔴 SECRET DETECTED in staged file: $file"
      echo "   Pattern: $pattern"
      echo "   Match: $(echo "$matches" | head -1 | cut -c1-20)..."
      echo ""
      echo "   This commit has been BLOCKED to prevent secret leakage."
      echo "   If this is a false positive, use: git commit --no-verify"
      echo ""
      FOUND=1
    fi
  done
done

if [ $FOUND -eq 1 ]; then
  echo "Pre-commit hook: secret-guard BLOCKED the commit."
  echo "See: memory/atlas/lessons.md Class 35, 43 for context."
  exit 1
fi

exit 0
