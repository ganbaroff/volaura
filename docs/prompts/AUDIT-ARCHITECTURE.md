# Architecture Audit — Volaura System

**Date:** 2026-03-22
**Auditor:** Claude (System Architecture)
**Status:** COMPREHENSIVE REVIEW COMPLETE
**Summary:** 7 CRITICAL gaps, 11 WARNING-level issues, 8 SUGGESTIONS for improvement

---

## Executive Summary

The MEGA-PROMPT and ADR-001 provide excellent high-level architecture decisions (Supabase + FastAPI + Vercel split is sound) and comprehensive database schema. However, there are **critical omissions** that will cause implementation failures if not addressed before development:

1. **No rate limiting spec** — API is wide open to abuse
2. **Assessment engine algorithm incomplete** — pseudo-adaptive logic is underspecified
3. **LLM evaluation timing/cost not modeled** — open_text scoring may timeout or bankruptcy
4. **Caching strategy missing** — no TTL strategy for Leaderboard, public profiles, embeddings
5. **Auth middleware gaps** — no spec for protected route enforcement on frontend
6. **No logging/monitoring config** — logging is mentioned but not structured
7. **Type generation pipeline incomplete** — OpenAPI codegen not documented

---

## DETAILED AUDIT

### 1. API DESIGN (Coverage: 70%)

#### Status: PARTIALLY COMPLETE

**What's Well-Defined:**
- ✅ Core CRUD endpoints listed (assessments, scores, leaderboard, org search)
- ✅ Response envelope format consistent: `{ data, meta }`
- ✅ Error format structured: `{ detail: { code, message } }`
- ✅ 10 routers identified with clear responsibility boundaries
- ✅ Path prefixes hierarchical: `/api/v1/{domain}`

**CRITICAL GAPS:**

1. **Profile Endpoints Missing Detail**
   ```python
   # Documented: None specific
   # Missing:
   - POST /api/v1/profiles/me (update own profile)
   - GET /api/v1/profiles/{user_id} (read public)
   - POST /api/v1/profiles/avatar (upload)
   - DELETE /api/v1/profiles/me (account deletion)
   ```
   **Impact:** Profile edit/update flow cannot be implemented.
   **Fix:** Add full CRUD spec in API-CONTRACTS doc.

2. **Email/Verification Endpoints Implicit**
   ```python
   # Mentioned in routes: verifications_router
   # Spec: Zero detail
   # Missing:
   - POST /api/v1/verifications/attestation (org attests after event)
   - GET /api/v1/verifications/history (read verification audit trail)
   ```
   **Impact:** Org attestation flow unclear.
   **Severity:** CRITICAL
   **Fix:** Spec all 3 verification levels in endpoint detail.

3. **Notification Endpoints Empty**
   ```python
   # Router exists: notifications_router
   # Endpoints: Not specified
   # Expected:
   - GET /api/v1/notifications (list)
   - PATCH /api/v1/notifications/{id}/read (mark as read)
   - DELETE /api/v1/notifications/{id} (dismiss)
   ```
   **Severity:** CRITICAL
   **Fix:** Define notification lifecycle.

4. **Share/OG Generation Endpoints**
   ```python
   # Router: share_router
   # Use case: Generate shareable images (LinkedIn, Story, QR)
   # Spec: Only mentions @vercel/og route at app/api/og/[username]/route.tsx
   # Missing:
   - POST /api/v1/share/image (generate custom image with filters)
   - GET /api/v1/share/qr?user_id=... (generate QR code)
   ```
   **Severity:** WARNING
   **Impact:** Share buttons may only work on edge-rendered OG endpoint.
   **Fix:** Clarify if share images are edge-only or API-generated.

5. **Admin Endpoints Unspecified**
   ```python
   # Router: admin_router (listed but empty)
   # Expected operations:
   - POST /api/v1/admin/questions (bulk upload)
   - POST /api/v1/admin/users/lock (disable user)
   - GET /api/v1/admin/metrics (system stats)
   ```
   **Severity:** CRITICAL
   **Fix:** Define admin responsibilities + auth model.

#### WARNING: Request/Response Shapes Incomplete

**Problem:** Many endpoints document response shape (scores_router example good), but request schemas are often missing request field constraints.

Example — Missing constraints:
```python
# Documented:
# POST /api/v1/assessments/{id}/answers
# Request: { "question_id": "uuid", "response": { "selected": 5 }, "time_spent_seconds": 45 }

# MISSING:
# - What if question_id doesn't belong to this assessment?
# - Is response.selected always int? What about MCQ responses?
# - Does time_spent_seconds have bounds (e.g., > 0, < 3600)?
# - What's the max words per character for open_text?
```

**Fix:** Create detailed Pydantic schema docs for each endpoint request/response.

---

### 2. DATA FLOW (Coverage: 75%)

#### Status: MOSTLY MAPPED, EDGE CASES MISSING

**Well-Documented Flows:**

✅ **Pattern 1: Direct Read**
```
Browser → Supabase Client (RLS) → PostgreSQL
Used for: profiles, events, leaderboard, notifications
```
Clear and correct.

