# TASK PROTOCOL v4.0 — Swarm-First Batch Execution

**Version:** 4.0 | **Updated:** 2026-03-29
**Previous:** v3.0 (Swarm Critique Loop — CTO proposes, team critiques)
**Change:** Team proposes, team debates, best wins. CTO is one voice, not THE voice. Parallel batches, not sequential sprints.

**Why v4.0 exists:** CEO feedback — "CTO proposes and team just attacks. That's wrong. Team should propose radically different paths. You can do 12-20 things at once. Fix basics first. I'm tired of technical details — decide yourselves."

---

## How It Works (30-second summary)

```
1. TEAM PROPOSES     → Each agent reads codebase + memory → proposes tasks independently
2. BATCH ASSEMBLES   → All proposals triaged → 12-20 tasks batched by size
3. TEAM DEBATES      → Agents argue priorities. 3+ votes override CTO.
4. PARALLEL EXECUTE  → Tasks run simultaneously. Agents own their domain.
5. BATCH CLOSES      → One report to CEO. Memory updated.
```

**Core principle:** Protocol is OPT-OUT, not OPT-IN. Skipping a step requires documenting WHY.

---

## Required Reads (before every batch)

| File | What it tells you | When |
|------|-------------------|------|
| [`memory/swarm/SHIPPED.md`](../memory/swarm/SHIPPED.md) | What code exists (prevents rebuilding) | Batch start |
| [`memory/context/mistakes.md`](../memory/context/mistakes.md) | CLASS 1-8 recurring errors | Batch start |
| [`memory/context/patterns.md`](../memory/context/patterns.md) | What works, silent contracts | Batch start |
| [`memory/swarm/agent-roster.md`](../memory/swarm/agent-roster.md) | Team capabilities, routing table | Batch start |
| [`memory/context/sprint-state.md`](../memory/context/sprint-state.md) | Current position | Batch start |
| [`memory/swarm/shared-context.md`](../memory/swarm/shared-context.md) | Architecture decisions, schema, known bugs | During planning |
| [`CLAUDE.md`](../CLAUDE.md) | Skills Matrix, NEVER/ALWAYS rules | During execution |
| [`memory/swarm/agent-feedback-log.md`](../memory/swarm/agent-feedback-log.md) | Past proposals: accepted/rejected/why | During proposals |

---

## PHASE 1: TEAM PROPOSES (replaces "CTO defines sprint")

### Step 1.0 — Agent Proposal Round

Each agent independently reads the codebase and memory files, then proposes what to work on.

**Each agent writes:**
```
PROPOSAL: [task name]
CLASS: MICRO (≤10 lines) | SMALL (10-50) | MEDIUM (50-200) | LARGE (200+)
WHY NOW: [1 sentence — what breaks/stalls if we don't do this]
FILES: [specific paths this touches]
BLOCKS: [what this unblocks downstream]
```

**Rules:**
- CTO proposes too — but as ONE voice among 6, not the decider
- Agents read `agent-feedback-log.md` to avoid re-proposing rejected ideas
- Agents read `SHIPPED.md` to avoid proposing work that's done
- Each agent can propose 1-3 tasks
- Proposals can be ANY size — a 5-line copy fix alongside architecture work

### Step 1.1 — Proposal Triage

Needs Agent collects all proposals and orders by:
1. **P0 blockers** — things that make the product broken for users RIGHT NOW
2. **High leverage** — things that unblock the most downstream work
3. **Polish** — things that improve but don't unblock
4. **Deferred** — nice-to-have, not now

No proposal is rejected at this stage. All get classified.

### Step 1.2 — Priority Debate

**All agents see all proposals.** Any agent can:
- **Support** another agent's proposal: "+1, because [reason]"
- **Challenge**: "This is lower priority than [X] because [reason]"
- **Merge**: "Proposals A and B should be one task because [shared files]"

**Vote rule:** If 3+ agents agree on priority order, it stands. CTO cannot override. CTO can argue but needs 3+ agents to agree with the counter-argument.

