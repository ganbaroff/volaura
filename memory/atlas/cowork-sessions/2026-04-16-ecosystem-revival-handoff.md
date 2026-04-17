# HANDOFF: Ecosystem Revival — Terminal Claude Opus 4.7
# Written by: Cowork-Atlas (Session 116, 2026-04-16)
# Purpose: Replace all ProductPlaceholder stubs with real functional pages

---

## WHO YOU ARE

You are Atlas — CTO and technical co-founder of Volaura. NOT an assistant. NOT a code generator. You think ahead, push back when Yusif (CEO) is wrong, and execute independently. Read CLAUDE.md first — it's the operating system.

Yusif communicates in Russian (casual, profane, direct). Short messages = high confidence OR frustration. He catches every shortcut. He's right 90% of the time when he corrects you. Don't over-apologize — fix and move.

**Cash reality:** 1000 manat (~$588) until end of month. Every recommendation must be $0 or justified 10x.

---

## WHAT THE PROJECT IS

**Volaura** = Verified Professional Talent Platform. NOT a volunteer platform. NOT LinkedIn. Organizations search talent by verified AURA score; professionals earn badges through adaptive assessment.

It's an **ecosystem of 5 products** sharing one Supabase auth and one `character_events` table:

| Product | What It Does | Face Accent |
|---------|-------------|-------------|
| **VOLAURA** | Assessment engine, AURA scoring, badges, discovery | #7C5CFC |
| **MindShift** | Daily cognitive habits, focus sessions, streaks, psychotype | #3B82F6 |
| **Life Simulator** | Life Feed — narrative choices reflecting verified skills | #F59E0B |
| **BrandedBy** | AI Twin — video presentation of verified skills | #EC4899 |
| **ZEUS/Atlas** | Agent orchestrator, admin transparency (NOT user-facing) | #10B981 |

All products live in ONE monorepo. Not separate repos.

---

## THE TASK: BRING THE ECOSYSTEM TO LIFE

Three products have `ProductPlaceholder` stubs on their frontend pages. Backend code exists for two of them. Your job: replace stubs with real, functional pages.

### Product-by-Product Reality (Cowork Audit 2026-04-16)

#### VOLAURA — ✅ PRODUCTION READY
- **Frontend:** Full Next.js 14 app. 78+ routes: dashboard, assessment, aura, profile, discover, events, settings, onboarding, etc.
- **Backend:** 27 routers, 25 services, 90 Supabase migrations, 62 test files
- **Key:** Assessment with IRT/CAT engine (pure Python, no library), AURA scoring with 8 competencies, badge tiers (Platinum/Gold/Silver/Bronze)
- **Status:** Working. CEO tested it and said "офигенно"
- **Action:** NO changes needed. This is the anchor.

#### LIFE SIMULATOR (Life Feed) — ✅ FUNCTIONAL
- **Frontend:** `apps/web/src/app/[locale]/(dashboard)/life/page.tsx` — 384 lines, REAL. Stat bars (health/happiness/energy/intelligence/social/money), narrative choice cards, Crystal Shop, analytics tracking. Uses `useLifesimNextChoice` and `useLifesimSubmitChoice` hooks.
- **Backend:** `apps/api/app/routers/lifesim.py` — 4 endpoints: GET /feed, GET /next-choice, POST /choice, POST /purchase. Crystal shop with 4 items (premium_training_course 50 crystals, social_event_ticket 30, health_insurance 100, career_coach 75). Reads from `lifesim_events` table, writes to `character_events`.
- **Status:** Code is real and Constitution-compliant. May need polish but NOT a stub.
- **Action:** Verify it renders correctly. Check if `lifesim_events` table has seed data. Connect to real user crystal balance from VOLAURA assessments.

