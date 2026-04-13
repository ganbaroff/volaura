# Agent Pairings Table — Volaura Swarm

**Last updated:** 2026-04-02
**Version:** v1.0
**Why this file exists:** Solo agent analysis misses cross-domain risks. This table defines which agents MUST work together — not "nice to have" but mandatory co-review.

---

## Tier 1 — CRITICAL PATH PAIRS (both must fire before work ships)

These pairs have found critical bugs when together that each would miss alone.
Missing either agent = shipping with a blind spot.

| Trigger | Agent A | Agent B | What they catch together |
|---------|---------|---------|--------------------------|
| Any IRT/CAT change, question added/modified | Assessment Science Agent | Analytics & Retention Agent | A: validates psychometric validity; B: catches instrumentation gaps. Neither alone catches both. |
| Crystal economy change (earn/spend/cap/new source) | Financial Analyst Agent | Security Agent | Financial: catches revenue cannibalization; Security: catches farming/arbitrage attacks. Crystal economy has BOTH risks. |
| Any payment/billing change | Payment Provider Agent | Security Agent | Payment: webhook reliability; Security: signature verification, secret rotation. Silent auth failure = revenue loss + security hole. |
| Any new API endpoint (public or internal) | Security Agent | Technical Writer Agent | Security: auth/RLS/rate limit audit; Technical Writer: documentation must exist before B2B demo. Together = secure AND discoverable. |
| Tribe mechanics change (matching, streaks, kudos) | Community Manager Agent | Analytics & Retention Agent | Community: user psychology + engagement gaps; Analytics: event instrumentation. Feature ships → events must fire → data must be clean. |
| PR campaign or press release | Communications Strategist | PR & Media Agent | Comms: narrative arc + positioning compliance; PR: outlet strategy + timing. Neither works without the other. |
| Any production deployment | DevOps/SRE Agent | Performance Engineer Agent | SRE: env vars, health checks, rollback plan; Performance: latency regression check. Deploy without both = flying blind on production health. |
| Analytics schema change, new event added | Data Engineer Agent | Analytics & Retention Agent | Engineer: builds the instrumentation; Analytics: defines what to measure. Must agree on schema before anything is built. |
| B2B feature (org search, org dashboard, pricing) | Sales Discovery Coach | Assessment Science Agent | Sales: discovery flow + demo readiness; Assessment Science: validity claims that will face scrutiny in B2B demos. |

---

## Tier 2 — HIGH VALUE PAIRS (load both for High/Critical sprints)

| Trigger | Agent A | Agent B | Why together |
|---------|---------|---------|--------------|
| New user-facing screen or flow | Behavioral Nudge Engine | Cultural Intelligence Strategist | Nudge engine prevents friction; Cultural agent prevents tone/framing errors for AZ users. |
| GDPR/data privacy decision | Legal Advisor | Data Engineer Agent | Legal: what data can/cannot be stored; Engineer: retention policies, deletion, schema compliance. |
| Any fundraising or investor-facing material | Investor/Board Agent | Financial Analyst Agent | Investor: due diligence readiness; Financial: unit economics accuracy. Investor agent without clean financials = failed DD. |
| University or partnership outreach | University Ecosystem Partner Agent | PR & Media Agent | Partnership: relationship strategy + proposal; PR: announcement timing + media amplification. |
| Onboarding flow change | UX Research Agent | Behavioral Nudge Engine | UX: usability testing protocol; Nudge: motivation architecture. Both needed to fix activation, neither sufficient alone. |
| Assessment methodology challenged by prospect | Assessment Science Agent | Technical Writer Agent | Science: methodology defense; Technical Writer: documentation that survives "show me the evidence" question. |
| New notification design | Community Manager Agent | Behavioral Nudge Engine | Community: cadence + tribal psychology; Nudge: cognitive load + hook timing. Notifications fire both domains. |
| Any competitor product change | Competitor Intelligence Agent | Growth Agent | Competitor: what changed + implications; Growth: acquisition channel impact. Competitive shift always has channel effect. |
| Railway scaling / infra change | DevOps/SRE Agent | Architecture Agent | SRE: operational execution; Architecture: strategic impact on system design. Ops change without architecture review = new tech debt. |
| Legal entity, jurisdiction, or tax decision | Legal Advisor | Investor/Board Agent | Legal: compliance + risk; Investor: what due diligence will ask. Jurisdiction decisions show up in DD 12 months later. |

