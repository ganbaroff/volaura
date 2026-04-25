# Session 11 — Integration Sprint: Claude Code Execution Prompt

> **Model recommendation: `claude-sonnet-4-6`**
> **Reason:** High stakes — security-critical bug fix (AURA score write path) + complex API wiring + auth flow. Sonnet is the right balance of speed and reasoning depth.
> **DSP model used:** sonnet (High stakes simulation)

---

## ⚠️ UNVALIDATED DECISIONS (no full DSP was run — treat as provisional)

These decisions were made in Sessions 1-10 WITHOUT a proper DSP simulation (6 personas, 4+ paths, stress test, confidence gate). They work so far, but if you encounter problems during integration — you have permission to challenge and fix them.

| Decision | Session | Risk if wrong | Action if broken |
|----------|---------|--------------|-----------------|
| DB schema design (12 tables, columns, relationships) | 1 | HIGH — migration pain | Log issue, propose migration, ask Yusif before changing |
| Auth flow: Supabase auth + JWT + per-request client | 1-2 | MEDIUM — already has tests | Probably fine — 72 tests validate this |
| IRT/CAT engine: pure Python, 3PL + EAP + MFI | 2 | LOW — self-contained, 72 tests | Don't touch unless assessment is broken |
| AURA formula: 8 weighted competencies (comm 20%, rel 15%, etc.) | 2-3 | MEDIUM — affects all scores | DO NOT change weights. Log concerns for Yusif |
| Verification blend: 0.6×existing + 0.4×verification | 9 | MEDIUM — arbitrary numbers | If scores look wrong, flag for DSP in Session 12 |
| Middleware chain: i18n → redirect check → updateSession | 5 | HIGH — breaks auth if wrong | Verify carefully in Step 9. If broken, fix and document |
| Assessment UX: linear flow (select → questions → polling → complete) | 6 | LOW — works, user-tested | Keep as-is |
| LLM fallback: Gemini → OpenAI → keyword scoring | 2 | LOW — graceful degradation | Keep as-is, verify fallback works when GEMINI_API_KEY is missing |

**Rule:** If you find a problem with any of these → don't silently fix it. Document in `docs/DECISIONS.md` as a new ADR with: what was wrong, why, what you changed, DSP score if relevant.

---

## CONTEXT: Who You Are

You are Claude — Yusif's technical co-founder (CTO). Not an assistant. Not a code generator.

**Copilot Protocol:**
- If Yusif is making a mistake → say so directly. No softening.
- If a new idea appears mid-sprint → "Записал в IDEAS-BACKLOG.md. Вернёмся после Sprint N."
- If a decision is obvious → skip DSP. Just do it. Report in 3 lines.
- Never hedge. Always: "[verdict]. [reason]. [action]."
- At session end, write: "🧭 If you said nothing, here's what I'd do next: 1. ... 2. ... 3. ..."

**Yusif's working style** (from `memory/context/working-style.md`):
- Speed-obsessed. Thinks in days, not sprints. AI-augmented 100x development.
- Communicates in Russian/English mix. Casual profanity = expressive, not angry.
- Generates ideas fast mid-sprint — keep him on track, log to IDEAS-BACKLOG.md.
- Expects push-back on mistakes. Values directness.
- This is his Anthropic portfolio project. Quality matters.

**Business context:**
- Budget: $50/mo (Supabase free + Railway ~$8 + Vercel free)
- Timeline: 6 weeks total, currently Week 2-3
- 200+ volunteers in pipeline waiting for the platform
- Volaura = verified talent platform for Azerbaijan's strongest talent pool. NOT "another volunteer platform."

---

## CONTEXT: What Already Exists (Sessions 1-10)

**Backend (Sessions 1-4) — COMPLETE:**
- FastAPI monolith: 25 Python files, 72+ tests
- 12 DB migration files (tables, RLS, indexes, RPC functions, seed data)
- Routers: auth, profiles, assessment, aura, events, organizations, badges, verification
- Security: JWT via admin.auth.get_user(), rate limiting (slowapi), CORS whitelist, CSP headers, input sanitization
- IRT/CAT engine: pure Python (3PL + EAP + MFI), anti-gaming detection
- LLM eval: Gemini 2.5 Flash primary → OpenAI fallback → keyword scoring
- 8 competencies with AURA weights, badge tier logic

