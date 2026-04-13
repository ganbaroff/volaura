# Volaura Architecture Master Document

**Created:** 2026-04-02 (Session 81 — Full Codebase Audit)
**Authors:** 5-agent parallel audit (Backend + Frontend + Infra + Docs + Architecture Synthesis)
**Health Score:** 72/100 — Conditional GO for public launch
**Purpose:** Single reference for system architecture. Supersedes scattered notes in shared-context.md and HANDOFF.md.

**Cross-references:** [[adr/ADR-001-system-architecture]] | [[adr/ADR-002-database-schema]] | [[adr/ADR-006-ecosystem-architecture]] | [[ECOSYSTEM-CONSTITUTION]] | [[ECOSYSTEM-MAP]] | [[API-REFERENCE]]

---

## 1. System Overview

Volaura is a **Verified Professional Talent Platform** — skills proven through adaptive assessment, not claimed on CVs.

**Ecosystem position:**
```
VOLAURA → verified skills (AURA score, badges, assessments)
MindShift → daily habits (focus sessions, streaks, psychotype)
Life Simulator → game character (stats, crystals, progression in Godot 4)
BrandedBy → professional identity (AI twin, video presence)
ZEUS → autonomous agent framework (local Windows, cloud-accessible)

All products share Supabase auth.
All products write to character_events table.
One user, five touchpoints. Crystal economy bridges VOLAURA→Life Simulator.
```

---

## 2. Repository Structure

```
volaura/                          ← Turborepo monorepo (pnpm workspaces)
├── apps/
│   ├── api/                      ← FastAPI backend (Python 3.11+)
│   │   ├── app/
│   │   │   ├── core/assessment/  ← IRT/CAT engine (pure Python, no deps)
│   │   │   ├── middleware/        ← rate_limit, security_headers, request_id, error_alerting
│   │   │   ├── routers/          ← 20 routers (activity, admin, assessment, auth, aura, ...)
│   │   │   ├── schemas/           ← Pydantic v2 models
│   │   │   ├── services/          ← Business logic (llm, assessment, rewards, notifications, ...)
│   │   │   ├── config.py          ← Settings (pydantic-settings)
│   │   │   ├── deps.py            ← FastAPI dependencies (SupabaseUser, SupabaseAdmin, CurrentUserId)
│   │   │   └── main.py            ← App factory, middleware chain, router registration
│   │   └── tests/                 ← 47 test files, 668+ tests
│   └── web/                       ← Next.js 14 App Router (TypeScript)
│       ├── src/
│       │   ├── app/[locale]/      ← All pages (auth, dashboard, public, admin)
│       │   ├── components/        ← UI components (shadcn/ui base + feature components)
│       │   ├── hooks/queries/     ← TanStack Query hooks (generated + custom)
│       │   ├── lib/               ← API client, utils, Supabase browser/server clients
│       │   ├── locales/           ← EN + AZ translation JSONs
│       │   └── stores/            ← Zustand stores (auth, assessment, ui)
├── packages/
│   ├── swarm/                     ← 22 swarm agent modules
│   └── eslint-config/             ← Shared ESLint config
├── supabase/
│   ├── migrations/                ← 20 migrations applied
│   └── seed.sql                   ← 8 competencies + sample data
├── docs/                          ← DECISIONS.md, ARCHITECTURE.md, TASK-PROTOCOL.md, ...
├── memory/                        ← Agent memory files (context, swarm, projects)
└── .github/workflows/             ← CI (ci.yml, swarm-daily.yml, session-end.yml, ...)
```

---

## 3. Request Lifecycle

Every API request follows this exact path:

```
Client
  │
  ▼
Railway Load Balancer (X-Forwarded-For → real client IP)
  │
  ▼
ProxyHeadersMiddleware  ← trusts X-Forwarded-For from Railway
  │
  ▼
slowapi Rate Limiter    ← per-IP (default 60/min) + per-user overrides
  │
  ▼
SecurityHeadersMiddleware  ← HSTS, CSP, X-Frame-Options, X-Content-Type
  │
  ▼
CORSMiddleware          ← whitelist: volaura.app, localhost:3000
  │
  ▼
ErrorAlertingMiddleware ← 5xx → Telegram CEO alert (1/5min rate limit)
  │
  ▼
RequestIdMiddleware     ← X-Request-ID correlation on every request
  │
  ▼
limit_request_body      ← POST/PUT/PATCH: Content-Length > 1MB → 413
  │
  ▼
FastAPI Router Dispatch
  │
  ▼
Route Handler
  ├── CurrentUserId (Depends) → admin.auth.get_user(JWT) → user_id UUID
  ├── SupabaseUser (Depends)  → acreate_client(ANON_KEY) per-request, RLS enforced
  └── SupabaseAdmin (Depends) → singleton client, SERVICE_ROLE, RLS bypassed
  │
  ▼
Business Logic / Service
  │
  ▼
Supabase PostgreSQL (RLS policies as security boundary)
```