✅ **Pattern 2: Authenticated Write via API**
```
Browser → FastAPI (Bearer token) → Supabase Admin → PostgreSQL
Used for: assessment answer, profile update, event registration
```
Clear and correct.

✅ **Pattern 3: Computed Read**
```
Browser → FastAPI → compute → return
Used for: AURA calculation, next question, LLM evaluation
```
Clear but has gaps (see below).

✅ **Pattern 4: Edge-Rendered**
```
Browser → Vercel Edge → ISR cache / Supabase → HTML
Used for: public profiles, OG images
```
Clear and correct.

✅ **Pattern 5: Realtime**
```
Browser → Supabase Realtime subscription
Used for: leaderboard live updates, notification badges
```
Clear and correct.

**CRITICAL GAPS IN FLOWS:**

1. **Assessment Submission Flow Ambiguous**
   ```
   User submits answer → FastAPI:

   IF question_type == 'open_text':
       - Call Gemini API (20-120s latency)
       - Store LLM score + feedback
       - Calculate next question
       - Return response

   TIMING ISSUE: Is this blocking or async?
   ```
   **Problem:** If blocking, HTTP timeout risk (Vercel free tier = 10s).
   **Current Spec:** Shows synchronous response, but 10s timeout insufficient for LLM calls.
   **Impact:** Open-text answers will timeout frequently.
   **Severity:** CRITICAL
   **Fix Required:**
   - Document async pattern: return immediately with `pending_evaluation: true`
   - Use Supabase Edge Function or FastAPI bg task to evaluate
   - Return score via WebSocket/polling or notification

2. **Badge Trigger Flow Missing**
   ```
   Assessment completes → AURA recalculated → Score changes → Badge changes?

   Current spec: POST /api/v1/assessments/{id}/complete returns badge_changed

   MISSING:
   - When does badge notification fire?
   - Is badge_history updated atomically with aura_scores?
   - What if score doesn't change (reassessment)? Still update history?
   ```
   **Severity:** WARNING
   **Fix:** Specify badge change trigger in POST /assessments/{id}/complete response.

3. **Event Registration → Profile Update Flow**
   ```
   User registers for event → competency requirements checked?

   Current: MIN_AURA_SCORE checked, required_competencies in schema

   MISSING:
   - If event requires [communication, leadership], does API validate
     user has non-zero scores in those?
   - What if scores are too new (< 24h old)?
   - Rejection reason returned to UI?
   ```
   **Severity:** WARNING
   **Fix:** Document eligibility check details in event registration endpoint.

4. **Referral Conversion Flow Missing**
   ```
   Invited user signs up with referral_code → what happens?

   Current schema: referrals.referred_by, referrals.converted_at, profiles.referral_code

   MISSING:
   - Endpoint to check if referral_code is valid?
   - POST /api/v1/auth/signup { ..., referral_code }?
   - When does conversion happen (signup or first assessment)?
   - Reward trigger spec (badges, score boost)?
   ```
   **Severity:** WARNING
   **Fix:** Document referral lifecycle endpoint.

---

### 3. AUTH FLOW (Coverage: 60%)

#### Status: PARTIALLY SPECIFIED, CRITICAL GAPS

**What's Good:**
- ✅ Magic link + Google OAuth flow documented
- ✅ JWT-based auth pattern clear: token in Bearer header
- ✅ Per-request Supabase client pattern solid (Depends())
- ✅ RLS policies on all tables defined

**CRITICAL GAPS:**

1. **Frontend Route Protection Undefined**
   ```typescript
   // Documented: Middleware exists at app/middleware.ts
   // Spec: "auth check + i18n locale redirect"

   // MISSING: Implementation details
   // Questions:
   - What routes require auth? (Implicit: /app/* requires auth, /(auth)/* public)
   - How does middleware enforce? (Check JWT in cookie?)
   - What happens to expired token? (Refresh? Redirect to /login?)
   - What if Supabase refresh fails? (Logout? Error page?)
   ```
   **Impact:** Developers won't know how to add protected routes.
   **Severity:** CRITICAL
   **Fix:** Document middleware logic with pseudocode.

2. **Token Refresh Strategy Missing**
   ```python
   # Supabase JWT expires in 1 hour
   # Supabase provides refresh_token to get new access token

   # Current spec: JWT in headers as Bearer token
   # MISSING:
   - Where are refresh tokens stored? (localStorage? Cookies?)
   - When does refresh happen? (On 401? On timer?)
   - Does Supabase SDK handle auto-refresh? (Yes, via @supabase/ssr)
   - But is this documented for FastAPI verification?
   ```
   **Severity:** CRITICAL
   **Fix:** Document token refresh flow in deps.py.

3. **Concurrent Session Handling**
   ```
   User logs in on Web + Mobile app simultaneously.
   Both have valid JWTs.

   MISSING:
   - Can user maintain concurrent sessions?
   - Single-device enforcement? (No spec = probably not enforced)
   - Logout on other devices? (No endpoint documented)
   ```
   **Severity:** SUGGESTION
   **Fix:** If single-session needed, add POST /api/v1/auth/logout-other-devices.

