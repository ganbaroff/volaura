# Volaura — Production Readiness Plan
**Version:** 1.0 | **Date:** 2026-03-26 | **Author:** CTO (Claude)
**Status:** EXECUTING — Sprint 9 + Sprint 10

---

## Executive Summary

Full audit of all 23 frontend pages, 43 backend endpoints, and all components.
Plan covers: critical 404 fixes, real data wiring, missing features, and comprehensive testing.

---

## CRITICAL BLOCKERS (must fix before any users see the app)

| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| C1 | `/onboarding` → 404 after signup | Every new user sees 404 | Create onboarding page |
| C2 | `/notifications` → 404 from nav | Broken navigation | Create notifications page |
| C3 | Forgot/Reset password — stubs | Can't recover account | Complete Supabase auth flow |
| C4 | No leaderboard API endpoint | Fake data shown | Add `/api/leaderboard` endpoint |
| C5 | No public stats API | Impact ticker = fake numbers | Add `/api/stats/public` endpoint |

---

## SPRINT 9A — Critical Fixes (Session 34–35)

### 9A-01: Onboarding Page
- Route: `/[locale]/(dashboard)/onboarding/page.tsx`
- After signup, user lands here to complete profile
- Steps: Username → Display Name → Location → Languages → First competency choice
- On complete: redirect to `/dashboard`
- Backend: POST `/api/profiles/me` already exists

### 9A-02: Notifications Page
- Route: `/[locale]/(dashboard)/notifications/page.tsx`
- Types: AURA update, badge earned, event registration, assignment, verification request
- Actions: mark as read (individual + all)
- Backend: needs `/api/notifications` endpoint OR use activity feed

### 9A-03: Forgot Password (complete)
- Current: form exists but no logic
- Fix: call `supabase.auth.resetPasswordForEmail(email)`
- Add success state ("Check your email")
- Reset page: call `supabase.auth.updateUser({ password })`

### 9A-04: Backend — Leaderboard Endpoint
- `GET /api/leaderboard?period=weekly|monthly|all_time&limit=50`
- Query: aura_scores JOIN profiles ORDER BY total_score DESC
- Anonymize: "First L." format for non-top-10
- Rate limit: RATE_DISCOVERY (10/min)
- Migration: materialized view for performance

### 9A-05: Backend — Public Stats Endpoint
- `GET /api/stats/public`
- Returns: total_volunteers, avg_aura_score, total_assessments, total_events
- Cache: 5 min (in-memory, acceptable for Railway)
- No auth required

### 9A-06: Backend — Coaching Endpoint
- `POST /api/assessment/{session_id}/coaching`
- Input: session results + competency scores
- Process: Gemini 2.5 Flash generates personalized recommendations
- Output: 3 specific improvement tips per competency scored below 70
- Cache: store in assessment_sessions.coaching_note column (migration 000027)
- Timeout: 15s (same as BARS)

---

## SPRINT 9B — Real Data Wiring (Session 35–36)

### 9B-01: Profile Page — Real Metrics
- Wire impact-metrics.tsx to real API data
- Use: stats from `/api/activity/stats/me`
- Map: events_attended, verified_skills (from aura_scores), total_hours_est

### 9B-02: Profile Page — Activity Timeline
- Wire activity-timeline.tsx to `/api/activity/me`
- Map: assessment completions, badge earns, event participations
- Show: last 10 items, date-formatted

### 9B-03: Leaderboard — Real API
- Replace `IS_PREVIEW = true` with `useLeaderboard()` hook
- Hook: calls `GET /api/leaderboard?period=weekly`
- Period tabs: weekly / monthly / all_time (query param)
- Skeleton loading state

### 9B-04: Landing Impact Ticker — Real API
- Replace `getMockImpactStats()` with `usePublicStats()` hook
- Calls: `GET /api/stats/public`
- Fallback: show cached numbers if API fails (graceful)

### 9B-05: Assessment Results — Gaming Flags
- If `gaming_flags.length > 0`, show warning banner:
  "Your score was adjusted. Reason: [flag description]"
- Map flag codes to human-readable AZ/EN text
- Non-intrusive: collapsible, amber color

### 9B-06: Assessment Results — Evaluation Log UI
- "Why this score?" expandable section per competency
- Shows: concept breakdown, AI reasoning, BARS criteria
- Fetch from: `GET /api/aura/me/explanation`
- Collapsible cards, Framer Motion animation

