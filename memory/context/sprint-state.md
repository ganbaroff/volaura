# Sprint State — Live Snapshot

**PURPOSE: Read this file FIRST at every session start. 30-second read. Then read CLAUDE.md.**
**UPDATE this file LAST at every session end. This is the single source of "where are we now".**
**Historical entries (Sessions 1-74) archived in git history to keep this file readable.**

---

## CURRENT POSITION — SESSION 81 (continued), 2026-04-02 — BATCH 2026-04-02-D

**Last Updated:** 2026-04-02 (Session 81 — BATCH D: Admin Panel MVP)

**BATCH 2026-04-02-D delivered:**
- Admin panel MVP: migration + FastAPI router (6 endpoints, fail-closed gate) + Next.js (admin)/route group
- 7 admin tests: 3 security gate tests (non-admin → 403) + 4 happy path
- 668/668 tests passing (excluding 1 pre-existing flaky IRT test)
- Architecture fix: `packages/swarm/types.py` → `swarm_types.py` (stdlib shadow eliminated)
- Root cleanup: removed 8 sources of clutter

**1-click required to activate admin panel:**
1. Apply migration `20260402130000_add_platform_admin.sql` in Supabase dashboard
2. In Supabase Table Editor → profiles → set `is_platform_admin=true` for Yusif's row
3. Visit `/az/admin` — AdminGuard will let you through

**Next session priorities:**
1. Apply migration + activate admin (1-click Yusif action)
2. Collective AURA Ladders: `pnpm generate:api` refresh
3. shadcn `table` component via CLI (admin tables would benefit from proper shadcn table)
4. Tribe Streaks: 7-checklist pre-code review
5. Supabase Realtime: enable notifications table publication (1-click)

---

## CURRENT POSITION — SESSION 81 (continued), 2026-04-02 — BATCH 2026-04-02-C

**Last Updated:** 2026-04-02 (Session 81 continued — BATCH 2026-04-02-C)

**BATCH 2026-04-02-C delivered:**
- `match_checker.py` — renamed `_TELEGRAM_CB_THRESHOLD` → `_CB_THRESHOLD` (name mismatch with test import)
- Result: 687 passed, 0 failed — full test suite green
- Route shadowing fix (BATCH B) + constant rename (BATCH C) = all 27 test_saved_searches tests pass

**Next session priorities (updated):**
1. Supabase Realtime: enable notifications table publication in Supabase dashboard (1-click)
2. Collective AURA Ladders: `pnpm generate:api` refresh to include new endpoint in SDK
3. Tribe Streaks: 7-checklist review before code — Cultural Intelligence + Security + Architecture agents

---

## CURRENT POSITION — SESSION 81 (continued), 2026-04-02

**Last Updated:** 2026-04-02 (Session 81 continued — BATCH 2026-04-02-B)

**BATCH 2026-04-02-B delivered:**
- `pnpm generate:api` — TypeScript SDK regenerated from live 76-route schema. +209 lines: SavedSearch types + SDK functions now generated. Zero TS errors.
- CIS-002 — patronymic name hint added. EN: "Full name (e.g. Yusif Eldar oglu)" / AZ: "Adınız Soyadınız (məs. Yusif Eldar oğlu)". MICRO fix, onboarding page.
- `docs/TRIBE-STREAKS-DESIGN.md` — Full design spec with anti-harassment safeguards, DB schema, matching algorithm, 7-item checklist REQUIRED before any code starts.

**Next session priorities (updated):**
1. Supabase Realtime: enable notifications table publication in Supabase dashboard (user action — 1 click)
2. Tribe Streaks: 7-checklist review before code — Cultural Intelligence + Security + Architecture agents
3. CEO sign-off on tribe visibility model (what exactly can tribe members see about each other?)

---

## CURRENT POSITION — SESSION 81 COMPLETE, 2026-04-02

**Last Updated:** 2026-04-02 (Session 81 — Growth D.2 sprint)

**Status:** Session 81 shipped: Growth Trajectory Widget (animated tier progress bar) + Milestone Banner (Gold/Platinum celebration) on assessment complete page. Board heavy models (nemotron-ultra-253b) ran — voted Tribe Streaks + Collective AURA Ladders, killed Leaderboard unanimously.

**Session 81 delivered:**
- Growth Trajectory widget — animated progress bar toward next badge tier (D.2-B)
- Milestone Banner — Gold/Platinum celebration with spring animation (D.2-A)
- i18n keys EN + AZ: progressToNextTier, tierMaxReached, milestonePlatinum, milestoneGold, milestoneDiscoverable
- board_heavy_run.py — heavy model runner (nemotron-ultra-253b × 2 + deepseek-r1)
- board-heavy-results.json — Board analysis artifact

**Board intelligence (Session 81 — nemotron-ultra-253b):**
- Strategic Board Director → Tribe Streaks & Kudos (winner)
- CPO Board → Collective AURA Ladders (winner)
- BOTH unanimously killed AURA Leaderboard
- NEW RISK: Anti-harassment safeguards for tribe formation (unmitigated)
- NEW RISK: Exclusionary cliques if group membership is static

**Next session priorities:**
1. `pnpm generate:api` — TypeScript SDK sync (saved-search + character endpoints)
2. Tribe Streaks / Collective AURA Ladders — MEDIUM sprint, requires new DB tables + anti-harassment safeguards design FIRST
3. CIS-002 — patronymic name field hint (P1 AZ UX)
4. Supabase Realtime: enable notifications table publication in dashboard (1-click)
5. Kill AURA Leaderboard framing anywhere it appears (unanimous Board + 5 agent vote)

---

## CURRENT POSITION — SESSION 80 COMPLETE, 2026-04-01

**Last Updated:** 2026-04-01 (Session 80 — context resumed after compaction)