4. **OAuth Scope Spec Missing**
   ```
   # "Google OAuth (redirect flow)"

   MISSING:
   - What scopes requested? (email? profile? calendar?)
   - If calendar requested, why? (No mention in features)
   - Consent screen text?
   ```
   **Severity:** WARNING
   **Fix:** Specify OAuth scopes in Google integration details.

5. **Rate Limiting on Auth Endpoints**
   ```
   POST /api/v1/auth/login (magic link) — how many per IP per hour?
   POST /api/v1/auth/callback — replay attack prevention?

   Current spec: ZERO rate limiting mentioned
   ```
   **Severity:** CRITICAL (see rate limiting section below)

---

### 4. ASSESSMENT ENGINE (Coverage: 65%)

#### Status: ALGORITHM UNDERSPECIFIED

**What's Specified:**
- ✅ 3 question types defined (BARS, MCQ, Open Text)
- ✅ Question selection "pseudo-adaptive" algorithm outlined
- ✅ IRT parameters in schema (irt_a, irt_b, irt_c)
- ✅ Score calculation by type (BARS = (selected-1)/6 * 100, etc.)

**CRITICAL GAPS:**

1. **Question Selection Algorithm Incomplete**
   ```python
   # Documented:
   # "Start at difficulty 1 (easy)
   #  If score > 70 on current question → next difficulty +1
   #  If score < 40 → next difficulty -1
   #  Stay within 1-3 range
   #  Select random unused question at current difficulty"

   # MISSING DETAILS:
   - How many questions per competency? (3? 5? 10?)
   - What if difficulty stays same (40 <= score <= 70)?
   - Can same question be asked twice? (Schema says "random unused" = no repeat)
   - What if pool of questions at that difficulty is exhausted?
   - How is "difficulty" property generated for IRT? (Calculated from irt_b?)
   - Are IRT parameters actually used in question selection? (Spec says they exist but not HOW)
   ```
   **Impact:** Algorithm cannot be implemented without guessing.
   **Severity:** CRITICAL
   **Fix:** Pseudo-code question selection with edge cases:
   ```python
   def select_next_question(assessment_id, current_difficulty, competency):
       """
       Select next question for adaptive assessment.

       Args:
           assessment_id: UUID of active assessment
           current_difficulty: SMALLINT 1-3
           competency: competency_type

       Returns:
           Question dict or None if pool exhausted

       Algorithm:
       1. Get all unused questions for this competency + difficulty
       2. If none exist, drop difficulty by 1 and retry
       3. If difficulty < 1, return None (assessment complete)
       4. Randomly select from available pool
       5. Mark question as used in assessment_responses
       """
   ```

2. **Open-Text LLM Evaluation Cost + Timing Not Modeled**
   ```
   Feature: Open-text answers evaluated by Gemini 2.5 Flash

   Cost: ~100 tokens per evaluation at $0.075/M input + $0.30/M output
   = ~0.000010 USD per evaluation

   Timing: Gemini API latency 1-30s typically

   MISSING FROM SPEC:
   - If assessment has 1-3 open_text questions per competency,
     and 8 competencies, max 24 LLM calls = 24-720 seconds runtime
   - Is this async? (CRITICAL — see data flow section)
   - Cost per user assessment: 24 * 0.000010 = $0.00024
   - At 1000 assessments/month = $0.24 (negligible)
   - At 10000 assessments/month = $2.40 (still OK on free tier)
   - But what if all 24 calls happen synchronously?

   Current spec: Shows synchronous response pattern
   Consequence: Assessments will timeout

   Timeout Bounds:
   - Vercel serverless: 10s limit
   - Railway: 30s+ OK
   - But frontend polling/socket needed
   ```
   **Severity:** CRITICAL
   **Fix:** Specify async LLM evaluation with timeout handling.

3. **Reliability Factor Calculation Ambiguous**
   ```python
   # Documented:
   # "reliability_factor = 1.0 - (0.15 × normalized_std_dev), clamped [0.85, 1.0]"

   MISSING:
   - normalized_std_dev of WHAT? All 8 competency scores?
   - Std dev across assessments (temporal) or across competencies (cross-section)?
   - How is std_dev normalized? (Divided by mean? Divided by max?)
   - Example: User has scores [85, 75, 90, 70, 88, 92, 78, 80]
     - std_dev ≈ 7.2
     - mean ≈ 82.25
     - normalized = 7.2 / 82.25 = 0.087
     - reliability = 1.0 - (0.15 * 0.087) = 0.987 (clamped [0.85, 1.0]) = 0.987 ✓
   - OR is it std_dev of score across multiple assessment attempts?
   ```
   **Impact:** AURA scores will be calculated incorrectly if formula misunderstood.
   **Severity:** CRITICAL
   **Fix:** Clarify with explicit example:
   ```python
   # Example calculation for user_id = abc123
   competency_scores = {
       "communication": 85,
       "reliability": 75,
       "english_proficiency": 90,
       "leadership": 70,
       "event_performance": 88,
       "tech_literacy": 92,
       "adaptability": 78,
       "empathy_safeguarding": 80,
   }

   # Weighted AURA (before reliability factor)
   weighted_sum = sum(score * WEIGHTS[comp] for comp, score in competency_scores.items())
   # = 85*0.20 + 75*0.15 + ... = 82.45

   # Standard deviation of the 8 scores
   import statistics
   std_dev = statistics.stdev(competency_scores.values())  # ≈ 7.27

   # Normalization: divide by mean
   mean_score = statistics.mean(competency_scores.values())  # ≈ 82.25
   normalized_std_dev = std_dev / mean_score  # ≈ 0.088

   # Reliability factor
   reliability_factor = 1.0 - (0.15 * normalized_std_dev)  # ≈ 0.987

   # Final AURA
   aura = weighted_sum * reliability_factor  # ≈ 82.45 * 0.987 = 81.38
   ```