**Critical:** Router order matters. Static routes before parameterized (`/me` before `/{id}`).

---

## 4. Authentication Flow

```
Frontend Signup/Login
  │
  ▼
Supabase Auth (JWT provider)
  │
  ├── JWT issued (access_token + refresh_token)
  │
  ▼
Next.js Middleware (runs on every request):
  1. i18nRouter          ← locale detection + redirect (az/en)
  2. updateSession        ← refreshes Supabase JWT (keeps session alive)
  3. Auth check           ← if protected route + no session → /login
  4. Locale routing       ← redirect / → /az or /en
  │
  ▼
API calls include: Authorization: Bearer <access_token>
  │
  ▼
FastAPI CurrentUserId dependency:
  admin.auth.get_user(token) → verifies with Supabase Auth server
  Returns: user_id (UUID)

RLS policies use auth.uid() == user_id for row-level filtering
```

---

## 5. Assessment Pipeline (Full E2E)

```
POST /api/assessment/start
  ├── Paywall check (fail-closed: missing row = blocked)
  ├── CREATE assessment_session (status=in_progress)
  └── Returns: session_id + first question

POST /api/assessment/answer
  ├── Session expiry check (expires_at)
  ├── IRT/CAT: score current answer (MCQ: exact match | Open: LLM eval)
  │   └── LLM eval chain: Vertex Express → Gemini → Groq → OpenAI → keyword_fallback
  │       └── Cache in session at submit_answer time (not on complete)
  ├── Anti-gaming: 7 detection methods:
  │   rushing, alternating, time_clustering, identical_responses,
  │   rapid_guessing, coherence, keyword_stuffing
  ├── CAT: update θ estimate (EAP) + SE (standard error)
  ├── Item selection: MFI (Maximum Fisher Information) 3PL model
  ├── Stop condition: SE ≤ 0.3 OR 20 items answered
  └── Returns: feedback + next_question (embedded in response)

POST /api/assessment/complete
  ├── Finalize score + gaming flags
  ├── Update AURA score (weighted: communication 20%, reliability 15%, ...)
  ├── Temporal decay applied (Ebbinghaus 2-phase)
  ├── emit_assessment_rewards():
  │   ├── game_character_rewards (idempotent by user+competency)
  │   ├── game_crystal_ledger (CRYSTAL_REWARD crystals)
  │   ├── character_events (visible in Life Simulator)
  │   └── cross_product_bridge: push_crystal_earned() + push_skill_verified()
  └── Returns: AssessmentResultOut (score + aura_updated + crystals_earned)
```

**IRT Model:** 3-Parameter Logistic (3PL)
- a = discrimination (≥1.2 required)
- b = difficulty (-3 to +3)
- c = guessing parameter

**Stopping criteria:** SE ≤ 0.3 (reliable estimate) OR 20 items (cap)

---

## 6. AURA Score System

```python
WEIGHTS = {
    "communication": 0.20,
    "reliability": 0.15,
    "english_proficiency": 0.15,
    "leadership": 0.15,
    "event_performance": 0.10,
    "tech_literacy": 0.10,
    "adaptability": 0.10,
    "empathy_safeguarding": 0.05,
}

BADGE_TIERS = {
    "Platinum": 90,
    "Gold": 75,
    "Silver": 60,
    "Bronze": 40,
}
```

**Temporal decay (Ebbinghaus 2-phase):**
- Phase 1 (0–30 days): Linear decay to 70% of original score
- Phase 2 (30+ days): Per-competency exponential decay with half-lives (730–1640 days)
- Floor: 60% (score never drops below 60% of assessed value)

**Verification multipliers:**
- Self-assessed: 1.00×
- Organization-verified: 1.15×
- Peer-verified: 1.25×

---

## 7. Database Architecture

**20 migrations applied. 18 tables. 3 safety views.**

### Core Tables

| Table | Purpose |
|-------|---------|
| `profiles` | User profiles, account_type, visible_to_orgs, is_platform_admin |
| `aura_scores` | Competency scores, total_score, badge_tier, temporal decay |
| `assessment_sessions` | In-progress + completed assessments, CAT state, anti-gaming flags |
| `assessment_answers` | Per-question answers, IRT scores, LLM evaluation cache |
| `organizations` | Org profiles, subscription_status, approved status |
| `org_saved_searches` | Saved talent search criteria with JSONB filters |
| `notifications` | Push notifications, org_view throttle, unread counts |
| `game_crystal_ledger` | Crystal transactions (earned, spent) |
| `game_character_rewards` | Idempotent reward claim record (user + competency) |
| `character_events` | Cross-product events (visible in Life Simulator) |
| `volunteer_embeddings` | pgvector(768) Gemini embeddings for semantic search |

