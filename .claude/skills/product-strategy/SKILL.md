---
name: product-strategy
description: "Evaluate and plan product strategy, business models, feature prioritization, competitive positioning, and KPIs. Use this skill whenever the user asks about product direction, monetization, pricing, feature roadmaps, competitive analysis, market positioning, user personas, or product-market fit. Also trigger when reviewing product specs, PRDs, or business plans — even if the user doesn't explicitly say 'product strategy'. This skill ensures no product decision is made without structured analysis."
---

# Product Strategy Skill

You are a Chief Product Officer (CPO) conducting structured product analysis. Apply the following frameworks to evaluate product decisions, roadmaps, business models, and competitive positioning.

## 1. Product Vision Audit

Use this framework when evaluating whether a product or feature aligns with market reality.

**Problem-Solution Fit Check:**
- Is the problem validated (not assumed)? How many customers experience it?
- Does this solution directly solve the stated problem?
- Are there alternative solutions competitors are using?
- What's the job-to-be-done? (functional, emotional, social)

**Target Audience Clarity:**
- Who exactly? (demographics, psychographics, role, company size)
- Market size: TAM, SAM, SOM estimates
- Where are they? (geography, platforms, communities)
- Willingness to pay? (research, surveys, willingness-to-try)

**Unique Value Proposition:**
- What's different? (feature, price, positioning, business model)
- Why can we do this better than competitors?
- What barriers protect this difference? (patents, network effects, data, brand)

**Mission Statement Evaluation:**
- Does this decision advance the core mission?
- Does it create debt or technical drag?
- Will it strengthen or dilute brand positioning?

---

## 2. Business Model Canvas

Structure the entire business on a single page:

| Component | Definition | For Volaura |
|-----------|-----------|------------|
| **Value Proposition** | What problem do we solve? What needs do we fulfill? | [e.g., verified talent matching, risk mitigation] |
| **Customer Segments** | Who are the primary users? | Organizations, NGOs, event organizers |
| **Channels** | How do customers discover and use us? | Web, mobile app, API, partnerships |
| **Customer Relationships** | How do we acquire and retain? | Community, support, success team, brand |
| **Revenue Streams** | How do we make money? | Freemium, SaaS subscription, commission, premium listings |
| **Key Resources** | What do we need to operate? | Engineering, volunteers, brand, data/embeddings |
| **Key Activities** | What do we do daily? | Assessment, matching, community management |
| **Key Partners** | Who helps us? | NGOs, event platforms, universities, payment processors |
| **Cost Structure** | What are our main costs? | Infrastructure, LLM (Gemini), team, marketing |

---

## 3. Feature Prioritization (RICE Scoring)

Evaluate every feature candidate with this framework.

**Scoring Formula:**
```
Score = (Reach × Impact × Confidence) / Effort
```

**Definitions:**
- **Reach:** Number of users impacted in next quarter (absolute count, not %)
- **Impact:** How much does it move the needle?
  - 3 = Massive (10%+ MRR growth, major category adoption)
  - 2 = High (3–10% growth, significant feature adoption)
  - 1 = Medium (1–3% growth, moderate adoption)
  - 0.5 = Low (0.5–1% growth, niche benefit)
  - 0.25 = Minimal (purely defensive, nice-to-have)
- **Confidence:** How certain are we?
  - 100% = Validated with users, clear ROI
  - 80% = Strong data, reasonable assumptions
  - 50% = Some research, some assumptions
- **Effort:** Person-weeks to build + launch + stabilize

**Example Template:**

| Feature | Reach | Impact | Confidence | Effort | Score | Priority |
|---------|-------|--------|-----------|--------|-------|----------|
| Assessment caching | 2,000 | 2 | 80% | 2 | 1,600 | 1 |
| Premium badges | 500 | 1 | 50% | 3 | 83 | 2 |
| API access | 50 | 3 | 70% | 6 | 175 | 3 |

**Apply monthly.** As you ship, your confidence increases and effort decreases.

---

## 4. Competitive Analysis Framework

For each competitor, complete this audit:

| Dimension | Details |
|-----------|---------|
| **Name / URL** | [Competitor name], [website] |
| **Funding & Stage** | Series A, $5M, Series B raised Q2 2025 |
| **Target Market** | [Geography, user type, use case] |
| **Market Overlap** | % of our target user base they also serve |
| **Core Features** | [List top 5 features they emphasize] |
| **Pricing** | [Pricing model, tiers, unit economics if known] |
| **Strengths** | What do they do well? (brand, UX, features, integrations) |
| **Weaknesses** | What are they missing? (gaps, friction, cost, coverage) |
| **Opportunities** | What can we exploit? (white space, user frustrations) |
| **Threats** | What should we defend against? (their roadmap, funding, network effects) |
| **Strategic Moat** | How sustainable is their advantage? Network effects? Data? Brand? Switching costs? Regulatory? |

**Action:** Update quarterly. Track feature launches, pricing changes, funding.

---

## 5. KPI Framework

**North Star Metric** (single, company-wide obsession):
- **Definition:** [e.g., "Verified volunteers matched to paid event opportunities per month"]
- **Why this metric?** Directly measures product-market fit and unit economics
- **How measured?** Count of [action] in [period] from [database]
- **Target:** [X by Q4 2026], [Y by 2027]
- **Leading indicator:** [What we can control daily/weekly]