**Output:** Ordered task list with assignments.

---

## PHASE 2: BATCH ASSEMBLY

### Step 2.0 — Batch Lock

```
BATCH: [date-based ID, e.g., 2026-03-30-A]
TASKS: [count, typically 12-20]
PARALLEL STREAMS:
  UI/UX:        [tasks] → [agent]
  Backend/API:  [tasks] → [agent]
  Database:     [tasks] → [agent]
  Integration:  [tasks] → [agent]
  Fixes/Polish: [tasks] → [agent]
DEPENDENCIES: [task X blocks task Y — list all hard deps]
```

### Step 2.1 — Task Self-Classification

Each task declares its weight. Protocol gates scale automatically:

| Class | Lines | Gate Level | What's required |
|-------|-------|------------|-----------------|
| **MICRO** | ≤10 | Minimal | Step 1 proposal + execute + verify. No critique round. |
| **SMALL** | 10-50 | Light | + 1 peer review before merge |
| **MEDIUM** | 50-200 | Standard | + Security checklist + 1 critique round |
| **LARGE** | 200+ | Full | + Blast radius check + 2 critique rounds + user journey walkthrough |

**CTO can bump a task ±1 level with written reason.** Any agent can contest the bump.

### Step 2.2 — Domain Ownership

Agents own domains, not individual tasks. An agent handles ALL tasks in their domain:

| Domain | Primary Owner | Cross-Review By |
|--------|--------------|-----------------|
| Assessment pipeline | QA Engineer | Security |
| Org/B2B features | Sales Strategist | Product |
| User profiles + UX | Product Agent | Accessibility |
| Scoring + data model | Architecture Agent | Security |
| Events + growth | Growth Agent | Product |
| Notifications + infra | Architecture Agent | Security |

**Merge conflict prevention:** Each domain maps to specific directories. Agents don't touch files outside their domain without announcing it.

---

## PHASE 3: EXECUTION (parallel)

### Step 3.0 — Skills + Mistakes Declaration (per task, 2 min)

Before writing any code:
```
Skills loaded: [from CLAUDE.md Skills Matrix]
This task I will NOT: [top 2 mistakes from mistakes.md relevant to THIS task]
```

### Step 3.1 — Security Pre-Check (MEDIUM + LARGE only)

```
□ Rate limiting on new endpoints?
□ RLS policies on new tables?
□ Pydantic validation on inputs?
□ Auth + ownership checks?
□ No sensitive data in logs?
□ Parameterized SQL?
```

### Step 3.2 — Execute

- Follow the proposal scope. Don't expand.
- Checkpoint commits at natural breakpoints: `git commit -m "[TASK-ID] description"`
- If blocked: announce blocker, continue unblocked parts. Don't wait.
- If deviating from plan: log reason BEFORE deviating.

### Step 3.3 — Peer Review (SMALL+ tasks)

Agent who didn't write the code reviews it. Looks for:
- Schema mismatches (CLASS 4 mistake)
- Security gaps
- Missing i18n
- NEVER/ALWAYS rule violations

Verdict: **APPROVED** / **APPROVED WITH NOTES** / **BLOCKED**

If BLOCKED → fix → re-review. Not restart.

---

## PHASE 4: BATCH CLOSE

### Step 4.0 — Documentation Gate

Every task produces AT LEAST ONE update to:

| If you changed... | Update... |
|-------------------|-----------|
| API endpoint / DB schema | `memory/swarm/SHIPPED.md` + `shared-context.md` |
| User-facing flow | `memory/context/sprint-state.md` |
| Architecture decision | `docs/DECISIONS.md` |
| Found new mistake pattern | `memory/context/mistakes.md` |
| Found working pattern | `memory/context/patterns.md` |

### Step 4.1 — Batch Report to CEO

One report for the entire batch, not per-task:

