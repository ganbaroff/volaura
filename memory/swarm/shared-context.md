# Swarm Shared Context — Read Before Every Task

**Updated:** 2026-03-25 | **By:** CTO (Claude Sonnet)
**Purpose:** Prevent agents from duplicating work, contradicting each other, or referencing wrong files.

---

## Current Sprint Goal

Trust Architecture Phase 1+2 — SHIPPED (2026-03-25)
- Phase 1: Privacy model (visibility, role_level, sharing_permissions)
- Phase 2: Transparent evaluation logs (BARS EvaluationResult, /aura/me/explanation)
- Security fixes applied post-review (enumeration leak, model_used exposure, org validation)

**Next sprint:** Phase 3 — Adoption/Progress framing + discovery endpoint for orgs

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

---

## No-Go Topics (Do NOT propose these)

- **API Gateway** — Deferred. Single FastAPI monolith works at current scale.
- **Redis** — Not needed until 2+ Railway instances. Current: in-memory rate limiter.
- **Microservices** — Monolith architecture intentional. No decomposition.
- **Celery/workers** — Use Supabase Edge Functions or pg_cron instead.
- **OpenAI as primary** — Gemini is primary. OpenAI is fallback only.
- **SQLAlchemy** — Supabase SDK only.
- **Privacy by default** — Already decided: PUBLIC by default (see Phase 1 decision log).

---

## Current File Tree (main areas)

```
apps/api/app/
  routers/
    aura.py          — AURA score endpoints (updated 2026-03-25)
    assessment.py    — Assessment start/answer/complete/results
    organizations.py — Org endpoints (has schema bug, fixed Sprint N)
    profiles.py      — Volunteer profiles
    telegram_webhook.py — CEO↔Bot bidirectional (rewritten 2026-03-25, Supabase-backed)
  core/assessment/
    engine.py        — IRT/CAT adaptive engine (3PL + EAP)
    bars.py          — BARS LLM evaluator (EvaluationResult class)
    antigaming.py    — Anti-gaming analysis
    aura_calc.py     — AURA score calculation
  schemas/
    aura.py          — AuraScoreResponse, UpdateVisibilityRequest, SharingPermissionRequest
    assessment.py    — SessionOut, StartAssessmentRequest, SubmitAnswerRequest, etc.
    organization.py  — OrganizationResponse (verified_at not is_verified, website not website_url)
  services/
    swarm_service.py — Multi-model swarm evaluation
    llm.py           — LLM abstraction layer
  middleware/
    rate_limit.py    — slowapi rate limiting (constants: RATE_AUTH, RATE_ASSESSMENT_*)
  deps.py            — Supabase client Depends(), CurrentUserId
  config.py          — Settings (pydantic-settings)
  main.py            — FastAPI app, router registration

supabase/migrations/
  20260325000021_add_privacy_role_visibility.sql  — Phase 1 schema
  20260325000022_create_ceo_inbox.sql             — Telegram ceo_inbox table

packages/swarm/
  engine.py          — ProviderRegistry, allocate_agents() — NEEDS team_leads wiring
  team_leads.py      — TeamLead classes (Content/Business/Security/Architecture/Speed)
  pm.py              — Swarm orchestrator
```

---

## Known Issues / Active Bugs

| ID | Issue | Status | Owner |
|----|-------|--------|-------|
| BUG-01 | Swarm path (swarm_enabled=True) doesn't produce evaluation_log → Phase 2 broken for swarm evals | OPEN | Next sprint |
| BUG-02 | k-anonymity not implemented (org sees stats with <5 users) | OPEN | Phase 3 |
| BUG-03 | Role percentile curves empty at launch (need bootstrap strategy) | OPEN | Phase 3 |
| BUG-04 | team_leads.py never called in engine.py allocate_agents() | OPEN | Next sprint |
| BUG-05 | evaluation_log storage: 14-43GB/year at 3K users — archive strategy needed | OPEN | Before 500 users |
| BUG-06 | No RLS integration tests (all tests use mocks) | OPEN | Next sprint |

