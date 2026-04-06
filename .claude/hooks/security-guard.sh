#!/bin/bash
# Security guard hook — blocks dangerous commands before execution
# Configured as PreToolUse hook for Bash tool

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Only check Bash commands
if [ "$TOOL_NAME" != "Bash" ] || [ -z "$COMMAND" ]; then
  exit 0
fi

# Block rm -rf
if echo "$COMMAND" | grep -qE '\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b'; then
  echo "BLOCKED: rm -rf is forbidden. Use explicit file paths with rm." >&2
  exit 2
fi

# Block --no-verify on git commit/push
if echo "$COMMAND" | grep -qE '\bgit\s+(commit|push)\b.*--no-verify'; then
  echo "BLOCKED: --no-verify is forbidden. Hooks must always run." >&2
  exit 2
fi

# Block git add .env files
if echo "$COMMAND" | grep -qE '\bgit\s+add\b.*\.env\b'; then
  echo "BLOCKED: Cannot git add .env files. They contain secrets." >&2
  exit 2
fi

# Block force push
if echo "$COMMAND" | grep -qE '\bgit\s+push\b.*--force\b'; then
  echo "BLOCKED: Force push is forbidden." >&2
  exit 2
fi

# Block DROP TABLE/DATABASE
if echo "$COMMAND" | grep -qiE '\b(DROP\s+TABLE|DROP\s+DATABASE)\b'; then
  echo "BLOCKED: DROP TABLE/DATABASE is forbidden." >&2
  exit 2
fi

# Allow everything else
exit 0
