#!/bin/bash
# PostToolUse hook — auto-formats TypeScript/TSX files after Edit or Write.
# Reads tool result JSON from stdin to get the file path that was just modified.
# Only runs if the file is .ts or .tsx and prettier is available.

INPUT=$(cat)

# Extract file path from tool result
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # PostToolUse gives us the tool input — check file_path field
    path = data.get('tool_input', {}).get('file_path', '') or data.get('file_path', '')
    print(path)
except:
    print('')
" 2>/dev/null)

# Only format TypeScript/TSX files
if [[ "$FILE_PATH" == *.ts ]] || [[ "$FILE_PATH" == *.tsx ]]; then
    # Check if prettier is available in the web app
    PRETTIER="$(dirname "$FILE_PATH")"
    # Walk up to find package.json with prettier
    WEB_DIR="$(pwd)/apps/web"
    if [ -f "$WEB_DIR/node_modules/.bin/prettier" ]; then
        "$WEB_DIR/node_modules/.bin/prettier" --write "$FILE_PATH" --log-level silent 2>/dev/null
    fi
fi

exit 0
