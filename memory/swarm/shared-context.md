<!-- RECENTLY_SHIPPED_START -->
## ⚡ RECENTLY SHIPPED (last push — 2026-04-18 20:59 UTC)
**Read this FIRST — prevents proposing already-shipped work.**
New/updated routers: telegram_webhook
<!-- RECENTLY_SHIPPED_END -->

# Swarm Shared Context — UPDATED 2026-04-07 (Session 91)

**By:** CTO (Claude) | **Updated:** 2026-04-07 (Session 91 — SWARM ALIVE end-to-end, 5 critical bugs fixed, Telegram bot live)

---

## 🔒 SECURITY UPDATE — READ THIS FIRST (overrides any older info below)

### Status: SWARM ALIVE END-TO-END WITH ENHANCED SECURITY

- `packages/swarm/autonomous_run.py` runs successfully (was dormant 2 weeks). 9 agents parallel.
- Telegram bot `@volaurabot` running as long-polling listener (PID alive). Commands: /status /proposals /run /approve /dismiss + free text → Gemini/Groq.
- GitHub Actions `swarm-daily.yml` cron last run = SUCCESS at 06:12 UTC.
- shared_memory.db has 21 entries. Memory consolidation cycle works.

### Tools You Now Have (use these instead of guessing)

| Tool | Path | When to use |
|------|------|------------|
| `scripts/swarm_agent.py` | `from swarm_agent import call` | Call multi-provider LLM with auto-fallback. NEVER call Anthropic directly. Profiles: fast/smart/code/reason/translation. |
| `scripts/dsp_debate.py` | CLI | 3 models propose + cross-critique. Use for architecture or security decisions. |
| `scripts/project_qa.py` | CLI | Ask docs questions. 384 markdown files indexed. Don't re-read 504 docs manually. |
| `scripts/execute_proposal.py` | CLI | **Bridge from agent proposal → concrete action**. Reads proposals.json, asks LLM for one specific bash/edit/git/read action. Use this to actually IMPLEMENT proposals, not just generate them. |
| `packages/swarm/coordinator.py` | `from swarm.coordinator import Coordinator` | Already exists since Session 88. make_plan() / route() / run_parallel() / synthesize(). DO NOT propose to "build a Coordinator". |
| `packages/swarm/shared_memory.py` | post_result/get_context/send_message/broadcast | SQLite-backed cross-agent state. Post your findings here so other agents see them. |
| `packages/swarm/telegram_ambassador.py` | `python -m packages.swarm.telegram_ambassador` | Long-polling Telegram bot. Already running. |

### Constitution Article 0 (HARD RULE)

**NEVER use Anthropic models in swarm.** Provider hierarchy:
1. Cerebras Qwen3-235B / Llama 3.3 8B (fastest, ~1.6s) — `CEREBRAS_API_KEY`
2. Ollama local GPU (free, RTX 5060 + qwen3:8b) — try BEFORE external APIs
3. NVIDIA NIM (free tier) — `NVIDIA_API_KEY`
4. Groq Kimi K2 / Llama 3.3 70B — `GROQ_API_KEY`
5. Gemini 2.5 Flash — `GEMINI_API_KEY`
6. OpenRouter DeepSeek V3.1 — `OPENROUTER_API_KEY`

If you find yourself about to call Anthropic Haiku or Claude Sonnet for swarm work, STOP. Use `scripts/swarm_agent.py` which structurally blocks Anthropic.

### 5 Critical Bugs FIXED in Session 91

1. **`autonomous_run.py:758`** "Untitled proposal" fallback → now derives title from content first line.
2. **`squad_leaders.py`** QUALITY squad missing security/audit/vulnerability/cve/rls/auth/blocker/p0/p1 keywords. Security proposals went unrouted. FIXED — added to QUALITY squad along with `security-auditor` agent member.
3. **`suggestion_engine.py:283`** `asyncio.run()` nested inside running event loop → crash. FIXED with ThreadPoolExecutor + new event loop.
4. **`telegram_ambassador.py:354`** wrapped sync `Application.run_polling()` in `asyncio.run()` → crash. FIXED — `run_bot()` now sync.
5. **`scripts/execute_proposal.py`** import path bug. FIXED — `swarm_agent.py` copied to main repo `scripts/`.

