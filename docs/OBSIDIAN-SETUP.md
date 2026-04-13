# Obsidian as Atlas Second Brain — Setup

**Decision:** Obsidian stays. Two plugins installed today: `claude-code-mcp` (Ian Sinnott) and `copilot` (Logan Yang). Research backed — industry consensus is Obsidian remains the best git-native second-brain vault in 2026. Supermemory + mem0 are complementary hot-memory layers, separate evaluation sprint.

## What's installed

`.obsidian/plugins/claude-code-mcp/` (1.1.8) — exposes vault over MCP at `http://localhost:22360/mcp`. Claude Code reads and writes memory/atlas/*.md live while CEO reads the same files visually in Obsidian.

`.obsidian/plugins/copilot/` (3.2.7) — vault-wide RAG chat with native Azure OpenAI support. Ask questions across the whole memory tree.

`.obsidian/community-plugins.json` — marks both as enabled.

`.mcp.json` — registered `obsidian` server so Claude Code discovers it automatically.

## Fresh-clone setup (run once per machine)

```bash
bash scripts/setup-obsidian.sh
```

The script fetches plugin binaries from GitHub releases into `.obsidian/plugins/`. Plugin binaries are gitignored (`.obsidian/` is excluded) so every developer runs this once.

## Copilot — Azure OpenAI config

Open Obsidian → Copilot → Settings → Model tab. Fields needed:

- **Azure API key** — from Azure AI Foundry portal, resource "Keys & Endpoint"
- **Azure instance name** — the Foundry resource name, e.g. `volaura-ai`
- **Azure deployment name** — the model you deployed, e.g. `gpt-4o-mini` or `gpt-4o`
- **Azure API version** — `2024-10-21` works today

The `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` that CEO provided 2026-04-16 are **Entra ID app credentials** — different animal. They authenticate a service principal to Azure ARM, not an OpenAI resource. Path:

1. Use Entra credentials to create an Azure OpenAI resource via ARM (one-time, Microsoft for Startups credits).
2. Deploy a model inside that resource (`gpt-4o-mini` is free tier friendly).
3. Copy the resource's API key + endpoint into Copilot.

If Azure deployment is pending, Copilot also speaks native Gemini and OpenRouter — set those in the same settings panel with existing `GEMINI_API_KEY` / `OPENROUTER_API_KEY` from `apps/api/.env`.

## Claude Code ↔ Obsidian bridge

Obsidian must be running for the MCP bridge to answer. When closed, the `obsidian` entry in `.mcp.json` is silently unreachable — Claude Code still works on files directly. When Obsidian is open, we get live two-way editing plus graph-aware search.

## Why not Logseq / Supermemory / mem0 right now

Logseq shipped MCP in January 2026 but block-metadata noise hurts AI parsing for agents — Obsidian's clean Markdown wins. Supermemory ranks #1 on LongMemEval-S (85.4%, sub-300ms recall) and is worth a sprint, but it's a separate hot memory layer on top of the cold git-tracked vault, not a replacement. mem0 costs more tokens per recall and is a slower competitor. Decision: keep Obsidian as the source of truth, evaluate Supermemory later as performance accelerator.
