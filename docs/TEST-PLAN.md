# Volaura Test Plan v1.0
**Date:** 2026-03-25 | **Author:** CTO (Claude) + Security Audit Team
**Coverage target:** 80%+ on critical paths, 100% on auth/assessment flows

---

## Architecture: What We're Testing

```
[User] → [Vercel/Next.js] → [Railway/FastAPI] → [Supabase PostgreSQL]
                                    ↓
                            [Gemini API] + [Swarm Engine]
```

---

## Layer 1 — Backend Unit Tests (Python/pytest)

### 1.1 IRT / CAT Engine (`apps/api/app/core/assessment/`)

| Test | File | Priority |
|------|------|---------|
| Theta estimation from known answer vectors | `test_irt_known_pairs.py` ✅ EXISTS | P0 |
| EAP posterior update: 0.8 ability, easy question → theta increases | engine.py | P0 |
| 3PL probability: P(correct) for known a/b/c and theta | engine.py | P0 |
| CAT stops at min 8 questions OR SE < 0.35 | engine.py | P0 |
| theta_to_score: theta=-3 → ~0, theta=0 → ~50, theta=3 → ~100 | engine.py | P0 |
| Score clamp: result always in [0, 100] | engine.py | P0 |

**Run:** `cd apps/api && python -m pytest tests/test_irt_known_pairs.py -v`

---

### 1.2 Anti-Gaming (`apps/api/app/core/assessment/antigaming.py`)

| Test | Scenario | Expected |
|------|----------|---------|
| Fast responses: all < 3s | 8 answers, all time=1000ms | flags.fast_responses = True |
| Slow responses: all > 60s | 8 answers, all time=70000ms | flags.slow_responses = True |
| Alternating binary: 0,1,0,1,0,1,0,1 | 8 binary answers | flags.alternating_pattern = True |
| Identical responses: all 0.5 | 8 identical scores | flags.all_identical = True |
| Clean responses: varied timing, varied scores | Normal distribution | no flags |
| Server-side timing (CRIT-03 fix) | Client sends response_time_ms=0, server measures actual | server_elapsed > 0 |

**New test needed:** `test_antigaming.py`

---

### 1.3 BARS / LLM Evaluation (`apps/api/app/services/llm.py`)

| Test | Scenario | Expected |
|------|----------|---------|
| Mock LLM returns invalid JSON | `{"not": "valid_bars"}` | raises/returns error gracefully |
| Mock LLM returns valid BARS | `{"score": 0.8, "feedback": "Good"}` | score=0.8 parsed |
| LLM timeout (>10s) | Gemini API down | fallback or 503, not 500 |
| Cache hit: same question+answer | Second call doesn't hit LLM | session cache hit count=1 |

**File:** `tests/test_llm_mock.py` ✅ EXISTS
**Run:** `python -m pytest tests/test_llm_mock.py -v`

---

### 1.4 Schema Validation

| Test | What | Expected |
|------|------|---------|
| `AssessmentStartResponse` | All required fields present | No KeyError in 10-Q session |
| `AnswerFeedback` | `raw_score` ABSENT (CRIT-03) | Field removed in production |
| `OrganizationResponse` | Uses `verified_at`, `website` | Matches DB columns |
| `QuestionOut` | No `correct_answer` field | Cannot leak answers |

---

## Layer 2 — Backend Integration Tests (pytest + real Supabase)

### 2.1 Authentication Flow

```
POST /api/auth/register → POST /api/auth/login → GET /api/profiles/me
```

| Test | Steps | Expected |
|------|-------|---------|
| Happy path registration | Valid email+password | 201, access_token |
| Duplicate email | Register same email twice | 400 REGISTRATION_FAILED (not 409 to prevent enumeration) |
| Login wrong password | Correct email, wrong password | 401 INVALID_CREDENTIALS |
| Login wrong email | Wrong email | 401 INVALID_CREDENTIALS (same message, no enumeration) |
| JWT expired | Use 7-day-old token | 401 |
| Malformed JWT | `Authorization: Bearer not-a-jwt` | 401 |
| No JWT | No Authorization header | 401 |
| Rate limit: 5 failed logins/minute | 6th request | 429 |

**File:** `tests/test_e2e_assessment.py` (auth section) ✅ EXISTS

---

### 2.2 Full Assessment Flow (E2E Happy Path)

```
POST /assessment/start → [8 questions loop: GET /assessment/current + POST /assessment/answer] → POST /assessment/complete → GET /assessment/results/{session_id}
```

| Step | Test | Expected |
|------|------|---------|
| Start | Valid user, no active session | 201, session_id, first_question |
| Start duplicate | Second start while active | 409 ACTIVE_SESSION_EXISTS |
| Answer: valid | Correct session_id + question_id | 200, next_question or completion signal |
| Answer: wrong session | Other user's session_id | 403 |
| Answer: already answered | Resubmit same question | 409 QUESTION_ALREADY_ANSWERED |
| Answer: 60/hour limit | 61st answer in 1 hour | 429 |
| Complete: before 8 questions | Force-complete at Q3 | 200 (early exit accepted) |
| Complete: invalid session | Nonexistent session_id | 404 |
| Results: valid | After complete | 200, aura_score 0-100, badge_tier |
| Results: in-progress session | Before complete | 403 |

