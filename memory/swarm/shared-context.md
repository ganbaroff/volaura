# Swarm Shared Context — Read Before Every Task

**Updated:** 2026-03-27 Session 51 | **By:** CTO (Claude)
**Purpose:** Prevent agents from duplicating work, contradicting each other, or referencing wrong files.

---

## ⚠️ ARCHITECTURE SHIFT (Session 51) — READ FIRST

**Old model (DEPRECATED):** 5 separate products (Volaura + Life Simulator + MindShift + BrandedBy + ZEUS)
**New model (ACTIVE):** 1 platform (Volaura) + skill library. This is v0Laura.

**What this means for agents:**
- Do NOT propose features for "Life Simulator" as a separate app — it's `feed-curator` skill
- Do NOT propose features for "MindShift" as a separate app — it's `behavior-pattern-analyzer` skill
- Do NOT propose features for "BrandedBy" as a separate platform — it's `ai-twin-responder` skill
- Do NOT propose "ZEUS engine" as a separate API — it's `assessment-generator` skill
- ALL new features = new skills or improvements to existing skills within Volaura

**Product skills (in memory/swarm/skills/):**
| Skill | Replaces | Does what |
|-------|----------|-----------|
| `content-formatter` | — | Draft → multi-format content pack |
| `aura-coach` | AURA Coach standalone | Personalized career coaching from AURA data |
| `assessment-generator` | ZEUS engine | Question generation with GRS validation |
| `behavior-pattern-analyzer` | MindShift app | Behavioral insights, churn prediction, nudges |
| `ai-twin-responder` | BrandedBy platform | AI Twin text/video responses via RAG |
| `feed-curator` | Life Simulator game | Personalized dashboard feed (5 card types) |

**Volaura routes powered by skills:**
```
/dashboard  → feed-curator
/profile    → ai-twin-responder + behavior-pattern-analyzer
/assessment → assessment-generator
/aura       → aura-coach
/share      → content-formatter
loading...  → metaverse invite teaser
```

**Evolution path:** Skills (current) → Living world UI (v1.0). Skills = brain. World = body. Brain first.

---

## Current Sprint Goal

**Last updated: Session 58 (2026-03-28)**

**Volaura Track: SPRINT 1 ✅ + SPRINT 2 ✅ COMPLETE — Sprint 3 is next**
**BrandedBy Track: Sprint B1-B2-B3 COMPLETE ✅** (folded into Volaura as ai-twin-responder skill)
**Ecosystem Track: REPLACED by skill library approach (Session 51)**

**SPRINT-PLAN-V3.md is the current plan** — 8 sprints, 25 days, swarm-validated 38/50.
Next: Sprint 3 — API Contracts + Assessment Refactor (docs/SPRINT-PLAN-V3.md)

**Key schema changes (Sessions 57-58) — agents must know:**
- `profiles` table now has: `account_type` (volunteer/organization), `visible_to_orgs` (bool, default false), `org_type` (ngo/corporate/government/startup/academic/other/null)
- `ProfileCreate` schema accepts all 3 new fields with validators
- `ProfileResponse` returns all 3 new fields
- Rate limits: `RATE_DISCOVERY` (10/min) for enumerable endpoints, `RATE_DEFAULT` (60/min) standard, `RATE_AUTH` (5/min) auth
- UUID validation: `_validate_uuid()` helper exists in `invites.py` AND `events.py` — use this pattern, don't inline
- Crystal ledger: table `game_crystal_ledger` columns are `id, user_id, amount, source, reference_id, created_at` — NOT `delta`, NOT `reason`

**Swarm improvements (Session 51+):**
- Memory consolidation daemon LIVE: `packages/swarm/memory_consolidation.py`
- 12 skills in `memory/swarm/skills/` (6 from Session 51 + 6 from Session 57)
- New Session 57 skills: sales-deal-strategist, sales-discovery-coach, linkedin-content-creator, cultural-intelligence-strategist, behavioral-nudge-engine, accessibility-auditor
- TASK-PROTOCOL.md: mandatory 10-step workflow for every task going forward

---

### BrandedBy Sprint B1-B2-B3 — COMPLETE ✅ (Sessions 48-50, 2026-03-27)

