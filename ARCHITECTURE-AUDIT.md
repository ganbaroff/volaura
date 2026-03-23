# VOLAURA ARCHITECTURE AUDIT
**Date:** 2026-03-22
**Scope:** Complete system assessment against MEGA-PROMPT, ADRs, and API contracts
**Status:** RESEARCH ONLY — no modifications

---

## EXECUTIVE SUMMARY

**Overall Assessment:** 85% documented completeness. Strong foundational architecture (Supabase-first + FastAPI), comprehensive API contracts, and clear database schema. **Critical gaps identified in:**

1. **New features undocumented** (activity_log, volunteer_leagues, AURA Coach, impact metrics)
2. **Missing ADRs** (security, caching strategy, realtime design, monitoring)
3. **Incomplete API contracts** (Coach endpoint, volunteer_requests, event_ratings, advanced search)
4. **Supabase Realtime** not formally defined
5. **Definition of Done** missing for API endpoints
6. **Performance targets** not validated for scale (5000 users, 40K assessments, 200 events)

---

## 1. DATABASE SCHEMA COMPLETENESS

### ✅ TABLES FULLY DESIGNED

| Table | Status | Notes |
|-------|--------|-------|
| profiles | ✅ Complete | All fields, RLS, triggers |
| aura_scores | ✅ Complete | Current/history tracking, tiers |
| competency_scores | ✅ Complete | 8 competencies, weights, verification levels |
| assessments | ✅ Complete | Status tracking, IRT theta/SE fields |
| assessment_responses | ✅ Complete | BARS/MCQ/open_text scoring |
| organizations | ✅ Complete | Plans, verification, API keys |
| org_members | ✅ Complete | Role-based access (owner/admin/member) |
| events | ✅ Complete | Dynamic data, min_aura, required_competencies |
| event_registrations | ✅ Complete | Status tracking, org ratings |
| questions | ✅ Complete | All 3 types, i18n, IRT parameters |
| notifications | ✅ Complete | Bilingual, polymorphic type field |
| volunteer_embeddings | ✅ Complete | pgvector(768) for Gemini |
| referrals | ✅ Complete | Referral code, conversion tracking |
| badge_history | ✅ Complete | Tier changes with audit trail |
| volunteer_requests | ✅ Complete | Org requests specific volunteer |

### 🟡 NEW TABLES MENTIONED BUT NOT DESIGNED

**From project context:** "New features: activity_log table, volunteer_leagues, AURA Coach, impact metrics"

| Table | Status | Details |
|-------|--------|---------|
| activity_log | ⚠️ Missing | No schema, missing RLS policies, undefined triggers |
| volunteer_leagues | ⚠️ Missing | No schema, unclear relationship to events/aura_scores |
| aura_coach_sessions | ⚠️ Missing | No schema for Gemini coaching interactions |
| impact_metrics | ⚠️ Missing | No schema, unclear aggregation logic |

**Severity:** HIGH — These tables are core to product expansion but have zero design.

### RLS Policies

**Status:** ✅ Complete for existing tables
- All tables have RLS enabled
- Policies follow principle of least privilege
- RPC functions use SECURITY DEFINER for elevated access

**Issue:** No RLS policies defined for activity_log, volunteer_leagues, aura_coach_sessions, impact_metrics.

### Indexes

**Status:** ✅ Well-designed
- Leaderboard: composite on `aura_scores(composite_score DESC) WHERE is_current`
- Assessment lookup: `assessments(user_id, competency)`
- Notifications: `notifications(user_id, is_read, created_at DESC)`
- Vector search: IVFFlat on `volunteer_embeddings` with 100 lists (optimal for <100K rows)

**Missing:** No indexes for new tables.

### RPC Functions

**Status:** ✅ 2/3 core functions designed

| Function | Status | Notes |
|----------|--------|-------|
| match_volunteers() | ✅ Complete | Vector search with min_aura filter, SECURITY DEFINER |
| get_leaderboard() | ✅ Complete | Pagination, ranking, location filter |
| calculate_aura_score() | ⚠️ Missing | Business logic defined in ADR-005, but no DB function |
| recalculate_event_performance() | ⚠️ Missing | Needed for batch AURA updates |

**Missing Functions:** No RPC for event performance calculation (must run post-event to update AURA scores).

---

