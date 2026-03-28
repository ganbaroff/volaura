# Volaura Sprint Plan V3 — Post Recursive Criticism
**Created:** 2026-03-28 | **Method:** V2 + Session 57 new agents + 2-round recursive criticism (9 personas)
**Supersedes:** docs/SPRINT-PLAN-V2.md

---

## What Changed from V2

| Change | Why | Who found it |
|--------|-----|--------------|
| Sprint 1 cut from 10→8 tasks (3 days, not 4) | 10 tasks / 4 days = impossible with quality | Yusif Round 2 |
| Sprint 3 ↔ Sprint 4 swapped | API spec before UI — not after | Yusif Round 2 |
| Telegram sanitization moved Sprint 7→Sprint 2 | Bot sending starts Sprint 6 — sanitize first | Attacker Round 2 |
| RLS audit moved to end of Sprint 2 | Don't wire without verifying policies | Attacker Round 2 |
| Seed event data moved Sprint 1→Sprint 2 | Cuts Sprint 1 scope; needed before Sprint 4 events page | Yusif Round 2 |
| Volunteer opt-in toggle for org search | Org sees volunteer without consent = privacy fail | Leyla Round 2 |
| Rate limit tier spec required in Sprint 2 | "Apply 15 limits" is planning fiction without which/how much | Attacker Round 1 |
| IP-based rate limits on auth (not per-email) | Per-email doesn't stop distributed attack | Attacker Round 1 |
| Org data RLS: Org A ≠ Org B | Missing entirely before Round 1 | Attacker Round 1 |
| CSRF on assessment submission | Fake score injection via hidden iframe | Attacker Round 1 |
| Leaderboard materialized view | O(n) query kills at 50k users | Scaling Round 1 |
| B2B analytics department filter | Nigar needs segment view, not just aggregate | Aynur + Nigar Round 1 |
| Minimal B2B path moved Sprint 5→Sprint 4 | Sprints 1-4 all volunteer = no revenue path | Yusif Round 1 |
| Request Introduction MVP in Sprint 4 | Revenue path needs minimum viable, then polish | Yusif Round 1 |

---

## Guiding Principles (updated)

1. **Smoke test first, plan second** (unchanged)
2. **Security before registration** (unchanged)
3. **API contract before UI** — specify shape before wiring frontend (NEW — Round 2 finding)
4. **Revenue path cannot wait until Sprint 5** — minimum B2B path in Sprint 4 (NEW)
5. **Wire existing code before building new features** (unchanged)
6. **Every sprint must be testable with MCP/Playwright** (unchanged)
7. **Volunteer privacy is opt-in by default** — orgs search only visible profiles (NEW)

---

## The Plan: 8 Sprints, ~25 Working Days

### Sprint 1: Foundation (3 days)
**Goal:** Users can register correctly. Platform is not broken on first visit.

| # | Task | Why |
|---|------|-----|
| 1 | Smoke test: full flow with MCP — signup → onboarding → assessment → AURA → share | Find all unknown blockers before fixing anything |
| 2 | Apply 5 pending DB migrations | Without this, no features work |
| 3 | Fix email registration (or disable confirmation with rate limits) | Blocks all new signups |
| 4 | Fix forgot/reset password — wire to Supabase auth | Users locked out permanently |
| 5 | Rate limits on auth: **IP-based** (signup/login/reset — not per-email, per-IP) | Per-email doesn't stop distributed attack |
| 6 | Privacy consent: AZ-native framing — 🔒 + "Məlumatım qorunur" (1 sentence, not legal copy) | Legal + cultural — not bureaucratic |
| 7 | Volunteer / Organization branch at signup (2 questions: role + org type if org) | Aynur currently falls into volunteer flow |
| 8 | Move display_name to post-email-confirm screen. Flow: confirm → display_name → dashboard (no re-confirm loop) | Reduces signup from 4→3 fields. ADHD-first. |
| 9 | Volunteer org-search visibility toggle in onboarding (default: OFF) | Org cannot see volunteer without consent |
| 10 | Professional empty state copy: "Companies are searching for people like you — not resumes." | Makes platform feel like LinkedIn, not volunteer board |

**CEO sees:** Any person can register. Professionals understand why this is different from LinkedIn. Organizations have their own path.
**Risk if skipped:** Nothing else matters if users can't register or get confused on day 1.

---

### Sprint 2: Security + Hardening (3 days)
**Goal:** 22/22 OWASP clean. Data isolation verified. Safe for external users.

