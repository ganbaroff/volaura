# Functional Test Execution — Team Handoff Guide

**Document Version:** 1.0
**Date:** 2026-04-04
**Purpose:** Instructions for each team to execute their testing phase autonomously

---

## Overview

Instead of manual clicking, we're running **parallel functional tests by domain**. Each team tests their own surface, reports results, we aggregate, and fix all issues in one batch.

**Timeline:** ~45 minutes to run all tests (8-10 people working simultaneously)
**Read first:** `/docs/FUNCTIONAL-TEST-STRATEGY.md` (Part 1: Decomposition, Part 2: Parallel Model)

---

## Your Role — Pick Your Phase

Find your team in the table below. Go to that section.

| Team | Phase | Endpoints | Duration | Status |
|------|-------|-----------|----------|--------|
| **Auth** | 1a | /auth/signup, /auth/login, /auth/logout, session | 10 min | → See Section A |
| **API Infrastructure** | 1b | Response envelope, CORS, errors, rate limits | 10 min | → See Section B |
| **Profile/AURA** | 2a | /profiles/me, /aura/me, badges, visibility | 5 min | → See Section C |
| **Assessment** | 2b | /assessment/sessions, questions, answers, IRT | 15 min | → See Section D |
| **Events** | 2c | /events, /attend, /checkin, attendance | 5 min | → See Section E |
| **Tribes** | 2d | /tribes/me, /leaderboard, stats | 5 min | → See Section F |
| **Skills** | 2e | /skills, weights, competencies | 3 min | → See Section G |
| **Notifications** | 2f | /notifications/*, unread count, real-time | 5 min | → See Section H |
| **Analytics** | 2g | /analytics/event, activity feed, stats | 5 min | → See Section I |
| **BrandedBy** | 2h | /brandedby/twins, /generations | 5 min | → See Section J |
| **Payments** | 2i | /subscription/status, invoices | 3 min | → See Section K |
| **Frontend** | 3 | Page load, rendering, console errors | 10 min | → See Section L |
| **Admin** | 4 | /admin/swarm/*, access control | 5 min | → See Section M |

---

## Pre-Test Setup (Everyone — 5 min)

Before your phase runs:

1. **Run the checklist script:**
   ```bash
   bash scripts/test_execution_checklist.sh
   ```
   This verifies API is up, creates test user, and populates `test_results/env.sh`

2. **Source the environment:**
   ```bash
   source test_results/env.sh  # Loads SESSION_TOKEN
   ```

3. **Verify test results directory:**
   ```bash
   ls -la test_results/  # Should have cookies.txt, test_user.json
   ```

4. **Announce readiness:** Slack #volaura-dev: "Auth team ready for Phase 1a"

---

## Phase 1a: AUTH TEAM (10 min)

**Owner:** Auth team lead
**Deliverable:** `test_results/auth-team.json`

### What You Test

1. **Email Signup**
   - Endpoint: `POST /api/auth/signup`
   - Test: Create new user account
   - Expected: `201 + user.id`

   ```bash
   curl -X POST https://volaura.app/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test_'$(date +%s)'@example.com",
       "password": "TestPass123!",
       "username": "testuser_'$(date +%s)'"
     }' | jq .
   ```

2. **Email Login**
   - Endpoint: `POST /api/auth/login`
   - Test: Log in with email + password
   - Expected: `200 + session.access_token + cookie set`

   ```bash
   curl -X POST https://volaura.app/api/auth/login \
     -H "Content-Type: application/json" \
     -c test_results/cookies_auth.txt \
     -d '{
       "email": "test@example.com",
       "password": "TestPass123!"
     }' | jq .
   ```

3. **Google OAuth Callback**
   - Test: User completes OAuth flow, lands on /callback
   - Expected: `apiFetch auto-injects token, session cookie set`
   - Manual test: Click "Login with Google" → choose account → confirm on /callback page
   - Check: Browser console should show NO errors, session should persist

4. **Session Persistence**
   - Test: Load page after login, verify session still active
   - Expected: `/api/profiles/me` returns `200 (not 401)`

   ```bash
   curl -b test_results/cookies.txt https://volaura.app/api/profiles/me | jq .
   ```

5. **Token Refresh**
   - Test: Make request, verify token auto-refreshed if expired
   - Expected: No 401 errors during session, interceptor handles refresh

6. **Logout**
   - Endpoint: `POST /api/auth/logout`
   - Test: Log out user
   - Expected: `200 + session cookie deleted`
   - Verify: `/api/profiles/me` returns `401`

7. **CORS Headers on Auth Endpoints**
   - Test: Check response headers
   - Expected: All responses include `Access-Control-Allow-Origin`

   ```bash
   curl -i https://volaura.app/api/auth/login | grep "Access-Control"
   ```

### Submit Results

Create file: `test_results/auth-team.json`

```json
{
  "team": "Auth",
  "phase": "1a",
  "status": "PASS",
  "summary": "All auth flows working. OAuth redirect working but auto-injection needs verification.",
  "tests": [
    {
      "name": "Email signup",
      "status": "PASS",
      "endpoint": "POST /api/auth/signup",
      "expected": "201 + user.id",
      "actual": "201 + user_id = abc123",
      "duration_ms": 234
    },
    {
      "name": "Email login",
      "status": "PASS",
      "endpoint": "POST /api/auth/login",
      "expected": "200 + access_token",
      "actual": "200 + token obtained",
      "duration_ms": 156
    },
    {
      "name": "Session persistence",
      "status": "PASS",
      "endpoint": "GET /api/profiles/me",
      "expected": "200",
      "actual": "200",
      "duration_ms": 89
    }
  ],
  "failures": 0,
  "blockers": [],
  "warnings": ["Google OAuth requires manual browser test"],
  "timestamp": "2026-04-04T17:05:00Z"
}
```

---

## Phase 1b: API INFRASTRUCTURE TEAM (10 min)

**Owner:** API team lead
**Deliverable:** `test_results/api-team.json`

### What You Test

1. **Response Envelope Format**
   - Test: All endpoints should return `{ data, meta }`
   - Sample endpoints: /health, /skills, /events, /profiles/me
   - Expected: Every response has `data` and `meta` fields

   ```bash
   curl -s https://volaura.app/api/health | jq 'keys'
   # Should output: ["data", "meta"]
   ```

2. **CORS Headers Present**
   - Test: Response headers include `Access-Control-Allow-Origin`
   - Test ALL endpoints (health, public, protected)
   - Expected: Every endpoint has CORS header

   ```bash
   curl -i -b test_results/cookies.txt \
     https://volaura.app/api/profiles/me | grep "Access-Control"
   ```

3. **Error Response Format**
   - Test: Trigger 404, 422, 500 errors
   - Expected: All errors return `{ code, message }` (not raw stack traces)

   ```bash
   curl -b test_results/cookies.txt \
     https://volaura.app/api/profiles/nonexistent | jq '.'
   # Should show: { "message": "Profile not found", "code": "PROFILE_NOT_FOUND" }
   ```

4. **HTTP Status Codes**
   - Test: Verify correct status per operation
   - POST create → 201, GET → 200, PUT → 200, DELETE → 204
   - Expected: Status codes match REST conventions

5. **Rate Limiting**
   - Test: Send 50+ requests in quick succession
   - Expected: After limit, 429 Too Many Requests

   ```bash
   for i in {1..50}; do
     curl -s https://volaura.app/api/health > /dev/null
   done
   # Last request should be 429
   ```

6. **Content-Type**
   - Test: All JSON endpoints return `application/json`
   - Expected: No `text/html` or `text/plain` on /api/*

### Submit Results

Create file: `test_results/api-team.json`

```json
{
  "team": "API Infrastructure",
  "phase": "1b",
  "status": "FAIL",
  "summary": "CORS headers missing on most endpoints. Response envelope correct. Errors properly formatted.",
  "tests": [
    {
      "name": "Response envelope /api/health",
      "status": "PASS",
      "endpoint": "GET /api/health",
      "expected": "Response has data and meta fields",
      "actual": "{ data: {...}, meta: {...} }",
      "duration_ms": 45
    },
    {
      "name": "CORS headers on /api/profiles/me",
      "status": "FAIL",
      "endpoint": "GET /api/profiles/me",
      "expected": "Access-Control-Allow-Origin header present",
      "actual": "Header missing",
      "duration_ms": 0,
      "root_cause": "Railway CORS middleware not deployed"
    }
  ],
  "failures": 1,
  "blockers": ["CORS headers missing on protected endpoints"],
  "warnings": [],
  "timestamp": "2026-04-04T17:05:00Z"
}
```

---

## Phase 2a: PROFILE/AURA TEAM (5 min)

**Owner:** Profile team lead
**Deliverable:** `test_results/profile-aura-team.json`

### What You Test

1. **Get Own Profile**
   ```bash
   curl -s -b test_results/cookies.txt https://volaura.app/api/profiles/me | jq '.data'
   ```
   - Expected: User profile with fields (username, bio, skills, avatar)

2. **Get AURA Score**
   ```bash
   curl -s -b test_results/cookies.txt https://volaura.app/api/aura/me | jq '.data'
   ```
   - Expected: `{ aura_score: <number>, components: {...}, badge_tier: "..." }`

3. **Verify AURA > 0 After Assessment**
   - Complete 1 assessment (via Assessment team)
   - Expected: AURA score updates

4. **Badge Tier Assignment**
   ```bash
   curl -s -b test_results/cookies.txt https://volaura.app/api/badges | jq '.data | length'
   ```
   - Expected: If AURA >= 90 → Platinum badge assigned

5. **Visibility Settings**
   - Change visibility: `PUT /api/aura/me/visibility`
   - Expected: Setting persists across logout + login

---

## Phase 2b: ASSESSMENT TEAM (15 min)

**Owner:** Assessment team lead
**Deliverable:** `test_results/assessment-team.json`

### What You Test — Interactive Workflow

1. **Create Assessment Session**
   ```bash
   curl -X POST -b test_results/cookies.txt \
     -H "Content-Type: application/json" \
     -d '{"competency_slug": "communication"}' \
     https://volaura.app/api/assessment/sessions | jq '.data'
   ```
   - Expected: `{ session_id: "...", current_question: {...} }`
   - Save session_id for next steps

2. **Fetch Question Details**
   ```bash
   curl -b test_results/cookies.txt \
     https://volaura.app/api/assessment/questions/{question_id} | jq '.data'
   ```
   - Expected: Question text, options, IRT parameters (a, b, c)

3. **Submit Answer (5 times)**
   ```bash
   curl -X POST -b test_results/cookies.txt \
     -H "Content-Type: application/json" \
     -d '{
       "question_id": "q123",
       "answer_text": "My response",
       "response_time_ms": 5000
     }' \
     https://volaura.app/api/assessment/sessions/{session_id}/submit_answer | jq '.data'
   ```
   - Expected: `{ next_question_id: "..." }` or `{ session_complete: true, score: X }`

4. **Verify Adaptive Difficulty**
   - Submit 5 answers (mix correct + incorrect)
   - Track question difficulty (IRT parameter `b`)
   - Expected: Difficulty should vary (not all same difficulty)

5. **Verify IRT Scoring**
   - Calculate expected score based on answer patterns
   - Compare to `/api/assessment/sessions/{id}` response
   - Expected: Score matches IRT model output

### What Counts as Success

- ✓ Session creates without error
- ✓ 5 questions answered
- ✓ Score calculated and > 0
- ✓ Session marked complete
- ✓ Difficulty varies across questions

---

## Phase 2c-2k: Other Teams (3-5 min each)

**Follow this pattern for your endpoint:**

1. **Create test user** (use cookies.txt from earlier)
2. **Call your endpoint(s)**
3. **Verify response format** (`{ data, meta }`)
4. **Check status code** (correct per operation type)
5. **Verify CORS headers** (should be present)
6. **Test state persistence** (logout + login → data still there)
7. **Record results** in JSON file

### Example Template

```bash
#!/bin/bash
# test_events.json generator

RESULTS_FILE="test_results/events-team.json"

# Test 1: List events
EVENTS=$(curl -s -b test_results/cookies.txt https://volaura.app/api/events)
EVENTS_STATUS=$(echo "$EVENTS" | jq '.data | length')

# Test 2: Attend event
ATTEND=$(curl -s -X POST -b test_results/cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"event_id": "evt_123"}' \
  https://volaura.app/api/events/evt_123/attend)

# Record as JSON
cat > "$RESULTS_FILE" <<EOF
{
  "team": "Events",
  "phase": "2c",
  "status": "PASS",
  "tests": [
    {
      "name": "List events",
      "status": "PASS",
      "endpoint": "GET /api/events",
      "expected": "200 + event list",
      "actual": "$EVENTS_STATUS events returned",
      "duration_ms": 123
    }
  ],
  "failures": 0,
  "blockers": [],
  "warnings": []
}
EOF
```

---

## Phase 3: FRONTEND TEAM (10 min)

**Owner:** Frontend team lead
**Deliverable:** `test_results/frontend-team.json`

### Use Playwright to Test All Pages

1. **Install dependencies (if needed):**
   ```bash
   npm install @playwright/test
   ```

2. **Create test file:** `tests/smoke.spec.ts`

   ```typescript
   import { test, expect } from '@playwright/test';

   test('Landing page loads', async ({ page }) => {
     await page.goto('https://volaura.app');
     await expect(page).toHaveTitle(/Volaura/);
     // Check console errors
     const errors = [];
     page.on('console', msg => {
       if (msg.type() === 'error') errors.push(msg.text());
     });
     expect(errors).toHaveLength(0);
   });

   test('Dashboard loads (logged in)', async ({ page, context }) => {
     // Use auth from earlier
     await page.goto('https://volaura.app/en/dashboard');
     await page.waitForLoadState('networkidle');
     // Verify no CORS errors in console
     // Screenshot for visual check
     await page.screenshot({ path: 'test_results/dashboard.png' });
   });

   test('Assessment page responsive (mobile)', async ({ page }) => {
     await page.setViewportSize({ width: 375, height: 812 });
     await page.goto('https://volaura.app/en/assessment');
     await page.screenshot({ path: 'test_results/assessment_mobile.png' });
   });
   ```

3. **Run tests:**
   ```bash
   npx playwright test --reporter=html
   ```

4. **Extract console errors and timing:**
   ```bash
   # Count console errors on each page
   # Check Core Web Vitals (LCP, FID, CLS)
   # Note: Use Lighthouse or Chrome DevTools for detailed metrics
   ```

### Success Criteria

- [ ] All pages load < 3s
- [ ] Console errors < 5 per page
- [ ] No CORS errors blocking page render
- [ ] Mobile layout responsive (375px width)
- [ ] Screenshot shows no blank pages or spinners

---

## Phase 4: ADMIN TEAM (5 min)

**Owner:** Admin team lead
**Deliverable:** `test_results/admin-team.json`

### What You Test

1. **Admin user access**
   ```bash
   # Must set is_platform_admin=true for test user in Supabase
   curl -s -b test_results/cookies.txt https://volaura.app/api/admin/swarm/agents
   ```
   - Expected: 200 (not 403)

2. **Swarm agents endpoint**
   - Expected: List of agents with status

3. **Proposals endpoint**
   - Expected: List of proposals (may be empty)

---

## Phase 5: QA COORDINATOR (5 min) — Aggregate Results

**Owner:** QA lead (or CTO)

```bash
# Collect all JSON files from all teams
ls test_results/*.json

# Aggregate
python3 scripts/aggregate_test_results.py test_results

# View report
open test_results/AGGREGATED_REPORT.html
```

---

## Timing & Coordination

### Timeline

| Time | Phase | Status |
|------|-------|--------|
| 17:00 | Setup: Run checklist script | All teams: await go-ahead |
| 17:01 | Phase 1a + 1b (Auth + API) | Auth + API teams execute |
| 17:11 | Phase 2a-2i (9 teams, parallel) | All domain teams execute simultaneously |
| 17:25 | Phase 3 (Frontend) | Frontend team executes |
| 17:35 | Phase 4 (Admin) | Admin team executes |
| 17:40 | Phase 5 (Aggregate) | QA coordinator aggregates + reports |

### Slack Updates

- **17:00** - "Starting Phase 0 health check..."
- **17:01** - "Phase 1a + 1b: Auth & API teams begin"
- **17:11** - "Phase 2a-2i: All domain teams executing in parallel"
- **17:25** - "Phase 3: Frontend team executing"
- **17:40** - "Aggregating results..."
- **17:45** - "REPORT READY: [link to AGGREGATED_REPORT.html]"

---

## If Your Test Fails

### Step 1: Identify failure type

| Failure | Likely Cause | Solution |
|---------|--------------|----------|
| CORS error | Access-Control-Allow-Origin missing | Check Railway CORS config, re-deploy |
| 401 | Token not being injected | Check apiFetch interceptor, Session token |
| 422 | Bad request body | Verify request format matches schema |
| 500 | Server error | Check Sentry logs, recent commits |
| Timeout | Slow endpoint | Check database query, add indexes |
| Page blank | JavaScript error | Check browser console |

### Step 2: Document & move on

- Record failure in test result JSON
- Add to "blockers" array
- Do NOT spend > 10 min debugging (log it, move on)
- Let QA coordinator triage post-aggregation

### Step 3: Re-test after fix

- Only re-run affected tests (not full audit)
- Update JSON with new status
- Re-run aggregation script

---

## Example: Full Submission Template

```json
{
  "team": "Assessment",
  "phase": "2b",
  "status": "PASS",
  "summary": "Assessment flow works end-to-end. IRT adaptive difficulty confirmed working.",
  "tests": [
    {
      "name": "Create assessment session",
      "status": "PASS",
      "endpoint": "POST /api/assessment/sessions",
      "expected": "201 + session_id + first question",
      "actual": "201, session_id: sess_abc123, question_id: q_001",
      "duration_ms": 234
    },
    {
      "name": "Submit 5 answers",
      "status": "PASS",
      "endpoint": "POST /api/assessment/sessions/{id}/submit_answer",
      "expected": "5 questions answered, difficulty varies, score calculated",
      "actual": "5 questions answered. Difficulty: [0.3, 0.6, 0.4, 0.7, 0.5]. Score: 72.",
      "duration_ms": 2340
    },
    {
      "name": "Session completion",
      "status": "PASS",
      "endpoint": "GET /api/assessment/sessions/{id}",
      "expected": "status=COMPLETED, score > 0, AURA updated",
      "actual": "status=COMPLETED, score=72, aura_delta=+8",
      "duration_ms": 89
    }
  ],
  "failures": 0,
  "blockers": [],
  "warnings": [],
  "timestamp": "2026-04-04T17:20:00Z"
}
```

---

## Questions?

- **Slack:** #volaura-dev
- **CTO:** Available for unblocking (e.g., CORS error, 500s)
- **This guide:** Point to FUNCTIONAL-TEST-STRATEGY.md for reference

---

**Last Updated:** 2026-04-04
**Test Execution Date:** Session 85, 2026-04-04 17:00 UTC