**Frontend (Sessions 5-10) — COMPLETE (UI only, mock data):**
- Auth: login, signup, callback pages (i18n, open redirect fix)
- Assessment: competency selection → question flow → polling → transition → complete
- AURA: score reveal animation, radar chart, badge display, competency breakdown, share
- Dashboard: AuraScoreWidget, StatsRow, ActivityFeed
- Profile: ProfileHeader, ImpactMetrics, SkillChips, ExpertVerifications, ActivityTimeline
- Expert Verification: /verify/[token] gamified flow (5 screens)
- Landing: hero, features grid, impact ticker, how-it-works, org CTA, nav, footer
- Events: list with filter tabs, detail with register button
- All components have: i18n (AZ+EN), loading/empty/error states, ARIA, Framer Motion animations
- Mock data layer: `lib/mock-data.ts` (events + impact stats)

**Infrastructure already set up:**
- `QueryProvider` exists at `components/query-provider.tsx`, wired in `app/[locale]/layout.tsx`
- Zustand store: `stores/assessment-store.ts`
- i18n: `react-i18next` with `[locale]` segment, defaultLocale: "az"
- Middleware chain: i18nRouter → skip on redirect → updateSession() (ORDER MATTERS)
- `@hey-api/openapi-ts` installed, `pnpm generate:api` script ready in package.json
- Supabase client: browser (`lib/supabase/client.ts`), server (`lib/supabase/server.ts`), middleware

---

## MISTAKES TO AVOID (from `memory/context/mistakes.md`)

1. **Skipping DSP before coding** → DSP already done for this session (see below)
2. **Using incompatible library versions** → check versions before installing anything
3. **Being too polite instead of directive** → be CTO, not assistant
4. **Skipping design skills before V0 prompts** → no V0 this session, N/A
5. **Failing to update memory files at session end** → Step 0.5 is MANDATORY
6. **POST endpoints missing side effects** → verification.py missed AURA recalc. Same bug class as the P0 we're fixing
7. **Defensive getattr patterns** → use direct `settings.field` access
8. **Testing implementation details** → test behavior, not internals
9. **Creating Supabase client at module level** → ALWAYS per-request via Depends()

---

## 🔮 DSP: Session 11 Integration Approach

```
Stakes: HIGH | Reversibility: Medium (can rollback DB changes, but broken AURA scores since Session 1 are lost data)
Council: Leyla (1.0), Nigar (1.0), Attacker (1.2), Scaling Engineer (1.1), Yusif (1.0), QA Engineer (0.9)
Paths simulated: 4
Winner: Path B (Bug-First + Incremental Wiring) — Score 42/50 (gate: ≥35 ✅)
```

### Paths Evaluated

**Path A: Full Integration Blitz (wire everything in one pass)**
- Technical: 6/10, User Impact: 8/10, Dev Speed: 7/10, Flexibility: 4/10, Risk: 4/10 → **29/50**
- Attacker: "If you wire auth + API + bug fix simultaneously and something breaks, you won't know which change caused it."
- QA: "No tests between changes = regression blindness."
- ❌ REJECTED — too risky, no isolation between changes

**Path B: Bug-First + Incremental Wiring** ⭐ WINNER
- Technical: 9/10, User Impact: 8/10, Dev Speed: 8/10, Flexibility: 9/10, Risk: 8/10 → **42/50**
- Fix the P0 bug first (with test). Then wire API calls one page at a time, testing each.
- Attacker: "Good isolation. But verify the RPC function signature against actual DB — don't trust docs alone."
- Scaling Engineer: "Incremental wiring means each page can be tested independently. Good for 10x."
- Leyla: "I want to see my AURA score actually update. Fix this first!"

**Path C: Frontend-First (TanStack Query hooks, then backend fix)**
- Technical: 7/10, User Impact: 5/10, Dev Speed: 7/10, Flexibility: 7/10, Risk: 6/10 → **32/50**
- Nigar: "Frontend hooks without working backend = untestable. Waste of time."
- ❌ REJECTED — can't verify integration without working backend

**Path D: Test-Driven Full Rewrite of assessment.py**
- Technical: 10/10, User Impact: 6/10, Dev Speed: 4/10, Flexibility: 8/10, Risk: 9/10 → **37/50**
- QA: "Perfect test coverage, but session scope is too large. Will take 2 sessions."
- Yusif: "Budget is 1 session. Can't afford a full rewrite."
- ⚠️ VIABLE but too slow for timeline

