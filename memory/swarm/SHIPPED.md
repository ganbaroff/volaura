# SHIPPED — What Exists in Production

**Purpose:** CTO reads this at session start. Single source of truth for "what code is live."
**Updated by:** CTO or agents after every session that adds/changes code.
**Rule:** If it's not here — CTO doesn't know it exists.

---

## Session 81 BATCH-D (2026-04-02) — Admin Panel MVP

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Migration | `supabase/migrations/20260402130000_add_platform_admin.sql` | Adds `is_platform_admin BOOLEAN DEFAULT FALSE` to profiles. Apply in Supabase dashboard + set `true` for Yusif. | ✅ NEW |
| `require_platform_admin` dep | `apps/api/app/deps.py` | Fail-closed gate. Checks `is_platform_admin` via service-role. Returns 403 if not admin. `PlatformAdminId` type alias. | ✅ NEW |
| Admin schemas | `apps/api/app/schemas/admin.py` | `AdminUserRow`, `AdminOrgRow`, `AdminStatsResponse`, `OrgApproveResponse` | ✅ NEW |
| Admin router | `apps/api/app/routers/admin.py` | 6 endpoints: ping, stats, users list, pending orgs, approve/reject org. 30/min rate limit. 102 routes total. | ✅ NEW |
| Admin tests | `apps/api/tests/test_admin.py` | 7 tests: 3 gate (non-admin → 403), 4 happy path (ping, pending orgs, approve, reject) | ✅ NEW |
| `use-admin.ts` | `apps/web/src/hooks/queries/use-admin.ts` | `useAdminPing`, `useAdminStats`, `useAdminUsers`, `usePendingOrganizations`, `useApproveOrganization`, `useRejectOrganization` | ✅ NEW |
| `admin-guard.tsx` | `apps/web/src/components/layout/admin-guard.tsx` | Client guard: checks session + /api/admin/ping. Redirects to /dashboard if not admin. | ✅ NEW |
| `admin-sidebar.tsx` | `apps/web/src/components/layout/admin-sidebar.tsx` | Nav: Overview / Users / Organizations / AURA Scores + Back to app | ✅ NEW |
| Admin layout | `apps/web/src/app/[locale]/(admin)/layout.tsx` | Route group layout wrapping AdminGuard + AdminSidebar | ✅ NEW |
| Admin pages | `(admin)/page.tsx`, `users/page.tsx`, `organizations/page.tsx`, `aura/page.tsx` | Overview stats, users table, org approval queue, AURA list | ✅ NEW |

**Access URL:** `/az/admin` (or `/en/admin`)
**1-click required:** Apply migration in Supabase + set `is_platform_admin=true` for Yusif's profile row

---

## Session 81 BATCH-C (2026-04-02) — Circuit Breaker Constant Fix

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `_CB_THRESHOLD` rename | `apps/api/app/services/match_checker.py` | Renamed `_TELEGRAM_CB_THRESHOLD` → `_CB_THRESHOLD` to match test import. 687 passed, 0 failed. | ✅ FIXED |

---

## Session 81 (2026-04-02) — Growth Trajectory Widget + Milestone Animation (D.2-A + D.2-B)

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Growth Trajectory Widget | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | Animated progress bar showing "X pts to [next tier]". Uses `aura.total_score` + tier thresholds. Framer Motion bar animates from 0 to pct on reveal (delay 0.75s). Shows Platinum max state. No new backend. | ✅ NEW |
| Milestone Banner | Same file | Gold/Platinum celebration banner — shows when `aura_updated && badge_tier in [gold,platinum]`. Gradient background (yellow/cyan), spring animation. Appears between Badge Reveal and Stats Row. | ✅ NEW |
| i18n growth keys EN | `apps/web/src/locales/en/common.json` | `progressToNextTier`, `tierMaxReached`, `milestonePlatinum`, `milestoneGold`, `milestoneDiscoverable` | ✅ NEW |
| i18n growth keys AZ | `apps/web/src/locales/az/common.json` | AZ translations for all 5 growth keys | ✅ NEW |
| Board heavy run script | `board_heavy_run.py` (project root) | nemotron-ultra-253b × 2 + deepseek-r1 on growth topic. Both Board agents voted: Tribe Streaks (Strategic Dir) + Collective AURA Ladders (CPO). BOTH killed AURA Leaderboard unanimously. | ✅ UTILITY |
| board-heavy-results.json | `memory/swarm/board-heavy-results.json` | Raw Board analysis results from heavy models | ✅ ARTIFACT |

**Board unanimous findings (both nemotron-ultra-253b agents):**
- KILL: AURA Score Leaderboard — "direct cultural mismatch, anxiety from public rankings will suppress usage in AZ/CIS"
- NEW RISK: Anti-harassment safeguards needed for Tribe formation (nobody else mentioned this)
- NEW RISK: Exclusionary cliques if group membership is static (Collective AURA Ladders)

---

## Session 80 (2026-04-01) — CIS-001 Fix + Profile View Infra

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Discovery: Sprint D.1 already shipped | `apps/api/app/routers/profiles.py` + `apps/web/src/components/profile/profile-view-tracker.tsx` + `apps/api/tests/test_profile_view.py` | `POST /api/profiles/{username}/view` endpoint existed, frontend ProfileViewTracker existed, 6 tests existed. Session confirmed these are live — not re-implemented. | ✅ CONFIRMED |
| `notify_profile_viewed()` | `apps/api/app/services/notification_service.py` | New helper function: throttled `org_view` notification emit. Checks 24h window via partial index. Never raises. Returns bool (sent/throttled). Uses `org_id` as reference_id. | ✅ NEW |
| Org view throttle index | `supabase/migrations/20260401180000_profile_view_notification_index.sql` | Partial index on `notifications(user_id, reference_id, created_at) WHERE type='org_view'`. Serves the 24h dedup query in `record_profile_view` endpoint. Prevents seq scan as notifications table grows. | ✅ NEW |
| Achievement level utility | `apps/web/src/lib/utils/achievement-level.ts` | `getAchievementLevelKey(percentileRank)` — maps 0-100 percentile to i18n key (Expert/Advanced/Proficient/Growing/Building/Starting). CIS-001 fix. | ✅ NEW |
| i18n achievement keys | `apps/web/src/locales/en/common.json` + `az/common.json` | `profile.achievementLabel` + 6 tier keys (achievementExpert → achievementStarting). AZ: Ekspert/Peşəkar/Bilikli/İnkişaf Edir/Hazırlanır/Başlanır. | ✅ UPDATED |
| CIS-001 fix: public profile | `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx` | Replaced `t("profile.topPercent", ...)` with `t(getAchievementLevelKey(percentileRank))`. "Top 5%" → "Expert". Non-competitive framing for AZ/CIS users. | ✅ UPDATED |
| CIS-001 fix: assessment complete | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | Achievement level replaces percentile stat box display. Label changes from "percentile" to `profile.achievementLabel`. Share text keeps `topPercent` (opt-in competitive context). | ✅ UPDATED |

---

## Session 79 (2026-04-01) — BATCH C: Sprint 8 Tests + Realtime Notifications

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Sprint 8 Tests | `apps/api/tests/test_saved_searches.py` | 13 tests: happy path (create/list/delete/update), privilege escalation (org A ≠ org B), validation (cap/dupe/badge_tier/UUID/empty), match checker service (no searches, DB error, circuit breaker). | ✅ NEW |
| Realtime Notifications Hook | `apps/web/src/hooks/queries/use-notifications.ts` | `useRealtimeNotifications(userId)` — Supabase Realtime subscription to `notifications` table INSERT. On INSERT → invalidates unread count + list queries instantly. Falls back silently. Cleans up on unmount. | ✅ UPDATED |
| Realtime Provider | `apps/web/src/components/layout/realtime-notifications.tsx` | `RealtimeNotificationsProvider` — client component. Reads userId from auth session, calls `useRealtimeNotifications()`. Renders nothing (side-effect only). | ✅ NEW |
| Dashboard Layout | `apps/web/src/app/[locale]/(dashboard)/layout.tsx` | Added `<RealtimeNotificationsProvider />` — persists subscription across all dashboard pages. | ✅ UPDATED |
| DSP Decision logged | `memory/swarm/agent-feedback-log.md` | Explicit defer: FastAPI WebSocket / ANUS = do NOT propose before 2026-07-01 or 500 active users. Alternative: Supabase Realtime (implemented). Stops 5+ convergent proposals from recurring. | ✅ UPDATED |

---

## Session 79 (2026-04-01) — SPRINT 8: Org Saved Search + Match Notifications

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Migration | `supabase/migrations/20260401171324_org_saved_searches.sql` | `org_saved_searches` table. JSONB filters (mirrors VolunteerSearchRequest). RLS: owner reads own only (via org FK chain). Partial index for notify_on_match. 20-search cap enforced at API layer. | ✅ NEW |
| Schemas | `apps/api/app/schemas/organization.py` | `SavedSearchFilters`, `SavedSearchCreate`, `SavedSearchUpdate`, `SavedSearchOut`, `SavedSearchMatchPreview`, `SavedSearchMatchNotification`. Validators: badge_tier enum, languages cap. | ✅ UPDATED |
| API endpoints | `apps/api/app/routers/organizations.py` | `POST /saved-searches`, `GET /saved-searches`, `PATCH /saved-searches/{id}`, `DELETE /saved-searches/{id}`. `_assert_search_ownership()` prevents cross-org access. 20-search cap. | ✅ UPDATED |
| Match Checker | `apps/api/app/services/match_checker.py` | Runs daily (GitHub Actions). Queries `aura_scores WHERE updated_at > last_checked_at`. Telegram notification via bot. Circuit breaker (3 failures → stop). Privacy: `visibility='public'` filter. CLI entry point for GitHub Actions. | ✅ NEW |
| GitHub Actions | `.github/workflows/match-checker.yml` | Cron: 07:00 UTC (11:00 Baku). Dry-run input for testing without Telegram. | ✅ NEW |
| Saved Search hooks | `apps/web/src/hooks/queries/use-organizations.ts` | `useSavedSearches()`, `useCreateSavedSearch()`, `useDeleteSavedSearch()` TanStack Query hooks. | ✅ UPDATED |
| Save Search UI | `apps/web/src/app/[locale]/(dashboard)/org-volunteers/page.tsx` | "Save search" button appears when search input is active. Modal: name + notify toggle. Saved search pills list with delete button. | ✅ UPDATED |
| i18n | `apps/web/src/locales/*/common.json` | orgDash.saveSearch, saveSearchHint, saveSearchModal, saveSearchName, saveSearchCta, saveSearchSaved, notifyOn, notifyOff — EN + AZ. | ✅ UPDATED |

---

## Session 79 (2026-04-01) — SPRINT 7: MindShift + Life Sim Integration

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Cross-Product Bridge | `apps/api/app/services/cross_product_bridge.py` | Fire-and-forget Volaura→MindShift event push. 3 public async functions: `push_crystal_earned()`, `push_skill_verified()`, `push_xp_earned()`. Circuit breaker: 3 failures/5min → 60s silence. httpx async client, 3s connect / 8s read timeouts. Never raises. `reset_circuit_breaker()` for tests. | ✅ NEW |
| rewards.py updated | `apps/api/app/services/assessment/rewards.py` | Added `user_jwt: str \| None = None` param. After persisting local events, calls `push_crystal_earned()` + `push_skill_verified()` on the bridge (fire-and-forget). | ✅ UPDATED |
| assessment.py updated | `apps/api/app/routers/assessment.py` | Extracts JWT from `Authorization: Bearer ...` header in `complete_assessment`. Passes it to `emit_assessment_rewards()` so bridge can authenticate with MindShift. | ✅ UPDATED |
| use-character.ts | `apps/web/src/hooks/queries/use-character.ts` | `useCrystalBalance()` — fetches `GET /api/character/crystals` (30s stale). `useCharacterState()` — fetches full state (1min stale). Both return null on 404 (no events yet). | ✅ NEW |
| CrystalBalanceWidget | `apps/web/src/components/dashboard/crystal-balance-widget.tsx` | Renders crystal balance on dashboard. Hides if balance=0 (no noise for new users). Silent on API error — never breaks dashboard. i18n-ready. | ✅ NEW |
| Dashboard page updated | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | Added `CrystalBalanceWidget` between StatsRow and Feed sections. Only shows for users with score. | ✅ UPDATED |
| i18n updated | `apps/web/src/locales/*/common.json` | Added `character.*` keys: crystalBalance, crystals, crystalLabel, earnOnVolaura — EN + AZ. | ✅ UPDATED |

---

## Session 78 (2026-04-01) — SPRINT 5+6: Skill Evolution Completion + Social Delivery Pipeline

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Skill Applier | `packages/swarm/skill_applier.py` | Applies improvement suggestions to skill .md files. 6 edit types: add_example, sharpen_rule, add_antipattern, add_trigger, remove_obsolete, generic. Creates .bak before every edit. `apply_from_evolution_log()` reads HIGH-priority items from skill-evolution-log.md and applies them. | ✅ NEW |
| Skill A/B Tester | `packages/swarm/skill_ab_tester.py` | Compares old vs new skill on a domain-specific test task. LLM self-scoring + cross-model judge. `apply_and_validate()` full pipeline: apply → test → keep or revert. Domain task library (10 domains). Logs to skill-ab-test-log.jsonl. | ✅ NEW |
| Report Generator | `packages/swarm/report_generator.py` | Structured batch-close reports. 3 formats: markdown (ceo-inbox.md), Telegram Markdown, stdout. `BatchReport` dataclass with health indicator (GREEN/YELLOW/RED). `write_to_ceo_inbox()` prepends most-recent-first. | ✅ NEW |
| autonomous_run.py updated | `packages/swarm/autonomous_run.py` | Replaced ad-hoc print block with `generate_batch_report()` + `write_to_ceo_inbox()`. Groundedness score now tracked per batch. Suggestion engine now feeds into report. | ✅ UPDATED |
| session_end_hook.py updated | `packages/swarm/session_end_hook.py` | Added skill evolution check at session end. Calls `apply_from_evolution_log()` — applies HIGH-priority skill improvements automatically after every push. | ✅ UPDATED |

---

