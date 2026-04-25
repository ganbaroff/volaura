# VOLAURA 500-Hour Execution Plan
**Generated:** 2026-04-02 | **Method:** 4-agent swarm audit + cross-critique
**Agents:** Security, Growth, Codebase, Retrospective
**Scope:** From current state (0 real users, beta-ready API) → 1000 paying organizations

---

## The Real Constraint

Before all else: **VOLAURA has no real users.** Every hour before first real user is infrastructure investment with zero feedback. The plan below front-loads user acquisition ruthlessly and defers infrastructure scaling until usage justifies it.

**Ground truth (as of 2026-04-02):**
- API: 336 tests, deployed on Railway, no real user has registered
- Web: Deployed on Vercel, org onboarding bug fixed, assessment flow works
- Revenue: $0. Paddle not set up. `payment_enabled=False`.
- The product is beta-ready. The bottleneck is not code — it's the first human using it.

---

## Hour Budget Allocation

| Phase | Hours | What It Buys |
|-------|-------|-------------|
| Phase 0: First Real User | 10 | CEO E2E walk + invite 3 friends |
| Phase 1: Security Hardening | 30 | Zero attack surface before public launch |
| Phase 2: First 100 Users | 80 | warm-network activation + onboarding polish |
| Phase 3: First Revenue | 60 | Paddle + org tier + billing flow |
| Phase 4: AURA Quality | 80 | IRT calibration, score explainer, reeval |
| Phase 5: Growth Engine | 80 | Viral loop, public profiles, referrals |
| Phase 6: B2B Org Funnel | 70 | Org dashboard, team management, CSV import |
| Phase 7: Ecosystem Bridge | 60 | MindShift crystal bridge, ZEUS API, Life Sim cloud |
| Phase 8: Scale Infra | 30 | DB-backed rate limiter, pgvector tuning, RLS audit |
| **Total** | **500** | |

---

## Phase 0: First Real User (10 hours)
**"Done" definition: 1 real human (not CEO) completes an assessment and sees their AURA score.**

### Hour 1-2: CEO E2E Walk
- CEO walks volaura.app with a real email (not developer account)
- Registers → profile setup → assessment → sees AURA score
- Notes every friction point (copy, timing, confusion)
- Creates a Loom recording of the walk

### Hour 3-5: Fix Friction from CEO Walk
- Fix whatever friction was found (copy changes, routing, timing)
- These are never known until a real human tries

### Hour 6-8: First 3 Invitations
- CEO invites 3 known people from his event/operations network (not developers)
- Invites go via Telegram/WhatsApp with personal message (not bulk)
- Goal: 1 completion, not 3. One human finishing = product validated.

### Hour 9-10: First Data Review
- Look at what assessment scores came back
- Are scores reasonable? Are questions clear?
- Document findings → feed into Phase 4

---

## Phase 1: Security Hardening (30 hours)
**"Done" definition: Security agent rates readiness ≥8/10. Zero CVSS≥7 open.**

### Completed (BATCH-R, 0 hours remaining)
- [x] `open_signup` default → `False`
- [x] LLM daily cap fail-closed
- [x] Resume 409 → redirect (not error)
- [x] Org onboarding routing fixed

### Remaining (30 hours)
**Hour 1-5: Telegram webhook hardening**
- Flip telegram webhook to fail-closed when no secret
- Add startup assertion: `if not telegram_webhook_secret and app_env == "production": raise`
- Test with real Telegram message

**Hour 6-15: Email confirmation**
- Enable `enable_confirmations = true` in Supabase Dashboard (5 min, requires CEO login to supabase.io)
- Add `Resend` (free tier) as transactional email provider
- 3 transactional emails: confirm account, assessment ready, weekly AURA update
- Template: Azerbaijani first, Russian second, English fallback

