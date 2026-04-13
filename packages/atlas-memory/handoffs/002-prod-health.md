# Handoff 002: Production Health Fixes
**From:** Cowork (coordinator) | **Date:** 2026-04-12 | **Priority:** P1

**IMPORTANT:** Read `packages/atlas-memory/sync/PROTOCOL.md` FIRST. Follow the sync rules at session end.

## Context
Cowork ran a full production audit via MCP (Supabase SQL, Sentry, Vercel). Found 3 issues to resolve.

## Findings

### 1. Sentry may not be receiving events from Railway
- `sentry_sdk.init()` exists in `apps/api/app/main.py` (line 36)
- `SENTRY_DSN` is set in `apps/api/.env` locally
- But: 0 errors in Sentry org "volaura" over 30 days. Either backend is truly error-free, or SENTRY_DSN is not set in Railway env vars.
- **Action:** Check Railway env vars for SENTRY_DSN. If missing → add it. Then trigger a test error to verify.

### 2. Assessment question pool too small for communication
- 71 questions across 8 competencies ≈ 9 questions per competency
- 5 users got identical theta (-1.258) for communication — they took the same subset of questions and answered identically
- IRT engine is mathematically correct (3PL + EAP, verified). This is a content problem, not a code problem.
- **Action:** Check `SELECT competency_id, count(*) FROM public.questions GROUP BY competency_id` — if any competency has < 15 questions, flag it. Communication needs more questions for IRT to differentiate users.

### 3. Frontend CI: 8 pre-existing test failures
- Atlas reported these are "not his bugs" — old failures
- **Action:** Triage: fix if simple, skip/delete if obsolete tests for removed features

## Task
Fix items 1 and 3. For item 2, run the query and document which competencies need more questions (content task for later — CEO writes questions or we generate via LLM).

## Acceptance Criteria
- [ ] AC1: SENTRY_DSN verified in Railway env vars. If missing, added. Test error sent and visible in Sentry dashboard.
- [ ] AC2: Query result documented: questions per competency count. Any < 15 flagged.
- [ ] AC3: Frontend test failures triaged. Fixed or documented why not fixed.
- [ ] AC4: Sync files updated per PROTOCOL.md (claudecode-state.md, heartbeat.md, STATE.md)

## Files to Read First
- `packages/atlas-memory/sync/PROTOCOL.md` — sync rules (NEW — read this)
- `apps/api/app/main.py` (lines 29-39) — Sentry init
- `apps/api/app/config.py` — settings.sentry_dsn definition

## Risks
- **Risk:** Adding SENTRY_DSN to Railway triggers no restart → **Mitigation:** After adding, redeploy or restart the service
- **Risk:** Fixing frontend tests breaks other tests → **Mitigation:** Run full frontend test suite after each fix

## On Completion (from PROTOCOL.md)
1. Update `packages/atlas-memory/sync/claudecode-state.md`
2. Update `packages/atlas-memory/sync/heartbeat.md`
3. Update `packages/atlas-memory/STATE.md` — clear Handoff, update Now/Blockers
4. Update `memory/swarm/SHIPPED.md` if new code