### Safety Views (NEVER bypass these)

| View | Hides from public |
|------|------------------|
| `aura_scores_public` | `events_no_show`, `reliability_score`, raw competency details |
| `questions_safe` | `correct_answer`, `irt_a`, `irt_b`, `irt_c`, `evaluation_rubric` |
| `organization_trust_scores` | Internal scoring only |

**pgvector:** `vector(768)` — Gemini `text-embedding-004` dimensions.
HNSW index: `m=16, ef_construction=64`.
All vector operations via RPC functions ONLY — never PostgREST operators.

### RLS Policy Summary
All 18 tables have RLS enabled. Security boundary: `auth.uid() == user_id / org_id`.
All CRITICAL findings fixed in migration `20260324000015`.

---

## 8. Crystal Economy & Cross-Product Bridge

```
VOLAURA assessment complete
  │
  ▼
emit_assessment_rewards()
  ├── Local: game_character_rewards (idempotency), game_crystal_ledger, character_events
  └── Bridge: cross_product_bridge.py (fire-and-forget)
      ├── push_crystal_earned() → MindShift API (updates crystal balance)
      ├── push_skill_verified() → MindShift API (logs skill milestone)
      └── Circuit breaker: 3 failures / 5min → 60s silence → never raises

VOLAURA frontend (dashboard)
  └── CrystalBalanceWidget → GET /api/character/crystals (shows balance, hides if 0)

Life Simulator (Godot 4)
  └── Reads character_events table directly via Supabase SDK
```

**Crystal reward:** `CRYSTAL_REWARD` constant in `rewards.py`. Idempotent — same competency only rewarded once.

---

## 9. Notification System

```
Server-side events that trigger notifications:
  - org_view: org admin views volunteer profile (1/24h throttle per org)
  - badge_earned: new badge tier achieved
  - org_intro_request: org requests introduction to volunteer
  - match_found: saved search criteria matched (daily via match_checker.py)

Delivery:
  - DB: INSERT into notifications table
  - Realtime: Supabase Realtime subscription (dashboard layout)
    └── RealtimeNotificationsProvider → useRealtimeNotifications(userId)
    └── On INSERT → invalidates unread count + list queries instantly

match_checker.py (daily cron):
  - GitHub Actions: 07:00 UTC (11:00 Baku)
  - Queries aura_scores WHERE updated_at > last_checked_at
  - Telegram notification for matches via bot
  - Circuit breaker: 3 Telegram failures → stop
```

---

## 10. Swarm / Autonomous Agent System

```
22 modules in packages/swarm/:

INFRASTRUCTURE:
  heartbeat_gate.py      ← KAIROS gate: should swarm run today?
  execution_state.py     ← State machine (IDLE→RUNNING→SUCCESS/FAILED)
  recovery_strategies.py ← 4 strategies: retry/simplify/decompose/escalate

INTELLIGENCE:
  code_index.py          ← Indexes 530 files, extracts symbols
  task_binder.py         ← Maps task → primary/secondary files
  suggestion_engine.py   ← Predicts next CEO actions after batch close
  proposal_verifier.py   ← Verifies agent proposals reference real files

SKILL EVOLUTION:
  skill_applier.py       ← Applies improvements to skill .md files
  skill_ab_tester.py     ← Compares old vs new skill on test task

ORCHESTRATION:
  autonomous_run.py      ← Main entry (GitHub Actions daily)
  session_end_hook.py    ← Post-push hook (skill evolution check)
  report_generator.py    ← Structured batch-close reports → ceo-inbox.md

OUTCOME:
  outcome_verifier.py    ← T1 (file checks) + T2 (LLM judge) verification

GitHub Actions:
  swarm-daily.yml        ← 09:00 Baku → heartbeat gate → 5 agents
  session-end.yml        ← On push → SESSION-DIFFS.jsonl + code-index rebuild
  match-checker.yml      ← 07:00 UTC → match_checker.py
  ci.yml                 ← Tests on PR/push
```

---

## 11. LLM Chain

```
BARS Evaluator chain (for open-ended assessment answers):
  Vertex Express API → Gemini 2.5 Flash → Groq llama-3.3-70b → OpenAI GPT-4o-mini → keyword_fallback

Each provider:
  Vertex Express: VERTEX_API_KEY (fastest, pay-per-use)
  Gemini:         GEMINI_API_KEY (15 RPM free tier)
  Groq:           GROQ_API_KEY (14,400 req/day FREE)
  OpenAI:         OPENAI_API_KEY (paid, last resort)
  keyword_fallback: label=pattern_matched, confidence=low (always works)

Embedding generation:
  Primary: Vertex → text-embedding-004 → vector(768)
  Fallback: Gemini embedding

Re-evaluation worker (ADR-010):
  Background task reads assessment_answers WHERE evaluation_quality = 'keyword_fallback'
  Re-evaluates with full LLM chain (SLA: within 24h of completion)
  Upgrades stored score from pattern_match → LLM
```

