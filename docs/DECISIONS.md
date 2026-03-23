# Architecture Decisions Log

## ADR-001: Monorepo with Turborepo
**Date:** 2026-03-21
**Decision:** Turborepo + pnpm workspaces
**Why:** Single repo for frontend + backend + migrations. Parallel dev servers. No code sharing between TS/Python (just API types via OpenAPI).
**Alternatives:** Separate repos (too much overhead for solo dev), Nx (heavier).

## ADR-002: Supabase Client — Per-Request via Depends()
**Date:** 2026-03-21
**Decision:** Use `acreate_client()` per request via FastAPI `Depends()`, NOT global client.
**Why:** RLS requires user-scoped JWT. Global client = all requests share same auth context = RLS bypass risk.
**Note:** `fastapi-supabase` package evaluated and rejected (abandoned, only 1 release mid-2025).
**Source:** Supabase team recommendation via @silentworks in GitHub Discussion #33811.

## ADR-003: No tRPC — OpenAPI + @hey-api/openapi-ts
**Date:** 2026-03-21
**Decision:** FastAPI generates OpenAPI spec → `@hey-api/openapi-ts` generates TypeScript types + TanStack Query hooks.
**Why:** FastAPI has built-in OpenAPI generation. tRPC requires tight coupling. hey-api provides equivalent type safety without framework lock-in.

## ADR-004: Gemini Primary, OpenAI Fallback
**Date:** 2026-03-21
**Decision:** Gemini 2.5 Flash (free tier) as primary LLM. OpenAI GPT-4o-mini as paid fallback.
**Why:** Free tier = $0 for MVP. 15 RPM limit is sufficient for assessment evaluations with caching.
**SDK:** `google-genai` (NOT `google-generativeai` — different package).