**What was built (committed to main, deployed to volaura.app):**

| File | What it does |
|------|-------------|
| `supabase/migrations/20260327151415_create_brandedby_schema.sql` | brandedby schema, ai_twins + generations tables, RLS, updated_at trigger |
| `supabase/migrations/20260327151441_fix_brandedby_search_path.sql` | SET search_path TO '' security fix |
| `supabase/migrations/20260327161705_brandedby_retry_count.sql` | retry_count INT DEFAULT 0 on generations |
| `apps/api/app/schemas/brandedby.py` | Pydantic v2: AITwinCreate/Update/Out, GenerationCreate/Out, TwinStatus/GenerationType literals |
| `apps/api/app/routers/brandedby.py` | 8 routes: POST/GET/PATCH twins, refresh-personality, activate, POST/GET/GET generations |
| `apps/api/app/services/brandedby_personality.py` | character_state → Gemini → personality_prompt (rule-based fallback) |
| `apps/api/app/services/video_generation_worker.py` | Async poll worker: queued→processing→completed/failed, stale-lock recovery, MAX_RETRIES=2 |
| `packages/swarm/zeus_video_skill.py` | ZeusVideoSkill: script → Kokoro TTS → audio_url → SadTalker → video_url |
| `apps/web/src/hooks/queries/use-brandedby.ts` | TanStack Query hooks, 5s polling on queued/processing |
| `apps/web/src/app/.../brandedby/page.tsx` | BrandedBy dashboard: 3-step setup + generate form + history |
| `apps/web/src/app/.../generations/[id]/page.tsx` | Video player + LinkedIn share + TikTok download ($730K mechanic) |

**E2E verified pipeline:**
```
portrait JPG + script
  → fal-ai/kokoro/american-english (TTS) → .wav audio URL
  → fal-ai/sadtalker (lip-sync) → .mp4 video URL (~2 min)
```

