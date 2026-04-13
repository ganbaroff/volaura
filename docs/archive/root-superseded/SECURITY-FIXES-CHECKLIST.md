# Security Fixes — Implementation Checklist

## P0: DEPLOY THIS SPRINT (Critical vulnerabilities)

### [ ] Telegram HMAC Signature Validation
**File:** `apps/api/app/routers/telegram_webhook.py`

**Change:**
```python
import hmac
import hashlib
from fastapi import HTTPException

@router.post("/webhook")
async def webhook(request: Request, body: dict):
    # VALIDATE TELEGRAM SIGNATURE
    token = settings.telegram_bot_token
    secret = hashlib.sha256(token.encode()).digest()
    signature = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")

    # Compute expected signature from request body
    expected = hmac.new(secret, str(body).encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected):
        logger.warning(f"Invalid Telegram signature: {signature}")
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")

    # Continue processing...
```

**Test:**
- ✓ Valid Telegram request → 200 OK
- ✓ Spoofed request (wrong signature) → 401 Unauthorized
- ✓ Missing signature header → 401 Unauthorized

**Effort:** 15 minutes
**Risk:** None (validation only, no behavior change)

---

### [ ] Rate-Limit Telegram Webhook
**File:** `apps/api/app/routers/telegram_webhook.py`

**Change:**
```python
from app.middleware.rate_limit import limiter

@router.post("/webhook")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def webhook(request: Request, body: dict):
    # Process...
```

**Test:**
- ✓ 10 requests in 60 seconds → all pass
- ✓ 11th request in same window → 429 Too Many Requests

**Effort:** 5 minutes

---

### [ ] Role-Level Immutability: API Schema
**File:** `apps/api/app/schemas/assessment.py`

**Change:**
```python
from typing import Literal

class StartAssessmentRequest(BaseModel):
    competency_slug: str
    language: Literal["en", "az"] = "en"
    role_level: Literal["volunteer", "coordinator", "specialist", "manager", "senior_manager"]  # NEW

    @field_validator("role_level")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ["volunteer", "coordinator", "specialist", "manager", "senior_manager"]:
            raise ValueError("Invalid role_level")
        return v
```

**Test:**
- ✓ Valid role_level → 201 Created
- ✓ Invalid role_level → 422 Unprocessable Entity
- ✓ Missing role_level → 422 Unprocessable Entity

**Effort:** 10 minutes

---

### [ ] Role-Level Immutability: Router Update
**File:** `apps/api/app/routers/assessment.py`

**Change:**
```python
@router.post("/start", response_model=SessionOut, status_code=201)
@limiter.limit(RATE_ASSESSMENT_START)
async def start_assessment(
    request: Request,
    payload: StartAssessmentRequest,
    db_admin: SupabaseAdmin,
    db_user: SupabaseUser,
    user_id: CurrentUserId,
) -> SessionOut:
    """Start a new CAT session for a given competency."""
    competency_id = await _get_competency_id(db_admin, payload.competency_slug)

    # ... existing code ...

    session_id = str(uuid.uuid4())
    await db_user.table("assessment_sessions").insert({
        "id": session_id,
        "volunteer_id": user_id,
        "competency_id": competency_id,
        "status": "in_progress",
        "role_level": payload.role_level,  # NEW
        "theta_estimate": state.theta,
        # ... rest of fields ...
    }).execute()
```

**Test:**
- ✓ Session created with role_level='volunteer'
- ✓ Session created with role_level='manager'
- ✓ role_level persists in database

**Effort:** 10 minutes

---

### [ ] Role-Level Immutability: Database Migration
**File:** Create new migration `supabase/migrations/20260325000021_role_level_constraint.sql`

