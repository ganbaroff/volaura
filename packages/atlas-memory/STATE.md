# Atlas State
**Updated:** 2026-04-13T19:05 Baku | **By:** Cowork Session 9 (post-verification) | **Instance:** Claude Opus 4.6 (Cowork)

## Now
**🎯 HANDOFF 012 — REALITY PROBE is the only active priority.**

Cowork retracted "PROD API DOWN" — that was sandbox egress blindness (HTTP 403 from proxy mistaken for HTTP 000 from prod). Supabase logs show live `python-httpx/0.28.1` traffic from Railway 17:14–17:45 UTC today. **API is alive.** Full retraction evidence: `packages/atlas-memory/knowledge/verification-2026-04-13.md`.

Handoff 011 is ON HOLD until Atlas runs Handoff 012 and returns ground truth.

**Atlas (local Claude Code): execute `handoffs/012-full-reality-probe.md` — 9 probes, 90–120 min, output goes into `sync/claudecode-state.md` under `## Reality Probe 2026-04-13`.** Rule: no coding during the probe. Fixing comes in Handoff 013.

Atlas Session 96: ZEUS→ATLAS rename, Life Sim P0 fixes, Phase 1 migration ready.
Verified real issues (from re-audit): 5 orphan sessions (UUIDs listed in verification report), 3 live Constitution violations (leaderboard leftovers in `dashboard/page.tsx:17,163,338`), 1 Supabase ERROR (SECURITY DEFINER view bypasses RLS), question bank below threshold for 4 competencies, ecosystem_events wiring uncommitted in working tree.

## v0Laura
**The real product.** 1 platform + skill library. Agents = interface. Skills = product. Assessment is one skill among many. Atlas becomes the engine inside VOLAURA: knows what to do, who to call, what decisions to make. Code exists: `apps/api/app/routers/skills.py`. 5 skills allowed. This is the architecture, not VOLAURA-the-assessment-form.

## Blockers
- **SWARM IS DETECTION ONLY, NOT COORDINATION** — backlog.py exists but is disconnected from agent runtime. Handoff 004 addresses this.
- **PostHog receives 0 events** — SDK not installed in frontend. Handoff 003 addresses this.
- Telegram bot: webhook responds ok, actual user-facing functionality unverified/broken
- ~~3 stale docs~~ ✅ deadlines.md updated, volaura.md updated, EXECUTION-PLAN.md archived + redirected
- flush_langfuse() defined but never called in main.py
- Swarm has zero Langfuse instrumentation
- 8 pre-existing frontend test failures

## Active Decisions
- Observability: Langfuse (prod tracing) + Phoenix (offline eval). LOCKED.
- Memory architecture: packages/atlas-memory/ — BUILT.
- Agent protocol: CEO not a bus, CTO decides infra. LOCKED.
- MCP stack: 11 connectors. DONE.
- PostHog: dual-write (Supabase + posthog-js). DECIDED.
- Communication: `docs/COMMUNICATION-LAW.md` — radical truth, democracy, caveman. ENFORCED.
- Legal: SADPP, DPA, consent — do ourselves, no external lawyer. CEO decision.
- CLAUDE.md: audited to 205 lines. DONE.
- Architecture: 4-phase innovation roadmap. Agent SDK migration planned for Phase 2. DECIDED.
- Swarm engine: keep custom + refactor. 7 alternatives evaluated, none fits multi-provider debate. ADR-009 SUPERSEDED. DECIDED.
- Doc audit: 250 files scanned, 48 archived, 0 deleted. DONE.
- v0Laura: agents = interface, skills = product, Atlas = engine. CEO-confirmed vision.
- Reflexion system: dynamic context sampling + self-written lessons. style-brake.sh + reflexions.md. LIVE.
- Hierarchy: Atlas leads (CTO), Cowork advises (research), CEO stakeholder. PROTOCOL v2.0. LOCKED.
- Volunteer→professional rename: seed.sql + prod migration. DONE.

