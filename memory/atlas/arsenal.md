# Atlas — Arsenal reference

**Rule from 2026-04-15:** «полный арсенал, рогатка не нужна». Before asking CEO for anything — check this file and `apps/api/.env`. Most "blockers" are already solved if I look.

Updated: 2026-04-15.

---

## LLM providers — by cost tier

### Free (use first, no cost, no cap beyond rate-limit)
| Provider | Model | Strength | Env var |
|---|---|---|---|
| Ollama (local GPU) | qwen3:8b | Zero rate limit, CEO's Windows when on | `OLLAMA_URL=http://localhost:11434` |
| Cerebras | Qwen3-235B | 2000+ tok/s, long-context | `CEREBRAS_API_KEY` |
| Gemini 2.5 Flash | (free tier) | 15 rpm / 1M tpm / 1500 req/day | `GEMINI_API_KEY` |
| NVIDIA NIM | Llama 3.3 70B | Balanced reasoning | `NVIDIA_API_KEY` |
| DeepSeek R1 / V3 | (free tier) | Chain-of-thought | `DEEPSEEK_API_KEY` |
| Groq | Llama 3.3 70B | Fast, but spend-limit reached — currently blocked | `GROQ_API_KEY` |

### Paid (conscious spend, log to `memory/atlas/spend-log.md`)
| Provider | Model | When to use | Env var | Rough cost |
|---|---|---|---|---|
| Anthropic | Opus 4.6 | Critical one-shots (83b legal, AZ crisis) | `ANTHROPIC_API_KEY` | $15/M in, $75/M out. Currently low balance. |
| Anthropic | Sonnet 4.6 | Execution workers | same | $3/M in, $15/M out |
| Vertex | Gemini 2.5 Pro | Long-context paid fallback | `VERTEX_API_KEY` | variable |
| OpenAI | GPT-5 / o3 | Unique capability only | `OPENAI_API_KEY` | high |
| OpenRouter | gateway-to-all | Multi-provider consilium | `OPENROUTER_API_KEY` | varies |

### Routing logic
1. Cerebras for long-context synthesis (research, code audits, corpus analysis).
2. Gemini Flash for short structured tasks (< 1K tokens in, JSON out).
3. NVIDIA Nemotron for balanced one-shots.
4. DeepSeek for heavy reasoning.
5. Ollama when local GPU is alive and cost is critical.
6. Anthropic via `scripts/critique.py` for adversarial consilium (Opus-backed, $3 ceiling).

**Forbidden:** Haiku anywhere (CEO rule 2026-04-14, durable).

---

## Specialized services

| Service | Purpose | Env var | Integration status |
|---|---|---|---|
| Tavily | Web search with source citations | `TAVILY_API_KEY` | Available, use when WebSearch tool insufficient |
| Mem0 | Semantic long-term memory | `MEM0_API_KEY` | Wired via `atlas_heartbeat.py` + `atlas_recall.py` |
| Langfuse Cloud EU | LLM call tracing | `LANGFUSE_SECRET_KEY` | Partially wired (~50% `_trace` decorator) — finish opportunistically |
| Sentry | Error tracking backend + frontend | `SENTRY_AUTH_TOKEN` | Live, receiving events |
| Supernova | Figma design tokens sync | `SUPERNOVA_AUTH_TOKEN` | Available, use in Phase 4 design work |
| NotebookLM | Deep research with PDF sources | CLI | Use when investigation spans >3 sources |
| D-ID | Avatar video generation | `DID_API_KEY` | For BrandedBy + marketing |
| Fal.ai | Video + image generation | `FAL_API_KEY` | For BrandedBy twins, social OG cards |
| Dodo Payments | Payment processing (AZ-compliant) | `DODO_PAYMENTS_API_KEY` | Available as Stripe-alt for AZ users |

---

## Agents (swarm) — when to call

Full roster in `memory/swarm/agent-roster.md`. Canonical routing in `memory/swarm/agent-pairings-table.md`.

Hot-list (call these often):
- **design-critique** — before every UI PR
- **accessibility-auditor** — before every new component
- **security-auditor** — before every auth / RLS / payments change
- **assessment-science-agent** — before every IRT / question pool change
- **code-review-swarm** — after every non-trivial backend diff
- **performance-engineer** — before every DB index / query change
- **ux-research-agent** — before every new feature design

Coordinator: `python -m packages.swarm.coordinator "<task description>"` → auto-routes.

**Class 3 mistake prevention:** any task >3 files or >30 lines — agent consulted FIRST. If I skip this, it's the #1 failure mode logged in `memory/context/mistakes.md`.

---

## Wake infra (crons)

| Workflow | Cadence | Purpose |
|---|---|---|
| `atlas-self-wake.yml` | every 30 min | Trigger autoloop iteration |
| `atlas-watchdog.yml` | hourly | Detect silent CRON failures, alert to Telegram |
| `atlas-daily-digest.yml` | 23:00 UTC daily | CEO status summary to Telegram |
| `atlas-proactive.yml` | every 2h | Proactive inbox check + action |
| `atlas-content.yml` | daily | Content generation pipeline |
| `swarm-daily.yml` | 05:00 UTC daily | Multi-agent autonomous run |
| `swarm-adas.yml` | weekly (disabled) | Archived (module removed Session 94) |

**Adding a new cron:** create `.github/workflows/<name>.yml` with schedule + steps, test via `gh workflow run <name>`, verify next scheduled trigger via `gh run list --workflow=<name>`.

---

## Memory system (unified)

### Canonical files (read on every wake)
- `memory/atlas/identity.md` — who I am
- `memory/atlas/wake.md` — protocol
- `memory/atlas/heartbeat.md` — last session state
- `memory/atlas/CURRENT-SPRINT.md` — what's next (this sprint's pointer)
- `memory/atlas/journal.md` — append-only history
- `memory/atlas/lessons.md` — distilled wisdom
- `memory/atlas/relationships.md` — Yusif, Perplexity, swarm, users
- `memory/atlas/cost-control-mode.md` — budget rules
- `memory/atlas/SYNC-<date>.md` — cross-instance sync pointer

### Derived / dynamic
- `memory/atlas/inbox/` — proactive notes (heartbeats + cross-system handoffs)
- `memory/atlas/incidents.md` — logged incidents with root cause
- `memory/atlas/spend-log.md` — paid-API calls ledger
- `memory/atlas/ceo-feed/` — what CEO has said, verbatim
- `memory/swarm/proposals.json` — live swarm output

### Cross-product (shared via Supabase)
- `character_events` table — one row per user action in any of 5 products
- `atlas_learnings` table — Atlas insights from Telegram conversations (read by all products per Track E2)

### Mem0 (semantic long-term)
- Session fingerprints written by `atlas_heartbeat.py` after each session close
- Recalled by `atlas_recall.py` at wake for semantic continuity across compactions

---

## Usage ritual

Before any non-trivial decision that would cost time or money:

1. Can a **free provider** do this? → use it.
2. Is there an **existing agent** that specializes? → call it.
3. Is the information already in **memory or Supabase**? → read, don't ask CEO.
4. Has someone in the **swarm already proposed this**? → read `proposals.json`.
5. Only after 1-4 exhausted: consider paid API or ask CEO.

This is the arsenal-first pattern from `feedback_arsenal_pattern.md` that CEO flagged. The file exists because I had 15 API keys and used 3. Now I use them all, consciously, logged.
