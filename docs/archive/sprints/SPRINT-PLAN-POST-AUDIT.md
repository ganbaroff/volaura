# Volaura Post-Audit Sprint Plan

> Generated: 2026-03-28 | Source: Feature Audit (78 features), Security Audit (39 findings), External Review (8/10), Production Bug Report
> Operator: 1 CTO (Claude AI). CEO (Yusif) sees outcomes only. No real users. $50/mo budget.
> Testing: CTO uses MCP tools, curl, browser preview, Supabase dashboard. No external testers.

---

## Sprint Priority Logic

1. Ship blockers (the product literally cannot be used)
2. Remaining OWASP security (7/22 unfixed)
3. Wire existing backend to frontend (12 PARTIAL features)
4. Empty states and error handling (production polish)
5. Backend-only features that unlock org revenue
6. New features only after 1-5 are solid

---

## SPRINT 1 — SHIP BLOCKERS (2 days)

**Goal:** Remove every blocker that prevents a new user from completing signup-to-AURA.

| # | Task | Why |
|---|------|-----|
| 1 | Apply 5 pending migrations to production Supabase | BUG-07. Database schema is behind. Nothing works correctly until migrations are current. |
| 2 | Fix email confirmation flow (or disable it) | BUG-08. Registration is broken. Option A: wire Supabase email confirm with redirect. Option B: disable email confirm in Supabase auth settings for MVP (faster, revisit later). Recommend Option B. |
| 3 | Wire forgot/reset password to Supabase Auth | Currently stub. Users who forget passwords are permanently locked out. Use Supabase `resetPasswordForEmail` + update password page. |
| 4 | Empty state for /aura page (no scores yet) | BUG from Audit 3 (fixed 404, but verify). New user with 0 assessments should see "Take your first assessment" CTA, not an error. |
| 5 | Smoke test: full flow signup -> onboarding -> assessment -> AURA reveal | CTO walks through as Leyla persona. Every screen must load. Every transition must work. Document any blockers found. |

**CEO sees:** "A new person can sign up, take an assessment, and see their AURA score. Registration works."
**Risk if skipped:** Product is unusable. Everything else is academic.

---

## SPRINT 2 — SECURITY CLOSURE (2 days)

**Goal:** Close remaining 7 OWASP findings. No HIGH severity items left open.

| # | Task | Why |
|---|------|-----|
| 1 | Assessment retest cooldown (HIGH) | Users can retry assessments indefinitely to game scores. Add `cooldown_hours` check in `POST /assessment/start`. 72h default. Store last_completed_at per competency per user. |
| 2 | BrandedBy TOCTOU race condition (HIGH) | Crystal deduction for BrandedBy has same double-spend risk fixed for main crystals. Apply `deduct_crystals_atomic()` pattern or `pg_advisory_lock` to BrandedBy endpoints. |
| 3 | Differential privacy on org dashboard (HIGH) | Org admins can see individual volunteer scores. Add k-anonymity threshold: if group < 5 volunteers, show only aggregate. |
| 4 | Rate limits on 15 remaining endpoints (MEDIUM) | Add slowapi rate limits to all public-facing endpoints missing them. Batch: auth endpoints (5/min), assessment endpoints (10/min), search/discovery (30/min). |
| 5 | UUID validation on path parameters (MEDIUM) | Add Pydantic UUID type to all router path params. Currently strings pass through, causing 500s on invalid UUIDs instead of 422s. |
| 6 | Fix column mismatch delta vs amount (MEDIUM) | Audit found inconsistent naming. One migration to rename + update references. |

**CEO sees:** "Security audit is 22/22. No open vulnerabilities."
**Risk if skipped:** Any security-aware reviewer (investor, partner org) will flag these. Assessment gaming destroys score credibility.

---

## SPRINT 3 — WIRE BACKEND TO FRONTEND (3 days)

**Goal:** Connect 8 existing backend endpoints to frontend pages. Zero new backend code.

