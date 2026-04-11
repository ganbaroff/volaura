# ARCHITECTURE_OVERVIEW — As-Built State of the AI Ecosystem

**Version:** 1.0 (2026-04-12, Session 93)
**Scope:** Actual state of the VOLAURA monorepo and its 5 products as of this session, not aspirational.
**Companion:** `docs/CONSTITUTION_AI_SWARM.md` (governance layer), `docs/EXECUTION_PLAN.md` (how we get from here to the target state)

---

## 1. ECOSYSTEM — FIVE PRODUCTS, NOT FOUR

The `AI_Ecosystem_Architecture.docx` strategic brief lists four products. The actual codebase has **five**. BrandedBy is active and has a FastAPI router (`apps/api/app/routers/brandedby.py`) and is mentioned in `docs/ECOSYSTEM-MAP.md`. Decision required — see CEO decision #1 in `docs/EXECUTION_PLAN.md`.

| Product | Role | Tech | Status | URL |
|---|---|---|---|---|
| **VOLAURA** | Verified competency platform — adaptive assessment, AURA score, badges, talent matching for orgs | Next.js 14 App Router + FastAPI + Supabase + pgvector 768-dim | **Live** | `volaura.app`, API `volauraapi-production.up.railway.app` |
| **MindShift** | ADHD-focused productivity — focus sessions, habit tracking, energy adaptation | Next.js + Capacitor (iOS/Android) + separate Supabase | **Live** | `mindshift.app`, Supabase `awfoqycoltvhamtrsvxk` |
| **LifeSimulator** | Godot 4 character progression game; crystals earned from VOLAURA assessments + MindShift focus sessions | Godot 4 GDScript | **Dev** | local, bridges to VOLAURA API |
| **BrandedBy** | AI video twin / professional identity generator | FastAPI + fal.ai MuseTalk | **Dev** | `brandedby.xyz` (planned) |
| **ZEUS** | Autonomous Python swarm agent framework with governance layer | Python swarm + Railway gateway + ngrok exposure | **Partial** (bridge live, orchestration local) | localhost + Railway `/api/zeus/proposal` |

**Positioning note.** The Ecosystem Constitution v1.7 and Sprint E1 locked decision (2026-03-29) define VOLAURA as a **"verified talent platform, not a volunteer platform."** The recent CEO briefing uses "волонтёрская платформа" in shorthand. This is logged as CEO Decision #1 for formal ratification or revocation.

---

## 2. TECHNOLOGY STACK (ACTUAL, VERIFIED)

### Frontend (`apps/web/`)

- **Framework:** Next.js **14.2.35** App Router. Not Next.js 15 — any tooling that assumes 15 is wrong.
- **Language:** TypeScript 5 strict mode, no `any` allowed.
- **Styling:** Tailwind CSS 4 (CSS-first config via `@tailwindcss/postcss`).
- **State:** Zustand (global), TanStack Query (server state).
- **Forms:** React Hook Form + Zod.
- **i18n:** react-i18next, AZ primary + EN secondary. All routes under `/${locale}/path`.
- **Charts:** Recharts (radar chart for AURA breakdown).
- **Components:** shadcn/ui base + `components/features/` compositions.
- **PWA:** `@ducanh2912/next-pwa`.
- **Animation:** Framer Motion, with Constitution Law 4 safety rules enforced (max 800ms non-decorative, prefers-reduced-motion required).

### Backend (`apps/api/`)

- **Framework:** FastAPI async on Python **>=3.11** (not hard 3.12 — `pyproject.toml` says `>=3.11`).
- **DB client:** Supabase async SDK, `acreate_client` **per request** via FastAPI `Depends()` — global client never allowed.
- **Schemas:** Pydantic v2 only (`ConfigDict`, `@field_validator`, `@classmethod`). Pydantic v1 syntax banned.
- **LLM:** `google-genai` SDK (Gemini primary). Fallback chain resolved through `app/services/model_router.py` (see section 4).
- **Assessment core:** Pure-Python IRT/CAT engine (3PL + EAP) — no external library. Lives in `apps/api/app/core/assessment/engine.py`.
- **Logging:** `loguru`. `print()` banned.
- **Observability:** Sentry DSN wired via Railway env; Langfuse keys optional.