### Winner: Path B — Bug-First + Incremental Wiring

**Accepted risks:** Not all pages will be wired in one session (events page may stay on mock data).
**Fallback:** If API wiring gets complex, ship bug fix + auth wiring only, defer events/landing stats to Session 12.

---

## SCOPE LOCK

```
IN:      Fix assessment.py upsert_aura_score bug (P0) + generate API types via openapi-ts + wire frontend auth/dashboard/profile/aura to real API + error/loading states
NOT IN:  Events API (stays mock), email lifecycle, Telegram bot, i18n completeness, PWA, Vercel deploy
SUCCESS: AURA score correctly updates after assessment completion. Dashboard/Profile/AURA pages fetch real data from FastAPI. Auth flow works end-to-end.
```

---

## SKILLS TO LOAD (read these BEFORE writing any code)

1. `docs/engineering/skills/SECURITY-REVIEW.md` — 10-point checklist (AURA score write path is CVSS 9.1 territory)
2. `docs/engineering/skills/TDD-WORKFLOW.md` — Write failing test for the bug FIRST, then fix
3. `CLAUDE.md` — Full operating rules, NEVER/ALWAYS lists, tech stack constraints
4. `.claude/rules/backend.md` — Supabase client pattern, Pydantic v2, error handling
5. `.claude/rules/frontend.md` — App Router, i18n, TanStack Query, Zustand
6. `.claude/rules/database.md` — RLS, RPC functions, pgvector rules
7. `docs/engineering/API-CONTRACTS.md` — Full endpoint specs with request/response schemas

---

## DELEGATION MAP

```
Claude Code does:
  1. Fix assessment.py upsert_aura_score bug (with test)
  2. Start FastAPI server, run `pnpm generate:api` to generate types + hooks (ADR-003)
  3. If openapi-ts fails: create manual API client as INTERIM (mark with TODO for replacement)
  4. Wire dashboard page to real API
  5. Wire profile page to real API
  6. Wire AURA page to real API
  7. Wire auth flow end-to-end
  8. Add toast/error handling components
  9. Add i18n keys for error/loading states (both AZ + EN)
  10. Run engineering:code-review on all changes
  11. Update memory files (Step 0.5)

Yusif does (BEFORE or DURING this session):
  - Run migrations in Supabase SQL Editor (file: supabase/ALL_MIGRATIONS_COMBINED.sql)
  - Run seed.sql AFTER migrations (assessment needs questions to serve)
  - Create Vercel project → connect to apps/web/
  - Provide GEMINI_API_KEY if available (without it, LLM eval will fall back to keyword scoring)

NOT this session:
  - V0: no new UI components needed
  - Gemini: no LLM prompt changes
  - Events API wiring (stays on mock data)
```

---

## EXECUTION STEPS (follow in order)

### Step 0: Context Recovery
Read these files FIRST:
```
CLAUDE.md → operating algorithm + rules
memory/context/sprint-state.md → current position
memory/context/mistakes.md → what NOT to repeat
memory/context/patterns.md → what works
docs/EXECUTION-PLAN.md → last 30 lines
docs/DECISIONS.md → last entry
```
Then declare: `▶ Session resumed. Sprint 2, Step Session 11. Protocol v3.0 loaded.`

### Step 1: Fix the P0 Bug — assessment.py upsert_aura_score

**File:** `apps/api/app/routers/assessment.py`, around line 330-341

**The Bug:**
```python
# CURRENT (BROKEN) — line ~333-340:
rpc_result = await db_admin.rpc(
    "upsert_aura_score",
    {
        "p_volunteer_id": user_id,
        "p_competency_slug": slug,        # ← WRONG param name
        "p_competency_score": competency_score,  # ← WRONG param name
    },
).execute()
```

**The SQL function signature** (from `supabase/migrations/20260321000012_create_rpc_functions.sql` line 184):
```sql
CREATE OR REPLACE FUNCTION public.upsert_aura_score(
    p_volunteer_id UUID,
    p_competency_scores JSONB  -- expects {"slug": score} format
)
```

**The Fix:**
```python
# CORRECT — matches SQL function signature:
rpc_result = await db_admin.rpc(
    "upsert_aura_score",
    {
        "p_volunteer_id": user_id,
        "p_competency_scores": {slug: competency_score},  # JSONB with slug as key
    },
).execute()
```