## Session 78 (2026-04-01) — SPRINT 3+4: Adaptive Execution Loop + Context Intelligence Engine

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Execution State | `packages/swarm/execution_state.py` | `ExecutionState` enum (IDLE/RUNNING/RETRYING/RECOVERING/FAILED/SUCCESS) + `AgentExecutionTracker`. Validated state transitions. JSON-serializable. `handle_failure()` returns strategy. | ✅ NEW |
| Recovery Strategies | `packages/swarm/recovery_strategies.py` | 4 strategies: retry (exponential backoff), simplify (reduce scope), decompose (split into subtasks), escalate (write to escalations.md). `apply_recovery_strategy()` dispatcher. `decomposed-tasks.jsonl` log. | ✅ NEW |
| Code Index | `packages/swarm/code_index.py` | Scans 530 files across `apps/api/app`, `apps/web/src`, `packages/swarm`, etc. Extracts: Python functions/classes/imports, TS exports, SQL tables. Keyword scoring. Written to `memory/swarm/code-index.json`. Rebuilt on every push via `session-end.yml`. | ✅ NEW |
| Task Binder | `packages/swarm/task_binder.py` | Maps task description → primary/secondary files. Domain mapping table (14 domains). Code index search. `BoundTask.to_briefing_section()` injects BOUND FILES into agent briefing. Tested: "crystal reward" → `assessment.py` + `rewards.py` (100% confidence). | ✅ NEW |
| autonomous_run.py updated | `packages/swarm/autonomous_run.py` | Loads code index before agents launch. Binds each perspective's lens to files. Injects `bound_files` into agent prompt. All wiring non-blocking (exceptions caught). | ✅ UPDATED |
| session-end.yml updated | `.github/workflows/session-end.yml` | Added "Rebuild code index" step after session-end hook. `code-index.json` committed to repo → always fresh for next swarm run. | ✅ UPDATED |
| code-index.json created | `memory/swarm/code-index.json` | 530 files indexed. Built 2026-04-01. | ✅ CREATED |

---

## Session 78 (2026-04-01) — SPRINT 1+2: Swarm Infrastructure P0 + Predictive Suggestions

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Heartbeat Gate | `packages/swarm/heartbeat_gate.py` | KAIROS binary gate: should swarm run? Checks 3 conditions (urgent proposals → active git → stale floor). Exit 0=RUN, Exit 1=SKIP. Wired into `swarm-daily.yml`. | ✅ NEW |
| Proposal Verifier | `packages/swarm/proposal_verifier.py` | Extracts file paths from proposals, checks existence, scores groundedness (0-100%). Ungrounded proposals tagged [UNGROUNDED]. Audited existing proposals: 29/30 grounded (96.7%). 1 caught: `apps/api/app/routes.py` doesn't exist. | ✅ NEW |
| Outcome Verifier | `packages/swarm/outcome_verifier.py` | Two-tier verification: T1 (deterministic: file checks + test delta + AST parse) + T2 (LLM judge when T1 <0.9). `verify_outcome()` + `record_outcome()`. Self-verification built in (`SPRINT_1_TASKS`). | ✅ NEW |
| Suggestion Engine | `packages/swarm/suggestion_engine.py` | Predictive next actions (Sprint 2 winner). After batch close, generates 2-3 CEO predictions with `trigger_reason`. Appends to `ceo-inbox.md`. Rule-based + LLM fallback. | ✅ NEW |
| autonomous_run.py updated | `packages/swarm/autonomous_run.py` | Two new hooks after batch: (1) proposal_verifier tags ungrounded proposals, (2) suggestion_engine generates predictions → ceo-inbox.md. | ✅ UPDATED |
| swarm-daily.yml updated | `.github/workflows/swarm-daily.yml` | Heartbeat gate step added. `should_run` output gates the main swarm step. Skip notice if gate=false. Manual dispatch always bypasses gate. Heartbeat log committed even on skip. | ✅ UPDATED |
| heartbeat-log.jsonl created | `memory/swarm/heartbeat-log.jsonl` | First entry written by gate test run: RUN reason=urgent_pending_proposals (10 HIGH/CRITICAL). | ✅ CREATED |
| ceo-inbox.md predictions | `memory/swarm/ceo-inbox.md` | First predictions appended: (1) Act on HIGH security proposal, (2) Run Sprint 1 verification. | ✅ UPDATED |

**All files syntax-verified. All imports clean.**

---

## Session 78 (2026-04-01) — ROADMAP + PROTOCOL: Implementation Roadmap + TASK-PROTOCOL v6.0

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| IMPLEMENTATION-ROADMAP.md | `docs/IMPLEMENTATION-ROADMAP.md` | 8-sprint unified plan from cross-repo analysis (ZEUS + MindShift + Claude Code patterns). ~21.5h total. Sprint 1: Swarm Infrastructure P0. Sprint 2: Predictive Suggestions. Sprint 3: Adaptive Execution Loop. Sprint 4: Context Intelligence. Sprint 5: Skill Evolution. Sprint 6: Social Delivery. Sprint 7: MindShift+LifeSim Integration. Sprint 8: Org Saved Search. | ✅ NEW |
| TASK-PROTOCOL v6.0 | `docs/TASK-PROTOCOL.md` | v5.3 → v6.0: +Detect+Read step (SESSION-DIFFS + code-index), +trigger_reason on proposals, +Round-2 debate gate, +outcome verification gate, +session-end skill evolution check. | ✅ UPDATED |
| sprint-state.md updated | `memory/context/sprint-state.md` | Current position → roadmap written, Sprint 1 next. | ✅ UPDATED |

---

