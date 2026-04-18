# GITA GEORGIA GRANT APPLICATION PACKAGE

**Cross-references:** [[MASTER-STRATEGY]] | [[VISION-FULL]] | [[financial-model]] | [[MONETIZATION-ROADMAP]]

**Volaura — Application 2026**
**Applicant:** Yusif Ganbarov
**Company:** Volaura Georgia LLC
**Date:** April 2026
**Grant Amount:** 150,000 GEL (~$55,000)

---

## 1. EXECUTIVE SUMMARY

### VOLAURA: THE VERIFIED TALENT PLATFORM

**PROBLEM:**
LinkedIn's self-reported "Top 10%" skills are meaningless. Professionals have no credible way to prove their real competencies, and employers waste ~40% of hiring time validating unverified credentials. Current solutions are either enterprise-only tools or rely on self-declaration. The skills verification gap costs employers billions annually and keeps talented candidates invisible to the organizations that need them.

**SOLUTION:**
Volaura's AI-powered adaptive assessment engine verifies 8 core professional competencies in ~30 minutes. Candidates earn Platinum/Gold/Silver/Bronze badges backed by Item Response Theory (IRT/CAT) testing — third-party AI-verified, not self-declared. Organizations search talent by verified skill and score, not unverified CVs.

**POSITIONING (supreme rule — do not dilute):**
Volaura is a **verified talent platform**. Not a volunteer platform. Not a LinkedIn skin. The product's sole job is to prove that a person actually has a skill they claim, in a way that an employer trusts.

**MARKET OPPORTUNITY:**
- Azerbaijan: 1.2M LinkedIn users, ~500K actively searching or switching jobs annually
- CIS region: 50M+ professionals on LinkedIn; ~8M annual job transitions
- Global HR tech market: $35B (2024), projected $47B by 2028
- Pre-hire assessment subsegment: $4B, growing 10%+ YoY
- Skills-based hiring movement: 73% of US/EU employers are shifting away from degree-based screening (LinkedIn Workforce Report 2024)

**TRACTION:**
- MVP live on production (volaura.app) with backend deployed to Railway, frontend on Vercel, Supabase Postgres + pgvector
- Assessment engine operational with adaptive testing (IRT 3PL + EAP)
- Target by end of grant period: 500 verified professional profiles, 10 organizational partners

**TEAM:**
- Yusif Ganbarov — Founder & CEO
- AI-assisted development (Claude Code + MiroFish swarm system of 13 specialised perspectives + ~118 skill modules coordinating across multiple LLM providers)

**ASK:**
150,000 GEL for product development, go-to-market execution, and market expansion into Georgia + wider CIS.

---

## 2. COMPANY DESCRIPTION

### 2.1 Legal Information
- **Company Name:** Volaura Georgia LLC
- **Legal Form:** Limited Liability Company
- **Registration Number:** [TO BE COMPLETED]
- **Virtual Zone Status:** Applied
- **Address:** [TO BE COMPLETED]
- **Owner:** Yusif Ganbarov (100%)

### 2.2 Mission Statement
To replace self-reported skill claims with third-party AI-verified competency scores — so that talented people can prove what they know, and employers can find them without wasting weeks on unreliable screening.

### 2.3 Vision
The new standard for professional credibility: every candidate has an AURA score the way they have a GPA. Every competency is backed by adaptive testing and expert verification, not a checkbox on a profile.

---

## 3. PRODUCT & SERVICE

### 3.1 Core Product: Volaura Platform

**AURA Score:**
- 8 professional competencies measured
- 0-100 composite score with transparent weighting
- Badge tiers: Platinum (≥90) / Gold (≥75) / Silver (≥60) / Bronze (≥40)
- Publicly shareable on LinkedIn, Telegram, any platform
- Re-takeable after 90 days to show growth

**Competencies Measured (current weights):**
1. Communication — 0.20
2. Reliability — 0.15
3. English Proficiency — 0.15
4. Leadership — 0.15
5. Event Performance — 0.10
6. Tech Literacy — 0.10
7. Adaptability — 0.10
8. Empathy & Safeguarding — 0.05

