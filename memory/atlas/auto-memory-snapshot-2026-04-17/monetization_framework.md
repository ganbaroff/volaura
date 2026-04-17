---
name: Monetization Framework — Crystal Economy + Tier Structure
description: Complete monetization strategy: tier structure (Free/Pro/Ultra), crystal economy, queue mechanic (12 applications), ethics red lines, pricing in AZN. Agent-validated (3 parallel agents, 2026-03-27).
type: project
last_updated: 2026-03-27
---

# VOLAURA ECOSYSTEM — Monetization Framework v1.0

> Agent-validated: 3 parallel agents (queue applications, tier structure, ethics) — 2026-03-27.
> DSP winner: PATH 4 — Hybrid (volunteer free + org premium). Score: 50.7/50.

---

## 1. CORE PHILOSOPHY

**Crystals = make life richer. NOT: avoid death. NOT: pay-to-win.**

Three principles (non-negotiable — CEO has ADHD, product is ADHD-first):

1. **Free users get the full product** — assessment, AURA, badges, basic visibility. Zero degradation.
2. **Paying users get MORE, not protection from less** — faster queue, voice, premium visuals.
3. **No AURA manipulation, ever** — skills are verified, not bought. This is the entire moat.

---

## 2. TIER STRUCTURE

### FREE TIER (default — always)
| Feature | Limit | Why free |
|---------|-------|---------|
| Assessment (any competency) | 1 per 30 days | Core value prop — must be free to verify trust |
| AURA score calculation | Unlimited | Computed from assessments already taken |
| Skill verification badges | All earned | Credentials = the moat. Never paywalled. |
| Basic profile visibility | Yes | Organizations need to find volunteers |
| Daily login reward | 5 crystals/day, 15 on day 7 | Engagement loop seed |
| Crystal earnings via gameplay | Yes (all sources) | Gamification works only if free users can earn |
| Life Simulator (basic) | Yes | Cross-sell funnel to paid |
| MindShift (basic habits) | 3 habits tracked | Enough to show value |
| Text AI Twin | Yes | Simple version without voice |
| Character state (read) | Yes | All products depend on this |

### PRO TIER — 4.99 AZN/month (~$2.95 USD)
| Feature | Value |
|---------|-------|
| Assessments | Unlimited (vs 1/30d) |
| Voice AI Twin (Kokoro/Bark) | Immediate (vs 48h queue) |
| Video avatar | Immediate (vs 72h queue) |
| Detailed AI report | Immediate (vs 12h queue) |
| Monthly crystal allowance | 100 crystals/month |
| Queue skips | 3 included per month |
| MindShift habits | Unlimited |
| LinkedIn integration (auto-post) | Yes |
| Priority org visibility | Yes |
| Badge showcase customization | Yes |

### ULTRA TIER — 12.99 AZN/month (~$7.65 USD)
> ⚠️ DECISION: Skip Ultra for now. AZ market too small. Revisit at 500+ paying users.
> When launched: everything Pro + BrandedBy AI avatar + celebrity NPC quests + dedicated support.

### ORGANIZATION TIER — 49-199 AZN/month
| Plan | AZN/month | Volunteer seats | Features |
|------|-----------|-----------------|---------|
| Starter | 49 | 25 | Dashboard, basic matching |
| Growth | 99 | 100 | Advanced analytics, bulk invite |
| Enterprise | 199 | Unlimited | API access, custom branding, priority support |

**Primary B2B revenue driver.** Orgs get:
- Aggregate AURA analytics across their volunteer pool
- Skill-based matching (find volunteers with verified communication ≥70)
- Bulk CSV invite (already built, Sprint 9)
- Retention and activity dashboards

---

## 3. CRYSTAL ECONOMY — FULL LEDGER

### Sources (HOW users earn crystals)