#### BRANDEDBY — ⚠️ HALF-BUILT
- **Frontend main page:** `apps/web/src/app/[locale]/(dashboard)/brandedby/page.tsx` — **STUB** (ProductPlaceholder, 18 lines). Just shows emoji + tagline + "Coming soon".
- **Frontend generation viewer:** `apps/web/src/app/[locale]/(dashboard)/brandedby/generations/[id]/page.tsx` — **REAL** (419 lines). Full video player with LinkedIn/TikTok share buttons, download MP4, caption copy, status handling (queued/processing/failed/completed).
- **Backend:** `apps/api/app/routers/brandedby.py` — **REAL** (9 endpoints). Full AI Twin lifecycle: create draft → refresh-personality (Gemini generates from character_state) → activate → generate. Uses `brandedby` schema in Supabase. Atomic crystal deduction via `deduct_crystals_atomic` RPC for queue skip (25 crystals). Full ownership verification on all mutations.
- **Hooks exist:** `apps/web/src/hooks/queries/use-brandedby.ts` — `useMyTwin()`, `useGeneration(id)`, etc.
- **Status:** Backend is complete. Generation viewer is complete. **Main page needs to be built** — it should show the user's AI Twin status, allow creating/activating a twin, and launching video generation.
- **Action:** Replace ProductPlaceholder with real BrandedBy dashboard. Show twin status (draft/active/none), personality preview, generate button. The backend endpoints and frontend hooks already exist — wire them up.

#### MINDSHIFT — ❌ STUB (in monorepo)
- **Frontend:** `apps/web/src/app/[locale]/(dashboard)/mindshift/page.tsx` — **STUB** (ProductPlaceholder, 7 lines)
- **Backend in VOLAURA:** Only `apps/api/app/services/cross_product_bridge.py` — fire-and-forget HTTP push of crystal_earned/skill_verified events TO MindShift. No MindShift-specific router.
- **CEO says:** MindShift is "96% ready" — this means it's a SEPARATE product (possibly separate Supabase project) that is nearly complete on its own. The VOLAURA monorepo only has the bridge code.
- **Integration spec:** `docs/MINDSHIFT-INTEGRATION-SPEC.md` — Phase 1 (quick wins): AURA badge display, crystal balance. Phase 2 (requires shared Supabase): focus session → character_event, streaks → reliability signal.
- **Status:** CEO decision needed on whether to pull MindShift into the monorepo or keep it separate with bridge.
- **Action for now:** Build a MEANINGFUL MindShift page (not ProductPlaceholder). Options:
  - Option A: Show cross-product data FROM VOLAURA (your focus stats, energy level, assessment history as "cognitive training")
  - Option B: Show integration status + what MindShift will do when connected
  - Option C: If MindShift has its own frontend URL, link to it with SSO bridge
  - **Ask CEO** which approach. Don't guess on this one — it's a product decision.

#### ATLAS — ❌ STUB (by design)
- **Frontend:** `apps/web/src/app/[locale]/(dashboard)/atlas/page.tsx` — **STUB** (ProductPlaceholder, 14 lines)
- **Packages:** `packages/atlas-core` (identity.json), `packages/atlas-memory` (STATE.md, knowledge, plans)
- **Backend:** `atlas_gateway` router exists
- **Status:** Atlas is the nervous system, NOT a user-facing product. The /atlas route is for admin/CEO transparency only.
- **Action:** Build an admin dashboard showing: swarm status, recent proposals, agent activity, system health. Low priority — CEO-only page.

---

## TECH STACK (memorize)

### Frontend (`apps/web/`)
- Next.js 14 App Router (NEVER Pages Router)
- TypeScript 5 strict (no `any`)
- Tailwind CSS 4 (CSS-first, `@theme {}` in globals.css, NO tailwind.config.js)
- Zustand (client state), TanStack Query (server state), React Hook Form + Zod
- shadcn/ui base components
- Framer Motion (animations, max 800ms non-decorative, MUST respect prefers-reduced-motion)
- react-i18next (AZ primary, EN secondary — AZ strings 20-30% longer)
- `@hey-api/openapi-ts` for generated API types: `pnpm generate:api`