## Session 77 (2026-03-31) — BATCH-S: Vertex LLM + Invite UX + Smoke Test + Sprint 5 Q-Bank + S-05 generate:api

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| S-01: Startup guard ALL envs | `apps/api/app/config.py` → `assert_production_ready()` | RISK-011 check (old Supabase URL) now fires BEFORE `if app_env != "production": return` — was silently bypassed on staging/dev. | ✅ S-01 |
| S-02: supabase_project_ref in /health | `apps/api/app/routers/health.py` | `HealthResponse` gains `supabase_project_ref: str`. CEO can `curl /health` to verify Railway points to correct DB (`dwdgzfusjsobnixgyzjk`). `_extract_project_ref()` parses URL. `llm_ok` now checks Gemini OR Vertex key. | ✅ S-02 |
| S-03+S-08: Invite pre-fill + flicker fix | `apps/web/src/app/[locale]/(auth)/signup/page.tsx` | `inviteCode` state initialized from `searchParams.get("invite")`. `openSignup` state initialized to `false` when `?invite=` present (avoids 200-400ms async fetch flicker). | ✅ S-03+S-08 |
| S-04: Vertex + Groq LLM chain | `apps/api/app/services/llm.py` | Full rewrite. Singleton clients (`_vertex_client`, `_gemini_client`). `reset_llm_clients()` for test teardown. Fallback chain: Vertex Express → Gemini → Groq → OpenAI. `_call_vertex()`: `genai.Client(vertexai=True, api_key=...)`. `_call_groq()`: `AsyncGroq`, `llama-3.3-70b-versatile`. `generate_embedding` tries Vertex first. | ✅ S-04 |
| S-04: vertex_api_key in config | `apps/api/app/config.py` | `vertex_api_key: str = ""` added with Vertex Express comment. `VERTEX_API_KEY=AQ.Ab8...` in `.env`. | ✅ S-04 |
| S-05: pnpm generate:api | `apps/web/src/lib/api/generated/` | Ran `pnpm generate:api` from live FastAPI /openapi.json. New endpoints added: `signupStatusApiAuthSignupStatusGet` (GET /api/auth/signup-status), `validateInviteApiAuthValidateInvitePost` (POST /api/auth/validate-invite). Signup page updated to use type-safe `SignupStatusResponse` + `ValidateInviteResponse` imports. **Unblocks CEO E2E walk.** | ✅ S-05 |
| S-07: Invalid invite Telegram CTA | `apps/web/src/app/[locale]/(public)/invite/page.tsx` | Invalid code state: Telegram primary CTA (`t.me/yusifganbarov`, #2AABEE button), LinkedIn secondary, manual code entry link. 4 new i18n keys. `invite.invalidBody` updated to mention Telegram. | ✅ S-07 |
| S-09: Production smoke test | `scripts/prod_smoke_test.py` | NEW. Hits real Railway URL. Steps: health→supabase_project_ref, signup-status, validate-invite, auth gate (401), public profile, leaderboard. Exit code 1 on failure. Mistake #52 prevention. | ✅ S-09 |
| S-10: Sprint 5 question bank | `scripts/question-evolution/sprint-5/*.json` | 7 profession JSON files (70 questions total). All pass: irt_a≥1.2 ✅, hard irt_b 1.2-2.0 ✅, evaluation_rubric on all open_ended ✅, empathy_safeguarding≥2 per set ✅. | ✅ S-10 |
| S-10: Sprint 5 voting results | `scripts/question-evolution/sprint-5/voting-results.json` | Winner: financial-analyst (96/100). Full scoring + sprint-6 recommendations. | ✅ S-10 |

## Session 76 continued (2026-03-30) — BATCH-Q fixes: 661/661 tests — ALL GREEN

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Fix test_org_b2b.py mock chain | `apps/api/tests/test_org_b2b.py` → `_build_dashboard_mock` + `_build_volunteers_mock` | Added `t.limit.return_value = t` to both `assessment_sessions` mock branches. SEC-Q4 added `.limit()` caps to org queries, breaking the chainable mock. 4 tests were failing → all 7 passing. | ✅ |
| Fix test_smoke_assessment.py pre-existing failure | `apps/api/tests/test_smoke_assessment.py` → `test_submit_open_ended_uses_keyword_fallback` | Root cause: module-level `_COMPETENCY_SLUG_CACHE` warm from previous tests shifted iterator; ALSO missed daily LLM cap check DB call (line 462 in assessment.py) in mock sequence. Fix: `clear_question_cache()` at test start + added `[]` response for cap check at position 2 in mock list. 1 pre-existing failure → now passing. | ✅ |
| New Supabase project keys | `apps/api/.env`, `apps/web/.env.local`, `apps/api/app/config.py` | New paid project `dwdgzfusjsobnixgyzjk` (Sydney). SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY, SUPABASE_PUBLISHABLE_KEY all updated. RISK-011 startup guard blocks boot if old project URL still present. | ✅ |
| SEC-Q2: Percentile visibility filter | `apps/api/app/routers/profiles.py` → `get_public_profile` | Both COUNT queries for percentile_rank now filter `.eq("visibility", "public")`. Previously counted private/badge_only scores → leaked aggregate platform stats. | ✅ SEC-Q2 |
| SEC-Q2: Username enumeration rate | `apps/api/app/routers/profiles.py` → `get_public_profile` | Rate limit changed from `RATE_DEFAULT` (60/min) to `RATE_DISCOVERY` (10/min). Prevents brute-force username enumeration. | ✅ SEC-Q2 |
| SEC-Q3: beta-funnel org-only guard | `apps/api/app/routers/stats.py` → `get_beta_funnel_stats` | Volunteers get 403 FORBIDDEN. Previously all authenticated users could access platform health metrics (completion rates, abandonment rates, user counts). | ✅ SEC-Q3 |
| SEC-Q4/BUG-005: ORM cap on org queries | `apps/api/app/routers/organizations.py` → `get_org_dashboard` + `list_org_volunteers` | `.limit(2000)` cap on dashboard sessions, `.limit(10_000)` on volunteer list. Both log WARNING at cap. Prevents OOM at 10k users. | ✅ SEC-Q4 |
| SEC-Q5: PII removed from logs | `apps/api/app/main.py`, `apps/api/app/routers/subscription.py`, `apps/api/app/routers/organizations.py` | 3 log statements fixed: `str(e)` → `type(e).__name__` in Stripe log; `query=payload.query[:50]` → `query_len=len(payload.query)` in search log; global exception handler truncated to `[:120]`. | ✅ SEC-Q5 |
| Migrations to new project | `supabase/migrations/` → Supabase project `dwdgzfusjsobnixgyzjk` | Agent applying all 57 migrations via Supabase MCP. In progress (~26/57 at last check). | 🔄 IN PROGRESS |

## Session 76 continued (2026-03-30) — BATCH-P: Security + UX + E2E Tests — 657/658 tests passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| SEC-ANSWER-01: Subscription gate on /answer | `apps/api/app/routers/assessment.py` → `submit_answer` | Fail-closed paywall check on POST /assessment/answer when `payment_enabled=True`. Returns 402 SUBSCRIPTION_REQUIRED for expired/cancelled status. Mirrors /start gate pattern. | ✅ SEC-ANSWER-01 |
| P0 paywall tests | `apps/api/tests/test_paywall_enforcement.py` | 2 new tests: `test_submit_answer_blocked_when_expired` + `test_submit_answer_blocked_when_cancelled`. Both verify 402 response. Total: 8/8 passing. | ✅ |
| ISSUE-Q4: Celebration pulse ring | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | Framer Motion pulse ring on badge circle for scores ≥75. Respects `useReducedMotion()` — ring suppressed for accessibility. `aria-hidden="true"`. | ✅ ISSUE-Q4a |
| ISSUE-Q4: Next-action cards | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` + EN/AZ locales | Replaced text-only bullets with 2 tappable nav cards: "Assess more competencies" → /assessment; "See your AURA score" → /aura. WCAG focus-visible ring. Score-contextual tip lines. | ✅ ISSUE-Q4b |
| ISSUE-AU3: NextStepCard on AURA page | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` + EN/AZ locales | 2 nav cards at bottom of AURA page: "Assess another competency" + "Leaderboard". Animate in with `revealed` state (0.75s delay). | ✅ ISSUE-AU3 |
| i18n: complete page keys | `apps/web/src/locales/en/common.json` + `apps/web/src/locales/az/common.json` | New keys: `nextStepAssess`, `nextStepAssessDesc`, `nextStepAura`, `nextStepAuraDesc`, `nextStepAuraScore`, `tipImprove`, `tipExcellent`. AZ uses formal Siz, collective framing. | ✅ |
| i18n: AURA page keys | `apps/web/src/locales/en/common.json` + `apps/web/src/locales/az/common.json` | New keys: `aura.nextSteps`, `aura.nextStepAssess`, `aura.nextStepAssessDesc`, `aura.nextStepLeaderboard`, `aura.nextStepLeaderboardDesc`. | ✅ |
| test_beta_user_journey.py (E2E chain) | `apps/api/tests/test_beta_user_journey.py` | 7 integrated E2E tests covering full beta user path: create profile → start assessment → submit answer → complete → AURA score → public profile → journey smoke. All 7 passing. Key contracts validated: db_admin for session UPDATE, raw_score not in response (CRIT-03), PublicProfileResponse schema. | ✅ QA-E2E |

## Session 76 continued (2026-03-30) — BATCH-O: Cultural Intelligence + Behavioral UX + Accessibility Polish — 648/649 tests passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| CI-ON1: Formal "Siz" throughout onboarding | `apps/web/src/locales/az/common.json` — onboarding section | 14 instances of informal `sən` replaced with formal `Siz` across all onboarding copy. AZ cultural standard: formal address for professional platform. | ✅ CI-ON1 |
| CI-ON2: ISO trust context | `apps/web/src/locales/az/common.json` → `onboarding.next2` | Added "ISO 10667-2 standartına uyğun" framing. Replaces "AI" with trust signal recognized in AZ market. | ✅ CI-ON2 |
| CI-ON3: Collective non-competitive reframe | `apps/web/src/locales/az/common.json` + `apps/web/src/locales/en/common.json` | `hiddenStrengthDesc`, `feature3Desc`, `shareText`, `leaderboard.emptyTitle/emptyDesc`, `nav.leaderboard`, `sharePrompt.title/desc` reframed from competitive to collective achievement framing. | ✅ CI-ON3 |
| CI-ON4: nav.leaderboard rename | `apps/web/src/locales/az/common.json` | "Liderlər Lövhəsi" (competitive) → "Ən Yaxşılar" (aspirational). Reduces competitive anxiety in collective culture. | ✅ CI-ON4 |
| CI-ON5: shareText formal + inclusive | `apps/web/src/locales/az/common.json` | "Sən də sına" → "Siz də yoxlayın". Formal address + active verb = professional tone. | ✅ CI-ON5 |
| CI-ON6: topPercent collective framing | `apps/web/src/locales/az/common.json` → `profile.topPercent` | "Ən yaxşı {{percent}}%" → "Ən yaxşıların {{percent}}% arasında". Membership framing not ranking. | ✅ CI-ON6 |
| CI-ON7: AI → alqoritm trust signal | `apps/web/src/locales/az/common.json` → `assessment.stillWorking` | "AI cavabınızı yoxlayır" → "qiymətləndirmə alqoritmi cavabınızı analiz edir". "AI" raises suspicion; "alqoritm" reads as systematic/fair. | ✅ CI-ON7 |
| CI-PUB1: 3 hardcoded EN strings on public profile | `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx` + both locales | `getAuraScore`, `foundingMember`, `founding1000`, `getStarted` — all hardcoded English replaced with `t()` calls. Critical: public profile is viral share target — was always showing EN to AZ users. | ✅ CI-PUB1 |
| BATCH-O A1: Pre-select communication | `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx` | Default selection `new Set(["communication"])` when no `?competency=` param. Eliminates 8-way decision paralysis on first load. | ✅ BATCH-O A1 |
| BATCH-O A3: Cooldown 429 with minutes | `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx` + both locales | 429 response now reads `Retry-After` header, shows exact wait time: `t("assessment.cooldownError", { minutes: waitMin })`. Turns dead 429 into re-engagement message. `cooldownError` key added to both locales. | ✅ BATCH-O A3 |
| BATCH-O ON1: Pre-select onboarding competency | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx` | `selectedCompetency` state defaults to `"communication"`. Reduces first-time user decision burden. | ✅ BATCH-O ON1 |
| BATCH-O ON3: positive visible_to_orgs | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx` + both locales | Replaced checkbox with positive confirmation text: "✓ Profiliniz təşkilatlara görünəcək". Checkbox was causing voluntary opt-outs before users understood the value. `visibleToOrgsInfo` key added. | ✅ BATCH-O ON3 |
| BATCH-O Q-counter cap | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` | `Math.min(answeredCount + 1, ESTIMATED_QUESTIONS)` — counter never shows "9 of 8". Off-by-one UX confusion fixed. | ✅ BATCH-O Q |
| BATCH-O SHARE: navigator.share() i18n | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` + both locales | `shareBody`, `shareBodyLow`, `shareTitle`, `shareTitleLow` keys added to both locales. Was hardcoded English template literals — every share from Baku users went to Telegram in English. Critical viral path fix. | ✅ BATCH-O SHARE |
| BATCH-O SHARE2: topPercent on complete page | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | Hardcoded "top X%" replaced with `t("profile.topPercent", { percent })`. | ✅ BATCH-O SHARE2 |
| BATCH-O AURA1: useReducedMotion | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Counter animation duration: `prefersReducedMotion ? 0 : 2000`. Share modal timer: 3000 → 5000ms. WCAG 2.2 motion preference compliance. | ✅ BATCH-O AURA1 |
| BATCH-O AURA2: skeleton loading state | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Full skeleton with animated pulse cards replaces bare spinner. Removed unused `Loader2` import. | ✅ BATCH-O AURA2 |
| BATCH-O AURA3: Continue routes to active session | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Added `useAssessmentStore` → reads `sessionId`. Continue button: `/${locale}/assessment/${activeSessionId}` when session active, else `/assessment`. Prevents routing to selection screen mid-assessment. | ✅ BATCH-O AURA3 |
| BATCH-O DASH1: useReducedMotion on dashboard | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | `pageVariantsReduced` + `sectionVariantsReduced` — disables translate/opacity animation for reduced-motion users. | ✅ BATCH-O DASH1 |
| BATCH-O DASH2: 44px dismiss buttons | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | Trial/share banner dismiss buttons: `size-5` → `size-11` (44px WCAG tap target). Color: `opacity-60` → `text-amber-600/700` for visibility. | ✅ BATCH-O DASH2 |
| BATCH-O DASH3: share prompt gate | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | Share prompt gated: `showSharePrompt = hasScore && !sharePromptDismissed && !!profile?.username && !(!bannerDismissed && (isTrial \|\| isExpired))`. Prevents two competing banners. | ✅ BATCH-O DASH3 |
| BATCH-O WCAG: sr-only table in radar chart | `apps/web/src/components/aura/radar-chart.tsx` + both locales | Added `<table className="sr-only">` with competency/score data. SVG `aria-hidden="true"`. Screen readers now get full chart data. `aura.competency` + `aura.score` keys added. | ✅ BATCH-O WCAG |

## Session 76 continued (2026-03-30) — BATCH-N: Growth + Safety Wave — 648/649 tests passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| RISK-N01: Telegram hard fail | `apps/api/app/config.py` → `assert_production_ready()` | Hard-errors if `TELEGRAM_WEBHOOK_SECRET` empty in prod — bot can't be silently dead at launch. | ✅ RISK-N01 |
| RISK-N02: Stripe hard fail | `apps/api/app/config.py` → `assert_production_ready()` | Hard-errors if `PAYMENT_ENABLED=True` + `STRIPE_WEBHOOK_SECRET` empty — blocks unsigned webhook spoofing before payments activate. | ✅ RISK-N02 |
| GROW-N01: Silver share copy | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` + EN/AZ locales | Silver tier (60-74) now sees "Building momentum — share your progress and challenge a peer" instead of "You're in the top tier" (factually wrong for Silver). | ✅ GROW-N01 |
| GROW-M02: Cooldown notification | `apps/api/app/routers/assessment.py` + EN/AZ locales | Fire-and-forget `notify()` call when cooldown is hit — tells user exactly how many minutes until retake is ready. Turns dead-end 429 into re-engagement nudge. | ✅ GROW-M02 |
| PROD-M03: Share buttons mobile | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | Both share buttons: `w-full sm:w-auto min-h-[44px]` — full-width on mobile, 44px tap targets, no overflow at 375px. | ✅ PROD-M03 |
| GROW-M03: Public profile peer benchmark | `apps/api/app/schemas/profile.py`, `apps/api/app/routers/profiles.py`, `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx`, new `apps/web/src/components/profile/challenge-button.tsx`, EN/AZ locales | `percentile_rank` added to PublicProfileResponse. Profile shows "Top X%" stat. "Challenge a peer" button copies `volaura.app/?ref=[username]` to clipboard. 3 i18n keys added. | ✅ GROW-M03 |
| ARCH-M03: pending_aura_sync banner | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` + EN/AZ locales | Amber banner shows when `result.aura_updated === false` — "Your AURA score is being recalculated — check back in a few minutes." Invisible on happy path. | ✅ ARCH-M03 |

## Session 76 continued (2026-03-30) — BATCH-M: Launch Readiness Wave — 648/649 tests passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| RISK-M01: LLM cost spiral guard | `apps/api/app/config.py` → `assert_production_ready()` | Hard error if Gemini configured without Groq on Railway. Prevents $240/day cost spiral when Gemini rate-limits and OpenAI paid fallback activates. | ✅ RISK-M01 |
| ARCH-M02: Leaderboard period index | `supabase/migrations/20260330180000_add_leaderboard_period_index.sql` | Composite index `(visibility, last_updated DESC, total_score DESC)` on aura_scores. Applied to prod via MCP. Leaderboard period queries (weekly/monthly) no longer full-scan. | ✅ ARCH-M02 |
| QA-M01: Leaderboard auth tests | `apps/api/tests/test_new_endpoints.py` → `TestLeaderboard` | 2 tests: `is_current_user=True` when auth token matches entry, `is_current_user=False` for all when no auth. Covers LEADERBOARD-01 implementation. | ✅ QA-M01 |
| GROW-M01: Silver share box | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | Share box now shown for score ≥60 (Silver), not ≥75 (Gold). Ghost button only for <60. Wider share funnel. | ✅ GROW-M01 |
| PROD-M01: Answer saved indicator | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` | 600ms "Saved ✓" state on submit button after successful answer save. `answerSaved` state + `isMounted` guard. EN+AZ keys added. | ✅ PROD-M01 |
| QA-M02: total_count tests | `apps/api/tests/test_new_endpoints.py` → `TestLeaderboardTotalCount` | 2 tests: (1) `total_count=200` when DB has 200 rows but page limit=50. (2) graceful fallback to `len(entries)` when count query raises. Both passing. | ✅ QA-M02 |
| QA-M03: Verification endpoint tests | `apps/api/tests/test_new_endpoints.py` → `TestVerificationEndpoint` | 5 tests: happy path 201, token_used→409, expired→410, not_found→404, AURA blend math (rating=4 + existing=75 → blended=77.0). All passing. | ✅ QA-M03 |

## Session 76 continued (2026-03-30) — BATCH-L: Security + UX + Leaderboard — 638/640 tests passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| SEC-03: display_name anonymization | `apps/api/app/routers/profiles.py` | Added `_anonymize_name()` at module level. Applied in `list_public_volunteers` loop — `display_name=_anonymize_name(row.get("display_name"))`. Closes org→discovery cross-reference deanonymization attack. | ✅ SEC-03 |
| OptionalCurrentUserId dep | `apps/api/app/deps.py` | New `get_optional_user_id()` async function + `OptionalCurrentUserId` Annotated type alias. Returns `str | None` — user id if valid JWT present, None otherwise. Used for public-but-personalizable endpoints. | ✅ LEADERBOARD-01 |
| Leaderboard is_current_user | `apps/api/app/routers/leaderboard.py` | Added `user_id: OptionalCurrentUserId` to `get_leaderboard()`. `is_current_user=bool(user_id and volunteer_id and user_id == volunteer_id)` in entry loop. Was always False. | ✅ LEADERBOARD-01 |
| Leaderboard total_count fix | `apps/api/app/routers/leaderboard.py` | Added post-loop count query with try/except fallback. `total_count` now reflects full DB count, not `len(entries)` (page size). Falls back gracefully if count query fails. | ✅ LEADERBOARD-02 |
| I18N-01: Missing locale keys | `apps/web/src/locales/en/common.json`, `apps/web/src/locales/az/common.json` | Added `aura.sharePromptTitle`, `aura.sharePromptBody`, `aura.coach.title`, `common.dismiss`. Both EN and AZ. Fixes AZ users seeing English on share modal and coach section. | ✅ I18N-01 |
| AURA-02: Zero-state split | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Split `if (!aura \|\| aura.total_score == null)` into two branches: `!aura` = "never started" (start button), `aura.total_score == null` = "in progress" (Clock icon + continue button). Added `Clock` import from lucide-react. | ✅ AURA-02 |
| I18N: assessmentInProgress keys | `apps/web/src/locales/en/common.json`, `apps/web/src/locales/az/common.json` | Added `aura.assessmentInProgress` and `aura.assessmentInProgressDesc` to both locales. Used by AURA-02 in-progress state. | ✅ AURA-02 |

## Session 76 continued (2026-03-30) — BATCH-K: Launch Readiness Sprint — 632/633 tests passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Remove dead Subscribe CTA | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | Replaced disabled "Subscribe" button with static "coming soon" text. Removed subscribeButton i18n key from both locales. | ✅ K-01 |
| AuraExplanationResponse schema | `apps/api/app/schemas/aura.py`, `apps/api/app/routers/aura.py` | Added AuraEvaluationItem, AuraCompetencyExplanation, AuraExplanationResponse Pydantic v2 schemas. response_model now on /aura/me/explanation. pnpm generate:api produces typed response. | ✅ K-02 |
| Fix share flow UTM + null username | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | Share button disabled until username loads. UTM params added (utm_source=assessment_complete). Both locale files: shareNudge + shareNudgeLow keys added. | ✅ K-03+09 |
| answer_version conflict test | `apps/api/tests/test_smoke_assessment.py` | New test: submit_answer returns 409 CONCURRENT_SUBMIT when optimistic lock fires (data=[]). | ✅ K-04 |
| Onboarding competency redirect | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx` | handleFinish() now passes selectedCompetency as ?competency= param. Assessment page already reads and pre-selects it. | ✅ K-05 |
| Org auth + owner_id removal | `apps/api/app/routers/organizations.py`, `apps/api/app/schemas/organization.py` | GET /api/organizations and /{org_id} now require CurrentUserId (was unauthenticated). owner_id removed from OrganizationResponse. Generated TS types updated. | ✅ K-06 |
| Session expiry tests | `apps/api/tests/test_smoke_assessment.py` | 2 new tests: submit_answer → 410 SESSION_EXPIRED, complete_assessment → 410 SESSION_EXPIRED. | ✅ K-07 |
| upsert_aura_score error handling | `apps/api/app/routers/assessment.py`, `supabase/migrations/20260330150000_add_pending_aura_sync.sql` | try/except around RPC call. On failure: logs error + sets pending_aura_sync=True on session row. HTTP 200 still returned. Migration adds pending_aura_sync BOOLEAN column + partial index. | ✅ K-08 |
| AURA endpoint rate limit | `apps/api/app/routers/aura.py` | GET /api/aura/{volunteer_id} rate limit changed from RATE_DEFAULT (60/min) to RATE_DISCOVERY (10/min). Prevents enumeration. Kept public for OG card fetches. | ✅ K-10 |
| Public profile zero-AURA state | `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx` | Clock icon + "Assessment in progress" + description replaces single dim text. i18n keys added to both locales. | ✅ K-11 |
| SENTRY_DSN warning | `apps/api/app/config.py` | validate_production_settings() warns if sentry_dsn is empty. | ✅ K-12a |
| keyword_fallback spike alert | `apps/api/app/core/assessment/bars.py` | Module-level hourly counter. Fires Telegram alert + logger.warning when 10th fallback occurs in current hour. | ✅ K-12b |
| /health uses Depends() | `apps/api/app/routers/health.py` | Replaced inline acreate_client() with SupabaseAdmin dependency. Test updated to mock admin dep. test_security.py updated too. | ✅ K-13 |
| Dashboard share prompt | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | One-time dismissible banner: "Your AURA profile is live!" shown after first score. Copy link + Telegram share. localStorage-persisted dismiss. i18n in both locales. | ✅ K-14 |
| Per-user daily LLM cap | `apps/api/app/core/assessment/bars.py`, `apps/api/app/routers/assessment.py` | force_degraded param on evaluate_answer(). Cap: 20 open-ended LLM calls/user/day. Over cap → keyword_fallback + reeval queue. Prevents budget drain from adversarial users. | ✅ K-15 |
| Test fixes | `apps/api/tests/test_profiles.py`, `apps/api/tests/test_security.py`, `apps/api/tests/test_subscription.py`, `apps/api/tests/test_health.py` | Mock SupabaseAdmin dep in tests that need it. profile create tests (3) + security headers + subscription unauthenticated (2) + health endpoint. | ✅ fixes |

## Session 76 continued (2026-03-30) — BATCH-C: Paywall + Subscription E2E — 623/623 tests passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Paywall gate | `apps/api/app/routers/assessment.py` | HTTP 402 SUBSCRIPTION_REQUIRED if subscription_status in ('expired', 'cancelled') on POST /api/assessment/start. Before any session creation. | ✅ SHIPPED |
| `/subscription/success` page | `apps/web/src/app/[locale]/(dashboard)/subscription/success/page.tsx` | Post-Stripe-checkout success page. Invalidates ['subscription'] + ['profile'] TanStack caches. Shows session_id reference (truncated). | ✅ NEW |
| `/subscription/cancelled` page | `apps/web/src/app/[locale]/(dashboard)/subscription/cancelled/page.tsx` | Post-Stripe-checkout cancel page. XCircle icon. CTAs: dashboard + settings. | ✅ NEW |
| Leaderboard → aura_scores_public | `apps/api/app/routers/leaderboard.py` | Switched from base aura_scores table to aura_scores_public view (security_barrier=TRUE). Period filter column: updated_at → last_updated. | ✅ FIXED |
| events_no_show removed | `apps/api/app/schemas/discovery.py`, `apps/api/app/routers/discovery.py` | Removed events_no_show from DiscoveryVolunteer. Field excluded from aura_scores_public — keeping it was a latent data-leak vector. | ✅ FIXED |
| stripe_customer_id excluded | `apps/api/app/routers/profiles.py` | GET /profiles/me now uses explicit column list. Excludes stripe_customer_id + stripe_subscription_id. Includes registration_number, registration_tier, subscription_status, trial_ends_at. | ✅ FIXED |
| Webhook race condition fix | `apps/api/app/routers/subscription.py` | _update_profile_subscription returns False on no-match → _handle_subscription_created returns bool → main dispatch raises HTTP 500 → Stripe retries. | ✅ FIXED |
| getattr antipattern removed | `apps/api/app/routers/subscription.py` | Replaced getattr(settings, "stripe_price_id", ...) with direct settings.stripe_price_id access. | ✅ FIXED |
| ESTIMATED_QUESTIONS = 8 | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` | Fixed: was 10, actual communication pool size is 8. Progress bar now accurate. | ✅ FIXED |
| Public profile registration badge | `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx` | PublicProfile interface + JSX: shows #0001 · Founding Member (founding_100) or #0342 · Early Member (founding_1000) badge. | ✅ NEW |
| Risk Manager + Readiness Manager | `packages/swarm/autonomous_run.py`, `memory/swarm/skills/risk-manager.md`, `memory/swarm/skills/readiness-manager.md`, `memory/swarm/agent-roster.md` | Two new permanent agents in PERSPECTIVES. ISO 31000 + Google SRE standards. Their first run found the paywall enforcement gap. | ✅ NEW |
| SESSION-DIFFS.jsonl bootstrap | `memory/swarm/SESSION-DIFFS.jsonl` | Bootstrap entry with all migrations + routes from previous sessions. Agents now have a baseline of shipped work. | ✅ NEW |
| TASK-PROTOCOL v5.1 Step 4.0.5 | `docs/TASK-PROTOCOL.md` | Completion Consensus step now has concrete output format: AGENT/TASKS COMPLETED/TESTS RAN/JOURNEY VERIFIED/MEMORY UPDATED/BLOCKERS/SIGN-OFF per agent. | ✅ UPDATED |
| test_paywall_enforcement.py | `apps/api/tests/test_paywall_enforcement.py` | 6 tests: blocked when expired, blocked when cancelled, allowed when trial, allowed when active, allowed when no profile row, error shape contract. | ✅ NEW |
| test_subscription_status_boundary.py | `apps/api/tests/test_subscription_status_boundary.py` | 5 tests: trial auto-expiry, future trial stays trial, 1-second boundary, no end date, Z-suffix ISO parsing. | ✅ NEW |
| Mock sequence updates | `tests/test_assessment_api_e2e.py`, `tests/test_security_hardening.py`, `tests/test_smoke_assessment.py` | Added {"subscription_status": "trial"} as first user mock entry in all tests that call POST /api/assessment/start. Rate limiter reset fixture added. | ✅ FIXED |

## Session 76 (2026-03-30) — Swarm Optimization Batch — 612/612 tests passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `session_end_hook.py` | `packages/swarm/session_end_hook.py` | On every push to main: captures git diff → `SESSION-DIFFS.jsonl`, injects RECENTLY SHIPPED block into `shared-context.md`. Closes 42% already-done proposals gap. | ✅ NEW |
| `skills_loader.py` | `packages/swarm/skills_loader.py` | Auto-matches task description against CLAUDE.md Skills Matrix using regex. Returns skill file content for injection into agent prompts. CLI: `--task "description"`. | ✅ NEW |
| `.github/workflows/session-end.yml` | `.github/workflows/session-end.yml` | Two jobs: (1) session-end-hook (captures diff on push), (2) session-mini-swarm (runs code-review mode swarm on changed files). Triggers on push to main for backend/migration/swarm code. | ✅ NEW |
| `autonomous_run.py` — SESSION-DIFFS.jsonl reader | `packages/swarm/autonomous_run.py` | `_read_project_state()` now reads last 3 SESSION-DIFFS.jsonl entries → injects RECENTLY SHIPPED section at top of agent context. Agents see git-level changes, not just static memory files. | ✅ UPDATED |
| `docs/TASK-PROTOCOL.md` v5.1 | `docs/TASK-PROTOCOL.md` | Added: Phase 0.7 (Sprint Gate DSP), Step 4.1.5 (Session-End Mini-Swarm), Step 4.2.5 (Retro Sim), 3 DSP auto-trigger modes (Session Hook/Code Gate/Retro Sim). Version bumped 5.0 → 5.1. | ✅ UPDATED |
| Trial subscription banner + settings section | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx`, `settings/page.tsx` | Amber/red trial countdown banner on dashboard (dismissible). Subscription section in settings with plan badge + days remaining. useSubscription hook. 16 i18n keys. | ✅ SHIPPED (BATCH-A) |
| Security hardening tests | `apps/api/tests/test_security_hardening.py` | 15 tests: rapid-restart cooldown (5) + prompt injection detection (8) + false-positive checks (2). All passing. | ✅ SHIPPED (BATCH-A) |
| Subscription router integration tests | `apps/api/tests/test_subscription.py` | 10 tests: GET status×4, checkout×3, webhook×3. All passing. | ✅ SHIPPED (BATCH-A) |
| `supabase/migrations/20260330000001_security_fixes_p0.sql` | Supabase | Crystal ledger idempotency UNIQUE INDEX; rapid-restart cooldown index; revoke avg_aura_score from anon+authenticated. | ✅ MIGRATION READY |
| `supabase/migrations/20260330100000_security_fixes_grants.sql` | Supabase | BrandedBy: REVOKE from authenticated; Notifications: DROP open INSERT policy; CEO inbox: documented intentional default-deny. | ✅ MIGRATION READY |
| `supabase/migrations/20260330110000_seed_questions_remaining_competencies.sql` | Supabase | 5 new MCQ questions for communication competency, IRT b-values -1.1 to 1.3. | ✅ MIGRATION READY |
| `apps/web/src/lib/api/configure-client.ts` | Frontend | SDK auth interceptor: Supabase Bearer token injected via @hey-api/client-fetch interceptors. Fixes unauthenticated generated SDK calls (HIGH security finding). | ✅ SHIPPED |

## Session 75 continued (2026-03-29) — Test suite: 574/574 passing

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| BARS fallback chain — add `_try_groq` patches | `tests/test_sprint8_fixes.py`, `tests/test_smoke_assessment.py` | Added `_try_groq` mock to all 3 BARS timeout tests. Groq sits between Gemini and OpenAI in the fallback chain; unpatched it called the real API and prevented OpenAI from being reached. | ✅ FIXED |
| assessment router — `status="in_progress"` for full pipeline | `tests/test_assessment_router.py` | Changed session fixture `status` from `"completed"` to `"in_progress"`. `completed` triggers early-return path (no RPC). Tests asserting `aura_updated=True` require `in_progress`. Admin mock call order corrected: call 1 = gaming UPDATE, call 2 = slug lookup. | ✅ FIXED |
| e2e tests — `app.dependency_overrides` pattern | `tests/test_assessment_api_e2e.py` | Converted all 3 tests from `patch()` to `app.dependency_overrides`. FastAPI captures dep references at import time; `patch()` doesn't intercept them. Fixed `MOCK_QUESTIONS.options` from `list[str]` to `list[dict]` (`{key, text_en, text_az}`). Removed `response=` kwarg from `submit_response()` (param doesn't exist). | ✅ FIXED |
| stats endpoint — RPC mock + rounding | `tests/test_new_endpoints.py`, `app/routers/stats.py` | Stats endpoint uses `db.rpc("avg_aura_score")` not table scan. Mock fixed to return RPC mock. Endpoint now calls `round(float(result.data), 1)`. | ✅ FIXED |
| smoke tests — LLM mocks return `(None, None)` tuples | `tests/test_smoke_assessment.py` | `_try_gemini`/`_try_groq` return `(scores, concept_details)` tuples. Mocking `return_value=None` caused unpacking errors. Fixed to `return_value=(None, None)`. | ✅ FIXED |
| RLS — UPDATE policy for `assessment_sessions` | `supabase/migrations/20260324000015_rls_audit_fixes.sql` | Added missing UPDATE policy "Users can only abandon own sessions" — `USING (auth.uid() = volunteer_id AND status = 'in_progress')`. Test `test_rls_session_update_policy_exists` was checking for this. | ✅ MIGRATION READY |