**Migration:**
```sql
-- Add NOT NULL constraint to role_level
UPDATE public.assessment_sessions
SET role_level = 'volunteer'
WHERE role_level IS NULL;

ALTER TABLE public.assessment_sessions
ALTER COLUMN role_level SET NOT NULL;

-- Add CHECK constraint
ALTER TABLE public.assessment_sessions
ADD CONSTRAINT chk_role_level
CHECK (role_level IN ('volunteer', 'coordinator', 'specialist', 'manager', 'senior_manager'));

-- Add comment for clarity
COMMENT ON COLUMN public.assessment_sessions.role_level
IS 'Role level for IRT difficulty calibration. Immutable after session creation. Sourced from org hierarchy, not user input.';
```

**Test:**
```bash
# Run locally:
supabase migration up

# Verify:
SELECT * FROM information_schema.table_constraints
WHERE table_name = 'assessment_sessions' AND constraint_name = 'chk_role_level';
# Should return 1 row
```

**Effort:** 5 minutes

---

## P1: DEPLOY NEXT SPRINT (High-severity design gaps)

### [ ] Evaluation Log Sanitization: Remove raw_score
**File:** `apps/api/app/routers/aura.py`

**Current behavior:**
```python
@router.get("/me/explanation")
async def get_explanation(db: SupabaseUser, user_id: CurrentUserId):
    # Returns per-answer breakdown with raw_score
    return {
        "answers": [
            {
                "question_id": "...",
                "evaluation_data": {
                    "raw_score": 0.72,  # ← REMOVE THIS
                    "criteria": "...",
                    "rationale": "..."
                }
            }
        ]
    }
```

**New behavior:**
```python
@router.get("/me/explanation")
@limiter.limit("1/day")  # NEW: Rate-limit to 1 per 24 hours
async def get_explanation(db: SupabaseUser, user_id: CurrentUserId):
    # Only return per-competency summary, not per-answer breakdown
    return {
        "summary": {
            "communication": {
                "overall_score": 72,
                "feedback": "You demonstrated clear communication with good structure..."
                # NO raw_score, NO per-answer breakdown, NO IRT hints
            },
            "reliability": { ... }
        }
    }
```

**Test:**
- ✓ First request within 24h → 200 OK
- ✓ Second request within same 24h → 429 Too Many Requests
- ✓ Response doesn't contain raw_score
- ✓ Response doesn't contain per-answer evaluation_data

**Effort:** 1.5 hours

---

### [ ] Hide IRT Parameters: Frontend Access Control
**File:** `apps/api/app/routers/assessment.py`

**Current behavior:**
```python
def _fetch_questions(db: SupabaseAdmin, competency_id: str) -> list[dict]:
    result = (
        await db.table("questions")
        .select("id, type, scenario_en, scenario_az, options, irt_a, irt_b, irt_c, ...")  # ← Exposes IRT params
        .execute()
    )
```

**New behavior:**
```python
def _fetch_questions(db: SupabaseAdmin, competency_id: str) -> list[dict]:
    result = (
        await db.table("questions")
        .select("id, type, scenario_en, scenario_az, options")  # ← REMOVE irt_a, irt_b, irt_c
        .eq("competency_id", competency_id)
        .eq("is_active", True)
        .execute()
    )
    # IRT parameters stay in database, only used server-side for CAT logic
    return result.data or []
```

**Test:**
- ✓ Question returned has id, type, scenario_en, scenario_az, options
- ✓ Question returned does NOT have irt_a, irt_b, irt_c
- ✓ Backend still has access to IRT params (for select_next_item)

**Effort:** 15 minutes

---

### [ ] Prevent Session Cherry-Picking: Database Constraint
**File:** Create new migration `supabase/migrations/20260325000022_unique_completed_session.sql`

