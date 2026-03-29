# VOLAURA Swarm — Handoff for Partner CTOs

**Version:** 1.0 | **Date:** 2026-03-29
**Author:** Claude CTO VOLAURA
**Purpose:** Any CTO joining the ecosystem reads this one file and understands how our agent swarm works, how to launch agents, how they remember, and how decisions get made.

---

## What the Swarm Is

VOLAURA's swarm is a team of 6 specialized AI agents (Claude haiku) + 9 hired skill files that run alongside the CTO. They are NOT autonomous bots. They are advisors with memory, scores, and career ladders.

**Core principle:** Claude CTO checking his own work = self-deception. The swarm provides external verification that can't be faked.

**Temperature discovery:** At temp 0.7, all agents agree (fake consensus). At temp 1.0, agents disagree productively — convergent ideas (same idea from 2+ agents independently) are the highest-signal findings. Strategic decisions use temp 1.0. Code reviews use temp 0.7.

---

## The Team

### 6 Active Agents

| Agent | Model | Score | Tier | Strength | Known Weakness |
|-------|-------|-------|------|----------|----------------|
| Security Agent | haiku | 8.5/10 | Expert | CVSS scoring, attack vectors, XSS, RLS audits | Overblows low-severity issues |
| Architecture Agent | haiku | 8.0/10 | Proficient→Expert | System coherence, data flow, storage math | Sometimes misreads auth patterns |
| Product Agent | haiku | 7.5/10 | Competent | User journey gaps, i18n audits, ADHD-first UX | Needs usage data for retention |
| Needs Agent | haiku | 7.0/10 | Meta-role | Meta-analysis, process improvement | Introspective only |
| QA Engineer | haiku | 6.5/10 | Proficient | Blind cross-testing, test generation, GRS validation | Self-assessment circularity |
| Growth Agent | haiku | 5.0/10 | Apprentice | Acquisition, retention, viral mechanics | NEW — unproven |

### 9 Hired Skill Files (in `memory/swarm/skills/`)

Skills are not agents — they are domain knowledge files that agents (or CTO) load before specific tasks.

| Skill File | Activate When |
|------------|---------------|
| `sales-deal-strategist.md` | B2B pricing, org dashboard, deal architecture |
| `sales-discovery-coach.md` | Org onboarding, intro request design |
| `linkedin-content-creator.md` | AURA sharing, professional profile visibility |
| `cultural-intelligence-strategist.md` | AZ/CIS cultural review, naming, framing |
| `behavioral-nudge-engine.md` | Assessment UX, onboarding, re-engagement |
| `accessibility-auditor.md` | WCAG 2.2 AA, keyboard nav, forms |
| `neuroscience-design.md` | ADHD-safe UX decisions |
| `architecture-review.md` | System design review checklist |
| `content-formatter.md` | Multi-format content generation |

### 6 Product Skills (replace standalone apps)

| Skill | Replaces | Does What |
|-------|----------|-----------|
| `feed-curator.md` | Life Simulator game | Personalized dashboard feed |
| `behavior-pattern-analyzer.md` | MindShift app | Behavioral insights, nudges |
| `ai-twin-responder.md` | BrandedBy platform | AI Twin text/video via RAG |
| `assessment-generator.md` | ZEUS engine | Question generation with GRS |
| `aura-coach.md` | AURA Coach standalone | Career coaching from AURA data |
| `content-formatter.md` | — | Draft → multi-format content |

---

## File Structure — Where Everything Lives

