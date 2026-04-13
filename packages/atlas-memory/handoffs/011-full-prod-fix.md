# Handoff 011 — Production Fix & Beta Gate Closure (P0)

**From:** Cowork Session 9 (continued) | **To:** Atlas
**Date:** 2026-04-13 | **Priority:** P0 — ALL GATES RED, PROD API DOWN
**CEO directive:** "снова проведи все тесты... всё готовы деплоить?"
**Answer:** НЕТ. 0 из 5 гейтов PASS. Production API не отвечает.

---

## Full Audit Results (2026-04-13, live queries)

| Metric | Value |
|--------|-------|
| Production API | **DOWN** — HTTP 000 (connection reset) |
| Users (auth.users) | 39 |
| Profiles | 27 |
| Total sessions | 20 |
| Completed sessions | 13 |
| AURA scores | 8 |
| Orphan sessions (completed, no AURA) | **5** |
| Sentry events (30 days) | **0** |
| character_events | 10 |
| Competencies with sessions | 2 of 8 (communication: 12, reliability: 1) |
| E2E test runs | **0** (file exists, never ran) |

### Question Bank
| Competency | Questions | Enough for CAT? |
|-----------|-----------|-----------------|
| tech_literacy | 15 | Yes |
| communication | 15 | Yes |
| adaptability | 15 | Yes |
| event_performance | 15 | Yes |
| empathy_safeguarding | 11 | NO (need 15) |
| reliability | 10 | NO (need 15) |
| english_proficiency | 10 | NO (need 15) |
| leadership | 10 | NO (need 15) |

### Constitution Violations (Frontend)
| Law | Violation | File | Fix |
|-----|-----------|------|-----|
| Law 3 (Shame-free) | "haven't completed their assessment yet" | `apps/web/src/app/[locale]/(dashboard)/org-volunteers/page.tsx:533` | Rewrite to "Assessment in progress" or "Awaiting assessment" |
| Law 4 (Animation ≤800ms) | `duration = 2000` | `apps/web/src/components/landing/impact-ticker.tsx:15` | Reduce to 800 |
| Law 4 (Animation ≤800ms) | `animationDuration={1200}` | `apps/web/src/components/aura/radar-chart.tsx:106` | Reduce to 800 |
| Law 4 (Animation ≤800ms) | `duration = 1200` | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx:28` | Reduce to 800 |

---

## Tasks — Priority Order (do them in this exact sequence)

### Task 0: REVIVE PRODUCTION API
**This blocks everything. Nothing else matters until API responds.**

- Check Railway dashboard: is the service running? Check deploy logs.
- If crashed: check `railway logs` for the last error. Common causes: OOM, env var missing, dependency crash.
- If sleeping: Railway free tier pauses after inactivity. Redeploy or upgrade plan.
- Verify: `curl https://volauraapi-production.up.railway.app/health` returns `{"status":"ok"}`
- If Railway is fundamentally broken, escalate to CEO immediately.

### Task 1: Recovery — Fix 5 Orphan AURA Scores (Gate 1)
**Retry logic already exists (commit d215c4b). Recovery script never ran.**

- Run `scripts/recover_lost_aura.py` against production Supabase
- If script doesn't exist or fails, manually recover:
  ```sql
  -- Find orphaned sessions
  SELECT s.id, s.volunteer_id, s.competency_id, s.metadata
  FROM assessment_sessions s
  LEFT JOIN aura_scores a ON s.volunteer_id = a.volunteer_id
  WHERE s.status = 'completed' AND a.volunteer_id IS NULL;
  
  -- For each: call upsert_aura_score RPC with the session's competency score
  ```
- Verify: query returns 0 orphans after recovery
- AC: `SELECT COUNT(*) ... WHERE status='completed' AND a.volunteer_id IS NULL` = 0

### Task 2: Resurrect Sentry (Gate 2)
**0 events in 30 days. Sentry is completely dead.**

- Check Railway env: `SENTRY_DSN` — does it match the Volaura project (not MindShift)?
- Use Sentry MCP to find correct DSN: `find_dsns(organizationSlug='volaura')`
- From Railway shell, test: `python -c "import sentry_sdk; sentry_sdk.init('CORRECT_DSN'); sentry_sdk.capture_message('atlas-011-test')"`
- Create alert rule in Sentry: any new issue → Telegram webhook
- AC: test event visible in Sentry within 60 seconds

### Task 3: Run E2E Test (Gate 3)
**File exists at `tests/e2e/full-journey.spec.ts`. CI at `.github/workflows/e2e.yml`. Never executed.**

- Install Playwright: `npx playwright install`
- Set test env vars (NEXT_PUBLIC_SUPABASE_URL, API_URL, test user credentials)
- Run: `npx playwright test tests/e2e/full-journey.spec.ts`
- If tests fail: fix them. The test must actually pass, not just exist.
- Push fix + verify GitHub Actions workflow triggers on push
- AC: `npx playwright test` exits 0 with all specs green

