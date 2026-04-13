#!/usr/bin/env bash
# Install Obsidian community plugins for Atlas second-brain integration.
# Per-machine setup — .obsidian/plugins/ is gitignored, so this runs once per clone.
# Docs: docs/OBSIDIAN-SETUP.md

set -euo pipefail

VAULT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGINS_DIR="${VAULT_ROOT}/.obsidian/plugins"

echo "→ Setting up Obsidian plugins at ${PLUGINS_DIR}"
mkdir -p "${PLUGINS_DIR}/claude-code-mcp" "${PLUGINS_DIR}/copilot"

fetch() {
  local owner_repo="$1" version="$2" plugin_dir="$3"
  local base="https://github.com/${owner_repo}/releases/download/${version}"
  for f in main.js manifest.json styles.css; do
    echo "   ${f}"
    curl -sfL -o "${PLUGINS_DIR}/${plugin_dir}/${f}" "${base}/${f}" || {
      echo "   ⚠ ${f} missing (ok if plugin has no styles.css)"
    }
  done
}

echo "→ claude-code-mcp (iansinnott) 1.1.8"
fetch "iansinnott/obsidian-claude-code-mcp" "1.1.8" "claude-code-mcp"

echo "→ copilot (logancyang) 3.2.7"
fetch "logancyang/obsidian-copilot" "3.2.7" "copilot"

echo "✓ Plugins installed."
echo ""
echo "Next steps:"
echo "  1. Open VOLAURA folder as Obsidian vault"
echo "  2. Settings → Community plugins → enable both"
echo "  3. Copilot settings → configure Azure OpenAI or Gemini"
echo "     (see docs/OBSIDIAN-SETUP.md for credentials wiring)"