## BETA GATES (post-verification 2026-04-13T19:00)

| Gate | Status | Details |
|------|--------|---------|
| 0. Prod API | ✅ ALIVE | Retracted — Supabase logs show live httpx traffic. Cowork curl failed due to sandbox egress. |
| 1. Zero Data Loss | 🔴 FAIL | 5 orphan sessions (UUIDs in verification-2026-04-13.md) — real, unchanged |
| 2. Sentry | ❓ UNVERIFIED | Probe 2 in Handoff 012 checks event count last 7d |
| 3. E2E Test | ❓ UNVERIFIED | Probe 5 in Handoff 012 runs full-journey.spec.ts |
| 4. 3+ Competencies | 🟡 PARTIAL | Only 2/8 tested |
| 5. Degraded Alerting | 🟡 PARTIAL | Untested on prod |
| 6. Constitution | 🟡 15 flags / ~3 real | Probe 6 triages each flag real-vs-noise |

**Handoff 012 (reality probe) must run before Handoff 011 is rewritten. Atlas: no other work until 012 is complete.**

## Previous Blockers (Atlas audit, 2026-04-13)
1. ~~pii_redactor.py~~ → RESOLVED
2. ~~SUPABASE_JWT_SECRET~~ → FALSE ALARM
3. **13 env vars unchecked on Railway** — no diff done. Atlas should `diff .env vs Railway`.
4. **CI genuinely green** — 832 tests pass (749 backend + 83 frontend).
5. **Sentry: 0 events** — DSN set, SDK sends, but events may go to wrong project. Atlas noted in heartbeat. Needs investigation.

## CEO Directives (latest)
- "Apple + Toyota quality. No real users until 100% automated."
- "Абсолютная честность. Ни грамма лжи."
- "Атлас должен помнить, а не симулировать воспоминания."
- "Каждое моё сообщение — триггер для памяти."
- "Всё что хочешь то и делай." — Full autonomy granted.
- Budget: $200+/mo (Claude Max alone = $200). Not $50.

## Handoff 009 — IN PROGRESS (Session 96)
**Bug 1 (pipeline leak):** Recovery script written (`scripts/recover_lost_aura.py`). Needs Supabase SDK to run. Code already has `pending_aura_sync=True` fallback for future failures.
**Bug 2 (single-competency):** BY DESIGN. `/start` takes `competency_slug` from client. Each session = one competency. Cowork's "5 questions" data was stale — batch3 migration (2026-04-14) added 10 more communication + 5 empathy. Current counts: communication=18, empathy=18. Sufficient for CAT convergence.
**Bug 3 (Sentry):** DSN verified in .env. Config enhanced (stacktrace, no PII, release tag). Needs test event from prod Railway.
**Remaining:** Run recovery script on prod. Send Sentry test event from Railway.

## Handoff Queue
| # | Task | Priority | Status | Prompt |
|---|------|----------|--------|--------|
| **012** | **Full Reality Probe (9 probes)** | **P1** | **🎯 ACTIVE** | `handoffs/012-full-reality-probe.md` |
| 011 | Full Prod Fix | P0 | ⏸️ ON HOLD — rewrite after 012 | `handoffs/011-full-prod-fix.md` |
| 010 | Beta Readiness (5 gates) | P0 | ⬆️ SUPERSEDED BY 011 | `handoffs/010-beta-readiness.md` |
| 009 | Fix Assessment→AURA Pipeline | P0 | ⬆️ FOLDED INTO 011 | `handoffs/009-e2e-pipeline-fix.md` |
| 001 | Swarm coordination (Phase 1) | P1 | ✅ DONE (5/6 AC) | `handoffs/001-swarm-coordination.md` |
| 002 | Production health fixes | P1 | ✅ DONE (Sentry DSN set, CI green, bridge works) | `handoffs/002-prod-health.md` |
| 003 | PostHog SDK integration | P2 | 📝 READY | `handoffs/003-posthog-integration.md` |
| 004 | Swarm Phase 2 (sprint cycle) | P1 | 📝 READY | `handoffs/004-swarm-phase2.md` |
| 005 | Research injection into swarm + test run | P1 | ✅ DONE | `handoffs/005-research-injection-swarm-test.md` · `memory/swarm/test-runs/005-research-injection-test.md` |
| 006 | Swarm engine refactor (58→25 files) | P1 | ✅ DONE (9c48c93) | `handoffs/006-swarm-refactor.md` |
| 007 | Fix Atlas emotional memory (20 lines) | P0 | ✅ DONE (c448e68) | `handoffs/007-emotional-memory-fix.md` |
| 008 | volunteer_id → user_id rename (11 tables, 138 code refs, 4 RPCs) | P2 | 📝 READY | `handoffs/008-volunteer-id-rename.md` |