### 9B-07: Organization Detail Page
- Route: `/[locale]/(public)/organizations/[id]/page.tsx`
- Shows: org name, description, events, volunteer count
- CTA: "Apply to volunteer" (if logged in)
- Backend: `GET /api/organizations/{org_id}` exists

---

## SPRINT 9C — Quality & Completeness (Session 36–37)

### 9C-01: Settings Page
- Account management: display name, username, location, languages
- Notification preferences (toggle)
- Privacy settings: AURA visibility toggle (public/badge_only/hidden)
- Danger zone: delete account (calls Supabase auth.admin.deleteUser)

### 9C-02: API Code Generation
- Run: `pnpm generate:api` (generates from openapi.json)
- Replace all 7 TODO comments in hooks/
- Update: use-aura, use-dashboard, use-profile, use-events, use-organizations
- Remove: lib/api/client.ts (replaced by generated client)

### 9C-03: Events Detail Page
- Route: `/[locale]/(public)/events/[id]/page.tsx`
- Shows: event details, registration button, capacity, min AURA requirement
- CTA: Register (if logged in + AURA meets minimum)
- Backend: `GET /api/events/{event_id}` exists

### 9C-04: Expert Verifications on Profile
- Wire expert-verifications.tsx to real data
- Fetch: completed expert_verifications from API
- Show: verifier name, competency, rating (stars), date

---

## SPRINT 10 — COMPREHENSIVE TESTING PLAN

### Frontend Unit Tests (Target: 100+ tests)

**Assessment Flow Tests:**
```
- test: competency selection (min 1 required)
- test: assessment start → API call fired
- test: question renders (MCQ + open-text + rating-scale)
- test: MCQ option selection updates state
- test: submit button disabled until answer selected
- test: timer counts down and fires callback
- test: progress bar updates on answer
- test: results page renders with real data
- test: gaming flag warning shown if flags non-empty
- test: badge tier displayed correctly (all 5 tiers)
- test: radar chart renders with 8 competency spokes
- test: share buttons visible on results
- test: "Why this score?" expandable section
```

**Auth Flow Tests:**
```
- test: login form validates email format
- test: login form validates password required
- test: login success → redirect to /dashboard
- test: login failure → error message shown
- test: signup validates username (3-30 chars)
- test: signup validates password strength
- test: signup success → redirect to /onboarding
- test: forgot password form sends email
- test: reset password validates password match
```

**Navigation Tests:**
```
- test: all nav links render
- test: active nav item highlighted
- test: logout clears session
- test: protected route redirects unauthenticated users
- test: language switcher toggles EN/AZ
```

**Dashboard Tests:**
```
- test: dashboard shows AURA score widget
- test: dashboard shows activity feed
- test: dashboard shows stats row
- test: empty state shown if no assessments
- test: error state with retry button
```

**Profile Tests:**
```
- test: public profile renders name and AURA
- test: hidden profile returns 404
- test: activity timeline renders items
- test: impact metrics show real numbers
- test: skill chips render per competency
```

**Leaderboard Tests:**
```
- test: renders top 10 list
- test: period tabs switch data
- test: current user highlighted
- test: skeleton loader shown during fetch
```

**Forms Tests:**
```
- test: create event form validates all required fields
- test: create event end date must be after start date
- test: create event submits to API
- test: create org form validates name required
- test: settings form saves correctly
```

**Chart Tests:**
```
- test: radar chart renders with 8 data points
- test: radar chart handles missing competencies (partial data)
- test: badge tier badge renders correct color
- test: impact ticker shows numbers
```

**i18n Tests:**
```
- test: all EN keys render without [MISSING]
- test: AZ keys render without [MISSING]
- test: language switch re-renders all strings
- test: AZ special characters render: ə ğ ı ö ü ş ç
```

**Accessibility Tests:**
```
- test: all buttons have accessible labels
- test: all forms have associated labels
- test: error messages use role="alert"
- test: loading states use aria-busy
- test: focus management on modal open/close
- test: color contrast meets WCAG AA (4.5:1)
- test: keyboard navigation (Tab, Enter, Space)
- test: screen reader text for icons
```

**Mobile Responsiveness Tests:**
```
- test: 375px viewport — no horizontal scroll
- test: 768px viewport — tablet layout
- test: 1024px viewport — desktop layout
- test: touch targets minimum 44x44px
- test: sidebar collapses on mobile
```

