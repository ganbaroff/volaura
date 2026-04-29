<!-- RECENTLY_SHIPPED_START -->
## RECENTLY SHIPPED (Session 129 — 2026-04-30)
**Read this FIRST — prevents proposing already-shipped work.**

Session 129: 17-agent team (was 11). Chief Strategist, Sales Director, UX Designer,
DevOps Engineer, Growth Hacker, QA Engineer added. Per-perspective temperature wired
(was hardcoded 1.0). Law 3 "remaining" fix. lint_shame_free.py + audit_dif_bias.py.
Blockers #7 (DIF), #13, #18 verified done.

Session 128: 35+ commits. Daemon 1263→1300+ LOC. Vertex AI agent loop + Azure sub-agents.
PostHog $50K tracking. Telegram reports. Per-perspective memory. Smart temperature.
All P0 blockers closed (code-level). $52K cloud credits connected.
<!-- RECENTLY_SHIPPED_END -->

# Swarm Shared Context — UPDATED 2026-04-26 (Session 125)

**By:** CTO (Code-Atlas) | **Updated:** 2026-04-26 (Session 125 — post-compaction, Codex S5 merged, CI unblocked)

---

## SECURITY / HARD RULES — READ FIRST

### Constitution Article 0 — Provider Chain (NEVER violate)

**NEVER use Anthropic or OpenAI models as swarm perspectives.**

| Priority | Provider | Key env var |
|----------|----------|-------------|
| 1 | Cerebras Qwen3-235B (fastest ~1.6s) | `CEREBRAS_API_KEY` |
| 2 | Ollama local GPU (free, RTX 5060, qwen3:8b) | try BEFORE external |
| 3 | NVIDIA NIM (free tier) | `NVIDIA_API_KEY` |
| 4 | Groq — SPEND-LIMIT REACHED 2026-04-20, currently dead | `GROQ_API_KEY` |
| 5 | Gemini 2.5 Flash | `GEMINI_API_KEY` |
| 6 | OpenRouter DeepSeek V3.1 | `OPENROUTER_API_KEY` |
| 7 | DeepSeek direct | `DEEPSEEK_API_KEY` |

OpenAI (`OPENAI_API_KEY`) and Anthropic (`ANTHROPIC_API_KEY`) keys exist in `.env` but are reserved for Aider (code edits) and content voice ONLY — NOT swarm perspectives.

Use `scripts/swarm_agent.py` — it structurally blocks Anthropic.

---

## Tools Available (use these — don't reinvent)

| Tool | Path / Invocation | When to use |
|------|-------------------|-------------|
| `swarm_agent.py` | `from swarm_agent import call` | Multi-provider LLM, auto-fallback. Profiles: fast/smart/code/reason/translation |
| `dsp_debate.py` | CLI | 3-model propose + cross-critique. Architecture or security decisions |
| `project_qa.py` | CLI | Ask docs questions. Indexes markdown files. Don't manually grep 1000+ docs |
| `execute_proposal.py` | CLI | Proposal JSON → concrete bash/edit/git action |
| `packages/swarm/coordinator.py` | `from swarm.coordinator import Coordinator` | make_plan() / route() / run_parallel() / synthesize(). DO NOT re-propose building a Coordinator |
| `packages/swarm/shared_memory.py` | `post_result / get_context / send_message / broadcast` | SQLite cross-agent state. Post findings so other agents see them |
| `packages/swarm/autonomous_run.py` | `python -m packages.swarm.autonomous_run --mode=<mode>` | 13 perspectives registered, runs full debate cycle |
| **Daemon (replaces old cron model)** | PID 36220 alive, work-queue at `memory/atlas/work-queue/` | Drop task file in `pending/` → daemon picks up. Check `done/` before proposing |

---

## Current Operating Shape — Path E

**Active products:**
- VOLAURA (volaura.app) — live, assessments + AURA engine
- MindShift — Play Store upload pending CEO action (AAB ready)