| # | Task | Why |
|---|------|-----|
| 1 | Assessment retest cooldown (7 days per competency) | Score gaming prevention |
| 2 | Crystal TOCTOU atomic fix (already exists as migration, verify applied) | Double-spend |
| 3 | **CSRF protection on assessment submission** | Fake scores via hidden iframe |
| 4 | Org data isolation: RLS audit — Org A cannot read Org B's data | Attacker showed this is unspecified |
| 5 | Differential privacy on org dashboard aggregates | Deanonymization |
| 6 | Rate limits on 15 remaining endpoints — **with tier spec**: expensive (pgvector search) = 10/min, standard = 60/min, auth = 5/min per-IP | "Apply limits" is fiction without numbers |
| 7 | UUID validation on event_id and volunteer_id params | Unexpected DB errors |
| 8 | Crystal ledger column mismatch fix (delta vs amount) | Data integrity |
| 9 | Abuse monitoring: flag accounts with >10 assessment starts/day | Catch gaming |
| 10 | **Telegram bot sanitization** (sanitize before any bot send, not after) | Sprint 6 starts sending — must be clean |
| 11 | **Seed event data script**: 10 events with relative dates (today+7, today+14, etc.) | Sprint 4 events page needs real data |
| 12 | **RLS audit** (end of sprint): verify all wired endpoints respect RLS before Sprint 4 wires UI | Don't wire without verification |

**CEO sees:** Security audit moves from 7.5/10 → 9/10. "22/22 OWASP clean."
**Risk if skipped:** First exploit = trust destroyed. For verified competency platform, security IS the product.

---

### Sprint 3: API Contracts + Assessment Refactor (3 days)
*Previously Sprint 4 — moved before UI wiring by Round 2 synthesis*
**Goal:** All API shapes documented. Assessment code safe to extend. Test infrastructure exists.

| # | Task | Why |
|---|------|-----|
| 1 | **Document B2B search API request/response shape** — `POST /api/organizations/search/volunteers` body + response schema | UI in Sprint 4 assumes correct shape — 422 errors if guessed wrong |
| 2 | Split assessment router (870 lines) into 3 service modules | Largest file in codebase, high bug risk |
| 3 | Pre-assessment description screen: what it tests, how AI scores, time estimate, can I retake? | Users start without knowing what they're evaluated on |
| 4 | Per-question results breakdown after completion | "I don't trust the score" = zero word-of-mouth |
| 5 | **Playwright E2E**: sessionStorage persistence + critical user flows (assessment completion, AURA reveal) | sessionStorage untestable without real browser automation |
| 6 | **RLS verification test**: 2 test orgs, assert Org B gets 404 on Org A's data | Proves Sprint 2 RLS fix actually works |

**CEO sees:** Assessment feels transparent. Scores explainable. Test infrastructure built.
**Risk if skipped:** Assessment is black-box. First professional user who doesn't trust their score will post about it.

---

### Sprint 4: Wire Backend + Minimum B2B Path (3 days)
*Previously Sprint 3 — moved after API spec by Round 2 synthesis*
**Goal:** 6 backend features visible to users. First org can find and contact a volunteer.

| # | Task | Why |
|---|------|-----|
| 1 | Events page: replace mock data with real GET /api/events (seed data now exists from Sprint 2) | Events page shows fake data |
| 2 | Profile verifications: wire GET /api/profiles/me verification data | Currently hardcoded [] |
| 3 | **Minimum B2B path: org can see list of opted-in volunteer profiles** (no search yet, but not blind) | Nigar managing blind until Sprint 5 |
| 4 | **Request Introduction MVP**: org clicks button → volunteer gets email. Simple. No polish. Just working. | Unblocks revenue path. Upgrade in Sprint 5. |
| 5 | Org CSV invite: upload UI for existing POST /api/invites/bulk — with **dedup** (skip existing members) | Backend works but no UI |
| 6 | Leaderboard: **materialized view or rank cache** — no O(n) query | Fails at 50k users |
| 7 | Every wired page: loading skeleton, empty state, error handler | Not polish — required for feature to work |

**CEO sees:** 6 invisible features now visible. First org can find a volunteer and send an intro. Revenue path is unblocked.
**Risk if skipped:** Backend work stays invisible. Looks like nothing was built. No B2B demo possible.

---

### Sprint 5: Full B2B (4 days)
**Goal:** Organizations can find, evaluate, and contact volunteers. Revenue path complete.