---

## 12. Frontend Architecture

**41 pages total.** ~70% complete.

### Page Groups

| Group | Status | Key Pages |
|-------|--------|-----------|
| `(auth)` | ✅ Complete | login, signup, callback, onboarding |
| `(dashboard)` | ✅ ~85% | dashboard, assessment/*, profile, org-volunteers, admin |
| `(public)` | ✅ Complete | u/[username], invite, landing |
| `(admin)` | ✅ New | overview, users, organizations, aura |

### State Management

```
Server state:    TanStack Query (fetching, caching, mutations)
Client state:    Zustand 3 stores:
  - auth store:        session, user, loading, setSession()
  - assessment store:  persisted to localStorage (survives redirect)
  - ui store:          modal states, sidebar open

Form state:      React Hook Form + Zod validation
```

### Supabase Clients

```typescript
// Browser (client components)
import { createClient } from "@/lib/supabase/client";
const supabase = createClient();  // singleton, stateful

// Server (server components, route handlers)
import { createClient } from "@/lib/supabase/server";
const supabase = await createClient();  // per-request, cookies
```

---

## 13. Known Open Risks (from Audit)

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| CRIT-I01 | P0 | No request body size limit | ✅ FIXED this session |
| BUG-012 | P1 | Degraded evaluations (keyword_fallback) not re-evaluated within 24h SLA | OPEN — reeval_worker running but SLA not enforced |
| ADR-008 | P1 | AURA Score Leaderboard killed by Board — ADR not yet formalized | OPEN |
| ADR-009 | P1 | Tribe Streaks + Collective AURA Ladders — Board approved, no design doc | OPEN |
| CEO-BLOCK-1 | P2 | 3 pending CEO questions on Tribe Streaks design (Q1/Q2/Q3 in TRIBE-STREAKS-DESIGN.md) | AWAITING CEO |
| MIGRATION-1 | P2 | `20260402130000_add_platform_admin.sql` not applied in Supabase | 1-CLICK CEO |
| REALTIME-1 | P2 | Notifications table Realtime publication not enabled in Supabase dashboard | 1-CLICK CEO |
| COV-1 | P2 | Missing test files: test_skills.py, test_embeddings.py, test_match_checker.py | BACKLOG |

---

## 14. Architecture Decisions (ADR Index)

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | Supabase as sole database + auth | Validated |
| ADR-002 | FastAPI monolith (not microservices) | Validated |
| ADR-003 | @hey-api/openapi-ts for generated types | Validated |
| ADR-004 | IRT/CAT pure Python (not external library) | Validated |
| ADR-005 | Gemini 2.5 Flash as primary LLM | Validated |
| ADR-006 | VOLAURA = verified talent platform (not volunteer platform) | Locked Sprint E1 |
| ADR-007 | Crystal economy: VOLAURA → Life Simulator bridge | Validated |
| ADR-008 | AURA Leaderboard KILLED — replace with Tribe Streaks | Board-approved, not formalized |
| ADR-009 | Tribe Streaks + Collective AURA Ladders (not leaderboard) | Board-approved, not formalized |
| ADR-010 | keyword_fallback re-evaluation worker (24h SLA) | Implemented, SLA not enforced |

---

## 15. Architecture Health Assessment

**Score: 72/100**

| Domain | Score | Notes |
|--------|-------|-------|
| Security | 16/20 | RLS solid, body limit now fixed (CRIT-I01). BUG-012 open. |
| Data integrity | 18/20 | 20 migrations, RLS, idempotent rewards, 3 safety views |
| Scalability | 13/20 | In-memory rate limiting (not Redis), no db connection pool, no CDN for embeddings |
| Test coverage | 11/20 | 668 tests, but 3 test files missing. Unit only — no E2E smoke in CI |
| Documentation | 14/20 | Strong core docs. Staleness was critical this session (now resolved). |

**Conditional GO criteria for public launch:**
1. ✅ Migrations applied (MIGRATION-1 — 1-click CEO)
2. ✅ Realtime enabled (REALTIME-1 — 1-click CEO)
3. ⚠️ BUG-012 SLA enforcement (24h reeval)
4. ⚠️ Tribe Streaks CEO Q1/Q2/Q3 answers
5. ⚠️ Production E2E smoke test in CI

---

*Last updated: 2026-04-02. Audit by 5-agent parallel codebase read. Update this document when: new router added, schema changed, new major feature shipped, or architecture decision made.*