### What ALREADY EXISTS (do NOT propose to build):

- ✅ `packages/swarm/coordinator.py` — full Coordinator class
- ✅ `packages/swarm/squad_leaders.py` — 5 squads with routing
- ✅ `packages/swarm/shared_memory.py` — SQLite shared state
- ✅ `packages/swarm/telegram_ambassador.py` — Telegram bot with /status /proposals /run /approve /dismiss
- ✅ `apps/api/app/services/email.py` — 173 lines, `send_aura_ready_email()` works
- ✅ `scripts/swarm_agent.py` — multi-provider LLM wrapper
- ✅ `scripts/dsp_debate.py` — 3-model debate pattern
- ✅ `scripts/project_qa.py` — per-project Q&A indexer
- ✅ `scripts/execute_proposal.py` — proposal → action bridge (PoC working)
- ✅ `scripts/load_test.js` — k6 production load test
- ✅ `apps/tg-mini/` — Telegram Mini App (NOT yet deployed to Vercel)
- ✅ `jarvis_daemon.py:478` `_create_mindshift_task` — VOLAURA ↔ MindShift bidirectional bridge
- ✅ 51 skills in `memory/swarm/skills/` (categorized)
- ✅ 13 perspectives in PERSPECTIVES array + ~118 skill modules total
- ✅ Coordinator-agent skill at `memory/swarm/skills/coordinator-agent.md`

### Knowledge Transfer For Agents Working On Proposals

When you generate a proposal:
1. **Always include a "title" field** in your JSON output. Don't omit it — fallback fires.
2. **Reference actual file paths**: `apps/api/app/routers/aura.py:line` — vague proposals score 0/5 on specificity.
3. **Check shared_memory.db first** via `get_context()` — another agent may have already addressed this.
4. **Read `memory/swarm/SHIPPED.md`** before proposing — 90% of "missing" features are already shipped.
5. **One concrete first step** beats "consider implementing X". The execute_proposal.py pipeline rejects vague proposals.
6. **Severity meaning**:
   - critical = production down, user can't complete core flow
   - high = blocking new development, security CVE, or 10+ users affected
   - medium = improves quality of life
   - low = nice-to-have

### Telegram Bot Commands (Test These)

CEO can send to @volaurabot:
- `/status` — current swarm state + pending proposals count
- `/proposals` — list pending proposals with details
- `/run` — trigger swarm run (~30s)
- `/approve <id>` — approve proposal
- `/dismiss <id>` — dismiss proposal
- Free text → Gemini/Groq answers with conversation context

If bot doesn't respond: process may have crashed. Restart with:
```
PYTHONIOENCODING=utf-8 python3 -m packages.swarm.telegram_ambassador
```

---

## ⚠️ ZERO: Read ECOSYSTEM-MAP.md FIRST

Full ecosystem map with all 5 products, Constitution laws, what NOT to propose:
`packages/swarm/memory/ECOSYSTEM-MAP.md`

The **ECOSYSTEM CONSTITUTION v1.7** governs everything:
`docs/ECOSYSTEM-CONSTITUTION.md` (branch `claude/blissful-lichterman`)

---

## ⚠️ CRITICAL: Read this before proposing anything

1. The "skill library replaces all products" architecture (Sessions 51-58) was REVERSED. Volaura, MindShift, Life Simulator, BrandedBy, ZEUS are separate products. Do NOT propose features as "skills within Volaura."
2. Sprint state is Design System + UX Polish (2026-04-06). Session 87 is most recent. PRs #7, #8 merged today.
3. **G9 FIXED:** Leaderboard page deleted today — redirect to dashboard. Do not re-propose leaderboard.
4. **G15 FIXED:** Score counter durations 800ms max. Do not propose duration > 800ms.
5. **G21 + Crystal Law 6 FIXED:** Badge/crystals removed from assessment complete page.
3. 57+ migrations are applied. Do NOT re-propose already-fixed bugs.
4. PAYMENT_ENABLED=False kill switch is active. Stripe code exists but paywall is disabled for beta.
5. Route ordering in aura.py is intentional — static routes before parameterized (P0 bug fixed Sprint 42).
6. **ECOSYSTEM RULE:** Every proposal must consider cross-product impact. Volaura events → character_events → Life Simulator crystals. Never propose Volaura features in isolation.