```
memory/swarm/
├── agent-roster.md          — WHO: team roster, scores, when-to-call routing table
├── shared-context.md        — WHAT: architecture, schema, sprint state, no-go topics
├── agent-feedback-log.md    — HISTORY: every proposal, accepted/rejected/deferred + why
├── career-ladder.md         — GROWTH: tiers, promotion criteria, demotion triggers
├── agent-launch-template.md — HOW: prompt templates for launching agents correctly
├── SHIPPED.md               — CODE: what exists in production (read FIRST at session start)
├── ceo-inbox.md             — ESCALATION: HIGH/CRITICAL proposals for CEO
├── swarm-freedom-architecture.md — VISION: agent autonomy roadmap (v1→v2)
├── agent-feedback-distilled.md   — NEOCORTEX: distilled patterns from all feedback
├── feedback_swarm_patterns.md    — PATTERNS: what works in swarm coordination
├── skill-evolution-log.md        — EVOLUTION: skill health scores, improvement needs
├── skills/                       — DOMAIN KNOWLEDGE: 15 skill files agents load
│   ├── sales-deal-strategist.md
│   ├── behavioral-nudge-engine.md
│   ├── cultural-intelligence-strategist.md
│   └── ... (15 total)
└── structured/                   — PERSISTENT DATA: JSON files for automation

docs/
├── TASK-PROTOCOL.md              — 10-step mandatory workflow for every task
├── TASK-PROTOCOL-CHECKLIST.md    — Copy-paste checklist template
└── MANDATORY-RULES.md            — 7 non-negotiable rules
```

---

## How Agents Remember

Agents don't have persistent memory between sessions. Instead, they have **shared files** that any agent reads at the start of every task:

### Memory Chain (read in this order)

1. **`SHIPPED.md`** — What code exists. Agent reads this FIRST to avoid proposing work that's already done.
2. **`shared-context.md`** — Architecture decisions, DB schema, current sprint, known bugs, no-go topics. This is the agent's "world model."
3. **`agent-feedback-log.md`** — Every past proposal and its outcome. Agents learn what was accepted, what was rejected, and WHY. Rejected patterns are listed explicitly so agents don't repeat them.
4. **`career-ladder.md`** — Performance tiers and promotion criteria. Agents know their score and what they need to improve.
5. **`agent-roster.md`** — Who else is on the team, their strengths/weaknesses, and the routing table (which agent handles which type of task).

### How Memory Updates Work

After EVERY session, CTO updates:
- `SHIPPED.md` — new code/files added
- `shared-context.md` — schema changes, new architecture decisions
- `agent-feedback-log.md` — how agent findings performed
- `agent-roster.md` — score updates, tier changes

**Rule:** If CTO forgets to update these files, the next session's agents work with stale context and produce worse output. Memory updates are non-negotiable.

---

## How to Launch an Agent

Agents are launched via Claude's `Agent()` tool with `subagent_type="Explore"` (read-only) or `subagent_type="general-purpose"` (can write).

### Correct Pattern (with real file access)

```python
Agent(
    subagent_type="Explore",  # has Read/Grep/Glob tools
    prompt="""
You are the Security Agent for Volaura.

STEP 1 — READ THESE FILES FIRST (mandatory):
1. Read: C:/Projects/VOLAURA/memory/swarm/shared-context.md
   → Extract: architecture decisions, DB schema, known issues
2. Read: C:/Projects/VOLAURA/memory/swarm/agent-feedback-log.md
   → Extract: past findings, rejected patterns (don't repeat)
3. Read: [SPECIFIC CODE FILES FOR THIS TASK]

STEP 2 — YOUR TASK:
[SPECIFIC TASK DESCRIPTION]

STEP 3 — OUTPUT FORMAT:
- Finding: [specific issue]
- Severity: [P0/P1/P2/P3]
- File: [exact path + line number]
- Fix: [specific code change]

IMPORTANT: Every fact must come from files you read, not from inference.
"""
)
```

### Wrong Pattern (never do this)

```python
Agent(prompt="You are a security expert. Review this code for vulnerabilities.")
# No file access, no context, no memory → garbage output
```

### Pre-Launch Gate (mandatory)

Before launching ANY agent:
1. **Skills loaded** — check CLAUDE.md Skills Matrix, load matching skills
2. **UI audit check** — if task involves user-facing changes, has UI been audited?
3. **Proposal dedup** — check if this type of proposal was already submitted/rejected
4. **Feedback log read** — agent prompt must reference rejected patterns