## Session 75 continued (2026-03-29) — QA Chaos Agent batch: 6 bugs

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| BUG-013: visibility filter in search | `apps/api/app/routers/organizations.py` | Added `.eq("visibility","public")` to rule-based aura_scores query + post-filter for semantic RPC path. Hidden/badge_only profiles no longer appear in org volunteer search. | ✅ FIXED |
| BUG-015: complete_assessment early return | `apps/api/app/routers/assessment.py` | Added early return when session status == "completed" — returns stored values without re-running pipeline. Prevents double aura_history append on race condition. | ✅ FIXED |
| BUG-009: retest cooldown .days → total_seconds | `apps/api/app/routers/assessment.py` | 3 locations: cooldown check (line ~124), info endpoint cooldown (line ~740), theta decay (line ~180). `.days` truncated fractional days; now uses `total_seconds() // 86400`. | ✅ FIXED |
| BUG-017: UNIQUE constraint on org owner | `supabase/migrations/20260329120000_organizations_owner_unique.sql` | `ALTER TABLE organizations ADD CONSTRAINT organizations_owner_id_unique UNIQUE (owner_id)`. Prevents duplicate orgs from race condition on simultaneous POST /api/organizations. | ✅ MIGRATION READY |
| BUG-003+014: intro_requests RLS hardening | `supabase/migrations/20260329120001_intro_requests_rls_hardening.sql` | Drops overly broad INSERT (TRUE) and unified UPDATE policies. Replaces with: org INSERT requires uid()=org_id; org UPDATE = withdraw only; volunteer UPDATE = accept/reject from pending only. | ✅ MIGRATION READY |

## Session 75 continued (2026-03-29) — BATCH E tail: Leyla P1 fixes

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `<a>` → `<Link>` in aura empty state | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Start assessment button in empty state was `<a>` (full-page reload on mobile). Changed to Next.js `<Link>` for client navigation. | ✅ FIXED |
| Null username guard | `apps/web/src/components/aura/share-buttons.tsx` | `username` prop changed to `string \| null \| undefined`. If null, renders "Set username in Settings to unlock sharing" instead of broken `/u/null` URLs. | ✅ FIXED |
| Assessment infinite spinner recovery | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` | Added `isStuck` state + 6s timeout. When `currentQuestion` is null after 6s on the question screen (refresh mid-session), shows recovery button → competency selection instead of infinite spinner. | ✅ FIXED |

## Session 75 (2026-03-29) — BATCH 2026-03-29-E: Simulation + Bug Fix Sprint

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Org row auto-creation | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx` | After profile creation for org accounts, auto-calls `POST /api/organizations` with display_name as org name. 409 silently ignored (idempotent). Fixes B2B launch blocker. | ✅ FIXED |
| .maybe_single() fix | `apps/api/app/routers/organizations.py` | 4 locations changed from `.single()` → `.maybe_single()`: get_my_organization, get_organization, get_org_dashboard, list_org_volunteers, assign_assessments. Prevents 500 errors. | ✅ FIXED |
| Discovery private field fix | `apps/api/app/routers/discovery.py` | Changed from `aura_scores` base table to `aura_scores_public` safe view. Removed `events_no_show` from select. Added `.gt("total_score", 0)` to exclude ghost profiles. | ✅ FIXED |
| AURA badge_only leak fix | `apps/api/app/routers/aura.py` | badge_only path now strips ALL private fields explicitly (last_updated, events_*, reliability_*) before constructing response. | ✅ FIXED |
| MCQ scoring fix | `apps/api/app/routers/assessment.py` | Case-insensitive comparison (.strip().lower() on both sides). Logger.warning when MCQ has no correct_answer. | ✅ FIXED |
| Double UPDATE fix | `apps/api/app/routers/assessment.py` | complete_assessment: merged gaming columns into single UPDATE for in_progress sessions. Eliminates race condition. | ✅ FIXED |
| Session expiry enforcement | `apps/api/app/routers/assessment.py` | expires_at checked in submit_answer AND complete_assessment. Returns 410 SESSION_EXPIRED. | ✅ FIXED |
| Signup org pre-select | `apps/web/src/app/[locale]/(auth)/signup/page.tsx` | `?type=organization` query param pre-selects org account type. useSearchParams added. | ✅ FIXED |
| Privacy consent error text | `apps/web/src/app/[locale]/(auth)/signup/page.tsx` | Separate i18n key `auth.privacyConsentRequired` for validation error vs consent label. | ✅ FIXED |
| Password hint inline | `apps/web/src/app/[locale]/(auth)/signup/page.tsx` | Inline hint below password field: "8+ characters, uppercase, lowercase, and a number." | ✅ FIXED |
| display_name required | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx` | step1Valid now requires display_name.trim().length >= 1. | ✅ FIXED |
| POST 404 fix | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx` | Removed `&& res.status !== 404` — POST 404 is now treated as a real error. | ✅ FIXED |
| Org CTA routing fix | `apps/web/src/components/landing/hero-section.tsx` | "Find talent" button routes to `signup?type=organization` instead of generic signup. | ✅ FIXED |
| Post-AURA share prompt | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Modal fires 3s after first AURA reveal. sessionStorage prevents repeat fires. Uses AnimatePresence + spring animation. | ✅ SHIPPED |
| Invite page | `apps/web/src/app/[locale]/(public)/invite/page.tsx` | Beta invite landing page with code allowlist (BETA_01-30, ORG_01-05, OPEN). Pre-selects org/volunteer type. 3s countdown auto-redirect to signup. Replaces waitlist mechanic. | ✅ SHIPPED |
| LinkedIn DAY 7 CTA | `docs/content/LINKEDIN-SERIES-CLAUDE-CTO.md` | "If you want to be in the first 50 → volaura.app/invite" added before P.S. UTM URL noted for Yusif. | ✅ UPDATED |