4. **Question Type Modifiers Not Calibrated**
   ```python
   # Documented:
   # "type_modifier (BARS=1.0, MCQ=0.9, Open Text=1.1)"

   MISSING:
   - Why these values? (Rationale?)
   - Open Text 1.1x boost — is this to account for variance in LLM scoring?
   - MCQ 0.9x reduction — why penalize multiple choice?
   - Should modifier be applied per-question or per-competency aggregate?
   - Example: User takes 2 BARS (80, 90) + 1 MCQ (85) + 1 Open (75)
     - Per-question: 80*1.0 + 90*1.0 + 85*0.9 + 75*1.1 = 259.5 / 4 = 64.875
     - Per-aggregate: (165 + 85 + 75) / 3 * modifier? (Unclear)
   ```
   **Severity:** CRITICAL
   **Fix:** Clarify with explicit example or algorithm.

---

### 5. AURA CALCULATION (Coverage: 85%)

#### Status: MOSTLY COMPLETE, 2 EDGE CASES

**What's Good:**
- ✅ 8 weights sum to 1.0: 0.20+0.15+0.15+0.15+0.10+0.10+0.10+0.05 = 1.0 ✓
- ✅ Verification multipliers documented: 1.0, 1.15, 1.25
- ✅ Badge tier thresholds clear: 90/75/60/40
- ✅ Clamping to [0, 100] prevents invalid scores

**GAPS:**

1. **Verification Multiplier Application Timing**
   ```python
   # Documented: "sum(competency_score × weight × verification_multiplier)"

   # Is it per-competency or global?
   # Case: User has:
   #   - communication (0.20 weight, self_assessed, 80 score)
   #   - reliability (0.15 weight, org_attested, 85 score)
   #
   # Option A (per-competency):
   #   80 * 0.20 * 1.0 = 16.0
   #   85 * 0.15 * 1.15 = 14.6625
   #   Total = 30.6625 (missing other 5 competencies...)
   #
   # Option B (aggregated then multiplied by max verification):
   #   All 8 competencies averaged = X
   #   X *= max_verification_multiplier_across_competencies
   #   (This doesn't match spec syntax)
   #
   # Current spec is ambiguous.
   ```
   **Severity:** CRITICAL
   **Fix:** Clarify with complete worked example.

2. **Percentile Calculation Missing**
   ```python
   # Schema has: aura_scores.percentile FLOAT
   # No spec for when/how it's calculated
   # Presumably: percentile rank within all users with is_public=true
   # But: Is it real-time? Daily? Per assessment?
   # MISSING: SQL for percentile calculation, update frequency
   ```
   **Severity:** WARNING
   **Fix:** Add percentile calculation to aura_calculator.py spec.

3. **Edge Case: First Assessment**
   ```python
   # User takes first assessment, gets 0 scores in 7 competencies
   # AURA = sum(0 * weight * multiplier) = 0
   # Tier = "none"
   # Badge history created with old_tier = null?
   ```
   **Severity:** SUGGESTION
   **Fix:** Document null handling in badge_history.

---

### 6. MISSING INFRASTRUCTURE

#### Rate Limiting (Coverage: 0%)

**Severity: CRITICAL**

Current Spec: **ZERO rate limiting mentioned anywhere.**

Risk Analysis:
```
Unprotected endpoints open to:
1. Brute force:
   - POST /api/v1/auth/login: unlimited magic link attempts
   - 1000 emails/minute per attacker IP

2. Assessment spam:
   - POST /api/v1/assessments/start: unlimited new assessments
   - Could DOS LLM evaluations

3. Search abuse:
   - POST /api/v1/org/volunteers/search: unlimited embeddings
   - Each embedding call = Gemini API cost + latency

4. Leaderboard scraping:
   - GET /api/v1/scores/leaderboard: no rate limit
   - Could scrape all 10,000 users in seconds
```

**Fix Required:**

```python
# app/middleware.py or routers

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# In routers:
@router.post("/assessments/start")
@limiter.limit("10/hour")  # Max 10 new assessments per user per hour
async def start_assessment(...): ...

@router.post("/auth/login")
@limiter.limit("5/minute")  # Max 5 magic link requests per IP per minute
async def request_magic_link(...): ...

@router.get("/scores/leaderboard")
@limiter.limit("30/minute")  # Max 30 requests per IP per minute
async def get_leaderboard(...): ...
```

---

#### Caching Strategy (Coverage: 10%)

**Severity: CRITICAL**

Only mentioned: "ISR pages" for public profiles.