---

## 🌍 ECOSYSTEM — 5 Products, 1 User

This is NOT a single product. Every agent must know all 5 and their integration points.

### Product Map

| Product | Status | What it does | Key tech |
|---------|--------|-------------|----------|
| **VOLAURA** | ✅ Live (volaura.app) | Verified talent platform. Assessment → AURA score → badges. Orgs search talent. | Next.js + FastAPI + Supabase |
| **ZEUS** | ✅ Running (GitHub Actions) | Autonomous content engine. Generates + publishes content to Telegram channels every 4h. Also: video generation via FAL/SadTalker. | `packages/swarm/zeus_content_run.py`, `zeus_video_skill.py` |
| **MindShift** | ✅ 92% built | Daily habits: focus sessions, streaks, psychotype tracking. Separate Supabase project (`awfoqycoltvhamtrsvxk`). | Separate repo |
| **Life Simulator** | 🔄 65% built | Godot 4 game. User has a character with stats/crystals/progression. VOLAURA assessments → crystal_earned events → visible in game. | Godot 4 + character_events bus |
| **BrandedBy** | 🔄 15% built | AI Twin: portrait + script → Kokoro TTS → SadTalker → MP4. Professional video presence. | FAL API + `zeus_video_skill.py` |

### Cross-Product Event Bus

All products write to `character_events` table (Supabase):
```sql
character_events: id, user_id, event_type, source_product, payload JSONB
game_crystal_ledger: id, user_id, amount, source, reference_id, created_at
```

**VOLAURA → Life Simulator flow:**
```
User completes assessment → AURA score calculated
→ emit crystal_earned + skill_verified to character_events
→ Life Simulator reads events → character gains crystals/XP
```

**ZEUS triggers:**
```
character_events INSERT (skill_verified, milestone_reached)
→ Supabase webhook → FastAPI /telegram/webhook
→ zeus_content_run.py generates content
→ Posts to Telegram channels (Volaura Community, BrandedBy, etc.)
```

### ZEUS — What It Does Today

- **Runs:** Every 4 hours via `.github/workflows/zeus-content.yml`
- **Channels:** Volaura Community Telegram, BrandedBy Telegram, MindShift Telegram
- **Content:** Skill tips, AURA milestones, motivational posts, product updates
- **Event-driven:** Fires on `skill_verified` + `milestone_reached` events
- **Video:** `zeus_video_skill.py` → portrait + script → FAL (MuseTalk/Kling) → MP4
- **Status:** Running. Last 5 GitHub Actions runs = SUCCESS

### What ZEUS Needs (Swarm Requested)

- **Orchestrator** — ZEUS currently runs as cron, not as always-on daemon
- **Railway worker** — planned: always-on process instead of GitHub Actions cron
- **Self-upgrade** — BLOCKED: needs staging branch + test gate (security review done, CVSS 8.1)
- **Code-aware agents** — agents currently BLIND to actual code files

---

---

## Current Sprint Goal

**Session 83, BATCH-U (executing 2026-04-02)**

- U1: shared-context.md refresh — THIS TASK
- U2: Transactional email skeleton with `email_enabled` kill switch (Resend API) — CEO sets RESEND_API_KEY when ready
- U3: Demo volunteer seed migration — visible profile for org cold search visits

**CEO actions required (blocking Phase 0):**
- Walk volaura.app E2E with real email (Phase 0 gate — nothing else unblocks until done)
- Apply pending DB migrations via Supabase Dashboard or `supabase db push`
- Set RESEND_API_KEY on Railway when Resend account is created
- Set `OPEN_SIGNUP=true` on Railway when ready to open beta (currently closed by default)
- Set GitHub secrets: SUPABASE_PROJECT_ID + SUPABASE_SERVICE_KEY (for analytics-retention workflow)

---

## What Was Built (Sessions 83 — most recent, 2026-04-02)