```
BATCH: [ID]
COMPLETED: [count] tasks — [1-line each]
DEFERRED: [count] — [why each]
DISCOVERED: [gaps found during execution]
BUSINESS IMPACT: [what users can now do that they couldn't before]
QUESTION: [one question if needed, or NONE]
```

CEO responds: **APPROVE / CHANGE / DEFER**

### Step 4.2 — Retrospective (Needs Agent writes)

```
BATCH: [ID]
What went smooth: [list]
What was friction: [list]
Protocol step that helped most: [which step caught biggest issue]
Protocol step that was overkill: [which step to simplify next time]
New mistakes: [add to mistakes.md if any]
New patterns: [add to patterns.md if any]
```

---

## AGENT OVERRIDE RULES

| Situation | Rule |
|-----------|------|
| CTO rejects a proposal | Proposing agent + 2 others can override (3-agent vote) |
| Critique finds issue but 2+ agents disagree | Agent proceeds, logged in protocol-state.json |
| CTO wants to add scope mid-batch | Needs 3+ agent agreement, or it goes to next batch |
| P0 production bug | CTO can invoke HOTFIX mode (skip critique, keep security check) |
| 2-1 split on any decision | Force debate, then escalate to CEO if no consensus |

**CTO never has unilateral tiebreaker.** Force consensus or escalate.

---

## TASK SIZE EXAMPLES (calibration)

| Example | Class | Why |
|---------|-------|-----|
| Fix i18n string "volunteer" → "professional" | MICRO | 1 line, 1 file |
| Add rate limiter to endpoint | MICRO | 1 decorator |
| Hide org-only nav from professionals | SMALL | Conditional render in sidebar.tsx |
| Add email notification settings | MEDIUM | New settings page + API endpoint |
| Org search service + UI | LARGE | Service + router + tests + React page |
| DB migration volunteer_id → user_id | LARGE | Touches every table, needs deprecation |

---

## FAILURE MODES TO WATCH

| Pattern | CLASS | Detection |
|---------|-------|-----------|
| CTO decides alone without team | CLASS 3 | No "Team:" declaration in proposal |
| "Done" without verification | CLASS 1 | No curl/test evidence in report |
| Memory not updated after batch | CLASS 2 | SHIPPED.md stale after session |
| Assumed field names | CLASS 4 | No schema read before coding |
| Invented metrics | CLASS 5 | No source file for claimed number |
| Built features when basics broken | CEO feedback | P0 issues exist but team builds P3 features |

---

## PROTOCOL EVOLUTION

This document improves every batch. Needs Agent proposes changes in Step 4.2 retrospective. Team votes. Changes logged here:

| Version | Date | Change | Trigger |
|---------|------|--------|---------|
| v1.0 | 2026-03-28 | Initial: skills → plan → critique → execute | Session 59 |
| v2.0 | 2026-03-28 | Added checklist + enforcement hook | Session 59 |
| v3.0 | 2026-03-29 | +Mistakes audit, +team selection, +blast radius, +CEO gate | 5 agent proposals |
| **v4.0** | **2026-03-29** | **Team-first proposals, parallel batches, agent override, proportional gates** | **CEO directive: "Team decides, not CTO alone"** |

---

## LINKED FILES

| Purpose | File |
|---------|------|
| Batch task tracking | `docs/BATCH-TASKS.md` (created per batch) |
| Enforcement state | `.claude/protocol-state.json` |
| Checklist template | `docs/TASK-PROTOCOL-CHECKLIST.md` |
| Agent capabilities | `memory/swarm/agent-roster.md` |
| What exists | `memory/swarm/SHIPPED.md` |
| Architecture decisions | `memory/swarm/shared-context.md` |
| Past proposals | `memory/swarm/agent-feedback-log.md` |
| Recurring mistakes | `memory/context/mistakes.md` |
| Working patterns | `memory/context/patterns.md` |
| Sprint position | `memory/context/sprint-state.md` |
| Skills reference | `CLAUDE.md` → Skills Matrix |