### 3.2 Technology Stack
- **Frontend:** Next.js 14 (React, TypeScript, App Router)
- **Backend:** FastAPI (Python 3.11+, async)
- **Database:** Supabase (PostgreSQL + pgvector for semantic search)
- **AI Engine:** Multi-provider LLM router (Gemini, Groq, Cerebras, NVIDIA NIM, OpenRouter, Ollama local)
- **Assessment Engine:** Pure-Python IRT/CAT (3PL + EAP adaptive testing)
- **AI Video (optional product line):** BrandedBy AI Twin via SadTalker/MuseTalk/Kling

### 3.3 Competitive Advantage

| Feature | LinkedIn | Pre-hire tests (HireVue, etc.) | Volaura |
|---|---|---|---|
| Skills verification | Self-reported | Employer-initiated only | Candidate-initiated, public |
| Adaptive testing (IRT/CAT) | No | Some | Yes |
| Candidate owns the credential | No | No | Yes |
| Multi-language (AZ/RU/EN/TR) | Partial | Limited | Yes (6 locales) |
| Open API | Limited | Enterprise only | Yes |
| Transparent scoring formula | No | No | Yes (published weights) |
| Price point | Free but limited | $100-500 per candidate | Free tier + Pro subscription |

**Primary moat:** Volaura makes the assessment **candidate-owned** — a person takes the test once and shares the result with any employer they choose. HireVue and similar tools are gated per-employer. LinkedIn does nothing. Volaura closes the gap: third-party credibility + candidate control.

---

## 4. MARKET ANALYSIS

### 4.1 Total Addressable Market (TAM)

**Global HR Tech Market:**
- 2024: ~$35B (Gartner, Grand View Research)
- 2028 projection: ~$47B
- Pre-hire assessment subsegment: ~$4B, 10%+ CAGR
- Skills-based hiring is mainstream — 73% of US/EU employers actively shifting away from degree-based screening

**Azerbaijan:**
- Population: 10.1M
- LinkedIn users: 1.2M (+20% YoY)
- Active job searchers/switchers annually: ~500K
- Registered companies: ~50K
- Corporate HR departments hiring annually: thousands

**CIS Region:**
- LinkedIn professionals: 50M+
- Annual job transitions: ~8M across Russia, Ukraine, Kazakhstan, Georgia, Uzbekistan
- HR tech adoption is 5-7 years behind Western Europe — blue-ocean for Azerbaijani/Georgian-based SaaS

### 4.2 Serviceable Addressable Market (SAM)

Narrow focus for years 1-3:
- Azerbaijan, Georgia, Turkey, and select CIS countries
- Professionals actively seeking employment or promotion
- HR departments at mid-market companies (50-500 employees) validating candidates
- Recruitment agencies placing candidates into 100+ open roles at a time

Estimated SAM: **~500K professional candidates and ~5K employing organizations by Year 5**.

### 4.3 Serviceable Obtainable Market (SOM)

Conservative launch trajectory:
- **Year 1 (2026):** 5,000 verified candidate profiles, 10 organizational partners
- **Year 2 (2027):** 25,000 candidates, 50 organizations
- **Year 3 (2028):** 50,000 candidates, 100 organizations

---

## 5. MARKETING STRATEGY

### 5.1 Zero-CAC Content Engine
- **LinkedIn content:** 3 posts per week (Tue/Wed/Thu, 9 AM Baku time)
- **Format priority:** Carousels (21.7% engagement rate in current data), founder-voice storytelling, contrarian takes on self-reported skills
- **Content mix:** 40% storytelling (founder journey, candidate case studies), 35% educational (how IRT works, what makes a credible score), 25% product updates
- **K-factor target:** ≥1.0 — each verified candidate brings at least one more through badge-sharing and referral crystals

### 5.2 User Acquisition

**B2B (primary revenue engine):**
- Recruitment agencies in Baku, Tbilisi, Istanbul
- Mid-market company HR departments (50-500 employees)
- Corporate L&D programs using AURA for internal skill mapping
- HR tech integration partners (ATS systems)

**B2C (top-of-funnel + product-led growth):**
- Free AURA score → Pro subscription upsell (detailed breakdown, coaching, retake privileges)
- Public badge sharing drives organic discovery
- University partnerships (graduating students get first AURA score free)

### 5.3 Channels

