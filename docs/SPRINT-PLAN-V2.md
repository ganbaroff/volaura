# Volaura Sprint Plan v2 — Post-Audit
**Created:** 2026-03-28 | **Method:** 3-round swarm review (Architecture → Product + Security critics → Synthesis)

---

## What We Know

| Metric | Value |
|--------|-------|
| Features audited | 78 |
| Live | 38 (49%) |
| Partial / Stub | 20 (25%) |
| Missing | 20 (26%) |
| Security findings | 39 total, 7 OWASP still open |
| Production bugs found | 1 fixed (AURA 404), more expected |
| Real users tested | 0 |

## Guiding Principles (from swarm debate)

1. **Smoke test first, plan second** — walk the full flow before listing fixes
2. **Security before registration** — don't open doors you can't lock
3. **Wire existing code before building new features** — 12 backend endpoints have no frontend
4. **Empty/error states are not polish** — they're part of wiring
5. **Every sprint must be testable with MCP tools** — no dependency on real users until Sprint 8
6. **No messaging/admin/conference until core is solid** — defer complexity

---

## The Plan: 8 Sprints, ~25 Working Days

### Sprint 1: Smoke Test + Ship Blockers (3 days)
**Goal:** A person can sign up, complete onboarding, take an assessment, see their AURA score.

| # | Task | Why |
|---|------|-----|
| 1 | Walk full flow with MCP tools: signup → onboarding → assessment → AURA → share | Discovers all unknown blockers before we plan fixes |
| 2 | Apply 5 pending database migrations to production | Without this, new features don't reach users |
| 3 | Fix email registration flow (or add rate limits if disabling confirmation) | Currently blocks all new signups |
| 4 | Fix forgot/reset password — wire frontend to Supabase auth | Users locked out permanently if they forget password |
| 5 | Add rate limits to auth endpoints (signup, login, reset) | Mandatory if registration is open |
| 6 | Add privacy policy consent checkbox to signup | Legal requirement before any real user data |

**CEO sees:** Working signup-to-AURA flow end-to-end. Can share link and someone can actually use it.
**Risk if skipped:** Nothing else matters if users can't register.

---

### Sprint 2: Security Closure (3 days)
**Goal:** 22/22 OWASP findings closed. Platform safe for external users.

| # | Task | Why |
|---|------|-----|
| 1 | Assessment retest cooldown (7 days per competency) | Users can game scores by retrying indefinitely |
| 2 | Fix BrandedBy crystal TOCTOU race — use atomic RPC | Double-spend vulnerability |
| 3 | Add differential privacy to org dashboard aggregates | Prevents deanonymization of volunteers |
| 4 | Rate limits on remaining 15 endpoints | All public endpoints must be rate-limited |
| 5 | UUID validation on event_id and volunteer_id params | Prevents unexpected DB errors |
| 6 | Fix crystal ledger column mismatch (delta vs amount) | Data integrity |
| 7 | Basic abuse monitoring: flag accounts with >10 assessment starts/day | Catch gaming before admin dashboard exists |

**CEO sees:** Security audit score moves from 7.5/10 to 9/10. "22/22 OWASP clean" — investor-grade security posture.
**Risk if skipped:** First exploit = trust destroyed. For a "verified competency" platform, security IS the product.

---

### Sprint 3: Wire Backend to Frontend (3 days)
**Goal:** 8 existing backend features become visible to users. Zero new backend code.

Prerequisite: Half-day RLS/authorization audit of all endpoints being wired.

| # | Task | Why |
|---|------|-----|
| 1 | Events page: replace mock data with real `GET /api/events` | Events page currently shows fake data |
| 2 | Profile verifications: wire `GET /api/profiles/me` verification data | Currently hardcoded `[]` |
| 3 | Org CSV invite: build upload UI for existing `POST /api/invites/bulk` | Backend works but no UI |
| 4 | Org assign assessment: build UI for `POST /api/organizations/assign-assessments` | Backend works but no UI |
| 5 | Leaderboard jump-to-rank: scroll to user's position automatically | Users ranked >20 can't find themselves |
| 6 | Every wired page gets: loading skeleton, empty state, error handler | Not polish — required for the feature to work |

**CEO sees:** 6 previously invisible features now work from the UI. Events page shows real events, not placeholder data.
**Risk if skipped:** Backend work stays invisible. Looks like nothing was built.

---

### Sprint 4: Assessment UX (3 days)
**Goal:** Assessment is clear, trustworthy, and maintainable.

| # | Task | Why |
|---|------|-----|
| 1 | Pre-assessment description screen: what it tests, how AI scores, estimated time | Users start without knowing what they're being evaluated on |
| 2 | Split assessment router (870 lines) into 3 service modules | Largest single file in codebase, high-risk for bugs |
| 3 | Per-question results breakdown after completion | Users want to know which answers were strong/weak |
| 4 | Assessment persistence: verify sessionStorage survives page refresh | Users lose progress if they accidentally close tab |

**CEO sees:** Users understand what they're signing up for. Results feel transparent, not black-box.
**Risk if skipped:** "I don't trust the score" = zero word-of-mouth.