| BATCH | Code | What it does |
|-------|------|-------------|
| BATCH-T | `test_tribes.py` mock fix | tribe_matching_pool AsyncMock — fixes join-pool test TypeError |
| BATCH-S | `answer_submitted` event | Frontend assessment page fires on every answer (useTrackEvent) |
| BATCH-S | `assessment_completed_view` event | Completion page fires on fetchResults success |
| BATCH-S | Telegram webhook hard-fail | TELEGRAM_WEBHOOK_SECRET missing → RuntimeError in production startup |
| BATCH-R | `open_signup` default → False | Was True; now closed by default, Railway must set OPEN_SIGNUP=true |
| BATCH-R | LLM cap fail-closed | Exception during cap check → _force_degraded=True (was fail-open) |
| BATCH-R | 409 resume flow | Assessment start 409 → reads session_id → redirects to existing session |
| BATCH-R | Org routing fix | accountType===organization → /my-organization (was routing to /assessment) |
| BATCH-R | 500-HOUR-PLAN.md | 8-phase plan, Phase 0 gates all. CEO vs CTO ownership separated. |

**Test count (2026-04-02):** 742 passing, 1 pre-existing failure (test_match_checker.py::test_no_matches_updates_last_checked)

---

## What Was Built (Session 82 — 2026-04-02)

| Code | Location | What it does |
|------|----------|-------------|
| Remove dead Subscribe CTA | `apps/web/.../dashboard/page.tsx` | Replaced broken button with "coming soon" text |
| AuraExplanationResponse schema | `apps/api/app/schemas/aura.py`, `routers/aura.py` | Typed response for /aura/me/explanation |
| Share flow UTM + null username guard | `routers/assessment.py`, `share-buttons.tsx` | UTM params on share URL; null username blocked |
| Onboarding competency redirect | `apps/web/.../onboarding/page.tsx` | ?competency= param passed to assessment page |
| Org GET endpoints require auth | `routers/organizations.py` | GET /organizations + /{org_id} now need JWT |
| upsert_aura_score error handling | `routers/assessment.py` | try/except + pending_aura_sync=True on failure |
| /aura/{id} rate limit → 10/min | `routers/aura.py` | Was 60/min; enumeration mitigation |
| /health uses Depends() | `routers/health.py` | Replaced inline acreate_client() |
| Dashboard share prompt | `apps/web/.../dashboard/page.tsx` | One-time dismissible banner post first AURA |
| Per-user daily LLM cap | `bars.py`, `routers/assessment.py` | 20 open-ended LLM calls/user/day; prevents budget drain |
| keyword_fallback spike alert | `bars.py` | Hourly counter; Telegram alert at 10th fallback |
| SENTRY_DSN warning at startup | `config.py` | validate_production_settings() warns if empty |

**Previous batch highlights (BATCH J–I, also 2026-03-30):**
- `docs/AGENT-BRIEFING-TEMPLATE.md` created — canonical VOLAURA CONTEXT BLOCK for agent prompts
- BUG-012 CLOSED: `has_pending_evaluations` + `pending_reeval_count` added to /aura/me/explanation
- PAYMENT_ENABLED kill switch in config.py (default False — beta users assess freely)
- Risk Manager + Readiness Manager added to autonomous_run.py PERSPECTIVES

---

## Architecture (accurate as of 2026-03-30)

### API Routes (complete list with prefixes)

All routers use prefix `/api` from main.py except health (no prefix).

