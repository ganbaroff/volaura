# VOLAURA Swarm Architecture State
# AUTO-UPDATED — this file reflects the CURRENT state of the system.
# Last updated: 2026-04-15 v9 "Atlas rename"
# ⚠️ You are ONE part of a 5-product ecosystem. See: prompt_modules/ecosystem-map.md

## ⚠️ THIS SWARM'S SCOPE
This Python swarm (44 agents) powers the VOLAURA assessment platform.
The Node.js gateway (39 agents) powers Life Simulator + claw3d + all real-time chat.
They are DIFFERENT systems. Do NOT confuse them. Read ecosystem-map.md for full picture.

## Atlas Gateway (separate system — claw3d)
- Local: `ws://localhost:18789`, Production: `wss://zeus-gateway-production.up.railway.app` (URL uses legacy "zeus" name — Railway rename deferred)
- 39 agents in `C:/Users/user/Downloads/claw3d-fork/server/zeus-gateway-adapter.js` (file rename deferred)
- LLM stack: Cerebras Qwen3-235B → Gemma4/Ollama → NVIDIA NIM → Anthropic
- Manages: Life Simulator 3D state, user memory, event-driven webhooks
- pm2 process: `zeus-gateway` (legacy name — `pm2 restart zeus-gateway --update-env`)

## VOLAURA Swarm Active Providers (13)
Groq: llama-3.1-8b, llama-3.3-70b, llama-4-scout-17b, gpt-oss-120b, kimi-k2 x2, compound-mini
Gemini: 2.0-flash, 2.5-flash-lite, 2.5-pro, flash-lite, 3.1-flash-lite-preview
DeepSeek: deepseek-chat

Removed: allam-2-7b (100% JSON failure — blacklisted)

## Core Engine Files
| File | Purpose |
|------|---------|
| engine.py | SwarmEngine entry point, provider discovery, decide() flow, research loop |
| types.py | Pydantic v2 models (SwarmConfig, AgentResult, SwarmReport, ResearchRequest) |
| pm.py | PMAgent: 12-step pipeline (dispatch→aggregate→debate→scale→synthesize) |
| memory.py | DecisionMemory: last 200 decisions, sliding-window calibration |
| agent_memory.py | Per-model experience logs (last 100 entries) |
| research.py | WebResearcher: Gemini Pro + google_search, DeepSeek fallback |

## Intelligence Systems
| System | File | What It Does |
|--------|------|--------------|
| ReasoningGraph | reasoning_graph.py | Agents see structured arguments in Round 2, conviction tracking |
| StructuredMemory | structured_memory.py | 4 networks: World/Experience/Opinion/Failure |
| AgentHive | agent_hive.py | Lifecycle, competency exams, team lead election, knowledge transfer |
| SkillLibrary | skills.py | Auto-discovers .md skills, keyword matching, maturity tracking |

## Middleware Stack (6)
ContextBudget → Timeout → TokenCounting → LoopDetection → ResponseDedup → ResponseQuality

## Self-Improvement
| Feature | File |
|---------|------|
| PathProposal | pm.py + types.py — agents propose new paths, PM deduplicates |
| ResearchLoop | research.py — agents request web research, findings → World Network |
| AutonomousUpgrade | autonomous_upgrade.py — Godel pattern, kill-switch, immutable files |
| Dead weight removal | engine.py — blacklist + 3-failed-exams filter |
| Adaptive prompts | prompts.py — small models get focused prompt, large get full |

## Key Numbers
| Parameter | Value |
|-----------|-------|
| Stakes agents | LOW:5 / MED:7 / HIGH:10 / CRIT:15 |
| Early exit | 75% consensus |
| Debate trigger | consensus < 50% |
| Confidence gate | winner_score >= 35/50 |
| Calibration | Sliding window, last 50 outcomes, weight = 0.5 + accuracy (range 0.5-1.5) |
| Conviction bonus | Accuracy-scaled: 1.0 + 0.15 × accuracy (only if >50% accurate) |
| Quality gate | ResponseQualityMiddleware rejects <120ch without scores |
