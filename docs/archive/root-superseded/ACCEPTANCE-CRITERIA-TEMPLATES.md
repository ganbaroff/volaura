# Acceptance Criteria Templates — VOLAURA
## Gherkin (Given/When/Then) Format — All Features

**Rule:** AC is written BEFORE coding starts. No exceptions. (Toyota Jidoka / Apple spec-first).
**Format:** Every AC must have ≥2 scenarios (happy path + at least 1 edge/failure case).

---

## Template: Standard Feature AC

```gherkin
Feature: [Feature Name]

Background:
  Given [shared preconditions across all scenarios]

Scenario: [Happy path — what works when everything is right]
  Given [starting state]
  When [user/system action]
  Then [observable outcome]
  And [secondary outcome if any]

Scenario: [Edge case — boundary condition]
  Given [edge state]
  When [action]
  Then [correct handling of edge]

Scenario: [Failure/unauthorized — what should NOT work]
  Given [wrong actor / wrong state]
  When [attempted action]
  Then [rejection with correct error]
```

---

## Domain Examples — VOLAURA B2B Talent Platform

### Assessment & AURA Score

```gherkin
Feature: IRT/CAT Adaptive Assessment

Background:
  Given a volunteer with a profile is authenticated

Scenario: Complete adaptability assessment — happy path
  Given the volunteer has no existing adaptability score
  When they complete 30 adaptive questions (CAT stops when SE < 0.3)
  Then an assessment_session row is created with status="completed"
  And aura_scores is updated with the new competency_score
  And badge_tier is recalculated (bronze/silver/gold/platinum)
  And an AURA ready email is sent (if EMAIL_ENABLED=true)

Scenario: Duplicate attempt — within 30 days
  Given the volunteer completed adaptability within the last 30 days
  When they attempt to start a new adaptability session
  Then the API returns HTTP 429 with "Assessment locked for 30 days"
  And no new assessment_session row is created

Scenario: Guest (unauthenticated) attempts assessment
  Given an unauthenticated user
  When they POST /api/assessment/start
  Then the API returns HTTP 401
  And no session is created
```

```gherkin
Feature: AURA Score Public Profile

Scenario: Volunteer with Gold badge visible to org
  Given a volunteer with visibility="public" and badge_tier="gold"
  When an org searches /api/volunteers?min_score=70
  Then the volunteer appears in results
  And the response includes total_score, badge_tier, and competency_scores
  And it does NOT include email, phone, or private fields

Scenario: Volunteer with private AURA not visible
  Given a volunteer with visibility="private"
  When an org searches /api/volunteers
  Then that volunteer is NOT in the results
  And the API returns HTTP 200 (not an error — just filtered out)

Scenario: RLS blocks cross-user score access
  Given Volunteer A is authenticated
  When they request GET /api/aura_scores?volunteer_id=VOLUNTEER_B_UUID
  Then the API returns HTTP 403 or empty result
  And Volunteer A's own score is NOT modified
```

### Organization Cold Search

```gherkin
Feature: Org Volunteer Search

Scenario: Org finds volunteer matching competency filter
  Given an authenticated org user
  And at least 1 volunteer with adaptability_score >= 80 and visibility="public"
  When they GET /api/volunteers?competency=adaptability&min_score=80
  Then at least 1 volunteer is returned
  And each result has: display_name, city, country, badge_tier, total_score

Scenario: Org searches with no matching volunteers
  Given an authenticated org user
  When they GET /api/volunteers?competency=adaptability&min_score=99
  Then the response returns HTTP 200 with empty results array
  And NOT HTTP 404 or an error

Scenario: Unauthenticated org search blocked
  Given an unauthenticated request
  When they GET /api/volunteers
  Then HTTP 401 is returned
```

### Authentication & Invite Gate

```gherkin
Feature: Invite-Gated Registration

Background:
  Given OPEN_SIGNUP=false and BETA_INVITE_CODE="VOLAURA2026"

Scenario: Valid invite code allows registration
  Given a new user with email new@example.com
  When they POST /api/auth/register with invite_code="VOLAURA2026"
  Then a new auth.users entry is created
  And a profiles row is created with account_type="volunteer"
  And the response returns HTTP 201

Scenario: Wrong invite code blocked
  Given OPEN_SIGNUP=false
  When they POST /api/auth/register with invite_code="WRONG"
  Then HTTP 403 is returned with "Invalid invite code"
  And no auth.users entry is created

Scenario: Open signup mode bypasses invite gate
  Given OPEN_SIGNUP=true (env var override)
  When they POST /api/auth/register without invite_code
  Then registration succeeds (HTTP 201)
```

### Transactional Email

```gherkin
Feature: AURA Ready Email

Background:
  Given EMAIL_ENABLED=true and RESEND_API_KEY is set

Scenario: Email sent after assessment completion
  Given a volunteer completes their adaptability assessment
  When the assessment is saved with status="completed"
  Then send_aura_ready_email is called with correct parameters
  And the email is sent to the volunteer's auth email
  And the subject is "Your Adaptability AURA score is ready"

Scenario: Email silently skipped when kill switch off
  Given EMAIL_ENABLED=false
  When assessment completes
  Then send_aura_ready_email returns immediately (no API call)
  And no error is raised
  And assessment completion is NOT blocked

Scenario: Email failure does not block assessment
  Given EMAIL_ENABLED=true and Resend API is down
  When assessment completes and email send fails
  Then the assessment is still saved as status="completed"
  And HTTP 200 is returned to the volunteer
  And a WARNING is logged (not an exception)
```

### Stripe / Payment (Post-Activation)

```gherkin
Feature: Pro Subscription Activation

Background:
  Given PAYMENT_ENABLED=true and STRIPE_WEBHOOK_SECRET is set

Scenario: Successful subscription webhook upgrades account
  Given a signed Stripe webhook: customer.subscription.created
  When it's received at POST /api/stripe/webhook
  Then the user's profiles.subscription_status is updated to "pro"
  And HTTP 200 is returned to Stripe

Scenario: Unsigned/invalid webhook rejected
  Given a POST to /api/stripe/webhook without Stripe-Signature header
  When received
  Then HTTP 400 is returned
  And no database changes are made

Scenario: Payment disabled rejects checkout
  Given PAYMENT_ENABLED=false
  When any user requests POST /api/stripe/create-checkout
  Then HTTP 503 is returned with "Payments not enabled"
```

---

## AC Quality Checklist

Before finalizing any AC, verify:

- [ ] **Testable:** Can be verified with code (not "it looks good")
- [ ] **Independent:** Each scenario can be tested alone
- [ ] **Specific:** No vague words ("works", "loads", "displays correctly")
- [ ] **Failure covered:** At least 1 scenario covers what should NOT happen
- [ ] **RLS covered:** Data isolation scenarios for any multi-user feature
- [ ] **Kill switch covered:** If feature has a kill switch, test with it off AND on

---

## AC → DoD Connection

AC (this document) answers: **"Did we build the right thing?"**
DoD (`QUALITY-SYSTEM.md` Section 4) answers: **"Did we build it right?"**

Both must pass. Neither alone is sufficient.
