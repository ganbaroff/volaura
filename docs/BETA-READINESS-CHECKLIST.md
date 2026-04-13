# Beta Readiness Checklist

**Created:** 2026-04-13 | **Authority:** CEO directive  
**Rule:** NO external users until ALL gates are PASS. Zero exceptions.

---

## Gate 1: Zero Data Loss
**Status:** 🟡 CODE FIXED — needs prod verification

| Check | Method | Result |
|-------|--------|--------|
| Every completed session has AURA score | SQL query | 5 orphans (pre-fix). Recovery script ready. |
| `upsert_aura_score` RPC retry on failure | Code review | ✅ ADDED: retry once after 2s (commit d215c4b) |
| Recovery script works | Run `scripts/recover_lost_aura.py` | READY — needs Supabase SDK on Railway |
| `pending_aura_sync` flag catches future failures | Code review | ✅ EXISTS + now only set after retry exhausted |

**PASS when:** Query returns 0 orphans. Recovery script has run. New assessment produces AURA score 100% of the time.

---

## Gate 2: Error Visibility (Sentry)
**Status:** 🔴 FAIL

| Check | Method | Result |
|-------|--------|--------|
| Sentry receives events from Railway | Send test event from prod | 0 events in 30 days |
| DSN matches prod project | Compare .env DSN vs Sentry dashboard | UNVERIFIED |
| Alert rules configured | Sentry MCP: check alert config | NO ALERTS |
| Telegram gets Sentry alerts | Trigger error → check Telegram | UNTESTED |

**PASS when:** Deliberately triggered error appears in Sentry within 60 seconds. Alert reaches Telegram.

---

## Gate 3: E2E Automated Test
**Status:** 🟡 WRITTEN — needs first run

| Check | Method | Result |
|-------|--------|--------|
| Playwright test: signup → assessment → AURA | `npx playwright test` | ✅ CREATED: tests/e2e/full-journey.spec.ts (commit d215c4b) |
| Test covers: pick competency → answer all → see score | Code inspection | ✅ 4 tests: health, signup, assessment loop, AURA verify |
| Test runs in CI on every push | `.github/workflows/e2e.yml` | ✅ CREATED (commit d215c4b) |
| Public profile shows badge after assessment | Test assertion | NOT YET (needs frontend route test) |

**PASS when:** `npx playwright test` runs green. CI blocks merge if it fails.

---

## Gate 4: 3+ Competencies Work End-to-End
**Status:** 🟡 PARTIAL

| Check | Method | Result |
|-------|--------|--------|
| Communication has enough questions for CAT convergence | DB: count questions where competency=communication | 15 MCQ + (open_ended TBD) |
| Reliability works end-to-end | DB: at least 1 completed session with AURA | ✅ 1 user |
| Leadership works end-to-end | DB: at least 1 completed session with AURA | ❌ 0 sessions |
| Each competency has ≥15 questions | DB query per competency | 4 of 8 have ≥15 |

**PASS when:** At least 3 competencies have been tested by automated E2E test, each producing valid AURA scores.

---

## Gate 5: Degraded Mode Alerting
**Status:** 🟡 PARTIAL

| Check | Method | Result |
|-------|--------|--------|
| keyword_fallback spike → Telegram alert | Code review of bars.py | CODE EXISTS (threshold=10/hr) |
| Alert actually fires in production | Trigger fallback spike | UNTESTED |
| Degraded answers auto-reeval within 60s | Code review of reeval_worker | CODE EXISTS |
| reeval_worker running on Railway | Check Railway processes | UNVERIFIED |

**PASS when:** Simulated LLM failure triggers Telegram alert. Degraded score is replaced by LLM score within 60 seconds.

---

## Summary

| Gate | Status | Owner |
|------|--------|-------|
| 1. Zero Data Loss | 🟡 CODE FIXED | Atlas — retry logic added, recovery script ready |
| 2. Error Visibility | 🔴 FAIL | Atlas — needs Railway test event |
| 3. E2E Automated Test | 🟡 WRITTEN | Atlas — Playwright + CI created, needs first run |
| 4. 3+ Competencies | 🟡 PARTIAL | Atlas (question bank + test) |
| 5. Degraded Alerting | 🟡 PARTIAL | Atlas (verify on Railway) |

**Beta launch: BLOCKED until 5/5 gates are PASS.**

---

## How to Verify (for Atlas)

```bash
# Gate 1: Run after recovery
SELECT COUNT(*) FROM assessment_sessions s 
LEFT JOIN aura_scores a ON s.volunteer_id = a.volunteer_id 
WHERE s.status = 'completed' AND a.volunteer_id IS NULL;
-- Must return 0

# Gate 2: Send test event
python -c "import sentry_sdk; sentry_sdk.init('DSN'); sentry_sdk.capture_message('test')"
-- Must appear in Sentry dashboard

# Gate 3: Run E2E
npx playwright test tests/e2e/full-journey.spec.ts
-- Must pass

# Gate 4: Verify 3 competencies
SELECT c.slug, COUNT(DISTINCT s.volunteer_id) as users_with_score
FROM assessment_sessions s
JOIN competencies c ON s.competency_id = c.id
JOIN aura_scores a ON s.volunteer_id = a.volunteer_id
WHERE s.status = 'completed'
GROUP BY c.slug;
-- At least 3 slugs with users_with_score > 0

# Gate 5: Check reeval worker
# On Railway: verify worker process is running
# Trigger: temporarily disable all LLM API keys, submit answer, check Telegram
```
