# Agent Roster — Swarm Team

**Purpose:** Agents know who's on the team and what each agent is best at.
**Updated:** 2026-03-27 (Session 51 — skill library architecture)

---

## Active Agents

| Agent Role | Model | Primary Strength | Known Weakness | Recent Score | Trend |
|-----------|-------|-----------------|----------------|-------------|-------|
| Security Agent | haiku | CVSS scoring, attack vectors, injection patterns, XSS detection, RLS audits | Overblows low-severity issues (anon keys, timing oracles) | **8.5/10** | +0.5 — proved CTO wrong twice |
| Architecture Agent | haiku | System coherence, data flow gaps, storage math, RLS policy analysis | Sometimes misreads auth patterns | **8.0/10** | +1.5 — found CVSS 9.8 aura_scores |
| Product Agent | haiku | User journey gaps, i18n audits, ADHD-first UX, ecosystem navigation | Needs usage data for retention analysis | **7.5/10** | +2.0 — unfairly low before |
| Needs Agent | haiku | Meta-analysis, process improvement, swarm structure, highest leverage-per-finding | N/A (introspective role) | **7.0/10** | New rating — 2/2 findings changed team workflows |
| QA Engineer Agent | haiku | Blind cross-testing, test generation, coverage analysis, GRS validation | Self-assessment circularity (Mistake #47) | **6.5/10** | -0.5 — circularity was fundamental |
| Growth Agent | haiku | User acquisition, retention, monetization, viral mechanics, competitor tracking | NEW — unproven | **5.0/10** | **REPLACED SWE Agent** (Session 53) |

### Retired Agents
| Agent | Sessions Active | Total Findings | Accuracy | Reason for Retirement |
|-------|----------------|---------------|----------|----------------------|
| SWE Agent | 25-53 | 1 | 100% (1/1) | Redundant. Code review → Architecture. Edge cases → QA. 1 finding in 30 sessions. Replaced by Growth Agent. |

---

## New Hires (Session 57 — 2026-03-28)

Hired after full swarm vote (6 original + 3 new personas — Kamal, Aynur, Rauf).
Source: https://github.com/msitarzewski/agency-agents.git (full repo reviewed, not pre-selected).

| Agent Skill | File | Activate | Primary Role |
|-------------|------|----------|--------------|
| Sales Deal Strategist | `skills/sales-deal-strategist.md` | Now | B2B deal architecture, org pricing, MEDDPICC |
| Sales Discovery Coach | `skills/sales-discovery-coach.md` | Now | B2B discovery flows, org onboarding questions |
| LinkedIn Content Creator | `skills/linkedin-content-creator.md` | Sprint 3 | AURA score portability, professional brand |
| Cultural Intelligence Strategist | `skills/cultural-intelligence-strategist.md` | Sprint 3 | AZ/CIS cultural audit, invisible exclusion |
| Accessibility Auditor | `skills/accessibility-auditor.md` | Sprint 6 | WCAG 2.2 AA, radar chart fix, keyboard nav |
| Behavioral Nudge Engine | `skills/behavioral-nudge-engine.md` | Now (as DSP skill) | ADHD-first validation, cognitive load audit |

**Why these 6:** Original swarm was modeling a volunteer management platform. New personas (Kamal = senior professional, Aynur = talent acquisition, Rauf = ambitious mid-career) revealed: no B2B sales architecture, no professional brand portability, no cultural context for AZ market.

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
| Code review (business logic) | Architecture Agent |
| Verb regex / keyword calibration | QA Engineer |
| User acquisition strategy | Growth Agent |
| Retention / churn analysis | Growth Agent |
| Monetization / pricing | Growth Agent |
| Viral / referral mechanics | Growth Agent |
| Competitor tracking | Growth Agent |
| Content for CEO | Fact-Check Agent (agent-launch-template.md) |
| B2B org pricing / deal structure | `sales-deal-strategist` skill |
| Org onboarding flow / intro request design | `sales-discovery-coach` skill |
| B2B org dashboard feature design | `sales-deal-strategist` + `sales-discovery-coach` |
| AURA score sharing / LinkedIn portability | `linkedin-content-creator` skill |
| Any user-facing copy (AZ/CIS market) | `cultural-intelligence-strategist` skill |
| Professional profile features | `linkedin-content-creator` + `cultural-intelligence-strategist` |
| Onboarding / registration flow | `behavioral-nudge-engine` + `cultural-intelligence-strategist` |
| Assessment UX changes | `behavioral-nudge-engine` skill |
| Notification design / email templates | `behavioral-nudge-engine` skill |
| Empty state / error state copy | `behavioral-nudge-engine` + `cultural-intelligence-strategist` |
| Sprint 6+ — accessibility audit | `accessibility-auditor` skill |
| Custom interactive component (modals, forms) | `accessibility-auditor` skill (even pre-Sprint 6) |
| Any screen with >3 interactive decisions | `behavioral-nudge-engine` (cognitive load check) |
| SQL scripts / migrations | Architecture + Security |
| CEO evaluation / professional review | All agents in parallel |
| Route ordering review (/{id} patterns) | Security Agent (Session 42 P0: route shadowing IS real) |
| GDPR / account deletion endpoint | Security Agent (irreversible, cascade risk) |
| Bulk file upload endpoint (CSV, images) | Security Agent (formula injection, size limits, MIME validation) |
| Mobile layout / responsive fixes | Product Agent + load: accessibility-auditor skill |
| Custom hook authoring | load: REACT-HOOKS-PATTERNS.md (hooks-in-callbacks is Class 1 bug) |
| Any `useMutation` / `useQuery` hook | Architecture Agent (hook placement, token freshness, envelope) |
| Council accuracy tracking | Firuza (execution micro-decisions) + Nigar (B2B feature decisions) |
| Dashboard personalization | Product Agent + load: feed-curator skill |
| AI Twin feature review | Product + Security + load: ai-twin-responder skill |
| Assessment question creation | QA Engineer + Security + load: assessment-generator skill |
| User behavior analysis / retention | Product Agent + load: behavior-pattern-analyzer skill |
| AURA coaching feature | Product Agent + load: aura-coach + neuroscience-design skills |
| Content/post generation | Product Agent + load: content-formatter skill |
| Any "Life Simulator" proposal | REDIRECT → feed-curator skill (no separate app — Session 51) |
| Any "MindShift" proposal | REDIRECT → behavior-pattern-analyzer skill (no separate app — Session 51) |
| Any "BrandedBy standalone" proposal | REDIRECT → ai-twin-responder skill (no separate platform — Session 51) |
| Any "ZEUS engine" proposal | REDIRECT → assessment-generator skill (no separate API — Session 51) |

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
| **Firuza (council)** | 62-63, 69 | **4/4 correct (100%)** | Sprint A1: 404 handling (✓), A3: check-in visualization (✓), A4: one-shot disable (✓), A5: removal comment (✓). Domain: execution micro-decisions, UX precision, ADHD-first validation. **v2.0 (Session 69):** Upgraded to proactive scanning. Influence 1.0→1.1. Pre-sprint UX audit + cross-sprint pattern detection added. Path to Expert: maintain accuracy + constructive disagreement + expand scope. |
| **Nigar (council)** | 62-63 | **2/2 correct (100%)** | A2: category tabs (✓), A3: registration count header (✓). Domain: B2B feature decisions, org workflows. |