| Source | Amount | Cap | Anti-farming |
|--------|--------|-----|-------------|
| Daily login | 5 crystals | 15/day (bonus on day 7) | DAILY_CRYSTAL_CAP enforced in API |
| Assessment complete (Volaura) | 50 per competency | 400 total (8 competencies × 50) | game_character_rewards idempotency |
| MindShift focus session | floor(minutes/10) crystals | 30/day | Daily cap per source |
| Life Sim milestone | 10-25 | Event-specific | One per milestone type |
| Stripe purchase | 100/200/400 | None | Real money |
| Referral bonus | 25 (both) | 1 per referral | Referral tracking table |
| Streak milestone (7d/30d/100d) | 25/50/100 | Once per milestone | Milestone table |

**Stripe packages:**
- 100 crystals = $0.99 (~1.68 AZN)
- 600 crystals = $4.99 (~8.47 AZN) [best value]
- 1400 crystals = $9.99 (~16.95 AZN) [whales]

### Sinks (HOW users spend crystals — POSITIVE ONLY)

#### Queue Skip Mechanic (PRIMARY SINK — Yusif's design)
All compute-heavy features use a priority queue. Free = wait. Crystals = skip. Pro = immediate.

| Feature | Free wait | Crystal skip | Pro |
|---------|-----------|-------------|-----|
| Voice avatar (Kokoro/Bark) | 48h | 10 crystals → 1h | immediate |
| Video avatar (SadTalker) | 72h | 25 crystals → 2h | immediate |
| AI portrait animation | 24h | 5 crystals → now | immediate |
| Detailed AURA report | 12h | 8 crystals → now | immediate |
| Custom assessment (extra slot) | 30d cooldown | 30 crystals → now | immediate |
| LinkedIn post generation | 4h | 5 crystals → now | immediate |
| Peer review priority | 7d wait | 15 crystals → 24h | immediate |
| Resume optimization | 48h | 12 crystals → now | Pro |
| Celebrity NPC unlock (BrandedBy) | Never (Pro only) | 400 crystals | included |
| MindShift coaching session | 24h | 10 crystals → now | immediate |
| Life Sim special event | 2 per week | 20 crystals → now | 3 per day |
| AURA leaderboard snapshot | Daily update | 5 crystals → live | immediate |

#### Premium Experiences (SECONDARY SINK)
| Item | Cost | Notes |
|------|------|-------|
| Life Sim special events (travel, education) | 150 | Positive milestone — ADHD safe |
| Celebrity NPC quest (BrandedBy) | 150 | Unique storyline |
| Cosmetics — character appearance | 50-200 | Purely aesthetic |
| Cosmetics — home decoration (Life Sim) | 50-300 | Purely aesthetic |
| Time capsule (save peak moment) | 100 | Memory/nostalgia mechanic |
| Gift crystals to friend | 50-200 | Social bonding |
| Custom badge frame | 75 | LinkedIn-visible |

**NEVER ACCEPTABLE as paid features:**
- AURA score increase
- Skip assessment (get badge without test)
- Hide negative assessment results
- Paid visibility boost on org search results
- Peer review manipulation

---

## 4. QUEUE MECHANIC — 12 APPLICATIONS ACROSS ECOSYSTEM

> From agent analysis (2026-03-27). Ordered by revenue impact.

### HIGH REVENUE IMPACT
1. **BrandedBy AI video generation** (500-1000 crystals) — compute-heaviest feature. Free = 72h. Crystal = 2h. Pro = immediate. GPU cost justification is clear.
2. **Volaura custom assessment extra slot** (30 crystals) — users at 1/30d limit want to test immediately. High conversion: motivated users who just finished one and want another.
3. **Volaura peer review priority** (15 crystals) — social proof acceleration. Orgs prefer verified-by-peer badges.

### MEDIUM REVENUE IMPACT
4. **Voice AI Twin** (10 crystals) — novelty is high, re-engagement is high (notification when ready).
5. **LinkedIn integration auto-post** (5 crystals/post or Pro) — professional motivation drives conversion.
6. **MindShift coaching session** (10 crystals) — perceived high value (feels like therapy session).
7. **Detailed AURA explanation** (8 crystals) — self-insight demand is high after assessment.
8. **Resume optimization** (12 crystals) — concrete career value, high willingness to pay.

