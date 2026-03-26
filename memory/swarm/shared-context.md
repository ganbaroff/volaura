# Swarm Shared Context — Read Before Every Task

**Updated:** 2026-03-27 | **By:** CTO (Claude)
**Purpose:** Prevent agents from duplicating work, contradicting each other, or referencing wrong files.

---

## Current Sprint Goal

**Sprint 9 — COMPLETE** ✅ | **Sprint 10 — STARTING**

Sprint 9 completed items:
- CSV bulk invite: DONE (Session 39)
- Assessment flow fixes: DONE (Session 40, 6 files rewritten)
- Assessment hardening: DONE (Session 42) — DeCE, anti-gaming, GRS, reeval worker
- E2E Leyla journey: DONE (Sessions 43-44) — production verified AURA 12.47
- All 9 migrations applied via Supabase MCP (Sessions 43-44)
- Question bank: 0 placeholders, 90 real scenarios across 8 competencies (Session 44)
- Railway fix: Supabase anon key hardcoded fallback (Session 44, Mistake #53)

**Sprint 10 priorities:**
1. `pnpm generate:api` → replace 7 TODO frontend hooks with generated types
2. Org dashboard — aggregate volunteer scores + matching endpoint for B2B
3. Post 003 LinkedIn post (angle: CEO decision needed)
4. Vitest fix (Node v24 filesystem bug → need Node v20 LTS)

**CRITICAL: Production env vars (Session 44 finding)**
- `SUPABASE_ANON_KEY` is intercepted by Railway's Supabase integration (injected as empty)
- Fix: hardcoded in `config.py` as default + `SUPABASE_ANON_JWT` as Railway fallback
- DO NOT change `SUPABASE_ANON_KEY` default in config.py — it must remain the JWT key
- Leyla test user: `leyla@test.volaura.com` / `LeylaProd2026!`

---

## Architecture Decisions (DO NOT RE-PROPOSE)

| Decision | Status | Rationale |
|----------|--------|-----------|
| Supabase async SDK (not SQLAlchemy) | ACTIVE | Consistent with monorepo, no ORM overhead |
| Gemini 2.5 Flash (primary) + GPT-4o-mini (fallback) | ACTIVE | Cost + quality balance |
| google-genai SDK (NOT google-generativeai) | ACTIVE | New SDK, old one deprecated |
| Zustand (not Redux) | ACTIVE | Frontend state |
| Next.js App Router (not Pages) | ACTIVE | Next.js 14 standard |
| Pydantic v2 syntax (not v1) | ACTIVE | ConfigDict, field_validator |
| slowapi rate limiter (in-memory, single Railway instance) | ACTIVE | Scale to Redis when 2+ instances |
| pgvector(768) — Gemini embeddings (NOT 1536 OpenAI) | ACTIVE | Gemini text-embedding-004 |
| Public visibility by default (not hidden) | ACTIVE | Adoption-first, Leyla's feedback |
| All DB writes via db_admin in assessment (not db_user) | ACTIVE | BLOCKER-1 fix, prevents theta manipulation |
| loguru for logging (not print()) | ACTIVE | Structured logs to Railway |
| ADR-010: keyword_fallback = evaluation_mode "degraded" | ACTIVE | Session 42 — keyword matching is vocabulary test, not competence |
| DeCE Framework: per-concept {score, quote, confidence} | ACTIVE | Session 42 — ISO 10667-2 Clause 6.7 compliance |
| Per-competency decay half-lives (not uniform) | ACTIVE | Session 42 — tech=730d, leadership=1640d, weighted avg=1295d |
| Multi-word behavioral phrase keywords (not single words) | ACTIVE | Session 42 — GRS gate requires >= 0.6, single words fail |

---

## No-Go Topics (Do NOT propose these)

- **API Gateway** — Deferred. Single FastAPI monolith works at current scale.
- **Redis** — Not needed until 2+ Railway instances. Current: in-memory rate limiter.
- **Microservices** — Monolith architecture intentional. No decomposition.
- **Celery/workers** — Use Supabase Edge Functions or pg_cron instead.
- **OpenAI as primary** — Gemini is primary. OpenAI is fallback only.
- **SQLAlchemy** — Supabase SDK only.
- **Privacy by default** — Already decided: PUBLIC by default.
- **keyword_fallback as valid evaluation** — It measures vocabulary, not competence. Always flag as "degraded".
- **Single-word keywords in questions** — Proven gameable (GRS < 0.4). All keywords must be 3+ word behavioral phrases.

---

## Current File Tree (main areas)

```
apps/api/app/
  routers/
    aura.py          — AURA score + /me/explanation (route order matters!)
    assessment.py    — Assessment start/answer/complete/results + enqueue degraded
    organizations.py — Org endpoints
    profiles.py      — Volunteer profiles
    telegram_webhook.py — CEO<->Bot bidirectional
  core/assessment/
    engine.py        — IRT/CAT adaptive engine (3PL + EAP)
    bars.py          — BARS LLM evaluator + DeCE + 4 anti-gaming gates
    aura_calc.py     — AURA score + per-competency decay half-lives
    quality_gate.py  — GRS metric + adversarial gate + 10-point checklist (NEW Session 42)
  schemas/
    aura.py          — AuraScoreResponse, UpdateVisibilityRequest
    assessment.py    — SessionOut, StartAssessmentRequest, SubmitAnswerRequest
    organization.py  — OrganizationResponse
  services/
    reeval_worker.py — Async LLM re-evaluation of degraded answers (NEW Session 42)
    swarm_service.py — Multi-model swarm evaluation
    llm.py           — LLM abstraction layer
  middleware/
    rate_limit.py    — slowapi rate limiting
  deps.py            — Supabase client Depends(), CurrentUserId
  config.py          — Settings (pydantic-settings)
  main.py            — FastAPI app, router registration, reeval_worker lifespan

supabase/migrations/
  ...30+ migration files including:
  20260326000029_evaluation_queue.sql     — Queue for degraded answer re-evaluation
  20260326000030_update_question_keywords_grs.sql — Keyword redesign for GRS compliance

scripts/
  audit_seed_questions.py  — GRS audit tool for question bank
```

---

## CRITICAL: Route Ordering in FastAPI

**Session 42 P0 bug:** `/me/explanation` was UNREACHABLE because `/{volunteer_id}` wildcard was registered first. FastAPI matches in registration order. Static routes MUST precede parameterized routes:

```python
@router.get("/me")              # exact — FIRST
@router.get("/me/explanation")  # exact — SECOND
@router.get("/{volunteer_id}")  # wildcard — LAST
```

**Any agent reviewing aura.py or any router with /{id} patterns MUST verify route order.**

---

## Assessment Pipeline (Session 42 — KNOW THIS)

```
User submits answer
  -> evaluate_answer() in bars.py
     -> Try Gemini (DeCE format: {score, quote, confidence} per concept)
     -> If Gemini fails -> Try OpenAI
     -> If both fail -> keyword_fallback (4 anti-gaming gates)
        -> Flag evaluation_mode="degraded" in log
        -> Enqueue for async LLM re-evaluation (reeval_worker.py)
           -> Worker polls every 60s, re-evaluates via Gemini
           -> Silently patches session answers + AURA score
```

**Anti-gaming gates (stack multiplicatively):**
1. min_length: < 30 words -> cap at 0.4
2. stuffing_detection: >60% keywords in <50 words -> 0.3x
3. coherence_heuristic: verb_count/keyword_hits < 0.4 -> 0.55x
4. scenario_relevance: token overlap < 15% -> 0.65x

**Question keyword design rules (GRS gate):**
- All keywords must be 3+ words (behavioral phrases)
- Keywords must describe ACTIONS, not CONCEPTS
- Keywords must be scenario-anchored
- GRS < 0.6 = question is gameable = DO NOT DEPLOY
- Run: scripts/audit_seed_questions.py before any question change

---

## Known Issues / Active Bugs

| ID | Issue | Status | Owner |
|----|-------|--------|-------|
| BUG-01 | Swarm path doesn't produce evaluation_log | OPEN | Next sprint |
| BUG-02 | k-anonymity not implemented (<5 users) | OPEN | Phase 3 |
| BUG-03 | Role percentile curves empty at launch | OPEN | Phase 3 |
| BUG-04 | team_leads.py never called in engine.py | OPEN | Next sprint |
| BUG-05 | evaluation_log storage: 14-43GB/year at 3K users | OPEN | Before 500 users |
| BUG-06 | No RLS integration tests | OPEN | Next sprint |
| BUG-07 | 5 pending migrations need supabase db push (CEO action) | OPEN | SHIP_BLOCKER |
| BUG-08 | Email confirmation blocks beta registration (CEO: disable in dashboard) | OPEN | SHIP_BLOCKER |

---

## DB Schema Snapshot (key tables)

```sql
-- aura_scores
volunteer_id UUID PRIMARY KEY REFERENCES auth.users(id)
total_score FLOAT NOT NULL
badge_tier TEXT NOT NULL  -- Bronze/Silver/Gold/Platinum
elite_status BOOLEAN DEFAULT FALSE
competency_scores JSONB DEFAULT '{}'
visibility TEXT DEFAULT 'public'
percentile_rank FLOAT
aura_history JSONB DEFAULT '[]'
last_updated TIMESTAMPTZ DEFAULT NOW()

-- assessment_sessions
id UUID PRIMARY KEY
volunteer_id UUID REFERENCES auth.users(id)
competency_id UUID REFERENCES competencies(id)
status TEXT  -- in_progress | completed
role_level TEXT DEFAULT 'volunteer'
theta_estimate FLOAT DEFAULT 0.0
theta_se FLOAT DEFAULT 1.0
answers JSONB DEFAULT '{}'
current_question_id UUID
started_at TIMESTAMPTZ
completed_at TIMESTAMPTZ

-- evaluation_queue (NEW — Session 42, ADR-010)
id UUID PRIMARY KEY
session_id UUID REFERENCES assessment_sessions(id)
volunteer_id UUID REFERENCES auth.users(id)
question_id UUID REFERENCES questions(id)
competency_slug TEXT NOT NULL
question_en TEXT NOT NULL
answer_text TEXT NOT NULL
expected_concepts JSONB NOT NULL
degraded_score FLOAT NOT NULL
status TEXT DEFAULT 'pending'  -- pending | processing | done | failed
retry_count INT DEFAULT 0
llm_score FLOAT
llm_model TEXT
score_delta FLOAT
queued_at TIMESTAMPTZ DEFAULT NOW()

-- questions
id UUID PRIMARY KEY
competency_id UUID REFERENCES competencies(id)
type TEXT  -- mcq | open_ended
scenario_en TEXT
scenario_az TEXT
options JSONB  -- for MCQ
correct_answer TEXT  -- for MCQ
expected_concepts JSONB  -- [{name, weight, keywords}] — keywords MUST be multi-word phrases
irt_a FLOAT DEFAULT 1.0
irt_b FLOAT DEFAULT 0.0
irt_c FLOAT DEFAULT 0.0
is_active BOOLEAN DEFAULT TRUE
```

---

## AURA Weights (DO NOT CHANGE)
- communication: 0.20, reliability: 0.15, english_proficiency: 0.15, leadership: 0.15
- event_performance: 0.10, tech_literacy: 0.10, adaptability: 0.10, empathy_safeguarding: 0.05

## Badge Tiers
Platinum >= 90, Gold >= 75, Silver >= 60, Bronze >= 40, None < 40

## Decay Half-Lives (per competency)
tech_literacy/event_performance: 730d, english_proficiency: 1095d, communication/reliability/adaptability: 1460d, leadership/empathy: 1640d, weighted avg: 1295.2d