| Router file | Prefix | Key routes |
|-------------|--------|-----------|
| `health.py` | (none) | GET /health |
| `auth.py` | /api/auth | POST /login, /register, /logout, /callback |
| `profiles.py` | /api/profiles | GET/POST/PUT /me, GET /public, GET/POST /{username} |
| `aura.py` | /api/aura | GET /me, GET /me/explanation, GET /{volunteer_id}, GET+PATCH /me/visibility, POST /me/sharing |
| `assessment.py` | /api/assessment | POST /start, POST /answer, POST /complete/{id}, GET /results/{id}, POST /{id}/coaching, GET /info/{slug}, GET /results/{id}/questions, GET /verify/{session_id} (public, no auth) |
| `events.py` | /api/events | CRUD for events |
| `organizations.py` | /api/organizations | GET+POST "", GET/PUT /me, GET /{id}, GET /me/dashboard, GET /me/volunteers, POST /search/volunteers, POST /assign-assessments, POST /intro-requests |
| `invites.py` | /api/organizations | (shares prefix) org invite endpoints |
| `badges.py` | /api/badges | Badge endpoints |
| `verification.py` | /api/verify | Email verification flow |
| `activity.py` | /api/activity | Activity log |
| `discovery.py` | /api/volunteers | GET /discovery (org talent search) |
| `leaderboard.py` | /api/leaderboard | GET leaderboard (uses aura_scores_public view) |
| `notifications.py` | /api/notifications | User notifications |
| `stats.py` | /api/stats | Platform stats (uses avg_aura_score RPC) |
| `telegram_webhook.py` | /api/telegram | Telegram bot webhook |
| `character.py` | /api/character | POST /events, GET /state, GET /events (crystal/XP bus) |
| `brandedby.py` | /api/brandedby | AI Twin + video generation |
| `skills.py` | /api/skills | Skills endpoints |
| `subscription.py` | /api/subscription | GET /status, POST /create-checkout, POST /webhook |
| `tribes.py` | /api/tribes | POST /join-pool, GET /me/pool-status, GET /me/tribe, cron endpoints. Added 2026-04-02. |
| `admin.py` | /api/admin | Admin panel MVP. Added 2026-04-02. |

**Services (non-router):**
| `analytics.py` | `app/services/analytics.py` | `track_event()` fire-and-forget. Never raises. Added 2026-04-02. |
| `tribe_matching.py` | `app/services/tribe_matching.py` | Greedy tribe matching algorithm. Daily cron. |
| `tribe_streak_tracker.py` | `app/services/tribe_streak_tracker.py` | Weekly streak tracking. |

**CRITICAL route order rule (aura.py):** Static routes MUST precede parameterized:
```
GET /me           # FIRST
GET /me/explanation  # SECOND
GET /{volunteer_id}  # LAST (wildcard)
```

### Key Database Tables

| Table | Key columns | Notes |
|-------|-------------|-------|
| `profiles` | id, account_type, visible_to_orgs (default true), subscription_status, trial_ends_at, registration_number, invited_by_org_id | id = auth.users.id |
| `aura_scores` | volunteer_id, total_score, badge_tier, competency_scores JSONB, visibility, percentile_rank, last_updated | Use aura_scores_public view in queries (security_barrier=TRUE) |
| `assessment_sessions` | id, volunteer_id, competency_id, status (in_progress/completed), theta_estimate, theta_se, answers JSONB, question_delivered_at, answer_version, pending_aura_sync | 30-min cooldown on start |
| `questions` | id, competency_id, type (mcq/open_ended), scenario_en, scenario_az, options JSONB, expected_concepts JSONB, irt_a/b/c | keywords MUST be 3+ word behavioral phrases |
| `evaluation_queue` | session_id, degraded_score, status (pending/processing/done/failed) | keyword_fallback answers queued for LLM re-eval |
| `character_events` | id, user_id, event_type, source_product, payload JSONB | Cross-product event bus |
| `game_crystal_ledger` | id, user_id, amount, source, reference_id, created_at | NOT `delta`, NOT `reason` — use these exact column names |
| `organizations` | id, owner_id, name, org_type, registration_number | owner_id UNIQUE constraint prevents duplicate orgs |
| `organization_invites` | id, org_id, email, invite_code, status | invited_by_org_id on profiles tracks attribution |
| `stripe_webhook_events` | id, stripe_event_id, event_type, processed_at | Idempotency table for Stripe webhooks |
| `analytics_events` | id, user_id FK, session_id FK, event_name, properties JSONB, locale, platform, created_at | Behavioral events. RLS: SELECT own, INSERT service-role only. GDPR 390-day retention via GitHub Actions. Added 2026-04-02. |
| `tribe_matching_pool` | user_id PK, joined_at | Persistent pool membership. RLS: user SELECT+INSERT+DELETE own. Added 2026-04-02. |
| `notifications` | id, user_id, type, title, body, is_read, reference_id, created_at | In supabase_realtime publication. RLS verified clean. |