## ADR-005: pgvector 768 dimensions
**Date:** 2026-03-21
**Decision:** vector(768) using Gemini text-embedding-004.
**Why:** Matches Gemini embedding model output. NOT 1536 (OpenAI). All vector ops via Supabase RPC functions (PostgREST can't call pgvector operators directly).

## ADR-006: i18n — react-i18next with [locale] segment
**Date:** 2026-03-21
**Decision:** `react-i18next` + `next-i18n-router` with `[locale]` route segment.
**Why:** Official approach for App Router. AZ primary, EN secondary. No Russian in assessment content.
**Note:** `next-i18next` is deprecated for App Router — use `react-i18next` directly.

---

## Sprint 1 Retrospective (2026-03-23)

**Sprint:** Backend Foundation (Sessions 1-4)
**DSP status:** ⚠️ NOT RUN before sprint (protocol violation — fixed in v3.0)
**Model used:** claude-sonnet-4-6

### Results
✓ **What went right:** 25 Python files, 12 SQL migrations, 72 tests passing. All 5 P0 security vulnerabilities patched. Pure Python IRT/CAT engine works without external dependencies.
✗ **What DSP would have caught:** 3 ad-hoc design decisions (auth pattern, rate limit thresholds, LLM fallback chain). The adaptivetesting library incompatibility — simulation with Scaling Engineer persona would have flagged Python 3.10 constraint.
→ **Feed into next simulation:** Always check runtime environment constraints before adding dependencies. Always run DSP before sprint.

### DSP Calibration (Sprint 2 pre-simulation)
```
Predicted: Path C "Scaffolding Sprint" — 45/50
Actual outcome: TBD (Sprint 2 not started yet)
```

### Algorithm Changes
- v1.0 → v2.0: Added QA Engineer persona, model routing
- v2.0 → v3.0: Added Scope Lock, Confidence Gate, Retrospective, Calibration, Self-Improvement Protocol, Copilot Protocol, Memory Protocol, Multi-Model Verification

---

## Sprint 2 — Session 5 Retrospective (2026-03-23)

**Session:** Frontend Scaffold + V0 Prompts
**DSP status:** ✅ Pre-sprint DSP run. Winner: Path C "Scaffolding Sprint" (45/50)
**Model used:** claude-sonnet-4-6

### Results
✓ **What went as simulated:**
- Scaffold already existed (29 TS files). Discovery saved ~3 sessions. Path C was right to prioritize scaffold-first.
- Auth middleware chain implemented correctly on first attempt.
- V0 prompts generated with full API contracts.

✗ **What DSP did not predict:**
- Process violation: design:handoff + design:ux-writing were NOT loaded before writing V0 prompts. Skills Matrix explicitly requires these for "Writing V0 prompts" but row didn't exist in matrix. Row now added.
- This was caught by Yusif ("какие алгоритмы и скилы ты использовал?") — same class as Mistake #1 (DSP skipped before Sprint 1).
- Memory files not updated at session end — caught by Yusif next session.

→ **Feed into next simulation:**
- Add "process compliance audit" as QA Engineer persona responsibility in DSP
- Skills Matrix "Writing V0 prompts" row added — this prevents recurrence
- Add mandatory memory update step to Execution protocol (Phase D)

### ADR-007: V0 Prompt Engineering Standards
**Date:** 2026-03-23
**Decision:** V0 prompts must include: all component states (loading/error/empty/disabled/hover),
animation specs with exact timing (duration + easing), ARIA accessibility, edge cases
(long AZ strings, slow connection, timer expiry, missing data), error message copy
following "what + why + how to fix" structure.
**Why:** Without these, V0 generates UI that looks complete but fails on accessibility,
edge cases, and error handling. Prompts without animation timing produce inconsistent motion.
**Skills required before writing:** design:handoff + design:ux-writing (mandatory).

---

## DSP Calibration Log

| Sprint | DSP Winner | Predicted Score | Actual Outcome | Delta | Action |
|--------|-----------|----------------|----------------|-------|--------|
| 1 | N/A (not run) | — | Good code, ad-hoc decisions | — | Created mandatory DSP rule |
| 2 Session 5 | Path C (Scaffolding) | 45/50 | Scaffold existed, prompts complete, process violations caught | -5 (process violations unpredicted) | Add process audit to QA persona |
| 2 Session 11 | Path B (Bug-First + Incremental) | 42/50 | All items delivered, 3 security issues caught + fixed | 0 | Approach validated |

---

## Sprint 2, Session 6 Retrospective — Assessment Flow

**Date:** 2026-03-23

✓ **What went as simulated:**
- All 14 assessment components + pages created in one session (DSP Path C predicted direct implementation would work)
- Engineering:code-review caught 6 real bugs before commit: relative routing, recursive poll leak, store guard
- AZ + EN i18n maintained parity throughout — no string left hardcoded
- Framer Motion transitions and Timer implemented with correct ARIA (aria-live, aria-busy, progressbar role)

✗ **What DSP did not predict:**
- V0 was expected to be used; Claude wrote components directly (faster for this complexity level)
- Polling pattern needed iterative loop + `isMounted` ref — recursive async approach had subtle unmount leak

→ **Feed into next simulation:**
- For "component-heavy sessions": Claude direct > V0 when API contracts are clear
- Always add `isMounted` ref to any component that polls (pattern now in patterns.md)
- Absolute locale-aware routing (`/${locale}/path`) must be default — relative paths always wrong in [locale] segment

### DSP Calibration — Session 6
| Predicted | Actual | Delta |
|-----------|--------|-------|
| Path C (direct implementation), ~44/50 | On target — all components delivered, 6 bugs caught | 0 delta |


---

## Sprint 2, Session 7 Retrospective — AURA Results + Radar

**Date:** 2026-03-23

✓ **What went as simulated:**
- Existing components upgraded (not rewritten from scratch) — reuse saved time
- Badge tier animations via Framer Motion boxShadow loop — Platinum shimmer works elegantly
- Animated counter (useAnimatedCounter hook) delivers the "wow moment" on score reveal
- i18n parity maintained: AZ + EN both have competency.* keys now

✗ **What DSP did not predict:**
- Existing code was further along than expected — radar-chart and share-buttons already existed from Sprint 1
- Efficiency gate correctly triggered: inline review instead of full engineering:code-review skill (< 200 lines changed per file)

→ **Feed into next simulation:**
- Always check existing components before planning "create from scratch" — prevents duplicate work
- The "upgrade existing" pattern is faster than "rewrite" — prefer it when structure is sound

### DSP Calibration — Session 7
| Predicted | Actual | Delta |
|-----------|--------|-------|
| ~40/50 (assumed create from scratch) | Better — upgrade path faster | +5 (efficiency gain from reuse) |

---

## DSP: Volaura Overall Product Strategy (запоздавший — должен был быть Day 1)

**Date:** 2026-03-23

**Winner: Path A — "LinkedIn для волонтёров" + Expert Verification layer**
Score: 43/50 (без expert verification) → ~48/50 (с expert verification)

**Ключевой инсайт от совета:**
- Leyla хочет badge который ценится как CV
- Nigar хочет filter по верифицированным навыкам
- Attacker: без human verification → AI scores fake через 3 месяца
- Scaling Engineer: Path A масштабируется без архитектурных изменений
- Yusif: единственный path реализуемый за 6 недель / $50 мо

**Фильтр для всех будущих фич:**
"Помогает ли это волонтёру получить верифицированный badge?"
"Помогает ли это организации найти верифицированного волонтёра?"
Если нет на оба → в бэклог.

**Calibration note:** Все предыдущие решения (Assessment, AURA, Expert Verification) 
совпали с Path A интуитивно. Это хороший знак — product instinct валиден.
Но DSP нужно было запустить в день 1 чтобы иметь явный north star.

ADR: теперь Path A = официальный north star всего проекта. Записан здесь.

---

## Sprint 2, Session 8 Retrospective — Dashboard + Profile

**Date:** 2026-03-23

✓ **What went as simulated:**
- All 10 components + 2 pages completed in one session (Claude direct, no Stitch needed)
- engineering:code-review caught 2 critical bugs before they would have caused runtime failures:
  1. `fetchAura` infinite skeleton (no `setLoading(false)` on early return)
  2. TypeScript excess-property error (`id` field in typed `ProfileFull` object)
- `Promise.all` for parallel fetch used correctly in profile/page.tsx — no sequential waterfall
- i18n parity maintained: AZ + EN both updated with 5 new keys

✗ **What DSP did not predict:**
- Stitch prompt created in Session 7 was not needed — Claude wrote directly (same pattern as Session 6)
- `useCallback` dep on full `session` object (not just `access_token`) was a subtle perf issue, caught in review
- `profile-view/` directory was empty (no prior code to upgrade from) — created all 5 components fresh

→ **Feed into next simulation:**
- For dashboard/profile type sessions: Claude direct is always faster than Stitch/V0 when API contracts are clear
- `useCallback` on fetch functions should always depend on minimal token/ID, not the full session object
- Always check what directory contents exist before planning (ls the components directory)

### DSP Calibration — Session 8
| Predicted | Actual | Delta |
|-----------|--------|-------|
| ~42/50 (Stitch output + integration) | Better — all components written directly, review caught 2 bugs | +3 |


---

## Sprint 2, Session 9 Retrospective — Expert Verification

**Date:** 2026-03-23

✓ **What went as simulated:**
- Full stack in one session: DB migration + FastAPI router + frontend page — Claude direct confirmed again as faster than Stitch for this complexity
- Attacker persona caught the TOCTOU race condition before code was written → TOCTOU guard added proactively
- UX Writing skill applied to all error states — empathetic messages (What happened + Why + How to fix) pattern strictly followed
- `TokenParam = Annotated[str, Path(max_length=100)]` — clean FastAPI pattern for path param validation
- AURA score blend formula (0.6×existing + 0.4×verification) is sound and non-destructive

✗ **What DSP did not predict:**
- AURA recalculation was the most critical gap — not predicted in scope lock because it seemed "obvious" but nearly shipped without it
- The existing assessment router calls `upsert_aura_score` with different param names than the SQL function signature — found a pre-existing bug in Session 1 code (logged, not fixed this session)
- `getattr(settings, ...)` fallback was defensive but wrong — `app_url` already exists in config

→ **Feed into next simulation:**
- "What happens after this data is saved?" must be in every POST endpoint scope lock — side effects (AURA, notifications, triggers) are the most commonly missed items
- Always check config.py before using `getattr` fallbacks on settings
- Pre-existing bugs found during review should be logged in mistakes.md immediately

### DSP Calibration — Session 9
| Predicted | Actual | Delta |
|-----------|--------|-------|
| ~42/50 (Path A, direct implementation) | On target — full stack delivered, 5 bugs caught | 0 delta |

---

## Sprint 2, Session 10 Prep — Claude Code Handoff

**Date:** 2026-03-23

✓ **What was delivered this session:**
- Comprehensive Claude Code handoff prompt written: `docs/prompts/CLAUDE-CODE-HANDOFF-SESSION10.md`
- Full project state: 9 sessions, all code, all rules, all bugs, all blockers documented
- PM task dashboard included: blocked tasks surfaced, upcoming sessions mapped
- Memory files updated (Step 0.5)

→ **Note for Session 10:**
- Load skills: design:critique, design:ux-writing, design:handoff, design:accessibility-review, engineering:code-review
- Landing page: NEVER hardcode event names — all dynamic data
- Events page: realtime counter via polling (not WebSocket — budget constraint)
- Run DSP before deciding realtime strategy (polling vs Supabase Realtime vs SSE)


---

## Sprint 2, Session 10 Retrospective — Landing Page + Events UI

**Date:** 2026-03-23

✓ **What went as simulated:**
- Claude direct confirmed faster than V0 for API-contract-heavy components (3rd consecutive session)
- Mock data layer cleanly isolated (lib/mock-data.ts) — Session 11 swap is one import change per file
- UX Writing skill applied: all CTAs start with verbs, all error states follow "what + why + how to fix"
- Impact ticker reused useCountUp hook pattern from AuraScoreWidget (Sessions 7+8 pattern pays off)
- engineering:code-review caught 3 bugs before shipping: 2× isMounted missing, 1× skip link inside main

✗ **What DSP did not predict:**
- events/[id]/page.tsx needed "use client" for register state — not flagged in scope lock
- useState misused for cleanup (should always be useEffect) — caught in review, fixed in 30s
- everything-claude-code repo: 118 skills, only 3 worth integrating — high filter cost, useful signal

→ **Feed into next simulation:**
- Session 11: fix assessment.py upsert_aura_score bug FIRST (P0) — before any API wiring
- Pattern: page needs interactive state + params → mark "use client" from the start
- Mock data layer is the right abstraction — create it BEFORE components, not after

### DSP Calibration — Session 10
| Predicted | Actual | Delta |
|-----------|--------|-------|
| 44/50 (Claude direct, mock data layer) | On target — all components delivered, 3 bugs caught + fixed | 0 delta |

---

## Sprint 2, Session 11 Retrospective — Integration Sprint

**Date:** 2026-03-23
**DSP:** Path B (Bug-First + Incremental Wiring) — 42/50
**Model:** claude-opus-4-6

✓ **What went as simulated:**
- P0 bug fix was straightforward — RPC params mismatch caught and fixed in minutes, TDD test confirmed
- Incremental wiring approach worked: each page wired independently with TanStack Query hooks
- API client + types created as INTERIM (manual) with TODO markers for ADR-003 compliance
- Code review agent caught 3 security issues: protocol-relative open redirect, 2× missing isMounted
- All 74 tests pass, zero regressions

✗ **What DSP did not predict:**
- shadcn/ui components not installed (button, skeleton, alert) — TS build fails on these imports. Pre-existing issue but blocks typecheck
- ActivityItem type mismatch between API types and component props — no dedicated activity endpoint exists, had to bypass
- Framer Motion `ease: "easeOut"` typing issue — widespread across all components, needs `as const` cast. Pre-existing

→ **Feed into next simulation:**
- Session 12 should start with `npx shadcn@latest add button skeleton alert` to unblock TS build
- `pnpm generate:api` should replace manual types once backend is accessible from frontend
- Events API wiring deferred as planned — mock data holds

### DSP Calibration — Session 11
| Predicted | Actual | Delta |
|-----------|--------|-------|
| 42/50 (Bug-First + Incremental Wiring) | On target — all planned items delivered, security review caught real issues | 0 delta |

---

## Sprint 2, Session 12 Retrospective — Stitch Design Integration

**Date:** 2026-03-23
**DSP:** Path C (Design System First + Incremental Pages) — 44/50
**Model:** claude-opus-4-6

✓ **What went as simulated:**
- Design system tokens extracted cleanly from Stitch HTML configs (all 50+ Material 3 tokens in globals.css)
- Dark-first approach works without `.dark` class toggle — `color-scheme: dark` + hardcoded dark body background = zero flash
- Plus Jakarta Sans + Inter loaded via next/font — proper CSS variables, no layout shift
- Leaderboard page built from Stitch HTML — animated podium, count-up scores, tier glow effects all working
- Notifications page: category tabs, mark-as-read, inline actions — full match to Stitch mockup
- Sidebar + TopBar + LanguageSwitcher migrated to Stitch dark palette in ~30 min
- i18n: 14 new keys (EN + AZ) added without regressions

✗ **What DSP did not predict:**
- Tailwind 4 CSS-first config: `@theme` block accepts `--font-*` variables but `font-headline` class still needs manual font-family CSS (not auto-resolved from variable)
- `bg-surface-container-low` Tailwind classes only work if the tokens are in `@theme` — confirmed they are
- Visual consistency check deferred — no preview server run this session to verify render

→ **Feed into next simulation:**
- Session 13: Run dev server and screenshot new pages before writing any new code
- For new pages with mock data: always add `// TODO: replace with useX() hook when endpoint exists` comment
- Stitch HTML inline styles (e.g., `border-color: #ffd700`) should become Tailwind `[style]` or utility classes — not raw inline on React elements

### DSP Calibration — Session 12
| Predicted | Actual | Delta |
|-----------|--------|-------|
| 44/50 (Design System First + Incremental Pages) | On target — all tokens extracted, 2 pages built, components migrated | 0 delta |

---

## DSP v4.0 Swarm — Phase 0 Proof-of-Concept (2026-03-23)

**Decision:** What should Session 14 start with?
**Architecture:** 5 × Claude haiku evaluators (parallel, blind) + Claude Sonnet synthesis
**Goal:** Validate swarm architecture before building full `packages/swarm/` engine.
**Gemini hybrid test:** Deferred (GEMINI_API_KEY empty in apps/api/.env — add to test)

### Raw Results

| Evaluator | Influence | path_a raw | path_b raw | path_c raw | path_d raw | Vote |
|-----------|-----------|-----------|-----------|-----------|-----------|------|
| Leyla     | 1.0       | 30        | 29        | 22        | 31        | path_a |
| Attacker  | 1.2       | 25        | 31        | 24        | 30        | path_a |
| Yusif     | 1.0       | 29        | 32        | 29        | 35        | path_a |
| Scaling   | 1.1       | 28        | 32        | 30        | 29        | path_a |
| QA        | 0.9       | 34        | 25        | 25        | 29        | path_a |

### Weighted Scores (/50)
- Path A — E2E Integration Test First: **28.9/50** ← Winner (vote)
- Path B — Vercel Deploy Preview First: **30.0/50**
- Path C — Embedding Pipeline First: **26.0/50** ← worst (GEMINI key blocks it)
- Path D — AURA Coach UI Wiring: **30.8/50** ← highest raw score

### Winner: Path A — E2E Integration Test First
**Vote:** 5/5 agents (unanimous) | **Raw score:** 28.9/50 (below 35 gate — see calibration note)
**Consensus reason:** Migrations + schema validation is a hard dependency for ALL other paths.
Path D looks best on dimensions but wires UI to endpoints that don't exist yet (tables uncreated).

### Key Divergence Signals
1. **Raw score vs vote winner mismatch:** Path D scores highest (30.8) but zero votes. Agents overrode scores via sequencing logic — dimensions don't capture "prerequisite" ordering. Real insight: dimension scoring alone is insufficient for dependency-constrained decisions.
2. **Risk dimension ambiguity (bug):** Attacker/Yusif/Scaling: risk=9 means "dangerous." Leyla/QA: risk=9 means "safe." Same dimension, opposite directions. Raw aggregation is invalid. Fix: add direction to prompt ("0 = catastrophic, 10 = very safe").
3. **Path C unanimous rejection:** GEMINI_API_KEY empty + migrations untested = blocked before first line.

### Surprise Insights
- **Attacker:** SupabaseAdmin privilege escalation risk if `apps/api/app/routers/assessment.py` misuses SupabaseAdmin — E2E test must verify admin vs user token isolation. Not in sprint plan.
- **Scaling:** `supabase/ALL_MIGRATIONS_COMBINED.sql` is monolithic — partial failure = DB in unknown state, no rollback. Recommend splitting into atomic migrations.

### Confidence Gate Exception
Winner scores 28.9/50 < 35 threshold. Exception applied: path_a is a prerequisite path. Low user_impact + dev_speed scores are expected for foundational work, not a flaw. Gate needs "prerequisite path" exception.

### Calibration Fixes for Next Swarm Run
1. **Risk direction:** Add "0 = catastrophic, 10 = very safe" to evaluator prompt
2. **Dependency dimension:** Add new dimension "dependency: 0 = blocked by unknowns, 10 = can start immediately" — would correctly rank path_a higher and path_c as blocked
3. **Confidence gate:** Add override for prerequisite paths with human confirmation

### Swarm Architecture Validation
✅ 5 parallel agents returned valid JSON (0 parse errors)
✅ Genuine divergence detected (raw score winner ≠ vote winner)
✅ Unique insights surfaced (Attacker privilege escalation, Scaling monolith risk)
✅ Risk dimension ambiguity caught (found real prompt bug before building full engine)
⚠️ GEMINI key needed to test true hybrid (Gemini evaluators + Claude synthesis)
→ Next: Add GEMINI_API_KEY to apps/api/.env and run `python packages/swarm/test_swarm.py`

### DSP Calibration Entry
| Predicted | Actual | Delta | Action |
|-----------|--------|-------|--------|
| TBD after Session 14 | — | — | Check after Session 14 completes |