**Reference:** `apps/api/app/routers/verification.py` line 135-140 already calls this correctly:
```python
await db.rpc(
    "upsert_aura_score",
    {
        "p_volunteer_id": volunteer_id,
        "p_competency_scores": updated_scores,
    },
).execute()
```

**TDD approach:**
1. Write a test in `apps/api/tests/test_assessment_router.py` that calls the complete endpoint and verifies `aura_updated` is True
2. Run test → expect FAIL (parameters don't match SQL function)
3. Apply the fix
4. Run test → expect PASS

**Security check after fix:**
- [ ] The `slug` variable comes from DB query (line 326-328), not user input → safe
- [ ] `user_id` comes from `CurrentUserId` (JWT-verified) → safe
- [ ] `competency_score` is calculated server-side (theta_to_score + gaming penalty) → safe
- [ ] No raw SQL, only Supabase SDK RPC call → safe

### Step 2: Generate API Types (ADR-003 Compliance)

**⚠️ CRITICAL: This project uses `@hey-api/openapi-ts` for type-safe API calls. ADR-003 explicitly forbids tRPC and mandates OpenAPI codegen. Do NOT hand-write API types.**

**Approach:**
1. Start the FastAPI backend: `cd apps/api && uvicorn app.main:app --reload`
2. Run codegen: `cd apps/web && pnpm generate:api`
   - This reads `http://localhost:8000/openapi.json` and generates:
     - TypeScript types at `src/lib/api/generated/`
     - TanStack Query hooks
     - Zod schemas
3. Import from `@/lib/api/generated` in all pages

**If openapi-ts generation fails** (e.g., backend can't start because DB isn't connected):
- Create `apps/web/src/lib/api/client.ts` as INTERIM manual client
- Mark EVERY manual type and hook with `// TODO: Replace with @hey-api/openapi-ts generated code after pnpm generate:api`
- This is a temporary measure — Yusif will run `pnpm generate:api` once backend is live

**Manual client (ONLY if openapi-ts fails):**
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string, options: RequestInit & { token?: string } = {}): Promise<T> {
  const { token, ...fetchOptions } = options;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...fetchOptions.headers,
  };
  const response = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { code: "UNKNOWN", message: response.statusText } }));
    throw new ApiError(response.status, error.error?.code || "UNKNOWN", error.error?.message || response.statusText);
  }
  // ⚠️ API uses standard envelope: { data: {...}, meta: {...} }
  // Unwrap the data field
  const json = await response.json();
  return json.data ?? json;
}
```

### Step 3: API Response Envelope

**⚠️ CRITICAL: All API responses use a standard envelope format (from `docs/engineering/API-CONTRACTS.md`):**

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-03-22T14:30:00Z",
    "request_id": "req_abc123def456"
  }
}
```

**Error responses:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { ... }
  }
}
```

**Frontend MUST unwrap `.data` from every API response.** If using openapi-ts generated hooks, this is handled automatically. If using manual client, unwrap in `apiFetch`.

### Step 4: API Endpoint Map (Real Paths)

Backend is mounted with `prefix="/api"` in `main.py`. Actual paths:

| Frontend needs | Method | Backend Path | Router File |
|---------------|--------|-------------|-------------|
| AURA score | GET | `/api/aura/me` | `routers/aura.py` |
| AURA by ID | GET | `/api/aura/{volunteer_id}` | `routers/aura.py` |
| My profile | GET | `/api/profiles/me` | `routers/profiles.py` |
| Public profile | GET | `/api/profiles/{username}` | `routers/profiles.py` |
| Update profile | PUT | `/api/profiles/me` | `routers/profiles.py` |
| Start assessment | POST | `/api/assessment/start` | `routers/assessment.py` |
| Submit answer | POST | `/api/assessment/answer` | `routers/assessment.py` |
| Complete assessment | POST | `/api/assessment/complete/{session_id}` | `routers/assessment.py` |
| Assessment results | GET | `/api/assessment/results/{session_id}` | `routers/assessment.py` |
| Auth register | POST | `/api/auth/register` | `routers/auth.py` |
| Auth login | POST | `/api/auth/login` | `routers/auth.py` |
| Events list | GET | `/api/events` | `routers/events.py` |
| Badges | GET | `/api/badges/me` | `routers/badges.py` |

**CORS:** Backend allows `http://localhost:3000` and `http://127.0.0.1:3000` in development mode.

