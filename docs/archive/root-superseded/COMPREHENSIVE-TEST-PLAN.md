# Volaura — Comprehensive Test Plan
**Version:** 1.0 | **Date:** 2026-03-26 | **Coverage target:** 90%+

---

## Test Infrastructure

| Layer | Framework | Runner | Location |
|-------|-----------|--------|----------|
| Backend unit/integration | pytest + httpx AsyncClient | `python -m pytest tests/` | `apps/api/tests/` |
| Frontend component | Vitest + @testing-library/react | `pnpm test` | `apps/web/src/**/*.test.tsx` |
| Frontend E2E | Playwright (future) | `npx playwright test` | `apps/web/e2e/` |

**Known issue:** Vitest crashes on Node v24 + Windows (pre-existing). Fix: use Node v20 LTS.
**Backend:** 275/286 passing. 11 pre-existing failures (mock pattern issues in old test files).

---

## PART 1 — BACKEND API TESTS

### Current Test Files

| File | Tests | Status |
|------|-------|--------|
| `test_sprint8_fixes.py` | 32 | ✅ All pass |
| `test_fixes_batch2.py` | 8 | ✅ All pass |
| `test_assessment_engine.py` | 33 | ✅ All pass (1 timing test updated) |
| `test_assessment_router.py` | 2 | ✅ All pass |
| `test_new_endpoints.py` | 24 | ✅ All pass |
| `test_swarm_council_p0.py` | 40+ | ✅ All pass |
| `test_auth.py` | 7 | ✅ All pass |
| `test_llm_mock.py` | 6 | ✅ All pass |
| `test_profiles.py` | varies | ✅ All pass |
| `test_security.py` | varies | ⚠️ 1 pre-existing fail |
| `test_smoke_assessment.py` | 3 | ⚠️ 3 pre-existing fails (KeyError raw_score) |

### Checklist — Every Endpoint

#### AUTH `/api/auth/`
- [x] POST /register → 201 + user created
- [x] POST /register → 400 if email taken
- [x] POST /login → 200 + JWT token
- [x] POST /login → 401 if wrong password
- [x] GET /me → 200 with valid token
- [x] GET /me → 401 without token

#### PROFILES `/api/profiles/`
- [x] POST /me → 201 + profile created + embedding triggered
- [x] GET /me → 200 own profile
- [x] PUT /me → 200 profile updated
- [ ] GET /{username} → 200 public profile
- [ ] GET /{username} → 404 if nonexistent
- [ ] POST /{id}/verification-link → 201 + token
- [ ] POST /{id}/verification-link → 403 if requesting for other user (CRIT-02)

#### ASSESSMENT `/api/assessment/`
- [x] POST /start → 201 session created
- [x] POST /answer → next question returned
- [x] POST /answer → BARS evaluation for open-ended
- [x] POST /complete/{id} → AURA upserted
- [x] POST /complete/{id} → anti-gaming applied
- [x] GET /results/{id} → stored data returned (no re-run)
- [x] POST /{id}/coaching → tips returned
- [x] POST /{id}/coaching → fallback tips on Gemini failure
- [x] POST /{id}/coaching → cached on second call
- [x] POST /{id}/coaching → 401 without auth
- [x] POST /{id}/coaching → 404 other user's session

#### AURA `/api/aura/`
- [ ] GET /me → 200 with score
- [ ] GET /me → 404 if no score yet
- [ ] GET /{id} → 200 public profile
- [ ] GET /{id} → 404 for hidden (identical to nonexistent — CRIT-04)
- [ ] GET /me/explanation → evaluation logs
- [ ] PATCH /me/visibility → visibility updated
- [ ] PATCH /me/visibility → 429 if rate limited
- [ ] POST /me/sharing → permission granted
- [ ] POST /me/sharing → 404 if org doesn't exist (HIGH-05)

#### BADGES `/api/badges/`
- [x] GET /{id}/credential → Open Badges 3.0 JSON
- [x] GET /{id}/credential → 422 invalid UUID
- [x] GET /{id}/credential → 404 hidden AURA
- [ ] GET /issuer → issuer metadata

#### LEADERBOARD `/api/leaderboard`
- [x] GET / → 200 public, no auth needed
- [x] GET / → entries have rank, display_name, total_score, badge_tier
- [x] GET / → rank 11+ names anonymized
- [x] GET /?period=weekly → accepted
- [x] GET / → hidden profiles excluded
- [x] GET / → empty list if no data

#### PUBLIC STATS `/api/stats/public`
- [x] GET / → 200, no auth needed
- [x] GET / → has total_volunteers, total_assessments, total_events, avg_aura_score
- [x] GET / → all values numeric >= 0
- [x] GET / → avg rounded to 1 decimal