## Session 74 (2026-03-29) — BATCH 2026-03-29-J: Pre-existing Test Fixes

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| test_profiles.py fix | `apps/api/tests/test_profiles.py` | Added `db.maybe_single = MagicMock(return_value=db)` to circular mock. Fixes 2 pre-existing failures (`TypeError: MagicMock can't be awaited`). | ✅ FIXED |
| test_aura.py fix | `apps/api/tests/test_aura.py` | Same `maybe_single` fix + updated AURA_ROW fixture: `overall_score` → `total_score`, added `visibility/percentile_rank/effective_score/last_updated` fields, updated assertion. Fixes 2 pre-existing failures. | ✅ FIXED |

## Session 74 (2026-03-29) — BATCH 2026-03-29-I: Verification Flow Tests

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Verification tests | `apps/api/tests/test_verification.py` | 9 tests: valid token→200, token not found→404, already used→409, expired→410, submit→201+rpc, submit expired→410, TOCTOU race→409, rating=6→422, rating=0→422. AURA blend math verified (70*0.6+80*0.4=74). All 9 passing. | ✅ SHIPPED |

## Session 74 (2026-03-29) — BATCH 2026-03-29-H: Intro Request Tests

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Intro request tests | `apps/api/tests/test_intro_request.py` | 8 integration tests: success→201+notification, non-org→403, volunteer missing→404, not discoverable→403, org target→422, duplicate→409, auth required, schema validation. Rate limiter reset fixture (autouse). All 8 passing. | ✅ SHIPPED |

## Session 74 (2026-03-29) — BATCH 2026-03-29-G: Notifications Bug Fix + Tests

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Notifications router bug fix | `apps/api/app/routers/notifications.py` | Fixed `request: object` → `request: Request` on all 4 endpoints. All endpoints were returning 422 in production (FastAPI couldn't inject the limiter's Request object). | ✅ FIXED |
| Profile view tests | `apps/api/tests/test_profile_view.py` | 6 integration tests: org sends notification, non-org silent 204, 24h dedup, self-view suppressed, volunteer not found, unauthenticated 401. All 6 passing. | ✅ SHIPPED |
| Notifications tests | `apps/api/tests/test_notifications.py` | 10 integration tests: unread-count (count + zero), list (items + empty + pagination + limit-max), mark-all-read, mark-single-read, 404 on not-found, auth required. All 10 passing. | ✅ SHIPPED |

## Session 74 (2026-03-29) — BATCH 2026-03-29-F: org_view Notification (S5-02)

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Profile view endpoint | `apps/api/app/routers/profiles.py` | POST /api/profiles/{username}/view — org-only, sends `org_view` notification to volunteer, deduped 1/24h per (org, volunteer) pair. 204 for non-org callers. | ✅ SHIPPED |
| ProfileViewTracker | `apps/web/src/components/profile/profile-view-tracker.tsx` | Client component fires POST on mount if viewer is logged in. Swallows all errors. Rendered in u/[username]/page.tsx. | ✅ SHIPPED |

## Session 74 (2026-03-29) — BATCH 2026-03-29-E: Sprint A1 Acceptance Tests

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Sprint A1 acceptance tests | `apps/api/tests/test_sprint_a1_acceptance.py` | 6 tests: emit_assessment_rewards (crystal write, below-bronze guard, idempotency) + GET /character/state (after assessment, new user, multiple skills). All 6 passing. | ✅ SHIPPED |

## Session 74 (2026-03-29) — BATCH 2026-03-29-D: Remaining 100-user blockers

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Assessment retry fix | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` | nextCompetency() moved after successful fetch (was eager — caused stuck state on error). Transition screen now shows error Alert + loading state on Continue button (BLOCKER-14) | ✅ SHIPPED |
| k6 load test script | `scripts/load_test.js` | 100 concurrent user test: health + assessment flow. Pass criteria: p(95)<3s, 0×504, error rate <1%. CEO runs: `k6 run scripts/load_test.js` (BLOCKER-11 script ready) | ✅ SHIPPED |
| Disaster recovery runbook | `docs/DISASTER-RECOVERY-RUNBOOK.md` | 7 incident scenarios: API down, 504, auth, DB, LLM degraded, bad deploy, Telegram alert. Env var table, RTO/RPO targets, post-incident checklist (BLOCKER-19) | ✅ SHIPPED |
| LAUNCH-BLOCKERS.md | `docs/LAUNCH-BLOCKERS.md` | BLOCKERs 12, 14, 19 marked resolved. BLOCKER-11 script ready. BLOCKER-15, 13 already marked in Batch B. | ✅ UPDATED |

## Session 74 (2026-03-29) — BATCH 2026-03-29-C: Mobile 375px Polish

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Skeleton grid fix | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | `grid-cols-3` → `grid-cols-1 sm:grid-cols-3` — skeleton cards no longer cramped on mobile | ✅ SHIPPED |
| Hide competencies column mobile | `apps/web/src/app/[locale]/(dashboard)/org-volunteers/page.tsx` | `w-16 text-right` span → `hidden sm:inline` — volunteer row doesn't overflow at 375px | ✅ SHIPPED |
| Filter buttons flex-wrap | `apps/web/src/app/[locale]/(dashboard)/org-volunteers/page.tsx` | `flex gap-1.5 shrink-0` → `flex flex-wrap gap-1.5` — status filter buttons wrap on small screens | ✅ SHIPPED |

## Session 73 (2026-03-29) — TASK-PROTOCOL v5.0 + Agent Improvement Proposals

| File | Location | What it does | Status |
|------|----------|-------------|--------|
| TASK-PROTOCOL v5.0 | `docs/TASK-PROTOCOL.md` | 14 changes from 6 agent proposals: Step 0.5 flow detection, parallel proposals with EFFORT, routing lock (1.0.5), MICRO fastpath, schema gate in 3.1, test execution gate 3.2.5, cross-QA gate 3.4, C3 verification teeth, C3.5 brief re-approval, C5.5 cultural copy sign-off, completion consensus 4.0.5, "What's next" in batch close | ✅ UPDATED |
| patterns.md | `memory/context/patterns.md` | 8 new patterns P-049→P-056: flow detection, MICRO fastpath, proactive "what's next", parallel proposals, EFFORT estimates, cross-QA, test execution = "verified", brief re-approval | ✅ UPDATED |
| sprint-state.md | `memory/context/sprint-state.md` | Session 73 entry added | ✅ UPDATED |

## Sessions 71-72 (2026-03-29) — PR Agency structure + TASK-PROTOCOL v4.1

| File | Location | What it does | Status |
|------|----------|-------------|--------|
| SESSION-FINDINGS.md | `docs/SESSION-FINDINGS.md` | Living intelligence document — 18 findings logged. Added to startup read protocol. | ✅ NEW |
| Communications Strategist skill | `memory/swarm/skills/communications-strategist.md` | Sits above copywriters. Owns narrative arc, fills CONTENT-BRIEF-TEMPLATE before copywriters write. | ✅ NEW |
| AZ LinkedIn Audience Profile | `docs/AZ-LINKEDIN-AUDIENCE.md` | Cultural intelligence baseline — WHY TONE-OF-VOICE rules exist. Required reading before any post. | ✅ NEW |
| CONTENT-BRIEF-TEMPLATE.md | `docs/CONTENT-BRIEF-TEMPLATE.md` | Fill-in brief with P1-P7 constraints baked in, hook constraint, management risk scan, PS instruction. | ✅ NEW |
| CULTURAL-AUDIT-CHECKLIST.md | `docs/CULTURAL-AUDIT-CHECKLIST.md` | 9-check pre-publish audit (2 min). APPROVE/REVISE/BLOCK before CEO sees post. | ✅ NEW |
| copywriter-team.md | `memory/swarm/skills/copywriter-team.md` | Rule 0 added: READ real files. Brief template requires 5 mandatory source files. | ✅ UPDATED |
| TASK-PROTOCOL v4.1 | `docs/TASK-PROTOCOL.md` | 5 Content Batch Gates C1-C5. CTO plan→council critique flow documented. | ✅ UPDATED |
| ADR-007 | `docs/DECISIONS.md` | Swarm architecture decision: keep current architecture (PATH A), borrow MiroFish methodology only. | ✅ LOGGED |
| CLAUDE.md | `CLAUDE.md` | SESSION-FINDINGS.md in startup read list. Skills Matrix updated for content batches. | ✅ UPDATED |
| agent-roster.md | `memory/swarm/agent-roster.md` | Communications Strategist + Cultural Intelligence routing added. | ✅ UPDATED |
| LinkedIn series DAY 2-7 | `docs/content/LINKEDIN-SERIES-CLAUDE-CTO.md` | All posts rewritten by SPARK/CORTEX/PRISM competition. Winners assembled. "My name is Claude" opener. | ✅ UPDATED |

## Session 70 (2026-03-29) — BATCH 2026-03-29-B: beta UX fixes + GIN index + docs

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Signup loading spinner | `apps/web/src/app/[locale]/(auth)/signup/page.tsx` | Added Loader2 icon to submit button during loading state (BLOCKER-13) | ✅ SHIPPED |
| "Still working…" message | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` | isSlowFetch state + useEffect: shows "Still working — AI is reviewing…" after 4s of submit wait | ✅ SHIPPED |
| stillWorking i18n key | `apps/web/src/locales/en/common.json`, `az/common.json` | "assessment.stillWorking" key added in EN + AZ | ✅ SHIPPED |
| GIN index migration | `supabase/migrations/20260329060000_character_events_gin_index.sql` | idx_character_events_payload_gin (GIN on payload) + idx_character_events_user_type (user_id, event_type) | ✅ READY TO APPLY |
| LAUNCH-BLOCKERS.md updated | `docs/LAUNCH-BLOCKERS.md` | Blockers 1,2,8,9,17 marked resolved. Accurate readiness signal for CEO. | ✅ UPDATED |

Discovered: BLOCKER-14 (retry button) already done. BLOCKER-8 already documented in rate_limit.py. All 10 must-fix blockers now resolved or CEO-actions-only.

---

## Session 70 (2026-03-29) — BATCH 2026-03-29-A: cultural fixes + RU wiring + i18n fix

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| CIS-001: tier labels reframed | `apps/web/src/locales/en/common.json`, `az/common.json` | "Top 5%/20%/45%" → "Expert/Advanced/Proficient"; "Where do you rank?" → "Your professional level" / "Peşəkar səviyyəniz" | ✅ SHIPPED |
| CIS-002: patronymic hint | `apps/web/src/locales/az/common.json` | namePlaceholder: "Tam adınız" → "Adınız Soyadınız (məs. Yusif Eldar oğlu)" | ✅ SHIPPED |
| scenario_ru in question delivery | `apps/api/app/schemas/assessment.py`, `services/assessment/helpers.py`, `routers/assessment.py` | question_ru added to QuestionOut + QuestionResultOut; SELECT includes scenario_ru; wired from helpers.py | ✅ SHIPPED |
| translate_ru.py script | `scripts/translate_ru.py` | Batch-translates scenario_en → scenario_ru via Gemini 2.0 Flash. Dry-run by default. Run: `python scripts/translate_ru.py --apply` | ✅ NEW |
| MindShift i18n.ts circular import fix | `src/i18n.ts` | Removed static useStore import. Deferred subscription via setTimeout(0) + dynamic import. Eliminates ReferenceError on boot. | ✅ SHIPPED |

Verified: Welcome page complete (no work needed). UTM capture complete (utm-capture.tsx already wired). Badge share complete (ShareButtons component already wired). Sprint A1 rewards already built in Session 68.

---

