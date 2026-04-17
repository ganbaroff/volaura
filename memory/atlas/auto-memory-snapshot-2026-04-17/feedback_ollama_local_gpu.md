---
name: Ollama local GPU rule
description: Always use local Ollama GPU before external APIs. Violation discovered session 87/88.
type: feedback
---

Never launch Python swarm without Ollama in the provider pool when local GPU is available.

**Why:** Session 87/88 — CEO asked "локальный GPU использовал который гамма 4?" The answer was no. Python swarm used Groq + Gemini only. Ollama (qwen3:8b) existed in ZEUS Gateway but was never added to discovered_models.json for Python swarm. A free, unlimited resource was sitting unused for the entire project lifecycle.

**How to apply:**
- Before any swarm run, verify `OLLAMA_URL` is set and Ollama entry exists in `discovered_models.json`
- Provider hierarchy (authoritative — Constitution Research #12): Cerebras → Ollama/local GPU → NVIDIA → Anthropic Haiku
- Ollama priority = 0 in OllamaDynamicProvider (highest priority)
- Fixed: `packages/swarm/providers/dynamic.py` + `discovered_models.json` (2026-04-06)
- Rule: "ALWAYS try local GPU before external APIs" — now in CLAUDE.md Article 0