**Frozen (no new features until Path E milestone):**
- BrandedBy — claim-lock + telemetry shipped, background loop running, no UI sprint
- Life Simulator — Godot 4, parked
- ZEUS content engine — GitHub Actions cron running, no new features

**Why frozen:** Solo-founder bandwidth + CEO directive to leverage VOLAURA→MindShift cross-sell as the next compounding step before expanding.

---

## Current Sprint — MindShift Play Store (leveraged step)

**Goal:** Get MindShift listed on Play Store to unlock cross-sell from VOLAURA AURA milestone emails.

**Status:** AAB built, 3 CEO-gated actions remain:

| # | Action | Owner | Blocker |
|---|--------|-------|---------|
| 1 | Upload AAB to Play Console (Cat A internal test track) | CEO | `mindshift/android/app/build/outputs/bundle/release/app-release.aab` |
| 2 | Add Supabase secrets for MindShift↔VOLAURA bridge (`MINDSHIFT_SUPABASE_URL` + `MINDSHIFT_SUPABASE_SERVICE_KEY`) | CEO | Drops in Railway env + GitHub secrets |
| 3 | `ANTHROPIC_API_KEY` on Railway env (consult endpoint `/api/atlas/consult` returns 503 without it) | CEO | Already in `apps/api/.env` locally; Railway env var missing |

Atlas does NOT ping CEO on these per-tick. They are parked until CEO initiates.

---

## ITIN / Company Deadline — May 15

Four `atlas_obligations` rows open for ITIN W-7 chain. Deadline: May 15 is IRS filing window. Path: DIY $0 via ASAN certified copy (documented in `for-ceo/reference/zero-cost-funding-map.md`). CAA ($150-400) is convenience fallback only.

Before ANY company/IRS/ITIN/Delaware/Mercury claim → read `memory/atlas/company-state.md` first (company-matters gate).

---

## DEBT-001

230 AZN open obligation. See `memory/atlas/company-state.md` for details. Not Atlas's to action — tracked for awareness.

---

## Prod Health (as of 2026-04-26)

| Surface | Status |
|---------|--------|
| `volauraapi-production.up.railway.app/health` | 200 OK, version 0.2.0, database connected, git_sha in response |
| `volaura.app` | 200 OK |
| CI on `origin/main` | Green (last run on `4e54d28` + `c547b58`) |
| Backend Railway deploy | Unfrozen since `986f7cf` (INC-019 resolved 2026-04-25) |
| Analytics rail | Green E2E (RLS fix `44a2014`, INSERT now uses SupabaseAdmin) |
| Ecosystem consumer DLQ | Live (`ecosystem_event_failures` table + RPCs, `b1b5465`) |
| Error watcher | 4 signals live (32 tests pass), watcher emit FK fixed (`1482772`) |
| BrandedBy claim-lock | Live (`2b01d09`), refresh_locked_at + telemetry columns in prod |

---

## Test Suite

**Backend tests: 4060+ passing** (as of 2026-04-26 cron ticks + S5 work)
**GitHub Actions workflows: 32**