## Session 69 (2026-03-29) — Production blockers + Sentry + strategic simulation

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Health check v2 | `apps/api/app/routers/health.py` | Verifies Supabase + LLM config, returns degraded/ok | ✅ SHIPPED |
| Assessment localStorage | `apps/web/src/stores/assessment-store.ts` | sessionStorage → localStorage (refresh-safe) | ✅ SHIPPED |
| Session expiry warning | `apps/web/src/app/.../assessment/[sessionId]/page.tsx` | 3s warning before redirect to login | ✅ SHIPPED |
| ErrorAlertingMiddleware | `apps/api/app/middleware/error_alerting.py` | 5xx → CEO Telegram (rate-limited 1/5min) | ✅ NEW |
| Sentry monitoring | Railway env + `apps/api/app/config.py` | Org: volaura, Project: volaura-api, DSN configured | ✅ DEPLOYED |
| All LLM keys on Railway | Railway env vars | Gemini + Groq + OpenAI + DeepSeek — 27 total vars | ✅ DEPLOYED |
| P1/P2 batch fixes | Multiple routers + frontend | badges maybe_single, skills RATE_LLM, leaderboard avatar, org grid responsive, telegram atomic write, embeddings logging, LLM structured logging, config warning | ✅ SHIPPED |
| LAUNCH-BLOCKERS.md | `docs/LAUNCH-BLOCKERS.md` | 19-item launch readiness checklist with capacity math | ✅ NEW |
| STRATEGIC-SIMULATION-RESULTS.md | `docs/STRATEGIC-SIMULATION-RESULTS.md` | DSP 3-path simulation, Agile framework, CEO action list | ✅ NEW |
| CEO-QUESTIONS-RESOLVED.md | `docs/CEO-QUESTIONS-RESOLVED.md` | 9 strategic questions answered from memory + research | ✅ NEW |
| GROWTH-STRATEGY-PLAYBOOK.md | `docs/GROWTH-STRATEGY-PLAYBOOK.md` | Grants + registration + promotion with verified data | ✅ NEW |
| SWARM-HANDOFF.md | `docs/SWARM-HANDOFF.md` | Swarm documentation for partner CTOs | ✅ NEW |
| AUDIT-REPORT.md | `docs/AUDIT-REPORT.md` | 62 findings (8 P0, 19 P1, 22 P2, 13 P3) | ✅ NEW |
| TASK-PROTOCOL v4.0 | `docs/TASK-PROTOCOL.md` | Team-first proposals, parallel batches, agent override | ✅ SHIPPED |
| 3 improved skills | `.claude/skills/` | accelerator-grant-searcher, promotion-agency, startup-registration-finder | ✅ NEW |
| Firuza v2.0 | `memory/swarm/skills/firuza-assistant.md` | Upgraded from reactive → proactive, expanded scope | ✅ UPDATED |

Blockers resolved: 9/10 (4 code fixes, 4 false positives, 1 Sentry+keys deployed). BUG-07+BUG-08 confirmed resolved via Supabase MCP.

---

## Session 68 (2026-03-29) — Sprint B+D+A: Type generation + onboarding fix + notifications

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `pnpm generate:api` output | `apps/web/src/lib/api/generated/` | 419 types, 78 SDK functions from 66 API paths. ADR-003 compliance. | ✅ SHIPPED |
| ProxyHeadersMiddleware fallback | `apps/api/app/main.py` | starlette 1.0 removed proxy_headers → fallback to uvicorn import | ✅ SHIPPED |
| Callback onboarding routing | `apps/web/src/app/[locale]/(auth)/callback/page.tsx` | New users (no profile) → /onboarding. Returning users → /dashboard. | ✅ SHIPPED |
| notification_service.py | `apps/api/app/services/notification_service.py` | Fire-and-forget `notify()` helper for all routers | ✅ NEW |
| Assessment notifications | `apps/api/app/services/assessment/rewards.py` | `assessment_complete` + `badge_earned` notifications on rewards emit | ✅ SHIPPED |
| Org notification refactor | `apps/api/app/routers/organizations.py` | Inline notification insert → uses notification_service.py | ✅ SHIPPED |
| SWARM-HANDOFF.md | `docs/SWARM-HANDOFF.md` | Complete swarm documentation for partner CTOs | ✅ NEW |
| MINDSHIFT-INTEGRATION-SPEC corrections | `docs/MINDSHIFT-INTEGRATION-SPEC.md` | Streak=Zustand, XP=placeholder, stat names corrected | ✅ UPDATED |

Verified: BUG-07 (all 33 migrations in production), BUG-08 (autoconfirm ON). Both resolved.

### Sprint E additions (same session):

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Public AURA privacy fix | `apps/api/app/routers/aura.py` | Strip `last_updated` from public `/{volunteer_id}` (Security P2) | ✅ SHIPPED |
| CompetencyBreakdown freshness | `apps/web/src/components/aura/competency-breakdown.tsx` | Per-competency freshness label (teal/amber/slate) + retake CTA | ✅ SHIPPED |
| effective_score display | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | AURA page shows decay-adjusted score, not raw | ✅ SHIPPED |
| AuraScore type + transformer | `apps/web/src/lib/api/types.ts` | Added `effective_score` to AuraScore type + toAuraScore() | ✅ SHIPPED |
| Freshness i18n (EN + AZ) | `apps/web/src/locales/{en,az}/common.json` | 6 new keys each: retakeNow, retakeIn, freshnessRecent/Weeks/Month, freshnessLabel | ✅ SHIPPED |

### P0 Batch fixes (same session):

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| TASK-PROTOCOL v4.0 | `docs/TASK-PROTOCOL.md` | Team-first proposals, parallel batches, agent override, proportional gates | ✅ SHIPPED |
| Public profile meta fix | `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx` | "volunteer profile" → "professional profile" in meta description | ✅ SHIPPED |
| Discover page copy fix | `apps/web/src/app/[locale]/(dashboard)/discover/page.tsx` | "Volunteer discovery" → "Talent discovery" in error message | ✅ SHIPPED |
| Role-based nav filtering | `apps/web/src/components/layout/sidebar.tsx` | Org-only items (my-org, org-volunteers, discover) hidden for professionals | ✅ SHIPPED |
| volunteerCta copy fix (EN+AZ) | `apps/web/src/locales/{en,az}/common.json` | "Contribute to our events" → "Share your expertise at our events" | ✅ SHIPPED |

---

## Session 67 (2026-03-29) — Sprint E1: Ecosystem Identity — rebrand + MindShift integration spec

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| EN i18n rebrand | `apps/web/src/locales/en/common.json` | 20+ volunteer strings → talent/professionals/participants | ✅ SHIPPED |
| AZ i18n rebrand | `apps/web/src/locales/az/common.json` | 20+ könüllü strings → istedadlar/peşəkarlar/iştirakçılar | ✅ SHIPPED |
| CLAUDE.md positioning | `CLAUDE.md` | Project Overview: "Verified Professional Talent Platform", 5-product ecosystem | ✅ SHIPPED |
| PROJECT-OVERVIEW.md | `docs/PROJECT-OVERVIEW.md` | Full living description of 5-product ecosystem | ✅ NEW |
| ADR-006 | `docs/adr/ADR-006-ecosystem-architecture.md` | Shared Supabase, event-sourced character_state, crystal economy decisions | ✅ NEW |
| MINDSHIFT-INTEGRATION-SPEC.md | `docs/MINDSHIFT-INTEGRATION-SPEC.md` | Exact API contract for MindShift ↔ VOLAURA (Sprint E2 implementation guide) | ✅ NEW |

Note: character_state API, migrations, and rewards service confirmed already built in Sprint 52-54. Not rebuilt this session.

---