### Database — Supabase

- **Shared project:** `dwdgzfusjsobnixgyzjk` — used by VOLAURA + cross-product bridge.
- **MindShift project:** `awfoqycoltvhamtrsvxk` — separate, bridged via edge function `volaura-bridge-proxy`.
- **Extensions:** `pgvector` for 768-dim Gemini embeddings (never 1536 / OpenAI).
- **RLS:** enabled on every table; policies follow `auth.uid() = <owner column>` pattern. Verified live this session via the new `inspect_table_policies` RPC.
- **Migrations:** `supabase/migrations/YYYYMMDDHHMMSS_description.sql`. 40+ migrations in repo, latest applied `20260411200500_zeus_harden.sql`.
- **New namespace:** `zeus` schema (not exposed via PostgREST — read via RPCs). Contains `governance_events` audit log + `inspect_table_policies` + `log_governance_event` RPCs.

### Hosting

- **Frontend:** Vercel auto-deploy on push to main.
- **Backend:** Railway service `volaura-api`, deploys from `Dockerfile`.
- **DB:** Supabase free tier (shared + MindShift projects).
- **Swarm:** GitHub Actions daily cron + local Python execution.

### LLM providers (Article 0 hierarchy, enforced via `model_router.py`)

| Priority | Provider | Model | Role | Available? |
|---|---|---|---|---|
| 1 | Cerebras | Qwen3-235B | judge / worker (fastest) | ❌ no key configured |
| 2 | Ollama local | qwen3:8b | worker (zero cost, zero rate limit) | ❌ not enabled in settings |
| 3 | NVIDIA NIM | llama-3.1-nemotron-ultra-253b-v1 | judge | ✅ key set |
| 3 | NVIDIA NIM | llama-3.3-70b-instruct | worker | ✅ key set |
| 4 | Gemini | gemini-2.5-pro | safe_user_facing primary | ✅ key set, **needs billing** |
| 4 | Gemini | gemini-2.0-flash | fast / fallback | ✅ key set, **free tier exhausted** this session |
| 5 | Groq | llama-3.3-70b-versatile | worker fallback | ✅ key set |
| 5 | Groq | llama-3.1-8b-instant | fast primary | ✅ key set |
| LAST | Anthropic | claude-haiku-4-5 | **safe_user_facing last resort only** | available; **physically unreachable from JUDGE/WORKER/FAST chains** per Article 0 |

**Claude is not a swarm runtime provider.** Hardcoded in `apps/api/app/services/model_router.py` — Haiku appears exactly once, at the tail of the `SAFE_USER_FACING` chain. It is not in `JUDGE`, `WORKER` or `FAST` chains and cannot be selected for those roles by any code path.

---

## 3. MONOREPO LAYOUT

Current structure is close to Cal.com / Next-forge conventions but lacks a `packages/` layer for shared code.

```
VOLAURA/
├── apps/
│   ├── web/                  # Next.js 14 frontend
│   └── api/                  # FastAPI backend (Python 3.11+)
│       ├── app/
│       │   ├── main.py       # FastAPI entry, middleware, global error handler
│       │   ├── config.py     # pydantic-settings, all env vars
│       │   ├── deps.py       # SupabaseAdmin, SupabaseUser, CurrentUserId
│       │   ├── routers/      # 26 routers (auth, assessment, aura, character, auth_bridge, skills, zeus_gateway, ...)
│       │   ├── services/     # llm, model_router (new), reeval_worker, notification, etc.
│       │   ├── core/         # assessment engine, reliability, matching
│       │   ├── schemas/      # Pydantic v2 models
│       │   └── middleware/   # rate_limit, error_alerting, request_id, security_headers
│       └── tests/
├── packages/
│   └── swarm/                # Python swarm — NOT a shared package in the monorepo sense; it's the orchestration module
│       ├── autonomous_run.py # main entry, 9 modes
│       ├── engine.py         # agent runner with ECOSYSTEM-MAP injection
│       ├── tools/            # code_tools, constitution_checker, deploy_tools, llm_router
│       ├── memory/           # ECOSYSTEM-MAP.md, Global_Context.md
│       └── skills/           # 48 skill definitions
├── supabase/
│   ├── migrations/           # 40+ .sql migrations, timestamp-prefixed
│   └── seed.sql              # 8 competencies + IRT sample questions
├── scripts/                  # prod_smoke_test, prod_smoke_e2e (new), audit_assessment_state, debug_aura_rpc, check_rls_live
├── docs/                     # 70+ markdown docs incl. ECOSYSTEM-CONSTITUTION, RUNBOOK, CONTRIBUTING, ARCHITECTURE (this file), etc.
├── memory/
│   ├── context/              # sprint-state, mistakes, patterns, working-style (gitignored)
│   └── swarm/                # proposals.json, agent-roster, ceo-inbox, SHIPPED, shared-context, 48 skill files
├── .github/workflows/        # ci.yml, swarm-daily.yml, session-end.yml (fixed session 93), post-deploy-agent, ...
├── .claude/                  # rules/, breadcrumb, hooks
└── CLAUDE.md                 # project-level instructions for Claude, Article 0 LLM hierarchy, 10-step algorithm
```