---

## DB Schema Snapshot (key tables)

```sql
-- aura_scores
volunteer_id UUID PRIMARY KEY REFERENCES auth.users(id)
total_score FLOAT NOT NULL
badge_tier TEXT NOT NULL  -- Bronze/Silver/Gold/Platinum
elite_status BOOLEAN DEFAULT FALSE
competency_scores JSONB DEFAULT '{}'
visibility TEXT DEFAULT 'public' CHECK (IN ('public','badge_only','hidden'))
reliability_score FLOAT DEFAULT 0.0
reliability_status TEXT DEFAULT 'pending'
events_attended INT DEFAULT 0
events_no_show INT DEFAULT 0
percentile_rank FLOAT
aura_history JSONB DEFAULT '[]'
last_updated TIMESTAMPTZ DEFAULT NOW()

-- assessment_sessions
id UUID PRIMARY KEY
volunteer_id UUID REFERENCES auth.users(id)
competency_id UUID REFERENCES competencies(id)
status TEXT  -- in_progress | completed
role_level TEXT DEFAULT 'volunteer' CHECK (IN ('volunteer','coordinator','specialist','manager','senior_manager'))
theta_estimate FLOAT DEFAULT 0.0
theta_se FLOAT DEFAULT 1.0
answers JSONB DEFAULT '{}'  -- CATState serialized (items, theta, theta_se, stopped, stop_reason)
current_question_id UUID
question_delivered_at TIMESTAMPTZ
answer_version INT DEFAULT 0
started_at TIMESTAMPTZ
completed_at TIMESTAMPTZ

-- sharing_permissions
id UUID PRIMARY KEY
user_id UUID REFERENCES auth.users(id)
org_id UUID REFERENCES organizations(id)
permission_type TEXT CHECK (IN ('read_score','read_full_eval','export_report'))
granted_at TIMESTAMPTZ DEFAULT NOW()
revoked_at TIMESTAMPTZ
UNIQUE(user_id, org_id, permission_type)

-- ceo_inbox (Telegram messages)
id UUID PRIMARY KEY
direction TEXT  -- inbound | outbound
message TEXT
message_type TEXT  -- idea | task | question | report | command | response
metadata JSONB DEFAULT '{}'
processed BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ DEFAULT NOW()

-- competencies
id UUID PRIMARY KEY
slug TEXT UNIQUE  -- communication, reliability, english_proficiency, leadership, ...
name_en TEXT
name_az TEXT
weight FLOAT
is_active BOOLEAN DEFAULT TRUE

-- questions
id UUID PRIMARY KEY
competency_id UUID REFERENCES competencies(id)
type TEXT  -- mcq | open_ended
scenario_en TEXT
scenario_az TEXT
options JSONB  -- for MCQ
correct_answer TEXT  -- for MCQ
expected_concepts JSONB  -- [{name, weight, keywords}]
irt_a FLOAT DEFAULT 1.0
irt_b FLOAT DEFAULT 0.0
irt_c FLOAT DEFAULT 0.0
is_active BOOLEAN DEFAULT TRUE
```

---

## API Response Format

All endpoints return structured errors:
```json
{"code": "SNAKE_CASE_CODE", "message": "Human readable message"}
```

No standard response envelope yet (`{data, meta}` deferred — ADR-003 pending implementation).

---

## AURA Weights (DO NOT CHANGE)
- communication: 0.20
- reliability: 0.15
- english_proficiency: 0.15
- leadership: 0.15
- event_performance: 0.10
- tech_literacy: 0.10
- adaptability: 0.10
- empathy_safeguarding: 0.05

## Badge Tiers
- Platinum: >= 90
- Gold: >= 75
- Silver: >= 60
- Bronze: >= 40
- None: < 40