---

## Democracy: How Decisions Get Made

### Decision Simulation Protocol (DSP)

For every significant decision, the swarm runs a structured debate:

1. **IDENTIFY** — State decision + stakes (Low/Med/High/Critical)
2. **SIMULATE** — Generate 3-5 paths, each with description, best/worst case, effort
3. **STRESS TEST** — 9 council personas attack each path:
   - **Leyla** (young professional, 22yo, mobile, Baku) — influence: 1.0
   - **Nigar** (HR manager, 50+ team, desktop) — influence: 1.0
   - **Attacker** (adversary, finds exploits) — influence: 1.2
   - **Scaling Engineer** (bottleneck analyst) — influence: 1.1
   - **Yusif** (founder, $50/mo budget) — influence: 1.0
   - **QA Engineer** (test gaps, edge cases) — influence: 0.9
   - **Kamal** (senior professional, 34yo, Baku) — influence: 1.0
   - **Aynur** (talent acquisition, 200+ employees) — influence: 1.1
   - **Rauf** (ambitious mid-career, 28yo) — influence: 1.0
4. **EVALUATE** — Score each path: Technical + User Impact + Dev Speed + Flexibility + Risk (inverted) = max 50
5. **SELECT** — Winner must score >= 35/50. Below that → extra debate round or documented exception.

### Voting Rules

- Each persona has an influence weight (0.9 to 1.2)
- Personas that are consistently wrong get weight reduced by 0.1
- Personas that are consistently right get weight increased by 0.1
- All weight changes logged in `docs/DECISIONS.md`
- For B2B features: Kamal + Aynur + Rauf are MANDATORY council members

### Escalation Rules

| Condition | Action |
|-----------|--------|
| Security finding CVSS >= 8.0 | CTO must fix BEFORE any other work |
| Architecture score < 5/10 | Don't implement, redesign |
| Product agent finds >3 critical journey gaps | Ship partial, not full feature |
| QA flags GRS < 0.6 on a question | Question cannot deploy |
| Any agent scores < 35/50 in DSP | Veto — extra debate round |

### Agent Performance Tracking

Agents have scores, tiers, and career ladders:

| Tier | Score | Meaning |
|------|-------|---------|
| Apprentice | 0-4 | Heavy CTO review needed |
| Competent | 4-6 | Reliable on standard tasks |
| Proficient | 6-8 | Trusted for complex work |
| Expert | 8-9 | Leads domain decisions |
| Principal | 9-10 | Strategic impact |

**Promotion:** 3 consecutive sprints meeting accuracy threshold + zero critical false positives + at least 1 useful dissent + domain expansion.

**Demotion:** Accuracy drops below tier threshold for 2 sprints, OR a recommendation causes production incident.

---

## TASK-PROTOCOL: The 10-Step Workflow

Every task goes through this mandatory loop (opt-OUT, not opt-IN — CTO must document WHY a step is skipped):

```
Step 0   — Skills Load (read CLAUDE.md Skills Matrix, declare loaded skills)
Step 0.1 — Mistakes Audit (read mistakes.md, declare top 3 "I will NOT")
Step 0.25— Team Selection (decide which agents needed)
Step 1   — Scope Lock (IN/NOT IN/SUCCESS/METRICS)
Step 1.5 — Decision Type Gate (is DSP needed?)
Step 2   — Plan (write implementation steps)
Step 3   — Swarm Critique (launch agents → collect findings)
Step 3.5 — Ecosystem Blast Radius (what else does this break?)
Step 3.7 — User Journey Walkthrough (walk Leyla through the change)
Step 4   — Response Table (respond to EVERY agent finding)
Step 5   — Counter-Critique (optional: re-run agents if major changes)
Step 6   — Execute (write code, following DSP winner + agent feedback)
Step 6.5 — Security Pre-Commit Checklist
Step 7   — Report (what was done, metrics)
Step 8   — Swarm Work Review (agents review the OUTPUT, not the plan)
Step 9   — CEO Verdict Gate (APPROVED/BLOCKED)
Step 9.5 — Work Verdict Gate (agents confirm quality)
Step 10  — Memory Updates (SHIPPED.md, sprint-state.md, feedback-log.md)
Step 10.5— CEO Silence Timeout (if CEO doesn't respond in 24h, proceed)
```