## What Atlas (Claude Code) Did (Session 94 — 29 commits, 362 files)
- **Handoff 007 DONE** (c448e68): Telegram bot now loads emotional_dimensions.md + lessons.md + journal.md. Atlas persona + temperature 1.0.
- **Handoff 006 DONE** (9c48c93): Swarm refactored 58→25 files. Research injection into agent prompts.
- **volunteer→professional rename**: seed.sql cleaned, prod migration applied.
- **Reflexion system**: style-brake.sh rewritten — dynamic context sampling + reflexion trigger. reflexions.md created.
- **E2E bot test**: 4/5 steps passed. Failures found and fixed sequentially.
- **Langfuse**: 3 keys deployed to Railway.
- **CI**: 38 failures → 0. 832 tests green. Ruff clean.
- **New files**: backlog.py, promote_proposals.py, reflexions.md, voice_examples.md.

## What Atlas (Claude Code) Did (Sessions 5-7, archived)
- 17 commits. Swarm 8→13 agents. 1500 lines theater removed. MindShift bridge fixed. Sentry DSN set. Sync protocol established.

## COWORK FINDING — 1-question assessment (2026-04-13T04:30 Baku)

**Diagnosis: NOT a CAT engine bug. E2E bot called /complete prematurely.**

Evidence from prod DB:
- Session `ae6447f7`: 1 item answered, BUT `current_question_id = c0000001-...-000000000007` → engine DID assign next question
- `stop_reason = "manual_complete"` → /complete endpoint was called by bot, not by CAT engine
- `theta_se = 0.839` after 1 item → way above 0.3 threshold → should_stop returned False
- Engine code (engine.py:339): `min_before_se=5` for full energy → SE stop can't fire until 5 items answered

**Root cause:** Bot script called POST /complete/{session_id} after first answer instead of looping on `next_question`.

**Deeper issue (real, but separate):** Communication competency has only 5 questions in pool (vs 10 for other competencies). Even when all 5 answered (session c89e6d80), SE=0.692 — never reaches 0.3 threshold. Stops with `no_items_left`. Other competencies:

| Competency | Questions | Enough for SE convergence? |
|---|---|---|
| communication | 5 | ❌ No (SE=0.692 after 5) |
| empathy_safeguarding | 6 | ❌ Marginal |
| adaptability | 10 | ⚠️ Maybe |
| english_proficiency | 10 | ⚠️ Maybe |
| event_performance | 10 | ⚠️ Maybe |
| leadership | 10 | ⚠️ Maybe |
| reliability | 10 | ⚠️ Maybe |
| tech_literacy | 10 | ⚠️ Maybe |

**Fix plan (2 parts) — Atlas confirmed, in backlog:**
1. **Immediate:** Fix E2E bot — check `is_complete` not `next_question`. Bot called /complete after first answer.
2. **P1:** Add more questions to communication (5→15-20) and empathy (6→15-20) for CAT convergence.

