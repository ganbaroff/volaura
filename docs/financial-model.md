# Volaura Financial Model — v1.0 (Skeleton)

**Cross-references:** [[MASTER-STRATEGY]] | [[MONETIZATION-ROADMAP]] | [[research/blind-spots-analysis]] | [[research/geo-pricing-research]] | [[GITA-GRANT-APPLICATION-2026]]

> Built by Claude (CTO) for Yusif's review.
> Rule from Investor advisor: "You must OWN every number and defend it in 90 seconds without slides."
> Yusif: review each assumption. Change what doesn't match your market knowledge.

---

## Revenue Streams

### Stream 1: B2C Volunteer Platform (Freemium)
| Tier | Price (AZN/mo) | What they get |
|------|---------------|---------------|
| Free | 0 | 1 assessment, basic profile, job board access |
| Pro | 49 | Unlimited assessments, detailed AURA report, priority in org search |
| Premium | 149 | All Pro + verified badge PDF, LinkedIn-shareable card, mentor matching |

**Assumptions (Yusif to validate):**
- Year 1 registered volunteers: 2,000 (from COP29/WUF/CIS network + university partnerships)
- Free-to-Pro conversion: 5% (industry benchmark: 3-8% for freemium SaaS)
- Pro-to-Premium conversion: 15% of Pro users
- Monthly churn (Pro): 8%

**Year 1 Monthly Recurring Revenue:**
- 2,000 × 5% = 100 Pro users × 49 AZN = 4,900 AZN/mo
- 100 × 15% = 15 Premium users × 149 AZN = 2,235 AZN/mo
- **Total MRR: ~7,135 AZN/mo (~$4,200)**
- **Annual: ~85,600 AZN (~$50,400)**

### Stream 2: B2B Organization Subscriptions
| Tier | Price (AZN/mo) | What they get |
|------|---------------|---------------|
| Starter | 199 | Search 50 volunteers/mo, basic filters |
| Business | 499 | Unlimited search, advanced filters, bulk assessment |
| Enterprise | 849 | All Business + custom question banks, API access, white-label |

**Assumptions:**
- Year 1 organizations: 20 (from Yusif's network: event companies, NGOs, government)
- Tier distribution: 60% Starter, 30% Business, 10% Enterprise
- Monthly churn: 5%

**Year 1 Org MRR:**
- 12 × 199 + 6 × 499 + 2 × 849 = 2,388 + 2,994 + 1,698 = **7,080 AZN/mo**
- **Annual: ~85,000 AZN (~$50,000)**

### Stream 3: B2B Per-Assessment (HR Testing)
| Product | Price per test | Volume target Y1 |
|---------|---------------|-------------------|
| HR Competency Test | 15-25 AZN | 500 tests |
| Kids Proforientation | 10-15 AZN | 300 tests |
| Company-Verified Badge | 5 AZN/badge + 1,500 AZN setup | 10 companies × 50 badges |

**Year 1 Assessment Revenue:**
- HR: 500 × 20 AZN avg = 10,000 AZN
- Kids: 300 × 12 AZN avg = 3,600 AZN
- Badges: 10 × 1,500 setup + 500 × 5 = 15,000 + 2,500 = 17,500 AZN
- **Total: ~31,100 AZN (~$18,300)**

### Stream 4: Placement Fees (Per Successful Hire)
| Type | Fee | Volume Y1 |
|------|-----|-----------|
| Standard placement | 250 AZN | 30 |
| Premium placement (Gold+ AURA) | 500 AZN | 10 |

**Year 1: 30 × 250 + 10 × 500 = 12,500 AZN (~$7,350)**

---

## Total Revenue Projection

| Stream | Year 1 (AZN) | Year 1 (USD) |
|--------|-------------|-------------|
| B2C Subscriptions | 85,600 | $50,400 |
| B2B Org Subscriptions | 85,000 | $50,000 |
| Per-Assessment (HR/Kids/Badges) | 31,100 | $18,300 |
| Placement Fees | 12,500 | $7,350 |
| **Total** | **214,200** | **$126,050** |

---

## Costs

| Item | Monthly (AZN) | Annual (AZN) | Notes |
|------|-------------|-------------|-------|
| Railway (backend) | 14 | 168 | ~$8/mo current |
| Vercel (frontend) | 0 | 0 | Free tier |
| Supabase (DB) | 0-42 | 0-510 | Free → Pro if >500MB |
| Gemini API | 0-17 | 0-200 | Free tier 15 RPM |
| OpenAI fallback | 8-17 | 100-200 | $5-10/mo buffer |
| Domain + email | 5 | 60 | volaura.az |
| Claude API (MiroFish) | 17-85 | 200-1,000 | For agent evaluations |
| **Total infra** | **~60-180** | **~730-2,140** | |
| | | | |
| Yusif (founder salary) | 0 (Y1) | 0 | Reinvest all revenue |
| Marketing | 170 | 2,000 | Minimal — organic + network |
| Legal (registration) | - | 500 | One-time MSMEDA |
| **Total costs Y1** | | **~3,230-4,640** | |

---

## Unit Economics

| Metric | Value | Benchmark |
|--------|-------|-----------|
| **CAC (volunteers)** | ~0 AZN | Network effect + university partnerships |
| **CAC (organizations)** | ~50-100 AZN | Direct outreach from existing network |
| **LTV (Pro volunteer)** | 49 × 8 months avg = 392 AZN | 8mo = 8% monthly churn |
| **LTV (Business org)** | 499 × 14 months = 6,986 AZN | 5% churn = ~14mo avg |
| **LTV:CAC ratio (orgs)** | ~70-140x | Healthy threshold: >3x |
| **Gross margin** | ~97% | SaaS with near-zero COGS |
| **Payback period** | <1 month | No acquisition cost for network sales |

---

## Breakeven Analysis

Monthly fixed costs: ~150 AZN
Breakeven: **4 Pro subscribers** OR **1 Starter org**

**Already profitable from month 1 if Yusif converts 4 people from his existing network.**

---

## Grant Pipeline (additional, non-dilutive)

| Grant | Amount | Status |
|-------|--------|--------|
| Georgia GITA Innovation | $240,000 | Research stage |
| Turkey TUBITAK/KOSGEB | $50,000 | Research stage |
| Kazakhstan Astana Hub | $20,000 | Research stage |
| **Total pipeline** | **$310,000** | |

---

## Key Assumptions to Validate (Yusif's homework)

1. [ ] **2,000 volunteers Year 1** — is this realistic from your network alone?
2. [ ] **20 organizations** — can you name 20 right now?
3. [ ] **5% free-to-paid** — would YOU pay 49 AZN/mo for this?
4. [ ] **Boss.az median salary 185 USD** — confirm this is still accurate
5. [ ] **250 AZN placement fee** — would orgs pay this vs posting on Boss.az for free?
6. [ ] **8% monthly churn** — too optimistic? Too pessimistic?

---

## 90-Second Pitch Version

"Volaura is a verified competency platform for volunteers. Organizations pay to find pre-tested talent. Volunteers get free assessments and earn verified badges.

Year 1 projection: 214,000 AZN revenue from 4 streams. Costs under 5,000 AZN. 97% gross margin. Already breakeven at 4 subscribers.

Why us: 10 years managing COP29, WUF13, CIS Games. 200+ volunteer network. AI-powered adaptive testing that no competitor in Azerbaijan has.

Ask: [grant amount / partnership / investment amount]."