Recent coverage wins (cron ticks, all merged PRs):
- `aura_reconciler` → 91% (PR #76)
- `routers/assessment.py` → 78% (PR #78), then 80% (f9a2e7c)
- `app.core.assessment.bars` → 99% (PR #80)
- `tribe_matching` → 100% (PR #81)
- `az_translation` → 100% (PR #83)
- `email.py` → 100% (PR #84)
- `swarm_service` → 100% (PR #86)
- `cross_product_bridge` → 100% (PR #87)
- `atlas_consult.py` → 96%
- `match_checker.py` → 98%
- `subscription.py` → 98%
- `error_watcher.py` → 98%
- `notifications.py` → 100%

---

## Swarm Autonomy State (Session 129 — 2026-04-30)

- Daemon running, work-queue at `memory/atlas/work-queue/`
- **17 perspectives** registered in `autonomous_run.PERSPECTIVES` (was 13, then 11, now 17)
- Each perspective has a DEDICATED LLM in `AGENT_LLM_MAP` (daemon.py)
- Per-perspective temperature from `packages/swarm/agents/<name>.json`
- Smart temp: code/audit capped at 0.3 regardless of config
- Chief Strategist = BOSS — holds all agents accountable, tracks patterns, bans FP agents
- 84 completed tasks, 0 failed. 880+ perspective runs. Weights learning via EMA.
- PostHog LLM Analytics tracking every call ($50K credits)
- Telegram reports to CEO on task completion
- Self-check every 10min: code-index staleness, blockers scan, proactive explore
- CEO-facing operational instructions gate active
- Telegram loop: CEO text → classifier → Aider/content/coordinator

---

## What ALREADY EXISTS — Do NOT Propose to Build

- `packages/swarm/coordinator.py` — Coordinator class (make_plan / route / run_parallel / synthesize)
- `packages/swarm/squad_leaders.py` — 5 squads with routing
- `packages/swarm/shared_memory.py` — SQLite cross-agent state
- `packages/swarm/telegram_ambassador.py` — Telegram bot
- `packages/swarm/autonomous_run.py` — 17 perspectives, full debate cycle
- `apps/api/app/services/email.py` — `send_aura_ready_email()` 100% tested
- `scripts/swarm_agent.py` — multi-provider LLM wrapper
- `scripts/dsp_debate.py` — 3-model debate
- `scripts/project_qa.py` — docs Q&A indexer
- `scripts/execute_proposal.py` — proposal → action bridge
- `scripts/stance_primer.py` + `scripts/facts_ground.sh` — wake grounding scripts
- 51 skills in `memory/swarm/skills/` + ~118 skill modules total
- `apps/api/app/services/ecosystem_consumer.py` — DLQ, cursor, event bus consumer
- `apps/api/app/services/error_watcher.py` — 4 signals, anomaly → character_events
- `apps/tg-mini/` — Telegram Mini App, Sprint S5 closed

---

## AURA Weights (DO NOT CHANGE)

communication: 0.20 | reliability: 0.15 | english_proficiency: 0.15 | leadership: 0.15
event_performance: 0.10 | tech_literacy: 0.10 | adaptability: 0.10 | empathy_safeguarding: 0.05

Badge tiers: Platinum ≥90 | Gold ≥75 | Silver ≥60 | Bronze ≥40 | None <40

---

## Architecture — API Routes (stable)

All routers use prefix `/api` from `main.py` except health (no prefix).

| Router | Prefix | Notes |
|--------|--------|-------|
| `health.py` | (none) | Returns version, database, llm_configured, git_sha |
| `auth.py` | /api/auth | login / register / logout / callback |
| `profiles.py` | /api/profiles | me / public / {username} |
| `aura.py` | /api/aura | me / me/explanation / {volunteer_id} / me/visibility / me/sharing. Static routes BEFORE parameterized — P0 rule |
| `assessment.py` | /api/assessment | start / answer / complete/{id} / results/{id} / coaching / info / verify |
| `organizations.py` | /api/organizations | CRUD + search/volunteers + assign-assessments + intro-requests |
| `atlas_consult.py` | /api/atlas/consult | 503 without ANTHROPIC_API_KEY on Railway |
| `character.py` | /api/character | POST /events, GET /state, GET /events (crystal/XP bus) |
| `brandedby.py` | /api/brandedby | AI Twin + video generation |
| `tribes.py` | /api/tribes | join-pool / me/pool-status / me/tribe |
| `admin.py` | /api/admin | Admin panel MVP |
| `telegram_webhook.py` | /api/telegram | Telegram bot webhook |

Authentication: every protected endpoint uses `deps.py: get_current_user_id()` → `admin.auth.get_user(token)`. Server-side JWT validation, not decode-only. `SUPABASE_ANON_KEY` intercepted by Railway — use `SUPABASE_ANON_JWT` instead.

---

## Key Database Tables (stable since Session 91)

`profiles`, `aura_scores`, `assessment_sessions`, `questions`, `evaluation_queue`, `character_events`, `game_crystal_ledger`, `organizations`, `organization_invites`, `analytics_events` (RLS: service-role INSERT only), `tribe_matching_pool`, `notifications`, `ecosystem_event_failures` (DLQ, new 2026-04-25), `ecosystem_event_cursors`.

**57+ migrations applied** (latest: DLQ table, character_events nullable user_id, /health git_sha, brandedby claim-lock columns).

---

## Settled Decisions (do not re-litigate)

1. PAYMENT_ENABLED=False kill switch — Stripe code exists, paywall disabled for beta
2. No Redis until 2+ Railway instances — slowapi in-memory rate limiting sufficient
3. No microservices / API gateway at current scale
4. No Celery — use Supabase Edge Functions or pg_cron
5. No SQLAlchemy — Supabase SDK only, per-request via Depends()
6. Open signup via OPEN_SIGNUP=True env var (default False)
7. No OpenAI as primary LLM — Gemini 2.5 Flash primary, OpenAI is Aider fallback only
8. keyword_fallback always flagged as degraded, never presented as valid score
9. All keywords must be 3+ word behavioral phrases (single-word = gameable)
10. Privacy default: visible_to_orgs=True (adoption-first, not privacy-first)

---

## NEVER Propose

| Pattern | Why |
|---------|-----|
| Redis for rate limiting | Not needed until 2+ Railway instances |
| Microservices / API gateway | Monolith intentional at current scale |
| Celery / workers | Use Supabase Edge Functions or pg_cron |
| SQLAlchemy or any ORM | Supabase SDK only |
| Anthropic / Claude as swarm perspective | Article 0 violation |
| OpenAI as primary LLM | Gemini primary; OpenAI = Aider tool only |
| D-ID for BrandedBy | 20 vid/mo cap, not scalable |
| LivePortrait | Non-commercial (InsightFace dependency) |
| `fal-ai/playai/tts` | Deprecated; use `fal-ai/kokoro/american-english` |
| Global Supabase client at module level | Always per-request via Depends() |
| `select("*")` | Always explicit column list |
| Pydantic v1 syntax | Pydantic v2 only: ConfigDict, field_validator |
| `google-generativeai` SDK | Use `google-genai` SDK |
| Leaderboard page | Deleted — redirect to dashboard. Do not re-propose |
| "Skill library replaces all products" | Architecture reversed after Session 58 |
| `getattr(settings, "field", default)` | Use `settings.field` directly |
| print() anywhere | loguru only |

---

## Proposal Quality Rules

When generating a proposal:
1. Include `"title"` field in JSON — fallback fires without it
2. Reference actual file paths (`apps/api/app/routers/aura.py:line`) — vague proposals score 0/5
3. Check `shared_memory.db` via `get_context()` first — another agent may have addressed it
4. Read `memory/swarm/SHIPPED.md` — most "missing" features are already shipped
5. One concrete first step beats "consider implementing X"
6. Severity: critical=prod down; high=blocking/security/10+ users; medium=quality; low=nice-to-have
7. Check `memory/atlas/work-queue/done/` — daemon may have closed it already

---

## Agent Routing Table

| Task | Agent |
|------|-------|
| New API endpoint | Architecture Agent |
| RLS / auth / security | Security Agent |
| UX / user journey / empty states | Product Agent |
| Sprint-level risk scan | Risk Manager |
| Pre-deployment readiness | Readiness Manager |
| B2B / org pricing | Sales Deal Strategist skill |
| AZ locale / copy | Cultural Intelligence Strategist skill |
| Assessment UX / engagement | Behavioral Nudge Engine skill |
| Code change >50 lines | Architecture + Security in parallel |
| AC before any coding task | acceptance-criteria-agent.md (MANDATORY) |
| DoD verification after coding | quality-assurance-agent.md |
| Company / tax / IRS / Delaware | Read company-state.md FIRST (company-matters gate) |