## 2. API CONTRACT COMPLETENESS

### ✅ FULLY DEFINED ENDPOINTS

**Health & System:** 1/1
- GET /health

**Authentication:** 0/4 (delegated to Supabase)
- POST /auth/v1/signup
- POST /auth/v1/token
- POST /auth/v1/token (refresh)
- GET /auth/v1/user

**Profiles:** 4/5
- GET /api/v1/profiles/me ✅
- PATCH /api/v1/profiles/me ✅
- GET /api/v1/profiles/{username} ✅
- POST /api/v1/profiles/me/avatar ✅
- DELETE /api/v1/profiles/me ✅

**Assessment:** 5/5
- POST /api/v1/assessments/start ✅
- GET /api/v1/assessments/{id} ✅
- GET /api/v1/assessments/{id}/next-question ✅
- POST /api/v1/assessments/{id}/answers ✅
- POST /api/v1/assessments/{id}/complete ✅
- GET /api/v1/assessments/history ✅

**AURA Scores:** 2/4
- GET /api/v1/scores/me ✅
- GET /api/v1/scores/leaderboard ⚠️ (defined but needs pagination, filtering)
- GET /api/v1/scores/{user_id} ⚠️ (public profile scores)
- GET /api/v1/scores/history ❌ (missing)

### 🟡 PARTIALLY DEFINED ENDPOINTS

**Events:** 3/6
- GET /api/v1/events ⚠️ (filters, pagination defined, needs min_aura eligibility check)
- GET /api/v1/events/{id} ❌
- POST /api/v1/events (org admin only) ❌
- PATCH /api/v1/events/{id} (org admin only) ❌
- DELETE /api/v1/events/{id} (org admin only) ❌
- GET /api/v1/events/{id}/volunteers (who can attend) ❌

