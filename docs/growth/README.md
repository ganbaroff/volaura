# Volaura Growth Knowledge Base

This directory contains Volaura's comprehensive growth strategy, covering viral mechanics, email lifecycle, event activation, and B2B sales. All documents are cross-referenced using Obsidian-style [[wiki-links]].

## Documents

### [[VIRAL-LOOP.md]]
**Core viral growth engine** — Badge-sharing loops, referral mechanics, leaderboards, gamification.
- Share triggers (score reveal, badge upgrade, leaderboard rank)
- Social proof amplifiers (live leaderboard, geo-segmentation, org logos)
- K-factor targets and monitoring
- Streaks, AURA Stars, competency specialization
- **Key metric:** K > 1.2 (each user brings 1.2+ new users)

### [[EMAIL-STRATEGY.md]]
**Lifecycle and transactional email system** — Nurtures users from signup through sharing and retention.
- Transactional emails (welcome, score ready, badge change, attestation, peer verification)
- Lifecycle sequences (Day 1 nudge → Day 90 reassessment)
- Resend + React Email implementation
- Bilingual templates (AZ/EN)
- List management, compliance, unsubscribe handling
- **Key metric:** 25% of assessed users share via email trigger

### Launch Event Strategy
**Event-specific strategy** — Turning the launch event (May 2026) into a concentrated growth moment.
- Pre-event positioning (landing page, social campaigns, printed collateral)
- On-site experience (booth, quick-mode assessment, live leaderboard, photo booth, org meetings)
- Post-event follow-up (email sequences, referral push, top performers recognition)
- Offline-first assessment, queue management
- **Key targets:** 500+ signups, 300+ assessments, K > 2.0 during event

### [[ORG-ACQUISITION.md]]
**B2B sales strategy** — Building the demand side: acquiring organizations that post events and create volunteer engagement.
- Target org segments (NGOs, event organizers, government, corporate, universities)
- Acquisition funnel (awareness → trial → activation → retention → paid)
- Outreach channels (launch event, cold email/LinkedIn, partnerships, content)
- Onboarding flow (profile creation → verification → dashboard → first event → attestation)
- Pricing tiers (Free, Growth $29/mo, Enterprise $99/mo+)
- **Key targets:** 5 pilot orgs pre-launch event, 15 total by Month 1, 50 orgs + 10 paid by Month 6

## How They Connect

```
                          ┌──────────────────┐
                          │ LAUNCH EVENT     │ (May 2026)
                          │ ACTIVATION       │
                          └────────┬─────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ↓                             ↓
            ┌──────────────┐          ┌──────────────────┐
            │  VIRAL-LOOP  │          │ ORG-ACQUISITION  │
            │ (Users share)│          │ (Orgs post)      │
            └──────┬───────┘          └────────┬─────────┘
                   │                           │
                   │ Referrals, badges,       │ Events, attestations,
                   │ social amplification     │ verification
                   │                           │
                   └───────────┬───────────────┘
                               ↓
                        ┌──────────────────┐
                        │ EMAIL-STRATEGY   │
                        │ (Triggers all    │
                        │  above flows)    │
                        └──────────────────┘
```

**Flow:**
1. **Email triggers signup** → User takes assessment
2. **Email triggers sharing** → Referrals increase (VIRAL-LOOP)
3. **Email invites to events** → Orgs post events (ORG-ACQUISITION)
4. **Events drive attestations** → AURA scores improve, more sharing
5. **Email celebrates milestones** → Leaderboards, badges drive FOMO, more signups

## Implementation Roadmap

**Phase 1 (Weeks 1-2, Pre-Launch Event):**
- [ ] Implement [[VIRAL-LOOP]] core mechanics (score reveal modal, referral tracking, leaderboard)
- [ ] Deploy [[EMAIL-STRATEGY]] transactional emails (welcome, score ready, magic link)
- [ ] Launch launch event pre-event positioning (landing page, social campaigns)
- [ ] Begin [[ORG-ACQUISITION]] cold outreach (LinkedIn, email to 30 target orgs)

