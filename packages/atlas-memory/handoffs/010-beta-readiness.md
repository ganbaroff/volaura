# Handoff 010 — Beta Readiness (P0)

**From:** Cowork Session 9 | **To:** Atlas  
**Date:** 2026-04-13 | **Priority:** P0 — BLOCKS ALL USER ACQUISITION  
**CEO directive:** "никаких юзеров пока не будете готовы"

---

## Context

Cowork completed full assessment engine audit (13 files, 101 questions, 13 real sessions, DB RPC functions). The engine is academically sound — IRT math, BARS evaluation, anti-gaming all work correctly. BUT the pipeline has holes that will embarrass us with real users.

CEO explicitly forbids beta users until 5 gates pass. See `docs/BETA-READINESS-CHECKLIST.md`.

---

## What Atlas Must Do

### Task 1: Fix AURA Data Loss (Gate 1)
**Continues Handoff 009 Bug 1.**

- Run `scripts/recover_lost_aura.py` on production — recover 5 lost AURA scores
- Verify: `SELECT COUNT(*) FROM assessment_sessions s LEFT JOIN aura_scores a ON s.volunteer_id = a.volunteer_id WHERE s.status = 'completed' AND a.volunteer_id IS NULL` → must return 0
- Add retry logic to `/complete` endpoint: if `upsert_aura_score` RPC fails, retry once after 2s before marking `pending_aura_sync`
- Test: complete an assessment and confirm AURA score appears

### Task 2: Resurrect Sentry (Gate 2)
**Continues Handoff 009 Bug 3.**

- Verify DSN on Railway matches Sentry project "Volaura" (not MindShift)
- Send test event from Railway: `python -c "import sentry_sdk; sentry_sdk.capture_message('Handoff 010 test')"`
- Confirm event appears in Sentry dashboard
- Set up alert rule: any new issue → Telegram notification

### Task 3: Write Playwright E2E Test (Gate 3)
**NEW — this is the biggest gap.**

Create `tests/e2e/full-journey.spec.ts`:
1. Sign up with test credentials
2. Navigate to assessment page
3. Select "communication" competency
4. Accept GDPR consent
5. Answer all questions (pick first MCQ option — the specific answers don't matter for this test, we're testing the pipeline)
6. Complete assessment
7. Assert: AURA score visible on profile
8. Assert: public profile page loads with badge

Add to CI: `.github/workflows/e2e.yml` — runs on every push to main.

### Task 4: Test 3rd Competency (Gate 4)

- Run E2E test for "leadership" (or "adaptability" — both have 15 questions)
- Verify AURA recalculates with 2 competency scores
- Manual verification: `SELECT competency_scores FROM aura_scores WHERE volunteer_id = '<test_user>'` should show 2+ competencies

### Task 5: Verify Degraded Mode (Gate 5)

- Confirm `reeval_worker` is running on Railway
- Temporarily test: disable LLM keys, submit one answer, verify:
  - evaluation_log shows `evaluation_mode: "degraded"`
  - Telegram alert fires (if spike threshold hit, or manually test alert)
  - Re-enable keys, verify reeval_worker rescores the answer

---

## Acceptance Criteria

```
AC-1: ZERO orphaned sessions (completed + no AURA score)
  Given: SELECT ... WHERE status='completed' AND a.volunteer_id IS NULL
  Then: count = 0

AC-2: Sentry receives events from production
  Given: sentry_sdk.capture_message('test') from Railway
  Then: event visible in Sentry within 60 seconds

AC-3: Playwright E2E test passes in CI
  Given: npx playwright test tests/e2e/full-journey.spec.ts
  Then: test passes, AURA score created, public profile loads

AC-4: 3+ competencies have completed sessions with AURA scores
  Given: SELECT DISTINCT c.slug FROM assessment_sessions s JOIN ... WHERE status='completed' AND a.volunteer_id IS NOT NULL
  Then: at least 3 distinct slugs

AC-5: Degraded mode is visible and recoverable
  Given: LLM failure triggers keyword_fallback
  Then: Telegram alert fires AND reeval_worker rescores within 60s
```

---

## Files to Touch

- `apps/api/app/routers/assessment.py` — retry logic in /complete
- `tests/e2e/full-journey.spec.ts` — NEW
- `.github/workflows/e2e.yml` — NEW
- Sentry dashboard — alert rule config
- Railway — verify env vars + worker process

---

## What Cowork Already Did

- Full audit report: `docs/audits/ASSESSMENT-ENGINE-AUDIT-2026-04-13.md`
- Beta readiness checklist: `docs/BETA-READINESS-CHECKLIST.md`
- Verified DB: 101 questions, all IRT params valid, 0 out-of-range
- Verified AURA math: DB functions match code, manual calc matches
- Confirmed: CV processing and JD alignment don't exist (by design, not a bug)
- Confirmed: anti-gaming is catching real patterns in production

---

## Risk

Without these 5 gates, first beta users will:
- Complete assessment, see no score → lose trust permanently
- Hit errors nobody notices → silent reputation damage
- Find one competency works, others don't → "this is half-baked"

CEO is right. Ship nothing until this passes.