| # | Task | Why |
|---|------|-----|
| 1 | Notifications page: replace mock data with `GET /api/notifications` | Page exists with hardcoded data. Backend exists. Wire TanStack Query hook. Add empty state. |
| 2 | Events page: replace mock data with `GET /api/events` | Same pattern. Wire real data. Add empty state for "no upcoming events." |
| 3 | Profile verifications: wire to `GET /api/verifications` | Currently hardcoded `[]`. Show verification badges when data exists, "No verifications yet" when empty. |
| 4 | Organization: wire CSV invite upload to `POST /api/invites/csv` | Org admin page exists. Upload component exists. Wire the actual API call. |
| 5 | Organization: wire assign-assessment to `POST /api/assessment/assign` | Org can assign assessments to volunteers. UI button exists, not connected. |
| 6 | Leaderboard: add jump-to-rank for users ranked >20 | Session 54 built `GET /api/leaderboard/me`. Use it to scroll/highlight user's position. |

**CEO sees:** "Notifications, events, verifications, org tools all show real data instead of placeholders."
**Risk if skipped:** Product feels fake. 49% of features are LIVE but the 15% PARTIAL ones are the most visible user-facing pages.

---

## SPRINT 4 — ASSESSMENT REFACTOR + DESCRIPTION (2 days)

**Goal:** Split the 870-line assessment router. Add pre-assessment context so users know what they are being tested on.

| # | Task | Why |
|---|------|-----|
| 1 | Split `assessment.py` (870 lines) into 3 files | External review flagged 38KB single file. Split into: `assessment_session.py` (start/submit/status), `assessment_evaluation.py` (LLM eval logic), `assessment_admin.py` (assign/manage). |
| 2 | Add assessment description screen before start | Users don't know what they're being tested on or that AI evaluates them. Add a pre-assessment page: competency name, what it measures, how scoring works, estimated time. |
| 3 | Add assessment progress persistence verification | Session 53 added Zustand persist. Verify: close browser mid-assessment, reopen, progress restored. Fix if broken. |
| 4 | Assessment results: show per-question breakdown | After assessment, user sees only final score. Add expandable breakdown: question, user answer, score, brief explanation. |

**CEO sees:** "Users understand what they're being tested on. Assessment code is maintainable. Results are transparent."
**Risk if skipped:** Bus factor = 1 and the biggest router is unmaintainable. Users distrust scores they don't understand.

---

## SPRINT 5 — ORG DASHBOARD + B2B WIRING (3 days)

**Goal:** Make the organization side functional enough for a pilot org to use.

| # | Task | Why |
|---|------|-----|
| 1 | Org dashboard: wire volunteer list with AURA scores | Backend `GET /api/organizations/{id}/volunteers` exists. Show table: name, AURA score, badge tier, last active. |
| 2 | Org dashboard: wire event management (create/edit) | Backend `POST/PUT /api/events` exists. Add create/edit form. Wire to API. |
| 3 | Org dashboard: wire registration management | Backend exists for approve/reject volunteer registrations. Add UI list with action buttons. |
| 4 | Org dashboard: wire volunteer rating | Backend `POST /api/organizations/{id}/rate` exists. Add star/comment form after events. |
| 5 | B2B search: wire `GET /api/discovery/search` to org search page | Orgs need to find volunteers by competency. Backend has semantic search. Wire to a search UI. |

**CEO sees:** "An organization admin can manage volunteers, events, and search for talent. B2B side works."
**Risk if skipped:** No revenue path. Orgs are the paying customers. Without this, Volaura is a portfolio project.

---

## SPRINT 6 — PRODUCTION POLISH + EMPTY STATES (2 days)

**Goal:** Every page handles zero-data, loading, and error states gracefully.

| # | Task | Why |
|---|------|-----|
| 1 | Audit every page for empty states | Systematic pass: dashboard, aura, events, notifications, profile, leaderboard, org pages. Each must have a meaningful empty state with CTA. |
| 2 | Audit every page for loading states | Replace any raw spinner or missing skeleton with consistent loading UI. |
| 3 | Audit every page for error states | Every API call must have error boundary or catch. No "Something went wrong" without context. Show retry button + what went wrong. |
| 4 | Mobile responsiveness pass | Bottom nav is done (Session 53). Verify every page works on 375px width. Fix overflow, text truncation, touch targets. |
| 5 | Telegram error leak fix (LOW security) | Sanitize error messages in Telegram webhook responses. |

**CEO sees:** "The app feels complete. No broken screens. Works on mobile."
**Risk if skipped:** First impression is everything. A single broken screen kills trust with pilot orgs.

---

## SPRINT 7 — EMAIL NOTIFICATIONS + CRYSTAL ECONOMY MVP (3 days)