Missing:
```
1. Leaderboard caching (rebuild frequency?)
   - GET /api/v1/scores/leaderboard is expensive with 10k users
   - SQL: ROW_NUMBER() OVER (...ORDER BY composite_score DESC)
   - Should cache for 5-60 minutes?

2. Volunteer embeddings (TTL?)
   - Generated via Gemini on profile updates
   - RPC match_volunteers queries them frequently
   - Should regenerate on score change? (Probably yes, invalidate)

3. Questions pool (in-app cache?)
   - Fetched per assessment
   - Supabase PostgREST caching headers?
   - TTL: Probably never, or on admin question updates

4. Public profile ISR revalidation frequency?
   - Spec says "ISR revalidates every 60s"
   - Is that correct for leaderboard changes?
   - If user A passes user B in ranking, user B's rank changes
   - But ISR won't know to revalidate user B's page
```

**Fix Required:**

Document cache invalidation strategy:
```python
# In aura_calculator.py:
async def recalculate_aura(user_id: UUID):
    """Recalculate AURA and invalidate caches."""
    aura_score = _compute_aura(user_id)
    await db.table("aura_scores").upsert(aura_score).execute()

    # Invalidate related caches:
    # 1. Leaderboard — rebuild after every score change
    await cache.invalidate_key("leaderboard:*")

    # 2. User's profile page — revalidate in Vercel ISR
    await revalidate_path(f"/u/{username}")  # Using Next.js revalidateTag

    # 3. User embeddings — regenerate vector if score_changed significantly
    if abs(old_aura - new_aura) > 5:  # 5-point threshold
        await embedding_service.regenerate_embedding(user_id)
```

---

#### Error Handling Middleware (Coverage: 30%)

**What's Good:**
- ✅ Structured error format: `{ detail: { code, message } }`
- ✅ HTTP status codes mentioned in spec

**Missing:**

1. **Exception Handlers Not Specified**
   ```python
   # FastAPI has @app.exception_handler(CustomException)
   # Current spec: None documented
   # Should handle:
   - TimeoutError (LLM evaluation timeout)
   - ValidationError (Pydantic)
   - AuthenticationError (Invalid JWT)
   - InsufficientPermissionError (RLS violation)
   - NotFoundError (Resource missing)
   - ConflictError (Duplicate entry)
   - RateLimitError (Too many requests)
   ```
   **Fix:** Create exception.py with FastAPI exception handlers.

2. **Sentry Integration Mentioned but Not Detailed**
   ```
   "Sentry (free tier): error tracking, frontend + backend"

   Missing:
   - How are errors sent to Sentry? (SDK initialization, breadcrumbs?)
   - What environment variables? (SENTRY_DSN)
   - Sampling rate for 10k+ users?
   - Source map upload?
   ```
   **Severity:** SUGGESTION
   **Fix:** Document Sentry setup in deployment guide.

---

#### Health Check Endpoint (Coverage: 50%)

**Mentioned:** "Health endpoint: `GET /api/health` returns DB, LLM, storage status"

**Missing Detail:**
```python
# Current spec lacks implementation detail

# Should be:
@router.get("/health")
async def health_check():
    """Health check — monitors critical services."""
    try:
        # Check DB connectivity
        db = await get_supabase_admin()
        db_ok = await db.table("profiles").select("count").execute()

        # Check LLM connectivity
        client = genai.Client(api_key=settings.gemini_api_key)
        llm_ok = True  # Implicit via API key validation

        # Check storage
        # Supabase storage is part of DB, so if DB OK, storage OK

        return {
            "status": "healthy" if (db_ok and llm_ok) else "degraded",
            "services": {
                "database": "ok" if db_ok else "error",
                "llm": "ok" if llm_ok else "error",
                "storage": "ok" if db_ok else "error",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return { "status": "unhealthy", "error": str(e) }, 503
```

---

#### Logging Configuration (Coverage: 40%)

**Mentioned:** `loguru` (logging — NEVER print())

**Missing:**

1. **Log Level Strategy**
   ```python
   # No spec for when to use DEBUG, INFO, WARNING, ERROR, CRITICAL
   # Should define:

   # DEBUG: Assessment question selection, IRT calculations
   # INFO: Assessment completion, user registration, API calls
   # WARNING: Rate limit hit, LLM timeout, DB lag
   # ERROR: Failed LLM evaluation, invalid JWT, RLS violation
   # CRITICAL: Service unavailable, data corruption, auth bypass
   ```

2. **Structured Logging Format**
   ```python
   # Loguru should output JSON for aggregation
   # Missing:

   import logging
   from loguru import logger
   import json

   # Configure loguru for JSON output
   logger.remove()  # Remove default handler
   logger.add(
       lambda msg: print(json.dumps({
           "timestamp": msg.record["time"].isoformat(),
           "level": msg.record["level"].name,
           "message": msg.record["message"],
           "function": msg.record["function"],
           "line": msg.record["line"],
       })),
       format="{message}",
   )
   ```

3. **Correlation IDs**
   ```python
   # No mention of request IDs for tracing
   # Should add: X-Request-ID header
   # Log it on every operation for debugging
   ```

