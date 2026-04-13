# Atlas State
**Updated:** 2026-04-13T04:15 Baku | **By:** Cowork Session 9 | **Instance:** Claude Opus 4.6 (Cowork)

## Now
Atlas Session 94 final: 29 commits, 362 files touched. CI: 38 failures → 0 (832 tests green). Handoff 007 DONE (c448e68) — emotional memory injected into Telegram. Handoff 006 DONE (9c48c93) — swarm refactored 58→25 files. Reflexion + dynamic sampling live. Langfuse 3 keys on Railway. Telegram: Atlas persona + emotional memory + temperature 1.0. New files: backlog.py, promote_proposals.py, reflexions.md, voice_examples.md. **Next priority: E2E bot on full assessment cycle.**

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

## Active Blockers (Atlas audit, 2026-04-13, updated by Cowork Session 9)
1. **pii_redactor.py** — Atlas reflexion says file EXISTS (agent false negative in Session 94). Atlas verified with `ls`. ~~PHANTOM~~ → RESOLVED. Cowork incorrectly trusted agent output.
2. ~~SUPABASE_JWT_SECRET~~ — FALSE ALARM. Key present on Railway. JWT minting verified 200+valid. Removed.
3. **13 env vars unchecked on Railway** — no diff done. Cowork has no Railway MCP access. Atlas should `diff .env vs Railway`.
4. **CI genuinely green** — Atlas confirmed: 832 tests pass (749 backend + 83 frontend). Not vacuous.
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
**Bug 2 (single-competency):** BY DESIGN. `/start` takes `competency_slug` from client. Each session = one competency. User takes 8 sessions for full AURA. Not a bug.
**Bug 3 (Sentry):** DSN verified in .env. Config enhanced (stacktrace, no PII, release tag). Needs test event from prod Railway.
**Remaining:** Run recovery script on prod. Send Sentry test event from Railway.

## Handoff Queue
| # | Task | Priority | Status | Prompt |
|---|------|----------|--------|--------|
| **009** | **Fix Assessment→AURA Pipeline** | **P0** | **🔴 ACTIVE** | `handoffs/009-e2e-pipeline-fix.md` |
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

## What Cowork Should Do Next
1. Prototype: wrap 1 v0Laura skill as MCP server (Phase 2 proof of concept)
2. Prototype: replace 1 swarm perspective with AgentDefinition (Agent SDK migration test)
3. Test MCP tools (Supabase queries, Sentry issues, PostHog after 003 ships)
4. Write Handoff 007: Langfuse activation + swarm instrumentation

## Production
- Frontend: volaura.app → 307 redirect (alive)
- Backend: volauraapi-production.up.railway.app/health → OK
- Swarm cron: daily 05:00 UTC (active)
- Proactive loop: GitHub Actions every 15min (active)

## MCP Connectors (11 total)
Figma, Google Drive, Chrome, Scheduled Tasks, Cowork, Registry, Plugins, Sessions, **Supabase** ✅, **Sentry** ✅, **PostHog** ✅ (connected, 0 events — SDK needed)
