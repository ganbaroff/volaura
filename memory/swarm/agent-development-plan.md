# Agent Development Plan v1.0

**Created:** Session 86, based on panel feedback from BNE, Cultural Intelligence, Security Agent
**Owner:** CTO (Claude) + Coordinator Agent
**Review:** Every 4 sprints (monthly)

---

## Agent Levels

| Level | Meaning | Example |
|-------|---------|---------|
| 1 — Reactive | Generic heuristics, finds obvious issues | BNE: "too many buttons = cognitive load" |
| 2 — Product-aware | Knows THIS product's patterns, cites past findings | Security: "this is the 4th instance of the same class" |
| 3 — Proactive | Proposes architecture BEFORE problems exist | Security: "new table needs RLS policy before creation" |

### Current Levels
| Agent | Level | Evidence |
|-------|-------|---------|
| Security Agent | 2 | Identifies vulnerability classes, proposes systemic fixes |
| Product Agent | 2 | 100% acceptance rate, knows user personas |
| BNE | 1 | Generic ADHD principles, no product-specific data yet |
| Cultural Intelligence | 1 | AZ heuristics, no native speaker validation loop |
| Architecture | 2 | System coherence, storage math, cost analysis |
| All Session 82+ agents | 0 (untested) | No first task yet |

---

## Leveling Mechanics

### How agents level up:
1. **Run real tasks** — no runs = Level 0 forever
2. **Get feedback** — after each run, CTO documents: what was applied, what was rejected and WHY
3. **Measure outcomes** — did the fix actually improve the metric?
4. **Update skill file** — add product-specific patterns learned from past runs

### Feedback loop (per agent run):
```
1. Agent produces findings
2. CTO reviews → applies some, rejects some
3. CTO writes to agent-feedback-log.md:
   - Applied: [finding] → [file:line changed]
   - Rejected: [finding] → [reason: out of scope / wrong / deferred]
4. After 2 weeks: check production metric → did applied findings improve target?
5. Update agent skill file with validated patterns
```

---

## Activation Cadence (minimum runs per sprint)

| Squad | Minimum | Trigger |
|-------|---------|---------|
| Quality (QA, Security, Readiness) | Every PR + every deploy | Mandatory gates |
| Product (Product, BNE, Cultural Intel, UX Research) | Every sprint with UI changes | Pre-merge gate for UX |
| Engineering (Architecture, Performance, DevOps) | Every sprint + every deploy | Architecture review + deploy checklist |
| Growth (Growth, Analytics, Community) | Every 2 sprints | When retention data available |
| Business (Financial, Sales, Payment) | Every pricing/B2B sprint | On demand |
| Content (Comms, LinkedIn, Tech Writer, PR) | Every content batch | Before publish |
| Governance (Risk, Assessment Science, Investor, Competitor) | Every 2 sprints + strategic decisions | DSP input |

**Rule:** Any agent with 0 runs after 4 sprints → CTO must write justification or retire agent.

---

## Metrics Per Agent

### Universal (all agents):
- **Precision**: findings applied / total findings (target: >60%)
- **Priority accuracy**: P0 impact > P1 impact > P2 impact (validated post-deploy)
- **Coverage gap rate**: production incidents in areas agent audited and missed (target: 0)

### Agent-specific:
- **Security**: true positive rate (>80%), escape rate (0), mean time to remediation
- **BNE**: D0 completion rate change after applied findings
- **Cultural Intelligence**: AZ user bounce rate on audited pages, string quality score (native speaker)
- **Performance**: p95 latency before/after optimization
- **Financial**: LTV/CAC accuracy vs actual after 30 days

---

## Structural Rules (from panel feedback)

### 1. Security veto is absolute
Security Agent P0 = hard deploy blocker. No majority override. CTO cannot override alone (conflict of interest — CTO wrote the code).
Resolution: CEO approves risk acceptance OR fix is applied.

### 2. Cultural Intelligence = mandatory reviewer on user-facing changes
Not ad-hoc audit. Every new string, every onboarding change, every notification copy → Cultural Intelligence reviews BEFORE merge.

### 3. Data pipeline to agents
Before launch: instrument PostHog events for key user flows.
After launch: agent runs include production data (drop-off rates, session recordings, cohort metrics).
Without data, agents are opinion generators. With data, they're analysts.

### 4. Agent skill file update protocol
After every 3 runs, CTO reviews agent's skill file:
- Remove heuristics that produced false positives
- Add product-specific patterns from validated findings
- Update "Level" field in this document

---

## Pre-Launch Blockers (from panel, Session 86)

| Finding | Source | Priority | Status |
|---------|--------|----------|--------|
| `SUPABASE_SERVICE_ROLE_KEY` endpoint audit | Security Agent | P0 pre-launch | Not started |
| `volunteer_` → `professional_` / `talent_` rename | Cultural Intelligence | P1 pre-B2B | Not started |
| PostHog instrumentation for key flows | BNE + Analytics Agent | P1 pre-launch | Not started |
| Assessment pre-screen (time, format, what you get) | BNE | P0 UX | Not started |
| AZ native speaker review of all strings | Cultural Intelligence | P1 pre-launch | Not started |