---

## Tier 3 — SITUATIONAL PAIRS (load when sprint specifically touches both domains)

| Trigger | Agent A | Agent B | Notes |
|---------|---------|---------|-------|
| Launch checklist sign-off | Readiness Manager | ALL Tier 1 agents | Readiness Manager is the aggregator. Requires all Tier 1 agents to have signed off before go/no-go. |
| AZ content batch (LinkedIn, email, social) | Communications Strategist | Cultural Intelligence Strategist | Content tone + AZ cultural accuracy. |
| B2B sales demo scheduled | Sales Deal Strategist | Technical Writer Agent | Deal strategy + "do the docs exist?" audit. |
| Ambassador program launch | Community Manager Agent | Legal Advisor | Ambassador terms + crystal/reward legal review. |
| Referral program design | Growth Agent | Financial Analyst Agent | CAC impact + referral fraud cost modeling. |
| Cold outreach campaign | Sales Discovery Coach | Cultural Intelligence Strategist | Discovery framework + AZ cultural communication norms. |
| Accelerator application | Accelerator Grant Searcher | Financial Analyst Agent | Application strategy + unit economics that will face scrutiny. |

---

## Mandatory Chain — Feature Launch Sequence

For any feature touching users, this chain fires in order:

```
1. UX Research Agent        → usability validated
2. Behavioral Nudge Engine  → cognitive load checked
3. Assessment Science Agent → (if assessment feature) validity confirmed
4. Security Agent           → auth + RLS + rate limit audited
5. Data Engineer Agent      → instrumentation events defined
6. Analytics Agent          → events match taxonomy, dashboard query written
7. Technical Writer Agent   → documentation exists
8. DevOps/SRE Agent         → deployment checklist passed
9. Performance Engineer     → p95 latency baseline confirmed
10. Readiness Manager       → GO / NO-GO declared
```

Skip any step = Mistake #14 class (solo execution without required pair).

---

## Anti-Pattern Log

Agents that were called ALONE when they should have been paired:

| Date | Agent called solo | Missing partner | What was missed |
|------|------------------|-----------------|-----------------|
| 2026-04-02 | Analytics & Retention Agent | Data Engineer Agent | Event schema defined without infrastructure plan — who builds the table? |
| 2026-04-02 | DevOps/SRE Agent | Performance Engineer Agent | Infrastructure health checklist created without latency baseline targets |
| 2026-04-02 | Financial Analyst Agent | Security Agent | Crystal economy health check written without anti-cheat specifics |

Add new entries when a solo agent miss is caught in retrospective.

---

## Routing Decision Tree

```
Is this a payment/billing change?
  YES → Payment Provider + Security (Tier 1)

Is this a data/analytics change?
  YES → Data Engineer + Analytics & Retention (Tier 1)

Is this a user-facing feature?
  YES → Behavioral Nudge + Cultural Intelligence (Tier 2)
  + UX Research if new screen

Is this a B2B sales-critical item?
  YES → Sales Discovery Coach + Assessment Science (Tier 1)
  + Technical Writer if docs needed

Is this a crystal/gamification change?
  YES → Financial Analyst + Security (Tier 1)

Is this a public announcement?
  YES → Communications Strategist + PR & Media (Tier 1)

Is this a production deployment?
  YES → DevOps/SRE + Performance Engineer (Tier 1)

Is this a new API endpoint?
  YES → Security + Technical Writer (Tier 1)

None of the above → check if sprint matches Tier 2 pairs. If still no match → solo agent acceptable.
```