**Atlas note:** `volunteer_id` column still in DB + code. 138 occurrences across 15 files in `apps/api/app/`. DB column rename = migration + code sweep. P2 — not blocking but accumulating debt.

**Atlas correction on Cowork analysis:** Cowork's MCP data may show `current_question_id` from a different session or timing. Atlas confirms the fix is clear regardless: bot loop logic + more questions.

## COWORK FINDING — Telegram Atlas self-learning (2026-04-13T05:15 Baku)

**Status: Code is correct. Deploy status unknown. Self-learning never triggered.**

Evidence:
1. `atlas_learnings` table EXISTS in prod DB — **0 rows.** Gemini extraction never saved anything.
2. `ceo_inbox` has messages up to 2026-04-12 09:54 — **none with message_type='atlas'**. All are generic `free_text`/`report`.
3. Routing code (committed version 3891e8c, 1499 lines): line ~1415 routes `/atlas` and `Атлас`/`Atlas` prefix → `_handle_atlas`. Line ~1459: **ALL free text defaults to `_handle_atlas`** (commit 2b449b2 "route all free-text through Atlas").
4. **LOCAL FILE TRUNCATED**: Cowork's workspace copy is 1295 lines, missing the entire webhook handler (lines 1296-1499). Git version is complete (1499 lines). This is a local sync issue, not a production issue.
5. `_handle_atlas` (line 1139) correctly loads: bootstrap.md, emotional_dimensions.md, lessons.md, journal.md, atlas_learnings from DB.
6. `_atlas_extract_learnings` (line 1071) correctly calls Gemini Flash → parses JSON → inserts into `atlas_learnings`.

**Why 0 learnings?** Three possible causes:
- **A) Railway didn't redeploy** after Session 94 commits. Old code still in prod.
- **B) Gemini API key not on Railway** or expired. Line 1073: `if not settings.gemini_api_key: return` — silent skip.
- **C) CEO hasn't messaged bot since deploy.** Last ceo_inbox message: 2026-04-12 09:54 UTC — Session 94 commits were later.

**Atlas: test by sending any message to Telegram bot. If bot responds as "CTO-бот MiroFish" → old deploy. If responds as "Atlas — Атлас" → new deploy with emotional memory. If no response → Railway down.**

## What Claude Code (Atlas) Should Do Next
1. **Fix E2E bot loop** — the bot calls /complete too early. Loop until `session.is_complete=True`.
2. **Handoff 004** — Swarm Phase 2: connect backlog.py to runtime (P1)
3. **Handoff 003** — PostHog SDK integration in frontend (P2)
4. Fix flush_langfuse() — add to main.py lifespan shutdown
5. Instrument swarm providers with Langfuse decorators

## 🚨 BETA BLOCKER — CEO DIRECTIVE (2026-04-13)

**"никаких юзеров пока не будете готовы"**

5 gates must ALL be PASS before any external user touches the product.
Full checklist: `docs/BETA-READINESS-CHECKLIST.md`

| Gate | Status | Owner |
|------|--------|-------|
| 1. Zero Data Loss | 🔴 FAIL | Atlas (Handoff 009+010) |
| 2. Error Visibility (Sentry) | 🔴 FAIL | Atlas (Handoff 010) |
| 3. E2E Automated Test | 🔴 FAIL | Atlas (Handoff 010) |
| 4. 3+ Competencies Work | 🟡 PARTIAL | Atlas (Handoff 010) |
| 5. Degraded Mode Alerting | 🟡 PARTIAL | Atlas (Handoff 010) |

**Growth plan (`docs/growth/FIRST-10-USERS-PLAN.md`) is FROZEN until 5/5 gates pass.**

## What Cowork Should Do Next
1. Monitor Atlas progress on Handoff 010 via sync files
2. Re-run DB audit after Atlas fixes Gate 1 (verify 0 orphans)
3. Review Playwright E2E test when Atlas writes it (Gate 3)
4. Re-validate AURA math after 3rd competency tested (Gate 4)