| Channel | Cost | Expected Users | Timeline |
|---|---|---|---|
| LinkedIn organic | $0 | 2,000 | 12 months |
| Recruitment agency partnerships | $0 | 1,500 | 6 months |
| HR tech integrations | $5K | 1,000 | 9 months |
| University partnerships | $0 | 500 | 12 months |

---

## 6. OPERATIONS

### 6.1 Team Structure (Year 1)
- **CEO:** Yusif Ganbarov
- **Technical delivery:** AI-assisted development via Claude Code + MiroFish swarm (13 specialised perspectives + ~118 skill modules across multiple LLM providers for code review, security audit, architecture, UX research)
- **Contractors:** React developer, Python developer (3 months each, funded by grant)
- **Advisors:** [Pending]

### 6.2 Development Timeline

**Phase 1 (Months 1-3): Production hardening + verification loop**
- Complete assessment engine (all 8 competencies live)
- User authentication hardening
- Public profile page + badge sharing
- First-user E2E smoke gate

**Phase 2 (Months 4-6): Organization side**
- Organization dashboard (search, filter, invite)
- Saved searches + notifications
- Intro request flow (crystal-gated)
- API v1 for HR tech integrations

**Phase 3 (Months 7-9): Scale + mobile**
- Mobile PWA (already deployed) → native build
- Advanced analytics + Pro tier activation
- Multi-language content expansion
- University/corporate partnership pilots

### 6.3 Key Milestones

| Milestone | Target Date | Success Metric |
|---|---|---|
| Georgian LLC registered | April 2026 | Legal entity active |
| MVP hardened + smoke test passed | June 2026 | One real candidate completes full flow |
| 100 candidates | August 2026 | Candidate milestone |
| 500 candidates | October 2026 | Traction milestone |
| 10 organizational partners | December 2026 | B2B traction |
| $50K revenue (B2B + B2C combined) | December 2026 | Revenue milestone |

---

## 7. FINANCIAL PROJECTIONS

### 7.1 Revenue Streams

| Stream | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| B2B Org Subscriptions | 85,000 AZN | 340,000 AZN | 1.3M AZN |
| B2C Pro Subscriptions | 85,600 AZN | 342,400 AZN | 1.4M AZN |
| Assessment API (per-call pricing) | 31,100 AZN | 124,400 AZN | 500K AZN |
| Placement/introduction fees | 12,500 AZN | 50,000 AZN | 200K AZN |
| **TOTAL** | **214,200 AZN** | **856,800 AZN** | **3.4M AZN** |

Exchange rate: 1 USD ≈ 1.7 AZN

### 7.2 Expense Budget (9-month grant period)

```
Development:          90,000 GEL (60%)
Marketing & Content:  37,500 GEL (25%)
Operations:           22,500 GEL (15%)
TOTAL:               150,000 GEL
```

### 7.3 Use of Grant Funds (Detailed)

| Category | Amount (GEL) | Description |
|---|---|---|
| React Developer (contractor) | 30,000 | 3 months × 10,000 GEL/mo |
| Python Developer (contractor) | 30,000 | 3 months × 10,000 GEL/mo |
| AI/ML: IRT Engine + swarm tooling | 20,000 | Assessment engine, verification pipeline |
| Frontend polish + mobile | 10,000 | UI, accessibility, native build |
| LinkedIn content (3 months) | 15,000 | Content creation + scheduling |
| Conference attendance (2 events) | 15,000 | HR tech summits, recruitment industry events |
| PR & outreach | 7,500 | Press, partnerships with HR media |
| Travel (Baku ↔ Tbilisi) | 10,000 | Monthly visits for partnerships + GITA reporting |
| Legal & accounting | 7,500 | Georgian compliance, reporting |
| Admin & misc | 5,000 | Office, equipment |
| **TOTAL** | **150,000** | |

---

## 8. RISK ASSESSMENT

### 8.1 Identified Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Low candidate adoption | Medium | High | University partnerships + free tier + referral loops |
| Employers don't trust third-party scores | Medium | High | Publish transparent scoring formula, offer validation partnerships with established HR firms |
| Technical delays | Medium | Medium | AI-assisted dev, agile weekly sprints, MVP scope discipline |
| Competition from incumbent HR tech | Low-Medium | Medium | Candidate-owned credential model is structurally different — existing players are employer-gated |
| Funding gap between grant periods | Medium | High | Stack grants: GITA + KOSGEB (Turkey) + Techstars/YC applications |
| Regulatory around AI assessment | Low | Medium | Transparent scoring, right-to-appeal, human review option for Pro tier |