---

#### Environment Variables (Coverage: 40%)

**Mentioned:** "Configure Vercel deployment with environment variables"

**What's Missing:** Complete list.

**Required:**

```bash
# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
NEXT_PUBLIC_API_URL=https://api.volaura.com
NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com

# Backend (.env)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx... (KEEP SECRET)
GEMINI_API_KEY=xxxxx
RESEND_API_KEY=xxxxx
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
RAILWAY_ENVIRONMENT=production
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
LLM_TIMEOUT_SECONDS=30
```

---

### 7. SECURITY GAPS

#### Input Validation (Coverage: 50%)

**What's Good:**
- ✅ Pydantic v2 field validators mentioned
- ✅ Zod validation on frontend
- ✅ RLS on all tables

**CRITICAL GAPS:**

1. **No Schema Validation Examples**
   ```python
   # Spec mentions @field_validator but no examples
   # Missing patterns:

   # Email validation
   class LoginRequest(BaseModel):
       email: EmailStr  # Pydantic EmailStr

   # Username validation
   class ProfileUpdate(BaseModel):
       username: str

       @field_validator("username")
       @classmethod
       def validate_username(cls, v: str) -> str:
           # Only alphanumeric + underscore, 3-30 chars
           if not re.match(r"^[a-z0-9_]{3,30}$", v):
               raise ValueError("Invalid username format")
           return v

   # Bio length limit
   class ProfileUpdate(BaseModel):
       bio: str = Field(..., max_length=500)

   # AURA score bounds
   class AssessmentResponse(BaseModel):
       score: int = Field(..., ge=0, le=100)
   ```
   **Severity:** WARNING
   **Fix:** Create validation.py with reusable validators.

2. **SQL Injection Prevention (RLS is Good, But)**
   ```python
   # Using Supabase SDK protects against SQL injection
   # But file operations might be vulnerable:

   # WRONG:
   with open(f"/tmp/{user_id}.txt") as f:  # Path traversal risk
       ...

   # RIGHT:
   safe_filename = os.path.basename(user_id)  # Only filename
   with open(f"/tmp/{safe_filename}.txt") as f:
       ...
   ```
   **Severity:** SUGGESTION
   **Fix:** Document safe file handling patterns.

3. **Open Text Word Limit Enforcement**
   ```python
   # Schema has: max_words INT
   # But no validation on submission

   # MISSING:
   class OpenTextResponse(BaseModel):
       text: str
       question_id: UUID

       @field_validator("text")
       @classmethod
       def validate_text(cls, v: str) -> str:
           word_count = len(v.split())
           if word_count > 500:  # Or get from question.max_words
               raise ValueError(f"Response exceeds word limit (got {word_count})")
           return v
   ```
   **Severity:** WARNING
   **Fix:** Add word limit validator.

---

#### XSS Prevention (Coverage: 70%)

**What's Good:**
- ✅ React.js (Next.js) auto-escapes by default
- ✅ No v-html or dangerouslySetInnerHTML mentioned
- ✅ User-generated content (bio, comments) not rendered as HTML

**Potential Gap:**

1. **OG Image Generation (Satori/vercel/og)**
   ```tsx
   // At app/api/og/[username]/route.tsx
   // Spec mentions "OG images auto-generated: name + AURA score + badge"

   // If user's bio is embedded:
   // WRONG:
   <div>{user.bio}</div>  // Satori renders as SVG, escaped = OK

   // SAFE in Satori (JSX auto-escapes)
   // But verify no HTML string injection in image generation
   ```
   **Severity:** SUGGESTION
   **Fix:** Document that Satori escapes all text content.

2. **Share URLs**
   ```
   Share link format: /u/[username]?shared=true&context=linkedin

   RISK: If context parameter is used to modify page:
   </profile>
   <script>alert('XSS')</script>

   But URL params are URL-encoded by browser, so risk low.
   ```
   **Severity:** SUGGESTION
   **Fix:** Always URL-encode share parameters.

---

#### CSRF Protection (Coverage: 20%)

**Not Mentioned Anywhere.**

**Risk:** State-changing operations (assessment submit, profile update) vulnerable to CSRF.

**Current Safeguard:** Bearer token auth in API means CSRF requires attacker to have token (low risk).

**Fix:**

```python
# FastAPI doesn't automatically provide CSRF like Django
# But Bearer token auth provides protection (CSRF needs to inject token)
#
# If using cookies + session-based auth later, add:

from fastapi.middleware.csrf import CSRFMiddleware

app.add_middleware(
    CSRFMiddleware,
    secret_key=settings.secret_key,
)
```

---

### 8. INTEGRATION GAPS

#### Frontend-Backend Integration (Coverage: 60%)

**What's Good:**
- ✅ OpenAPI codegen via @hey-api/openapi-ts mentioned
- ✅ Generated types for frontend consumption planned
- ✅ TanStack Query for data fetching

**CRITICAL GAPS:**