**Migration:**
```sql
-- Only ONE completed assessment per volunteer per competency
ALTER TABLE public.assessment_sessions
ADD CONSTRAINT uc_volunteer_competency_completed
UNIQUE (volunteer_id, competency_id)
WHERE status = 'completed';

-- Add index for performance
CREATE INDEX idx_assessment_sessions_completed
ON public.assessment_sessions(volunteer_id, competency_id)
WHERE status = 'completed';

-- Add comment
COMMENT ON CONSTRAINT uc_volunteer_competency_completed
ON public.assessment_sessions
IS 'Enforce: users can complete each competency assessment only once. If retesting is allowed later, deprecate old sessions instead of creating new ones.';
```

**Test:**
```sql
-- Try to insert second completed session for same user/competency:
INSERT INTO assessment_sessions (
    volunteer_id, competency_id, status
) VALUES (
    '<user_id>', '<competency_id>', 'completed'
);
-- Should fail with: duplicate key value violates unique constraint

-- But abandoned/in_progress sessions are allowed:
INSERT INTO assessment_sessions (
    volunteer_id, competency_id, status
) VALUES (
    '<user_id>', '<competency_id>', 'in_progress'
);
-- Should succeed
```

**Effort:** 10 minutes

---

### [ ] Prevent Session Cherry-Picking: Router Validation
**File:** `apps/api/app/routers/assessment.py`

**Change:**
```python
@router.post("/start", response_model=SessionOut, status_code=201)
async def start_assessment(...) -> SessionOut:
    """Start a new CAT session for a given competency."""

    # Check for in-progress session
    existing_in_progress = (
        await db_user.table("assessment_sessions")
        .select("id")
        .eq("volunteer_id", user_id)
        .eq("competency_id", competency_id)
        .eq("status", "in_progress")
        .execute()
    )
    if existing_in_progress.data:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SESSION_IN_PROGRESS",
                "message": "Resume your active assessment; each competency can only be completed once",
                "session_id": existing_in_progress.data[0]["id"],
            },
        )

    # NEW: Check for completed session
    existing_completed = (
        await db_user.table("assessment_sessions")
        .select("id")
        .eq("volunteer_id", user_id)
        .eq("competency_id", competency_id)
        .eq("status", "completed")
        .execute()
    )
    if existing_completed.data:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ASSESSMENT_ALREADY_COMPLETED",
                "message": "You've already completed this assessment. Each competency is assessed once.",
            },
        )

    # ... continue with session creation ...
```

**Test:**
- ✓ First completed session → 201 Created
- ✓ Attempt to start second assessment for same competency → 403 Forbidden
- ✓ Abandoned/in_progress session can be resumed

**Effort:** 20 minutes

---

### [ ] Differential Privacy: Org Dashboard Aggregates
**File:** `apps/api/app/routers/organizations.py` (or new endpoint for dashboard)

**Current behavior:**
```python
@router.get("/dashboard/{org_id}/stats")
async def get_org_stats(org_id: str, db: SupabaseAdmin):
    gold_count = await db.table("aura_scores").select("*").eq("badge_tier", "gold").execute()
    silver_count = await db.table("aura_scores").select("*").eq("badge_tier", "silver").execute()
    # Returns exact counts: Gold=13, Silver=18 (enables inference attacks)
```

**New behavior:**
```python
import random

@router.get("/dashboard/{org_id}/stats")
async def get_org_stats(org_id: str, db: SupabaseAdmin):
    gold_actual = len(await db.table("aura_scores").select("*").eq("badge_tier", "gold").execute().data or [])
    silver_actual = len(await db.table("aura_scores").select("*").eq("badge_tier", "silver").execute().data or [])

    # Add differential privacy noise (±5% jitter)
    noise = lambda count: int(count * (1 + random.uniform(-0.05, 0.05)))

    return {
        "gold": noise(gold_actual),
        "silver": noise(silver_actual),
        "bronze": noise(bronze_actual),
        "none": noise(none_actual),
        "note": "Counts include ±5% statistical noise for privacy protection"
    }
```

**Test:**
- ✓ Two calls to same endpoint return slightly different numbers
- ✓ Variance is ±5% around true count
- ✓ Prevents exact inference attacks

