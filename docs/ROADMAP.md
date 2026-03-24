# Volaura — Product Roadmap

**Owner:** Yusif Ganbarov (CEO) + Claude (CTO)
**Format:** Timeline-based with outcome milestones
**Updated:** 2026-03-25
**Rule:** CTO reads this at every session start. Priorities come from HERE, not from CEO.

---

## NOW — March 2026 (Sprint 3)

**Goal: Live demo for Pasha Bank pitch. Everything else waits.**

| # | Deliverable | Status | Business reason |
|---|-------------|--------|-----------------|
| 1 | API live on Railway (28 endpoints) | DONE | Backend for demo |
| 2 | Frontend live on Vercel (volaura.app) | DONE | User-facing app |
| 3 | Assessment E2E flow (start → answer → complete → AURA score) | DONE | Core product proof |
| 4 | Organizations API (CRUD + volunteer search) | DONE (fixed 2026-03-25) | B2B feature for Pasha |
| 5 | Privacy Policy page | NOT STARTED | Legal blocker for B2B |
| 6 | Pasha Bank pitch deck with live demo | IN PROGRESS | 7,000 AZN contract |
| 7 | LinkedIn Post #2 published | READY (text finalized) | Brand visibility |
| 8 | HNSW index for pgvector | NOT STARTED | Performance for search |
| 9 | LLM mock for tests | NOT STARTED | Test reliability |

**Sprint 3 success = Pasha Bank sees live demo. Score calculated. Organization dashboard works.**

**Deadline: 2026-03-31**

---

## NEXT — April–May 2026 (Sprint 4)

**Goal: First 10 paying organizations. GITA grant application submitted.**

| # | Deliverable | Business reason |
|---|-------------|-----------------|
| 1 | Register Georgian legal entity | Unlocks GITA ($240K), 0% tax 10 years |
| 2 | GITA Georgia grant application | Largest funding: up to $240K |
| 3 | Bulk CSV volunteer invite (50+) | Orgs need mass onboarding |
| 4 | Org → volunteer assessment assignment | Core B2B workflow |
| 5 | Results export (PDF/Excel) | HR teams need reports |
| 6 | Post-assessment results page (badge reveal) | Volunteer retention |
| 7 | Full RLS policy audit | Security for enterprise clients |
| 8 | IRT engine unit tests | Quality assurance for core algorithm |
| 9 | 10 beta organizations onboarded | Product-market fit signal |
| 10 | Astana Hub application (Kazakhstan, $5-20K) | Multi-country grant pipeline |

**Sprint 4 success = 10 orgs pay. GITA submitted. 50+ volunteers have AURA scores.**

---

## LATER — June–September 2026 (Sprints 5-6)

**Goal: 500 verified volunteers. 3 grant applications active. Turkish expansion started.**

| # | Deliverable | Business reason |
|---|-------------|-----------------|
| 1 | Turkiye Tech Visa application | Grants + technopark + visa |
| 2 | KOSGEB grant (Turkey, ~$50K) | Operational costs covered |
| 3 | Offline assessment (PWA) | Mobile-first users in field events |
| 4 | Push notifications (org views profile) | Volunteer engagement loop |
| 5 | HR system API/webhook (1C/SAP) | Enterprise integration — zero friction |
| 6 | Cost-per-assessment documented | Unit economics for investors |
| 7 | Test coverage 80% critical paths | Release confidence |
| 8 | LinkedIn content calendar (weekly) | Consistent brand presence |
| 9 | QazInnovations application (Kazakhstan, $40-160K) | Requires acceleration program first |

**Phase 1 milestone (September 30): 500+ volunteers, 10+ paying orgs, 1,000+ assessments.**

---

## Q4 2026 — Phase 2: Tbilisi

**Goal: Second city. Prove the model works outside Azerbaijan.**

| # | Deliverable | Business reason |
|---|-------------|-----------------|
| 1 | Tbilisi chapter launch (if GITA approved) | Geographic expansion proof |
| 2 | 2,000+ volunteers across 2 countries | Scale signal for investors |
| 3 | 30+ paying organizations | Revenue diversification |
| 4 | Company-verified badges API | New B2B revenue stream ($2-5/badge) |
| 5 | MiroFish Architecture post (LinkedIn + GitHub) | Technical credibility + Anthropic visibility |
| 6 | Register Kazakhstan entity (Astana Hub) | Unlocks Almaty market entry |