---

### Sprint 5: Org Dashboard + B2B (4 days)
**Goal:** Organizations can find, evaluate, and contact volunteers. This is the revenue path.

| # | Task | Why |
|---|------|-----|
| 1 | B2B volunteer search UI (wire to `POST /api/organizations/search/volunteers`) | Backend's semantic search is live but has no frontend |
| 2 | B2B analytics dashboard (wire to `GET /api/organizations/me/dashboard`) | Orgs need to see their volunteer data |
| 3 | Event registration management UI | Orgs can't manage who signed up for events |
| 4 | Volunteer rating after events | Orgs can rate volunteers, feeds into AURA |
| 5 | "Request Introduction" email bridge — org clicks → volunteer gets email | Without this, search is a dead end. Minimal contact mechanism. |
| 6 | Event edit UI (wire to `PUT /api/events/{id}`) | Orgs can create but not edit events |

**CEO sees:** The B2B side works. An org can create events, find volunteers, contact them, rate them. Revenue proposition is demonstrable.
**Risk if skipped:** Volaura is a portfolio project, not a business.

---

### Sprint 6: Notifications + Email (3 days)
**Goal:** Users get notified when something happens. Platform feels alive.

| # | Task | Why |
|---|------|-----|
| 1 | Build notifications backend: table + router + triggers | Currently 100% mocked — the #1 most embarrassing stub |
| 2 | Wire notifications page to real data | Replace MOCK_NOTIFICATIONS |
| 3 | 3 email templates via Supabase Edge Functions (assessment complete, badge earned, event invite) | Users need a reason to come back |
| 4 | SPF/DKIM/DMARC DNS records for volaura.com | Emails won't be delivered without this |
| 5 | Crystal balance display on profile/dashboard | Users earn crystals but can't see them |

**CEO sees:** Users get emails. Notifications page shows real activity. Crystal balance visible.
**Risk if skipped:** Platform feels dead. No re-engagement mechanism.

---

### Sprint 7: Mobile Polish + Final Sweep (2 days)
**Goal:** Every page works on mobile. No embarrassing states.

| # | Task | Why |
|---|------|-----|
| 1 | Mobile responsiveness audit: every page on 375px viewport | Most Azerbaijani users are mobile-first |
| 2 | Fix any remaining empty/loading/error states missed in Sprint 3-6 | Catch stragglers |
| 3 | Telegram bot error message sanitization | Currently leaks exception text |
| 4 | Account deletion endpoint (`DELETE /api/profiles/me`) | Legal requirement before real users |
| 5 | Settings page: add email change, password change, notification preferences | Currently minimal |

**CEO sees:** Product feels polished on phone. No broken states anywhere.
**Risk if skipped:** First impression on mobile = last impression.

---

### Sprint 8: First Real Users (3 days)
**Goal:** Break the "55 sessions, zero real users" pattern.

| # | Task | Why |
|---|------|-----|
| 1 | CEO walks full flow on personal phone (signup → AURA → share) | First real validation |
| 2 | Fix top 5 issues from CEO test | There will be issues |
| 3 | Invite 3-5 real volunteers (WUF13 alumni, personal contacts) | First external feedback |
| 4 | Set up error alerting (Sentry webhook → Telegram) | Know when things break |
| 5 | Security event monitoring: failed auth, rate limit hits → Telegram | Catch abuse attempts |
| 6 | Collect feedback, prioritize Sprint 9 | Data-driven next steps |

**CEO sees:** Real people using the product. Real feedback. Real proof that Volaura works.
**Risk if skipped:** Everything before this is hypothetical.

---

## What's Explicitly Deferred

| Feature | Why deferred | When to build |
|---------|-------------|---------------|
| Messaging / Chat system | Core loop doesn't need it yet. "Request Introduction" email covers the gap. | After 50+ active users |
| Admin dashboard | CTO uses Supabase dashboard + SQL monitoring. Not worth building for <100 users. | After 100+ users |
| Conference / Video rooms | Not in core value prop. Users use Zoom/Meet. | Phase 3 (if ever) |
| Advanced crystal economy (shops, spending UI) | Users need to earn crystals first. Too complex for first 100 users. | After crystal earning validated |
| BrandedBy AI Twin improvements | Works end-to-end already. Not on critical path. | When users request it |
| Multi-language expansion (RU, TR) | AZ + EN sufficient for Azerbaijan launch | After CIS expansion decision |
| OAuth (Google, Apple) | Email auth works. OAuth is convenience, not blocker. | After first 50 signups show demand |

---

## How to Track Progress

- Each sprint ends with a retrospective entry in `docs/DECISIONS.md`
- Completed items marked in `docs/EXECUTION-PLAN.md`
- All shipped code logged in `memory/swarm/SHIPPED.md`
- Mistakes added to `memory/context/mistakes.md`

---

*Plan v2. Created by swarm: Architecture Agent (plan) → Product Agent (5 criticisms) → Security Agent (5 criticisms) → CTO synthesis. 3 rounds of review before presenting to CEO.*