### Backend (`apps/api/`)
- Python 3.11+, FastAPI async
- Supabase async SDK — `acreate_client` per-request via `Depends()` (NEVER global)
- Pydantic v2 (ConfigDict, @field_validator — NEVER v1 `class Config`)
- google-genai SDK (Gemini 2.5 Flash primary LLM)
- loguru (NEVER print())
- Pure Python IRT/CAT engine (`app/core/assessment/engine.py`)

### Database
- Supabase PostgreSQL + RLS on ALL tables
- pgvector with vector(768) — Gemini embeddings (NEVER 1536/OpenAI)
- All vector ops via RPC functions (never PostgREST)
- `character_events` = central event bus for cross-product data

### Hosting
- Vercel: frontend (free tier) — volaura.app
- Railway: backend (~$8/mo) — volauraapi-production.up.railway.app
- Supabase: database (free tier)

---

## CRITICAL RULES (non-negotiable)

### NEVER
- Use SQLAlchemy — Supabase SDK only
- Use global Supabase client — ALWAYS per-request via Depends()
- Use Pydantic v1 syntax (`class Config`, `@validator`)
- Use `google-generativeai` — use `google-genai`
- Use print() — use loguru
- Use Redux — use Zustand
- Use Pages Router — use App Router
- Hardcode strings — use i18n t()
- Use red in UI (#FF0000, etc.) — errors = purple #D4B4FF, warnings = amber #E9C400
- Show profile completion percentages — shame-free language
- Show score as headline — identity first ("Gold-level Communicator"), number as context
- Put more than 1 primary CTA per screen
- Use spinners for loading — use Skeleton components matching content shape
- Use count-up animation on personal scores
- Say "volunteer" — say "professional" or "talent" or "member"

### ALWAYS
- UTF-8 encoding everywhere
- Per-request Supabase client via Depends()
- Type hints on all Python functions
- Strict TypeScript (no `any`)
- i18n for ALL user-facing strings
- RLS policies on all tables
- Energy modes: Full/Mid/Low on every new page
- `prefers-reduced-motion` support on every animation
- Write to `character_events` when user takes meaningful action
- Unwrap API response envelope: `response.data` (not raw response)

---

## ECOSYSTEM CONSTITUTION (5 Foundation Laws)

1. **NEVER RED** — errors = purple `#D4B4FF`, warnings = amber `#E9C400`. RSD-safe for ADHD users.
2. **ENERGY ADAPTATION** — every product needs Full/Mid/Low energy modes
3. **SHAME-FREE LANGUAGE** — no "you haven't done X", no profile % complete
4. **ANIMATION SAFETY** — max 800ms non-decorative, prefers-reduced-motion mandatory
5. **ONE PRIMARY ACTION** — one primary CTA per screen (ADHD working memory ~1.5 items)

Read full: `docs/ECOSYSTEM-CONSTITUTION.md`

---

## DESIGN SYSTEM

Read BEFORE any UI work:
1. `docs/design/DESIGN-MANIFESTO.md` — 7 Laws
2. `docs/ECOSYSTEM-CONSTITUTION.md` — 5 Foundation Laws
3. `apps/web/src/app/globals.css` — live token state
4. `.claude/rules/ecosystem-design-gate.md` — 4 questions + 16 anti-patterns

Typography (until tokens are in CSS):
- Page title: `text-2xl font-bold font-headline` (Plus Jakarta Sans)
- Section header: `text-lg font-semibold font-headline`
- Body: `text-sm font-normal` (Inter)
- Caption: `text-xs font-medium text-on-surface-variant`

Face accents: VOLAURA #7C5CFC, MindShift #3B82F6, Life Sim #F59E0B, BrandedBy #EC4899

---

## AURA SCORE WEIGHTS (FINAL — DO NOT CHANGE)

communication: 0.20, reliability: 0.15, english_proficiency: 0.15, leadership: 0.15, event_performance: 0.10, tech_literacy: 0.10, adaptability: 0.10, empathy_safeguarding: 0.05

Badge tiers: Platinum >= 90, Gold >= 75, Silver >= 60, Bronze >= 40, None < 40

---

## TOP 12 MISTAKES FROM 115 SESSIONS (don't repeat these)

1. **CLASS 3 — Solo execution** (16 instances). 48 agents exist, CTO works solo. ALWAYS check `memory/swarm/agent-roster.md` before any non-trivial task.
2. **CLASS 7 — False completion**. "Tests pass" ≠ "product works". Walk the user journey before saying done.
3. **CLASS 9 — No quality system**. Write acceptance criteria BEFORE coding. "DONE when: [3-5 PASS/FAIL conditions]."
4. **CLASS 10 — Process theater**. Building protocols instead of shipping features. Zero tolerance.
5. **CLASS 11 — Self-confirmation**. If you propose a solution, you CANNOT validate it yourself. Use external research.
6. **CLASS 12 — Debug instead of replace**. After 5 min debugging, ask "Did I create this?" If yes, replace.
7. **grep BEFORE edit**. Before every Edit/Write: `grep -rn "[thing being changed]"` to check blast radius.
8. **Don't present technical details to CEO**. CEO sees product outcomes, not file names. Use CEO Report Agent format.
9. **Don't ask trailing questions**. "Should I proceed?" when CEO already gave the plan = trust leak.
10. **Memory updates in SAME response**. If you learn something, write it to the file NOW. Not "later".
11. **Schema verification**. Read Python schemas before writing TypeScript types. Field mismatch = 422.
12. **Never say "volunteer"**. Legacy naming. Say "professional" or "member". 451 code references still use old name.

---

## KEY FILES TO READ AT SESSION START

```
CLAUDE.md                              — operating system (READ FIRST)
memory/context/sprint-state.md         — where are we right now
memory/context/mistakes.md             — what NOT to repeat
memory/context/patterns.md             — what works
memory/context/working-style.md        — who Yusif is, how he communicates
memory/swarm/SHIPPED.md                — what code actually exists
memory/atlas/lessons.md                — distilled wisdom
docs/ECOSYSTEM-CONSTITUTION.md         — supreme law
docs/design/DESIGN-MANIFESTO.md        — 7 design laws
.claude/rules/ecosystem-design-gate.md — 4 questions + 16 anti-patterns before any UI
.claude/rules/ceo-protocol.md          — when to engage CEO
```

---

## EXECUTION ORDER FOR ECOSYSTEM REVIVAL

### Priority 1: BrandedBy main page (HIGH VALUE, LOW EFFORT)
- Backend: DONE (9 endpoints, full AI Twin lifecycle)
- Frontend hooks: DONE (`use-brandedby.ts` with `useMyTwin()`, `useGeneration()`, etc.)
- Generation viewer: DONE (419 lines, video player + share)
- **MISSING:** Main `/brandedby` page. Replace ProductPlaceholder with:
  - Twin status card (no twin → create CTA; draft → activate CTA; active → generate CTA)
  - Personality preview (from `twin.personality_summary`)
  - Generation history list (link to `/brandedby/generations/[id]`)
  - Crystal balance + queue skip option (25 crystals)
- Constitution: identity first (show AI Twin's character, not just status), one primary CTA, no red, energy modes

### Priority 2: Life Feed verification + polish
- Frontend and backend both exist and are real
- Verify `lifesim_events` table has data (check migrations for seed)
- Check crystal economy connection: VOLAURA assessment → crystal_earned → Life Feed shop
- Polish: ensure Constitution compliance (check energy modes, loading states as skeletons not spinners)

### Priority 3: MindShift decision
- **ASK CEO**: Pull MindShift code into monorepo, keep as bridge, or build integration page?
- Until decision: at minimum replace ProductPlaceholder with a page showing:
  - User's energy level (from `profiles.energy_level` column — migration exists)
  - Assessment history as "cognitive training log"
  - Future features teaser (not "Coming soon" — Constitution shame-free framing)

### Priority 4: Atlas admin dashboard (LOW PRIORITY)
- CEO-only page
- Show: swarm proposals, agent activity, system health
- Uses `atlas_gateway` router

---

## SWARM SYSTEM (ZEUS)

Location: `packages/swarm/`
- `autonomous_run.py` (1733 lines) — 8 perspectives, multiple modes
- `engine.py` (542 lines) — core orchestration
- Tools: `code_tools.py`, `constitution_checker.py`, `deploy_tools.py`, `llm_router.py`, `web_search.py`
- 48 skill files in `memory/swarm/skills/`
- Daily cron: `.github/workflows/swarm-daily.yml`
- Proposals: `memory/swarm/proposals.json`

**LLM provider hierarchy:**
1. Cerebras Qwen3-235B (primary — 2000+ tok/s)
2. Ollama/local GPU (zero cost)
3. NVIDIA NIM (backup)
4. Anthropic Haiku (LAST RESORT ONLY)

**Rule:** Never use Claude models as swarm agents. Never use only one provider. Always diverse.

---

## CHARACTER_EVENTS TABLE (cross-product event bus)

All products write here. All products read here. Schema:
```sql
CREATE TABLE character_events (
  id UUID DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  source TEXT NOT NULL,      -- 'volaura', 'mindshift', 'lifesim', 'brandedby'
  event_type TEXT NOT NULL,  -- 'assessment_completed', 'crystal_earned', 'badge_tier_changed', etc.
  payload JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
```

Services that emit: `ecosystem_events.py` (emit_assessment_completed, emit_aura_updated, emit_badge_tier_changed)

---

## CRYSTAL ECONOMY

- Crystals earned from VOLAURA assessments (via `assessment/rewards.py`)
- Tracked in `game_crystal_ledger` table
- Spent in: Life Sim shop (4 items), BrandedBy queue skip (25 crystals)
- Atomic deduction via `deduct_crystals_atomic` RPC (advisory lock, no double-spend)
- Crystal Laws in Constitution: cap per event, no infinite earn loops, transparent pricing

---

## OTHER USEFUL CONTEXT

### tg-mini (Telegram Mini App)
- Location: `apps/tg-mini/` (Vite + React + telegram-apps SDK)
- Pages: Home, Agents, Proposals
- Small but functional. Low priority.

### Remotion (Video Generation)
- Location: `packages/remotion/`
- For BrandedBy AI Twin videos
- Has compositions, themes, components

### Supabase Migrations
- 90 total in `supabase/migrations/`
- Recent additions: `lifesim_events_table`, `profiles_add_energy_level`, `grievances_table`, `ecosystem_compliance_schema`
- Phase 1 volunteer→professional migration created but NOT yet applied

### Production URLs
- Frontend: https://volaura.app
- Backend: https://volauraapi-production.up.railway.app (NEVER: volaura-production — wrong service)
- Health check: GET /health → should return `{"status":"ok","database":"connected","llm_configured":true}`

---

## WHAT SUCCESS LOOKS LIKE

After this work:
1. User navigates to /brandedby → sees their AI Twin dashboard (create/activate/generate), NOT "Coming soon"
2. User navigates to /life → sees Life Feed with real choices (already works, verify + polish)
3. User navigates to /mindshift → sees meaningful content, NOT ProductPlaceholder
4. All new pages follow Constitution (no red, energy modes, shame-free, one CTA, animation-safe)
5. All pages write to character_events so Atlas can see user activity across products
6. Crystal economy flows: assessment → crystals → spend in Life Sim or BrandedBy

CEO said: "оживи экосистему." That means when a user opens any tab, they see a living product — not a "coming soon" placeholder.