### Backend API Tests (Target: 80+ tests)

**Assessment Engine Tests:**
```
- test: POST /assessment/start creates session
- test: POST /assessment/answer returns next question
- test: POST /assessment/answer runs BARS for open-ended
- test: POST /assessment/complete runs anti-gaming
- test: POST /assessment/complete upserts AURA
- test: GET /assessment/results returns stored data
- test: duplicate session start returns existing
- test: answer to completed session returns 400
- test: answer timing stored server-side
```

**AURA Score Tests:**
```
- test: GET /aura/me returns score for authenticated user
- test: GET /aura/{id} returns 404 for hidden profile
- test: PATCH /aura/me/visibility updates correctly
- test: POST /aura/me/sharing validates org exists
```

**Profile Tests:**
```
- test: POST /profiles/me creates profile + triggers embedding
- test: GET /profiles/{username} returns public profile
- test: PUT /profiles/me updates + re-embeds
- test: verification link has 7-day expiry
```

**Leaderboard Tests:**
```
- test: GET /leaderboard returns top 50 by score
- test: GET /leaderboard?period=weekly filters correctly
- test: non-top-10 names anonymized
```

**Public Stats Tests:**
```
- test: GET /stats/public returns counts
- test: no auth required
```

**Security Tests:**
```
- test: /api/aura/me without token → 401
- test: /api/assessment/start rate limit (3/hour)
- test: bad UUID in badges → 422
- test: hidden AURA → identical 404 to nonexistent
- test: theta not in API response (CRIT-03)
- test: raw_score not in API response
- test: SQL injection in search → sanitized
- test: oversized answer text → capped at 2000 chars
```

### End-to-End Tests (Playwright — Target: 15 flows)

```
Flow 1: New user signup → onboarding → first assessment → results
Flow 2: Login → AURA score page → share badge
Flow 3: Login → start assessment → answer all questions → see results
Flow 4: Login → view leaderboard → navigate to profile
Flow 5: Organization: create org → create event → register volunteer
Flow 6: Login → update visibility to hidden → verify 404 on public
Flow 7: Expert verification: create link → submit rating → AURA updates
Flow 8: Password reset: forgot → email → reset → login
Flow 9: Language switch: EN → AZ → verify all strings translate
Flow 10: Mobile: complete assessment on 375px viewport
Flow 11: Profile sharing: copy link → open in incognito
Flow 12: API codegen: types match actual API responses
Flow 13: Anti-gaming: robotic timing → flag shown in results
Flow 14: Badge credential: fetch Open Badges 3.0 JSON
Flow 15: Coaching: complete assessment → view recommendations
```

---

## PRODUCTION CHECKLIST

### Frontend
- [ ] No `console.log` in production code
- [ ] No hardcoded strings (all via `t()`)
- [ ] No `any` TypeScript types
- [ ] No `IS_PREVIEW = true` flags
- [ ] All routes return pages (no 404s)
- [ ] Error boundaries on all pages
- [ ] Loading states on all data fetches
- [ ] Empty states on all lists
- [ ] Meta tags (title, description, OG) on all pages
- [ ] PWA manifest and service worker
- [ ] HTTPS enforced (Vercel handles)

### Backend
- [ ] All endpoints have rate limiting
- [ ] All user inputs validated (Pydantic)
- [ ] RLS policies on all tables
- [ ] No `print()` statements (loguru only)
- [ ] Health check endpoint working
- [ ] Environment variables documented
- [ ] No debug endpoints in production

### Database
- [ ] All migrations applied
- [ ] Seed data for competencies + questions
- [ ] HNSW index on embeddings
- [ ] GIN index on competency_scores JSONB
- [ ] Backups enabled (Supabase handles)

### Monitoring
- [ ] loguru structured logging
- [ ] Railway health check configured
- [ ] Error alerting via Telegram bot

---

## PRIORITY ORDER FOR THIS SESSION

1. **IMMEDIATE** (30 min): Onboarding page + Notifications page
2. **HIGH** (1 hr): Backend endpoints (leaderboard, stats, coaching)
3. **HIGH** (1 hr): Profile real data + results gaming flags
4. **MEDIUM** (1 hr): Evaluation log UI, org detail page
5. **MEDIUM** (1 hr): Settings page, forgot/reset password
6. **LOWER** (ongoing): API codegen, comprehensive test suite
