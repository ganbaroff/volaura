# Functional Test Strategy — VOLAURA E2E Audit (Async, Parallel)

**Date:** 2026-04-04 (Session 85)
**Purpose:** Replace manual UI clicking with autonomous, parallel testing by domain teams
**Goal State:** All functional surfaces tested asynchronously, results aggregated, batch fix all failures
**Timeline:** 4-6 hours to run all tests in parallel, 2-3 hours to batch-fix failures

---

## PART 1: Decomposition — Testable Surfaces

### 1. Authentication & Session Management
**Owner:** Auth Team
**Scope:** User registration, login (email + Google OAuth), session persistence, logout, token refresh

| Surface | Endpoints | Test Method | Success Criteria |
|---------|-----------|-------------|------------------|
| Email signup | POST /api/auth/signup | HTTP direct + browser persistence | 201 + user.id + session cookie set |
| Email login | POST /api/auth/login | HTTP direct + browser persistence | 200 + JWT in cookie + user context |
| Google OAuth flow | GET /auth/callback?code=... | Browser → Supabase → apiFetch auto-inject | 2xx + redirect to /dashboard + Supabase session |
| Session persistence | GET /api/profiles/me | Verify token in request headers | 200 + profile data (not 401) |
| Logout | POST /api/auth/logout | Clear session cookie | 200 + cookie deleted + /api/profiles/me returns 401 |
| Token refresh | Auto-refresh on expiry | Verify interceptor working | No 401 errors during long session |
| CORS allow /auth/* | All auth endpoints | Check response headers | Access-Control-Allow-Origin present |

**Pass Criteria:**
- Email signup → login → dashboard accessible
- Google OAuth → dashboard accessible (without manual code exchange)
- Session cookie persists across page reloads
- Logout clears session + redirects to /
- No 401 errors on authenticated requests

**Fail Criteria:**
- 401/403 on any authenticated endpoint
- Session lost on page reload
- CORS errors (Access-Control-Allow-Origin missing)
- Manual code exchange required (indicates onAuthStateChange listener not working)

---

### 2. API Response Envelope & Data Formats
**Owner:** API Team
**Scope:** Verify all endpoints return correct format, CORS headers, status codes, error structure

| Surface | Check | Test Method | Success Criteria |
|---------|-------|-------------|------------------|
| Response envelope | All endpoints should return `{ data, meta }` | Sample 5+ endpoints | All 2xx responses have `data` + `meta` |
| CORS headers | Access-Control-Allow-Origin header present | curl -i each endpoint | Header visible in response |
| Error format | All 4xx/5xx return `{ code, message }` | Trigger 404, 422, 500 errors | Errors match schema |
| Content-Type | application/json on all JSON endpoints | Check headers | Never text/html on API responses |
| Status codes | Correct codes per endpoint spec | Verify 201 on POST create, 200 on GET, 204 on DELETE | No 200 on DELETE, no 201 on GET |

**Pass Criteria:**
- All endpoints respond with correct envelope
- CORS headers present on all responses (including errors)
- Error responses structured and readable
- No HTML/XML responses on /api/*

**Fail Criteria:**
- Missing `data` or `meta` fields
- CORS errors (Access-Control-Allow-Origin missing)
- Raw error stack traces returned
- Wrong status codes (e.g., 200 on DELETE)

---

### 3. Core Data Flows — Profiles & AURA
**Owner:** Profile/AURA Team
**Scope:** User profile creation, AURA score calculation, visibility settings, badge assignment

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| Create profile | POST /api/profiles + PUT /api/profiles/{id} | After signup, fill profile data | 201 + profile returned with all fields |
| Get profile | GET /api/profiles/me + GET /api/profiles/{id} | Query own + another user's profile | 200 + correct fields (bio, skills, verification_status) |
| AURA score calculation | GET /api/aura/me | After creating profile + completing assessment | 200 + aura_score present (not null) |
| AURA visibility | PUT /api/aura/me/visibility | Toggle public/private | 200 + visibility setting persisted |
| Badge assignment | Check /api/badges (after AURA > 90) | Query badges endpoint | 200 + list of earned badges (Platinum if >90) |
| Profile search | GET /api/discovery (with filter params) | Search by skill, AURA, badge | 200 + results match filters |

**Pass Criteria:**
- Profile data persists across sessions
- AURA score > 0 after first assessment
- Badge tiers correct (Bronze 40-60, Silver 60-75, Gold 75-90, Platinum >90)
- Visibility toggle works (toggle on/off, verify in another user's search)

**Fail Criteria:**
- AURA score = 0 or null after assessment
- Badges not assigned when AURA threshold met
- Profile data lost on logout + login
- 404 when accessing own profile

---

### 4. Assessment Engine
**Owner:** Assessment Team
**Scope:** Start assessment, answer questions, calculate scores, adaptive difficulty

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| Start assessment | POST /api/assessment/sessions | Create session for a competency | 201 + session_id + first question |
| Get question | GET /api/assessment/questions/{id} | Retrieve question with options | 200 + question_text, difficulty, options |
| Submit answer | POST /api/assessment/sessions/{id}/submit_answer | Answer question, get feedback | 200 + next_question (or session_complete) |
| Adaptive difficulty | Submit answers, track difficulty progression | First 3 answers should vary in difficulty | Difficulty changes based on previous answers |
| Session completion | Submit final answer → end session | Session status should change to COMPLETED | 200 + final_score, competency, recommendations |
| Score persistence | GET /api/assessment/sessions/{id} | Retrieve completed session | 200 + score persists, results cached |
| IRT calculation | Submit 5-10 answers, verify score ranges | Different answer patterns → different scores | Scores consistent with answer quality |

**Pass Criteria:**
- Session created → 5 questions asked → score calculated (in <30s)
- Difficulty adapts (easy answers → harder questions)
- Score = function of answer quality (wrong answers = lower score)
- Session data persists in DB
- No assessment stuck in incomplete state after session ends

**Fail Criteria:**
- All questions same difficulty (not adaptive)
- Score = 0 or null after completion
- Session doesn't end after final answer
- Questions repeat or missing options
- IRT parameters missing (a, b, c)

---

### 5. Events & Attendance
**Owner:** Events Team
**Scope:** Create/list/attend events, check-in, attendance tracking

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| List events | GET /api/events | Fetch all events | 200 + list with id, title, date, attendee_count |
| Get event details | GET /api/events/{id} | Fetch single event | 200 + full event data (description, location, date, attendees) |
| Attend event | POST /api/events/{id}/attend | Mark user as attending | 200/201 + user added to attendee list |
| Unattend event | DELETE /api/events/{id}/attend | Remove attendance | 200/204 + user removed from attendee list |
| Check-in | POST /api/events/{id}/checkin | Coordinator code entry | 200 + user marked checked-in + reward issued |
| Attendance list | GET /api/events/{id}/attendees | Fetch attendee list | 200 + list of attendees with check-in status |

**Pass Criteria:**
- User can attend event → appears in attendee list
- Check-in: coordinator enters code → user marked present
- Attendance persists after logout + login
- Rewards issued on check-in (crystals, AURA boost)
- Event list updated in real-time (new events appear)

**Fail Criteria:**
- User not added to attendee list after /attend
- Check-in doesn't work (coordinator code not recognized)
- Attendance data lost on logout
- No rewards issued on check-in

---

### 6. Activity & Analytics
**Owner:** Analytics Team
**Scope:** Log user actions, track activity feed, analytics events

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| Log activity event | POST /api/analytics/event | Submit user action (assessment_completed, event_attended) | 204 (no content) |
| Get activity feed | GET /api/activity/me | Fetch user's recent actions | 200 + chronological list of activities |
| Get activity stats | GET /api/activity/stats/me | Fetch aggregates (total_assessments, total_events) | 200 + stats object with counts |
| Activity filtering | GET /api/activity/me?type=assessment | Filter by activity type | 200 + only matching activities returned |
| Raw analytics query | Check Langfuse/PostHog integration | Events should appear in observability tool | All events logged + searchable in dashboard |

**Pass Criteria:**
- Actions logged (404 endpoints shouldn't break logging)
- Activity feed shows 10+ recent actions
- Stats count matches manual activity count
- Analytics visible in external dashboard (Langfuse, PostHog)

**Fail Criteria:**
- POST /api/analytics/event returns 5xx
- Activity feed returns 401/CORS errors
- Stats count = 0 after activities completed
- No events in Langfuse

---

### 7. Notifications & Real-Time
**Owner:** Notifications Team
**Scope:** Fetch unread count, mark as read, delivery

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| Unread count | GET /api/notifications/unread-count | Fetch current unread notifications | 200 + unread_count integer |
| List notifications | GET /api/notifications | Fetch notification history | 200 + list with id, type, created_at, read_status |
| Mark as read | PUT /api/notifications/{id}/read | Mark single notification read | 200 + notification.read_status = true |
| Mark all read | POST /api/notifications/read-all | Clear all unread | 200/204 + unread_count becomes 0 |
| Notification delivery | Trigger action → check notifications list | e.g., Someone follows you → notification appears | Notification in list within 2s |

**Pass Criteria:**
- Unread count > 0 when notifications exist
- Mark read → unread count decreases
- Notifications persist after refresh
- Real-time delivery working (Supabase subscriptions)

**Fail Criteria:**
- Unread count always 0
- 401/CORS errors on notification endpoints
- Notifications disappear after refresh
- Delivery lag > 5s

---

### 8. Tribes & Communities
**Owner:** Tribes Team
**Scope:** Create/join tribes, leaderboard, contributions

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| Get my tribes | GET /api/tribes/me | Fetch user's tribe memberships | 200 + list of tribes |
| Tribe leaderboard | GET /api/leaderboard/me (or /tribes/{id}/leaderboard) | Get tribe rankings | 200 + members ranked by AURA/contributions |
| Tribe stats | GET /api/stats/me (tribe context) | Get personal stats in tribe | 200 + contributions_count, rank, level |
| Join tribe | POST /api/tribes/{id}/join | User joins tribe | 200/201 + user in tribe member list |
| Leave tribe | DELETE /api/tribes/{id}/leave | User leaves tribe | 200/204 + user removed from tribe |

**Pass Criteria:**
- User can join/leave tribes
- Leaderboard shows correct ranking (highest AURA first)
- Contributions counted in tribe context
- Tribe data persists

**Fail Criteria:**
- 401/CORS errors on tribe endpoints
- Leaderboard doesn't update after assessment
- User can't join tribe
- Stats show 0 contributions when contributions made

---

### 9. Skills & Competencies
**Owner:** Skills Team
**Scope:** List skills, filter, search, competency progression

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| List all skills | GET /api/skills | Fetch skill library | 200 + 8+ skills (communication, reliability, etc.) |
| Get skill details | GET /api/skills/{id} | Fetch skill with AURA weight | 200 + skill name, weight, description |
| Skill assessment | Assess in a skill → GET /api/aura/me | AURA should reflect skill scores | AURA > 0, skill weights applied |
| Filter by level | GET /api/discovery?min_aura=60 | Filter professionals by skill level | 200 + results match filter |

**Pass Criteria:**
- 8 skills available (communication, reliability, english_proficiency, leadership, event_performance, tech_literacy, adaptability, empathy_safeguarding)
- Each skill has correct AURA weight
- Assessments update skill scores

**Fail Criteria:**
- Skill list empty
- Skills missing from AURA calculation
- Skill weight = 0 for any skill

---

### 10. Payments & Subscription
**Owner:** Payments Team
**Scope:** Subscription status, payment method, upgrade/downgrade

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| Check subscription status | GET /api/subscription/status | Fetch current plan (Free/Pro/Ultra) | 200 + plan, next_billing_date |
| Billing history | GET /api/subscription/invoices | Fetch past invoices | 200 + list of invoices with amounts |
| Update payment method | PUT /api/subscription/payment-method | Save card via Stripe/Paddle | 200 + method saved (no error) |

**Pass Criteria:**
- All users have a default subscription status (Free)
- No errors on payment method updates
- Subscription persists after logout + login

**Fail Criteria:**
- 500 on subscription endpoint
- Payment method not saved
- Subscription data missing/null

---

### 11. BrandedBy Integration
**Owner:** BrandedBy Team
**Scope:** AI twin generation, video, profile sync

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| Generate twin | POST /api/brandedby/twins | Create AI twin from profile | 201 + twin_id + status PENDING/GENERATING |
| Twin status | GET /api/brandedby/twins/{id} | Check generation progress | 200 + status (in-progress/complete/failed) |
| Generate video | POST /api/brandedby/generations | Create video from script | 201 + generation_id |
| List generations | GET /api/brandedby/generations | Fetch user's videos | 200 + list of videos with status |

**Pass Criteria:**
- Twin creation doesn't crash (returns 201 even if generation async)
- Status endpoint responds with PENDING/COMPLETE
- No 500 errors on generation endpoints

**Fail Criteria:**
- 5xx errors on twin/generation endpoints
- Status always FAILED
- Video list always empty

---

### 12. Admin Features
**Owner:** Admin Team
**Scope:** Admin panel access, user management, analytics dashboard

| Flow | Endpoints | Test Method | Success Criteria |
|------|-----------|-------------|------------------|
| Admin auth | Admin user can access /api/admin/* | Set is_platform_admin=true for user in DB | 200 (not 403) |
| Swarm agents | GET /api/admin/swarm/agents | Fetch agent status | 200 + list of agents with status |
| Proposals | GET /api/admin/swarm/proposals | Fetch pending AI proposals | 200 + list (may be empty) |

**Pass Criteria:**
- Admin user can access admin endpoints
- Admin dashboard loads (no 403)
- Swarm agents endpoint responds

**Fail Criteria:**
- 403 on admin endpoints for admin user
- 500 on agent/proposal endpoints

---

### 13. UI / Browser Rendering
**Owner:** Frontend Team
**Scope:** Page load, layout rendering, no console errors

| Page | Test Method | Success Criteria |
|------|-------------|------------------|
| Landing page | Load `/` | 200 + page renders in <3s, no console errors |
| Signup page | Load `/signup` | 200 + form renders, no client-side 404s |
| Login page | Load `/login` | 200 + form renders, OAuth button visible |
| Dashboard | Logged in, load `/dashboard` | 200 + cards render, no CORS errors in console |
| Assessment | Load `/assessment` | 200 + question renders, options clickable |
| Profile | Load `/profile` | 200 + profile data visible, no 401 errors |
| Events | Load `/events` | 200 + event list renders |
| Admin | Logged in as admin, load `/admin` | 200 + admin panel renders |

**Pass Criteria:**
- All pages load in <3s
- No console errors (CORS, 401, 404)
- No layout shifts / CLS issues
- Mobile responsive (tested at 375px width)

**Fail Criteria:**
- Page blank or spinner stuck
- Console errors > 5
- CORS errors blocking page load
- Mobile layout broken

---

## PART 2: Parallel Execution Model

### Dependency Graph (What runs when)

```
┌──────────────────────────────────────────────────────────────┐
│ PHASE 0: Health Check (run first, 1 min)                    │
│ - GET /health → 200                                           │
│ - Verify API is responding                                    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        ┌─────────────────────┐      ┌─────────────────────┐
        │ PHASE 1a: Auth Flow │      │ PHASE 1b: API Layer │
        │ (5-10 min)          │      │ (5-10 min)          │
        │                     │      │                     │
        │ 1. Email signup     │      │ 1. Response envelop │
        │ 2. Email login      │      │ 2. CORS headers     │
        │ 3. Google OAuth     │      │ 3. Error formats    │
        │ 4. Token refresh    │      │ 4. Status codes     │
        │ 5. Logout           │      │ 5. Rate limits      │
        └──────────┬──────────┘      └──────────┬──────────┘
                   │ (session ready)             │ (endpoints verified)
                   └──────────────┬──────────────┘
                                  ▼
                    ┌─────────────────────────────────────┐
                    │ PHASE 2: Protected Routes (10 min)   │
                    │ (requires logged-in session)         │
                    │                                       │
                    │ 2a. Profile/AURA (in parallel)      │
                    │ 2b. Assessment (in parallel)         │
                    │ 2c. Events (in parallel)             │
                    │ 2d. Tribes (in parallel)             │
                    │ 2e. Skills (in parallel)             │
                    │ 2f. Notifications (in parallel)      │
                    │ 2g. Analytics (in parallel)          │
                    │ 2h. BrandedBy (in parallel)          │
                    │ 2i. Payments (in parallel)           │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │ PHASE 3: UI/Browser (10 min)         │
                    │ (uses Playwright batch)              │
                    │                                       │
                    │ - Load all pages in parallel         │
                    │ - Screenshot + console logs          │
                    │ - Responsive test (mobile/desktop)   │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │ PHASE 4: Admin (5 min)               │
                    │ (requires admin user)                │
                    │                                       │
                    │ - Admin auth                         │
                    │ - Swarm agents endpoint              │
                    │ - Proposals endpoint                 │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │ PHASE 5: Aggregate Results (5 min)   │
                    │                                       │
                    │ - Merge all test results             │
                    │ - Generate report                    │
                    │ - Identify failures                  │
                    │ - Recommend fixes                    │
                    └─────────────────────────────────────┘
```

### Team Assignments

| Team | Phase | Endpoints | Duration | Tools |
|------|-------|-----------|----------|-------|
| **Health** | 0 | /health | 1 min | curl |
| **Auth** | 1a | /auth/* + session management | 5-10 min | Playwright + curl |
| **API** | 1b | Response format, CORS, errors | 5-10 min | curl + Firefox DevTools |
| **Profile/AURA** | 2a | /profiles/*, /aura/* | 5 min | curl (logged in) |
| **Assessment** | 2b | /assessment/*, IRT calculation | 10-15 min | volaura_web_checker (interactive) |
| **Events** | 2c | /events/*, /checkin | 5 min | curl |
| **Tribes** | 2d | /tribes/*, /leaderboard | 5 min | curl |
| **Skills** | 2e | /skills/*, weights | 3 min | curl |
| **Notifications** | 2f | /notifications/*, real-time | 5 min | curl + WebSocket (if applicable) |
| **Analytics** | 2g | /analytics/event, logs | 5 min | curl + check logs |
| **BrandedBy** | 2h | /brandedby/*, twin/video generation | 5 min | curl |
| **Payments** | 2i | /subscription/*, invoices | 3 min | curl |
| **Frontend** | 3 | All pages, browser rendering | 10 min | Playwright batch |
| **Admin** | 4 | /admin/*, swarm agents | 5 min | curl (admin session) |
| **QA Coordinator** | 5 | Aggregate + report | 5 min | Python script |

### Parallel Execution Timeline

```
Session start: 2026-04-04 17:00 UTC

17:00 - 17:01  │ PHASE 0: Health check
               │
17:01 - 17:11  │ PHASE 1a (Auth) + 1b (API) — run in parallel
               │
17:11 - 17:25  │ PHASE 2a-2i (all protected routes) — 9 teams in parallel
               │
17:25 - 17:35  │ PHASE 3: Frontend/UI (all pages) — Playwright batch
               │
17:35 - 17:40  │ PHASE 4: Admin checks
               │
17:40 - 17:45  │ PHASE 5: Aggregate + report

Total: ~45 minutes to complete full functional audit
```

---

## PART 3: Aggregation Plan — Collect All Results

### Test Result Format

Each team submits results in JSON:

```json
{
  "team": "Assessment",
  "phase": "2b",
  "status": "PASS" | "FAIL" | "PARTIAL",
  "summary": "Assessment flow works end-to-end; IRT scoring correct",
  "tests": [
    {
      "name": "Start assessment session",
      "status": "PASS",
      "endpoint": "POST /api/assessment/sessions",
      "expected": "201 + session_id",
      "actual": "201 + session_id = abc123",
      "duration_ms": 145
    },
    {
      "name": "Submit answer",
      "status": "PASS",
      "endpoint": "POST /api/assessment/sessions/abc123/submit_answer",
      "expected": "200 + next_question",
      "actual": "200 + next_question_id = def456",
      "duration_ms": 312
    },
    {
      "name": "IRT adaptive difficulty",
      "status": "FAIL",
      "endpoint": "GET /api/assessment/questions/*",
      "expected": "Questions vary in difficulty (a, b, c parameters differ)",
      "actual": "All questions have same difficulty = 0.5",
      "duration_ms": 0,
      "root_cause": "IRT difficulty not changing based on previous answers"
    }
  ],
  "failures": 1,
  "blockers": ["IRT adaptive difficulty not working"],
  "warnings": [],
  "timestamp": "2026-04-04T17:20:00Z"
}
```

### Aggregation Script

```python
#!/usr/bin/env python3
# scripts/aggregate_test_results.py

import json
import sys
from pathlib import Path
from datetime import datetime

def aggregate(results_dir: str) -> dict:
    """Merge all team test results into one report."""

    results = []
    for json_file in Path(results_dir).glob("*.json"):
        with open(json_file) as f:
            results.append(json.load(f))

    # Summary
    total_tests = sum(len(r["tests"]) for r in results)
    passed = sum(1 for r in results for t in r["tests"] if t["status"] == "PASS")
    failed = sum(1 for r in results for t in r["tests"] if t["status"] == "FAIL")

    # Blockers (failures in critical path)
    blockers = []
    for r in results:
        for failure in r.get("blockers", []):
            blockers.append(f"{r['team']}: {failure}")

    # Report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "PASS" if failed == 0 else "FAIL",
        "summary": {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{100*passed/total_tests:.1f}%" if total_tests > 0 else "N/A",
        },
        "by_team": results,
        "critical_blockers": blockers,
        "next_steps": [
            f"Fix {failed} failing tests" if failed > 0 else "All tests pass",
            "Batch-fix failures (estimated 2-3 hours)",
            "Re-run audit to confirm fixes",
            "Manual walkthrough as final validation"
        ]
    }

    return report

if __name__ == "__main__":
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "test_results"
    report = aggregate(results_dir)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["overall_status"] == "PASS" else 1)
```

### Where Results Go

```
test_results/
├── auth-team.json          (Phase 1a)
├── api-team.json           (Phase 1b)
├── profile-aura-team.json  (Phase 2a)
├── assessment-team.json    (Phase 2b)
├── events-team.json        (Phase 2c)
├── tribes-team.json        (Phase 2d)
├── skills-team.json        (Phase 2e)
├── notifications-team.json (Phase 2f)
├── analytics-team.json     (Phase 2g)
├── brandedby-team.json     (Phase 2h)
├── payments-team.json      (Phase 2i)
├── frontend-team.json      (Phase 3)
├── admin-team.json         (Phase 4)
└── AGGREGATED_REPORT.json  (Phase 5 output)
```

---

## PART 4: "Ready" State — Acceptance Criteria

### Critical (Must Pass Before Walkthrough)
- [ ] Health: GET /health → 200
- [ ] Auth: Email signup → login → session persists
- [ ] Auth: Google OAuth → session persists (no manual code exchange)
- [ ] Auth: CORS headers present on all /api/* responses
- [ ] API: All endpoints return `{ data, meta }` envelope
- [ ] Errors: 4xx/5xx return `{ code, message }` (no stack traces)
- [ ] Protected routes: GET /api/profiles/me, /api/aura/me, /api/assessment/* all return 200 (not 401)
- [ ] Notifications: GET /api/notifications/unread-count → 200 (not CORS error)
- [ ] Assessment: POST /api/assessment/sessions → 201, can submit answers
- [ ] Console: < 5 console errors on any page (excluding warnings)
- [ ] Admin: Admin user can access /admin/* (not 403)

### High (Should Pass Before Walkthrough)
- [ ] Response times: All API responses < 1s
- [ ] AURA: Score > 0 after first assessment completion
- [ ] Events: Can list events without CORS errors
- [ ] Activity: POST /api/analytics/event → 204 (no 5xx)
- [ ] Tribes: GET /api/tribes/me → 200
- [ ] Mobile: Pages responsive at 375px width (no broken layout)
- [ ] Payments: GET /api/subscription/status → 200

### Medium (Nice to Have)
- [ ] IRT adaptive difficulty (questions vary based on answers)
- [ ] Real-time notifications (< 2s delivery)
- [ ] BrandedBy: Twin generation doesn't crash (returns 201)
- [ ] Langfuse: Events appear in observability dashboard

---

## PART 5: Recommended Tool Stack

### Phase 1: HTTP Tests (Auth, API, Protected Routes)
**Tool:** `curl` (CLI) or `httpie` (human-friendly)
**Why:** Fast, scriptable, can run in parallel, no overhead

```bash
# Example: test /api/profiles/me
curl -H "Cookie: sb-access-token=..." \
     -H "Content-Type: application/json" \
     https://volaura.app/api/profiles/me

# Batch test with parallel
parallel 'curl -s {} | jq .meta' ::: \
  "https://volaura.app/api/profiles/me" \
  "https://volaura.app/api/aura/me" \
  "https://volaura.app/api/assessment/sessions"
```

### Phase 2: Interactive Tests (Assessment, Events, Check-in)
**Tool:** `volaura_web_checker` (Playwright batch) or `pytest + httpx`
**Why:** Can follow workflows, extract session IDs, state-dependent tests

```bash
# Run assessment flow
pnpm test:e2e --suite=assessment-flow --headless
```

### Phase 3: UI/Browser Tests (Page Load, Rendering, Console Errors)
**Tool:** Playwright (headless batch)
**Why:** Capture screenshots, console logs, network waterfall

```bash
# Load all pages, capture errors
npx playwright test --project=chromium tests/smoke.spec.ts
```

### Phase 4: Real-Time / WebSocket Tests (Notifications, Subscriptions)
**Tool:** `wscat` or custom Python script with Supabase JS client
**Why:** Can listen to real-time subscriptions, verify delivery

```bash
# Listen to notifications subscription
npx supabase-js-listener --table=notifications --auth_token=...
```

### Phase 5: Aggregation
**Tool:** Python script (aggregate_test_results.py)
**Output:** Single JSON report + pretty HTML summary

---

## PART 6: Estimated Timeline

| Phase | Task | Tool | Team Size | Duration | Parallel? |
|-------|------|------|-----------|----------|-----------|
| 0 | Health check | curl | 1 | 1 min | Serial (gate) |
| 1a | Auth flow | Playwright + curl | 2 | 10 min | With 1b |
| 1b | API layer | curl + DevTools | 1 | 10 min | With 1a |
| 2a | Profile/AURA | curl | 1 | 5 min | Yes (9-way) |
| 2b | Assessment | volaura_web_checker | 2 | 15 min | Yes |
| 2c | Events | curl | 1 | 5 min | Yes |
| 2d | Tribes | curl | 1 | 5 min | Yes |
| 2e | Skills | curl | 1 | 3 min | Yes |
| 2f | Notifications | curl + wscat | 1 | 5 min | Yes |
| 2g | Analytics | curl | 1 | 5 min | Yes |
| 2h | BrandedBy | curl | 1 | 5 min | Yes |
| 2i | Payments | curl | 1 | 3 min | Yes |
| 3 | Frontend/UI | Playwright batch | 2 | 10 min | Yes (with 2) |
| 4 | Admin | curl | 1 | 5 min | Yes |
| 5 | Aggregate | Python | 1 | 5 min | Serial |
| **TOTAL** | | | **8-10 people** | **~45 min** | **High parallelism** |

### Resource Allocation
- **Small team (4 people):** Phases run sequentially (total ~2 hours)
- **Medium team (8-10 people):** Phases 2a-2i run in parallel (total ~45 min)
- **Large team (12+ people):** All phases parallel except 0, 5 (total ~30 min)

---

## PART 7: Failure Triage Process

### When a Test Fails

1. **Capture details:**
   - Endpoint tested
   - HTTP method + URL
   - Request headers (token, content-type)
   - Response status + body
   - Error message (CORS, 401, 422, 500, etc.)
   - Timestamp

2. **Categorize failure:**
   - **Auth blocker:** 401/403 → verify session token, rerun Phase 1a
   - **CORS blocker:** Missing Access-Control-Allow-Origin → check Railway/Vercel config, re-deploy
   - **API logic error:** 422/400 → check request body format, Pydantic validation
   - **Server error:** 5xx → check API logs in Sentry/Railway, review recent commits
   - **UI blocker:** Console error, page blank → check browser console, network tab

3. **Assign to owner:** Route to responsible team
   - Auth blockers → Auth team
   - API/CORS → API infrastructure team
   - Data/logic → specific domain team (Assessment, Events, etc.)

4. **Batch all fixes:** Collect 5+ fixes, then push one commit
   - Avoid hot-fixes (per-issue deployments)
   - Batch changes reduce deployment risk

5. **Re-test:** Rerun only affected tests, not full audit

---

## PART 8: Expected Failure Patterns (Session 85 Context)

Based on sprint-state.md, expect these failures:

### Known Issues (Likely to Fail)
1. **CORS errors on /api/* (BLOCKER)**
   - Root cause: Missing Access-Control-Allow-Origin headers
   - Fix deployed in commits: e4a40cb, 06c36fc
   - Status: Awaiting deployment to production
   - Expected failures: All /api/* endpoints return CORS error
   - Recovery: Redeploy Railway backend, clear Vercel cache

2. **OAuth callback not working (BLOCKER)**
   - Attempt 3 (onAuthStateChange) deployed
   - May still fail if session token not auto-injected
   - Expected failure: Stuck on /callback page after OAuth redirect
   - Recovery: Check apiFetch token injection in request interceptor

3. **Admin endpoint 403 (if is_platform_admin not set)**
   - Expected failure: GET /api/admin/* returns 403
   - Recovery: Run migration 20260403000003 in Supabase, set is_platform_admin=true for Yusif

4. **BrandedBy endpoints missing (EXPECTED)**
   - Twin/generation endpoints may not be fully wired
   - Expected failure: 404 on POST /api/brandedby/twins
   - Recovery: Deferred feature, mark as "Not Yet Implemented"

### Likely to Pass
- Activity logging (POST /api/analytics/event)
- Subscription status (GET /api/subscription/status)
- Basic auth (email signup/login)
- Assessment endpoint structure (no IRT logic errors expected)

---

## Summary Table

| Area | Decomposed into | Owner | Tool | Pass Criteria |
|------|-----------------|-------|------|---------------|
| Auth | Signup, login, OAuth, session, logout | Auth Team | Playwright + curl | Email + Google login work, session persists |
| API | Envelope, CORS, errors, status codes | API Team | curl + DevTools | All responses have `{data,meta}`, CORS headers present |
| Profiles | Create, read, AURA score, badges, visibility | Profile/AURA Team | curl | AURA > 0 after assessment, badges assigned |
| Assessment | Start, answer, adaptive difficulty, completion | Assessment Team | volaura_web_checker | 5 questions → score calculated, difficulty adapts |
| Events | List, attend, check-in, attendance tracking | Events Team | curl | Can attend → appears in attendee list, check-in works |
| Tribes | Join, leaderboard, stats, contributions | Tribes Team | curl | Can join/leave, leaderboard updated |
| Notifications | Unread count, list, mark read, real-time | Notifications Team | curl + wscat | Unread count > 0 when notifications exist |
| Analytics | Event logging, activity feed, stats | Analytics Team | curl | Events logged, feed shows 10+ actions, stats correct |
| Skills | List, details, AURA weights | Skills Team | curl | 8 skills present, weights sum to 1.0 |
| BrandedBy | Twin generation, video creation, status | BrandedBy Team | curl | Endpoints respond (even if async generation) |
| Payments | Subscription status, invoices | Payments Team | curl | All users have default status, no 500 errors |
| Admin | Access control, swarm agents, proposals | Admin Team | curl | Admin user gets 200 (not 403), agents endpoint responds |
| Frontend | Page load, rendering, console errors, responsive | Frontend Team | Playwright | All pages load <3s, <5 console errors, mobile works |

---

## Next Steps (After Strategy Approval)

1. **Week 1:**
   - [ ] CTO meets with each team (15 min each) → assign test owner, share tool setup
   - [ ] Distribute this strategy document
   - [ ] Set up test results directory structure
   - [ ] Confirm test environment (staging or production)

2. **Week 2:**
   - [ ] Each team writes Phase-specific tests (curl commands / Playwright tests)
   - [ ] Test environment verified (can access API, can create test user)
   - [ ] Team lead confirms readiness for parallel execution

3. **Execution Day:**
   - [ ] 17:00 UTC: Phase 0 (Health check) — 1 min
   - [ ] 17:01 UTC: Phases 1a + 1b (Auth + API) — 10 min
   - [ ] 17:11 UTC: Phases 2a-2i (all protected routes) — 9 teams in parallel — 15 min
   - [ ] 17:25 UTC: Phase 3 (Frontend) — 10 min
   - [ ] 17:35 UTC: Phase 4 (Admin) — 5 min
   - [ ] 17:40 UTC: Phase 5 (Aggregate) — 5 min
   - [ ] 17:45 UTC: Report generated + triage begins

4. **Post-Audit:**
   - [ ] Batch-fix all failures (2-3 hours)
   - [ ] Re-run failed tests only (30 min)
   - [ ] Manual walkthrough (1-2 hours)
   - [ ] CEO sign-off on "launch ready" state

---

## Appendix: Example Test Commands

### Phase 1a: Auth Flow

```bash
# Test email signup
curl -X POST https://volaura.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "username": "testuser"
  }' \
  | jq .

# Test email login
curl -X POST https://volaura.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }' \
  -c cookies.txt \
  | jq .

# Test protected endpoint with session cookie
curl https://volaura.app/api/profiles/me \
  -b cookies.txt \
  -H "Authorization: Bearer $TOKEN" \
  | jq .meta

# Test CORS headers
curl -i https://volaura.app/api/health \
  | grep "Access-Control-Allow-Origin"
```

### Phase 1b: API Response Format

```bash
# Test response envelope on 5+ endpoints
for endpoint in \
  "https://volaura.app/api/health" \
  "https://volaura.app/api/skills" \
  "https://volaura.app/api/events"
do
  echo "Testing $endpoint"
  curl -s "$endpoint" | jq 'keys' # Should show ["data", "meta"]
done

# Test error responses (should have { code, message })
curl -s https://volaura.app/api/profiles/nonexistent \
  -b cookies.txt \
  | jq '.message'
```

### Phase 2b: Assessment Flow

```bash
# Start assessment session
SESSION_ID=$(curl -s -X POST https://volaura.app/api/assessment/sessions \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"competency_slug": "communication"}' \
  | jq -r '.data.session_id')

echo "Session: $SESSION_ID"

# Submit answer
curl -X POST https://volaura.app/api/assessment/sessions/$SESSION_ID/submit_answer \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "q123",
    "answer_text": "My answer",
    "response_time_ms": 5000
  }' \
  | jq '.data.next_question'
```

---

**End of Functional Test Strategy**
**Version 1.0 — Ready for Team Deployment**