### LOWER VOLUME (but good engagement)
9. **Life Sim leaderboard snapshot** (5 crystals) — competitive users, low cost to build.
10. **Life Sim XP calculation (detailed)** (5 crystals) — niche but sticky for power users.
11. **AI Twin training data update** (15 crystals) — when user updates AURA, AI Twin re-trains. One-time per competency update.
12. **Organization batch AURA report** (org feature, 200 crystals or org plan) — premium B2B sink.

### Queue UX Pattern (same everywhere)
```
"Your [feature] is queued — ready in [wait time].
Skip with 10 crystals? You have [balance] crystals."
[Skip Queue] [Wait] [Get More Crystals]
```
Notification (push/email) when ready → 80%+ open rate → re-engagement.
"Not pay-to-avoid-pain, but pay-to-get-sooner." — ADHD-safe framing.

---

## 5. REVENUE MODEL + PROJECTIONS

### Unit Economics (AZ market, conservative)

| Metric | Value |
|--------|-------|
| MAU target (6 months) | 1,000 |
| DAU/MAU ratio | 30% = 300 DAU |
| Pro conversion (volunteers) | 15% = 150 users |
| Avg Pro revenue | 4.99 AZN/month |
| Pro monthly revenue | 749 AZN (~$440) |
| Org conversions | 5 orgs |
| Avg org plan | 99 AZN/month |
| Org monthly revenue | 495 AZN (~$291) |
| Crystal purchases (% of users) | 5% = 50 users |
| Avg crystal spend | 8.99 AZN ($5.30) |
| Crystal monthly revenue | 450 AZN (~$264) |
| **Total monthly (Month 6)** | **~1,694 AZN (~$995)** |

At 5,000 MAU (Month 12):
- Pro: 750 users × 4.99 = 3,742 AZN
- Orgs: 20 × 99 = 1,980 AZN
- Crystals: 5% × 250 = 2,247 AZN
- **Total: ~7,969 AZN (~$4,690/month)**

### Why 2-tier (not 3) for AZ market
- AZ average salary: ~1,200 AZN/month
- 4.99 AZN = 0.4% of salary — reasonable
- 12.99 AZN = 1.1% of salary — stretch for students (core persona)
- Ultra tier requires 500+ paying users to justify support overhead
- Every additional tier adds pricing confusion → lower conversion

---

## 6. ETHICS RED LINES (non-negotiable)

These are NEVER monetized, regardless of revenue pressure:

| Red Line | Why |
|----------|-----|
| AURA score manipulation | Core trust = platform credibility. Org trust dies on day 1. |
| Credential selling (badge without assessment) | Legal risk + existential risk to the brand |
| Assessment shortcuts ("skip questions, get badge") | Same as above |
| Visibility manipulation (paid = higher search results) | Violates volunteers' equal opportunity promise |
| Data selling (user behavior to orgs) | GDPR violation + Azerbaijan data law |
| Pay-to-avoid-harm (life extension, removal from bad list) | ADHD-first principle. Anxiety loop = product dies. |

**Enforcement mechanism:** These are documented in CLAUDE.md as hard rules. Any feature proposal touching these must go to CEO (not CTO) for explicit review.

---

## 7. IMPLEMENTATION PRIORITY

| Sprint | Monetization work | Prerequisites |
|--------|------------------|---------------|
| A0 ✅ | Crystal ledger, event bus | DONE |
| A1 | Volaura assessment → crystal_earned (50/competency) | A0 |
| A4+ | Queue infrastructure (priority_queue table) | A1-A3 |
| A5+ | Voice AI Twin with queue | A4 |
| A6+ | Stripe integration (crystal purchase) | A4 |
| B4+ | BrandedBy video queue | B3 |
| Year 2 | Ultra tier, org analytics v2 | 500+ users |

---

## 8. OPEN QUESTIONS (CEO decisions needed)

1. **AZN pricing finalized?** 4.99 AZN/month confirmed or different?
2. **Stripe or local payment first?** Kapital Bank integration for AZ cards vs Stripe?
3. **Crystal gifting** — enable immediately or after enough users to make it social?
4. **Queue wait times** — are 48h/72h/24h correct, or should they be longer to drive more skips?
5. **Referral program** — launch with product or after first 100 users?