**59+ migration files applied** as of 2026-04-02. Latest: `analytics_events`, `fix_security_definer_views`, `fix_search_path_and_ceo_inbox`.

### Assessment Pipeline

```
POST /api/assessment/start
  → paywall check (if subscription_status in expired/cancelled → 402)
     ONLY when PAYMENT_ENABLED=True (default False)
  → rapid-restart cooldown check (30 min since last session start)
  → create assessment_sessions row
  → fetch questions for competency (5-min TTL cache)
  → return first question via IRT/CAT engine

POST /api/assessment/answer
  → answer_version optimistic lock (409 on concurrent submit)
  → question_delivered_at future-timestamp tamper detection
  → prompt injection detection (10 regex patterns on open-ended)
  → per-user daily LLM cap (20 open-ended/day; over cap → keyword_fallback + reeval queue)
  → evaluate_answer() in bars.py:
       Gemini 2.5 Flash (DeCE: {score, quote, confidence} per concept)
       → Groq llama-3.3-70b (free: 14,400 req/day)
       → OpenAI gpt-4o-mini
       → keyword_fallback (degraded mode → enqueue for async re-eval)
  → update theta via EAP (3PL model)
  → stopping: SE ≤ 0.3 OR 20 questions max OR no items left

POST /api/assessment/complete/{session_id}
  → early return if already completed (prevents double aura_history)
  → upsert_aura_score RPC (try/except: on failure sets pending_aura_sync=True)
  → emit crystal_earned + skill_verified to character_events
```

**Anti-gaming gates (multiplicative):**
1. min_length < 30 words → cap 0.4
2. stuffing_detection (>60% keywords in <50 words) → 0.3×
3. coherence_heuristic (verb_count/keyword_hits < 0.4) → 0.55×
4. scenario_relevance (token overlap < 15%) → 0.65×

### Authentication

```
Every protected endpoint:
  Authorization: Bearer <supabase_jwt>
  ↓
deps.py: get_current_user_id()
  → admin.auth.get_user(token)  ← server-side validation (NOT anon-key decode)
  → returns user UUID (str)

Type aliases (use these in router signatures):
  SupabaseAdmin   = Annotated[AsyncClient, Depends(get_supabase_admin)]
  SupabaseUser    = Annotated[AsyncClient, Depends(get_supabase_user)]
  SupabaseAnon    = Annotated[AsyncClient, Depends(get_supabase_anon)]
  CurrentUserId   = Annotated[str, Depends(get_current_user_id)]

SUPABASE_ANON_KEY intercepted by Railway — use SUPABASE_ANON_JWT instead.
Hardcoded fallback in config.py is intentional (public anon key).
```

### Rate Limits

| Constant | Value | Used on |
|----------|-------|---------|
| RATE_AUTH | 5/minute | Login, register |
| RATE_ASSESSMENT_START | 3/hour | POST /assessment/start |
| RATE_ASSESSMENT_ANSWER | 60/hour | POST /assessment/answer |
| RATE_ASSESSMENT_COMPLETE | 10/hour | POST /assessment/complete |
| RATE_LLM | 30/hour | LLM-heavy endpoints |
| RATE_DEFAULT | 60/minute | General endpoints |
| RATE_DISCOVERY | 10/minute | /volunteers/discovery, /aura/{id} (enumeration mitigation) |

Rate limiter: slowapi in-memory (single Railway instance). Migrate to Redis or Supabase Edge Functions when 2+ instances.

---

## Open Bugs (do not re-fix without checking)

