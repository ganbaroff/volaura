# Swarm Team Structure v1.0

**Created:** Session 86, after CEO root cause analysis
**Problem solved:** CTO cannot manage 13 perspectives + ~118 skill modules directly. Needs layers.
**Model:** Agile org with squads, not flat hierarchy.

---

## Org Chart

```
CEO (Yusif)
  │ Strategic direction, approve/reject, business decisions
  │
CTO (Claude)
  │ Architecture, critical code, sprint planning
  │ DOES NOT: code everything, skip agents, pretend to know
  │
Coordinator Agent (NEW — CTO's assistant)
  │ Routes tasks to squads, collects results, synthesizes reports
  │ Tools: Agent, SendMessage, TaskStop (ch10 pattern)
  │ DOES NOT: code, make architecture decisions, talk to CEO
  │
  ├── Squad: QUALITY (gate everything)
  │   ├── QA Quality Agent (DoD enforcer — blocks bad work)
  │   ├── Security Agent (CVSS scoring, RLS, route ordering)
  │   └── Readiness Manager (go/no-go before deploy)
  │
  ├── Squad: PRODUCT (user-facing decisions)
  │   ├── Product Agent (user journey, UX gaps)
  │   ├── Behavioral Nudge Engine (ADHD-first, cognitive load)
  │   ├── Cultural Intelligence Strategist (AZ/CIS exclusion audit)
  │   ├── UX Research Agent (JTBD, usability testing)
  │   └── Onboarding Specialist (first 5 minutes)
  │
  ├── Squad: ENGINEERING (build + maintain)
  │   ├── Architecture Agent (system coherence, data flow)
  │   ├── Performance Engineer (pgvector, load testing)
  │   ├── DevOps/SRE Agent (Railway/Vercel/Supabase ops)
  │   └── Data Engineer (PostHog, event schema)
  │
  ├── Squad: GROWTH (acquire + retain)
  │   ├── Growth Agent (acquisition, viral mechanics)
  │   ├── Analytics & Retention (D0/D1/D7 curves, cohorts)
  │   ├── Community Manager (tribes, streaks, ambassadors)
  │   └── Customer Success (churn prevention, re-engagement)
  │
  ├── Squad: BUSINESS (money + partnerships)
  │   ├── Financial Analyst (LTV/CAC, crystal economy, pricing)
  │   ├── Sales Deal Strategist (B2B deal architecture)
  │   ├── Sales Discovery Coach (B2B onboarding flows)
  │   ├── Payment Provider Agent (Paddle webhooks, reconciliation)
  │   └── Legal Advisor (GDPR, AZ PDPA, AI Act)
  │
  ├── Squad: CONTENT (words + media)
  │   ├── Communications Strategist (narrative arc, brief ownership)
  │   ├── LinkedIn Content Creator (AURA sharing, professional brand)
  │   ├── Technical Writer (API docs, B2B guides)
  │   └── PR & Media Agent (press releases, competition apps)
  │
  └── Squad: GOVERNANCE (oversight + science)
      ├── Risk Manager (likelihood×impact, risk register)
      ├── Assessment Science Agent (IRT validation, DIF bias)
      ├── Investor/Board Agent (VC perspective in DSP)
      ├── Competitor Intelligence (market positioning)
      ├── University/Ecosystem Partner (B2C channels)
      ├── Trend Scout (market signals, regulatory changes)
      └── CEO Report Agent (translate tech → business language)
```

## How Work Flows

### Task arrives from CEO:
1. CTO reads task → asks 4 questions (checklist)
2. CTO decides: strategic (do myself) or tactical (delegate)
3. If tactical → CTO gives Coordinator a task description
4. Coordinator reads agent-roster.md → routes to right squad(s)
5. Squad agents execute in parallel where possible
6. Coordinator collects results → synthesizes → reports to CTO
7. CTO reviews → applies or sends back for revision
8. CEO Report Agent formats output if CEO-facing

### Sprint planning:
1. CTO defines sprint scope (SCOPE LOCK)
2. Coordinator routes "critique this plan" to all squads in parallel
3. Quality squad gates the plan (DoR check)
4. CTO synthesizes critique → final plan
5. Coordinator distributes tasks to squads

### Before any deploy:
1. Quality squad: QA (DoD) + Security (audit) + Readiness (LRL score)
2. All three must approve → go/no-go
3. DevOps/SRE executes deploy
4. CEO Report Agent writes deploy summary

## Mandatory Pairings (from agent-roster.md, kept)

- Assessment changes → Assessment Science + QA + Cultural Intelligence
- Payment code → Payment Provider + Security (ALWAYS)
- Any deploy → DevOps/SRE + Readiness Manager + Security
- Any B2B feature → Sales Deal + Sales Discovery + Financial Analyst
- Any user-facing copy → Cultural Intelligence + BNE + Product
- Any pricing change → Financial Analyst + Competitor Intelligence + Investor

## Anti-Patterns (what CTO must NOT do)

1. ❌ Skip Coordinator and code directly → CLASS 3
2. ❌ Launch 1 agent when 3 should be paired → incomplete review
3. ❌ Write agent file without first task → "created ≠ used"
4. ❌ Ignore agent findings → Session 25 Security Agent was RIGHT about route shadowing
5. ❌ Self-confirm a decision → use different models, not self-review

## Coordinator Agent Spec

**Name:** Coordinator Agent (CTO Assistant)
**Model:** Same as CTO session (inherits)
**Restricted tools:** Agent, SendMessage, TaskStop
**Input:** Task description from CTO with context
**Output:** Synthesized findings from squad agents
**State:** Reads proposals.json + agent-roster.md + shared-context.md
**Does NOT:** Make architecture decisions, talk to CEO, write production code