### 8.2 Mitigation Strategy

**Candidate adoption:**
- Partner with 3-5 universities for graduating class pilots
- Free tier for first 1,000 candidates
- Crystal economy incentivizes completion and referral

**Employer trust:**
- Publish the AURA weighting formula in public documentation
- Partner with one established recruitment agency as a "validation anchor"
- Offer comparative data: "candidates with AURA ≥75 show X% higher retention at 6 months"

**Technical:**
- Weekly sprints with measurable deliverables
- Clear milestone gates tied to real user reality, not internal completeness metrics
- Production smoke testing before any feature is declared done

**Competition:**
- Focus on candidate-owned credential angle (no incumbent does this)
- Build data moat: every completed assessment improves IRT parameters
- Stay non-enterprise early — avoid competing where HireVue/Codility are entrenched

---

## 9. ATTACHMENTS CHECKLIST

- [ ] Executive Summary
- [ ] Company Description
- [ ] Product/Service Description
- [ ] Market Analysis
- [ ] Marketing Strategy
- [ ] Operations Plan
- [ ] Financial Projections
- [ ] Project Budget Breakdown
- [ ] Timeline with Milestones
- [ ] Georgian LLC Certificate (register by April 15)
- [ ] Bank Statement (showing 10% match: ~15,000 GEL)
- [ ] Passport Copy
- [ ] Founder CV

---

## 10. TIMELINE WITH MILESTONES

```
APRIL 2026 ──────────────────────────────────────
Week 1-2:   Register Volaura Georgia LLC
Week 2-3:   Open Georgian bank account, deposit 10% match
Week 3-4:   Sign GITA grant agreement

MAY 2026 ────────────────────────────────────────
Week 1-2:   Hire contractors, begin Phase 1 development
Week 3-4:   MVP hardening: all 8 competencies live
            Apply Y Combinator (S26 batch)

JUNE 2026 ───────────────────────────────────────
Week 1-2:   Production smoke test with first real candidate (CEO walks full flow)
Week 3-4:   First 100 candidates onboarded via LinkedIn content + partnerships

JULY 2026 ───────────────────────────────────────
Week 1-2:   Organization dashboard launched
Week 3-4:   First 3 organizational partnerships signed
            Apply Techstars

AUGUST 2026 ─────────────────────────────────────
Week 1-2:   500 candidates milestone
Week 3-4:   10 organizational partners signed
            GITA interim report due

SEPTEMBER 2026 ──────────────────────────────────
Week 1-2:   B2B dashboard full feature release
Week 3-4:   API v1 for HR tech integrations
            Apply KOSGEB (Turkey)

OCTOBER 2026 ────────────────────────────────────
Week 1-2:   $50K revenue milestone
Week 3-4:   GITA final report + demo day
```

---

## 11. FOUNDER CV

**Yusif Ganbarov**
*Founder & CEO — Volaura*

**Background:**
- 33 years old, Azerbaijani entrepreneur
- Based in Baku, Azerbaijan
- Building a global-first verified talent platform

**Professional Experience:**
- Project management in civil society and digital transformation sectors
- Multi-stakeholder program coordination
- Hands-on product development and AI-assisted engineering

**Why Volaura:**
"I spent years watching talented people unable to prove what they actually know. LinkedIn says everyone is a 'Top 10% Communicator' — but nobody verifies it. Employers waste weeks on unreliable screening, and real talent stays invisible. Volaura changes that. A person takes one adaptive test, earns a score that means something, and owns the credential forever. That's the standard we're building."

**Contact:**
- Email: yusif@volaura.com
- LinkedIn: linkedin.com/in/yusifganbarov

---

## 12. CERTIFICATION

I, Yusif Ganbarov, certify that:
1. All information provided is accurate to the best of my knowledge
2. I have 10% matching funds available (~15,000 GEL)
3. The company is (or will be by the grant agreement date) registered in Georgia
4. Funds will be used as described in this application
5. I commit to all GITA reporting requirements

**Signature:** _________________
**Date:** _________________
**Name:** Yusif Ganbarov

---

*Document prepared April 2026. Positioning: verified talent platform. Not a volunteer platform.*
