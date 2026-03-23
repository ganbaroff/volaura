# Volaura KPIs & Metrics Framework

## North Star Metric

### Monthly Active Assessed Volunteers (MAAV)
**Definition:** Unique users who have a valid, non-expired AURA score and have logged in at least once within the trailing 30 days.

**Why This Metric:**
- Combines activation (assessment complete) + engagement (active return)
- Free tier MAAV shows organic traction; Pro tier MAAV shows monetization potential
- Leads lagging metrics (revenue, retention) by 4–8 weeks
- Single number to optimize across all product decisions

**Target Milestones:**
- Launch (May 2026): 200 MAAV
- M3: 600 MAAV
- M6: 2,000 MAAV (post-launch event growth)
- M12: 5,000+ MAAV

**Tracking:**
- Daily dashboard (Mixpanel/Plausible)
- Breakdown by: Free tier, Pro tier, badge level
- Cohort analysis: MAAV retention by signup month (distinguish event cohort from organic)

---

## Activation Metrics

### Time to First AURA Score
**Definition:** Median time from account creation to assessment submission + score calculation.

**Target:** <15 minutes (allows interruption tolerance).

**Why Matters:**
- Predicts likelihood to upgrade to Pro (fast completion = high intent)
- Identifies UX friction (CAT/IRT algorithm latency, form abandonment)
- Correlates with D1/D7 retention

**Calculation:**
```
Time to First Score = (timestamp: score_generated) - (timestamp: account_created)
```

**Tracking:**
- Mixpanel: event funnel "sign_up" → "assessment_started" → "assessment_submitted" → "score_generated"
- Session recording (Hotjar/LogRocket) for bottleneck videos
- A/B test: "Submit" vs "Get Score" button copy

**Red Flags:**
- >20 min: UX friction (redesign assessment UI)
- >30 min: Algorithm latency (optimize LLM/IRT calls)

---

### Assessment Completion Rate
**Definition:** % of signed-up users who successfully submit an assessment and receive AURA score.

**Target:** >75%