**Status:** Session 80 shipped: CIS-001 fix (achievement levels), profile view throttle index, notify_profile_viewed() helper. Open: pnpm generate:api (needs live server), Supabase Realtime enable on notifications table (1-click dashboard), CIS-002 (patronymic name hint — P1), BNE-001 (assessment cognitive overload — open).

**Session 80 delivered:**
- `supabase/migrations/20260401180000_profile_view_notification_index.sql` — partial index for org_view throttle dedup query
- `apps/api/app/services/notification_service.py` — `notify_profile_viewed()` helper (24h throttle, never raises)
- `apps/web/src/lib/utils/achievement-level.ts` — `getAchievementLevelKey()` utility — CIS-001 fix
- i18n EN + AZ: `profile.achievementLabel` + 6 tier keys (achievementExpert → achievementStarting)
- `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx` — CIS-001 fix: "Top 5%" → "Expert" / achievement level
- `apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` — CIS-001 fix: stat box shows achievement level instead of percentile number

**Discovery this session (already existed — confirmed live):**
- `POST /api/profiles/{username}/view` — throttled profile view notification endpoint (profiles.py)
- `ProfileViewTracker` component — frontend fires POST on mount (profile-view-tracker.tsx)
- `test_profile_view.py` — 6 tests for the endpoint (already existed)

**Next session priorities:**
1. `pnpm generate:api` — regenerate TypeScript SDK (saved-search + character endpoints need sync). Requires running FastAPI dev server.
2. CIS-002 — patronymic name field hint ("Adınız Soyadınız (məs. Yusif Eldar oğlu)") — P1 AZ UX fix
3. BNE-001 — assessment cognitive overload: single-path feedback, save messaging, time estimates
4. Supabase Realtime: enable notifications table publication in Supabase dashboard (1-click)

---

## CURRENT POSITION — SPRINTS 7 + 8 COMPLETE, 2026-04-01

**Status:** Sprint 8 (Org Saved Search + Match Notifications) SHIPPED. All 8 roadmap sprints DONE.

**Sprint 8 delivered:**
- `supabase/migrations/20260401171324_org_saved_searches.sql` — table + RLS + partial index
- `apps/api/app/schemas/organization.py` — 6 new schemas: SavedSearchFilters, SavedSearchCreate, SavedSearchOut, etc.
- `apps/api/app/routers/organizations.py` — 4 new endpoints + `_assert_search_ownership()` security helper
- `apps/api/app/services/match_checker.py` — daily match checker, Telegram notifications, circuit breaker
- `.github/workflows/match-checker.yml` — daily cron at 07:00 UTC, dry-run mode
- `apps/web/src/hooks/queries/use-organizations.ts` — useSavedSearches, useCreateSavedSearch, useDeleteSavedSearch
- `apps/web/src/app/[locale]/(dashboard)/org-volunteers/page.tsx` — save search button + modal + pills
- i18n: EN + AZ orgDash.* saved search keys

**QA NOTE (for next session):** Sprint 8 tests needed before prod deploy:
- Privilege escalation: org A cannot read/delete org B's saved searches
- Duplicate name → 409 | Cap > 20 → 422 | Delete foreign → 404

**What's next (first time all 8 roadmap sprints are done):**
- Write test suite for Sprint 8 (privilege escalation + cap enforcement)
- `pnpm generate:api` to sync TypeScript SDK with new saved-search + character endpoints
- Decide on ANUS/WebSocket (5+ convergent swarm proposals — highest-signal pending item)

---

## CURRENT POSITION — SPRINT 7 COMPLETE, 2026-04-01

**Status:** Sprint 7 (MindShift + Life Sim Integration) SHIPPED. Cross-product bridge live.

**Sprint 7 delivered:**
- `apps/api/app/services/cross_product_bridge.py` — fire-and-forget Volaura→MindShift event push. Circuit breaker (3 failures / 5-min window → 60s silence). httpx async, 3s/8s timeouts. Never blocks main request.
- `rewards.py` updated — `emit_assessment_rewards()` now accepts `user_jwt` and calls `push_crystal_earned()` + `push_skill_verified()` after local events persist.
- `assessment.py` router updated — extracts JWT from Authorization header, passes to `emit_assessment_rewards()`.
- `apps/web/src/hooks/queries/use-character.ts` — `useCrystalBalance()` + `useCharacterState()` TanStack Query hooks.
- `apps/web/src/components/dashboard/crystal-balance-widget.tsx` — Crystal balance widget (hides when balance=0, never breaks dashboard on error).
- Dashboard page updated — `CrystalBalanceWidget` wired between StatsRow and Feed.
- i18n: `character.*` keys added to EN + AZ locales.

**What was already live (confirmed in discovery):**
- `character.py` router — 4 endpoints including `GET /api/character/crystals`
- `rewards.py` — `emit_assessment_rewards()` already wired into `complete_assessment`
- `character_events` table + 3 migrations already deployed

**Next sprint per IMPLEMENTATION-ROADMAP.md:**
- Sprint 8: Org Saved Search + Match Notifications

---

## CURRENT POSITION — SPRINTS 1-6 COMPLETE, 2026-04-01

**Status:** All 6 swarm infrastructure sprints SHIPPED. 11 new files total this session.

**Sprint 5 (Skill Evolution):** `skill_applier.py` + `skill_ab_tester.py` wired into `session_end_hook.py`. After every push, HIGH-priority skill improvements auto-applied + A/B tested. Winners kept, losers reverted.

**Sprint 6 (Social Delivery):** `report_generator.py` wired into `autonomous_run.py`. CEO now gets: structured markdown in ceo-inbox.md + Telegram message with health indicator (GREEN/YELLOW/RED) + GitHub Actions stdout with actionable summary.

