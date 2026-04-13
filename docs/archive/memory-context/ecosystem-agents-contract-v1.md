# ECOSYSTEM-AGENTS-CONTRACT v1
**Version:** 1.0 | **Date:** 2026-04-10
**Author:** CTO (Claude) | **Approved by:** Yusif Aliyev
**Canonical copies:** mindshift/memory/wip-ecosystem-agents-contract.md + this file

---

## This file must be synced between both projects when changed.

## What This Contract Defines

Agents as world inhabitants + transparent crystal economy + closed elite communities.
All entities below are implemented in MindShift Supabase (migrations 016-019).

---

## Agent Tiers

| Tier | LLM | Available to | Notes |
|------|-----|-------------|-------|
| FREE | Gemini 2.5 Flash | All users | Hardcoded fallback first, AI replaces if <4s |
| PRO | Groq (fast) | Pro subscribers | Sub-200ms, richer context, no rate limit |
| ELITE | Groq + custom system prompt | Elite community members only | Exclusive to that community |

## Agent Ranks (from Python swarm — identical system)

| Rank | Weight | Condition |
|------|--------|-----------|
| PROBATIONARY | 0.8x | New, first 20 interactions |
| MEMBER | 1.0x | Competency confirmed |
| SENIOR | 1.1x | 50+ interactions, accuracy ≥70% |
| LEAD | 1.2x | Best in their domain group |
| QUARANTINE | 0.3x | Chronic underperformer — outputs reviewed before acting |

## Agent States

`idle → listening → working → recovering → offline`

## Baseline Agents (seeded in migration 016)

| Slug | Tier | Specialty | ZEUS ID |
|------|------|-----------|---------|
| mochi | FREE | Focus companion | mochi-respond |
| guardian | PRO | Bug catcher / security | security-agent |
| strategist | PRO | Growth analytics | analytics-retention-agent |
| coach | FREE | ADHD support | ux-research-agent |
| scout | FREE | Product exploration | product-agent |

---

## Crystal Economy

### Two Crystal Types

| Type | How Earned | Transferable | Use |
|------|-----------|-------------|-----|
| FOCUS | Focus sessions (1 min = 5 crystals) | No | XP, shop items |
| SHARE | Admin grants, ecosystem rewards | Yes (donate) | Community entry, shareholder positions |

### Crystal Ethics (Constitution — never violate)
1. Crystals NEVER expire
2. No timers in shop
3. Transparent formula always shown: "1 min = 5 FOCUS crystals"
4. Shop never interrupts (never post-session popup)
5. 24h refund on purchases

---

## Community Tiers

| Tier | Entry Cost | Anonymous | Agents | Notes |
|------|-----------|-----------|--------|-------|
| OPEN | 0 crystals | No | FREE | Public, joinable by all |
| ELITE | 10,000 SHARE crystals | Optional | ELITE | Fight Club rules. Shareholders. |

### Elite Community Rules
- What happens inside stays inside (no public disclosure of discussions)
- Members get unique badge + optional alias (anonymous outside, known inside)
- Members become shareholders by staking SHARE crystals
- Agent access: ELITE-tier agents only accessible here

---

## Shareholder Mechanics

- Shareholders = ELITE community members who stake SHARE crystals
- Revenue snapshot published monthly (public transparency)
- Dividend pool = 50% of net income (when positive)
- Distribution formula: (user_share_units / total_community_shares) × dividend_pool
- Dividends credited as FOCUS crystals (internal utility, not equity)
- Legal note: these are internal utility credits, NOT securities. No fiat withdrawal in v1.

---

## New Event Types (append to character_events)

```
agent_activated         zeus    { agent_id, tier, state }
agent_leveled_up        zeus    { agent_id, old_rank, new_rank }
agent_caught_bug        zeus    { agent_id, product, severity }
agent_helped_user       zeus    { agent_id, user_id, resolution_ms }
community_created       volaura { community_id, tier, entry_cost }
community_joined        volaura { user_id, community_id, crystal_spent }
crystal_earned          ms/vl   { user_id, type: 'FOCUS'|'SHARE', amount, source }
crystal_donated         volaura { from_user_id, to_user_id, amount }
dividend_accrued        volaura { user_id, community_id, amount }
dividend_claimed        volaura { user_id, community_id, amount }
revenue_snapshot_published vl   { period, net_income, dividend_pool }
```

---

## New Supabase Tables (MindShift migrations 016-019)

| Table | Migration | Purpose |
|-------|-----------|---------|
| agents | 016 | Agent profiles, tier, rank, state |
| agent_state_log | 016 | Audit: every state transition |
| communities | 017 | OPEN and ELITE communities |
| community_memberships | 017 | Who is where, badges, aliases |
| crystal_ledger | 018 | Append-only financial ledger |
| shareholder_positions | 018 | Stake + dividend tracking |
| revenue_snapshots | 019 | Monthly public financial report |

---

## Sync Protocol

When MindShift changes this contract:
→ Update `mindshift/memory/wip-ecosystem-agents-contract.md`
→ Update this file `VOLAURA/memory/context/ecosystem-agents-contract-v1.md`

When VOLAURA changes:
→ Update `VOLAURA/docs/MINDSHIFT-INTEGRATION-SPEC.md`
→ Notify via `VOLAURA/memory/swarm/ceo-inbox.md`
