# Handoff: Fix Assessment→AURA Pipeline (3 Critical Bugs)
**From:** Cowork | **Date:** 2026-04-13 | **Priority:** P0

## Context
Cowork ran a full production database audit via Supabase MCP. The user funnel is broken:

```
27 profiles → 18 started assessment → 13 completed → 8 got AURA score
                                                       ↑
                                              5 USERS LOST HERE (38% leak)
```

Three critical bugs prevent the core product journey from working end-to-end.

## Bug 1: Pipeline Leak — completed sessions with no AURA score (P0)
**Evidence:** 5 users completed assessment but have `aura_result = NULL` in assessment_sessions and NO row in aura_scores. All 5 are from 2026-04-11 19:09-19:17 UTC. Their theta_estimate = -1.259 (identical — likely same batch/test).

**Root cause hypothesis:** LLM evaluation (Gemini/Groq) failed silently after session marked "completed". The `evaluate_with_llm()` call either timed out, returned invalid JSON, or the upsert_aura_score() RPC wasn't called.

**Fix approach:**
1. Find the code path: assessment complete → evaluate → upsert_aura_score. It's likely in `apps/api/app/routers/assessment.py` in the `/complete` endpoint.
2. Add error handling: if LLM eval fails, log to Sentry AND set a `pending_aura_sync = true` flag (column already exists in assessment_sessions schema).
3. Add a recovery path: background job or on-next-login check that retries AURA calculation for sessions where `status = 'completed'` AND `aura_result IS NULL`.
4. **Immediate data fix:** For the 5 lost users, manually trigger AURA calculation from their stored answers.

**Leaked user IDs (volunteer_id):**
- d7faab58-3ec5-4193-84b1-8b64bf19dde1
- dddbd0d4-2102-401d-b33c-e502d79e7cc5
- e7030d03-ee4e-429c-aeab-48eedc36b42d
- 4d4b0d5d-6768-47e3-adc1-a2c3f7dea3fb
- 36c72369-681c-43c5-acc5-7784211f8bd0

## Bug 2: Single-competency scoring (P1)
**Evidence:** ALL 8 aura_scores rows show only `communication` (7 users) or `communication + reliability` (1 user: atlas_e2e_test). NEVER more than 2 of 8 competencies scored.

**Database reality:**
- 8 competencies exist, all `is_active = true`
- 101 questions across all 8 competencies (10-15 each)
- But assessment sessions only test 1 competency per session

**Question:** Is this by design (user takes 8 separate sessions, one per competency)? Or should one session cover all 8?

If by design: the AURA total_score is meaningless — it's just 1 competency score divided. The frontend shows "Your AURA Score" implying a holistic assessment.

If bug: the session creation logic (`/assessment/start`) needs to either:
- Create 8 sub-sessions (one per competency) in a single sitting
- Or cycle through competencies within one session

**Atlas: check `apps/api/app/routers/assessment.py` — how does `/start` pick competency_id? Is it always defaulting to communication?**

## Bug 3: Sentry dead (P1)
**Evidence:** Sentry MCP returns 0 issues for org "volaura" in last 30 days. Atlas Session 94 noted: SDK works locally (event ID sent from test), but prod may be wrong project or DSN not deployed.

Given Bug 1 (5 users lost silently), this is critical — we're flying blind in production.

**Fix:** Verify `SENTRY_DSN` on Railway matches the correct Sentry project. Send a test event from the Railway deployment. Confirm it appears in Sentry dashboard.

## Acceptance Criteria
- [ ] AC1: The 5 leaked users either have AURA scores recalculated, or `pending_aura_sync=true` flag set for retry
- [ ] AC2: New assessment completions always produce an AURA score (or log an error to Sentry if LLM fails)
- [ ] AC3: Atlas documents whether single-competency-per-session is by design or a bug, and if bug — provides fix plan
- [ ] AC4: Sentry receives at least 1 real event from production Railway deployment
- [ ] AC5: `aura_result` is never NULL for a completed session going forward

## Files to Read First
- `apps/api/app/routers/assessment.py` — the /start and /complete endpoints
- `apps/api/app/services/llm.py` — evaluate_with_llm function
- `apps/api/app/services/aura.py` or wherever upsert_aura_score is called
- `supabase/migrations/` — check if pending_aura_sync column has a trigger or is manual

## Files to NOT Touch
- `apps/web/src/app/globals.css` — just redesigned by Cowork, stable
- `packages/atlas-memory/sync/PROTOCOL.md` — locked
- Any `apps/web/src/components/` — frontend redesign is Cowork's domain

## Risks
- **Risk 1:** Recalculating AURA for 5 users may require their original answers. Check if `answers` JSONB in assessment_sessions has the data. If empty/null, data is lost.
- **Risk 2:** Changing assessment flow (single→multi competency) is a major product change. Document findings, don't implement without CEO confirmation.
- **Risk 3:** Sentry DSN change may require Railway redeploy.

## On Completion
1. Update `sync/claudecode-state.md`
2. Update `sync/heartbeat.md`
3. Update `STATE.md` — clear Handoff section, update Blockers
4. Update `memory/swarm/SHIPPED.md` if new code