**Hour 16-22: RLS audit pass**
- Verify each table: SELECT/INSERT/UPDATE/DELETE policies correct
- Specifically: `assessment_sessions` (can user see others' sessions?), `aura_scores` (public read?), `organizations` (owner-only write?)
- Document confirmed-clean list

**Hour 23-28: Rate limiter → DB-backed**
- Replace slowapi in-memory with Supabase counter (SQL approach, $0 cost)
- Table: `rate_limit_buckets(key TEXT, count INT, window_start TIMESTAMPTZ)`
- Atomic upsert via PostgreSQL ON CONFLICT DO UPDATE
- Survives Railway restarts

**Hour 29-30: Pen test basics**
- Run OWASP ZAP (free) against API
- Fix any HIGH findings
- Document results

---

## Phase 2: First 100 Users (80 hours)
**"Done" definition: 100 users with completed AURA scores. ≥5 returning (second assessment).**

### Hour 1-15: Warm Network Activation
Yusif's event and operations network is the highest-density warm list currently available.

- Create invite system: `beta_invite_code` → unique codes per organization
- Event-network announcement: "Test your AURA score for free"
- Target: 200 signups → 100 completions (50% completion rate assumption)
- Track: where do people drop off? (signup → profile → assessment → score)

**Onboarding improvements (informed by CEO walk):**
- Reduce assessment time estimate on landing page (reality: 3-4 min per competency, not 5)
- Add progress indicator in assessment: "Question 3 of 7"
- Show sample AURA score BEFORE signup (demo profile: `/u/volaura-demo`)

### Hour 16-35: Mobile UX Polish
50%+ of the early warm-network cohort will be mobile. Current web is responsive but not mobile-first.

- Audit every screen on iPhone 13 + Android mid-range
- Fix touch targets (min 44px)
- Fix assessment question card overflow on small screens
- Fix AURA radar chart on mobile (currently SVG, may be too small)
- Test with Azerbaijani text (longer words → layout breaks)

### Hour 36-55: Assessment Quality Pass
Bad assessment questions = wrong AURA scores = users don't trust the platform.

- Review all questions with 3 real volunteers
- Replace jargon-heavy questions (volunteers may not speak corporate English)
- Add Azerbaijani translations for all questions (critical: primary market)
- Calibrate IRT difficulty parameters from first 100 responses

### Hour 56-70: Retention Hooks
- "Your AURA improved!" notification after retest (email + in-app)
- "3 orgs viewed your profile" notification (social proof)
- Weekly email: "Complete [competency] to improve your score"

### Hour 71-80: First Public Case Study
- Pick 1 volunteer with good AURA score
- Write their story (with permission): "How Ayan improved her reliability score from 72 to 89"
- Post on volaura.app/blog + LinkedIn
- This converts passive visitors to registrations

---

## Phase 3: First Revenue (60 hours)
**"Done" definition: First paid organization subscription. Even 1 AZN proves willingness to pay.**

### Hour 1-10: Paddle Setup (CEO does, not CTO)
- CEO creates Paddle account (no company needed initially)
- Create 2 products: Org Starter ($29/mo, 10 active candidates), Org Growth ($99/mo, unlimited)
- Webhook endpoint already wired (`payment_enabled=False` → flip to `True`)
- Test checkout with test card

### Hour 11-25: Org Subscription Flow
- "Upgrade to search candidates" CTA on org dashboard
- Paywall: org can VIEW public profiles free, but contact/filter requires paid
- Checkout → Paddle → webhook → `subscription_tier = "pro"` in DB
- Cancellation flow: graceful downgrade, data retention 90 days

### Hour 26-40: Invoice & Receipts
- Paddle sends automatic receipts
- Add billing history page in org dashboard
- "Your subscription renews on [date]" in org settings

### Hour 41-50: First 5 Org Outreach
- Identify 5 NGOs/social orgs in Azerbaijan that recruit volunteers
- Send personalized demo: "Here's what AURA says about your current event-talent pool"
- Offer 3-month free trial if they bring 20+ people to assess
- This is CEO's work, but CTO supports with demo data + org setup

### Hour 51-60: Revenue Reporting
- Admin dashboard: MRR, churn, new orgs this month
- Telegram bot `/revenue` command: shows live MRR
- Set revenue target: $1,000 MRR = launch success signal

---


## Phase 4: AURA Quality (80 hours)
**"Done" definition: Users trust their score. Repeat assessors see improvement. Score explains itself.**

### Hour 1-20: Score Explainer
Current: user sees AURA score + radar chart. No explanation of what it means or how to improve.

- "Your AURA: 73/100" → "What this means" expandable section
- Per-competency breakdown: "Communication 82 — Strong. Leadership 61 — Room to grow."
- Improvement tips per competency (3 bullet points, ADHD-friendly, no fluff)
- Show percentile vs similar volunteers (privacy: only show if ≥50 users in category)
- Incorporate regional labor market data to provide more relevant and actionable insights

### Hour 21-40: IRT Calibration
- After 100+ assessments: run IRT parameter estimation on response data
- Update question difficulty/discrimination parameters in DB
- Questions with low discrimination (all users answer same) → replace or remove
- Questions with ceiling effect (everyone scores 1.0) → increase difficulty

### Hour 41-60: Transparent Evaluation Log
- "How was this score calculated?" link on AURA score card
- Show: which questions were asked, what concepts were evaluated, LLM or keyword scoring
- No raw prompt/response exposure — just competency concepts
- Builds trust with skeptical users

### Hour 61-80: Retest & Improvement Loop
- Enable retest after 7 days (currently 7-day cooldown enforced)
- Show "Score history" chart: last 3 assessments over time
- "You improved 8 points in Leadership since last month" notification
- This is the retention engine: users come back to see improvement

---

## Phase 5: Growth Engine (80 hours)
**"Done" definition: Viral coefficient ≥ 0.3 (every 10 users bring 3 more organically).**

### Hour 1-20: Public Profile Optimization
Public profile (`/u/username`) is the growth surface — it's visible to unauthenticated visitors.

- SEO: proper `<title>`, `<meta description>`, OpenGraph tags on public profile
- "Verify your AURA score" CTA for unauthenticated visitors
- Profile share cards (already built in `/u/[username]/card`)
- LinkedIn share: "I just got my AURA score. Join me →"

### Hour 21-40: Referral System
- "Invite a colleague" button in dashboard
- Unique referral link: `volaura.app/join?ref=username`
- Referral rewards: +5 AURA XP for referrer when invitee completes assessment
- Track: referral attribution in analytics_events

### Hour 41-60: Organization Discovery
- Public org directory: organizations can opt in to "looking for talent"
- User can browse orgs and apply
- This creates supply (people want to be discovered) AND demand (orgs want verified talent)

### Hour 61-80: Content Engine
- Blog: "What makes a great contributor?" → SEO traffic
- Monthly "AURA Leaderboard" (opt-in): top improving profiles this month
- "Member of the Month" case study: written by community, published with consent

---

## Phase 6: B2B Org Funnel (70 hours)
**"Done" definition: 5 paying organizations actively using platform to recruit.**

### Hour 1-25: Org Dashboard v2
Current org dashboard is minimal. Organizations need:
- Candidate pipeline view: "Applied to your org", "Shortlisted", "Accepted"
- Filter by AURA score, competency, location, availability
- Saved searches (already built) + email alerts for new matches
- Bulk invite: "Invite 50 volunteers via CSV"

### Hour 26-45: Intro Request Flow
- Org sees interesting volunteer → sends intro request
- Volunteer gets notification: "[Org name] wants to connect"
- Volunteer accepts/declines (anonymous until accepted)
- Once accepted: contact info shared, intro facilitated

### Hour 46-60: Team Management
- Org admin can add team members (HR managers, program coordinators)
- Role-based: Owner (full access), Manager (view + contact), Viewer (view only)
- Audit log: who accessed which candidate profile

### Hour 61-70: Org Onboarding Sequence
- After org registers: 5-email onboarding sequence over 14 days
- Day 1: "Set up your org profile"
- Day 3: "Search your first candidate"
- Day 7: "You have X candidates matching your criteria"
- Day 14: "Try premium search filters"

---

## Phase 7: Ecosystem Bridge (60 hours)
**"Done" definition: MindShift crystal → VOLAURA AURA connection works end-to-end.**

### Hour 1-20: VOLAURA ↔ MindShift Bridge
- `character_events` table already exists
- Crystal event from MindShift: POST `/api/character/crystal-event` with JWT + crystal_amount
- Store in `character_events`: user_id, source=mindshift, event_type=crystal_earned, amount, session_id
- AURA score boost: +0.1 AURA XP per 10 crystals (capped at 5 XP/day from MindShift)
- MindShift user sees "✨ Your focus earned 3 AURA XP today"

### Hour 21-40: ZEUS Integration
- ZEUS can query VOLAURA API: "What's my current AURA score?"
- ZEUS Reflect loop uses AURA score as performance signal
- ZEUS can trigger "I just completed a task" → crystal event → AURA XP

### Hour 41-60: Life Simulator Cloud Save
- `CLOUD_ENABLED=true` in Life Simulator
- Character state synced to VOLAURA `character_state` table
- Life Sim events (level up, achievement) → crystal events → AURA XP
- This creates the cross-product engagement loop the CEO designed

---

## Phase 8: Scale Infrastructure (30 hours)
**"Done" definition: Platform handles 10,000 concurrent users without degradation. Costs stay under $200/mo.**

*This phase starts ONLY when Phase 2 (100 users) is complete. Building for scale before users is waste.*

### Hour 1-10: Database Optimization
- Add missing indexes (run EXPLAIN ANALYZE on slowest queries)
- pgvector: test at 10,000 embeddings — is HNSW still fast?
- Connection pooling: PgBouncer via Supabase (already available)

### Hour 11-20: Railway Multi-Instance
- Test horizontal scaling: 2 Railway instances behind load balancer
- Replace in-memory rate limiter with Supabase SQL counter (Phase 1 item)
- Stateless sessions: verify no session state in process memory

### Hour 21-30: Monitoring + SRE
- Sentry: error rate dashboard, P95 latency, alert on >5 errors/minute
- Uptime monitoring: Better Uptime (free tier)
- Runbook: "API is down" → 5 diagnostic steps → escalation path

---

## The Order Matters

```
Week 1:  Phase 0 (first real user, CEO E2E) + Phase 1 remaining (email confirmation, Telegram hardening)
Week 2:  Phase 3 Hours 1-10 (Paddle setup, CEO action) + Phase 2 Hours 1-15 (warm-network wave)
Week 3:  Phase 2 Hours 16-55 (mobile + assessment quality)
Week 4:  Phase 4 Hours 1-20 (score explainer) + Phase 2 Hours 56-80 (retention)
Month 2: Phase 3 full (revenue) + Phase 5 Hours 1-40 (viral)
Month 3: Phase 6 (B2B) + Phase 4 remaining (IRT calibration)
Month 4: Phase 5 remaining (content) + Phase 7 (ecosystem bridges)
Month 5: Phase 8 (scale infra — only when justified by users)
```

---

## What CTO Does vs CEO Does

**CTO (Claude) owns:**
- All code changes, bug fixes, infrastructure
- Test coverage, deployment pipeline
- Architecture decisions with CEO approval

**CEO (Yusif) owns — cannot be delegated:**
- E2E walk (Hour 1-2 of Phase 0) — only a real user perspective counts
- Paddle account setup — no company ID available to CTO
- Warm-network outreach — personal relationships, CTO cannot substitute
- First org sales calls — trust requires human connection
- Decision: when to open `open_signup=True`

**The blocking constraint is always CEO actions, not CTO code.**

---

## Anti-Patterns This Plan Avoids

| Anti-Pattern | How This Plan Avoids It |
|-------------|------------------------|
| Building analytics before first user | Analytics track second, users first |
| Infrastructure for 10,000 users with 0 | Phase 8 gated on Phase 2 completion |
| Prioritizing ecosystem over core product | Ecosystem in Phase 7 (hours 380-440) |
| Security theater (fixing anon key instead of real P0) | Cross-critique removed misclassified issues |
| CEO-directed outreach outsourced to bot | CEO actions explicitly listed, not automated |

---

*Plan authored: 2026-04-02. Swarm input: Security agent (4 P0/P1 findings), Growth agent (resume bug, username, org routing), Codebase agent (63 migrations, schema validation), Retrospective agent (first-user definition, wrong priority diagnosis). Cross-critique: Security challenged Growth's P0 classification; Growth challenged Security's config.toml flag. Result: 2 of 4 "P0" items correctly downgraded.*