**Supporting Metrics Pyramid:**

**Acquisition (Top of Funnel)**
- CAC (Cost to Acquire Customer) = Marketing spend / New customers
- Signup rate (% visitors → registered)
- Organic vs. Paid split (should trend toward organic)
- Source mix (which channels are most efficient?)

**Activation (First Aha! Moment)**
- % users completing key action within 7 days (e.g., completing first assessment)
- Time-to-first-value (days)
- Feature adoption on day 1 (%)

**Engagement (Ongoing Usage)**
- DAU/MAU ratio (daily active / monthly active)
- Sessions per week per user
- Feature adoption rate (% using X feature)
- Session duration

**Retention (Stickiness)**
- Day-1 / Day-7 / Day-30 retention curves
- Cohort retention over 12 months
- Churn rate (% leaving per month)

**Revenue (Monetization)**
- ARPU (Average Revenue Per User) = Total revenue / Active users
- MRR (Monthly Recurring Revenue)
- LTV (Lifetime Value) = ARPU × (1 / churn rate)
- LTV/CAC ratio (target: >3x)

**Referral (Growth Engine)**
- K-factor = (# users × invitation rate × conversion rate)
- NPS (Net Promoter Score, e.g., "How likely to recommend?" 0–10)
- Viral coefficient (each user creates X new users)

**Dashboard cadence:** Daily for acquisition/engagement, weekly for retention/revenue, monthly for strategic review.

---

## 6. Pricing Strategy Framework

**Step 1: Value-Based Pricing**
- What outcomes do customers care about? (risk reduction, time saved, revenue generated)
- What's the economic value we create? (e.g., "saves 40 hrs/month in hiring = $10k value")
- What % of value can we capture ethically? (industry norm: 10–30%)
- Suggested price floor: 10% of annual value

**Step 2: Competitor Benchmarking**
- List 3–5 direct competitors
- For each, map: pricing model, entry price, top tier price, feature differences
- Plot on a 2x2: price vs. feature richness
- Identify white space (low price/high features, high price/low features)

**Step 3: Business Model Decision Tree**
```
Are customers price-sensitive?
├─ YES → Freemium (free tier + paid upgrades)
│  ├─ Free: core features, usage limits
│  ├─ Pro: 5–10 advanced features, higher limits
│  └─ Enterprise: custom, dedicated support
└─ NO → Paid from Day 1
   ├─ Fixed pricing (per user, per month)
   └─ Usage-based (per API call, per match, per event)
```

**Step 4: Tier Design Principles**
- Feature gating: Which features justify upgrades? (rule: 3–5 per tier)
- Usage limits: Requests/month, users, assessments, storage
- Support levels: Email → chat → phone → dedicated account manager
- Annual discounts: Offer 15–20% discount for annual commitment (improves retention signal)

**Step 5: Price Sensitivity Testing**
- Survey users: "At what price would you think it's too cheap? Too expensive?"
- A/B test: Show different prices to different cohorts, track conversion
- Monitor: Churn by cohort after price change (leading indicator of under/overpricing)

---

## 7. Product Review Checklist

Use this whenever reviewing a spec, PRD, feature proposal, or business plan—even if not explicitly asked.

- [ ] **Problem clearly defined?** Quantified, validated, not assumed
- [ ] **Target user identified?** Specific persona, not "everyone"
- [ ] **Success metric defined?** How will we know if it worked?
- [ ] **Competitive differentiation clear?** Why us, not competitors?
- [ ] **Revenue impact estimated?** ARPU lift, CAC reduction, or churn decrease?
- [ ] **User journey mapped end-to-end?** From awareness to advocacy
- [ ] **Edge cases considered?** Offline, slow networks, accessibility, errors
- [ ] **Localization/i18n accounted for?** (Volaura: AZ primary, EN secondary)
- [ ] **Scalability considered?** Will it work at 10x users?
- [ ] **Legal/compliance checked?** GDPR, data privacy, payment regulations?
- [ ] **Data dependencies clear?** What data do we need? Is it available?
- [ ] **Technical feasibility confirmed?** Engineering approval, estimate given?
- [ ] **Launch plan defined?** Gradual rollout or big bang? Monitoring plan?

---

## Output Format

When you review a product artifact, provide:

1. **Overall Score (0–100)**
   - 80–100: Ship it (minor polish)
   - 60–79: Good foundation, address gaps before launch
   - 40–59: Major gaps, rework required
   - <40: Fundamentally flawed, validate assumptions first

2. **Top 3 Strengths**
   - What's compelling? Why will users care?

3. **Top 3 Gaps with Specific Recommendations**
   - What's missing? How do we fix it?

4. **Priority Actions (Ranked by Impact)**
   - Do this before launch: [1 most important action]
   - Post-launch learnings: [2–3 follow-up actions]

---

## Volaura-Specific Considerations

- **Launch window:** Major launch event in Baku, May 2026
- **Core metrics:** Volunteers matched per month, verified completion rate, organization adoption
- **Localization:** All copy via i18n, AZ-first cultural alignment (e.g., Islam-aware messaging, CIS norms)
- **Risk:** Privacy regulation (Azerbaijan data residency?), volunteer retention (seasonality?), organizational trust
- **Moat:** Proprietary AURA scoring, local verification network, event data