**Gaps vs Cal.com / Next-forge:**
- No `packages/ui` — shadcn components live inside `apps/web` only.
- No `packages/db` with shared Prisma/Supabase types.
- No `packages/config` — ESLint / Prettier / TSConfig duplicated per workspace.
- No Turborepo pipeline (`turbo.json` exists but not optimally configured).

These are P2 refactor targets, not P0 blockers.

---

## 4. THE ZEUS GOVERNANCE LAYER (deployed this session)

Session 93 deployed the first real governance infrastructure to prod. Prior to this session, governance was entirely prompt-based. Now it has a database backing.

### `zeus.governance_events` table (migration `20260411193900_zeus_governance.sql` + `_200500_zeus_harden.sql`)

```
id            UUID PRIMARY KEY
event_type    TEXT       -- 'constitution_violation' | 'challenge' | 'ceo_escalation' | 'reconciliation' | 'security_harden' | ...
severity      TEXT       -- 'info' | 'low' | 'medium' | 'high' | 'critical'
source        TEXT       -- 'cto-hands' | 'cto-brain' | 'swarm' | 'agent:<name>' | 'system' | 'ceo'
actor         TEXT       -- who triggered (agent name, user_id, 'claude-opus-4-6', 'perplexity', ...)
subject       TEXT       -- what was affected (table, file, feature, plan ID)
payload       JSONB      -- structured details: challenge body, evidence, decisions
created_at    TIMESTAMPTZ
```

RLS: service role only. `authenticated` and `anon` roles explicitly REVOKEd (CRITICAL fix in `_200500_zeus_harden.sql`).

### `public.inspect_table_policies(p_table_name TEXT)` RPC

SECURITY DEFINER wrapper around `pg_catalog.pg_policies`. PostgREST blocks `pg_catalog` directly (PGRST106), so this RPC is the only way to read live RLS policies via the Supabase SDK. Service role only.

### `public.log_governance_event(...)` RPC

Structured insert helper. Validates severity, enforces JSONB payload, returns new event UUID. Service role only.

### `apps/api/app/services/model_router.py` (the role-based provider selector)

- 4 roles: `JUDGE`, `WORKER`, `FAST`, `SAFE_USER_FACING`.
- Each role has an ordered preference chain honouring Article 0.
- `emit_fallback_event()` non-blocking hook writes a `model_router_fallback` governance event when production runs on a degraded provider.
- Claude Haiku is reachable only through `SAFE_USER_FACING` as the final fallback. Physically unreachable from JUDGE/WORKER/FAST chains.

---

## 5. DATA FLOWS

### User signup → assessment → AURA → share (the "golden path")

Verified end-to-end in prod this session (`scripts/prod_smoke_e2e.py` passes):