## Session 65 (2026-03-29) — TASK-PROTOCOL recursive audit (CX-1 to CX-4) + Assessment UX

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| `deduct_crystals_atomic` RPC in brandedby.py | `apps/api/app/routers/brandedby.py` | TOCTOU crystal double-spend race fixed via pg_advisory_lock RPC | ✅ SHIPPED | Concurrent queue skip requests — only one deducts |
| `@limiter.limit(RATE_DEFAULT)` on `/my/registrations` | `apps/api/app/routers/events.py` | Rate limit + .limit(50) cap added to previously unlimited endpoint | ✅ SHIPPED | Check endpoint decorator |
| `avg_aura_score()` PostgreSQL RPC | `supabase/migrations/20260329055859_avg_aura_score_rpc.sql` | O(1) server-side AVG replaces O(n) Python fetch in stats.py | ✅ DEPLOYED | `SELECT public.avg_aura_score()` → returns real value |
| `stats.py` avg_aura_score via RPC | `apps/api/app/routers/stats.py` | Uses db.rpc("avg_aura_score") instead of fetching all rows | ✅ SHIPPED | GET /api/stats/public returns real avg |
| `skills.py` JSONB extraction fix | `apps/api/app/routers/skills.py` | Reads competency_scores from aura_scores JSONB column (was querying non-existent table) | ✅ SHIPPED | Execute skill → gets real competency context |
| `API_BASE` exported constant | `apps/web/src/lib/api/client.ts` | Single source for API URL, imported by 11 pages | ✅ SHIPPED | No more duplicate env lookups |
| `RequestIdMiddleware` | `apps/api/app/middleware/request_id.py` | X-Request-ID UUID4 on all responses, correlation tracing | ✅ SHIPPED | Check any API response headers |
| `assert_production_ready()` | `apps/api/app/config.py` | Raises RuntimeError at startup if APP_ENV=production and SERVICE_KEY empty or APP_URL=localhost | ✅ SHIPPED | Deploy with missing keys → fails fast |
| CORS `expose_headers: X-Request-ID` | `apps/api/app/main.py` | Browsers can read X-Request-ID cross-origin | ✅ SHIPPED | Check CORS response headers |
| `MeResponse` / `MessageResponse` schemas | `apps/api/app/routers/auth.py` | response_model on GET /auth/me, DELETE /auth/me, POST /auth/logout | ✅ SHIPPED | OpenAPI /docs shows typed schemas |
| Rate limit on `GET /skills/` | `apps/api/app/routers/skills.py` | @limiter.limit(RATE_DEFAULT) added to list_skills() | ✅ SHIPPED | Check endpoint decorator |
| Assessment `?competency=` pre-select | `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx` | Reads URL param, pre-selects competency, shows info callout. Suspense wrapper added. isMounted fix. | ✅ SHIPPED | Navigate to /assessment?competency=communication |
| `assessment.recommended` + `assessment.min` i18n | `apps/web/src/locales/en/common.json` + `az/common.json` | Translation keys for info callout | ✅ SHIPPED | Check locales |
| `response_time_ms` tracking | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` | Sends real elapsed ms (was always 0) — anti-gaming flags now have real data | ✅ SHIPPED | Submit answer → check request payload |
| `competencyLabel` i18n on results page | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | Uses t('competency.{slug}') instead of string manipulation | ✅ SHIPPED | Switch to AZ locale → see AZ competency name |

---

## Session 63 (2026-03-29) — SPRINTS B1-B5: SWARM SELF-IMPROVEMENT

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| `SWARM_DATA_DIR` env var | `packages/swarm/structured_memory.py` | StructuredMemory persists to repo (memory/swarm/structured/) instead of ephemeral ~/.swarm/. GitHub Actions sets this. | ✅ SHIPPED | Check swarm-daily.yml env block |
| `git pull --rebase` before push | `.github/workflows/swarm-daily.yml` | Prevents concurrent runner push conflicts. Commits memory/ alongside proposals/. | ✅ SHIPPED | Check workflow step |
| `convergent: bool` field | `packages/swarm/inbox_protocol.py` | Marks proposals where 2+ agents independently proposed same idea (highest quality signal). | ✅ SHIPPED | Check proposals.json for convergent=true |
| Jaccard word overlap detection | `packages/swarm/autonomous_run.py` | Post-hoc convergence detection (threshold=0.35). Replaces broken severity-based voting. Convergent → Telegram with 🎯. | ✅ SHIPPED | Run swarm, check Telegram |
| `full_prompt`/`full_response` in log_experience | `packages/swarm/agent_memory.py` | Stores failure traces. get_context_for_agent() shows "You wrote X. Correct was Y." for WRONG entries (Reflexion, arXiv:2303.11366). | ✅ SHIPPED | Check agent_logs/*.json |
| `log_trajectory()` method | `packages/swarm/agent_memory.py` | Appends raw task traces to agent-trajectories.jsonl (EvoSkill pattern). | ✅ SHIPPED | Run engine.decide(), check agent-trajectories.jsonl |
| trajectory logging in engine | `packages/swarm/engine.py` | Calls log_trajectory() for failures + winners. Passes full_prompt+response to log_experience(). | ✅ SHIPPED | Run SwarmEngine decision |
| `_load_failed_trajectories()` | `packages/swarm/skill_evolution.py` | Reads agent-trajectories.jsonl and injects into LLM skill review prompt. EvoSkill gap closed. | ✅ SHIPPED | Run skill_evolution.py |
| VOYAGER verification gate | `packages/swarm/skill_evolution.py` | HIGH-priority proposed skills: drafted by LLM → static checks → LLM verification → saved as .candidate.md. CTO renames to activate. | ✅ SHIPPED | Run skill_evolution.py with GROQ_API_KEY |
| `adas_agent_designer.py` | `packages/swarm/adas_agent_designer.py` | Reads failure archive → Gemini designs 1 new agent role → writes .agent-proposal.md for CTO review + Telegram notification. | ✅ SHIPPED | python -m packages.swarm.adas_agent_designer |
| `swarm-adas.yml` | `.github/workflows/swarm-adas.yml` | Weekly GitHub Action (Sunday 06:00 UTC) that runs ADAS meta-agent designer. | ✅ SHIPPED | GitHub Actions → ADAS Weekly Agent Designer |
| `AgentStatus.QUARANTINE` | `packages/swarm/agent_hive.py` | SentinelNet immune system: weight 0.3x, credibility_score decay/recovery, auto-rehabilitation. Triggered by chronic underperformance (15+ decisions, <25% accuracy) OR streak (5 consecutive wrong). | ✅ SHIPPED | Run decisions with consistently wrong agent |
| `is_quarantined()` / `get_quarantine_summary()` | `packages/swarm/agent_hive.py` | Public methods for checking quarantine status + report. | ✅ SHIPPED | hive.get_quarantine_summary() |
| QUARANTINE check in dead-weight filter | `packages/swarm/engine.py` | Quarantined agents excluded from dispatch pool before exam/JSON checks. | ✅ SHIPPED | Check _filter_dead_weight() |
| Cross-model judge `_judge_proposal()` | `packages/swarm/autonomous_run.py` | Gemini 2.0 Flash judges Groq-generated proposals on 5 criteria (specificity, evidence, actionability, novelty, impact). Binary pass/fail, asymmetric to avoid 25% self-favor bias. Score 0-5 stored per proposal. | ✅ SHIPPED | Run autonomous_run.py, check proposals.json judge_score |
| `judge_score`/`judge_criteria` fields | `packages/swarm/inbox_protocol.py` | Proposal model gains judge_score (0-5), judge_model, judge_reasoning, judge_criteria dict. Telegram shows [Quality: N/5]. | ✅ SHIPPED | Check proposals.json after daily run |

## Session 63 (2026-03-29) — SPRINTS A9-A10: SWARM UPGRADE + PRE-LAUNCH RESILIENCE

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| `REACT-HOOKS-PATTERNS.md` | `docs/engineering/skills/` | 5 rules for React hooks safety: no hooks in callbacks, isMounted, fresh token, one-shot buttons, envelope unwrap. Prevents Class 1 bug. | ✅ CREATED | Load when writing use*.ts files |
| agent-roster.md routing rows | `memory/swarm/agent-roster.md` | New routing: GDPR deletion → Security, bulk upload → Security, mobile → Product+accessibility, custom hooks → REACT-HOOKS-PATTERNS, useMutation → Architecture | ✅ UPDATED | Read When to Call table |
| Firuza/Nigar accuracy tracking | `memory/swarm/agent-roster.md` | A1-A8: Firuza 4/4 (execution), Nigar 2/2 (B2B). Both confirmed in council. | ✅ UPDATED | Read Agent Improvement Tracking |
| CLAUDE.md Skills Matrix | `CLAUDE.md` | Added React hooks skill rows: writing use*.ts + any useMutation/useQuery hook | ✅ UPDATED | Read Skills Matrix |
| `not-found.tsx` | `apps/web/src/app/[locale]/not-found.tsx` | Branded 404 page: 404 code + message + "Go to Dashboard" button. Locale-aware routing. | ✅ LIVE | Navigate to non-existent route |
| `loading.tsx` | `apps/web/src/app/[locale]/(dashboard)/loading.tsx` | Spinner shown during dashboard route transitions (Next.js streaming). | ✅ LIVE | Navigate between dashboard pages on slow connection |
| `global-error.tsx` | `apps/web/src/app/global-error.tsx` | Root-level error boundary: catches crashes from root layout. Full HTML/body, no Tailwind (safe). | ✅ LIVE | Throw in root layout to test |

## Session 63 (2026-03-29) — SPRINTS A2-A8: NOTIFICATIONS → CSV INVITE

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| `GET /api/notifications/unread-count` | `apps/api/app/routers/notifications.py` | Returns `{unread_count}`. RLS-compliant via SupabaseUser. | ✅ LIVE | GET with user JWT |
| `GET /api/notifications` | `apps/api/app/routers/notifications.py` | Full notification list with total. Optional unread filter. | ✅ LIVE | GET with user JWT |
| `PATCH /api/notifications/read-all` | `apps/api/app/routers/notifications.py` | Mark all unread → read. Returns updated count. | ✅ LIVE | PATCH with user JWT |
| `PATCH /api/notifications/{id}/read` | `apps/api/app/routers/notifications.py` | Mark single notification read. | ✅ LIVE | PATCH with user JWT |
| `useUnreadCount/useNotifications/useMarkAllRead` | `apps/web/src/hooks/queries/use-notifications.ts` | TanStack Query hooks for all notification endpoints. | ✅ LIVE | Used by sidebar + notifications page |
| Sidebar notification badge | `apps/web/src/components/layout/sidebar.tsx` | Red dot on hamburger + number badge on notifications nav item. Polls every 2min. | ✅ LIVE | Visit sidebar with unread notifications |
| Notifications page (real) | `apps/web/src/app/[locale]/(dashboard)/notifications/page.tsx` | Real data replaces mock. Category filter (All/AURA/Events/Org). Mark read on click. | ✅ LIVE | Visit /notifications |
| `GET /{event_id}/attendees` | `apps/api/app/routers/events.py` | Org-owner-only enriched view: registrations + profiles + aura_scores join. Returns `EventAttendeeRow[]`. | ✅ LIVE | GET with org-owner JWT |
| `coordinator_rate_volunteer` → AURA | `apps/api/app/routers/events.py` | After saving star rating: recalculates avg across all ratings, normalizes (avg-1)/4×100, calls upsert_aura_score RPC. Non-blocking. | ✅ LIVE | Rate a checked-in volunteer |
| `useEventAttendees/useRateVolunteer` | `apps/web/src/hooks/queries/use-events.ts` | TanStack hooks for attendees view + coordinator rating mutation. | ✅ LIVE | Used by attendees page |
| `/events/[eventId]/attendees` | `apps/web/src/app/[locale]/(dashboard)/events/[eventId]/attendees/page.tsx` | Attendees list: check-in status, badge chip, AURA score, 1-5 star rating (one-shot disable). 403 if not org owner. | ✅ LIVE | Click Attendees on org event card |
| "Attendees" button on org events | `apps/web/src/app/[locale]/(dashboard)/my-organization/page.tsx` | UserCheck button per event card → /events/{id}/attendees | ✅ LIVE | Visit /my-organization as org user |
| `types.gen.ts` manual patch | `apps/web/src/lib/api/generated/types.gen.ts` | Added account_type, visible_to_orgs, org_type to ProfileResponse + ProfileUpdate. Remove when pnpm generate:api runs live. | ✅ PATCHED | Import ProfileResponse |
| Mobile z-index fix | `apps/web/src/components/layout/sidebar.tsx` + `top-bar.tsx` | Hamburger z-[60] (was z-40, hidden under TopBar z-50). TopBar pl-14 md:pl-6. overflow-x:hidden on body. | ✅ LIVE | Test at 375px width |
| `DELETE /api/auth/me` | `apps/api/app/routers/auth.py` | GDPR account deletion: admin.delete_user → cascades all DB data. RATE_AUTH limited. | ✅ LIVE | DELETE with user JWT |
| Delete account UI | `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx` | Danger Zone: 2-step modal, must type "DELETE", calls API then signOut. | ✅ LIVE | Visit /settings → Delete Account |
| `/my-organization/invite` | `apps/web/src/app/[locale]/(dashboard)/my-organization/invite/page.tsx` | CSV bulk invite: drag-drop zone, file picker, FormData POST to /api/organizations/{org_id}/invites/bulk. Results: created/skipped/errors grid + per-row audit log. | ✅ LIVE | Visit /my-organization → Invite |
| "Invite" button on org dashboard | `apps/web/src/app/[locale]/(dashboard)/my-organization/page.tsx` | Upload icon button in events header → /my-organization/invite | ✅ LIVE | Visit /my-organization as org user |
| Firuza accuracy update | `memory/swarm/skills/firuza-assistant.md` | A1-A5 accuracy: 4/4 correct (100%). Wins execution micro-decisions vs Nigar (2/2, B2B domain). | ✅ UPDATED | Read file |

## Session 62 (2026-03-29) — SPRINT A1: PER-QUESTION BREAKDOWN

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| `useQuestionBreakdown(sessionId)` | `apps/web/src/hooks/queries/use-assessment.ts` | TanStack Query hook: GET /api/assessment/results/{sessionId}/questions. Returns QuestionBreakdown (session_id, competency_slug, questions[]). Auth via useAuthToken. 404/422 → no redirect (page handles it). | ✅ LIVE | Import from use-assessment |
| `/assessment/[sessionId]/questions` | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/questions/page.tsx` | Per-question breakdown: grouped correct/incorrect sections, difficulty badge (Easy/Med/Hard/Expert), response time (seconds), locale-aware question text (AZ preferred). 404/422 → redirects to complete page. | ✅ LIVE | Complete an assessment → click breakdown button |
| "See Question Breakdown" button | `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | ListChecks icon button between CoachingTips and share nudge → navigates to /questions sub-page | ✅ LIVE | Complete any assessment |
| Firuza council persona | `memory/swarm/skills/firuza-assistant.md` | New DSP council member: precision-first analyst, accuracy tracked from Sprint A1 | ✅ CREATED | Read file |
| i18n keys (EN+AZ) | `apps/web/src/locales/*/common.json` | seeBreakdown, questionBreakdown, correct, incorrect, responseTime, difficulty_expert, backToResults, sessionNotFound, questionsCorrect | ✅ LIVE | Both locales updated |

## Session 61 (2026-03-28) — SPRINT 5: SEMANTIC VOLUNTEER SEARCH

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| Search endpoint hardened | `apps/api/app/routers/organizations.py` POST /search/volunteers | Dual org check (account_type + org ownership), RATE_DISCOVERY, asyncio.wait_for timeout, fallback pagination fix, missing-profile skip | ✅ LIVE | POST with org JWT |
| `useVolunteerSearch()` | `apps/web/src/hooks/queries/use-organizations.ts` | Mutation hook: POST /api/organizations/search/volunteers, typed payload + result | ✅ LIVE | Used by /discover search mode |
| `/discover` upgraded | `apps/web/src/app/[locale]/(dashboard)/discover/page.tsx` | Browse|Smart Search mode toggle. Smart Search: query input, AURA quick filters (Any/Bronze+/Silver+/Gold+), badge tier pills, similarity labels (High/Good/Partial), clear → browse | ✅ LIVE | Visit /az/discover as org user |
| Sidebar: /discover link | `apps/web/src/components/layout/sidebar.tsx` | Added 🔍 Discover nav link | ✅ LIVE | Open sidebar |

## Session 60 (2026-03-28) — SPRINT 4: BACKEND WIRING + B2B PATH

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| Migration: `profiles_org_fields` | `supabase/migrations/20260328240000_...` | Adds account_type (volunteer/organization), visible_to_orgs, org_type to profiles. Index on visible_to_orgs=TRUE. | ✅ APPLIED | `SELECT account_type, visible_to_orgs FROM profiles LIMIT 1` |
| Migration: `create_notifications` | `supabase/migrations/20260328240001_...` | notifications table: 7 types, user_id FK, is_read, RLS (user reads own, service inserts) | ✅ APPLIED | `SELECT * FROM notifications LIMIT 1` |
| Migration: `create_intro_requests` | `supabase/migrations/20260328240002_...` | intro_requests table: org→volunteer, timeline enum, status, unique pending index, 4 RLS policies | ✅ APPLIED | `SELECT * FROM intro_requests LIMIT 1` |
| Events pages: real API | `apps/web/src/app/[locale]/(public)/events/` | events/page.tsx + events/[id]/page.tsx use real `useEvents`/`useEvent` hooks. `event-card.tsx` and `events-list.tsx` use `EventResponse` (snake_case fields). `getMockEvents()` removed. | ✅ LIVE | Visit /events in browser |
| `DiscoverableVolunteer` schema | `apps/api/app/schemas/profile.py` | New Pydantic model for the public volunteer browse response | ✅ LIVE | `GET /api/profiles/public` |
| `GET /api/profiles/public` | `apps/api/app/routers/profiles.py` | Org-only endpoint: lists visible_to_orgs=TRUE volunteers with AURA join, ordered by score | ✅ LIVE | Need org JWT to call |
| `/discover` dashboard page | `apps/web/src/app/[locale]/(dashboard)/discover/page.tsx` | Org-only volunteer browse: search by name/location, badge tier badge, AURA score, click→/u/username | ✅ LIVE | Visit /az/discover as org user |
| `useDiscoverableVolunteers()` | `apps/web/src/hooks/queries/use-profile.ts` | React Query hook for GET /api/profiles/public | ✅ LIVE | Used by /discover page |
| `IntroRequestCreate/Response` schemas | `apps/api/app/schemas/organization.py` | Pydantic models: volunteer_id (UUID validated), timeline enum, project_name, message (max 500) | ✅ LIVE | Part of POST endpoint |
| `POST /api/organizations/intro-requests` | `apps/api/app/routers/organizations.py` | Dual org-role check + volunteer visibility guard + 5/hour rate limit + fire-and-forget notification | ✅ LIVE | POST with org JWT |
| `useCreateIntroRequest()` | `apps/web/src/hooks/queries/use-organizations.ts` | Mutation hook: JSON.stringify body, 409 dedup handling, ApiError typed | ✅ LIVE | Used by IntroRequestButton |
| `IntroRequestButton` | `apps/web/src/components/profile/intro-request-button.tsx` | Client component: org-only gate via useMyOrganization(), modal (3 fields), success/error toast | ✅ LIVE | Visit /u/[username] as org user |

## Session 51 (2026-03-27) — ARCHITECTURE SPRINT

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| `memory_consolidation.py` | `packages/swarm/` | Hippocampus→neocortex: reads agent-feedback-log.md, distills to agent-feedback-distilled.md, archives old entries. Runs daily in GitHub Actions at 09:00 Baku. | ✅ LIVE | `python3 -m packages.swarm.memory_consolidation` |
| `skill_evolution.py` | `packages/swarm/` | Scans `memory/swarm/skills/*.md`, checks quality (triggers, outputs, cross-refs), generates improvements via LLM, appends to skill-evolution-log.md. Runs daily AFTER memory_consolidation. | ✅ LIVE | `python3 -m packages.swarm.skill_evolution` |
| `skills.py` router | `apps/api/app/routers/` | `POST /api/skills/{name}` — executes any skill by name, passes user context, returns LLM output. `GET /api/skills/` — list available skills. | ✅ LIVE | `curl -X POST .../api/skills/aura-coach` |
| Telegram bidirectional | `apps/api/app/routers/telegram.py` | CEO can RESPOND to proposals via Telegram bot. Responses written to `memory/swarm/ceo-inbox.md`. Commands: /proposals, /ask {agent}, act {id}, dismiss {id}, defer {id} | ✅ LIVE | Send `/proposals` to @volaurabot |
| `swarm-freedom-architecture.md` | `memory/swarm/` | Documents temp 1.0 mandate, freedom protocol, convergent signal rules, roadmap to full autonomy | ✅ DOC | Read-only reference |
| NotebookLM notebook | External | Competitive landscape research. Sources: 12 competitor analyses. v0Laura moat: 6 elements. | ✅ LIVE | notebook ID: a76be380 |

## Session 51 — Product Skills (6 new files in `memory/swarm/skills/`)

| Skill | Replaces | What it does |
|-------|---------|-------------|
| `content-formatter.md` | BrandedBy standalone | Multi-format content generation (POST_CLEAN + TELEGRAM + EMAIL + CTA) |
| `aura-coach.md` | MindShift standalone | Personalized coaching based on AURA score gaps |
| `assessment-generator.md` | ZEUS standalone | Generates assessment questions, scenarios, keywords for any competency |
| `behavior-pattern-analyzer.md` | MindShift behavioral engine | Identifies user behavior patterns, predicts needs |
| `ai-twin-responder.md` | BrandedBy AI Twin | AI Twin responses in user's voice, uses MindShift memory |
| `feed-curator.md` | Life Simulator feed | Personalized content feed based on AURA + behavior patterns |

## Session 53 (2026-03-28) — OWASP + UX SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `deduct_crystals_atomic()` | `supabase/migrations/20260328000040_atomic_crystal_deduction.sql` | Atomic crystal deduction with pg_advisory_lock. Prevents TOCTOU double-spend. | ✅ APPLIED TO PROD |
| `bottom-nav.tsx` | `apps/web/src/components/layout/` | Mobile bottom navigation, 5 tabs, 72px, ADHD-first always-visible labels | ✅ LIVE |
| `assessment-store.ts` (persist) | `apps/web/src/stores/` | Zustand persist middleware (sessionStorage). Survives page refresh. | ✅ LIVE |
| `POST /api/auth/logout` | `apps/api/app/routers/auth.py` | Logout endpoint with audit logging | ✅ LIVE |
| OWASP fixes (15 of 22) | various | Rate limits, audit logs, error sanitization, webhook auth, deleted /health/env-debug | ✅ LIVE |

## Session 54 (2026-03-28) — USER SIMULATION SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `GET /api/leaderboard/me` | `apps/api/app/routers/leaderboard.py` | Returns current user's rank (users_with_higher_score + 1) | ✅ LIVE |
| `useMyLeaderboardRank` hook | `apps/web/src/hooks/queries/use-leaderboard.ts` | TanStack Query hook for leaderboard rank | ✅ LIVE |
| Share buttons (copy fallback) | `apps/web/src/components/aura/share-buttons.tsx` | execCommand fallback for HTTP clipboard, async TikTok flow | ✅ LIVE |

## Session 55 (2026-03-28) — HOUSEKEEPING SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `START-SESSION-VOLAURA.md` | root | Brain activation file. Mandatory first read every session. | ✅ LIVE |
| `volaura-security-review/skill.md` | `docs/openspace-skills/` | OpenSpace-format 10-point OWASP checklist for FastAPI endpoints | ✅ LIVE |
| OpenSpace MCP | `C:/tools/openspace-venv` | MCP server for reusable skill patterns. Tools: execute_task, search_skills, upload_skill, fix_skill | ✅ LIVE |
| `feedback_swarm_patterns.md` | `memory/swarm/` | Temp 1.0 rules, convergent signal patterns, swarm anti-patterns | ✅ DOC |
| `SHIPPED.md` | `memory/swarm/` | THIS FILE — log of what exists in production | ✅ DOC |

## Session 56 (2026-03-28) — AURA COACH + DASHBOARD FIX

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `aura-coach` wired to `/aura` | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | `useSkill("aura-coach")` fires after reveal animation. Shows STRENGTH_MAP + GROWTH_PATH + PEER_CONTEXT. Skeleton during load → AuraCoach component. | ✅ LIVE |
| AURA 404 fix | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | API returns 404 when no score → frontend now shows "Start Assessment" instead of crashing | ✅ LIVE |

## Session 57 (2026-03-28) — TEAM EXPANSION + SPRINT PLAN V3

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `sales-deal-strategist.md` | `memory/swarm/skills/` | B2B deal strategy, pricing, org onboarding | ✅ SKILL |
| `sales-discovery-coach.md` | `memory/swarm/skills/` | Discovery questions, intro requests, B2B flow | ✅ SKILL |
| `linkedin-content-creator.md` | `memory/swarm/skills/` | AURA-to-LinkedIn portability, professional brand | ✅ SKILL |
| `cultural-intelligence-strategist.md` | `memory/swarm/skills/` | CIS/AZ cultural framing, trust signals, naming | ✅ SKILL |
| `behavioral-nudge-engine.md` | `memory/swarm/skills/` | ADHD-first design, cognitive load, engagement | ✅ SKILL |
| `accessibility-auditor.md` | `memory/swarm/skills/` | WCAG, AZ chars (ə ğ ş ç), mobile a11y — activates Sprint 6 | ✅ SKILL |
| `RECURSIVE-CRITICISM.md` | `docs/engineering/skills/` | Standard: 2-round critique on all plans before execution | ✅ DOC |
| `SPRINT-PLAN-V3.md` | `docs/` | Final plan: 8 sprints, 25 days, swarm-validated (38/50) | ✅ DOC |
| Railway deploy fix | root `railway.toml` + `Dockerfile.railway` | Fixes Railway building Node instead of Python — root-level config now forces Docker | ✅ LIVE |

## Session 59 (2026-03-28) — SPRINT 3: API CONTRACTS + ASSESSMENT REFACTOR

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Assessment router split | `services/assessment/` (3 modules) | `rewards.py` (crystal+skill events), `helpers.py` (DB lookups), `coaching_service.py` (Gemini+fallbacks). Router 919→660 lines. | ✅ LIVE |
| `CoachingTip`, `CoachingResponse`, `AssessmentInfoOut` | `schemas/assessment.py` | Moved from router, added to schemas | ✅ LIVE |
| `QuestionResultOut`, `QuestionBreakdownOut` | `schemas/assessment.py` | Per-question result with mapped difficulty labels (no IRT leak) | ✅ LIVE |
| `GET /assessment/info/{slug}` | `routers/assessment.py` | Pre-assessment info: time estimate, can_retake, days_until_retake | ✅ LIVE |
| `GET /assessment/results/{id}/questions` | `routers/assessment.py` | Per-question breakdown: difficulty_label, is_correct, response_time_ms. IRT params mapped to easy/medium/hard/expert. | ✅ LIVE |
| Competency info migration | `supabase/migrations/20260328230000` | `time_estimate_minutes`, `can_retake` columns added to competencies | ✅ APPLIED |
| Events rate limit fix | `routers/events.py` | Added @limiter.limit to GET /{id} and GET /{id}/registrations | ✅ LIVE |
| B2B search API docs | `docs/api/volunteer-search-api.md` | Full request/response spec for org volunteer search | ✅ DOC |
| API E2E tests (3) | `tests/test_assessment_api_e2e.py` | Happy path, retest cooldown, question breakdown security | ✅ TEST |
| RLS write vectors (6) | `tests/test_rls_audit.py` | UPDATE/DELETE/INSERT isolation, questions_safe enforcement, naked TRUE check | ✅ TEST |
| Protocol enforcement hook | `.claude/hooks/protocol-enforce.sh` | Blocks Edit/Write on apps/ until protocol step >= 6 | ✅ LIVE |
| TASK-PROTOCOL v2.0 | `docs/TASK-PROTOCOL.md` + `CHECKLIST.md` | v2.0: context check, blockers, exit condition, doc gate, pre-commit review | ✅ DOC |

## Session 58 (2026-03-28) — SPRINT 1+2 SECURITY HARDENING

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| Signup redesign | `apps/web/src/app/[locale]/(auth)/signup/page.tsx` | Role selector (volunteer/org), org_type dropdown, AZ privacy consent, display_name removed | ✅ LIVE |
| Onboarding rewrite | `apps/web/src/app/[locale]/(dashboard)/onboarding/page.tsx` | username pre-fill from user_metadata, org 2-step flow, visible_to_orgs toggle (default OFF), org_type forwarded to API | ✅ LIVE |
| `account_type`, `visible_to_orgs`, `org_type` fields | `apps/api/app/schemas/profile.py` + `supabase/migrations/` | New profile fields with validators. Migration applied to prod. | ✅ LIVE |
| `ProxyHeadersMiddleware` | `apps/api/app/main.py` | Railway proxy: real client IP now reaches rate limiter (was always proxy IP) | ✅ LIVE |
| Professional empty states | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | NoScoreBanner: volunteer → "Companies searching for you", org → "Verified talent waiting" | ✅ LIVE |
| Assessment retest cooldown | `apps/api/app/routers/assessment.py` | 7-day block per competency after completion | ✅ LIVE |
| Abuse monitoring | `apps/api/app/routers/assessment.py` | >10 starts/day → logger.warning (no block) | ✅ LIVE |
| Rate limits (11 endpoints) | `activity.py`, `auth.py`, `profiles.py`, `organizations.py`, `invites.py`, `events.py` | @limiter.limit added to 11 endpoints previously unprotected | ✅ LIVE |
| UUID validation | `events.py` (8 handlers), `assessment.py` GET /results | `_validate_uuid()` helper + call on all event_id and session_id path params | ✅ LIVE |
| Crystal ledger fix | `apps/api/app/routers/brandedby.py` | `"delta"` → `"amount"`, removed non-existent columns `reason`/`source_event_type` | ✅ LIVE |
| Seed events (10 events) | Supabase migration | 10 events with relative dates (NOW() + INTERVAL), status=open | ✅ APPLIED |
| `TASK-PROTOCOL.md` | `docs/` | 10-step swarm critique loop: skills → plan → critique → response → counter-critique → execute → report → swarm review. Hard gates. | ✅ DOC |

---

## DAILY EXECUTION CYCLE (what runs automatically)

```
09:00 Baku → .github/workflows/swarm-daily.yml
  ├── 1. autonomous_run.py (5 agents, temp 1.0)
  │       → proposals.json updated
  │       → HIGH/CRITICAL → Telegram to CEO
  ├── 2. memory_consolidation.py
  │       → agent-feedback-log.md → agent-feedback-distilled.md
  │       → episodic_inbox/ archives old entries
  └── 3. skill_evolution.py
          → scans memory/swarm/skills/*.md
          → suggests improvements → skill-evolution-log.md
```

## Session 56 (2026-03-28) — SKILL WIRING SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `aura-coach` wired to `/aura` page | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | `useSkill("aura-coach")` fires after reveal animation. Shows loading skeleton → AuraCoach component renders STRENGTH_MAP + GROWTH_PATH + PEER_CONTEXT text. | ✅ LIVE |
| `feed-curator` wired to `/dashboard` | already existed from Session 54 | `useSkill("feed-curator")` + `FeedCards` component — confirmed wired and complete. | ✅ CONFIRMED |
| `leaguePosition` type fix | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | `myRank?.rank` (number) now formatted as `#${rank}` string. TS error resolved. | ✅ LIVE |
| `RevealCurtain` missing `t()` fix | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Pre-existing bug: `t()` called without `useTranslation()`. Added hook call. | ✅ LIVE |
| AURA 404→empty state fix | `apps/web/src/hooks/queries/use-aura.ts` | API returns 404 when no score exists. Previously threw error ("Something went wrong"). Now returns null → page shows empty state with "Start Assessment" CTA. | ✅ LIVE |
| Sprint Plan v2 (3-round swarm review) | `docs/SPRINT-PLAN-V2.md` | 8 sprints, 25 days. Architecture Agent → Product + Security critics → synthesis. 78 features audited, 39 security findings. | ✅ DOC |

## Session 57 (2026-03-28) — TEAM EXPANSION SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `sales-deal-strategist.md` | `memory/swarm/skills/` | B2B deal architecture, MEDDPICC for Volaura, org pricing tiers, red flags | ✅ LIVE |
| `sales-discovery-coach.md` | `memory/swarm/skills/` | B2B discovery flows, org onboarding questions, Gap Selling for Volaura | ✅ LIVE |
| `linkedin-content-creator.md` | `memory/swarm/skills/` | AURA score portability, LinkedIn share templates for Kamal/Rauf personas | ✅ LIVE |
| `cultural-intelligence-strategist.md` | `memory/swarm/skills/` | AZ/CIS cultural audit, invisible exclusion patterns, AZ text/naming rules | ✅ LIVE |
| `accessibility-auditor.md` | `memory/swarm/skills/` | WCAG 2.2 AA, radar chart fix, Volaura component risk map, AZ a11y | ✅ LIVE (activates Sprint 6) |
| `behavioral-nudge-engine.md` | `memory/swarm/skills/` | ADHD-first validation, cognitive load budgeting, notification cadence | ✅ LIVE (DSP skill) |
| 3 new DSP personas | `CLAUDE.md` | Kamal (senior professional), Aynur (talent acquisition), Rauf (mid-career) added to council | ✅ LIVE |
| Sprint Plan V2 updated | `docs/SPRINT-PLAN-V2.md` | Sprint 1 +3 tasks: org/volunteer branch, post-confirm display_name, professional empty state | ✅ LIVE |
| Skills Matrix updated | `CLAUDE.md` | 9 new routing rows for B2B, cultural, accessibility, nudge, LinkedIn skills | ✅ LIVE |

**How new agents were hired:** Full repo (164 agent files) given to Kamal + Aynur + Rauf personas. Their nominations + existing 6-agent votes synthesized. Reality Checker rejected (duplicates Attacker). 6 agents hired.

| `SPRINT-PLAN-V3.md` | `docs/` | Sprint Plan after 2-round recursive criticism (9 personas, 18→38/50). Swaps Sprint 3↔4, IP rate limits, CSRF, org RLS, volunteer opt-in, Telegram sanitization moved to Sprint 2. | ✅ DOC |
| `RECURSIVE-CRITICISM.md` | `docs/engineering/skills/` | Standard protocol for recursive plan criticism. 2 rounds minimum for sprint plans. | ✅ DOC |

---

## HOW TO UPDATE THIS FILE

After any session that adds/changes code:
```
| {file/feature} | {location} | {what it does} | ✅ LIVE | {how to test} |
```
Add to the correct session section. Never delete old entries — archive to SHIPPED-ARCHIVE.md when file exceeds 200 lines.

---

## Session 66 — 2026-03-29

| What | Where | Does what | Status |
|------|-------|-----------|--------|
| `TASK-PROTOCOL.md` v3.0 | `docs/` | +10 protocol steps from 5 swarm agents: Steps 0.1 (Mistakes Audit), 0.25 (Team Selection), 1.5 (Decision Type Gate), 3.5 (Ecosystem Blast Radius), 3.7 (User Journey Walkthrough), 6.5 (Security Pre-Commit Checklist), 9.5 (Work Verdict Gate), 10.5 (CEO Silence Timeout). OPT-OUT not OPT-IN principle. | ✅ DOC |
| `TASK-PROTOCOL-CHECKLIST.md` v3.0 | `docs/` | Synced with protocol v3.0. All 10 new steps have fill-in templates. | ✅ DOC |
| `use-assessment.ts` fixes | `apps/web/src/hooks/queries/` | Fix CLASS 4: difficulty_label type lowercase (was Title Case — API always lowercase). Add competency_score to QuestionBreakdown. Add AssessmentInfo interface + useAssessmentInfo hook (staleTime 10min). | ✅ LIVE |
| `assessment/[sessionId]/questions/page.tsx` fixes | `apps/web/src/app/[locale]/(dashboard)/` | Fix DIFFICULTY_COLORS to lowercase keys. DifficultyBadge normalizes defensively. competencyLabel uses t() with fallback. | ✅ LIVE |
| i18n keys EN + AZ | `apps/web/src/locales/*/common.json` | Move difficulty_expert adjacent to sibling keys (was orphaned). Add 6 info page keys: infoAbout, infoTimeLabel, infoRetakeAvailable, infoRetakeCooldown ({{days}}), infoNoDescription, infoContinueButton. | ✅ LIVE |
| `assessment/info/[slug]/page.tsx` | `apps/web/src/app/[locale]/(dashboard)/assessment/info/[slug]/` | NEW: Pre-assessment info page. Fetches GET /api/assessment/info/{slug}. Shows competency label (t()), description (null-safe), time estimate, retake status. Auth redirect with returnTo. 404/429/5xx error states. isMounted on all router.replace. retakeBlocked checks both can_retake and days_until_retake. | ✅ LIVE |
| "About" link in assessment callout | `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx` | Added inside preselectedComp && block — links to /assessment/info/{slug}. | ✅ LIVE |