| ID | Issue | Status |
|----|-------|--------|
| BUG-005 | list_org_volunteers OOM — complex join | Deferred post-beta |
| BUG-011 | fire-and-forget notification failure | Architectural, documented |
| BUG-016 | JWT revocation (logout doesn't invalidate active sessions immediately) | Sprint 6 |
| BUG-018/019/020 | Scale issues under load | Post-beta |
| GROWTH-2 | invite→profile attribution (invited_by_org_id column added but funnel not complete) | verify |
| GROWTH-3/9/10/11 | Analytics system | Post-beta |
| SEC-030 | rating CHECK constraint (float not validated at DB level) | BATCH L |
| QA-03 | Org B2B test coverage (org dashboard + search) | BATCH L |
| SEC-03 | display_name anonymization consistency | BATCH L |

---

## NEVER Propose (rejected patterns)

| Pattern | Why rejected |
|---------|-------------|
| Redis for rate limiting | Not needed until 2+ Railway instances |
| Microservices / API gateway | Monolith intentional at current scale |
| Celery/workers | Use Supabase Edge Functions or pg_cron |
| SQLAlchemy / any ORM | Supabase SDK only |
| OpenAI as primary LLM | Gemini primary, OpenAI is last fallback |
| keyword_fallback as valid score | Vocabulary match ≠ competence; always flag as degraded |
| Single-word keywords in questions | Gameable (GRS < 0.4); all keywords must be 3+ word behavioral phrases |
| D-ID for BrandedBy video | ~20 vid/mo cap at $5.90 plan, not scalable |
| MuseTalk for portrait→video | Requires MP4 input, not still image |
| LivePortrait | Non-commercial (InsightFace dependency) |
| fal-ai/playai/tts | Deprecated; use fal-ai/kokoro/american-english |
| "Skill library replaces all products" | Architecture reversed after Session 58 |
| Privacy by default (visible_to_orgs=false) | Adoption-first: public by default |
| `getattr(settings, "field", default)` | Use `settings.field` directly |
| Global Supabase client at module level | Always per-request via Depends() |
| `select("*")` | Always use explicit column list |
| Pydantic v1 syntax (class Config, orm_mode) | Pydantic v2 only: ConfigDict, field_validator |
| `google-generativeai` SDK | Use `google-genai` SDK |

---

## Agent Routing Table

| Task | Best Agent(s) |
|------|--------------|
| New API endpoint | Architecture Agent |
| RLS policy, auth, security | Security Agent (Expert 9.0/10) |
| UX, user journey, empty states | Product Agent (100% accuracy) |
| Sprint-level risk scan | Risk Manager (new hire) |
| Pre-deployment readiness | Readiness Manager (new hire, LRR scoring) |
| B2B features, org pricing | Sales Deal Strategist skill |
| Any user-facing copy, AZ locale | Cultural Intelligence Strategist skill |
| Assessment UX, engagement | Behavioral Nudge Engine skill |
| Code change >50 lines | Architecture + Security in parallel |
| New data model | Architecture Agent |
| Meta/process improvement | Needs Agent |
| Writing AC before any coding task | acceptance-criteria-agent.md (MANDATORY — no task starts without AC) |
| Verifying DoD before marking done | quality-assurance-agent.md (15-item checklist, fires after every task) |
| DORA metrics after each batch | dora-metrics-agent.md (CFR, Lead Time, Deploy Freq — quality-metrics.md) |
| AI call tracing, cost visibility | langfuse-integration-agent.md (LiteLLM proxy, Andon visual management) |
| AI agent swarm orchestration (future) | CrewAI Flows — see docs/QUALITY-SYSTEM.md Section 6 |

**Pairing rule:** Risk Manager + Readiness Manager must both approve before any MEDIUM+ feature ships.
**Quality rule:** AC Agent runs BEFORE coding. QA Agent runs AFTER coding. DORA Agent runs AFTER deploy. Always.

---

## AURA Weights (DO NOT CHANGE)

communication: 0.20 | reliability: 0.15 | english_proficiency: 0.15 | leadership: 0.15
event_performance: 0.10 | tech_literacy: 0.10 | adaptability: 0.10 | empathy_safeguarding: 0.05

## Badge Tiers
Platinum ≥ 90 | Gold ≥ 75 | Silver ≥ 60 | Bronze ≥ 40 | None < 40

## Decay Half-Lives (per competency)
tech_literacy/event_performance: 730d | english_proficiency: 1095d
communication/reliability/adaptability: 1460d | leadership/empathy: 1640d | weighted avg: 1295d