```
1. (Direct VOLAURA or MindShift bridge)
   → POST /api/auth/register          (if direct, email confirmation required)
   OR
   → POST /api/auth/from_external     (if bridged from MindShift; returns shared_jwt + creates profiles row)

2. POST /api/assessment/start         (returns SessionOut with first_question)
3. POST /api/assessment/answer        (loop, driven by CAT engine, until is_complete=true)
4. POST /api/assessment/complete/{session_id}  (finalises, calls upsert_aura_score RPC, emits crystal_earned, fires analytics)
5. GET  /api/aura/me                  (returns AuraScoreResponse: total_score, badge_tier, competency_scores)
6. (share/link via public profile endpoint — PublicVerificationOut schema)
```

**Two bugs fixed this session that broke this path**:

- `auth_bridge.py` never created a `profiles` row for shadow users → FK violation on every `assessment_sessions.volunteer_id`. Fixed commit `8b153e0` with `_ensure_profile_row()`.
- `submit_answer` pre-marked session `status='completed'` when CAT stopped, causing `/complete` to hit the BUG-015 idempotency branch and skip `upsert_aura_score`. Fixed commit `5c0b006` — submit_answer no longer sets status.

### Crystal economy (cross-product bridge)

All products write to `public.character_events` table in the shared Supabase project:

```
VOLAURA assessment complete  → xp_earned    (+50-200 crystals)
VOLAURA badge earned         → buff_applied (+100 crystals)
MindShift focus session      → xp_earned    (+10-30 crystals)
Life Simulator reads character_events for game world progression
```

RLS on `character_events`: `USING (auth.uid() = user_id)` for SELECT + `WITH CHECK (auth.uid() = user_id)` for INSERT. **Live verified this session via `inspect_table_policies('character_events')` — the "silent blocker" hypothesis from the AI council brief is resolved: the policy is correct, not `USING (true)`.**

### Swarm feedback flow

```
Swarm daily cron (05:00 UTC)
  → packages/swarm/autonomous_run.py --mode=daily-ideation
  → 8 specialist perspectives + CTO watchdog + Ecosystem Auditor
  → Proposals written to memory/swarm/proposals.json (gitignored, local canonical)
  → HIGH/CRITICAL proposals surfaced to memory/swarm/ceo-inbox.md
  → Telegram bot notification to CEO for CRITICAL only
  → Session-start hook surfaces pending proposals on next session

Swarm on every push to main (session-end.yml)
  → session_end_hook captures git diff
  → Appends to memory/swarm/SESSION-DIFFS.jsonl
  → Rebuilds memory/swarm/code-index.json
  → Runs mini-swarm code-review on changed files (async, non-blocking push)
  → Proposes + opens PRs for auto-fix in some cases (aider auto-commit)
```

### Bridged user flow (MindShift → VOLAURA)

```
MindShift user with active JWT
  → MindShift calls its edge function volaura-bridge-proxy (awfoqycoltvhamtrsvxk)
  → Edge function validates MindShift JWT, then calls VOLAURA API:
  → POST /api/auth/from_external  with X-Bridge-Secret header
     + body: { standalone_user_id, standalone_project_ref, email, source_product: 'mindshift' }
  → VOLAURA looks up user_identity_map, creates shadow auth.users if absent,
    creates profiles row (fixed this session), mints a shared project JWT
  → Returns { shared_user_id, shared_jwt, expires_at }
  → Bridged user now hits /api/assessment/start etc with the shared JWT
```

---

## 6. CI/CD AND DEPLOY CHAIN

### Workflows

- **`ci.yml`** — typecheck + lint + pytest on every PR. **Currently red pre-existing** (ruff UP041/N806/B904 errors in `bars.py`, `deps.py`; pnpm lockfile drift). Not a Session 93 regression. Added to CEO Decision list.
- **`swarm-daily.yml`** — 05:00 UTC (09:00 Baku) daily swarm run. Writes proposals.
- **`session-end.yml`** — on push to main, captures diff + rebuilds code index + runs mini-swarm. Fixed this session (`pydantic` install + bash quoting).
- **`post-deploy-agent.yml`** — after deploy, health verification + swarm context update.
- **`swarm-adas.yml`** — adversarial swarm runs.
- **`analytics-retention.yml`**, **`tribe-matching.yml`**, **`zeus-content.yml`** — scheduled data jobs.

### Deploy targets