**Phase 2 (Weeks 3-4, Pre-Launch Event):**
- [ ] Badge upgrades, rank notifications [[VIRAL-LOOP]]
- [ ] Lifecycle emails (Day 1, Day 7) [[EMAIL-STRATEGY]]
- [ ] Print collateral for launch event
- [ ] 5 pilot orgs signed up [[ORG-ACQUISITION]]

**Phase 3 (Week 5, at Launch Event):**
- [ ] Booth activation, live leaderboard at event
- [ ] Event reminder emails [[EMAIL-STRATEGY]]
- [ ] Org rep meetings [[ORG-ACQUISITION]]
- [ ] On-site referral tracking [[VIRAL-LOOP]]

**Phase 4 (Weeks 6+, Post-Launch Event):**
- [ ] Post-event email sequences [[EMAIL-STRATEGY]]
- [ ] Referral push [[VIRAL-LOOP]]
- [ ] Organization onboarding acceleration [[ORG-ACQUISITION]]
- [ ] Monthly AURA Stars recognition [[VIRAL-LOOP]]
- [ ] A/B testing on all channels

## Key Success Metrics

| Domain | Metric | Target (Month 1) | Target (Month 6) |
|--------|--------|------------------|------------------|
| **Viral** | K-factor | 1.2+ | 1.5+ |
| | Monthly active sharers | 40% of assessed | 60%+ |
| **Email** | Transactional open rate | 45%+ | 50%+ |
| | Email-driven signups | 15% | 25%+ |
| **Launch Event** | Event signups | 500+ | N/A |
| | Assessments completed | 300+ | N/A |
| **Orgs** | Active organizations | 5 | 50 |
| | Orgs on paid tier | 0 | 10+ |
| **Overall** | Total users | 700+ | 2000+ |
| | Monthly active users | 60% | 70%+ |

## Dependencies & Tech Stack

**Frontend (Next.js 14):**
- [[VIRAL-LOOP]] requires: Zustand (referral state), TanStack Query (leaderboard realtime), Framer Motion (badge animations)
- [[EMAIL-STRATEGY]] requires: i18n (bilingual emails), dynamic OG image generation
- Launch event strategy requires: Service workers (offline assessment caching), WebSocket (live leaderboard)

**Backend (FastAPI):**
- [[EMAIL-STRATEGY]] requires: Resend SDK, React Email, Supabase Edge Functions (scheduled emails)
- [[VIRAL-LOOP]] requires: Supabase RPC functions (leaderboard queries), loguru (analytics logging)
- [[ORG-ACQUISITION]] requires: Supabase (org profiles, attestations), webhook handling

**Database (Supabase + pgvector):**
- New tables: `referral_conversions`, `email_logs`, `attestations`, `organizations`, `events`
- RPC functions: `get_leaderboard()`, `match_volunteers()`, `calculate_aura_score()`

## Ownership & Maintenance

- **[[VIRAL-LOOP]]:** Product engineer + growth
- **[[EMAIL-STRATEGY]]:** Growth engineer (email templates, Resend integration)
- **Launch event strategy:** Event project manager + all hands
- **[[ORG-ACQUISITION]]:** Founder/CEO (sales), growth support

## Related Documents

- [[../../CLAUDE.md]] — Tech stack, project rules
- [[../DECISIONS.md]] — Architectural decisions, AURA score weights
- [[../HANDOFF.md]] — Design system, component documentation (when available)

## Notes

- All cross-references use Obsidian wiki-links for easy navigation in editors like Obsidian, VS Code
- Email templates use i18n keys; actual copy should be in `packages/i18n/locales/{locale}/email.json`
- Metrics can be tracked in Supabase (tables) or exported to analytics tool (Mixpanel, PostHog)
- This is a living document—update after each phase with actual results, learnings