---

## H1 2027 — Phase 3: Istanbul + New Products

**Goal: 5,000 volunteers. 3 countries. New revenue streams.**

| # | Deliverable | Business reason |
|---|-------------|-----------------|
| 1 | Istanbul chapter launch | Turkey = 85M population, event capital |
| 2 | AI Assessment API as standalone product | B2B SaaS: $2-5 per test, 500+ clients |
| 3 | Professional orientation for children (14-22) | New market: schools + parents (Duolingo model) |
| 4 | Full HR dashboard + company-branded tests | Enterprise feature set |
| 5 | UN agencies + PwC + Deloitte as target clients | High-value contracts |

---

## H2 2027 — Phase 4: Scale + Fundraise

**Goal: Series A readiness. Regional dominance.**

| # | Deliverable | Business reason |
|---|-------------|-----------------|
| 1 | 10,000+ volunteers, 5+ countries | Data moat = competitive advantage |
| 2 | Series A pitch ($500K–$1M) | Scale team, accelerate expansion |
| 3 | MiroFish Decision Simulator MVP | Second product: "predict human decisions" |
| 4 | Almaty chapter launch | Central Asia entry |
| 5 | AURA as industry standard (like ISO for people) | Long-term vision: become the certification layer |

---

## Grant Calendar (hard deadlines)

| When | What | Amount | Action | Status |
|------|------|--------|--------|--------|
| March 2026 | Pasha Bank pitch | 7,000 AZN | Deck + live demo | IN PROGRESS |
| April 2026 | GITA Georgia | up to $240K | Register GE company, apply | NOT STARTED |
| May 2026 | Astana Hub | $5-20K | Online application | NOT STARTED |
| June 2026 | Turkiye Tech Visa | Grant + technopark | turkiyetechvisa.gov.tr | NOT STARTED |
| July 2026 | KOSGEB (Turkey) | ~$50K | After TR company registration | NOT STARTED |
| Sept 2026 | QazInnovations (KZ) | $40-160K | After acceleration program | NOT STARTED |

**At 50% grant success rate: ~$175K in year 1.**

---

## Revenue Projections

| Period | Monthly gross | Annual gross | Source |
|--------|-------------|-------------|--------|
| Month 6 (Sept 2026) | ~$3K | ~$36K | 30 orgs (AZ only) |
| Month 12 (Dec 2026) | ~$8.9K | ~$106K | 80 orgs (AZ only) |
| Month 12 (multi-country) | ~$16-23K | $190-280K | AZ + Turkey + KZ |
| Month 18 (mid-2027) | ~$30-50K | $360-600K | 3 countries + API product |

---

## Known Gaps

| Gap | Impact | Owner | When to solve |
|-----|--------|-------|---------------|
| No press coverage about Yusif | Wikipedia ineligible, weak PR | Yusif (partnerships) | Q2-Q3 2026 |
| Financial model not built | Can't pitch investors | CTO (build) | Before GITA application |
| LinkedIn post calendar undefined | Inconsistent brand presence | CTO (create) | This week |
| No beta tester pipeline | Sprint 4 depends on 10 orgs | Yusif (network) | April 2026 |
| No legal entity outside AZ | Blocks all grant applications | Yusif (register GE) | April 2026 |

---

## How CTO Uses This Document

1. **Session start:** Read ROADMAP.md → know what sprint we're in → know priorities
2. **Choosing next task:** Pick from current section (NOW/NEXT/LATER), not from CEO
3. **Saying "no" to new ideas:** If it's not in NOW or NEXT → goes to IDEAS-BACKLOG.md
4. **Reporting to CEO:** One line per deliverable. Status changed or blocked. No technical details.
5. **Updating:** After every sprint, move items between sections. Add new grants/deadlines.

---

*Previous files absorbed into this roadmap: EXECUTION-PLAN.md (Sprint 1-3), BACKLOG.md (Sprints 3-6), MASTER-STRATEGY.md (grants + revenue), ROADMAP-TO-9.md (Phase 1-4 vision).*