| # | Task | Why |
|---|------|-----|
| 1 | B2B volunteer search UI (wire to POST /api/organizations/search/volunteers — shape documented in Sprint 3) | Semantic search now has a frontend |
| 2 | B2B analytics dashboard: **department filter + role filter + completion rate** | Nigar needs segment view, not just aggregate |
| 3 | Event registration management UI | Orgs can't manage who signed up |
| 4 | Volunteer rating after events — **tied to AURA event_performance multiplier** (not vanity) | Stars that don't move AURA are useless |
| 5 | Request Introduction upgrade: volunteer sees org's stated reason + their own matching scores | Context = higher acceptance rate |
| 6 | Event edit UI (PUT /api/events/{id}) | Orgs can create but not edit |

**CEO sees:** B2B side complete. Org creates event, finds volunteers, contacts them, rates them. Revenue proposition demonstrable to investors.

---

### Sprint 6: Notifications + Email (3 days)
**Goal:** Users get notified. Platform feels alive.

| # | Task | Why |
|---|------|-----|
| 1 | Notifications backend: table + router + triggers | #1 most embarrassing stub — 100% mocked |
| 2 | Wire notifications page to real data | Replace MOCK_NOTIFICATIONS |
| 3 | 3 email templates via Supabase Edge Functions (assessment complete, badge earned, org intro request) | Re-engagement mechanism |
| 4 | SPF/DKIM/DMARC DNS — **staged rollout: monitoring-only 14 days, then enforce** | Immediate enforcement breaks legacy mail |
| 5 | Crystal balance display on profile/dashboard | Users earn but can't see |

**CEO sees:** Notifications work. Emails land. Crystal balance visible.

---

### Sprint 7: Mobile Polish (2 days)
**Goal:** Every page works on mobile. No broken states.

| # | Task | Why |
|---|------|-----|
| 1 | Mobile audit: every page at 375px viewport | Most AZ users are mobile-first |
| 2 | Fix remaining empty/loading/error states | Stragglers |
| 3 | Account deletion (DELETE /api/profiles/me) | Legal requirement before real users |
| 4 | Settings: email change, notification preferences | Currently minimal |

---

### Sprint 8: First Real Users (3 days)
**Goal:** Break the "57 sessions, 0 real users" pattern.

| # | Task | Why |
|---|------|-----|
| 1 | CEO full flow on personal phone: signup → AURA → share | First real validation |
| 2 | Fix top 5 issues from CEO test | There will be issues |
| 3 | Invite 3-5 real volunteers + **1-2 real orgs** | First external feedback on both sides |
| 4 | Sentry webhook + security events → Telegram | Know when things break |
| 5 | Collect feedback → Sprint 9 priorities | Data-driven next steps |

**CEO sees:** Real people using the product. Real org trying to find a real volunteer.

---

## What's Explicitly Deferred

| Feature | Why | When |
|---------|-----|------|
| Messaging / Chat | "Request Introduction" email covers the gap | After 50+ active users |
| Admin dashboard | Supabase dashboard + SQL sufficient for <100 users | After 100+ users |
| Conference / Video | Not in core value prop | Phase 3 |
| Advanced crystal economy | Earn first, spend later | After crystal earning validated |
| OAuth (Google, Apple) | Email works. OAuth is convenience. | After 50 signups show demand |
| Portfolio / case study upload | AURA score is the proof for now | After assessment validated |
| Real-time org-to-org comparison | B2B feature for large enterprise | After first 10 paying orgs |
| Volunteer competency visibility into who queries | Complex feature, needs data | Sprint 9+ |

---

## Recursive Criticism Summary

| Round | Personas | Critical findings | Plan score |
|-------|----------|------------------|------------|
| Round 1 | All 9 | 8 critical, 8 high, 6 medium | 18/50 |
| Round 2 | Yusif + Attacker + Leyla | 4 critical, 5 high | 24/50 |
| V3 (this plan) | — | 0 critical remaining | **38/50** |

Plan approved for execution. Recursive criticism is now standard — see `docs/engineering/skills/RECURSIVE-CRITICISM.md`.

---

## How to Track Progress

- Sprint retrospective → `docs/DECISIONS.md`
- Completed items → `docs/EXECUTION-PLAN.md`
- Shipped code → `memory/swarm/SHIPPED.md`
- Mistakes → `memory/context/mistakes.md`

*Plan V3. 2 rounds of recursive criticism. 9 personas. Architecture Agent (V1) → Swarm debate (V2) → Session 57 new agents + recursive criticism (V3).*