**File:** `tests/test_e2e_assessment.py` ✅ EXISTS
**Run:** `python -m pytest tests/test_e2e_assessment.py -v --tb=short`

---

### 2.3 RLS Audit Tests

| Test | Query | Expected |
|------|-------|---------|
| User reads own profile | `SELECT * FROM profiles WHERE id = auth.uid()` | Returns row |
| User reads other's profile | `SELECT * FROM profiles WHERE id = other_uid` | Empty (RLS blocks) |
| User reads own sessions | `SELECT * FROM assessment_sessions WHERE user_id = auth.uid()` | Returns rows |
| User reads other's sessions | `SELECT * FROM assessment_sessions WHERE user_id = other_uid` | Empty |
| Anon reads public profiles | `SELECT * FROM profiles WHERE is_public = TRUE` | Returns rows |
| Anon reads private profiles | `SELECT * FROM profiles WHERE is_public = FALSE` | Empty |
| Service role bypasses RLS | Admin client reads any row | Returns row (expected) |
| questions_safe view | `SELECT correct_answer FROM questions_safe` | Column doesn't exist |

**File:** `tests/test_rls_audit.py` ✅ EXISTS

---

### 2.4 Security Tests

| Test | Attack Vector | Expected |
|------|--------------|---------|
| SQL injection in username | `username = "'; DROP TABLE profiles;--"` | 422 (regex validation) |
| XSS in bio | `<script>alert(1)</script>` | HTML stripped or 422 |
| Path traversal in session_id | `../../../etc/passwd` | 422 UUID validation |
| Oversized answer | 10MB string in answer field | 422 (max length validation) |
| CRIT-02: verify link for other user | `POST /profiles/{other_user_id}/verification-link` | 403 (after fix) |
| HIGH-03: client-controlled timing | Send `response_time_ms=999999` | Server uses own timestamp |

**File:** `tests/test_security.py` ✅ EXISTS

---

## Layer 3 — Frontend Component Tests (Vitest)

### 3.1 Existing Tests (run: `pnpm test`)

| File | Component | Tests |
|------|-----------|-------|
| `login.test.tsx` ✅ | LoginPage | render, submit, error states |
| `competency-card.test.tsx` ✅ | CompetencyCard | score display, badge color |
| `mcq-options.test.tsx` ✅ | McqOptions | selection, disabled state |
| `progress-bar.test.tsx` ✅ | ProgressBar | width calculation |
| `aura-score-widget.test.tsx` ✅ | AuraScoreWidget | score render, loading |
| `stats-row.test.tsx` ✅ | StatsRow | counts display |
| `sidebar.test.tsx` ✅ | Sidebar | navigation items, active state |

**Run:** `cd apps/web && pnpm test`

### 3.2 Missing Tests (write these)

| Component | What to test | Priority |
|-----------|-------------|---------|
| `question-card.tsx` | MCQ render, text render, time display | P0 |
| `assessment/[sessionId]/page.tsx` | Start → question loop → complete button | P0 |
| `dashboard/page.tsx` | AURA score loads, error state, empty state | P1 |
| `profile/page.tsx` | Edit mode toggle, save, validation errors | P1 |
| `organizations/page.tsx` | List render, empty state, org card click | P1 |
| Privacy Policy page | All 10 sections render, Back link works | P2 |

---

## Layer 4 — API Contract Tests

### 4.1 OpenAPI Compliance

Every response must match the generated TypeScript types (`apps/web/src/lib/api/generated/types.gen.ts`).

```bash
# Generate fresh types and check for diff
cd apps/web && pnpm generate:api
git diff --exit-code src/lib/api/generated/
```

If diff exists → backend response shape changed without updating frontend types.

### 4.2 Response Envelope

All API responses must follow `{ data: T, meta?: {} }` format.

| Endpoint | Envelope check |
|----------|---------------|
| GET /api/profiles/me | `response.data.id` exists |
| POST /api/assessment/start | `response.data.session_id` exists |
| GET /api/organizations | `response.data` is array |

---

## Layer 5 — Smoke Tests (Production)

**Run after every deploy. Target: `https://volauraapi-production.up.railway.app`**

```bash
cd apps/api && python -m pytest tests/test_smoke_assessment.py -v --prod
```

| Check | Expected |
|-------|---------|
| GET /health | `{"status": "ok"}` |
| GET /api/organizations | 200, array (not 500) |
| POST /api/auth/login with wrong creds | 401 (not 500) |
| GET /api/assessment/current (no auth) | 401 (not 500) |
| Response time < 3s | All above endpoints |

**File:** `tests/test_smoke_assessment.py` ✅ EXISTS

---

## Layer 6 — Security Tests (new, from audit findings)

These tests do NOT exist yet. Write before launch.

### 6.1 CRIT-02 Fix Test — Verification Link Authorization

```python
# test_security.py — add this test
def test_cannot_create_verification_link_for_other_user(client, user_a_token, user_b_id):
    response = client.post(
        f"/api/profiles/{user_b_id}/verification-link",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={"verifier_name": "Attacker", "verifier_org": "Evil Corp"}
    )
    assert response.status_code == 403
```

