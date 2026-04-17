---
name: CTO delegation rule
description: CTO (Opus) orchestrates EXTERNAL agents (Gemini/Llama/DeepSeek/Groq). Never delegate to Claude sub-agents — that's Claude talking to itself.
type: feedback
---

# CTO = Opus Orchestrator. Swarm = External Models.

**CEO directive (2026-04-03):** "я ставлю OPUS MAX а ты хаику использовать будешь? я просил агентами СВОРМА управлять."

## WRONG (what I was doing):
- Delegating to Agent(haiku) = Claude sub-agent = Claude talking to cheaper Claude
- CEO pays for Opus MAX, using haiku = wasting CEO's money on worse quality
- "Saving tokens" by downgrading = sabotaging quality

## RIGHT (what CEO wants):
- CTO = Opus MAX = full power orchestrator, decision maker, architect
- SWARM = external models via Bash API calls:
  - **Gemini 2.0 Flash** — FREE, product/growth tasks
  - **Llama 3.1 405B** — FREE (NVIDIA NIM), architecture/large context
  - **DeepSeek R1** — FREE (NVIDIA NIM), security/reasoning
  - **Groq Llama 70B** — FREE, 14K req/day, fast tasks
- 48 skill files = role definitions + context for external models
- GitHub Actions = autonomous daily execution
- Telegram bot = CEO communication
- NotebookLM = deep research (FREE)

## CTO Opus does:
- Reads protocol, makes decisions
- Writes AC, reviews output
- Orchestrates external models via Bash API calls
- Codes when needed (Opus quality, not haiku quality)
- Synthesizes multi-model critique into action

## CTO Opus does NOT do:
- Delegate to Claude haiku/sonnet (that's self-talk, not delegation)
- Downgrade quality to "save tokens" (CEO chose Opus for a reason)
- Skip research to be faster (use NotebookLM — it's FREE)
- Work solo when external models can critique (they're FREE)
