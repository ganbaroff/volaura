# Telegram Bot Audit — Session 113, 2026-04-16

CEO complaint: "твой агент в телеграме смок тест предлагает второй день подряд. завис."

## Root cause: stale heartbeat context → LLM repetition

`_handle_atlas()` at line 1931-1935 of `telegram_webhook.py` reads `heartbeat.md` into system prompt every request (up to 2000 chars). Heartbeat was Session 112 which led with Session 111's highlight "CEO прошёл signup → assessment → AURA". LLM inferred "smoke test E2E" was the top priority and recommended it each time CEO wrote.

**Fix applied this session:** heartbeat.md updated to Session 113 context (two P0 shipped, fabrication audit closed, self-wake cron active, remaining items are MIRT/ASR/DIF backend). Next LLM request will read current state instead of smoke-test-heavy Session 111/112 context.

Anti-loop mechanism (LoopCircuitBreaker, lines 2170-2198) exists but catches literal duplicates, not semantic repeats ("same idea different words"). This is a known gap — structural fix requires embedding-based similarity which isn't trivial for a 2500-line bot file. Logged as observation, not fixed.

## Security: HMAC present — proposal was wrong

Security Auditor proposal (6d0bd9d5) claimed "Telegram HMAC validation missing in production." Verified false:
- Line 2262-2272: `X-Telegram-Bot-Api-Secret-Token` checked via `hmac.compare_digest()`
- Fail-closed: if `TELEGRAM_WEBHOOK_SECRET` not set, returns 403 to ALL requests
- Rate limiter also applied: `@limiter.limit(RATE_DEFAULT)` at line 2252

Proposal dismissed as inaccurate — agent did not read the actual code.

## Strengths

Bot architecture is solid. 2485 lines, well-segmented:
- 16 command handlers (/status, /proposals, /ecosystem, /findings, /simulate, /agents, /ask, /swarm, /queue, /help, /backlog, /skills, atlas free-text + 3 more)
- Action layer: imperatives create GitHub issues or inbox files before LLM responds
- Emotional state detection feeds into system prompt with 4-state model (A/B/C/D)
- Loop circuit breaker with multi-signal detection + automatic issue creation
- Self-learning: `_atlas_extract_learnings()` writes observations about CEO to DB after each exchange
- Free-tier provider chain: NVIDIA NIM → Gemini → Groq (no Anthropic, cost-compliant)
- Memory injection: identity + emotional_dimensions + lessons + journal + heartbeat + canonical memory + learnings from DB

## Risks

1. **Context window budget** — system prompt is ~9000 chars of canonical memory (line 1971) + identity + emotional + learnings + heartbeat + action block. With NVIDIA NIM (8K context on llama-3.3-70b) this is tight. Gemini 2.0 Flash has 1M context so no issue there, but Groq also has limited context. Risk: truncated system prompt on NVIDIA path → Atlas loses identity.

2. **Semantic loop gap** — anti-loop catches literal duplicates but CEO's "второй день подряд" complaint is semantic repetition that slips through. Needs embedding-based similarity or topic-tracking across sessions (not just last 2 replies).

3. **Stale context dependency** — bot reads heartbeat.md from filesystem every request. If heartbeat isn't updated between sessions, bot gives stale advice. Now fixed, but fragile — depends on Atlas CLI updating heartbeat at session close.

4. **Self-learning quality** — `_atlas_extract_learnings()` extracts CEO patterns via LLM and stores in `atlas_learnings` table. No human review. Accumulated learnings might drift or contradict canonical memory/ceo/ files. Should cross-reference periodically.

5. **Provider fallback logging** — fallback events logged via loguru but not to zeus.governance_events. `emit_fallback_event()` in model_router.py exists but isn't wired into the Telegram bot's provider chain. Means degraded-provider events are invisible to the governance layer.

## What to do next

- Router security sweep: verify rate limits + auth requirements on 5 recently-added routers (lifesim, grievance, community, webhooks_sentry, zeus_gateway) — per triage, canonical surviving proposal from 4-agent cluster
- Consider adding session-level topic tracking to the anti-loop system — if "smoke test" appears as recommended action in 3+ consecutive exchanges across 24h, inject explicit "I already recommended this — here's what's NEW since then" preface into system prompt
- Wire Telegram bot's provider chain into model_router.py fallback events (currently uses inline httpx calls, not the centralized router)