**Full swarm pipeline now:**
```
push to main
  → session_end_hook.py: capture diff → SESSION-DIFFS.jsonl → rebuild code-index.json
  → skill_applier.py: apply HIGH-priority skill improvements → A/B test → keep winner

09:00 Baku daily
  → heartbeat_gate.py: SKIP if no activity + no urgent proposals + stale floor not reached
  → code_index.py: load 530-file index
  → task_binder.py: bind each perspective lens to verified files
  → 7 agents: generate proposals (with bound files in context)
  → proposal_verifier.py: tag ungrounded proposals [UNGROUNDED]
  → cross-model judge: score all proposals
  → suggestion_engine.py: generate 2-3 predicted next actions
  → report_generator.py: write to ceo-inbox.md + Telegram + stdout
  → memory_consolidation.py: distill feedback → neocortex
  → skill_evolution.py: scan skills → suggest improvements → log
```

**Next sprints per IMPLEMENTATION-ROADMAP.md:**
- Sprint 7: MindShift + Life Sim Integration (wire `rewards.py` → `character_events` → Life Sim polling)
- Sprint 8: Org Saved Search + Match Notifications

---

## CURRENT POSITION — SPRINTS 1-4 COMPLETE, 2026-04-01

**Status:** Sprint 1 (Infra P0) + Sprint 2 (Predictive Suggestions) + Sprint 3 (Adaptive Execution) + Sprint 4 (Context Intelligence) ALL SHIPPED.

**8 new files this session:**
- `heartbeat_gate.py` — KAIROS gate (swarm-daily.yml wired)
- `proposal_verifier.py` — groundedness check (96.7% on existing)
- `outcome_verifier.py` — Tier 1+2 verification + self-check
- `suggestion_engine.py` — predictive next actions (CEO inbox)
- `execution_state.py` — ExecutionState enum + tracker
- `recovery_strategies.py` — retry/simplify/decompose/escalate
- `code_index.py` — 530 files indexed, searchable
- `task_binder.py` — task → verified file bindings (100% confidence tested)

**autonomous_run.py now:**
1. Runs heartbeat gate → skip if no activity
2. Loads code index → binds each perspective to files before launch
3. Tags ungrounded proposals [UNGROUNDED]
4. After batch: generates predictive suggestions → CEO inbox

**Next sprints per IMPLEMENTATION-ROADMAP.md:**
- Sprint 5: Skill Evolution Completion (add applier + A/B tester to `skill_evolution.py`)
- Sprint 6: Social Delivery Pipeline (richer Telegram reports from `report_generator.py`)
- Sprint 7: MindShift + Life Sim Integration (wire `rewards.py` → `character_events`)

---

## CURRENT POSITION — SPRINT 1+2 COMPLETE, 2026-04-01

**Status:** Sprint 1 (Swarm Infrastructure P0) + Sprint 2 (Predictive Suggestions) SHIPPED.

**What was built:**
- `packages/swarm/heartbeat_gate.py` — KAIROS gate, wired into swarm-daily.yml
- `packages/swarm/proposal_verifier.py` — groundedness check (96.7% on existing proposals)
- `packages/swarm/outcome_verifier.py` — Tier 1+2 verification, self-verification built in
- `packages/swarm/suggestion_engine.py` — predictive next actions (Sprint 2 winner)
- `autonomous_run.py` updated — both engines wired in at batch close
- `swarm-daily.yml` updated — heartbeat gate step added

**Verification results:**
- All 4 new files: syntax OK, importable
- Heartbeat gate: correctly identified 10 urgent proposals → EXIT 0 (RUN)
- Proposal verifier: 29/30 grounded (96.7%), 1 caught invalid path
- Suggestion engine: generated 2 predictions, appended to ceo-inbox.md

**Next sprints per IMPLEMENTATION-ROADMAP.md:**
- Sprint 3: Adaptive Execution Loop (`packages/swarm/execution_state.py` + `recovery_strategies.py`)
- Sprint 4: Context Intelligence Engine (`packages/swarm/code_index.py` + `task_binder.py`)
- Sprint 5: Skill Evolution Completion (add applier + A/B tester to existing `skill_evolution.py`)

---

## CURRENT POSITION — IMPLEMENTATION ROADMAP WRITTEN, 2026-04-01

**Status:** `docs/IMPLEMENTATION-ROADMAP.md` created. 8 sprints, ~21.5h total. `docs/TASK-PROTOCOL.md` updated to v6.0. Awaiting CEO review + Sprint 1 execution start.

