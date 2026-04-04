# QA Coordinator Checklist — Parallel Test Execution

**Role:** QA Lead / CTO (orchestrates parallel test execution)
**Duration:** ~50 minutes total (including setup, execution monitoring, aggregation)

---

## 17:00 — PRE-EXECUTION (10 min)

- [ ] **Verify environment:**
  ```bash
  bash scripts/test_execution_checklist.sh
  ```
  - API responding ✓
  - Frontend accessible ✓
  - Test user created ✓
  - test_results/ directory ready ✓

- [ ] **Create team assignment spreadsheet:**
  | Team | Phase | Start Time | Status | Owner | ETA |
  |------|-------|-----------|--------|-------|-----|
  | Auth | 1a | 17:01 | pending | ... | 17:11 |
  | API | 1b | 17:01 | pending | ... | 17:11 |
  | Profile/AURA | 2a | 17:11 | pending | ... | 17:16 |
  | ... | ... | ... | ... | ... | ... |

- [ ] **Send team notifications:**
  ```
  @channel: Functional test execution begins in 1 min
  • Read: docs/FUNCTIONAL-TEST-STRATEGY.md (Part 2)
  • Read: docs/TEST-TEAM-HANDOFF.md (your section)
  • Source env: source test_results/env.sh
  • Announce readiness: "{Team} ready for {Phase}"
  ```

- [ ] **Set up result monitoring:**
  ```bash
  # Watch for test_results/*.json files
  ls -la test_results/
  ```

---

## 17:01 — PHASE 1a + 1b EXECUTION (10 min)

**Auth Team + API Infrastructure Team execute in PARALLEL**

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Email signup → login | Auth | ⏳ | Monitor for CORS errors |
| Google OAuth callback | Auth | ⏳ | Check apiFetch token injection |
| Response envelope | API | ⏳ | Sample 5+ endpoints |
| CORS headers present | API | ⏳ | CRITICAL BLOCKER if missing |
| Error format | API | ⏳ | Should be `{code, message}` |

**Coordinator Actions:**
- [ ] Start timer (10 min)
- [ ] Monitor Slack for team status updates
- [ ] **If CORS errors appear:** Document immediately (likely blocker for Phase 2)
- [ ] **If 401 errors:** Alert Auth team (token injection issue)
- [ ] At 17:10: Remind teams to submit results to test_results/

**Expected Results Files:**
- `test_results/auth-team.json`
- `test_results/api-team.json`

**Go/No-Go Decision at 17:11:**
- ✓ Auth + API pass → proceed to Phase 2
- ✗ CORS blocker → cannot proceed to Phase 2 (most endpoints will fail)
- ✗ Auth blocker → cannot proceed (no logged-in session for Phase 2)

---

## 17:11 — PHASE 2a-2i EXECUTION (15 min)

**All 9 domain teams execute SIMULTANEOUSLY**