**Event Registration:** 2/4
- POST /api/v1/events/{id}/register ❌
- DELETE /api/v1/events/{id}/register ❌
- PATCH /api/v1/event_registrations/{id} (update status) ❌
- GET /api/v1/event_registrations (user's) ❌

### ❌ COMPLETELY MISSING ENDPOINTS

**Volunteer Requests** (org → volunteer)
- POST /api/v1/organizations/{org_id}/volunteer_requests
- GET /api/v1/volunteer_requests (user's incoming)
- PATCH /api/v1/volunteer_requests/{id} (accept/decline)

**Event Ratings** (org rates volunteer post-event)
- POST /api/v1/event_registrations/{id}/rating
- GET /api/v1/event_registrations/{id}/rating

**Search / Volunteer Matching**
- POST /api/v1/organizations/search-volunteers (semantic search + filters)
- GET /api/v1/volunteers/recommended (for given event)

**AURA Coach** (Gemini-powered coaching)
- POST /api/v1/aura-coach/start-session
- GET /api/v1/aura-coach/sessions/{id}
- POST /api/v1/aura-coach/sessions/{id}/message
- GET /api/v1/aura-coach/insights

**Organizations**
- GET /api/v1/organizations (verified orgs list)
- POST /api/v1/organizations (new org signup)
- PATCH /api/v1/organizations/{id} (org admin)
- GET /api/v1/organizations/{id}/members
- POST /api/v1/organizations/{id}/members (invite)
- DELETE /api/v1/organizations/{id}/members/{user_id}

**Notifications**
- GET /api/v1/notifications
- PATCH /api/v1/notifications/{id} (mark read)
- DELETE /api/v1/notifications/{id}
- POST /api/v1/notifications/subscribe (Realtime)

**Referrals**
- GET /api/v1/referrals/stats
- POST /api/v1/referrals/redeem/{code}

**Leaderboards (advanced)**
- GET /api/v1/leaderboard/by-competency/{competency}
- GET /api/v1/leaderboard/by-event/{event_id}
- GET /api/v1/leaderboard/trending (7-day gainers)

**Activity Feed**
- GET /api/v1/activity (global feed)
- GET /api/v1/activity/following (for social features)

**Severity:** HIGH — Missing ~25 endpoints critical to production launch.

---

## 3. SUPABASE REALTIME DESIGN

### Current Status: ⚠️ NOT FORMALLY DESIGNED

**What's Mentioned:**
- ADR-001 references "real-time leaderboard"
- MEGA-PROMPT mentions "live volunteer counters" for events
- STATE-MANAGEMENT.md shows no Realtime patterns

**Missing:**
1. **Realtime Subscription Schema** — which tables/events trigger subscriptions?
   - event_registrations (capacity update)
   - aura_scores (leaderboard changes)
   - notifications (new messages)
   - activity_log (global feed)

2. **Subscription Patterns** — no code examples for:
   - Leaderboard live updates
   - Event registration count
   - Notification badges
   - Activity feed pagination + realtime

3. **Channel Configuration** — no broadcast/presence channel design

4. **Client-side Handling** — no Zustand store for Realtime state

**Recommendation:** Document a Supabase Realtime ADR with:
- Table subscriptions (LISTEN/NOTIFY)
- Presence channels (leaderboard viewers, event attendees)
- Broadcast channels (live event updates)
- Client reconnection logic
- Message queuing for offline scenarios

---

## 4. AURA CALCULATION — EXECUTION MODEL UNDEFINED

### ✅ Formula Defined (ADR-005)

```
AURA = clamp(Σ(competency_score_i × weight_i × verification_multiplier_i) × reliability_factor, 0, 100)
```

**Competency Weights:** ✅ Finalized (sum = 1.00)
**Reliability Factor:** ✅ Defined (0.85–1.00 based on std deviation)
**Verification Multipliers:** ✅ Defined (1.00–1.25)
**Event Performance:** ✅ Defined (weighted rating + attendance + recency)

### ❌ EXECUTION MODEL UNDEFINED

**Critical Questions:**

1. **Where does calculation run?**
   - Backend API endpoint? ✅ (documented for submit_answer)
   - Supabase Edge Function? ❌
   - pg_cron batch job? ❌
   - Combination?

2. **When is it recalculated?**
   - On every assessment completion? (1 competency)
   - Full recalc nightly? (all 8 competencies)
   - On event attendance update?
   - On org attestation?

3. **What triggers AURA update?**
   - Event registration status changes?
   - Org rates volunteer?
   - Peer verification arrives?

4. **Caching strategy?**
   - aura_scores.is_current = TRUE/FALSE?
   - How long before re-query?
   - Invalidation logic?

**Missing:** Database function for batch recalculation, Edge Function for real-time calculation, or FastAPI endpoint contract.

### Reliability Factor Implementation

**Issue:** Std deviation calculation undefined
- Do we calculate per-competency std dev across all assessment responses?
- Rolling 6-month window?
- Minimum N responses required?

**Example gap:** User has 1 communication assessment → std dev = 0 → factor = 1.00. Is this correct?

---

## 5. GEMINI INTEGRATION ASSESSMENT

### ✅ Defined Usage

| Feature | Status | Notes |
|---------|--------|-------|
| Open text evaluation | ✅ | evaluate_with_llm() service in ADR-004 |
| Embedding generation | ✅ | vector(768) for Gemini text-embedding-004 |
| Fallback to OpenAI | ✅ | Mentioned in CLAUDE.md rules |

### ❌ Missing

1. **AURA Coach Endpoint** — completely undefined
   - No prompt design
   - No session storage schema
   - No message format
   - No caching for repeated questions

2. **LLM Evaluation Caching** — "Cache at submit_answer time" (ADR-004:229)
   - Where is cache stored? (assessment_responses table?)
   - TTL? (lifetime or 6 months?)
   - Re-evaluation allowed?

3. **Cost Estimation**
   - Free tier: $800 until December 2026
   - 200 users × 8 competencies = 1,600 assessments
   - Assume 5 open text responses per assessment = 8,000 evaluations/month
   - Gemini 2.5 Flash: ~0.0375 per 1M tokens
   - Estimate: 100 tokens/evaluation = **~$0.03/month** ✅ (negligible)

4. **Error Handling for LLM Failure**
   - Fallback to pending_review? ✅ (ADR-004:194)
   - Who reviews pending? (admin interface missing)
   - SLA for manual review?

### Recommendation

- Document Coach feature (prompt, session schema, message format)
- Define LLM evaluation caching table/TTL
- Create admin dashboard for pending_review queue
- Add rate limiting per user (e.g., 1 assessment per day to prevent abuse)

---

## 6. PERFORMANCE AT SCALE

### Scale Target
- Users: 200 day 1 → 5,000 in 6 months
- Assessments: 1,600 → 40,000 (8 per user × 5000)
- Questions answered: 8,000 → 200,000 (5 per assessment)
- Events: ~10 → 200
- Event registrations: N/A → ~5,000

### Database Load Estimates

**Query Performance Targets:**

| Query | Frequency | Size | Target Latency | Risk |
|-------|-----------|------|-----------------|------|
| Leaderboard (top 50) | 10/sec | 50 rows | <50ms | ✅ (index on composite_score DESC) |
| Volunteer search (vector) | 1/sec | 20 results | <100ms | 🟡 (IVFFlat with 100 lists; might need tuning) |
| Assessment next question | 100/sec | 1 row | <10ms | ✅ (questions table, small) |
| AURA calculation | ~0.2/sec | 80 rows (8 × 10 users) | <100ms | 🟡 (requires index on user_id + is_current) |
| Event list (with filters) | 5/sec | 20 rows | <50ms | 🟡 (no index on status + date_start) |

**Missing Indexes:**
```sql
-- For event filtering
CREATE INDEX idx_events_status_date ON events(status, date_start DESC);

-- For AURA batch recalculation
CREATE INDEX idx_aura_scores_user_current ON aura_scores(user_id, is_current);

-- For activity feed pagination
CREATE INDEX idx_activity_log_user_created ON activity_log(user_id, created_at DESC);
```

### Supabase Connections

**Concern:** Free tier allows 40 concurrent connections.
- FastAPI on Railway: 1-10 workers
- Frontend browser clients: 100-500 concurrent
- **Gap:** Browser clients will exceed free tier limit during peak (launch event, COP29)

**Recommendation:**
- Upgrade to Pro tier immediately (100 connections, ~$25/mo)
- Or implement connection pooling via PgBouncer (not available in Supabase free)

### Caching Strategy (Not Defined)

**Missing:**
- TanStack Query cache invalidation policy
- Response-level caching (HTTP Cache-Control headers)
- Leaderboard cache TTL (refresh every 60s? 300s?)
- Profile cache TTL
- Assessment history cache

**Recommendation:** Document caching strategy per endpoint:
- Static (profiles): Cache-Control: public, max-age=3600
- Semi-static (aura_scores): public, max-age=60
- Dynamic (leaderboard): public, max-age=10
- User-specific (scores/me): private, max-age=30

---

## 7. MISSING ARCHITECTURAL DECISION RECORDS (ADRs)

### Current ADRs: 5/10

| ADR | Status | Impact |
|-----|--------|--------|
| ADR-001: System Architecture | ✅ | Clear Supabase + FastAPI split |
| ADR-002: Database Schema | ✅ | Comprehensive table design |
| ADR-003: Auth & Verification | ⚠️ Partial | Magic link + OAuth defined; verification levels incomplete |
| ADR-004: Assessment Engine | ✅ | Three question types, CAT/IRT roadmap |
| ADR-005: AURA Scoring | ✅ | Formula defined; execution model missing |

### Missing Critical ADRs

1. **ADR-006: Caching Strategy**
   - Client-side (TanStack Query): invalidation policy, stale-while-revalidate
   - Server-side (Redis? Edge cache?): what to cache, TTL
   - Database-level: view materialization, pg_cron refresh

2. **ADR-007: Supabase Realtime**
   - Table subscriptions vs broadcast channels
   - Presence for concurrent users
   - Reconnection logic
   - Message ordering and deduplication

3. **ADR-008: Security Hardening**
   - Rate limiting implementation (FastAPI middleware, Supabase Auth)
   - CSRF protection (SameSite cookies defined but not edge cases)
   - XSS mitigation (CSP headers defined but not tested)
   - CORS policy (not mentioned)
   - SQL injection prevention (Supabase SDK handles, but validate)

4. **ADR-009: Monitoring & Observability**
   - Sentry integration (mentioned in ADR-001, no contract)
   - Loguru structured logging (backend only; frontend?)
   - Metrics: what to track, dashboards, alerting
   - Error budget and SLOs

5. **ADR-010: New Features (Activity Log, Leagues, Coach)**
   - Schema design for activity_log, volunteer_leagues
   - AURA Coach architecture (Gemini prompt, session management)
   - Impact metrics aggregation and display
   - User onboarding and notification strategy

---

## 8. STATE MANAGEMENT ASSESSMENT

### ✅ Architecture Well-Defined

**Layers:**
1. Server State: TanStack Query ✅
2. Client State: Zustand ✅
3. Form State: React Hook Form + Zod ✅
4. URL State: searchParams ✅
5. Auth State: Supabase Auth synced to Zustand ✅

**Query Key Structure:** ✅ Hierarchical, enables granular invalidation

### 🟡 Missing Patterns

1. **Realtime State Sync**
   - No pattern for Supabase Realtime subscriptions in Zustand
   - Example: leaderboard live update → should emit event → Zustand store listens → updates

2. **Error State Management**
   - No Zustand store for global errors
   - Forms have error states, but no global error boundary integration

3. **Optimistic Updates**
   - Mutations shown, but no optimistic UI patterns
   - Example: "register for event" should optimistically update registered_count

4. **Offline Support**
   - STATE-MANAGEMENT.md says PWA offline for assessments
   - No Dexie.js integration patterns shown
   - No sync logic for offline answers → online

---

## 9. SECURITY & COMPLIANCE GAPS

### ✅ Defined

- JWT verification in FastAPI ✅
- RLS policies on all tables ✅
- HttpOnly cookies for tokens ✅
- CSRF via SameSite cookies ✅

### ⚠️ Partially Defined

- Rate limiting: 100 req/min (authenticated), 10 req/min (unauthenticated) — no implementation detail
- CORS policy: not mentioned
- Data deletion: soft-delete for accounts, but no data retention policy
- PII handling: no encryption for phone/sensitive fields

### ❌ Missing

1. **GDPR Compliance**
   - Right to be forgotten: soft-delete deletes in 90 days, but data?
   - Data portability endpoint missing
   - Consent management missing

2. **Abuse Prevention**
   - Assessment cheating detection (multiple high scores in short time?)
   - Referral spam (same referrer multiple times?)
   - Event registration abuse (same user multiple registrations?)

3. **Secret Management**
   - Gemini API key, Supabase JWT secret, Resend API key in .env
   - No secret rotation policy
   - No audit trail for API key usage

---

## 10. DEFINITION OF DONE FOR API ENDPOINTS

### Current Status: ❌ Not Defined

**Missing checklist for each endpoint:**
- [ ] Pydantic schema defined (request + response)
- [ ] Error codes enumerated with status codes
- [ ] Rate limiting documented
- [ ] RLS policy verified (if applicable)
- [ ] Response envelope (data + meta) matched
- [ ] Pagination documented (if applicable)
- [ ] i18n keys defined (error messages)
- [ ] TypeScript types generated (@hey-api/openapi-ts)
- [ ] TanStack Query hook created (query-keys.ts + useQuery)
- [ ] Integration test written
- [ ] OpenAPI schema auto-generated and validated

**Recommendation:** Create endpoint DoD template in DECISIONS.md

---

## 11. MISSING FEATURES DOCUMENTATION

### From Context: "New features before deploy"

**Activity Log** ❌ Completely undefined
- Schema: which events are logged? (assessment complete, event attended, badge earned, profile updated)
- Storage: events table with user_id, event_type, metadata JSONB, created_at?
- Privacy: are activity logs public? (user's own only, followers only, public?)
- Queryability: need index for timeline view

**Volunteer Leagues** ❌ Completely undefined
- What's a league? (grouping of volunteers by competency? by event? by AURA tier?)
- Schema: league_id, name, tier_threshold, volunteer_count, leader_id?
- Mechanics: do volunteers join leagues, or auto-assigned?
- Leaderboard: separate leaderboard per league?

**AURA Coach** ❌ Completely undefined
- Session model: coach_sessions table with user_id, created_at, messages JSONB?
- Coaching topics: which competencies can be coached?
- Prompt design: how does Gemini provide personalized coaching?
- UX: modal, page, or chat sidebar?

**Impact Metrics** ❌ Completely undefined
- What metrics? (events organized, volunteers mentored, badges awarded, lives impacted?)
- Aggregation: global, per-org, per-volunteer, per-competency?
- Display: dashboard, public profile, org portal?
- Real-time or batch calculated?

---

## 12. MISSING FRONTEND PATTERNS

### From MEGA-PROMPT, §MODULE 1

**Defined:** File structure, component taxonomy
**Missing:**
- Error boundary implementation
- Loading skeleton patterns
- Accessibility (WCAG 2.1 AA) validation checklist
- Animation spring configs usage across components
- Color scheme usage guide (oklch values)
- Responsive breakpoint usage patterns
- Form submission error handling
- Modal/dialog composition patterns
- Deep linking for assessment state (URL params for current question?)

---

## 13. DEPLOYMENT & INFRASTRUCTURE

### ✅ Defined

- Vercel (frontend): free tier with ISR
- Railway (backend): ~$8/mo, auto-scaling
- Supabase: free tier, upgradeable
- Gemini API: free tier until December, $0.03/month at scale

### ⚠️ Incomplete

- No deployment checklist beyond engineering/DEPLOY-CHECKLIST.md reference
- No environment variable management docs
- No database migration strategy for production
- No rollback plan
- No monitoring dashboard setup
- No log aggregation setup (Loguru configured but where are logs stored?)

---

## 14. TESTING STRATEGY

### Status: ⚠️ Mentioned but incomplete

**Defined:** TESTING-STRATEGY.md exists (not read in audit, but referenced)

**Likely gaps:**
- Unit test coverage targets
- E2E test scenarios (assessment flow, event registration, AURA calculation)
- Load testing (5000 concurrent users)
- Security testing (OWASP Top 10)

---

## SEVERITY BREAKDOWN

| Severity | Count | Examples |
|----------|-------|----------|
| CRITICAL | 5 | Missing 25+ API endpoints; new tables undefined; AURA execution model missing; Realtime design absent; Supabase tier limit at scale |
| HIGH | 8 | Missing ADRs (6), caching undefined, performance unvalidated |
| MEDIUM | 6 | State management gaps, error handling patterns, security details |
| LOW | 4 | Code style guides, component patterns, logging setup |

---

## RECOMMENDATIONS (PRIORITY ORDER)

### Phase 1: Unblock Production Launch (This Week)

1. **Design missing tables + RLS + indexes**
   - activity_log (schema, RLS, index on user_id + created_at)
   - volunteer_leagues (schema, RLS, relationship to aura_scores)
   - aura_coach_sessions (schema, RLS, conversation storage)

2. **Define remaining API endpoints (25)**
   - Event management (CRUD)
   - Volunteer requests (org → user)
   - Event ratings (post-event feedback)
   - Search/matching (organizations find volunteers)
   - Referrals (stats, redeem)

3. **Create AURA Calculation RPC Function**
   - Input: user_id
   - Aggregate: all 8 competency scores, verification levels, event performance
   - Output: new aura_scores row, update is_current flag
   - Run via FastAPI endpoint `/api/v1/scores/calculate` (admin only for test)

4. **Document Supabase Realtime Pattern**
   - Create ADR-007: Realtime
   - Specify table subscriptions for leaderboard, notifications, activity
   - Add Zustand + TanStack Query integration examples

### Phase 2: Production Hardening (Next 2 Weeks)

5. **Security ADR-008: Hardening**
   - Rate limiting implementation (FastAPI middleware)
   - CORS policy
   - Data encryption for sensitive fields
   - Secret rotation policy

6. **Monitoring ADR-009: Observability**
   - Sentry setup for both frontend + backend
   - Loguru structured logging to file/cloud
   - Metrics: response times, error rates, AURA calculations
   - Alerting: DB connection limit, LLM API failures

7. **Caching ADR-006**
   - TanStack Query invalidation rules per endpoint
   - Response-level HTTP caching headers
   - Leaderboard cache TTL (10s for live feel)

8. **Performance Validation**
   - Load test: 100 concurrent assessment submissions
   - Vector search latency: <100ms for 10K embeddings
   - Leaderboard query: <50ms
   - Supabase connection pooling assessment

### Phase 3: Feature Completion (Weeks 3-4)

9. **Coach Feature**
   - Define prompt template (5-shot examples)
   - Session schema and Gemini API integration
   - User onboarding flow

10. **Impact Metrics**
   - Schema design (what to track)
   - Aggregation logic (batch vs real-time)
   - Display in profile + org portal

11. **Volunteer Leagues**
   - Define mechanics (auto-assign? join?)
   - Separate leaderboards
   - Badges/rewards

12. **Activity Feed**
   - Event types to log
   - Privacy model
   - Realtime subscription pattern

---

## SPECIFIC ISSUES BY COMPONENT

### Backend (FastAPI)

1. **Missing assessment endpoint:** `GET /api/v1/assessments/{id}/questions` (pre-fetch all for offline mode)
2. **Missing event endpoints:** CRUD (6 endpoints)
3. **Missing Coach endpoint:** `POST /api/v1/coach/sessions`
4. **Missing volunteer search:** `POST /api/v1/organizations/search`
5. **Error handling:** No global exception handler middleware defined
6. **Logging:** Loguru configured but no request/response logging example
7. **LLM caching:** ADR-004 says "cache immediately" but no caching mechanism designed

### Database (Supabase)

1. **Activity log function:** `INSERT INTO activity_log (user_id, event_type, metadata) VALUES (...)`
   - Missing triggers for: assessment_complete, event_registered, badge_earned, profile_updated
   - Missing retention policy (auto-delete after 1 year?)

2. **AURA calculation:** Function should:
   ```sql
   CREATE OR REPLACE FUNCTION recalculate_aura(p_user_id UUID) RETURNS DECIMAL AS $$
   -- Calculate AURA per formula in ADR-005
   -- Return updated aura_scores row
   $$
   ```

3. **Event registration triggers:** Auto-increment registered_count, check capacity

4. **Performance:** No materialized views for leaderboard (consider for 5K+ users)

### Frontend (Next.js)

1. **Missing Realtime hooks:** `useLeaderboardSubscription()`, `useActivityFeed()`
2. **Missing Coach UI:** Page + modal + message component
3. **Missing offline assessment:** Service Worker + Dexie.js integration
4. **Missing deep-link support:** Assessment state should be recoverable from URL
5. **Form validation:** No Zod schema examples for new features

### API Generation (@hey-api/openapi-ts)

1. After finalizing API contracts, run: `pnpm generate:api`
2. This auto-generates types and TanStack Query hooks
3. **Update needed:** OpenAPI schema for all 25 missing endpoints

---

## ARCHITECTURE STRENGTHS

✅ **Supabase-first design:** Direct RLS reads eliminate backend round-trips
✅ **Clear auth flow:** Magic link + OAuth with JWT verification
✅ **Type safety:** FastAPI → OpenAPI → TypeScript codegen → TanStack Query
✅ **Scalable schema:** pgvector for semantic search, RLS for multi-tenant safety
✅ **Assessment engine:** Clear 3-question-type design, IRT roadmap
✅ **AURA formula:** Defensible, weighted, verification-aware
✅ **Cost-effective:** Free tiers, minimal infrastructure ($8/mo)

---

## ARCHITECTURE WEAKNESSES

❌ **New features not designed:** activity_log, leagues, coach, metrics undefined
❌ **Execution model unclear:** Where/when does AURA recalculation run?
❌ **Realtime undefined:** No subscription patterns, Zustand integration missing
❌ **25+ endpoints missing:** Event CRUD, search, volunteer requests, ratings
❌ **Caching strategy absent:** No TTLs, invalidation rules, HTTP headers
❌ **Performance unvalidated:** No load tests, connection limit check, vector search latency
❌ **Scale assumptions untested:** 5000 users → Supabase free tier limit (40 connections)
❌ **Monitoring minimal:** Sentry mentioned, no alerting, no SLOs

---

## CONCLUSION

**Ready for MVP?** 60% ready
- Core tables, auth, assessments, AURA formula: ✅ solid
- New features, realtime, 25+ endpoints, performance validation: ⚠️ critical gaps

**Timeline to production:** 3-4 weeks with parallel work
- Week 1: Complete schema + API endpoints
- Week 2: Realtime + caching + security hardening
- Week 3: Performance testing + monitoring setup
- Week 4: Features (Coach, Impact Metrics, Leagues)

**Recommended next step:** Run skills-first protocol
- `design:system-design` for activity_log + volunteer_leagues schemas
- `engineering:system-design` for realtime + caching ADRs
- `engineering:code-review` for missing endpoint contracts

---

**Generated:** 2026-03-22
**Audit Type:** Completeness + Gap Analysis
**Status:** RESEARCH ONLY