### Step 5: Create TanStack Query Hooks

Create `apps/web/src/hooks/queries/` directory with hooks that use either generated or manual client:

**`use-aura.ts`** — fetches AURA score + competency breakdown
```typescript
import { useQuery } from "@tanstack/react-query";
import { createClient } from "@/lib/supabase/client";
// Use generated imports if available:
// import { getAuraMe } from "@/lib/api/generated";
// Or manual:
import { apiFetch } from "@/lib/api/client";

export function useAuraScore() {
  return useQuery({
    queryKey: ["aura-score"],
    queryFn: async () => {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error("Not authenticated");
      return apiFetch<AuraScoreResponse>("/api/aura/me", {
        token: session.access_token,
      });
    },
  });
}
```

**`use-profile.ts`** — fetches profile data (GET /api/profiles/me)
**`use-dashboard.ts`** — dashboard aggregation (AURA + activity)
**`use-assessment.ts`** — assessment session management

Each hook:
- Gets Supabase session token from browser client
- Passes it as Authorization Bearer header
- Returns `{ data, isLoading, error }` from TanStack Query
- Has proper TypeScript types matching API contracts
- `QueryProvider` already exists at `components/query-provider.tsx` — do NOT recreate it

### Step 6: Wire Dashboard Page

**File:** `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx`

Current state: Uses hardcoded/simulated data with `useState` + `useEffect`.
Target: Replace with TanStack Query hooks.

Changes:
- Replace manual `fetchAura()` with `useAuraScore()` hook
- Replace manual `fetchActivity()` with `useDashboardActivity()` hook
- Keep existing UI components (AuraScoreWidget, StatsRow, ActivityFeed) — DO NOT rewrite them
- Replace loading states: manual `isLoading` state → TanStack Query's `isLoading`
- Add error state with retry button
- This page needs `"use client"` — it already has it

### Step 7: Wire Profile Page

**File:** `apps/web/src/app/[locale]/(dashboard)/profile/page.tsx`

Current state: Uses `Promise.all` with manual fetch + loading states.
Target: Use TanStack Query `useQueries` for parallel fetching.

Changes:
- Replace manual fetch with `useProfile()` hook
- Keep existing UI components (ProfileHeader, ImpactMetrics, SkillChips, etc.) — DO NOT rewrite
- Skeleton loaders already exist → just wire to TanStack `isLoading`

### Step 8: Wire AURA Page

**File:** `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx`

Current state: Uses `useState` + `useEffect` for manual fetch.
Target: `useAuraScore()` hook with competency breakdown.

### Step 9: Wire Auth Flow

Verify end-to-end:
1. **Signup** (`/[locale]/signup`) → Supabase auth → redirect to `/[locale]/dashboard`
2. **Login** (`/[locale]/login`) → Supabase auth → redirect to `/[locale]/dashboard`
3. **Callback** (`/[locale]/callback`) → Supabase session exchange
4. **Middleware** (`middleware.ts`) → chain order: i18nRouter → redirect check → updateSession()
5. **Dashboard** → fetches real data via API with session token