### 6.2 CRIT-03 Fix Test — Raw Score Not In Response

```python
def test_answer_feedback_has_no_raw_score(client, session, token):
    response = client.post("/api/assessment/answer", ...)
    assert "raw_score" not in response.json()
    assert "raw_score" not in response.json().get("data", {})
```

### 6.3 HIGH-03 Fix Test — Server-Side Timing

```python
def test_server_measures_timing_not_client(client, session, token):
    # Send suspiciously fast time from client
    response = client.post("/api/assessment/answer", json={
        "session_id": session.id,
        "question_id": session.current_question_id,
        "answer": "test answer",
        "response_time_ms": 0  # Client claims instant
    })
    # Anti-gaming should use server-side elapsed time, not 0
    # Session state should show a reasonable elapsed time
    assert response.json()["data"]["anti_gaming_flags"]["fast_responses"] == False
```

---

## Layer 7 — Performance Tests

| Endpoint | Load | Target P95 |
|----------|------|----------|
| GET /health | 100 RPS | < 50ms |
| GET /api/organizations | 50 RPS | < 200ms |
| POST /api/assessment/answer | 10 RPS | < 2s (LLM call) |
| GET /api/profiles/{username} | 50 RPS | < 150ms |

**Tool:** `locust` or `k6`
**Run against staging only, never production.**

---

## Layer 8 — Manual QA Checklist (before each release)

### 8.1 Full User Journey (Volunteer)

- [ ] Register with new email
- [ ] Confirm email (if confirmation enabled)
- [ ] Complete profile (name, city, languages, bio)
- [ ] Start assessment
- [ ] Answer 8+ questions (mix of MCQ and open-ended)
- [ ] Complete assessment
- [ ] View AURA score and badge
- [ ] Check public profile is accessible at `/{locale}/profile/{username}`

### 8.2 Organization Flow

- [ ] Register as org admin
- [ ] View organizations list
- [ ] View org profile
- [ ] Search volunteers (by competency, location)

### 8.3 Edge Cases

- [ ] Start assessment → close browser → reopen → resume (or blocked from starting new)
- [ ] Answer with empty string → validation error shown
- [ ] Answer with 10,000 character string → capped or rejected
- [ ] Switch locale mid-assessment → AZ strings display correctly
- [ ] Mobile viewport (375px) → all pages usable

---

## CI/CD Test Matrix

```yaml
# Runs on every PR and push to main
tests:
  backend:
    - pytest tests/test_irt_known_pairs.py      # IRT math
    - pytest tests/test_llm_mock.py             # LLM mock
    - pytest tests/test_security.py             # security
    - pytest tests/test_rls_audit.py            # RLS (requires Supabase test project)
  frontend:
    - pnpm test                                  # Vitest
    - pnpm build                                 # TypeScript compile check
  smoke:
    - pytest tests/test_smoke_assessment.py --prod  # production health
```

---

## Priority Order (what to fix/write first)

### Week 1 (Before any public announcement)
1. **Fix CRIT-02**: Add authorization check on verification-link endpoint
2. **Fix CRIT-03**: Remove `raw_score` from `AnswerFeedback` response
3. **Fix HIGH-03**: Record `question_delivered_at` server-side, use for timing
4. **Write tests** for CRIT-02 and CRIT-03 fixes
5. Run full smoke test suite on production

### Week 2 (Before Pasha Bank pitch)
6. Fix HIGH-01: Add optimistic locking on assessment answer submit
7. Fix HIGH-02: Rate limit `complete_assessment` endpoint + UUID validation
8. Add `question-card.tsx` component test
9. Add `assessment/[sessionId]/page.tsx` E2E test
10. Performance baseline: run locust against staging

### Week 3 (Before public beta)
11. Fix MED-01: Email enumeration prevention
12. Fix MED-03: `_fetch_questions` — remove `correct_answer` from select
13. Fix MED-05: Add anon-role RLS policy for public profiles
14. Complete missing frontend tests
15. Full manual QA checklist run

---

## Test Commands Reference

```bash
# Backend (from apps/api/)
python -m pytest tests/ -v                          # all tests
python -m pytest tests/test_irt_known_pairs.py -v   # IRT only
python -m pytest tests/ -k "security" -v            # security only
python -m pytest tests/ --cov=app --cov-report=html # with coverage

# Frontend (from apps/web/)
pnpm test                  # watch mode
pnpm test --run            # single run
pnpm test --coverage       # with coverage report

# Smoke (production)
PRODUCTION_URL=https://volauraapi-production.up.railway.app \
  python -m pytest tests/test_smoke_assessment.py -v

# Generate API types (run after backend schema changes)
pnpm generate:api
```

---

## Security Score Tracker

| Version | Date | Score | Critical | High | Medium |
|---------|------|-------|---------|------|--------|
| v1.0 | 2026-03-25 | 6.5/10 | 3 | 4 | 5 |
| v1.1 | — | — | 0 (target) | 0 (target) | 2 (target) |