### Task 4: Test 3rd Competency E2E (Gate 4)
**Only communication (12 sessions) and reliability (1 session) have been tested. Need 3+.**

- Pick competencies with 15 questions: tech_literacy, adaptability, or event_performance
- Run a full assessment for at least ONE of those (via E2E test or manual API calls)
- Verify AURA recalculates with the new competency
- AC: `SELECT DISTINCT c.slug FROM assessment_sessions s JOIN competencies c ON ... JOIN aura_scores a ON ... WHERE s.status='completed'` returns ≥ 3 slugs

### Task 5: Verify Degraded Mode (Gate 5)
**reeval_worker.py exists. Never tested on production.**

- Confirm reeval_worker is running as a background task in Railway
- If not running: it starts with the FastAPI app in `main.py` — check if `asyncio.create_task(start_reeval_worker())` is there
- Test: temporarily set invalid LLM key, submit one answer, verify:
  - `evaluation_queue` table shows entry with status='pending'
  - Telegram alert fires (if spike threshold hit)
  - Restore keys → reeval_worker picks up and rescores within 60s
- AC: degraded answer is replaced by proper LLM score within 60 seconds

### Task 6: Fix Constitution Violations (Frontend)
**4 violations found. All are simple one-line fixes.**

1. `apps/web/src/app/[locale]/(dashboard)/org-volunteers/page.tsx:533`
   - Change: "Professionals have been assigned but haven't completed their assessment yet."
   - To: "Professionals have been assigned — assessment in progress."

2. `apps/web/src/components/landing/impact-ticker.tsx:15`
   - Change: `duration = 2000`
   - To: `duration = 800`

3. `apps/web/src/components/aura/radar-chart.tsx:106`
   - Change: `animationDuration={1200}`
   - To: `animationDuration={800}`

4. `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx:28`
   - Change: `duration = 1200`
   - To: `duration = 800`

Also check line 267 of aura/page.tsx: `5000` ms delay references "counter animation (2000ms)" — update comment to match new 800ms duration.

- AC: `grep -rn "duration.*[0-9]\{4,\}" apps/web/src/` returns 0 non-decorative animations > 800ms
- AC: `grep -rn "haven't" apps/web/src/` returns 0 shame-language results

### Task 7: Add Questions to Underpopulated Competencies
**4 competencies have < 15 questions. CAT needs 15+ for convergence.**

| Competency | Current | Need |
|-----------|---------|------|
| empathy_safeguarding | 11 | +4 |
| reliability | 10 | +5 |
| english_proficiency | 10 | +5 |
| leadership | 10 | +5 |

- Generate questions using the existing format in `supabase/seed.sql`
- Each question needs: text, competency_id, question_type, options (MCQ or open_ended), IRT params (a, b, c)
- IRT param ranges: a ∈ [0.8, 2.5], b ∈ [-2.0, 2.0], c ∈ [0.15, 0.25]
- Insert via migration: `supabase/migrations/YYYYMMDDHHMMSS_add_questions_batch2.sql`
- AC: `SELECT c.slug, COUNT(q.id) FROM competencies c JOIN questions q ON ... GROUP BY c.slug` → all ≥ 15

---

## Acceptance Criteria Summary

```
AC-0: curl https://volauraapi-production.up.railway.app/health → {"status":"ok"}
AC-1: 0 orphaned sessions (completed + no AURA)
AC-2: Sentry test event visible within 60 seconds
AC-3: npx playwright test exits 0
AC-4: ≥ 3 competencies with completed sessions + AURA scores
AC-5: Degraded answer rescored by reeval_worker within 60s
AC-6: 0 Constitution violations in frontend (shame language + animation > 800ms)
AC-7: All 8 competencies have ≥ 15 questions
```

**Beta launch: BLOCKED until AC-0 through AC-6 are PASS.**
AC-7 is P1 (needed before opening all 8 competencies, but 4 already have 15).

---

## What Cowork Already Did (don't repeat this work)

- Full audit: `docs/audits/ASSESSMENT-ENGINE-AUDIT-2026-04-13.md`
- Architecture research: `docs/research/ASSESSMENT-ARCHITECTURE-RESEARCH-2026-04-13.md`
- Ecosystem events service: `apps/api/app/services/ecosystem_events.py` (3 events wired into /complete)
- character_events table: exists, 10 events already recorded
- Retry logic in /complete: exists (commit d215c4b)
- E2E test file: exists (commit d215c4b) — just never ran
- Beta checklist: `docs/BETA-READINESS-CHECKLIST.md`

---

## Risk if Skipped

Users will:
1. See a dead API (right now, production doesn't respond)
2. Complete assessment, get no score (5 already lost)
3. Hit errors nobody sees (Sentry dead for 30+ days)
4. Find 6 of 8 competencies untested
5. See janky 2-second animations on a mobile connection

CEO will kill the beta. And he'll be right.