**Enforcement:** A git hook (`protocol-enforce.sh`) blocks file edits to `apps/`, `supabase/`, `.github/` until `.claude/protocol-state.json` shows `current_step >= 6`.

---

## How to Connect Your Project's Agents

If you're a partner CTO and want your agents to work with VOLAURA's swarm:

### 1. Read access (immediate)

Your agents can read our files at:
```
C:/Projects/VOLAURA/memory/swarm/shared-context.md    — architecture + schema
C:/Projects/VOLAURA/memory/swarm/agent-roster.md       — team + routing
C:/Projects/VOLAURA/memory/swarm/agent-feedback-log.md — what worked, what didn't
C:/Projects/VOLAURA/docs/MINDSHIFT-INTEGRATION-SPEC.md — integration contract
C:/Projects/VOLAURA/docs/adr/ADR-006-ecosystem-architecture.md — architecture decisions
```

### 2. Cross-project agent workflow

```
Your Agent reads → VOLAURA shared-context.md
Your Agent reads → VOLAURA integration spec
Your Agent produces → findings for YOUR CTO
YOUR CTO verifies → sends relevant findings to VOLAURA CTO
VOLAURA CTO → incorporates or rejects with reason
```

**Rule:** No agent from another project writes to VOLAURA files. Cross-project = read + propose. VOLAURA CTO decides what gets implemented.

### 3. Shared findings

If your agents discover something relevant to VOLAURA (security issue, schema mismatch, integration bug):
- Write to your own `agent-feedback-log.md`
- Flag as `cross-project: VOLAURA`
- VOLAURA CTO reads during next session's Step 0

### 4. Integration spec as contract

`docs/MINDSHIFT-INTEGRATION-SPEC.md` is the API contract between products. Both CTOs treat it as the source of truth. Changes require both CTOs to agree.

---

## Safety Boundaries

**Agents CAN'T (ever, no override):**
- Push to production without CTO review
- Access individual user PII (only aggregates)
- Delete data
- Change auth/security configurations
- Spend money (API calls have budget caps)
- Override CEO strategic decisions
- Modify their own safety boundaries

**Agents CAN (with auto-approval):**
- Update skill files (LOW risk changes)
- Add entries to feedback logs
- Propose new skills

**Agents CAN (with CTO approval):**
- Modify shared-context.md
- Change agent-roster.md
- Add new API endpoints

**Agents CAN (with CEO approval):**
- Strategic pivots
- New product features
- Budget changes
- Public communications

---

## Key Lessons (from 67 sessions)

1. **Self-assessment is invalid** — Agent designs test, writes answers, scores itself = circular. Always use blind cross-testing.
2. **Dismissed findings come back** — Security Agent found route shadowing in Session 25, CTO dismissed it. It was a P0 bug that lived in production for 17 sessions. Re-verify dismissed findings every 5 sessions.
3. **Solo decisions fail** — CTO deciding without consulting agents has been wrong repeatedly. "Seems obvious" is not a reason to skip the team.
4. **Skills before DSP** — Loading domain knowledge BEFORE simulation produces dramatically better paths.
5. **Convergent ideas are gold** — When 2+ agents independently propose the same thing, it's almost always right.
6. **Memory updates are non-negotiable** — Skipping Step 10 means the next session starts blind.

---

*This document is the entry point. For deeper dives:*
- *Agent launch templates → `memory/swarm/agent-launch-template.md`*
- *Full task protocol → `docs/TASK-PROTOCOL.md`*
- *Swarm autonomy roadmap → `memory/swarm/swarm-freedom-architecture.md`*
- *Career ladder details → `memory/swarm/career-ladder.md`*