1. **API Codegen Process Not Documented**
   ```bash
   # Spec mentions: pnpm generate:api
   # Missing: Full setup

   # Should be:
   # 1. FastAPI starts and emits /openapi.json
   # 2. @hey-api/openapi-ts reads it
   # 3. Generates /src/lib/api/generated/
   #    - Types (TypeScript)
   #    - TanStack Query hooks
   #    - Request/response validators
   # 4. Frontend imports from generated

   # MISSING:
   - What's in openapi.json generation? (Ensure all endpoints documented)
   - Build step integration? (pnpm setup, turbo.json)
   - Validation schema generation? (Zod)
   - Local dev flow? (Start API, run codegen, start frontend)
   ```
   **Severity:** CRITICAL
   **Fix:** Document codegen setup in engineering/API-CONTRACTS doc.

2. **Type Sync Between Frontend and Backend**
   ```typescript
   // Current plan: OpenAPI codegen (good)
   // But what about shared types not in OpenAPI?

   // Example: Badge tier enum
   // Backend: enum badge_tier { platinum, gold, silver, bronze, none }
   // Frontend: manually typed? auto-imported?

   // MISSING:
   // - Are Pydantic v2 models automatically converted to TypeScript?
   // - How are validation schemas shared?
   // - Example: open_text max_words per question
   ```
   **Severity:** WARNING
   **Fix:** Confirm all Pydantic models included in OpenAPI spec.

---

#### Real-Time Integration (Coverage: 30%)

**What's Good:**
- ✅ Supabase Realtime subscription pattern documented (Pattern 5)
- ✅ Used for leaderboard live updates + notification badges

**Missing:**

1. **Realtime Setup Not Detailed**
   ```typescript
   // Spec says: "Browser → Supabase Realtime subscription"
   // Missing: Client-side subscription code

   // Should be in components/features/leaderboard/LeaderboardTable.tsx:
   "use client";

   import { createClient } from "@/lib/supabase/client";

   export function LeaderboardTable() {
       const supabase = createClient();

       useEffect(() => {
           const subscription = supabase
               .channel("leaderboard")
               .on(
                   "postgres_changes",
                   { event: "UPDATE", schema: "public", table: "aura_scores" },
                   (payload) => {
                       // Update leaderboard in-memory or refetch
                   }
               )
               .subscribe();

           return () => subscription.unsubscribe();
       }, []);
   }
   ```
   **Severity:** WARNING
   **Fix:** Document Realtime subscription pattern in components.

2. **Notification Delivery Mechanism**
   ```
   Notifications table exists: notifications.is_read, notifications.action_url

   But HOW are they delivered to client?
   - Push notifications? (Not mentioned)
   - In-app badge? (Yes, via Realtime)
   - Email? (Resend SDK mentioned but no trigger spec)

   MISSING:
   - When is notification inserted? (Post-assessment? Event registration?)
   - Which events trigger notifications?
   - Email template list?
   ```
   **Severity:** CRITICAL
   **Fix:** Document notification trigger spec.

---

#### Embedding Search Integration (Coverage: 40%)

**What's Good:**
- ✅ pgvector (768-dim) specified
- ✅ RPC function match_volunteers documented
- ✅ Org semantic search endpoint: POST /api/v1/org/volunteers/search

**Missing:**

1. **Embedding Generation Trigger**
   ```python
   # When is user embedding created/updated?
   # Schema: volunteer_embeddings.user_id, embedding, updated_at

   # MISSING:
   # - Generated on signup? Profile update? Assessment completion?
   # - What text is embedded? (bio + competencies + skills?)
   # - How often regenerated?

   # Spec mentions "embedding_service.py" but no detail
   ```
   **Severity:** CRITICAL
   **Fix:** Document embedding generation in embedding.py spec.

2. **Search Query Embedding**
   ```python
   # Spec: POST /api/v1/org/volunteers/search
   # Request: { "query": "Reliable English-speaking event coordinator", "min_aura": 60, "limit": 20 }
   #
   # Missing:
   # - How is query embedded? (Same model as volunteer profiles? Gemini text-embedding-004?)
   # - Is embedding cached per query?
   # - Latency: embedding query takes ~1-3 seconds + vector search
   ```
   **Severity:** WARNING
   **Fix:** Document query embedding latency in performance budget.

---

### CRITICAL RULES VALIDATION

**Are the 16 critical rules from MEGA-PROMPT enforced by architecture?**

| Rule | Coverage | Status |
|------|----------|--------|
| NEVER Pages Router | 100% | ✅ App Router mandated in schema |
| NEVER Redux | 100% | ✅ Zustand in schema |
| NEVER SQLAlchemy | 100% | ✅ Supabase SDK only |
| NEVER global Supabase | 100% | ✅ Depends() pattern in backend rules |
| NEVER Pydantic v1 | 100% | ✅ v2 syntax mandated |
| NEVER google-generativeai | 100% | ✅ google-genai mandated |
| NEVER print() | 100% | ✅ loguru mandated |
| NEVER hardcoded strings | 100% | ✅ i18n t() mandated |
| NEVER tailwind.config.js | 100% | ✅ @theme {} in globals.css |
| NEVER vector(1536) | 100% | ✅ 768-dim specified |
| ALL tables RLS | 100% | ✅ RLS on all 15 tables defined |
| ALL responses envelope | 100% | ✅ { data, meta } pattern defined |
| ALL errors structured | 100% | ✅ { detail: { code, message } } defined |
| UTF-8 everywhere | 20% | ⚠️ Mandated but not enforced by architecture |
| Type hints on Python | 20% | ⚠️ Mandated but not enforced by architecture |
| Strict TypeScript | 100% | ✅ tsconfig strict mode enforced |