#### ORGANIZATIONS `/api/organizations/`
- [ ] GET / → list public orgs
- [ ] POST / → create org
- [ ] GET /me → my org
- [ ] GET /{id} → public org detail
- [ ] POST /search/volunteers → semantic search

#### EVENTS `/api/events/`
- [ ] GET / → list public events
- [ ] GET /{id} → event detail
- [ ] POST / → create event (org owner)
- [ ] POST /{id}/register → register for event
- [ ] POST /{id}/checkin → check in volunteer
- [ ] POST /{id}/rate/volunteer → rate event

#### ACTIVITY `/api/activity/`
- [x] GET /me → activity feed
- [x] GET /stats/me → dashboard stats

#### VERIFICATION `/api/verify/`
- [ ] GET /{token} → valid token returns volunteer info
- [ ] GET /{token} → 404 expired/used token
- [ ] POST /{token} → rating submitted + AURA updated

#### DISCOVERY `/api/volunteers/discovery`
- [ ] GET → returns paginated results
- [ ] GET → no auth required
- [ ] GET → hidden profiles excluded
- [ ] GET?competency=communication → filtered

---

## PART 2 — FRONTEND COMPONENT TESTS

### Existing Tests (19 tests — all should pass on Node v20)

| File | Tests | Coverage |
|------|-------|----------|
| `competency-card.test.tsx` | 5 | render, toggle, aria |
| `mcq-options.test.tsx` | 5 | A-D labels, select, disabled, aria |
| `progress-bar.test.tsx` | 3 | percentage, 0%, cap 100% |
| `login.test.tsx` | 5 | form, loading, error, redirect, open-redirect |
| `stats-row.test.tsx` | 5 | 3 cards, streak, events, labels |

### New Tests (created this session)

| File | Tests | Coverage |
|------|-------|----------|
| `radar-chart.test.tsx` | 9 | full/partial/empty data, 8 labels, tiers, sizes |
| `activity-feed.test.tsx` | 12 | empty state, items, types, count, locale links |
| `badge-display.test.tsx` | 14 | all 5 tiers, aria, elite label |
| `auth-flows.test.tsx` | 13 | forgot-password, signup, error states |

### Test Checklist — Every UI Element

#### Buttons
- [ ] Every CTA button has accessible label (aria-label or text content)
- [ ] Loading state shows spinner + disables button
- [ ] Destructive actions have confirmation step
- [ ] Share buttons copy/open correct URLs
- [x] Submit buttons disabled until form valid

#### Forms
- [x] Login: email validation, password required
- [x] Signup: username pattern (3-30 chars), all fields validated
- [ ] Create Event: end > start date, bilingual titles required
- [ ] Create Org: name required
- [ ] Settings: display name, visibility
- [ ] Onboarding: 3-step progression, API call on finish
- [ ] Forgot Password: email format validation
- [ ] Reset Password: match + length validation

#### Charts & Visualizations
- [x] Radar chart: 8 spokes, partial data, empty
- [x] Badge tier: all 5 tiers render correct color/label
- [ ] Impact ticker: numbers animate, fallback on API fail
- [ ] Competency breakdown bars: proportional widths
- [ ] Stats row: 3 values render correctly

#### Navigation & Routing
- [ ] Sidebar: all nav links present + accessible
- [ ] Active state: current page highlighted
- [ ] Language switcher: EN ↔ AZ toggles correctly
- [ ] Auth guard: unauthenticated → redirect to /login
- [ ] All 23 page routes return pages (no 404s)

#### i18n
- [ ] EN: all t() keys resolve without [MISSING]
- [ ] AZ: all t() keys resolve without [MISSING]
- [ ] AZ special chars render: ə ğ ı ö ü ş ç
- [ ] AZ text doesn't overflow layouts (20-30% longer)

#### Accessibility (WCAG 2.1 AA)
- [ ] All images have alt text
- [ ] All icon buttons have aria-label
- [ ] All forms have label↔input association
- [ ] Error messages use role="alert"
- [ ] Loading states use aria-busy="true"
- [ ] Color contrast: 4.5:1 normal, 3:1 large text
- [ ] Keyboard: Tab navigates all interactive elements
- [ ] Keyboard: Enter/Space activates buttons
- [ ] Focus visible on all focusable elements

#### Mobile Responsiveness (375px, 768px, 1024px)
- [ ] No horizontal scroll on any page at 375px
- [ ] Touch targets minimum 44×44px
- [ ] Sidebar collapses on mobile
- [ ] Assessment flow usable on mobile
- [ ] Charts readable on small screens

