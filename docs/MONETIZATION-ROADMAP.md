# Volaura Ecosystem — Monetization Roadmap v1.0
> Written: 2026-03-27 | Agent-validated (3 parallel agents) | CTO synthesis

## Summary

**Path:** Hybrid — volunteer core free + org premium + crystal cosmetics/queue
**Tier count:** 2 (Free + Pro) for launch. Ultra deferred until 500+ paying users.
**Primary crystal sink:** Queue Skip mechanic (Yusif's design — pay to get sooner, not to avoid harm)
**Ethics constraint:** AURA scores, credentials, and visibility are never monetized.

---

## Tier Structure

### Free (default — always)
- 1 assessment per 30 days
- AURA score + badges (all earned skills)
- Basic profile visibility
- Life Simulator + MindShift (basic)
- Text AI Twin
- Crystal earning (daily login + gameplay)

### Pro — 4.99 AZN/month (~$2.95)
- Unlimited assessments
- Immediate access (no queue) for all AI features
- 100 crystals/month allowance
- 3 queue skips/month included
- LinkedIn auto-post integration
- Priority org visibility

### Organizations — 49-199 AZN/month
- Volunteer analytics dashboard
- Skill-based matching
- Bulk CSV invite (already built)
- Aggregate AURA reporting

---

## Crystal Economy — Complete Ledger

### Sources
| Source | Crystals | Cap |
|--------|---------|-----|
| Daily login | 5/day, 15 on day 7 | 15/day |
| Assessment complete | 50 per competency | 400 total (8 competencies) |
| MindShift focus session | floor(minutes/10) | 30/day |
| Life Sim milestone | 10-25 | One per type |
| Referral bonus | 25 (giver + receiver) | 1 per referral |
| Stripe: 100 crystals | $0.99 | No cap |
| Stripe: 600 crystals | $4.99 | No cap |
| Stripe: 1400 crystals | $9.99 | No cap |

### Sinks — Queue Skip (PRIMARY)
| Feature | Free wait | Crystal skip | Pro |
|---------|-----------|-------------|-----|
| Voice avatar | 48h | 10 crystals | immediate |
| Video avatar | 72h | 25 crystals | immediate |
| AI portrait animation | 24h | 5 crystals | immediate |
| Detailed AURA report | 12h | 8 crystals | immediate |
| Extra assessment slot | 30d cooldown | 30 crystals | immediate |
| LinkedIn post generation | 4h | 5 crystals | immediate |
| Peer review priority | 7d | 15 crystals | 24h |

### Sinks — Premium Experiences (SECONDARY)
| Item | Cost |
|------|------|
| Life Sim special events | 150 |
| Celebrity NPC quest (BrandedBy) | 150 |
| Cosmetics (avatar/home) | 50-300 |
| Time capsule | 100 |
| Gift to friend | 50-200 |
| Custom badge frame | 75 |

---

## Queue Mechanic — 12 Applications Found

Ordered by revenue impact:

**High:**
1. BrandedBy AI video generation (500-1000 crystals)
2. Volaura custom assessment extra slot (30 crystals)
3. Volaura peer review priority (15 crystals)

**Medium:**
4. Voice AI Twin (10 crystals)
5. LinkedIn auto-post (5 crystals/post)
6. MindShift coaching session (10 crystals)
7. Detailed AURA explanation (8 crystals)
8. Resume optimization (12 crystals)

**Lower volume:**
9. Life Sim leaderboard snapshot (5 crystals)
10. Life Sim XP calculation detail (5 crystals)
11. AI Twin re-training after AURA update (15 crystals)
12. Organization batch AURA report (200 crystals / org plan)

**UX pattern (same everywhere):**
> "Your voice is queued — ready in 48h. Skip for 10 crystals? You have 85 crystals."
> [Skip Queue] [Wait] [Get More Crystals]

---

## Revenue Projections

| Scenario | MAU | Monthly Revenue |
|----------|-----|----------------|
| Month 6 | 1,000 | ~1,694 AZN (~$995) |
| Month 12 | 5,000 | ~7,969 AZN (~$4,690) |
| Break-even | ~2,000 | ~$2,000/month (covers Railway + Supabase + misc) |

---

## Ethics Red Lines — NEVER Monetized

| Feature | Why never |
|---------|----------|
| AURA score increase | Core trust = org credibility. One sale kills the platform. |
| Badge without assessment | Legal + brand existential risk |
| Visibility manipulation | Volunteers must compete on merit only |
| Assessment shortcuts | Same as badge without assessment |
| Data selling (behavior to orgs) | GDPR + AZ data law |
| Pay-to-avoid-harm | ADHD-first design principle |

---

## Implementation Roadmap

| Sprint | Deliverable | Status |
|--------|------------|--------|
| A0 ✅ | Crystal ledger (character_events + game_crystal_ledger) | DONE |
| A1 | Volaura assessment complete → crystal_earned (50/skill) | NEXT |
| A2 | MindShift → character_state (focus → XP) | Planned |
| A3 | Life Sim bug fixes | Planned |
| A4 | Voice AI Twin + queue infrastructure | Planned |
| A5 | Stripe integration (crystal purchase) | Planned |
| A6 | Pro tier billing (Stripe subscriptions) | Planned |
| B4+ | BrandedBy video queue + celebrity NPC | Parallel track |
| Year 2 | Ultra tier, org analytics v2 | After 500+ users |

---

## CEO Open Questions

1. **AZN pricing:** 4.99 AZN/month confirmed?
2. **Payment processor:** Stripe or Kapital Bank first?
3. **Queue wait times:** 48h/72h long enough to drive crystal purchases, or too long?
4. **Referral program:** Launch with product or wait for 100+ users?
5. **Crystal gifting:** Enable at launch or post 1,000 users?