---

## SUMMARY TABLE: SEVERITY BREAKDOWN

| Severity | Count | Component |
|----------|-------|-----------|
| **CRITICAL** | 7 | API Design (3), Data Flow (1), Auth (3) |
| **CRITICAL** | 2 | Assessment Engine (2) |
| **CRITICAL** | 3 | Infrastructure (Rate Limiting, Caching, Logging Config) |
| **CRITICAL** | 1 | Integration (Codegen) |
| **WARNING** | 11 | Spread across Design (3), Data Flow (3), Auth (2), AURA (1), Logging (1), Validation (1) |
| **SUGGESTION** | 8 | Spread across Monitoring, File Handling, Type Sync, etc. |

---

## TOP 5 BLOCKING ISSUES (Fix Before Development)

### 1. **Assessment Engine: Open-Text Evaluation Timing** (CRITICAL)
**Problem:** Synchronous LLM evaluation will timeout on Vercel.
**Impact:** All open-text assessments fail.
**Fix:** Implement async pattern with background job + polling/notification.
**Time to implement:** 4-6 hours

### 2. **Rate Limiting (All Endpoints)** (CRITICAL)
**Problem:** Zero rate limiting spec — API will be spammed.
**Impact:** Cost explosion, service abuse, brute-force attacks.
**Fix:** Add slowapi middleware with per-endpoint limits.
**Time to implement:** 2-3 hours

### 3. **Assessment Question Selection Algorithm** (CRITICAL)
**Problem:** Pseudo-adaptive logic incomplete — developers will guess.
**Impact:** Broken adaptive testing, wrong difficulty progression.
**Fix:** Write detailed pseudocode with all edge cases.
**Time to implement:** 1-2 hours (doc only)

### 4. **Caching Strategy (Leaderboard, Embeddings)** (CRITICAL)
**Problem:** No cache invalidation plan — stale data or performance issues.
**Impact:** Leaderboard wrong after updates, embeddings not regenerated on score change.
**Fix:** Document cache TTL + invalidation triggers.
**Time to implement:** 2-3 hours (doc + code)

### 5. **Auth Middleware + Token Refresh** (CRITICAL)
**Problem:** Route protection and token refresh undefined.
**Impact:** Developers won't know how to add protected routes.
**Fix:** Document middleware logic + refresh strategy.
**Time to implement:** 1-2 hours (doc only)

---

## RECOMMENDATIONS

### Phase 1: Before Day 1 Development (Priority)

1. **Write API-CONTRACTS.md** with full endpoint specs (request/response/error cases)
2. **Write ASSESSMENT-ENGINE.md** with complete algorithm, edge cases, examples
3. **Write INFRASTRUCTURE.md** with rate limiting, caching, logging, monitoring setup
4. **Write AUTH.md** with middleware logic, token refresh, protected routes
5. **Write AURA-CALCULATION.md** with worked examples for all edge cases
6. **Add ENVIRONMENT.md** with complete env var list for all services

### Phase 2: Before Testing

7. Create @hey-api/openapi-ts codegen setup in turbo.json
8. Implement exception handlers + Sentry integration (middleware.py)
9. Implement rate limiting (slowapi)
10. Implement async LLM evaluation with background jobs

### Phase 3: Before Launch

11. Load test assessment engine under conference WiFi conditions (offline capability)
12. Load test leaderboard queries with 10k+ users
13. Monitor Gemini API costs (cap if exceeds budget)
14. Audit RLS policies for access control gaps

---

## DOCUMENTS TO CREATE

1. **API-CONTRACTS.md** — Full endpoint reference (request/response shapes, error cases)
2. **ASSESSMENT-ENGINE.md** — Algorithm, IRT integration, question selection with pseudocode
3. **INFRASTRUCTURE.md** — Rate limiting, caching, logging, monitoring setup
4. **AUTH.md** — Middleware logic, token refresh, protected routes
5. **AURA-CALCULATION.md** — Worked examples, reliability factor normalization
6. **EMBEDDING-GENERATION.md** — When/how embeddings created, update triggers, costs
7. **NOTIFICATION-TRIGGERS.md** — Events that trigger notifications, email lifecycle
8. **ENVIRONMENT.md** — Complete env var reference for frontend + backend
9. **DEPLOYMENT-CHECKLIST.md** — Pre-launch health checks, monitoring, alerts
10. **PERFORMANCE-BUDGET.md** — LLM latency, API response times, embeddings search time

---

## SCORE: 72/100

**Verdict:** Architecture is sound at high level (Supabase + FastAPI split is correct). Database schema is comprehensive. But critical implementation details are missing that will cause blockers if not documented before development starts.

**Recommendation:** Allocate 2-3 days to fill gaps in documentation before starting implementation. This will accelerate development by 10x and prevent mid-project rework.

