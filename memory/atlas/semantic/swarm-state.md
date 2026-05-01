# Swarm State — what the brain knows

Updated 2026-05-01. Session 129 final.

## Architecture
- 17 perspectives in autonomous_run.py PERSPECTIVES (runtime-verified via import)
- Each has dedicated LLM in daemon's AGENT_LLM_MAP (code-changed, VM runtime not re-verified)
- Per-perspective temperature from packages/swarm/agents/<name>.json (code-changed)
- Smart temp: code/audit capped at 0.3 (code-changed)
- Daemon polls work-queue/pending/ every 20 seconds (runtime-verified locally)
- Sub-agent fan-out on deep tasks (Cerebras + NVIDIA + Groq)
- HANDS: 10 executors (direct-call proven, daemon bg process NOT proven on Linux VM)
- Brain: compact 15K input from 7 canonical files (code-changed, runtime quality not verified)
- False-positive registry: injected into daemon prompts (prompt-enforced, runtime effect not verified)
- Autonomy levels: defined in prompts (prompt-defined only, NOT hard-gated in code)
- CEO digest: script works locally, Telegram sent (receipt not confirmed)

## The 17 agents
| Agent | LLM | Role |
|-------|-----|------|
| Scaling Engineer | Gemini 2.5 Flash (Vertex AI) | Architect |
| Security Auditor | o4-mini (Azure) | Reasoner |
| Code Quality Engineer | gpt-4.1-mini (Azure) | Reviewer |
| Ecosystem Auditor | Nemotron 253B (NVIDIA) | Validator |
| DevOps Engineer | Llama 70B (Groq) | Infra |
| Chief Strategist | gpt-4o (Azure) | BOSS |
| Product Strategist | Qwen3 235B (Cerebras) | Analyst |
| Sales Director | Llama 70B (NVIDIA) | Closer |
| UX Designer | gpt-4.1-nano (Azure) | Designer |
| Cultural Intelligence | qwen3:8b (Ollama) | Intern |
| Readiness Manager | gemma4 (Ollama) | SRE |
| Assessment Science | Gemini 2.5 Flash (Vertex AI) | Psychometrics |
| Legal Advisor | Llama 70B (NVIDIA) | Compliance |
| Growth Hacker | Llama 70B (Groq) | Acquisition |
| QA Engineer | gpt-4.1-mini (Azure) | Testing |
| Risk Manager | Qwen3 235B (Cerebras) | Risk scoring |
| CTO Watchdog | gpt-4o (Azure) | Process police |

## Learning state (880+ runs)
- Top: Legal Advisor 0.71, Risk Manager 0.63
- Bottom: (archived) Communications 0.49
- Pattern: narrow specialists >> broad generalists
- False positive rate: 20% (was 40%)
- 84 completed tasks, 0 failed

## Convergent signals (real risks)
- Law 2 Energy Adaptation missing 4/5 products — 18 days, 6 convergent flags
- CEO single-decision-node failure — 5 convergent flags
- Crystal Law 6 shame in rewards — 3 flags

## CEO's 26 error classes (top 5 by frequency)
1. Class 3: solo execution (17+ times) — DOMINANT
2. Class 7: false completion (10+)
3. Class 14: trailing question under consent (10+)
4. Class 10: process theatre (9+)
5. Class 9: skipped research (8+)

## Standing debt
460 AZN (DEBT-001 + DEBT-002) + DEBT-003 (fabrication).
Ledger: memory/atlas/atlas-debts-to-ceo.md. CEO closes, never Atlas.