**Architecture decisions (BrandedBy):**
- fal.ai SadTalker = Phase 1 (not D-ID — 10 vid/mo cap, not scalable; not MuseTalk — needs MP4 input not image; not LivePortrait — non-commercial InsightFace)
- fal.ai Kokoro TTS = Phase 1 (not PlayAI — deprecated; `fal-ai/kokoro/american-english`, voice: `am_adam`)
- SadTalker inputs: `source_image_url` + `driven_audio_url` (NOT `video_url`)
- `_ensure_fal_url()`: re-uploads arbitrary CDN photos to fal.media before SadTalker (fal workers can't reach Supabase Storage)
- Queue mechanic: free = 48h wait, 25 crystals = skip queue, Pro = instant
- `QUEUE_SKIP_CRYSTAL_COST = 25`
- brandedby.* schema: separate PostgreSQL schema (isolates from public.* Volaura tables)
- Auth is shared: auth.users JWT = one login for all products

**Production state:**
- FAL_API_KEY ✅ on Railway
- GROQ_API_KEY ✅ on Railway
- volaura.app ✅ updated (latest deploy with BrandedBy)
- brandedby.xyz ⏳ pending A record in GoDaddy: `@ 76.76.21.21`

---

### Volaura Sprint 10 — IN PROGRESS

Sprint 10 completed:
- Org dashboard: GET /api/organizations/me/dashboard + GET /api/organizations/me/volunteers (B2B matching)
- OrgDashboardStats + OrgVolunteerRow schemas
- /org-volunteers page: 4 stat cards, badge distribution, volunteer table with search + filter
- MASS-ACTIVATION-PLAN.md: 5 onboarding questions answered, Sprint 10.5 plan
- Migration 000034: referral_code + utm_source + utm_campaign + referral_stats VIEW
- Migration 000035: scenario_ru column on questions
- Groq fallback in bars.py: Gemini → Groq → OpenAI → keyword_fallback
- config.py: GROQ_API_KEY warning in validate_production_settings

Sprint 10 pending:
1. **UTM capture at auth callback** — save UTM params to localStorage at /register → PATCH profile at auth/callback
2. **Welcome page** — /welcome with "Start Assessment" CTA (biggest conversion fix — 60% bounce)
3. **Badge share button** — LinkedIn/TikTok share on /aura page post-completion
4. **30 RU question translations** — scripts/translate_ru.py via Gemini batch
5. **pnpm generate:api** — replace 7 TODO hooks with generated TypeScript (ADR-003)
6. CEO provides ~10 HR coordinator names → generate ref codes → activation wave

---

### Sprint A1 — NEXT

1. POST /api/assessment/complete → emit crystal_earned + skill_verified events
2. game_character_rewards idempotency: check BEFORE INSERT
3. Acceptance: Complete assessment → GET /character/state shows crystals + verified_skills

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
| fal.ai SadTalker for BrandedBy video | ACTIVE | Session 48-49 — NOT MuseTalk (needs MP4), NOT LivePortrait (non-commercial), NOT D-ID (cap 20 vid/mo) |
| fal.ai Kokoro TTS for BrandedBy audio | ACTIVE | Session 49 — NOT PlayAI (deprecated). Model: fal-ai/kokoro/american-english, voice: am_adam |
| _ensure_fal_url() before SadTalker | ACTIVE | Session 49 — fal workers can't reach Supabase Storage. Must re-upload to fal.media CDN first |
| Groq as Gemini fallback in bars.py | ACTIVE | Session 47 — Free tier 14,400 req/day. Chain: Gemini → Groq → OpenAI → keyword_fallback |
| brandedby.* separate schema | ACTIVE | Session 48 — Isolates from public.* Volaura. Auth is shared (auth.users JWT) |
| Multi-word behavioral phrase keywords (not single words) | ACTIVE | Session 42 — GRS gate requires >= 0.6, single words fail |

---

## BrandedBy — DB Schema Snapshot

```sql
-- brandedby.ai_twins
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
display_name TEXT NOT NULL
tagline TEXT
photo_url TEXT                    -- portrait photo (Supabase Storage or R2)
voice_id TEXT                     -- TTS voice identifier (Phase 2)
personality_prompt TEXT           -- auto-generated from character_state via Gemini
status TEXT DEFAULT 'draft'       -- draft | active | suspended
CONSTRAINT ai_twins_one_per_user UNIQUE (user_id)  -- one AI Twin per user

-- brandedby.generations
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
twin_id UUID NOT NULL REFERENCES brandedby.ai_twins(id) ON DELETE CASCADE
user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
gen_type TEXT DEFAULT 'video'     -- video | audio | text_chat
input_text TEXT NOT NULL          -- script
output_url TEXT                   -- generated video URL (fal.ai CDN)
thumbnail_url TEXT
status TEXT DEFAULT 'queued'      -- queued | processing | completed | failed
error_message TEXT
queue_position INT                -- free=wait, crystal skip = jump ahead
crystal_cost INT DEFAULT 0        -- crystals spent to skip
duration_seconds INT
processing_started_at TIMESTAMPTZ
completed_at TIMESTAMPTZ
retry_count INT DEFAULT 0         -- MAX_RETRIES=2 in worker
```

**RLS rules:**
- Users read/create/update/delete ONLY their own ai_twins
- Users read/create ONLY their own generations
- Status transitions (queued→processing→completed) handled ONLY by service_role (backend)

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
- **D-ID for BrandedBy video** — Invalidated. $5.90/mo = only ~20 videos/month cap. Not scalable.
- **LivePortrait / SadTalker via Replicate** — LivePortrait = non-commercial (InsightFace dependency). SadTalker on Replicate = slow (4 min) + no SLA. Use fal.ai SadTalker.
- **MuseTalk for portrait input** — MuseTalk requires MP4 video input, NOT still image. For portrait→video use SadTalker.
- **fal-ai/playai/tts** — Deprecated by fal.ai. Use fal-ai/kokoro/american-english.

---

## Current File Tree (main areas)

```
apps/api/app/
  routers/
    aura.py          — AURA score + /me/explanation (route order matters!)
    assessment.py    — Assessment start/answer/complete/results + enqueue degraded
    organizations.py — Org endpoints + /me/dashboard + /me/volunteers (B2B)
    profiles.py      — Volunteer profiles
    telegram_webhook.py — CEO<->Bot bidirectional
    character.py     — Cross-product event bus
                        POST /api/character/events, GET /api/character/state, GET /api/character/events
    brandedby.py     — AI Twin platform (NEW Sprint B1-B2)
                        POST/GET/PATCH /api/brandedby/twins
                        POST /api/brandedby/twins/{id}/refresh-personality
                        POST /api/brandedby/twins/{id}/activate
                        POST/GET /api/brandedby/generations
                        GET /api/brandedby/generations/{id}
  core/assessment/
    engine.py        — IRT/CAT adaptive engine (3PL + EAP)
    bars.py          — BARS LLM evaluator + DeCE + 4 anti-gaming gates + Groq fallback
    aura_calc.py     — AURA score + per-competency decay half-lives
    quality_gate.py  — GRS metric + adversarial gate + 10-point checklist
  schemas/
    aura.py          — AuraScoreResponse, UpdateVisibilityRequest
    assessment.py    — SessionOut, StartAssessmentRequest, SubmitAnswerRequest
    organization.py  — OrganizationResponse, OrgDashboardStats, OrgVolunteerRow, BadgeDistribution
    character.py     — EventType, SourceProduct, CharacterEventCreate/Out, CharacterStateOut
    brandedby.py     — AITwinCreate/Update/Out, GenerationCreate/Out, TwinStatus, GenerationType (NEW)
  services/
    reeval_worker.py      — Async LLM re-evaluation of degraded answers
    video_generation_worker.py — Async BrandedBy video worker (queued→processing→completed, 15s poll) (NEW)
    brandedby_personality.py   — character_state → Gemini → personality_prompt (NEW)
    swarm_service.py      — Multi-model swarm evaluation
    llm.py               — LLM abstraction layer
  middleware/
    rate_limit.py    — slowapi rate limiting
  deps.py            — Supabase client Depends(), CurrentUserId
  config.py          — Settings (pydantic-settings) — FAL_API_KEY, GROQ_API_KEY added
  main.py            — FastAPI app, router registration, reeval_worker + video_worker lifespan

packages/swarm/
  zeus_video_skill.py — ZeusVideoSkill class (NEW Sprint B3)
                        script → fal-ai/kokoro/american-english TTS → audio_url
                        photo + audio → fal-ai/sadtalker → video_url
                        _ensure_fal_url(): re-uploads to fal.media CDN (CRITICAL)

apps/web/src/
  app/[locale]/(dashboard)/
    brandedby/page.tsx              — AI Twin setup (3 steps) + generate form + history (NEW)
    brandedby/generations/[id]/page.tsx — Video player + LinkedIn/TikTok share (NEW)
    org-volunteers/page.tsx         — Org B2B dashboard (NEW)
  hooks/queries/
    use-brandedby.ts    — useMyTwin, useGenerations, useGeneration (5s polling), mutations (NEW)
    use-organizations.ts — useOrgDashboard, useOrgVolunteers added

supabase/migrations/
  ...35 migration files including:
  20260326000029_evaluation_queue.sql             — Queue for degraded answer re-evaluation
  20260326000030_update_question_keywords_grs.sql — Keyword redesign for GRS compliance
  20260327000031_character_state_tables.sql       — character_events + game_crystal_ledger + game_character_rewards
  20260327000032_character_state_fixes.sql        — CHECK constraints, BIGINT, search_path, skill_unverified
  20260327000034_activation_tracking.sql          — referral_code + utm_* on profiles + referral_stats VIEW
  20260327000035_scenario_ru_column.sql           — scenario_ru on questions (nullable RU fallback)
  20260327151415_create_brandedby_schema.sql      — brandedby.* schema, ai_twins + generations (NEW)
  20260327151441_fix_brandedby_search_path.sql    — search_path security fix (NEW)
  20260327161705_brandedby_retry_count.sql        — retry_count on brandedby.generations (NEW)

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
     -> If Gemini fails -> Try Groq llama-3.3-70b (FREE: 14,400 req/day, 30 RPM)
     -> If Groq fails -> Try OpenAI gpt-4o-mini
     -> If all LLMs fail -> keyword_fallback (4 anti-gaming gates)
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