| Team | Endpoint | Start | ETA | Status |
|------|----------|-------|-----|--------|
| Profile/AURA | /profiles/me, /aura/me | 17:11 | 17:16 | ⏳ |
| Assessment | /assessment/sessions, questions | 17:11 | 17:26 | ⏳ |
| Events | /events, /attend, /checkin | 17:11 | 17:16 | ⏳ |
| Tribes | /tribes/me, /leaderboard | 17:11 | 17:16 | ⏳ |
| Skills | /skills | 17:11 | 17:14 | ⏳ |
| Notifications | /notifications/* | 17:11 | 17:16 | ⏳ |
| Analytics | /analytics/event, stats | 17:11 | 17:16 | ⏳ |
| BrandedBy | /brandedby/twins, /generations | 17:11 | 17:16 | ⏳ |
| Payments | /subscription/status | 17:11 | 17:14 | ⏳ |

**Coordinator Actions:**
- [ ] Start Phase 2 timer (15 min)
- [ ] Monitor Slack channels for team updates
- [ ] **Watch for common failures:**
  - CORS errors (indicates Phase 1b issue not resolved)
  - 401 errors (indicates Phase 1a issue not resolved)
  - 422 errors (likely request format issue, ask team to verify body)
  - 500 errors (server error, check Sentry)
  - Timeouts (database slow, escalate to backend)

- [ ] **If blocker found:** Decide: proceed anyway (mark as failure) OR wait for fix
  - Generally: Document and move on (aggregate phase will show impact)
  - Only pause if it blocks multiple teams (e.g., shared dependency)

- [ ] At 17:25: "Phase 2 wrapping up, expect results submission by 17:26"

**Expected Results Files (9 total):**
- `test_results/profile-aura-team.json`
- `test_results/assessment-team.json`
- `test_results/events-team.json`
- `test_results/tribes-team.json`
- `test_results/skills-team.json`
- `test_results/notifications-team.json`
- `test_results/analytics-team.json`
- `test_results/brandedby-team.json`
- `test_results/payments-team.json`

---

## 17:25 — PHASE 3 EXECUTION (10 min)

**Frontend Team + UI Visual Checks**

| Task | Status | Notes |
|------|--------|-------|
| Landing page load (<3s) | ⏳ | Check screenshot |
| Dashboard load + render | ⏳ | Verify no CORS errors in console |
| Assessment page | ⏳ | Check question renders |
| Mobile responsive (375px) | ⏳ | Verify layout not broken |
| Console errors | ⏳ | Count per page (target: <5) |

**Coordinator Actions:**
- [ ] Start Phase 3 timer (10 min)
- [ ] **If Phase 2 still running:** Start Phase 3 anyway (parallel)
- [ ] Monitor for console errors (Frontend team will report)
- [ ] At 17:34: "Phase 3 wrapping up"

**Expected Results File:**
- `test_results/frontend-team.json`

---

## 17:35 — PHASE 4 EXECUTION (5 min)

**Admin Team**

| Task | Status | Notes |
|------|--------|-------|
| Admin auth (not 403) | ⏳ | Requires is_platform_admin=true |
| Swarm agents endpoint | ⏳ | Should return agent list |
| Proposals endpoint | ⏳ | Should return proposals (may be empty) |

**Coordinator Actions:**
- [ ] Start Phase 4 timer (5 min)
- [ ] **Quick note:** If admin tests fail, likely not critical path (Phase 2 is priority)
- [ ] At 17:39: "Admin tests wrapping up"

**Expected Results File:**
- `test_results/admin-team.json`

---

## 17:40 — AGGREGATION (5 min)

**Coordinator's Turn**

### Step 1: Verify all results files present

```bash
ls -la test_results/*.json | grep -v AGGREGATED
# Should have ~13 files (1 auth + 1 API + 9 domain + 1 frontend + 1 admin)
```

Missing files? Slack: "@{Team}: Please submit test_results/{team}-team.json"

### Step 2: Run aggregation script

```bash
python3 scripts/aggregate_test_results.py test_results
```

This produces:
- `test_results/AGGREGATED_REPORT.json` (machine-readable)
- `test_results/AGGREGATED_REPORT.html` (human-readable)

### Step 3: Review summary

```bash
cat test_results/AGGREGATED_REPORT.json | jq '.summary'
```

Expected output:
```json
{
  "total_tests": 45,
  "passed": 44,
  "failed": 1,
  "pass_rate": "97.8%",
  "teams_reporting": 13
}
```

---

## 17:45 — REPORT & TRIAGE (5 min)

### Communicate Results

**Slack announcement:**
```
📊 Functional Test Report Ready

✅ Overall Status: [PASS/FAIL]
📈 Total Tests: {N}
✓ Passed: {N} ({pass_rate}%)
✗ Failed: {N}

🔗 Full report: [link to AGGREGATED_REPORT.html]

Next steps:
{next_steps from aggregation}
```

### Critical Failures → Triage

If `overall_status == "FAIL"`:

**Step 1: Categorize failures**
```bash
cat test_results/AGGREGATED_REPORT.json | jq '.failure_details'
```

| Failure | Team | Root Cause | Severity | Owner |
|---------|------|-----------|----------|-------|
| CORS error | API | Missing Access-Control-Allow-Origin | CRITICAL | Backend |
| 401 on /profiles/me | Auth | Token not injected | CRITICAL | Frontend |
| AURA not updating | Profile/AURA | Logic error | HIGH | Backend |
| Mobile layout broken | Frontend | CSS issue | MEDIUM | Frontend |

**Step 2: Assign to owners**
- CRITICAL failures → pause, escalate to CTO
- HIGH failures → schedule fix in next 30 min
- MEDIUM failures → log for post-launch

**Step 3: Decide: Ship or Hold?**

| Status | Decision | Action |
|--------|----------|--------|
| 0 failures | 🚀 SHIP | Proceed to manual walkthrough |
| 1-2 CRITICAL | ⏹️ HOLD | Fix critical issues, re-test |
| 3+ CRITICAL | 🔴 ABORT | Too risky, needs deeper debugging |
| MEDIUM/LOW only | 🚀 SHIP | Log issues, fix post-launch |

**Example decision:**
```
Result: 44/45 tests pass (97.8%)
Critical failures: 0
High failures: 1 (AURA not updating after assessment)

Decision: SHIP with known issue
Reason: AURA calculation is non-blocking; core flows (auth, assessment, profiles) all pass
Post-launch fix: Schedule AURA calculation fix for Session 86
```

---

## 17:50 — HANDOFF TO CEO

**One-liner summary:**
```
E2E audit complete: 44/45 tests pass. CORS + auth working. Assessment flow verified.
Ready for CEO walkthrough.
```

**Include:**
- ✅ What's working (critical path: auth, assessment, profiles)
- ⚠️ What's not working (non-critical: AURA calculation pending)
- 🎯 Launch gate status (PASS/FAIL)

---

## After Aggregation — If Failures Found

### Re-Test Cycle (30-60 min)

1. **Document fixes needed** (from AGGREGATED_REPORT.json)
2. **Backend team fixes code** (e.g., CORS headers, AURA logic)
3. **Deploy to production** (one batch commit, not per-issue)
4. **Verify deployment** (check Railway logs, Vercel build status)
5. **Re-run affected tests only** (not full audit)
   ```bash
   # E.g., if CORS fixed, retest: curl api/profiles/me
   ```
6. **Update results** (update auth-team.json CORS test to PASS)
7. **Re-run aggregation** (python3 scripts/aggregate_test_results.py)
8. **Report new status** (Slack update)

---

## Escalation Paths

| Issue | Escalate To | Action |
|-------|-------------|--------|
| CORS errors persist | Backend + Infra | Check Railway config, Vercel rewrites |
| 5xx errors in API | Backend | Check Sentry logs, recent commits |
| Auth token issues | Frontend | Check apiFetch interceptor, session storage |
| Database timeout | Backend | Check query performance, add indexes |
| Playwright errors | Frontend | Check Chrome version, network issues |
| > 5 failures in one team | CTO | May indicate architectural issue, needs deep review |

---

## Success Criteria (Go/No-Go for CEO Walkthrough)

| Metric | Threshold | Status |
|--------|-----------|--------|
| **Overall Pass Rate** | ≥ 90% | ✅ |
| **Critical Path Tests** | 100% | ✅ |
| **CORS headers present** | All /api/* | ✅ |
| **Auth flows working** | Email + OAuth | ✅ |
| **Session persistence** | No 401 after login | ✅ |
| **Assessment flow** | Create → submit → score | ✅ |
| **Console errors** | < 5 per page | ✅ |
| **Response time** | < 1s avg | ✅ |

**Decision logic:**
```
if (overall_pass_rate >= 90% AND critical_path_100% AND cors_present):
  status = "READY_FOR_WALKTHROUGH"
else:
  status = "NEEDS_FIXES"
```

---

## Post-Execution Cleanup

After CEO signs off (or issues identified):

- [ ] Archive test results
  ```bash
  mkdir -p archive/session85
  cp test_results/*.json archive/session85/
  ```

- [ ] Update sprint-state.md with E2E results
  ```
  ## Session 85 E2E Audit (Date)
  - Status: PASS (44/45 tests)
  - Timeline: ~45 min
  - Known issues: [list]
  - Ship decision: [PASS/HOLD]
  ```

- [ ] Retrospective (if issues found)
  ```
  What failed: CORS headers
  Why: Railway middleware not deployed
  Fix: Commit e4a40cb + 06c36fc merged, re-deployed
  Prevention: Add CORS check to pre-deployment checklist
  ```

---

## Coordinator Quick-Reference Commands

```bash
# Check if all teams submitted results
ls -1 test_results/*.json | wc -l  # Should be ~13

# Aggregate all results
python3 scripts/aggregate_test_results.py test_results

# View summary
jq '.summary' test_results/AGGREGATED_REPORT.json

# View failures only
jq '.failure_details' test_results/AGGREGATED_REPORT.json

# Open HTML report
open test_results/AGGREGATED_REPORT.html

# Count failures by severity
jq '.critical_blockers | map(.severity) | group_by(.) | map({severity: .[0], count: length})' test_results/AGGREGATED_REPORT.json
```

---

## Timeline Summary

```
17:00 ┌─ Pre-Execution (setup, team notifications)
      │
17:01 ├─ Phase 1a + 1b (Auth + API, parallel, 10 min)
      │  └─ Gate: CORS + auth working?
      │
17:11 ├─ Phase 2a-2i (9 domain teams, parallel, 15 min)
      │  └─ Gate: Critical flows working?
      │
17:25 ├─ Phase 3 (Frontend, 10 min)
      │  └─ Gate: Pages load, no console errors?
      │
17:35 ├─ Phase 4 (Admin, 5 min)
      │
17:40 ├─ Aggregation (5 min)
      │  └─ Produce AGGREGATED_REPORT.json + .html
      │
17:45 ├─ Triage & Decision (5 min)
      │  └─ PASS → Ship, FAIL → Fix & Re-test
      │
17:50 └─ Handoff to CEO (1-liner summary)
```

**Total: ~50 minutes**

---

## Template: Escalation Message to CTO

If you find a blocker you can't resolve:

```
Coordinator: {CTO}, we have a blocker in {Phase}

Issue: {Description}
Impact: {How many tests affected}
Expected vs Actual: {Specific failure}
Teams waiting: {Which teams blocked}

Can you {action}?
- Check {service} logs?
- Re-deploy {component}?
- Clarify {requirement}?

Timeline: Need decision by 17:{time}
```

---

**Last Updated:** 2026-04-04
**Version:** 1.0 — Ready for Execution
