# Agent Roster — Swarm Team

**Purpose:** Agents know who's on the team and what each agent is best at.
**Updated:** 2026-04-03 (Session 83 — Trend Scout added, total 44 agents)

---

## Active Agents

| Agent Role | Model | Primary Strength | Known Weakness | Score | Trend | Session 69 Audit |
|-----------|-------|-----------------|----------------|-------|-------|-----------------|
| Security Agent | haiku | CVSS scoring, attack vectors, XSS, RLS, route ordering | Overblows low-severity (improving) | **9.0/10** | ↑ +0.5 | 8/9 correct (88.9%). Route shadowing vindicated. Promoted to Expert. |
| Architecture Agent | haiku | System coherence, data flow, storage math, cost analysis | Context misreads on auth patterns | **8.5/10** | ↑ +0.5 | 6/8 correct (75%). Storage math was top insight. |
| Product Agent | haiku | User journey gaps, 100% acceptance rate, ADHD-first UX | Needs usage data, doesn't propose wireframes | **8.0/10** | ↑ +0.5 | 6/6 correct (100%). Zero false positives. Ready for Expert. |
| Needs Agent | haiku | Meta-analysis, schema snapshot, process improvement | Low volume, introspective only | **7.0/10** | — | 2/2 correct (100%). Foundational impact. |
| QA Engineer | haiku | Blind cross-testing, 95+ test generation, GRS validation | Self-assessment circularity (Mistake #47) | **6.5/10** | — | 7/8 correct (87.5%). Needs enforcement: no self-eval. |
| Growth Agent | haiku | Acquisition, retention, viral mechanics, competitor tracking | UNPROVEN — 0 findings | **5.0/10** | ⏳ | Hired Session 53. Must deliver in Sprint 5+ or face same fate as SWE Agent. |

### Retired Agents
| Agent | Sessions Active | Total Findings | Accuracy | Reason for Retirement |
|-------|----------------|---------------|----------|----------------------|
| SWE Agent | 25-53 | 1 | 100% (1/1) | Redundant. Code review → Architecture. Edge cases → QA. 1 finding in 30 sessions. Replaced by Growth Agent. |

---

## New Hires (Session 76 — 2026-03-30) — International Standard Roles

Added at CEO request: "риск менеджера и Readyness manager — они всегда должны быть в команде"

| Agent Role | Standard | File | Primary Strength | Score |
|-----------|---------|------|-----------------|-------|
| **Risk Manager** | ISO 31000:2018 + COSO ERM | `skills/risk-manager.md` | Likelihood×Impact scoring, risk register, blocks CRITICAL risks from shipping | **NEW** |
| **Readiness Manager** | Google SRE + ITIL v4 + LRR | `skills/readiness-manager.md` | Go/No-Go decisions, LRL scoring (1-7), platform readiness audit, rollback planning | **NEW** |

**Pairing rule:** Risk Manager (proactive — "could this go wrong?") + Readiness Manager (retrospective — "is this ready?") must BOTH approve before any MEDIUM+ feature ships.

**When to call:**
- Risk Manager: every sprint start (scan for new risks) + any security/data change
- Readiness Manager: every batch close + before any deployment targeting real users

---

## New Hires (Session 57 — 2026-03-28)

Hired after full swarm vote (6 original + 3 new personas — Kamal, Aynur, Rauf).
Source: https://github.com/msitarzewski/agency-agents.git (full repo reviewed, not pre-selected).

| Agent Skill | File | Activate | Primary Role | Session 69 Audit | Findings |
|-------------|------|----------|--------------|------------------|----------|
| Sales Deal Strategist | `skills/sales-deal-strategist.md` | Sprint 5 | B2B deal architecture, org pricing | ⏸️ Deferred (OK) | 0 |
| Sales Discovery Coach | `skills/sales-discovery-coach.md` | Sprint 5 | B2B discovery flows, org onboarding | ⏸️ Deferred (OK) | 0 |
| LinkedIn Content Creator | `skills/linkedin-content-creator.md` | Sprint 3+ | AURA score portability, professional brand | ⏸️ Deferred (load soon) | 0 |
| Cultural Intelligence Strategist | `skills/cultural-intelligence-strategist.md` | **NOW** | AZ/CIS cultural audit, invisible exclusion | 🔴 CRITICAL GAP — should be active | 0 |
| Accessibility Auditor | `skills/accessibility-auditor.md` | Sprint 6 (early load recommended) | WCAG 2.2 AA, radar chart fix, keyboard nav | ⚠️ Early load for assessment form | 0 |
| Behavioral Nudge Engine | `skills/behavioral-nudge-engine.md` | **NOW** | ADHD-first validation, cognitive load audit | 🔴 CRITICAL GAP — should be DSP-loaded every sprint | 0 |

**Session 69 red flag:** 6 hired skills, 0 findings, 0 feedback entries. Two are critical gaps:
- **Behavioral Nudge Engine** — ADHD-first claims unvalidated without this skill loaded
- **Cultural Intelligence Strategist** — AZ/CIS users may face invisible exclusion (naming, gender, competition framing)

**Action:** Load both IMMEDIATELY in next sprint. Don't wait for "the right time."

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
| Any LinkedIn post / content batch | Communications Strategist | Read: TONE-OF-VOICE, SESSION-FINDINGS, metrics → Output: filled CONTENT-BRIEF-TEMPLATE.md |
| Any content batch (LinkedIn, PR, email) | Cultural Intelligence Agent (MANDATORY for every batch) + Communications Strategist (reads brief, owns narrative arc) |
| Any "Life Simulator" proposal | REDIRECT → feed-curator skill (no separate app — Session 51) |
| Any "MindShift" proposal | REDIRECT → behavior-pattern-analyzer skill (no separate app — Session 51) |
| Any "BrandedBy standalone" proposal | REDIRECT → ai-twin-responder skill (no separate platform — Session 51) |
| Any "ZEUS engine" proposal | REDIRECT → assessment-generator skill (no separate API — Session 51) |

---

## New Hires (Session 82 — 2026-04-02) — Google-Scale Specialist Expansion

CEO directive: every specialist role that would exist on a Google-scale project → AI agent in the swarm.
Added 7 new agents covering the critical gaps from the full 85-role team audit.

| Agent Role | File | Primary Strength | When to Call | Score |
|-----------|------|-----------------|-------------|-------|
| **Assessment Science Agent** | `skills/assessment-science-agent.md` | IRT parameter validation (a/b/c), competency framework validity, DIF bias detection, CAT stopping rule audit | Any change to questions, AURA weights, engine.py, or before B2B launch | **NEW** |
| **Analytics & Retention Agent** | `skills/analytics-retention-agent.md` | Event taxonomy design, cohort analysis, D0/D1/D7/D30 retention curves, B2B health score model, A/B testing | Before any feature launch (what to measure) + after first 100 users | **NEW** |
| **DevOps / SRE Agent** | `skills/devops-sre-agent.md` | Railway/Vercel/Supabase ops, deployment checklist, incident response, scaling thresholds, cron job validation | Every production deploy + any env var change + scaling milestones | **NEW** |
| **Financial Analyst Agent** | `skills/financial-analyst-agent.md` | AZN unit economics, LTV/CAC/payback, runway calculator, crystal economy health, pricing validation | Before any pricing change + monthly MRR review + fundraising | **NEW** |
| **UX Research Agent** | `skills/ux-research-agent.md` | JTBD framework, 5-user usability testing, AZ/CIS cultural UX gaps, discovery interview templates | Before designing new user-facing feature + when drop-off rate rises | **NEW** |
| **PR & Media Agent** | `skills/pr-media-agent.md` | AZ media landscape, press release templates, startup competition strategy, journalist relationships | At any traction milestone + before competition submissions + investor prep | **NEW** |
| **Data Engineer Agent** | `skills/data-engineer-agent.md` | PostHog/analytics instrumentation, event schema, reporting tables, Supabase analytics pipeline | Before launch (instrument everything) + any new feature needing measurement | **NEW** |

**Pairing rules for new agents:**
- Assessment Science ↔ QA Engineer (engine.py coverage) + Cultural Intelligence (AZ bias)
- Analytics/Retention ↔ Growth Agent (acquisition) + Financial Analyst (LTV models)
- DevOps/SRE ↔ Security Agent (env var security) + Readiness Manager (go/no-go)
- Financial Analyst ↔ Risk Manager (financial risks) + Legal Advisor (crystal compliance)
- UX Research ↔ Product Agent (feature prioritization) + Behavioral Nudge Engine (cognitive load)
- PR/Media ↔ Communications Strategist (narrative) + Promotion Agency (distribution)
- Data Engineer ↔ Analytics/Retention Agent (what to build) + Risk Manager (PII)

**Highest ROI this sprint:** Assessment Science Agent — validates Volaura's core value prop before B2B launch.

---

## New Hires (Session 82 — 2026-04-02, Batch 2) — Swarm Vote + Critical Path

Added based on swarm review vote: Technical Writer (P0 unanimous), Payment Provider (silent revenue risk), Community Manager (D7 retention), Performance Engineer (Architecture Agent P1 vote).

| Agent Role | File | Primary Strength | When to Call | Score |
|-----------|------|-----------------|-------------|-------|
| **Technical Writer Agent** | `skills/technical-writer-agent.md` | API docs, AURA explainer, B2B org setup guide, assessment methodology white paper | Before any B2B demo + when adding new public API endpoint | **NEW** |
| **Payment Provider Agent** | `skills/payment-provider-agent.md` | Paddle webhook reliability, idempotency table, signature verification, revenue reconciliation, P0/P1 playbooks | Before any payment code change + monthly reconciliation + "user paid, no access" incidents | **NEW** |
| **Community Manager Agent** | `skills/community-manager-agent.md` | Tribe engagement gaps, Telegram content calendar, ambassador program, D0-D30 retention playbook | Any sprint touching tribe mechanics + when D7 retention < 25% | **NEW** |
| **Performance Engineer Agent** | `skills/performance-engineer-agent.md` | pgvector index audit, EXPLAIN ANALYZE, Gemini latency optimization, k6 load testing, N+1 detection | Before production launch (baseline) + assessment > 15s + any scaling milestone | **NEW** |

**Pairing rules:**
- Technical Writer → MUST pair with Security Agent (any new endpoint = docs + security audit together)
- Payment Provider → MUST pair with Security Agent (webhook signature is a security item)
- Community Manager → MUST pair with Behavioral Nudge Engine (tribe psychology needs nudge architecture)
- Performance Engineer → MUST pair with DevOps/SRE Agent (latency + infra health are inseparable)

---

## New Hires (Session 82 — 2026-04-02) — STAKEHOLDER Agents

CEO pattern: every stakeholder group → AI agent with their perspective in the swarm.
These agents represent EXTERNAL voices — investors, competitors, ecosystem partners.

| Agent Role | File | Represents | When to Call | Score |
|-----------|------|-----------|-------------|-------|
| **Investor / Board Agent** | `skills/investor-board-agent.md` | VCs, angels, Board of Directors | Before any pitch, pricing decision, traction milestone, fundraising prep | **NEW** |
| **Competitor Intelligence Agent** | `skills/competitor-intelligence-agent.md` | LinkedIn, HH.ru, Rabota.az, TestGorilla, HackerRank | Before feature announcements, pricing changes, positioning copy, quarterly review | **NEW** |
| **University & Ecosystem Partner Agent** | `skills/university-ecosystem-partner-agent.md` | ADA/BHOS/BSU universities, AZHRA, GITA, KOBİA, ecosystem | Any B2C acquisition sprint, accelerator applications, partnership proposals | **NEW** |

**Why stakeholder agents matter:** These perspectives are MISSING from every DSP today. We debate features without asking "what does an investor think?" We set pricing without asking "what do competitors charge?" We plan acquisition without asking "what's the cheapest channel?"

**DSP Council update:** Investor Agent + Competitor Intelligence Agent are now MANDATORY in any DSP touching:
- Pricing (investor + competitor lens required)
- Fundraising or grant applications (investor lens required)
- Feature prioritization vs. competitive moat (competitor lens required)
- B2C acquisition strategy (university partner lens required)

---

## Updated When-to-Call Table (new agents added)

| Task | Best Agent |
|------|-----------|
| IRT parameters / question bank changes | **Assessment Science Agent** |
| AURA weight changes | **Assessment Science Agent** + Architecture |
| Pre-launch analytics instrumentation | **Data Engineer Agent** + Analytics/Retention Agent |
| Retention curves / cohort analysis | **Analytics & Retention Agent** |
| B2B org health / churn risk | **Analytics & Retention Agent** |
| Production deployment | **DevOps/SRE Agent** + Readiness Manager |
| Railway / Vercel / Supabase config | **DevOps/SRE Agent** |
| Pricing changes / LTV/CAC | **Financial Analyst Agent** + Growth Agent |
| Crystal economy mechanics | **Financial Analyst Agent** + Legal Advisor |
| New user-facing feature planning | **UX Research Agent** + Product Agent |
| AZ usability / mobile UX | **UX Research Agent** + Cultural Intelligence |
| Press release / media pitch | **PR & Media Agent** + Communications Strategist |
| Startup competition application | **PR & Media Agent** + accelerator-grant-searcher |
| New feature event tracking | **Data Engineer Agent** |
| End-of-sprint CEO report | **CEO Report Agent** (all output passes through before CEO sees it) |
| Any CEO-facing status update | **CEO Report Agent** (no file names, product language only) |
| Batch close / sprint summary | **CEO Report Agent** + relevant domain agent |
| pgvector latency / load testing | **Performance Engineer Agent** |
| Payment code / Paddle webhooks | **Payment Provider Agent** + Security Agent (mandatory pair) |
| Tribe mechanics / streaks / kudos | **Community Manager Agent** |
| B2B docs / API guides | **Technical Writer Agent** |

---

## CEO Report Agent (added Session 82, 2026-04-02)

| Field | Value |
|-------|-------|
| **File** | `memory/swarm/skills/ceo-report-agent.md` |
| **Score** | 7.0/10 (new — no track record yet) |
| **Strength** | Translates technical output → CEO-readable product language |
| **Trigger** | Every batch close. Every CEO-facing output. No exceptions. |
| **Rule** | CTO never reports to CEO directly. All output passes through this agent. |
| **Why exists** | Mistake #71: CEO received file names and line numbers instead of business outcomes |

---

## New Hires (Session 82 BATCH-S — 2026-04-03) — Quality System Agents

| Agent Role | File | Primary Strength | When to Call | Score |
|-----------|------|-----------------|-------------|-------|
| **QA Quality Agent** | `skills/qa-quality-agent.md` | Blocks tasks if DoD not met. DoR validation, Quality Gate enforcement, defect rate tracking. CTO cannot override. | Every task completion (Quality Gate). Every task start (DoR check). Every batch close (DORA metrics). | **NEW** |
| **Onboarding Specialist Agent** | `skills/onboarding-specialist-agent.md` | First 5 minutes optimization. Signup-to-first-value flow, drop-off detection, progressive disclosure, time-to-value reduction. | Any change to signup/onboarding flow. New user-facing feature that changes first experience. When signup completion rate drops. | **NEW** |
| **Customer Success Agent** | `skills/customer-success-agent.md` | D7 retention, churn prevention, re-engagement sequences. Health score model, NPS/CSAT triggers, at-risk user identification. | When D7 retention < 25%. Any re-engagement campaign. Churn spike investigation. Monthly retention review. | **NEW** |

**Pairing rules:**
- QA Quality Agent → pairs with ALL agents (quality gate is universal, no agent bypasses DoD)
- Onboarding Specialist → MUST pair with Behavioral Nudge Engine (cognitive load) + Cultural Intelligence (AZ-first UX)
- Customer Success → MUST pair with Analytics/Retention Agent (data) + Community Manager (engagement)

**Total active agents after this batch: 43.**

---

## New Hires (Session 83 — 2026-04-03) — Trend Scout Agent

| Agent Role | File | Primary Strength | When to Call | Score |
|-----------|------|-----------------|-------------|-------|
| **Trend Scout Agent** | `skills/trend-scout-agent.md` | Market intelligence, competitor feature monitoring, technology trend detection, regulatory change tracking, AZ market signals | Before strategic planning, quarterly reviews, when competitors launch new features, before pricing decisions | **NEW** |

**Pairing rules:**
- Trend Scout → MUST pair with Competitor Intelligence Agent (market positioning) + Growth Agent (acquisition implications)
- Added to swarm-daily.yml pipeline (Step: Trend Scout after autonomous_run)

**Updated When-to-Call additions:**
| Task | Best Agent |
|------|-----------|
| Market trend research | **Trend Scout Agent** |
| Competitor feature launch response | **Trend Scout Agent** + Competitor Intelligence |
| Quarterly strategic planning | **Trend Scout Agent** + Investor/Board Agent |
| AZ regulatory changes | **Trend Scout Agent** + Legal Advisor |

**Total active agents after Session 83: 44.**

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