- **Frontend:** Vercel auto-deploys `apps/web/` on push to main.
- **Backend:** Railway auto-deploys `apps/api/` via Dockerfile on push to main.
- **Migrations:** Manual via `npx supabase db push --project-ref dwdgzfusjsobnixgyzjk`. NOT automated — each migration requires explicit CEO push (or CTO push under explicit CEO autonomy directive). Session 93 applied two migrations this way.
- **MindShift edge function:** `npx supabase functions deploy volaura-bridge-proxy --project-ref awfoqycoltvhamtrsvxk`.

### Secrets

- Railway env: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `EXTERNAL_BRIDGE_SECRET`, `GATEWAY_SECRET`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `NVIDIA_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CEO_CHAT_ID`, Sentry DSN.
- MindShift Supabase edge secrets: `EXTERNAL_BRIDGE_SECRET` (matching), `DODO_API_KEY`, `DODO_WEBHOOK_SECRET`, `VOLAURA_API_URL`.
- Local `.env`: `apps/api/.env` contains everything for local dev. Gitignored. Never committed. Secret prefix auto-detection via `.claude/rules/secrets.md`.

---

## 7. KNOWN GAPS VS IDEAL STATE (SUMMARIZED FROM `AI_Ecosystem_Architecture.docx`)

The strategic brief identifies a target architecture; these are the deltas between it and what actually exists today:

| Gap | Severity | Source |
|---|---|---|
| No LLM golden dataset / eval harness | **P0** | Gemini-SRE section |
| No shadow-testing pipeline for new LLM versions | **P0** | Gemini-SRE section |
| MindShift crisis-keyword deterministic escalation not wired | **P0** | Gemini-Product section |
| Only 2 ADRs exist (009, 010); foundational 8-12 ADR set missing | **P0** | Perplexity ADR section |
| No AGENTS.md manifests per workspace | P1 | Gemini-Constitutional |
| No OpenTelemetry instrumentation on agent spans | P1 | Perplexity observability section |
| No per-PR Reviewer Agent gate (daily swarm only) | P1 | Gemini-Constitutional |
| No prompt semantic versioning | P1 | Gemini-SRE + Perplexity |
| No Auditor Agent running outside CTO hierarchy | P1 | Gemini-Constitutional whistleblower section |
| Data classification matrix (Category A/B/C) not formalised | P1 | Gemini-Product |
| No LangGraph / supervisor graph refactor of the swarm | P2 | Perplexity multi-agent section |
| No event sourcing / CQRS | P2 | Gemini-Constitutional |
| No privacy-preserving logging hashing user payloads | P2 | Gemini-Constitutional |
| No Ethics Advisory Board with institutional veto | P2 | Gemini-Product |
| `packages/` layer (ui, db, config) not extracted | P2 | Perplexity monorepo section |

See `docs/EXECUTION_PLAN.md` for the sequencing of these gaps and assignment of responsibility.

---

## 8. CORE FILE INDEX (FAST NAVIGATION)

| Question | File |
|---|---|
| What exists in prod? | `memory/swarm/SHIPPED.md` |
| Where are we right now? | `.claude/breadcrumb.md` + `memory/context/sprint-state.md` |
| Can we do X? | `docs/ECOSYSTEM-CONSTITUTION.md` + `CLAUDE.md` Article 0 + `docs/CONSTITUTION_AI_SWARM.md` (this layer) |
| Has this bug happened before? | `memory/context/mistakes.md` |
| Does this pattern work? | `memory/context/patterns.md` |
| Who owns this task? | `memory/swarm/agent-roster.md` + `agent-pairings-table.md` |
| What's the DB schema? | `supabase/migrations/` search by table name |
| Which endpoint handles X? | `apps/api/app/routers/` filename = router prefix |
| Full project map? | `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\reference_file_map.md` (this file's navigation sibling) |

---

## REVISION HISTORY

| Version | Date | Change | Author |
|---|---|---|---|
| 1.0 | 2026-04-12 | Initial as-built snapshot after Session 93 infrastructure work (zeus governance + model_router + 2 prod bug fixes + full E2E verification) | Claude Opus 4.6 (CTO-Hands) |