**Goal:** Users get emails for important events. Crystal economy exists in simplest form.

| # | Task | Why |
|---|------|-----|
| 1 | Email notifications via Supabase Edge Functions | Assessment complete, new badge earned, org invitation received. Use Supabase `pg_net` or Edge Function + Resend/Postmark (free tier). 3 templates max. |
| 2 | Crystal balance display on profile/dashboard | Backend `crystals` column exists. Show balance. Show transaction history from `crystal_transactions` table. |
| 3 | Crystal earn rules (simplest version) | Complete assessment = +10 crystals. Earn badge = +25 crystals. Referral = +50 crystals. Hardcode in backend. No shop, no spending, no complexity. |
| 4 | Crystal spend: unlock detailed AURA breakdown | One spend action only. 5 crystals = see detailed per-question scores. Test the atomic deduction function built in Session 53. |

**CEO sees:** "Users get email when something happens. Crystals exist and have a reason to earn/spend them."
**Risk if skipped:** Without notifications, users forget the platform exists. Without crystals, there is no engagement loop. But both are worthless if Sprints 1-6 are incomplete.

---

## SPRINT 8 — FIRST REAL USER TEST + LAUNCH PREP (2 days)

**Goal:** One real human (not CTO) completes the full flow. Fix everything that breaks.

| # | Task | Why |
|---|------|-----|
| 1 | CEO (Yusif) walks through full flow on phone | Signup, onboarding, assessment (1 competency), AURA reveal, share, view leaderboard. CEO reports what confused him. |
| 2 | Fix top 3 issues from CEO test | Whatever breaks or confuses, fix immediately. |
| 3 | Invite 3-5 real volunteers (Yusif's network) | Give them the link. Observe via Supabase dashboard: who signed up, who completed assessment, where they dropped off. |
| 4 | Collect feedback, create bug/improvement backlog | Transform feedback into prioritized issues for next cycle. |
| 5 | Production monitoring: set up error alerting | Supabase logs + Railway logs. Telegram notification to CEO on 5xx errors. |

**CEO sees:** "Real people used the product. We know what works and what doesn't. We have data, not assumptions."
**Risk if skipped:** The external review's most critical finding: "55 sessions without a single real user." This sprint exists to break that pattern.

---

## What Is NOT In These 8 Sprints

These are explicitly deferred until the core is solid and real users exist:

| Feature | Why deferred |
|---------|-------------|
| Messaging system | Needs user base to be useful. Build after 50+ active users. |
| Admin dashboard | CTO uses Supabase dashboard directly. Build when there's an ops team. |
| Conference/video | Phase 3 feature. Not MVP. |
| Advanced crystal economy (shop, marketplace) | External review called it "too complex for MVP." Earn/spend basics only. |
| Multi-language beyond AZ/EN | No demand signal yet. |
| BrandedBy integration | Separate product. Volaura core must work first. |
| AI Twin / advanced skills | Skills infrastructure exists (Session 51). Activate after core loop proven with real users. |

---

## Success Criteria (after Sprint 8)

- [ ] New user can signup, assess, get AURA score, share it (Sprint 1)
- [ ] 22/22 OWASP findings closed (Sprint 2)
- [ ] All PARTIAL features show real data (Sprint 3)
- [ ] Assessment is understandable and maintainable (Sprint 4)
- [ ] Org admin can manage volunteers and events (Sprint 5)
- [ ] No broken/empty screens on any page (Sprint 6)
- [ ] Users receive email notifications, crystals work (Sprint 7)
- [ ] At least 1 real human completed the full flow (Sprint 8)
- [ ] Feature audit moves from 49% LIVE to 75%+ LIVE

---

## Estimated Timeline

| Sprint | Duration | Cumulative |
|--------|----------|-----------|
| 1 - Ship Blockers | 2 days | Day 2 |
| 2 - Security | 2 days | Day 4 |
| 3 - Wire Backend | 3 days | Day 7 |
| 4 - Assessment Refactor | 2 days | Day 9 |
| 5 - Org Dashboard | 3 days | Day 12 |
| 6 - Polish | 2 days | Day 14 |
| 7 - Email + Crystals | 3 days | Day 17 |
| 8 - Real User Test | 2 days | Day 19 |

**Total: ~19 working days (4 weeks).** Aggressive but achievable for a single CTO working full sessions.