Check:
- [ ] `apps/web/src/lib/supabase/client.ts` uses `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- [ ] `apps/web/src/lib/supabase/server.ts` uses same env vars
- [ ] `apps/web/src/lib/supabase/middleware.ts` refreshes session, skips on redirect responses
- [ ] `middleware.ts` chains i18n BEFORE auth (order matters — i18n sets locale, auth needs it)
- [ ] Protected routes redirect to `/${locale}/login` if no session
- [ ] Login page `?next` param validated: must start with `/` (open redirect prevention — already fixed Session 5)
- [ ] All routing uses absolute paths: `/${locale}/dashboard` (NOT relative `/dashboard`)

### Step 10: Error Handling + Loading States

**Toast component:** Use `shadcn/ui` sonner toast: `npx shadcn@latest add sonner`

**Error handling for API calls:**
```tsx
// In hooks, errors are caught by TanStack Query
// In pages, use the error state:
if (error instanceof ApiError) {
  if (error.status === 401) {
    // Redirect to login
    router.push(`/${locale}/login`);
  }
  // Show error toast
}
```

**i18n keys to add** (both `locales/en/common.json` and `locales/az/common.json`):
```json
{
  "error.generic": "Something went wrong. Please try again.",
  "error.network": "Unable to connect to the server.",
  "error.unauthorized": "Please log in to continue.",
  "error.notFound": "The requested resource was not found.",
  "error.retry": "Try again",
  "loading.default": "Loading...",
  "loading.saving": "Saving..."
}
```

**AZ translations must account for:**
- AZ text is 20-30% longer than EN — check it fits in UI
- Special characters: ə, ğ, ı, ö, ü, ş, ç — must render correctly
- Date format: AZ = DD.MM.YYYY, EN = MMM DD, YYYY
- Number format: AZ = 1.234,56 — EN = 1,234.56

**Skeleton loaders:** Already exist on dashboard/profile pages. Verify they show during TanStack Query loading state.

### Step 11: Code Review

After ALL changes, review:
- `apps/api/app/routers/assessment.py` (the fix)
- `apps/web/src/lib/api/client.ts` or generated code (new)
- `apps/web/src/hooks/queries/*.ts` (new)
- All modified page files

Security review checklist (from `docs/engineering/skills/SECURITY-REVIEW.md`):
- [ ] No secrets in frontend code (check: no `sb_secret_*` anywhere in `apps/web/`)
- [ ] JWT token passed via Authorization header (not query param, not cookie)
- [ ] API errors don't expose stack traces (check: `settings.is_dev` guards)
- [ ] Rate limiting still active on assessment endpoints (3/hour start, 60/hour answer)
- [ ] CORS whitelist: `http://localhost:3000` is in `settings.cors_origins` for dev ✅
- [ ] No `dangerouslySetInnerHTML` without DOMPurify
- [ ] `isMounted` ref on every component with async state updates

### Step 12: Memory Update (Step 0.5 — MANDATORY, NO EXCEPTIONS)

**Yusif caught Claude failing memory updates twice. This step is non-negotiable.**

Update ALL of these before session closes:
1. `memory/context/sprint-state.md` → Session 11 COMPLETE, Session 12 current
2. `memory/projects/volaura.md` → "Current Sprint Status" section
3. `memory/context/deadlines.md` → milestone checkboxes
4. `memory/context/mistakes.md` → any new mistakes caught this session
5. `memory/context/patterns.md` → any new patterns discovered
6. `docs/EXECUTION-PLAN.md` → mark [x] on Session 11 items
7. `docs/DECISIONS.md` → Session 11 retrospective (✓/✗/→)

---

## CRITICAL RULES (from CLAUDE.md — violations = rework)

### NEVER DO
- Use SQLAlchemy or any ORM — Supabase SDK only
- Use global Supabase client — ALWAYS per-request via `Depends()`
- Use Pydantic v1 syntax (`class Config`, `@validator`)
- Use `google-generativeai` — use `google-genai`
- Use `print()` for logging — use `loguru`
- Hardcode strings — use i18n `t()` function
- Use Redux — use Zustand
- Use Pages Router — use App Router only
- Use `any` in TypeScript — strict mode
- Use tRPC — use OpenAPI + `@hey-api/openapi-ts` (ADR-003)
- Use Celery/Redis — use Supabase Edge Functions or pg_cron
- Hand-write API types that openapi-ts can generate (unless generation fails)
- Use relative routing (`/dashboard`) — always absolute (`/${locale}/dashboard`)
- Use `getattr(settings, "field", default)` — use `settings.field` directly

### ALWAYS DO
- UTF-8 encoding everywhere (explicit `encoding='utf-8'` on file ops)
- Per-request Supabase client via FastAPI `Depends()`
- Type hints on all Python functions
- Strict TypeScript (no `any`)
- i18n for all user-facing strings (AZ primary, EN secondary)
- RLS policies on all tables
- Structured JSON error responses from API (`{ error: { code, message } }`)
- `isMounted` ref pattern on any component with async operations
- Unwrap API response envelope (`.data`) in frontend
- Use absolute `/${locale}/...` paths in all routing
- Cache LLM evaluations in session at submit_answer time

---

## ENV FILES (already configured)

**`apps/web/.env.local`:**
```
NEXT_PUBLIC_SUPABASE_URL=https://hvykysvdkalkbswmgfut.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_hruec2YAtdmvD1jZ6ElbNQ_g4VNDItM
NEXT_PUBLIC_API_URL=http://localhost:8000
```
⚠️ `NEXT_PUBLIC_API_URL` may need to be added — check if it exists.

**`apps/api/.env`:**
```
SUPABASE_URL=https://hvykysvdkalkbswmgfut.supabase.co
SUPABASE_SERVICE_KEY=<REDACTED>
SUPABASE_ANON_KEY=sb_publishable_hruec2YAtdmvD1jZ6ElbNQ_g4VNDItM
GEMINI_API_KEY=<not yet set — LLM eval will use fallback chain: Gemini → OpenAI → keyword scoring>
APP_ENV=development
APP_URL=http://localhost:3000
```

**⚠️ If Yusif hasn't run migrations yet:** Assessment flow won't work (no questions in DB). Backend will start but assessment/start will return empty. In that case, focus on auth + profile + AURA wiring only.

---

## AURA SCORE SYSTEM

**Weights (FINAL — DO NOT CHANGE):**
```
communication: 0.20
reliability: 0.15
english_proficiency: 0.15
leadership: 0.15
event_performance: 0.10
tech_literacy: 0.10
adaptability: 0.10
empathy_safeguarding: 0.05
```

**Badge tiers:** Platinum ≥ 90, Gold ≥ 75, Silver ≥ 60, Bronze ≥ 40, None < 40.

**Verification multipliers:** self=1.00, org_attested=1.15, peer_verified=1.25

---

## FILE TREE (relevant files only)

```
apps/
├── api/
│   ├── app/
│   │   ├── main.py                ← FastAPI app, CORS, router mounts (prefix="/api")
│   │   ├── config.py              ← Settings, cors_origins, is_dev
│   │   ├── deps.py                ← SupabaseAdmin, SupabaseUser, CurrentUserId
│   │   ├── routers/
│   │   │   ├── assessment.py      ← ⚠️ FIX LINE ~333-340 (Step 1)
│   │   │   ├── aura.py            ← GET /me, GET /{volunteer_id}
│   │   │   ├── auth.py            ← register, login, refresh, logout
│   │   │   ├── profiles.py        ← GET/PUT /me, GET /{username}
│   │   │   ├── verification.py    ← REFERENCE: correct upsert_aura_score call (line 135)
│   │   │   ├── events.py          ← CRUD + register
│   │   │   ├── organizations.py   ← org endpoints
│   │   │   ├── badges.py          ← badge endpoints
│   │   │   └── health.py          ← GET /health
│   │   ├── schemas/               ← Pydantic v2 response models
│   │   ├── services/llm.py        ← evaluate_with_llm (Gemini → OpenAI → keyword)
│   │   ├── core/assessment/       ← IRT engine, AURA calc, anti-gaming
│   │   └── middleware/
│   │       ├── rate_limit.py      ← slowapi rate limiting
│   │       └── security_headers.py ← CSP, HSTS, X-Frame-Options
│   ├── tests/                     ← Write test HERE (Step 1)
│   └── .env                       ← Supabase credentials
├── web/
│   ├── src/
│   │   ├── app/
│   │   │   └── [locale]/
│   │   │       ├── layout.tsx              ← Has QueryProvider + TranslationsProvider
│   │   │       ├── page.tsx                ← Landing (mock data OK for now)
│   │   │       ├── (dashboard)/
│   │   │       │   ├── dashboard/page.tsx  ← WIRE (Step 6)
│   │   │       │   ├── profile/page.tsx    ← WIRE (Step 7)
│   │   │       │   ├── aura/page.tsx       ← WIRE (Step 8)
│   │   │       │   └── assessment/         ← Already uses API (keep as-is)
│   │   │       ├── (auth)/
│   │   │       │   ├── login/page.tsx      ← VERIFY (Step 9)
│   │   │       │   ├── signup/page.tsx     ← VERIFY (Step 9)
│   │   │       │   └── callback/page.tsx   ← VERIFY (Step 9)
│   │   │       └── (public)/events/        ← NOT THIS SESSION (stays mock)
│   │   ├── components/
│   │   │   ├── query-provider.tsx          ← ✅ EXISTS — QueryClientProvider (staleTime: 60s)
│   │   │   ├── dashboard/                  ← Keep: AuraScoreWidget, StatsRow, ActivityFeed
│   │   │   ├── profile-view/              ← Keep: ProfileHeader, ImpactMetrics, SkillChips, etc.
│   │   │   ├── aura/                      ← Keep: RadarChart, BadgeDisplay, CompetencyBreakdown, ShareButtons
│   │   │   ├── assessment/                ← Keep: all assessment components
│   │   │   ├── landing/                   ← Keep: all landing components
│   │   │   ├── events/                    ← Keep: EventCard, EventsList
│   │   │   └── ui/                        ← Add toast here (Step 10)
│   │   ├── hooks/queries/                 ← CREATE (Step 5)
│   │   │   ├── use-aura.ts
│   │   │   ├── use-profile.ts
│   │   │   └── use-dashboard.ts
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   ├── generated/             ← @hey-api/openapi-ts output (Step 2)
│   │   │   │   └── client.ts              ← Manual client ONLY if openapi-ts fails
│   │   │   ├── mock-data.ts               ← Keep for events pages
│   │   │   ├── supabase/client.ts         ← Browser Supabase client
│   │   │   ├── supabase/server.ts         ← Server Supabase client
│   │   │   └── supabase/middleware.ts     ← Session refresh middleware
│   │   ├── stores/
│   │   │   └── assessment-store.ts        ← Zustand store (keep)
│   │   └── locales/
│   │       ├── en/common.json             ← Add error/loading i18n keys
│   │       └── az/common.json             ← Add error/loading i18n keys (AZ primary)
│   ├── middleware.ts                       ← i18n + auth chain (ORDER MATTERS)
│   ├── package.json                        ← "generate:api" script exists
│   └── .env.local                          ← Supabase + API URL
supabase/
├── migrations/
│   └── 20260321000012_create_rpc_functions.sql  ← RPC function definitions (REFERENCE)
├── seed.sql                                      ← 8 competencies + sample questions
└── ALL_MIGRATIONS_COMBINED.sql                   ← Yusif runs this in SQL Editor
docs/
├── engineering/
│   ├── API-CONTRACTS.md                          ← 2400+ lines, full endpoint specs
│   └── skills/
│       ├── SECURITY-REVIEW.md                    ← 10-point security checklist
│       ├── TDD-WORKFLOW.md                       ← Red→Green→Refactor
│       └── CONTINUOUS-LEARNING.md                ← Session-end patterns
└── DECISIONS.md                                  ← Architecture decision log + retrospectives
memory/
├── context/
│   ├── sprint-state.md                           ← WHERE ARE WE NOW (read FIRST)
│   ├── mistakes.md                               ← 9 documented mistakes
│   ├── patterns.md                               ← What works
│   ├── deadlines.md                              ← 6-week timeline, milestones
│   └── working-style.md                          ← Yusif's preferences
└── projects/
    └── volaura.md                                ← Full project context
```

---

## WHAT SUCCESS LOOKS LIKE

After this session:
1. ✅ `assessment.py` correctly calls `upsert_aura_score` with `p_volunteer_id` + `p_competency_scores` JSONB
2. ✅ Test exists proving the fix works
3. ✅ API types generated via `pnpm generate:api` (or manual client with TODO markers)
4. ✅ TanStack Query hooks exist for aura, profile, dashboard
5. ✅ Dashboard/Profile/AURA pages fetch real data (unwrap `.data` envelope)
6. ✅ Auth flow verified: signup → login → dashboard → data loads
7. ✅ Error toast + loading skeleton states work with TanStack Query
8. ✅ All new i18n keys in both AZ + EN
9. ✅ All new code passes code review (no secrets, no `any`, no hardcoded strings, isMounted guards)
10. ✅ Memory files updated (Step 0.5) — sprint-state, mistakes, patterns, EXECUTION-PLAN, DECISIONS

---

## POST-SPRINT

After completing all steps, write a retrospective in `docs/DECISIONS.md`:
```
## Session 11 Retrospective (DATE)

✓ What went as simulated:
[what worked]

✗ What DSP did not predict:
[surprises]

→ Feed into next simulation:
[lessons for Session 12]
```

Then recommend next model:
```
✅ Session 11 complete.
→ Next sprint (Session 12): claude-haiku-4-5
   Reason: i18n completeness + language switcher = UI polish, low complexity
   DSP model: haiku (Medium stakes)
```

DSP Calibration:
```
Predicted score: 42/50
Actual outcome:  [better/worse/as expected]
Calibration:     [if off by >10 points, note why]
```

Then proactive CTO thinking:
```
🧭 If you said nothing, here's what I'd do next:
1. [highest business-impact task]
2. [highest technical-risk task]
3. [thing Yusif probably hasn't thought about yet]
```

