# Agent Roster — Swarm Team

**Purpose:** Agents know who's on the team and what each agent is best at.
**Updated:** 2026-03-26 (Session 42)

---

## Active Agents

| Agent Role | Model | Primary Strength | Known Weakness | Recent Score |
|-----------|-------|-----------------|----------------|-------------|
| Architecture Agent | haiku | System coherence, data flow gaps, storage math | Sometimes misreads auth patterns | 6.5/10 |
| Security Agent | haiku | CVSS scoring, attack vectors, injection patterns, XSS detection | Needs actual DB state to verify RLS correctness | 8.0/10 |
| Product Agent | haiku | User journey gaps, Leyla/Nigar persona gaps, adoption risks | Doesn't have usage data | 5.5/10 |
| QA Engineer Agent | haiku | Blind cross-testing, test generation, coverage analysis | Self-assessment circularity (Mistake #47) | 7.0/10 |
| SWE Agent | haiku | Code review, verb regex calibration, edge case detection | Self-assessment circularity (Mistake #47) | 6.5/10 |
| Needs Agent | haiku | Meta-analysis, process improvement, swarm structure | N/A (introspective role) | N/A |

---

## When to Call Each Agent

| Task | Best Agent |
|------|-----------|
| New API endpoint design | Architecture Agent |
| RLS policy review | Security Agent |
| New feature UX review | Product Agent + load: neuroscience-design skill |
| Any UI copy / achievement / reward mechanic | Product Agent + load: neuroscience-design skill |
| Assessment UX flow review | Product Agent + load: neuroscience-design skill |
| Cross-product integration feature | Architecture Agent + load: neuroscience-design skill |
| Sprint planning critique | All agents in parallel |
| Code change >50 lines | Architecture + Security |
| New user-facing flow | Product Agent |
| Process improvement | Needs Agent |
| Data model changes | Architecture Agent |
| New auth flow | Security Agent |
| Assessment question design / keywords | QA Engineer + Security (GRS gate + adversarial review) |
| Anti-gaming / evaluation pipeline changes | Security + QA Engineer |
| Test generation / coverage analysis | QA Engineer |
| Code review (business logic) | SWE Agent |
| Verb regex / keyword calibration | SWE + QA Engineer |
| Content for CEO | Fact-Check Agent (agent-launch-template.md) |
| SQL scripts / migrations | Architecture + Security |
| CEO evaluation / professional review | All agents in parallel |
| Route ordering review (/{id} patterns) | Security Agent (Session 42 P0: route shadowing IS real) |

---

## CRITICAL LESSON: Route Shadowing IS Real (Session 42)

Session 25 Security Agent flagged route shadowing `/me` vs `/{volunteer_id}` — CTO dismissed as "FastAPI handles it." **Session 42 proved the agent was RIGHT.** `/me/explanation` was unreachable because `/{volunteer_id}` was registered first. Static routes MUST precede parameterized routes.

**Rule:** Never dismiss agent security findings without verification. Security Agent was correct, CTO was wrong.

---

## CRITICAL LESSON: Self-Assessment Is Invalid (Session 42)

QA/SWE/Security agents generated assessment questions, wrote "expert" answers targeting their own keywords, scored 0.59-0.89. CEO caught the circularity. Blind cross-test proved buzzword persona scores 0.77 — nearly matching "experts."

**Rule:** ALL assessment validation requires BLIND cross-evaluation. Creator must NOT evaluate their own work.

---

## Escalation Rules

- If Security Agent finds CVSS >= 8.0 -> CTO must fix before any other work
- If Architecture Agent scores design < 5/10 -> don't implement, redesign
- If Product Agent finds >3 critical user journey gaps -> ship partial, not full feature
- If QA Engineer flags GRS < 0.6 on a question -> question cannot deploy
- Any agent can veto by scoring < 35/50 in DSP

---

## What Agents Need in Every Task Prompt

**Required (blocks good work without these):**
1. shared-context.md (C:\Projects\VOLAURA\memory\swarm\shared-context.md) — architecture decisions, current sprint, schema
2. Specific code snippet being reviewed
3. Current sprint goal
4. Relevant skill files (SECURITY-REVIEW.md, TDD-WORKFLOW.md, etc.)

**Helpful:**
5. Related file context
6. agent-feedback-log.md — learn from past findings
7. Which other agents are running in parallel

---

## Agent Improvement Tracking

| Agent | Session | Was Agent Right? | Note |
|-------|---------|-----------------|------|
| Security Agent | 25 | Yes (4/5 correct) | Route shadowing was initially dismissed — proved correct in Session 42 |
| Architecture Agent | 25 | Mostly (4/6 correct) | SupabaseAdmin fix was wrong context |
| Product Agent | 25 | Yes (all gaps real) | Can't prioritize without usage data |
| Needs Agent | 25 | Yes (schema snapshot was top need) | Schema now in shared-context.md |
| Security Agent | 42 | Yes (3/3 correct) | Found P0 route ordering, P0 stored XSS, P1 concept injection |
| QA Engineer | 42 | Yes (blind cross-test was correct methodology) | Proved keyword_fallback = vocabulary test |
| QA Engineer | 42 | Partial (self-assessment was circular) | Mistake #47: scored 0.59-0.89 on own questions |
| SWE Agent | 42 | Yes (verb regex calibration correct) | Expanded 45 -> 100+ verbs, fixed false positives |