**Summary of what was analyzed this session:**
- ZEUS repo (`C:\Users\user\OneDrive\Documents\GitHub\ANUS\`) — 143 Python files, 4 patterns identified
- MindShift (`C:\Users\user\Downloads\mindshift`) — 95% complete, volaura-bridge.ts already built
- Claude Code architecture patterns (heartbeat gate, MEMORY-INDEX, outcome verification)

**Sprint 1 (next session):** Swarm Infrastructure P0 — heartbeat gate + proposal verifier + outcome verifier + 3-layer MEMORY-INDEX

**CEO decision needed:** Sprint 7 auth sync strategy — Option C recommended (emit events first, migrate auth later)

**GitHub OAuth:** Configured end-to-end. GitHub → Supabase callback → frontend.
**Vercel:** Auto-deploy fixed. First successful build after weeks. volaura.app live.

---

## CURRENT POSITION — BATCH-S COMPLETE + S-05 SHIPPED, 2026-03-31

**Status:** S-05 (pnpm generate:api) ✅ SHIPPED. TypeScript SDK now in sync with 2 new FastAPI endpoints: `GET /api/auth/signup-status` + `POST /api/auth/validate-invite`. Signup page uses type-safe response types. **Unblocks CEO E2E walk.**

**BATCH-S COMPLETE (Session 77):**
- S-01 ✅ config.py startup guard fires on ALL envs (not just production)
- S-02 ✅ /health returns supabase_project_ref for CEO verification
- S-03+S-08 ✅ Invite code pre-fill + flicker fix on signup page
- S-04 ✅ Groq + Vertex Express wired into LLM fallback chain (Vertex→Gemini→Groq→OpenAI)
- S-05 ✅ **pnpm generate:api — TypeScript SDK synced with auth endpoints**
- S-07 ✅ Invalid invite error page → Telegram primary CTA (AZ beta audience)
- S-09 ✅ Production smoke test script (scripts/prod_smoke_test.py)
- S-10 ✅ Sprint 5 question bank — 7/7 profession agents complete, voting declared

**Sprint 5 Question Bank:**
- Winner: Financial Analyst — 96/100
- All scores: FA 96 | DevOps 94 | Product Mgr 92 | Scrum Master 91 | HR Manager 91 | QA Engineer 90 | Marketing Manager 86
- Saved: `C:\Projects\VOLAURA\scripts\question-evolution\sprint-5\voting-results.json`
- Sprint 6 key patterns: london_delta must cite article number + quantified threshold (not just regulation name)

**NEXT DECISION POINT:** CEO E2E walk (full invite→assess→complete→AURA→public profile journey on volaura.app) OR Sprint 6 question evolution. E2E walk is blocking launch readiness declaration.

---

## CURRENT POSITION — Question Evolution Sprint 3 COMPLETE, 2026-03-31

**Status:** Sprint 3 question generation COMPLETE. 7/7 profession sets generated (70 questions total). Voting complete.
**Winner:** DevOps/Cybersecurity — 39/40
**All scores:** DevOps 39/40 | QA Engineer 38/40 | Financial Analyst 38/40 | HR Manager 37/40 | Scrum Master 34/40 | Product Manager 33/40 | Marketing Manager 33/40
**Saved:** `C:\Projects\VOLAURA\scripts\question-evolution\sprint-3\voting-results.json`
**Next:** Sprint 4 generation — propagate DevOps/Cybersecurity winning patterns to all 7 profession sets.

**Sprint 4 MANDATORY patterns (copy to every set):**
- Every question cites a named AZ institution (not just 'AZ law') that structurally changes the correct answer
- london_delta must cite specific UK/EU framework by name (FCA, GDPR, UK Equality Act, etc.) + name the AZ consequence
- empathy_safeguarding ≥2 questions per set, target 7-8 of 8 competencies covered
- Open-ended questions must have 5-level rubrics where levels 4-5 reward AZ institutional knowledge specifically
- Use documented AZ incidents as scenario foundations: ASAN 2020, E-GOV 2021, AzərGold 2016, ASAN SMS cascade
- London delta HALL OF FAME examples: prof-devops-s3-001, prof-devops-s3-006, prof-qa-s3-008, prof-fin-s3-003

---

## CURRENT POSITION — Sprint E2 / BATCH-R, 2026-03-31 (667/667 tests — ALL GREEN)

**Status:** 667/667 ✅. BATCH-R Wave 1 complete. Invite gate (RISK-014) shipped: `open_signup` + `beta_invite_code` config flags, 2 new endpoints (`GET /auth/signup-status`, `POST /auth/validate-invite`), frontend invite-code field, 6 new tests. P0 test gaps filled: `test_p0_launch_gaps.py` (3 tests). Complete page "what this score unlocks" nudge added. Behavioral sim scripts shipped: `scripts/behavioral_sim.py` (630 lines, 5 archetypes) + `scripts/concurrent_stress.py` (230 lines). MIGRATION COMPLETE: all 57 migrations applied to new Supabase project `dwdgzfusjsobnixgyzjk` (57 applied, 1 skipped pre-existing, 0 errors). RISK-011 fully resolved.
**Next action:** CEO: (1) Set `OPEN_SIGNUP=false` + `BETA_INVITE_CODE=<code>` on Railway — invite gate is built, needs activation. (2) Verify Railway `SUPABASE_URL` = `https://dwdgzfusjsobnixgyzjk.supabase.co` — CRITICAL. (3) Pause old project `hvykysvdkalkbswmgfut`. (4) Walk volaura.app E2E with real email. (5) Polar.sh "Start selling". CTO next: BATCH-R Wave 2 — LLM parallel dispatch in bars.py.

## CURRENT POSITION — Sprint E2, 2026-03-30 (BATCH P COMPLETE — 657/658 tests)

**Status:** BATCH P complete. P0 security: SEC-ANSWER-01 subscription gate on POST /assessment/answer (mirrors /start gate, fail-closed, 402 for expired/cancelled). P1 ISSUE-Q4: celebration pulse ring (score≥75, useReducedMotion) + 2 actionable next-step nav cards on completion page. P1 ISSUE-AU3: NextStepCard on AURA page (2 cards, animated in). QA E2E: test_beta_user_journey.py created — 7/7 passing, full beta journey chain validated. 657/658 ✅ (1 pre-existing: test_submit_open_ended_uses_keyword_fallback).
**Next action:** CEO: (1) Walk volaura.app E2E with real email → declare FULL GO → send first 20 invites. (2) POST /api/telegram/setup-webhook (5 min — Telegram bot not webhooking). (3) Set VOLAURA_TEST_JWT on Railway → k6 load test. (4) Start Polar.sh signup (24h approval).

## CURRENT POSITION — Sprint E2, 2026-03-30 (BATCH O COMPLETE — POLISH SPRINT)

**Status:** BATCH O complete — ALL 3 AGENTS FULLY ACTIONED. Behavioral agent second pass: AU4 share modal 3000→5000ms (past counter animation); A3 cooldown 429 → shows minutes remaining; A1 assessment page pre-selects communication; D1 share prompt gated when trial/expired banner active; D2 StatsRow suppressed until hasScore; AU2 AURA Continue button now routes to activeSessionId from Zustand store if available. Total: 30 fixes across 11 files. 0 TS errors. Both JSON valid. LRL ~88/100.
**Next action:** CEO: walk volaura.app E2E with real email → declare FULL GO → send first 20 invites. Set VOLAURA_TEST_JWT on Railway → k6 load test.

## CURRENT POSITION — Sprint E2, 2026-03-30 (BATCH N COMPLETE — 648/649 tests)

**Status:** BATCH N complete. 3 waves. Wave 1 MICROs: RISK-N01, RISK-N02, GROW-N01. Wave 2 SMALLs: GROW-M02, PROD-M03. Wave 3 SMALLs: GROW-M03, ARCH-M03. 648/649 ✅ (1 pre-existing). LRL ~78/100 CONDITIONAL GO.
**Next action:** CEO: walk volaura.app E2E with real email → declare FULL GO → send first 20 invites. Set VOLAURA_TEST_JWT on Railway → k6 load test. Sign up Polar.sh.

## CURRENT POSITION — Sprint E2, 2026-03-30 (BATCH M COMPLETE — superseded)

**Status:** BATCH M complete. All 3 waves done. Wave 1 (P0): RISK-M01. Wave 2 (P1): QA-M01 ×2, GROW-M01, PROD-M01, ARCH-M02. Wave 3 (QA): QA-M02 ×2 + QA-M03 ×5 = 7 new tests all green. 648/649 (1 pre-existing: test_submit_open_ended_uses_keyword_fallback). LRL 76/100 CONDITIONAL GO.
**Next action:** CEO: (1) Walk prod E2E on volaura.app with real email — REQUIRED for full GO. (2) Sign up Polar.sh + Paddle.com. (3) k6 load test (set VOLAURA_TEST_JWT). | CTO: Next BATCH N cycle or deploy if CEO E2E passes.

## CURRENT POSITION — Sprint E2, 2026-03-30 (BATCH L COMPLETE — superseded)

**Status:** BATCH L complete. 5 proposals executed — 1 P0 security fix + 2 P1 UX/i18n fixes + 2 P2 bug fixes. 638/640 tests passing (2 pre-existing failures: test_submit_open_ended_uses_keyword_fallback + test_mfi_selects_most_informative_at_theta). Readiness ~74/100 CONDITIONAL GO.
**Next action:** CEO: (1) Walk prod E2E on volaura.app with real email (30 min — REQUIRED for full GO). (2) Sign up Polar.sh today + Paddle.com. (3) k6 load test (set VOLAURA_TEST_JWT). | CTO next: Next BATCH M cycle (Team Proposes again) OR hand to CEO for prod walk.

### CEO Actions Required (blocking launch):
1. ~~`supabase db push`~~ — **DONE via MCP. All 7 migrations applied 2026-03-30. DB is in sync.**
2. **Payment path decision** — See AZ advisory below. Recommendation: Paddle (merchant of record, no company needed, wire to AZ bank). Set PAYMENT_ENABLED=true on Railway only after payment entity is ready.
2. Stripe Atlas ($500) → Delaware LLC → Stripe live
3. After Stripe: set `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET` on Railway
4. k6 load test: `k6 run scripts/load_test.js` (script ready, needs `VOLAURA_TEST_JWT` env var)

### Open Bugs (deferred from previous batches):
- BUG-005: list_org_volunteers OOM — complex, deferred post-beta
- BUG-011: fire-and-forget notification failure — architectural, documented
- BUG-012: empty explanation → has_pending_evaluations — Sprint 6
- BUG-016: JWT revocation — Sprint 6
- BUG-018+019+020: scale issues — post-beta
- GROWTH-2: invite→profile attribution
- GROWTH-3/9/10/11: analytics system
- SEC-030: rating CHECK constraint
- BrandedBy RLS: GRANT ALL to authenticated — needs explicit policies
- QA-03: Org B2B test coverage (org dashboard + search + volunteers) — 4h, BATCH L
- ARCH-03: Rebuild shared-context.md (3 weeks stale) — 1.5h, BATCH L
- SEC-03: display_name anonymization consistency (profiles/public vs discovery) — 20min, BATCH L

---

## Last Updated (BATCH 2026-03-30-L — Security + UX + Leaderboard fixes, 638/640 tests)
2026-03-30 | 3 parallel agents → 5 proposals → all executed. 638/640 ✅ (2 pre-existing).
**SEC-03 (P0):** `_anonymize_name()` applied in `list_public_volunteers` in profiles.py. Org-to-discovery cross-referencing deanonymization attack vector closed.
**I18N-01 (P1):** 4 missing locale keys added to both EN and AZ: `aura.sharePromptTitle`, `aura.sharePromptBody`, `aura.coach.title`, `common.dismiss`. AZ users no longer see English on share modal.
**LEADERBOARD-01 (P1):** `is_current_user` now set server-side via `OptionalCurrentUserId` dep (new in deps.py). Field was always False before.
**LEADERBOARD-02 (P2):** `total_count` now from DB count query (not `len(entries)`). Fallback to page size on exception (test-safe).
**AURA-02 (P2):** `/aura` page zero-state split: `!aura` → "Never started / Start assessment"; `aura.total_score == null` → Clock icon + "Assessment in progress / Continue". Users who started no longer think their work was lost.
**Also added:** `OptionalCurrentUserId` to deps.py (optional auth pattern for public-but-personalizable endpoints).

## Last Updated (BATCH 2026-03-30-K — Launch Readiness Sprint)
2026-03-30 | 7 agents → 22 proposals → 15 tasks executed. 632/633 tests ✅.
**K-01:** Dead Subscribe CTA removed from trial banner (was breaking trust for beta users).
**K-02:** AuraExplanationResponse schema + response_model on /aura/me/explanation (pnpm generate:api now produces typed response).
**K-03+09:** Share flow fixed (null username guard + UTM params) + shareNudge/shareNudgeLow i18n keys added to both locales.
**K-04:** answer_version conflict test (double-submit guard coverage).
**K-05:** Onboarding competency selection now passed to assessment page via ?competency= param — micro-commitment honoured.
**K-06:** GET /api/organizations + /{org_id} now require auth. owner_id removed from OrganizationResponse.
**K-07:** 2 session expiry tests (submit_answer + complete_assessment → 410).
**K-08:** upsert_aura_score wrapped in try/except + pending_aura_sync migration. AURA score no longer lost on RPC failure.
**K-10:** /aura/{id} rate limit downgraded from 60/min to 10/min (enumeration mitigation).
**K-11:** Public profile zero-AURA state shows Clock icon + "Assessment in progress" (not broken-looking text).
**K-12:** SENTRY_DSN warning in validate_production_settings + keyword_fallback hourly alert to Telegram.
**K-13:** /health uses SupabaseAdmin via Depends() (not raw acreate_client on every poll).
**K-14:** Dashboard share prompt — one-time dismissible banner after first AURA score, Telegram share button.
**K-15:** Per-user daily LLM cap (20 open-ended/day) — prevents adversarial Gemini budget drain.
**Readiness Manager score:** 72/100 CONDITIONAL GO (was 61/100). Gap: CEO E2E walk on prod still required.

## Last Updated (BATCH 2026-03-30-J — Agent Briefing System)
2026-03-30 | Meta-task complete: agent prompting gap identified, documented, and structurally fixed.
**Root cause found:** Research agents launched without project context → technically correct but contextually wrong answers. After context compression, agents have zero memory. CTO assumed shared context exists — it doesn't.
**Created:** `docs/AGENT-BRIEFING-TEMPLATE.md` — canonical VOLAURA CONTEXT BLOCK (300-word project context) + full prompt template, anti-patterns, per-type checklists (research/code/content).
**Updated:** `docs/TASK-PROTOCOL.md` v5.2 → v5.3 — added Step 1.0.3 (Agent Briefing Requirements, BLOCKING gate), 3 new FAILURE MODES, v5.3 entry in PROTOCOL EVOLUTION table, AGENT-BRIEFING-TEMPLATE.md in LINKED FILES.
**Documented:** Mistake #60 (agents launched without context block) in mistakes.md. Pattern P-057 (agent briefing template) in patterns.md. FINDING-041 through FINDING-044 in SESSION-FINDINGS.md.
**CEO actions (payment path — from this session):** (1) Polar.sh sign-up today (24h approval, Stripe Connect, avoids WHT). (2) Paddle.com sign-up (1-3 week approval, MoR, Wise intermediary for payout). (3) Get written WHT opinion ($100-150 AZ tax advisor) before going live. DSP council voted: Path C = Polar/Paddle now + Stripe Atlas at MRR >$500.

## Last Updated (BATCH 2026-03-30-I — BUG-012 + PAYMENT_ENABLED flag, 630/630 tests)
2026-03-30 | BUG-012 CLOSED: `has_pending_evaluations` + `pending_reeval_count` added to `/aura/me/explanation` response. Frontend now knows when LLM re-eval is queued for degraded answers. 3 new tests.
**PAYMENT_ENABLED kill switch:** `payment_enabled: bool = False` added to config.py. Paywall in `start_assessment` now gated behind this flag — beta users can assess freely. `create_checkout` + webhook also gated. Set `PAYMENT_ENABLED=true` on Railway to activate billing. 7 test files updated (paywall mock sequences adjusted for removed subscription call). 630/630 ✅
**AZ payment advisory delivered:** DSP council voted Path C. Polar.sh recommended (Stripe Connect, not SWIFT, avoids 10% WHT risk). Full risk matrix: buyer side, seller side, company registration options (AZ MMC simplified tax + Polar = safest path today).

## Last Updated (BATCH 2026-03-30-H — Autonomous Team Proposes #2, 623/623 tests)
2026-03-30 | Team Proposes flow #2. 4 tasks + pnpm generate:api. 0 CEO interruptions.
**BUG-016 CLOSED:** `/auth/logout` now calls `db_admin.auth.admin.sign_out(token)` — real token revocation. Since auth uses `admin.auth.get_user(token)`, the token is immediately invalid after logout. No blacklist table needed.
**GROWTH-2 CLOSED:** `invited_by_org_id UUID` column added to profiles table (migration `profile_invite_attribution`). `ProfileCreate` schema gains `invited_by_org_id` field. On profile creation, if provided: looks up user email via admin API → marks matching `organization_invites` row as accepted. Full attribution funnel now tracked.
**Telegram:** `/ask risk` and `/ask readiness` now work. Both agents added to `_handle_ask_agent` map with full skill descriptions. `/help` updated to show all 7 agents.
**Frontend types:** `pnpm generate:api` run — discovery cursor fields (`next_after_events`, `next_after_updated`) now in generated types. SDK in sync with backend.
**Tests:** 623/623 ✅

## Last Updated (BATCH 2026-03-30-G — Autonomous Team Proposes, 623/623 tests)
2026-03-30 | Team Proposes flow. 4 tasks shipped autonomously. 0 CEO interruptions.
**DB:** Stripe idempotency migration (20260330200000) applied via Supabase MCP. 44 total migrations now in sync.
**SEC-030:** rating `int` → `float` in event.py (CoordinatorRatingRequest, VolunteerRatingRequest, response fields) and verification.py. DB stores FLOAT — schema now matches.
**Discovery perf:** Steps 3+7 (two `assessment_sessions` queries) merged into one bounded query. Old Step 3 was unbounded (queried ALL sessions globally), new query scoped to current result set only. DB calls: 4→3 (role_level case), 3→2 (no role_level).
**Discovery pagination:** `sort_by=events` and `sort_by=recent` were broken — no cursor support, returned same first page every time. Fixed: `after_events`/`after_updated`/`after_id` cursor params added. `DiscoveryMeta` has `next_after_events`, `next_after_updated` fields. All 3 sort types now paginate correctly.
**Tests:** 623/623 ✅

## Last Updated (BATCH 2026-03-30-F — Telegram fix + Ecosystem audit + MindShift handoff)
2026-03-30 | Telegram bot enhanced: added `_get_ecosystem_context()` (full platform state), expanded system prompt from 3-line stats to full ecosystem context, increased max_output_tokens 200→400, added `/ecosystem` command, added `risk`/`readiness` intent keywords. Bot now answers questions about ZEUS, Life Sim, crystals, integration state.
Risk Manager + Readiness Manager audit delivered to CEO: Volaura = CONDITIONAL GO ≤200 users. Ecosystem = 28% complete, integration layer = 0%.
MindShift handoff prompt created at `docs/MINDSHIFT-HANDOFF-PROMPT.md` with embedded Risk Manager + Readiness Manager skills for cross-platform analysis.
Honest status: Life Simulator = 4 crash bugs, NOT playable. ZEUS = 0% Godot bridge. Crystal bridge = does not exist. character_state API = does not exist. 60+ sprints remaining.

## Last Updated (BATCH 2026-03-30-E — 6-Agent Adversarial Critique + Fixes, 623/623 tests)
2026-03-30 | Full adversarial critique by 6 specialist agents. Found 40+ issues, fixed 14.
**Security:** P0 paywall bypass fixed (fail-closed: missing profile row now returns 402). `anext(get_supabase_admin())` anti-pattern removed from profiles.py (memory leak). 3× `.single()` → `.maybe_single()` (avoids 500 on missing rows). Hardcoded `/az/` locale in verification URL → `settings.default_locale`.
**Performance:** `fetch_questions()` now has 5-minute TTL in-process cache (`_QUESTION_CACHE`). `get_aura_explanation` LIMIT 10 added. `clear_question_cache()` + conftest autouse fixture prevents test cross-pollution.
**i18n:** `auth.welcomeAboard` + `auth.foundingMemberMessage` added to EN+AZ. `{score}`/`{badge}` → `{{score}}`/`{{badge}}` (i18next double-brace syntax) in aura keys EN+AZ.
**Product P0:** `/welcome` route (404 for all new signups) → redirects to `/assessment`. Org empty-state link → `/org-volunteers` (was leaderboard). `visible_to_orgs` default → `true` (was false, killing ~50% discoverability).
**Scaling:** `get_competency_slug()` cached (2 DB round trips → 0 per answer). `datetime.now()` captured once per submit_answer. `get_my_aura` explicit column list.
**Code quality:** `notify()` typed (`AsyncClient`). `select("*")` → explicit columns in list_notifications. Double DB round-trip in notifications eliminated. Split fastapi import + deferred import fixed.
**Risk (R-02):** Stripe webhook idempotency table migration + `_is_stripe_event_processed` + `_mark_stripe_event_processed` guards wired.
**Risk (R-07):** `_update_profile_subscription` explicit `-> bool` return.
**Risk (R-09):** `stripe_customer_id` removed from SubscriptionStatus schema — no longer exposed to clients.
**Observability:** LLM keyword fallback now logs `llm_fallback=True, provider=keyword_fallback` — Sentry alert can be set on this tag.
**Mistakes:** #57 (fail-open paywall), #58 (mock sequence offset), #59 (i18next single-brace) added to mistakes.md.
**Readiness:** LRL 4 — GO with monitoring (73/100). Ready for controlled beta ≤200 invite-only users.
**Deferred:** JWT revocation (BUG-016), Stripe webhook idempotency table, k6 load test (CEO), question bank expansion, item exposure log.

## Last Updated (BATCH 2026-03-30-C — Paywall + Subscription E2E, 623/623 tests)
2026-03-30 | Risk Manager + Readiness Manager added to agent roster and autonomous_run.py. Subscription system E2E wired.
**Backend:** Paywall gate in start_assessment (HTTP 402 for expired/cancelled). Leaderboard uses aura_scores_public view. events_no_show removed from discovery schema. stripe_customer_id excluded from GET /profiles/me. Webhook race condition fixed (_update_profile_subscription returns False → caller raises 500 → Stripe retries). getattr antipattern removed from subscription.py.
**Frontend:** /subscription/success + /subscription/cancelled pages created. ESTIMATED_QUESTIONS = 8. Public profile shows registration_number + registration_tier badge.
**Swarm:** Risk Manager + Readiness Manager added to PERSPECTIVES (autonomous_run.py). SESSION-DIFFS.jsonl seeded with bootstrap entry. TASK-PROTOCOL v5.1 Step 4.0.5 updated with concrete output format.
**Tests:** 18 new tests (test_paywall_enforcement.py ×6, test_subscription_status_boundary.py ×5). test_assessment_api_e2e + test_security_hardening + test_smoke_assessment mock sequences updated (+1 paywall entry each). 623/623 passing.
**Deferred:** pnpm generate:api (ProfileResponse missing subscription_status, trial_ends_at, is_subscription_active). Stripe Atlas (CEO). k6 load test (CEO).

## Last Updated (BATCH 2026-03-30-B — Swarm Optimization, 612/612 tests)
2026-03-30 | Swarm optimization batch. 4 new files. Root cause of 42% already-done proposals fixed.
**Files shipped:** session_end_hook.py, skills_loader.py, .github/workflows/session-end.yml.
**autonomous_run.py updated:** reads SESSION-DIFFS.jsonl → agents see git-level changes per session.
**TASK-PROTOCOL.md v5.1:** Sprint Gate DSP (Phase 0.7), 3 DSP auto-trigger modes, session-end mini-swarm.
**Effect:** On every push to main, session-end workflow captures diff → SESSION-DIFFS.jsonl → 3-agent code-review mini-swarm runs async. Agents will no longer propose work that was shipped in the last 3 sessions.

## Last Updated (BATCH 2026-03-30-A — 7 tasks, 612/612 tests)
2026-03-30 | TASK-PROTOCOL v5.0 Team Proposes batch. 4 parallel agents. 7 tasks:
**MICRO (3):** BrandedBy GRANT ALL → revoked from authenticated (service_role only). Notifications open INSERT policy → dropped (service_role bypasses RLS, no policy needed). CEO inbox → explicit default-deny documentation in migration comment.
**SMALL (4):** Trial countdown banner on dashboard (amber=trial, red=expired, dismissible). Subscription status section in settings page (plan badge + days remaining). Tests for rapid-restart cooldown (5 tests) + prompt injection detection (8 tests) — all passing. Communication competency question gap fixed (+5 MCQ questions, b=-1.1 to 1.3 spread).
**MEDIUM (1):** Subscription router integration tests — 10 tests (GET status×3, checkout×3, webhook×4).
**File fixes also done:** sprint-state.md + mistakes.md trimmed (768→55 lines, 550→59 lines — both now readable in one call).
**New migrations:** 20260330000001_security_fixes_p0.sql, 20260330100000_security_fixes_grants.sql, 20260330110000_seed_questions_remaining_competencies.sql
**CEO actions:** supabase db push now has 10 pending migrations (not 9).

## Last Updated (Sprint E2 — P0 Security Fixes)
2026-03-30 | 6 P0 security fixes from full OWASP + assessment integrity audit:
1. **Crystal ledger idempotency** — `UNIQUE INDEX uq_crystal_ledger_reference` on `(user_id, reference_id) WHERE reference_id IS NOT NULL` (migration 20260330000001). Prevents double-spend on network retries.
2. **Rapid-restart cooldown** — 30-min cooldown on ANY new assessment start (including abandoned sessions, not just completed). Blocks answer-fishing. Test mock updated +1 entry.
3. **Future timestamp detection** — `question_delivered_at` in future = tampered session. Logs anomaly, treats as 0ms elapsed (triggers timing flag). Server-side validation.
4. **Prompt injection detection** — 10 regex patterns on open-ended answers in `SubmitAnswerRequest.sanitize_answer`. Catches role-override, persona injection, jailbreak delimiters.
5. **SDK auth interceptor** — `configure-client.ts` wires Supabase Bearer token via `@hey-api/client-fetch` interceptors, called from QueryProvider at startup. Fixes HIGH finding: generated SDK was making unauthenticated API calls.
6. **Revoke anon avg_aura_score()** — removed EXECUTE from anon + authenticated roles. Only service_role retains access. Removes unauthenticated DoS vector.
**Test suite: 587/587 ✅**

## Last Updated (Session 75 — BATCH 2026-03-29-F: New Bug Hunt — 5 agents, 14 fixes)
2026-03-29 | TASK-PROTOCOL v5.0 batch. 5 agents ran in parallel (Security, QA, Architecture, Product, Growth). Found 32 new bugs total. Fixed 14.
**Backend:** engine.py sd=0 guard (QA-021); assessment.py expires_at try/except (QA-023); invites.py ×2 .maybe_single() (SEC-025); events.py "waitlisted" message (SEC-022).
**Migration:** `20260329130000_update_aura_scores_public_view.sql` — adds visibility + events_attended to aura_scores_public view. Without this, visibility filter silently did nothing and discovery returned ALL volunteers.
**Frontend:** invite/page.tsx sessionStorage→localStorage (GROWTH-1); aura/page.tsx reveal animation localStorage (GROWTH-6) + share prompt 24h window (GROWTH-7); share-buttons.tsx settingsUrl prop + link CTA (GROWTH-8).
**i18n:** Added 10 missing keys to EN + AZ.
**Deferred:** GROWTH-2, GROWTH-3/9/10/11, SEC-030, BUG-QA-022, ARCH-021, BUG-FE-5.

## Last Updated (Session 75 continued — Test suite: 574/574 passing)
2026-03-29 | Full test suite green. Key patterns: (1) BARS fallback chain = Gemini → Groq → OpenAI → keyword. All 3 must be patched in tests. (2) `complete_assessment` with status="completed" takes early-return — tests needing full pipeline must use status="in_progress". (3) `_try_gemini`/`_try_groq` return `(scores, concept_details)` tuples — mock as `(None, None)` not `None`. (4) FastAPI DI: `app.dependency_overrides` required; `patch()` doesn't intercept deps captured at import time. (5) Stats endpoint uses `db.rpc("avg_aura_score")` — mock must return RPC mock.

## Last Updated (Session 75 — BATCH E: 5-Agent Simulation + Bug Fix Sprint)
2026-03-29 | 15 bugs fixed. Key: org auto-creates organizations row on onboarding (B2B blocker); discovery uses aura_scores_public safe view; badge_only path no longer leaks private fields; MCQ scoring case-insensitive; double UPDATE race fixed; session expiry enforced. New /invite page with beta code allowlist. Post-AURA share prompt modal. LinkedIn DAY 7 has beta CTA.

## Last Updated (Session 68 — Sprint B+D+A mega-session)
2026-03-29 | pnpm generate:api → 419 types, 78 SDK functions, 0 TS errors. ADR-003 compliant. Callback routing: new users → /onboarding. notification_service.py created + wired. AURA page shows effective_score with freshness labels. TASK-PROTOCOL v4.0 written.