**Effort:** 1 hour

---

## P2: DEPLOY IN FOLLOWING SPRINT (Medium-severity design gaps)

### [ ] Database Constraint: Badge Tier Consistency
**File:** Create migration `supabase/migrations/20260326000023_badge_tier_check.sql`

```sql
ALTER TABLE public.aura_scores
ADD CONSTRAINT chk_badge_matches_score
CHECK (
    (badge_tier = 'platinum' AND total_score >= 90.0) OR
    (badge_tier = 'gold' AND total_score >= 75.0 AND total_score < 90.0) OR
    (badge_tier = 'silver' AND total_score >= 60.0 AND total_score < 75.0) OR
    (badge_tier = 'bronze' AND total_score >= 40.0 AND total_score < 60.0) OR
    (badge_tier = 'none' AND total_score < 40.0)
);
```

**Effort:** 15 minutes

---

### [ ] Audit Trigger: Log AURA Score Updates
**File:** Create migration `supabase/migrations/20260326000024_aura_audit_trigger.sql`

```sql
CREATE TABLE IF NOT EXISTS public.aura_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id),
    old_total_score FLOAT,
    new_total_score FLOAT,
    old_badge_tier TEXT,
    new_badge_tier TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by TEXT,
    reason TEXT
);

CREATE OR REPLACE FUNCTION log_aura_update()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.aura_audit_log (
        volunteer_id, old_total_score, new_total_score,
        old_badge_tier, new_badge_tier, changed_by
    ) VALUES (
        NEW.volunteer_id,
        OLD.total_score,
        NEW.total_score,
        OLD.badge_tier,
        NEW.badge_tier,
        current_user_id()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_aura_update
AFTER UPDATE ON public.aura_scores
FOR EACH ROW
EXECUTE FUNCTION log_aura_update();
```

**Effort:** 30 minutes

---

## Summary

| Phase | Effort | Critical Fixes |
|-------|--------|---|
| **P0 (This Sprint)** | ~1 hour | Telegram HMAC validation + Role-level immutability |
| **P1 (Next Sprint)** | ~4 hours | Evaluation log sanitization + Session uniqueness + Differential privacy |
| **P2 (Following Sprint)** | ~2 hours | Database constraints + Audit logging |
| **Total** | ~7 hours | System moved from critical risk to defensible state |

---

## Validation Checklist

After each fix, verify:
- [ ] Code compiles without errors
- [ ] Unit tests pass (existing + new tests for fix)
- [ ] Integration tests pass (database migrations, API endpoints)
- [ ] Manual testing confirms fix blocks attack vector
- [ ] No regression in other endpoints
- [ ] Logging shows audit trail (especially for CRITICAL fixes)
- [ ] Performance impact < 5% (new rate limits, queries, crypto ops)

---

## Deployment Order

1. **Week 1:** Deploy P0 (Telegram + role_level)
   - Blocks CRITICAL exploits
   - Minimal code changes
   - No API breaking changes for clients

2. **Week 2-3:** Deploy P1 (evaluation logs + session uniqueness + privacy)
   - Requires client awareness (explanation endpoint now rate-limited)
   - Database migrations must run cleanly
   - Brief period where old sessions exist without constraint (acceptable)

3. **Week 4+:** Deploy P2 (constraints + audit logging)
   - No user-visible changes
   - Improves observability and future debugging

---

## Post-Deployment Monitoring

After each deployment, monitor:
- Telegram webhook error rates (spike = spoofing attempts?)
- Assessment start endpoint rejection rate (role_level validation)
- Explanation endpoint rate-limit hits (normal usage profile)
- Aura_audit_log growth (detects suspicious update patterns)
- Badge tier constraint violations (detects mutation attempts)

Set up alerts for:
- Telegram 401 errors > 5/hour
- Assessment start 403 errors > 10/day
- Aura_audit_log unusual changes (same user, score +50 in 1 minute)