#### Animations (Framer Motion)
- [ ] AURA score count-up animation completes
- [ ] Badge reveal animation fires on results
- [ ] Radar chart draws in on mount
- [ ] Page transitions don't cause layout shift
- [ ] Animations respect `prefers-reduced-motion`

#### Colors & Design
- [ ] Platinum: shimmer/silver gradient
- [ ] Gold: gold/amber gradient
- [ ] Silver: silver/gray gradient
- [ ] Bronze: bronze/copper gradient
- [ ] None tier: muted gray
- [ ] Error states: red/rose
- [ ] Warning states (gaming flags): amber/yellow
- [ ] Success states: green
- [ ] Dark theme consistent across all pages

---

## PART 3 — ASSESSMENT FLOW (End-to-End Checklist)

Manual verification until Playwright is set up:

### Happy Path
- [ ] Start assessment → competency selector loads
- [ ] Select competency → POST /assessment/start fires
- [ ] Question renders with correct type (MCQ/open-text)
- [ ] Answer MCQ → next question loads
- [ ] Answer open-text → BARS evaluation runs (server-side)
- [ ] Progress bar increments
- [ ] Timer visible and counting
- [ ] After 5-20 questions → results redirect
- [ ] Results show: score, badge tier, radar chart
- [ ] Gaming flags shown if any (amber warning)
- [ ] Share buttons visible
- [ ] Coaching tips accessible (POST /coaching)

### Edge Cases
- [ ] Network error during answer → retry option shown
- [ ] Session expired → redirect to login
- [ ] Assessment for already-assessed competency → existing session found or new started
- [ ] User answers < min questions → CAT stops at SE threshold
- [ ] All answers wrong → low score shown (not crash)
- [ ] All answers correct → high score shown (not crash)

---

## PART 4 — SECURITY TEST CHECKLIST

- [x] JWT required for protected endpoints (401 without token)
- [x] Rate limits on assessment (3 starts/hour, 60 answers/hour)
- [x] Rate limits on LLM endpoints (30/hour)
- [x] UUID validation on badge credential endpoint (422 on garbage)
- [x] Hidden AURA → identical 404 to nonexistent (no enumeration)
- [x] Theta not exposed in API responses (CRIT-03)
- [x] Raw score not exposed in API responses
- [x] Model names masked in evaluation logs (CRIT-05)
- [x] Org existence validated before sharing permission (HIGH-05)
- [x] Server-side timing for assessment questions (HIGH-03)
- [x] Optimistic locking on answer submission (HIGH-01)
- [ ] SQL injection: search queries are parameterized
- [ ] XSS: user input sanitized before storage
- [ ] CSRF: Supabase tokens validate origin
- [ ] Open redirect: /callback page validates redirect URL
- [x] CRIT-02: Cannot create verification link for other user

---

## PART 5 — PRODUCTION READINESS CHECKLIST

### Backend
- [x] All 43 endpoints implemented
- [x] Rate limiting on all endpoints
- [x] Structured JSON errors (no stack traces)
- [x] loguru logging (no print() statements)
- [x] Pydantic v2 validation on all inputs
- [x] RLS on all Supabase tables
- [x] CORS configured
- [x] Health endpoint live
- [x] Coaching endpoint + migration applied
- [x] Leaderboard endpoint live
- [x] Public stats endpoint live

### Frontend
- [x] Zero 404 navigation links (onboarding + notifications pages created)
- [x] Leaderboard wired to real API (no mock data)
- [x] Impact ticker wired to real API
- [x] Profile metrics wired to real API
- [x] Assessment results show gaming flags
- [x] Settings page complete (account + privacy + sign out)
- [x] Forgot/reset password complete
- [x] Organization detail page created
- [ ] Evaluation log UI ("Why this score?" — Sprint 9B)
- [ ] Coaching tips UI (Sprint 9B)
- [ ] API codegen (pnpm generate:api — Sprint 9C)
- [ ] E2E Playwright tests (Sprint 10)
- [ ] Vitest Node v20 compatibility fix

### Database
- [x] Migration 000027: coaching_note column applied to production
- [x] All 26 prior migrations applied
- [x] HNSW index on embeddings
- [x] GIN index on competency_scores

---

## RUNNING TESTS

```bash
# Backend — all tests
cd apps/api && python -m pytest tests/ --ignore=tests/test_e2e_assessment.py -v

# Backend — new endpoints only
cd apps/api && python -m pytest tests/test_new_endpoints.py -v

# Backend — sprint 8 fixes
cd apps/api && python -m pytest tests/test_sprint8_fixes.py -v

# Frontend — requires Node v20
nvm use 20
cd apps/web && pnpm test

# Frontend — single file
cd apps/web && npx vitest run src/components/aura/radar-chart.test.tsx
```