**Why Matters:**
- Directly drives MAAV (incomplete assessments don't count)
- High drop-off indicates question difficulty, motivation, or technical issues
- Lower completion = lower network effect (fewer profiles to discover)

**Calculation:**
```
Completion Rate = (assessments_submitted with score) / (accounts_created) × 100%
```

**Tracking:**
- Amplitude funnel: "signup" → "q1_started" → "q1_submitted" → ... → "score_generated"
- Cohort survival: % completing by day 1, 3, 7, 30
- Drop-off analysis: Which question has highest abandonment?

**Diagnostic Questions:**
- Is drop-off at CAT algorithm start? (Redesign intro copy)
- At open-ended questions? (Pre-fill examples, reduce effort)
- At payment (for Pro trial)? (Reduce friction in upgrade flow)

**Red Flags:**
- <50%: Significant UX issue or misaligned targeting
- Sudden drop in cohort: A/B test regression or algorithm change

---

### Profile Completion Rate
**Definition:** % of assessed users who fill out >50% of optional profile fields (bio, skills, location, photo, social links).

**Target:** >60%

**Why Matters:**
- Detailed profiles increase discoverability (org search, leaderboard appeal)
- Photo + bio = higher trust signal (credibility for org attestation)
- Correlates with Pro conversion (invested users = willing to pay)

**Calculation:**
```
Profile Completion Rate = (users with >3 of 6 fields filled) / (users with score) × 100%
```

**Fields Tracked:**
1. Profile photo
2. Bio (50+ chars)
3. Location/city
4. Skills tags (3+)
5. Social links (LinkedIn, portfolio, etc.)
6. Volunteer history/testimonials

**Tracking:**
- Mixpanel: "profile_field_updated" events
- Cohort analysis: % completion by signup month + tenure
- Correlation: profile completion → org searches → event registrations

**Optimization Loop:**
- Week 1 post-signup: Send in-app prompt to "Complete Your Profile" (+bio modal)
- Week 3: Email: "Make your profile stand out" (gamified: "70% profile strength")
- In-app: Show peer profiles with high completion (social proof)

---

## Engagement Metrics

### Weekly Profile Views (Own + From Orgs)
**Definition:** Total number of times a user's profile is viewed in a week, split by:
- **Own views:** User viewing their own profile (self-engagement)
- **Org views:** Organization account viewing volunteer profile (key signal)
- **Other views:** Other volunteer profiles (peer browsing)

**Target:**
- Median: >1 view/week (from orgs)
- Top 10% volunteers: >5 views/week (high org interest)

**Why Matters:**
- Org views = demand signal (validation that volunteers are discoverable)
- Correlates with event registration + attestation (orgs find you → recruit you)
- Prerequisite for AURA API monetization (orgs want searchable talent pool)

**Calculation:**
```
Weekly Profile Views = COUNT(profile_view_event) WHERE timestamp IN [week]
Org Views Rate = (profile_views FROM org_account) / (total_profile_views) × 100%
```

**Tracking:**
- Event: "profile_viewed" with context (viewer_type: "self" | "org" | "volunteer")
- Dashboard: Median views/volunteer, percentile distribution
- Cohort: Views by AURA badge level (Gold volunteers get more views?)

**Red Flags:**
- <0.3 org views/week: Org users aren't discovering volunteers (poor search or org adoption)
- All views = "self": Volunteer narcissism; low org interest = low attestation/recruitment

---

### Share Actions Per User Per Month
**Definition:** Total number of times a user shares their AURA card, profile, or assessment result.

**Target:** >2 shares/user/month (activated users).

**Why Matters:**
- Viral coefficient proxy (shares → invites → new signups)
- Low shares = weak social proof narrative (cards aren't compelling)
- Shares on LinkedIn/WhatsApp drive external traffic (SEO + brand awareness)

**Calculation:**
```
Share Actions = COUNT(share_event) WHERE event_type IN ["share_card", "share_profile", "share_certificate"]
Shares Per User Per Month = SUM(share_actions) / COUNT(active_users) / 12 × 30
```

**Share Types Tracked:**
1. "Share AURA Card" (social media, WhatsApp, Telegram, copy link)
2. "Share Profile" (org recruitment link)
3. "Share Certificate" (PDF download + social)
4. "Generate LinkedIn Carousel" (Pro feature)

**Tracking:**
- Event: "share_initiated" with platform (instagram, whatsapp, linkedin, twitter, link_copy)
- Referral link tracking: UTM parameter "share_source=aura_card"
- Post-share funnel: shares → link clicks → new signups

**Optimization:**
- A/B test share card designs (colors, badge prominence, peer count)
- Monthly email: "You've earned 500 shares this month! (Top 1%)" (gamification)
- In-app prompt at key moments: Post-score, post-event-registration, post-leaderboard-achievement

---

### Events Registered Per Active User
**Definition:** Average number of event registrations per MAAV user, per month.

**Target:** >1 event/user/month (demonstrates event marketplace value).

**Why Matters:**
- Drives org engagement (more registrations = more useful org product)
- Signals volunteer satisfaction (willing to commit time)
- Potential future revenue (event ticketing, org commission)

**Calculation:**
```
Events Per User = COUNT(event_registrations) / COUNT(MAAV_users)
```

**Tracking:**
- Event: "event_registered" (linked to event_id, user_id, AURA score, badge level)
- Cohort: Events registered per user by signup cohort + tenure
- Org analysis: Events registered per org (top 20% orgs by registrations)

**Red Flags:**
- <0.5: Users aren't discovering/registering for events (poor event discovery UX or org pipeline)
- Event completion rate <50%: Users register but don't attend (trust issue or overcommitment)

---

### Leaderboard Engagement (Views & Reactions)
**Definition:** Monthly views of leaderboard page + interactions (reactions, profile clicks from leaderboard).

**Target:**
- 40% of MAAV view leaderboard weekly
- >2,000 reactions/month (emoji votes, congratulations)

**Why Matters:**
- Drives reassessment (volunteers want to improve rank)
- Competitive engagement = higher retention
- Social proof (badges + rankings visible to all)

**Calculation:**
```
Leaderboard Views = COUNT(page_view WHERE page = "/leaderboard")
Reactions = COUNT(reaction_event WHERE context = "leaderboard")
Engagement Rate = (Leaderboard Views + Reactions) / MAAV / 30 days
```

**Tracking:**
- Page analytics: /leaderboard views, bounce rate, session duration
- Event: "leaderboard_reaction" (emoji type, target_volunteer, reactor_id)
- Cohort: % active leaderboard users by badge level (are Gold volunteers more competitive?)

**Optimization:**
- Scoped leaderboards (by event, by region, by competency)
- Weekly email digest: "You ranked 5th in your region! Reassess to move up."
- Trophy icons + confetti animations (ego/competitive drives)

---

### Reassessment Rate
**Definition:** % of users with a previous AURA score who complete a new assessment within the reassessment window.

**Target:** >30% within 90 days (for Free tier), >50% within 30 days (for Pro tier).

**Why Matters:**
- Indicates growth trajectory belief (volunteers see value in re-evaluating)
- Pro conversion key driver (faster reassessment = premium feature proof)
- Extends LTV (reassessed volunteers stay longer)
- Data freshness (older scores become stale for org matching)

**Calculation:**
```
Reassessment Rate (90d) = (users who reassessed within 90 days) / (users eligible for reassessment) × 100%
Reassessment Rate (Pro, 30d) = (Pro users who reassessed within 30 days) / (Pro users eligible) × 100%
```

**Eligibility Window:**
- Free tier: 90 days after previous score
- Pro tier: 30 days after previous score

**Tracking:**
- Cohort analysis: % of users from month N who reassess by month N+3
- Email campaign tracking: "Time to reassess!" email → click → assessment_submitted
- A/B test: Reassessment reminders (frequency, copy)

**Red Flags:**
- <15%: Users don't see value in reassessment (LLM bias? Competency growth stalled?)
- Pro <40%: Pro tier isn't delivering promised feedback loop (improve analytics/visualization)

---

## Retention Metrics

### D1/D7/D30 Retention Rates
**Definition:** % of users from a cohort who return and log in on day 1, day 7, and day 30 after signup.

**Targets:**
- D1 retention: >50%
- D7 retention: >35%
- D30 retention: >20% (Free tier), >40% (Pro tier)

**Why Matters:**
- Early signals of product-market fit (D1 = immediate value delivery)
- Pro vs Free split shows monetization viability
- Informs marketing CAC sustainability (need >20% D30 to justify acquisition spend)

**Calculation:**
```
D1 Retention = (users who logged in on day 1) / (total signups in cohort) × 100%
D7 Retention = (users who logged in between days 2-7) / (total signups) × 100%
D30 Retention = (users who logged in between days 8-30) / (total signups) × 100%
```

**Tracking:**
- Amplitude cohort analysis: Grouped by signup date, split by Free/Pro
- Compare: retention by signup source (launch event vs organic vs referral)
- Bottleneck: Which day has largest drop-off? (Week 1, Week 2, Day 30 cliff?)

**Improvement Levers:**
- D1: Faster AURA score delivery, celebrate score via email
- D7: Leaderboard ranking email, org discovery email, event recs
- D30: Reassessment prompt, Pro upsell (radar chart + analytics)

---

### Monthly Active Rate
**Definition:** % of users assessed (all-time) who have logged in at least once in the last 30 days.

**Target:** >40% at D30 (calendar month retention).

**Why Matters:**
- Stabilized version of D30 retention (accounts for non-linear return patterns)
- Monthly budget planning (MRR predictability)
- Plateau point for churn optimization

**Calculation:**
```
Monthly Active Rate = (unique_users logged in last 30 days) / (cumulative_assessed_users) × 100%
```

**Tracking:**
- Monthly dashboard: Graph of monthly active rate over time
- Cohort retention curve: Vintage cohorts (month 1, month 6, month 12 signups)

---

### Churn Reasons Tracking
**Definition:** Structured feedback from users who disable/delete accounts or stop logging in >60 days.

**Target:** Understand top 3 reasons; prioritize fixes.

**Why Matters:**
- Qualitative insight (quantitative metrics don't explain "why")
- Early warning signals (e.g., "assessment was too hard" → bias issue)
- Pro tier churn often preventable (e.g., reassessment reminders)

**Collection Methods:**
1. **Offboarding email** (to churned users): "Why did you leave?" survey (SMS + email)
2. **In-app churn prediction**: Users with <1 login/month + declining engagement → "Keep your profile fresh" prompt
3. **Monthly user interviews**: Talk to 5 churned users, 5 active Pro users
4. **Exit survey** (optional, at delete account time)

**Tracking:**
- Qualtrics/Typeform: Churn feedback; categorize and prioritize
- Cohort: Churn reasons by Pro vs Free, by tenure, by badge level
- Root cause analysis: "Assessment too hard" → LLM calibration issue? Question phrasing?

**Common Reasons to Monitor:**
- "Assessment felt irrelevant to my volunteering"
- "No events in my area"
- "Limited time to volunteer"
- "Orgs aren't reaching out"
- "Pro tier features not worth $5/month"

---

## Viral & Growth Metrics

### Viral Coefficient (K-Factor)
**Definition:** Average number of new users invited/acquired per activated user.

**Formula:**
```
K = (shares per user) × (conversion rate from share to signup)
```

**Target:** >1.2 (each user generates >1.2 new users)

**Why Matters:**
- Exponential growth path (K>1 = compounding; K<1 = linear/declining)
- Indicates product virality without paid acquisition (sustainable)
- Platform defensibility (network effects)

**Example Calculation:**
- Avg shares/user/month: 2.5
- Share-to-signup conversion: 8% (clicks share link → 8% complete signup)
- K = 2.5 × 0.08 = 0.2 monthly

**To Achieve K=1.2:**
- Need 2.5 shares × 48% conversion, OR
- 3.0 shares × 40% conversion, OR
- 4.0 shares × 30% conversion

**Tracking:**
- UTM link tracking: "share_source=user_aura_card"
- Event: "share_created" → "link_clicked" → "signup_from_referral"
- Monthly calculation: Aggregate across all shares

**Optimization Levers:**
- A/B test share card design (higher % of receivers sign up?)
- Referral incentive: "Invite 3 friends, both get 30-day Pro free"
- Viral moments: First score, badge earned, leaderboard achievement

---

### Referral Conversion Rate
**Definition:** % of people who click a referral link and complete signup, broken by source.

**Target:** >10% (all sources), >15% (referral from friend).

**Why Matters:**
- Identifies highest-quality acquisition channels
- Friend referral usually = higher LTV (trusted source)
- Directs marketing budget toward viral mechanics

**Calculation:**
```
Referral Conversion = (signups from referral link) / (referral link clicks) × 100%
```

**Tracking by Source:**
- User share (AURA card): Target >12%
- Leaderboard (viewed volunteer profile): Target >8%
- Event (registered attendee shared): Target >15%
- Org attestation (org created badge + shared): Target >20%

**Red Flags:**
- <5%: Landing page or signup flow friction (redesign)
- Huge variance by source: Some sources are low-intent (adjust messaging)

---

### Share-to-Signup Rate
**Definition:** Subset of referral conversion; specifically social media shares.

**Target:** >5% (WhatsApp, LinkedIn, Instagram shares result in signups).

**Why Matters:**
- Validates AURA card emotional appeal (users willing to share publicly)
- Indicates network growth sustainability (less dependent on email)
- Platform moat (social proof > paid ads)

**Calculation:**
```
Share-to-Signup Rate = (signups from social share links) / (social shares) × 100%
```

**Tracking:**
- Event: "share_to_platform" (whatsapp, linkedin, instagram, telegram, twitter)
- UTM parameter: utm_source=social_share, utm_medium=[platform]
- Cohort: Share-to-signup by badge level (Gold volunteers' shares convert better?)

---

### Organic Search Impressions (Public Profiles)
**Definition:** Monthly Google Search impressions for volunteer profile URLs (Google Search Console).

**Target:** >5,000 impressions/month by M6 (each volunteer profile is SEO asset).

**Why Matters:**
- Free, compounding acquisition (SEO multiplier)
- Validates that public profiles are discoverable and indexed
- Reduces paid CAC dependency

**Calculation:**
```
Organic Impressions = (Google Search Console: Impressions for domain/profiles)
```

**Tracking:**
- Google Search Console: Filter for "/profiles/*" URLs
- Monthly report: Impressions, clicks, avg position (CTR)
- Top profiles: Which volunteers rank for what searches?

**SEO Optimization:**
- Profile schema markup (JSON-LD: Person, skills, badges)
- Canonical URLs (avoid duplicate profiles)
- Backlinks: Org leaderboards, event pages link to volunteer profiles
- Regional SEO: Profiles rank for "[City] + [Competency] + volunteer"

---

## Revenue Metrics

### Monthly Recurring Revenue (MRR)
**Definition:** Total predictable monthly revenue from all recurring subscriptions (Pro tier + Growth/Enterprise orgs).

**Calculation:**
```
MRR = (Pro subscribers × $4.99/mo) + (Growth orgs × $29/mo) + (Enterprise orgs × $99/mo)
```

**Target Milestones:**
- Launch (M1): $800 (160 Pro users @ 50% annual paid monthly-equivalent)
- M6: $4,000–10,000 (post-launch event growth)
- M12: $8,000–28,000 (conservative to optimistic)

**Tracking:**
- Stripe dashboard: Real-time MRR calculation
- Cohort: MRR by signup month (shows retention curves)
- Churn analysis: Which cohorts retain best?

**Key Metrics Derived from MRR:**
- Month-over-Month (MoM) Growth Rate: (MRR_thisMonth - MRR_lastMonth) / MRR_lastMonth
- Annual Run Rate (ARR): MRR × 12
- CAC Payback Period: CAC ÷ (ARPU monthly)

---

### Pro Conversion Rate
**Definition:** % of Free tier users (assessed) who upgrade to Pro tier within 180 days.

**Target:** >5% at scale, >10% immediately post-launch event.

**Why Matters:**
- Direct revenue impact (each Pro = $40/year LTV)
- Product value signal (if <2%, features don't resonate)
- Determines unit economics sustainability

**Calculation:**
```
Pro Conversion Rate = (Pro subscribers) / (assessed Free users) × 100%
```

**Tracking:**
- Cohort analysis: % converting by signup month (launch event cohort vs organic)
- Funnel: Assessment complete → Sees Pro upsell → Clicks upsell → Completes payment
- Dropoff: Which step loses most users?

**Conversion Optimization:**
- **Trigger 1:** Immediately after score (confetti + "Unlock pro features" modal)
- **Trigger 2:** Week 1 email: Radar chart screenshot (social proof: "See how you compare to peers")
- **Trigger 3:** At reassessment eligible date: "Upgrade to reassess in 30 days vs 90"
- **Trigger 4:** Leaderboard: Show Pro-only features (percentile rank, trend chart)

**A/B Tests to Run:**
- Price point: $4.99/mo vs $3.99/mo (elasticity)
- Annual discount: 33% off vs 40% off vs no discount
- Trial: 7-day free vs 14-day vs paid tier only
- Copy: Value prop (radar + analytics) vs urgency (limited-time offer)

---

### Org Paid Conversion Rate
**Definition:** % of Starter (Free) org accounts that upgrade to Growth tier within 90 days.

**Target:** >10% at scale.

**Why Matters:**
- Org segment unit economics (LTV = $522 at 1.5-year retention)
- Product-market fit signal (orgs value unlimited search + API + analytics)
- Determines org expansion roadmap ROI

**Calculation:**
```
Org Paid Conversion Rate = (Growth + Enterprise org subscriptions) / (Starter org accounts) × 100%
```

**Tracking:**
- Cohort analysis: Starter → Growth conversion by org signup month
- Org characteristics: Size, industry, initial event count (do bigger orgs convert faster?)
- Time to first paid event: How many events do orgs list before upgrading?

**Conversion Optimization:**
- **Trigger 1:** After 5 volunteer applications: "Upgrade to unlock full volunteer search + API"
- **Trigger 2:** Week 2 email: "X orgs are using Growth tier. See how you compare."
- **Trigger 3:** At 90-day mark: Offer 3-month free Growth trial (lock-in)
- **White-glove:** Sales call (demo API, show ROI on bulk matching)

---

### Average Revenue Per User (ARPU)
**Definition:** Total revenue ÷ total active users (blended across Free, Pro, Starter, Growth, Enterprise).

**Target:**
- Volunteer segment: $0.30/user/month (5% × $40/year ÷ 12 = $0.17 + network effects)
- Org segment: $5/org/month (higher CAC, higher LTV)

**Calculation:**
```
Blended ARPU = (Total MRR) / (MAAV + Active Orgs)
```

**Importance:**
- KPI dashboard to track blended SaaS health
- Informs CAC payback sustainability
- Guides pricing strategy (raise prices if ARPU < target)

---

## Quality & Integrity Metrics

### Average AURA Score Distribution
**Definition:** Histogram of all AURA scores; track mean, median, std deviation, percentiles.

**Target:** Bell curve centered around 55–65 (Gaussian distribution, no ceiling/floor effects).

**Why Matters:**
- Validates IRT calibration (if skewed, questions too hard/easy)
- Identifies assessment bias (e.g., all women score low → gender bias in LLM)
- Badge distribution impacts perceived credibility (too many Platinum = inflation)

**Calculation:**
```
Mean AURA = AVG(all_aura_scores)
Median AURA = 50th percentile of scores
Std Dev = STDEV(all_aura_scores)
Target: Mean ~60, Std Dev ~15 (range: 30-90 for 95%)
```

**Tracking:**
- Monthly histogram chart (Looker/Tableau)
- Percentile table: 10th, 25th, 50th, 75th, 90th
- Cohort comparison: Organic cohort vs launch event cohort (different difficulty?)
- Competency breakdown: Which competencies have highest/lowest avg score?

**Red Flags:**
- Mean < 50: Questions too hard (LLM setting incorrect; reassess calibration)
- Mean > 70: Questions too easy (inflate scores; badges lose credibility)
- Std Dev < 10: No discrimination (everyone gets same score; assessment broken)
- Skewed distribution: Potential bias (e.g., LLM favors certain backgrounds)

---

### Verification Rate (Self-Assessed → Org-Attested)
**Definition:** % of volunteer claims (skills, experience) that are verified/attested by organizations.

**Target:** >30% within 12 months (demonstrates org engagement + trust building).

**Why Matters:**
- Attestation = org endorsement (increases profile credibility)
- Feedback loop for volunteers (improve areas where attestation is low)
- Org engagement proxy (active orgs are attesting profiles)

**Calculation:**
```
Verification Rate = (volunteers with ≥1 skill attested by org) / (total volunteers) × 100%
```

**Tracking:**
- Org engagement: Which orgs are most active in attestation?
- Volunteer engagement: Who gets attested? (badge level, profile completeness)
- Competency breakdown: Which skills are most frequently attested? (market validation)

**Improvement Levers:**
- In-app prompt: "X people viewed your profile. Invite them to verify your skills."
- Org incentive: Leaderboard for most-attesting orgs (gamification)
- Email: "You're missing attestations. Reach out to mentors!" (referral)

---

### LLM Evaluation Accuracy
**Definition:** % agreement between human expert evaluation and LLM evaluation on a sampled assessment (BLEU score, semantic similarity).

**Target:** >90% agreement (human judges ≈ LLM judges).

**Why Matters:**
- Validates AURA score legitimacy (LLM isn't hallucinating/gaming)
- Detects bias (e.g., LLM penalizes non-native English speakers)
- Regulatory compliance (audit trail for data privacy/fairness)

**Methodology:**
1. Monthly: Sample 50 recent assessments
2. 2 human experts (blind) evaluate responses using rubric
3. Compare expert consensus to LLM score
4. Calculate agreement rate (Cohen's kappa ≥ 0.80 = acceptable)

**Calculation:**
```
Agreement Rate = (assessments where LLM score matches expert consensus) / 50 × 100%
```

**Tracking:**
- Kappa statistic: Inter-rater reliability (human experts ≈ LLM)
- Competency breakdown: Which competencies have lowest agreement? (flag for retraining)
- Bias analysis: Does agreement vary by volunteer demographics? (gender, age, language)

**Remediation:**
- LLM score mismatch → Retrain LLM prompt, add examples
- Systematic bias → Audit data for fairness (gender, language, education bias)
- Low agreement → Expand human review sample; consider third expert opinion

---

### Assessment Reliability (Cronbach's Alpha)
**Definition:** Internal consistency of the 8-question adaptive CAT; measures if questions correlate with overall score.

**Target:** >0.70 (good internal consistency; >0.80 = excellent).

**Why Matters:**
- Validates that all questions measure same construct (volunteer aptitude)
- Low alpha = questions are unrelated (assessment broken)
- Regulatory/academic credibility (published assessments report alpha)

**Calculation:**
```
Cronbach's Alpha = (number of items / (number of items - 1)) ×
                   (1 - (sum of variances / total variance))
```

**Tracking:**
- Quarterly: Calculate alpha across all assessments
- Cohort: Alpha by demographic group (check for differential reliability)
- Item analysis: Remove questions with low item-total correlation (if alpha < 0.70)

**Improvement:**
- Low alpha → Review CAT algorithm (are adaptive paths causing inconsistency?)
- Low correlation for Q3 → Rewrite Q3 (clearer, more discriminating)
- Demographic mismatch → Different alpha for different groups (potential bias)

---

## Operational Metrics (Supporting)

### Infrastructure & Performance
- **API latency:** p95 response time <200ms
- **Assessment completion latency:** LLM evaluation + IRT calculation <5s
- **Uptime:** >99.5% (SLA)
- **Error rate:** <0.5% (API errors, failed LLM calls)

### Product Development Velocity
- **Deployment frequency:** >2x per week (continuous deployment)
- **Cycle time:** <1 week from feature request to production
- **Bug fix time:** Critical bugs fixed <24h

### Support & Community
- **Support response time:** <4 hours (Slack, email)
- **NPS (Net Promoter Score):** >50 (target)
- **Community engagement:** >20% of volunteers active in discussion forums/Discord

---

## Dashboards & Cadence

### Daily Dashboard (Internal — Slack Summary)
- MAAV (Free, Pro breakdown)
- Sign-ups (previous 24h)
- API errors / infrastructure alerts
- Top events registered

### Weekly Dashboard (Product Team — Metrics Sync)
- MAAV trends + cohorts
- D1/D7 retention (current week signups)
- Conversion funnel (assessment → Pro)
- Top churned reasons (new feedback)

### Monthly Dashboard (Leadership — Business Review)
- MRR + MoM growth rate
- MAAV, ARPU, CAC payback
- Org adoption (Starter → Growth conversion)
- Quality metrics (AURA distribution, LLM accuracy audit)
- North Star + all secondary KPIs

### Quarterly Review (Board + Stakeholders)
- 12-week growth vs targets (conservative/optimistic scenarios)
- Cohort retention curves (showing if retention improving)
- Roadmap impact (did feature X improve metric Y?)
- Capital runway + burn rate

---

## Metric Ownership & Alerts

| Metric | Owner | Alert Threshold | Action |
|--------|-------|-----------------|--------|
| MAAV | Product | <80% of target | Emergency sprint on activation |
| Assessment Completion | Product | <65% | UX audit; test new copy |
| D7 Retention | Product | <25% | Email campaign; engagement features |
| Time to Score | Engineering | >20 min | Algorithm latency review |
| MRR | Finance | <80% of target | Pricing review; upsell urgency |
| Pro Conversion | Growth | <3% | A/B test trigger; discounts |
| LLM Accuracy | QA | <85% | Prompt retraining; human review |
| API Uptime | Ops | <99% | On-call incident response |

---

## See Also
- [[BUSINESS-MODEL]]: Revenue targets and unit economics
- [[ROADMAP]]: Feature timeline and expected metric impacts
- [[ADR-001-AURA-Weights]]: AURA scoring methodology (impacts distribution)
- [[TECH-STACK]]: Analytics tool setup (Mixpanel, Stripe, GSC integration)

