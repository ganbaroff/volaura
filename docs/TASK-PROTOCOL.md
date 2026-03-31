# TASK PROTOCOL v5.3 — Swarm-First Batch Execution

**Version:** 5.3 | **Updated:** 2026-03-30
**Previous:** v5.2 (Risk Manager + Readiness Manager integrated throughout)
**Change:** Agent Briefing Requirements — every agent launch MUST include the VOLAURA CONTEXT BLOCK. Agents launched without project context = CLASS 3 mistake. Full template: `docs/AGENT-BRIEFING-TEMPLATE.md`.

**Why v5.0 exists:** Session 73 — All 6 agents proposed improvements after CEO directive "fix routing, rules, speed, efficiency." Proposals reviewed, voted, and implemented in one batch.

---

## How It Works (30-second summary)

```
0. FLOW DETECTION  → CTO reads CEO signal → declares which flow: Team Proposes / CTO Plan / HOTFIX
1. TEAM PROPOSES   → All agents read SIMULTANEOUSLY (15 min) → propose in parallel (10 min)
2. BATCH ASSEMBLES → Proposals triaged → 12-20 tasks batched by size + effort
3. TEAM DEBATES    → Agents argue priorities. 3+ votes override CTO.
4. PARALLEL EXECUTE → Tasks run simultaneously. Agents own their domain.
5. BATCH CLOSES   → One report to CEO. "What's next" declared. Memory updated.
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
| [`memory/swarm/skills/risk-manager.md`](../memory/swarm/skills/risk-manager.md) | Active risk register — what CRITICAL/HIGH risks are open | Batch start (always) |
| [`memory/swarm/skills/readiness-manager.md`](../memory/swarm/skills/readiness-manager.md) | Platform LRL score — what's blocking next launch readiness level | Batch start (always) |

---

## STEP 0.5 — FLOW TYPE SIGNAL DETECTION (NEW — Security P0)

**Before any phase starts, CTO declares:**

```
FLOW DETECTION:
  CEO signal (verbatim): "[exact words CEO used]"
  Flow type: [Team Proposes / CTO Plan / HOTFIX]
  Confidence: [high / medium / low]
  Reasoning: [1 line]

  If confidence = medium/low → ask CEO before proceeding.
```

**Signal guide:**

| CEO says... | Correct flow |
|-------------|-------------|
| "что дальше" / "что делаем" / "tell me what we should do" | **CTO Plan** — present full plan, team critiques |
| "загрузи протокол и делай" / "start working on X" | **Team Proposes** — agents propose tasks autonomously |
| "срочно" / "production broken" / P0 keyword | **HOTFIX** — skip critique, keep security check |
| "предложи / propose / plan" | **CTO Plan** — put full proposal on table first |

**Rule:** Wrong flow = wasted batch (Session 72 = entire sprint redone). This step costs 30 seconds.

---

## PHASE 1: TEAM PROPOSES (replaces "CTO defines sprint")

### Step 1.0 — Parallel Proposal Round (UPDATED — Growth P0)

**Read window (15 min): All agents read SIMULTANEOUSLY.**
- All agents read codebase + memory files in parallel (not sequential).
- No agent starts proposing until all have declared "Reading complete."

**Propose window (10 min): All agents write proposals in parallel.**

**Each agent writes:**
```
PROPOSAL: [task name]
CLASS: MICRO (≤10 lines) | SMALL (10-50) | MEDIUM (50-200) | LARGE (200+)
EFFORT: [20 min | 1.5h | 4h | >4h]  ← NEW: required on every proposal
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
- **EFFORT is mandatory.** Proposals without EFFORT estimate are returned to proposing agent.

### Step 1.0.3 — Agent Briefing Requirements (v5.3 — BLOCKING)

**Every agent launch — research, code, content — MUST include a VOLAURA CONTEXT BLOCK.**

This is the #1 context-loss mechanism: CTO launches an agent with only the specific question,
zero project context. Agent produces technically correct but contextually wrong output.
Analogy: hiring a consultant without telling them what your company does.

**MANDATORY in every agent prompt:**
```
REQUIRED SECTIONS (copy from docs/AGENT-BRIEFING-TEMPLATE.md):
1. What Volaura is (3 sentences — not a volunteer platform)
2. Founder profile (Yusif, Baku, $50/mo budget, 6 weeks)
3. Target users (Leyla/Kamal/Rauf B2C + Nigar/Aynur B2B)
4. What's already decided (don't re-research what's settled)
5. Current sprint goal (why this agent is being launched RIGHT NOW)
6. NEVER rules (no generic answers, no invented numbers)
7. Output format required (table / list / comparison / code)
```

**BLOCKING CHECK before launching any agent:**
- [ ] Context block pasted?
- [ ] "What's already decided" filled in?
- [ ] "Current sprint goal" filled in?
- [ ] Output format specified?

If ANY checkbox is empty → do not launch. Fill it first. Takes 2 minutes. Saves hours.

**Failure mode:** Agent launched without context = CLASS 3 mistake (Mistake #60).
Full template: `docs/AGENT-BRIEFING-TEMPLATE.md`

---

### Step 1.0.5 — Agent Routing Lock (NEW — Architecture P1)

**CTO declares domain ownership BEFORE proposals are reviewed. 30 seconds.**

```
AGENT ROUTING LOCK:
  Assessment pipeline      → QA Agent
  User profiles + UX       → Product Agent + Accessibility Agent
  Org/B2B features         → Sales Agent + Product Agent
  Scoring + data model     → Architecture Agent + Security Agent
  Content/LinkedIn/copy    → Growth Agent + Cultural Intelligence Agent
  Infra + notifications    → Architecture Agent + Security Agent
  [Any agent CAN propose outside their domain — but must flag: "OUT-OF-DOMAIN: [reason]"]
```

This reduces debate collisions. Agents know which domain to cover before reading codebase.

### Step 1.1 — Proposal Triage

Needs Agent collects all proposals and orders by:
1. **P0 blockers** — things that make the product broken for users RIGHT NOW
2. **High leverage** — things that unblock the most downstream work (cross-reference EFFORT: prefer LOW_EFFORT P0 first to build momentum)
3. **Polish** — things that improve but don't unblock
4. **Deferred** — nice-to-have, not now

**Triage order:** P0 + LOW_EFFORT → P0 + HIGH_EFFORT → P1 + LOW_EFFORT → P1 + HIGH_EFFORT → P2+

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
CONCURRENT EDITS: [list any files touched by 2+ tasks — declare primary owner]
```

### Step 2.1 — Task Self-Classification

Each task declares its weight. Protocol gates scale automatically:

| Class | Lines | Gate Level | What's required |
|-------|-------|------------|-----------------|
| **MICRO** | ≤10 | **FAST PATH** | Proposal → execute → spot verify. Skip Steps 3.0/3.1/3.3/3.4. No critique. |
| **SMALL** | 10-50 | Light | + 1 peer review before merge |
| **MEDIUM** | 50-200 | Standard | + Security checklist + Schema verification + 1 critique round |
| **LARGE** | 200+ | Full | + Blast radius check + 2 critique rounds + user journey walkthrough |

**MICRO FASTPATH (NEW — Product P1):** If a task is ≤10 lines AND touches only 1-2 files AND has no security/auth implications → skip Steps 3.0, 3.1, 3.3, 3.4. Execute directly after proposal approval. This prevents 2-line copy fixes going through the same gates as 200-line features.

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
| Risk identification (ALL domains) | **Risk Manager** | Architecture |
| Launch readiness (ALL domains) | **Readiness Manager** | QA |

**Rule:** Risk Manager and Readiness Manager are cross-domain. They review every domain's output, not just one. Their sign-off is required on MEDIUM+ batches (already enforced in Step 4.0.5).

**Merge conflict prevention (NEW — Architecture P2):**
When two tasks touch the same file:
```
CONCURRENT EDIT PROTOCOL:
  1. Task [X] is declared primary owner → commits first
  2. Task [Y] is dependent → waits for X commit, then applies changes
  3. Conflict detected → force sequential re-execution (no parallel merge)
  This is declared in Step 2.0 Batch Lock.
```

---

## PHASE 3: EXECUTION (parallel)

### Step 3.0 — Skills + Mistakes Declaration (per task, 2 min)
*(Skipped for MICRO tasks — FASTPATH)*

Before writing any code:
```
Skills loaded: [from CLAUDE.md Skills Matrix]
This task I will NOT: [top 2 mistakes from mistakes.md relevant to THIS task]
```

### Step 3.1 — Security Pre-Check (MEDIUM + LARGE only)
*(Skipped for MICRO tasks — FASTPATH)*

```
□ Rate limiting on new endpoints?
□ RLS policies on new tables?
□ Pydantic validation on inputs?
□ Auth + ownership checks?
□ No sensitive data in logs?
□ Parameterized SQL?
□ Pydantic schemas read: [which files in apps/api/app/schemas/]  ← NEW (Security P0)
  (Prevents CLASS 4: assumed field names — recurring 4x in mistakes.md)
□ All interim TypeScript types verified against source schemas: [mismatches: none / list]
```

**Schema verification is BLOCKING.** Cannot proceed with MEDIUM/LARGE if unchecked.

### Step 3.2 — Execute

- Follow the proposal scope. Don't expand.
- Checkpoint commits at natural breakpoints: `git commit -m "[TASK-ID] description"`
- If blocked: announce blocker, continue unblocked parts. Don't wait.
- If deviating from plan: log reason BEFORE deviating.

### Step 3.2.5 — Test Execution Gate (NEW — QA P1)
*(SMALL+ tasks — skipped for MICRO)*

Before any task is marked complete:
```
□ Test file exists and is committed
□ Tests ran locally: `pytest --cov` or `npm test`  ← must actually run, not just exist
□ Coverage >= 80% on new code
□ QA declares: "Tests executed. [N] passing, [N] skipped, 0 failing."
□ CI/CD log confirms test run (link to run or paste output)

"Verified" = tests RAN and PASSED. Not: tests exist as code.
```

### Step 3.3 — Peer Review (SMALL+ tasks)
*(Skipped for MICRO tasks — FASTPATH)*

Agent who didn't write the code reviews it. Looks for:
- Schema mismatches (CLASS 4 mistake)
- Security gaps
- Missing i18n
- NEVER/ALWAYS rule violations

Verdict: **APPROVED** / **APPROVED WITH NOTES** / **BLOCKED**

If BLOCKED → fix → re-review. Not restart.

### Step 3.4 — Cross-QA Verification (NEW — QA P0)
*(MEDIUM+ tasks only)*

QA cannot self-verify tests. Independent agent spot-checks:
```
CROSS-QA SPOT-CHECK (by Architecture or Security Agent):
  □ Tests are actually running code (not just mocking everything)
  □ Tests cover failure case, not just happy path
  □ Test data is realistic (not just value = true / value = "test")
  □ Edge cases present for known risk areas (auth, scoring, PII)

Cross-checker declares: "Tests verified by [Agent]. Spotted [N] issues."

If issues found → QA re-tests. Not "QA approves QA."
Rule: QA Engineer CANNOT cross-check their own test suite.
```

---

## CONTENT BATCH SPECIAL RULES (v4.1 + v5.0 additions)

When batch touches LinkedIn / PR / content — additional gates apply BEFORE execution:

```
GATE C1 — DATA FIRST
  Run analytics on existing posts BEFORE briefing any copywriter.
  Minimum: engagement rate + audience segment breakdown.
  If no analytics exist → 1h research task before anything else.
  "We'll add analytics later" = building blind. Not acceptable.

GATE C2 — HOOK EXTRACTION
  Before every post brief: extract 1 new hook from SESSION-FINDINGS.md.
  No new hook found → delay post. Do not repeat existing hooks.
  Staleness is invisible to writers but visible to returning readers.

GATE C3 — COPYWRITER READ GATE
  Every copywriter agent MUST read real source files (not summaries).
  Files to read: TONE-OF-VOICE.md, AZ-LINKEDIN-AUDIENCE.md,
  published posts, SESSION-FINDINGS.md (last 10 entries).
  Agent declares "Files read: [list]" before writing first word.
  No declaration = output rejected.

  C3 VERIFICATION (NEW — Security P1):
  Output reviewer spot-checks READ declaration:
  - Pull one specific rule from TONE-OF-VOICE.md
  - Check if output follows it (cite line in copy)
  - If not → output REJECTED, agent re-reads and rewrites
  This creates real friction for fake READ declarations.

GATE C3.5 — BRIEF REVISION RE-APPROVAL (NEW — Cultural Intelligence P0)
  If copywriter revises copy AFTER brief is approved:
  → Cultural Intelligence re-reads REVISED brief from top
  → Not "the brief was already approved" — revision resets approval
  → Any change to hook/framing/CTA/audience = full Cultural re-check
  Copy that changes after C5 checkpoint → C5 runs again.

GATE C4 — GROWTH LOOP DEFINITION
  Every content batch must define: how do post-publish metrics
  return to the Strategist? Who measures? When? In what format?
  If loop is not defined → no publish. Broadcast without feedback = waste.

GATE C5 — CULTURAL CHECKPOINT
  Cultural Intelligence Agent reviews brief (not just final copy).
  Brief fails if: competitive framing, personal grievance risk,
  EN/AZ voice bleed, management risk unaddressed.
  Checkpoint is BEFORE copywriters write, not after.

GATE C5.5 — CULTURAL COPY SIGN-OFF (NEW — Cultural Intelligence P1)
  After copywriters write final copy (not just brief):
  □ Cultural Intelligence reads FINAL copy (not draft, not summary)
  □ Checks: tone/framing/gender/competition/AZ-EN bleed/management risk
  □ Verdict: APPROVED / APPROVED WITH NOTES / BLOCKED
  If copywriter changes copy after C5.5 first read → C5.5 runs again.
  Cultural approval is gate before CEO sees copy. Not after-thought.
```

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

### Step 4.0.5 — Completion Consensus (NEW — Architecture P1)

Before writing the batch report, each primary agent produces this exact output:

```
AGENT: [Name]
TASKS COMPLETED: [list task IDs]
TESTS RAN: [pytest command] → [X passed, Y failed]
JOURNEY VERIFIED: [page/flow tested + what was confirmed]
MEMORY UPDATED: [files updated, or "none required"]
BLOCKERS: [any unresolved issue, or "none"]
SIGN-OFF: ✅ READY / ❌ BLOCKED — [reason if blocked]
```

Consensus rules:
- 3+ READY sign-offs required before Step 4.1
- Any ❌ BLOCKED → batch stays open, CTO investigates
- If agent cannot produce TESTS RAN line → task is NOT done (assertion by CTO doesn't count)
- Risk Manager and Readiness Manager sign-offs required for any MEDIUM+ feature batch

This makes "done" explicit. Not implicit. Audit trail for every batch.

### Step 4.1 — Batch Report to CEO

One report for the entire batch, not per-task:

```
BATCH: [ID]
COMPLETED: [count] tasks — [1-line each]
DEFERRED: [count] — [why each]
DISCOVERED: [gaps found during execution]
BUSINESS IMPACT: [what users can now do that they couldn't before]
QUESTION: [one question if needed, or NONE]

WHAT'S NEXT (NEW — Product P0):
  1. [highest priority unblocked task — ready to start immediately]
  2. [highest risk item outstanding]
  3. [thing CEO probably hasn't thought about yet]
```

**Rule:** "What's next" is declared by CTO proactively, not after CEO asks "что дальше". Every batch close includes it. No exceptions.

### Step 4.1.5 — Session-End Mini-Swarm (AUTO — fires on git push)

Triggered automatically by `.github/workflows/session-end.yml` on every push to main.
3 agents (Security / QA / Product) review THIS session's changes via SESSION-DIFFS.jsonl.
CTO does NOT trigger this manually — it fires in the background.

Output: `code-review` mode proposals → `memory/swarm/proposals.json`.
CEO sees HIGH/CRITICAL findings via Telegram within 10 minutes of push.

**CTO rule:** After push, do NOT immediately start next batch. Wait 3 minutes. If Telegram
alert arrives → triage before proceeding. If no alert → continue.

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

### Step 4.2.5 — Retro Simulation (auto-trigger after HIGH/CRITICAL batches)

For batches marked HIGH or CRITICAL stakes, Retro Sim fires async after Step 4.2.
3-4 agents review: "What did the batch miss? What needs validation?"
Confidence gate: ≥35/50. Below threshold → findings go to inbox for next batch.
Feeds `memory/swarm/agent-feedback-log.md` with validated patterns.

---

## PHASE 0.7 — SPRINT GATE DSP (fires when CEO says "загрузи протокол")

**Purpose:** Force DSP before batch assembly — not just for code, but for sprint strategy.
Prevents embarking on a week of wrong work.

```
SPRINT GATE DSP:
  Trigger: CEO says "загрузи протокол" or "start working on X"
  When: BEFORE Step 1.0 (Team Proposes), not after
  Agents: 7 async agents — Product / Architecture / Security / QA / Growth / Risk Manager / Readiness Manager
  Time budget: 2 minutes
  Confidence gate: ≥40/50 = proceed | 25-39 = CTO decides with caveat | <25 = BLOCK

  Questions to simulate:
  1. What is the highest-impact work RIGHT NOW for launch readiness?
  2. What technical risk is being deferred that will bite us later?
  3. What does the user journey look like TODAY — what breaks?

  Output format:
  DSP SPRINT GATE: [session date]
  Paths simulated: [N] | Winner: [path name] — [score]/50
  Key risk identified: [1 sentence]
  Recommended focus: [P0 list for this batch]
  Gate result: PROCEED / PROCEED WITH CAVEAT / BLOCK
```

**Rule:** Sprint Gate DSP is advisory, not blocking (below 25 blocks, but 25-39 proceeds
with CTO caveat). Its job is to surface blind spots, not slow down execution.

---

## DSP AUTO-TRIGGER MODES (v5.1 addition)

Three modes that fire DSP WITHOUT CTO remembering to run it.

### Mode 1 — Session Hook (fires at sprint start signal)
```
Trigger: CEO says "загрузи протокол" / "load protocol" / "что дальше"
Flow: 7 agents, 2 min, advisory
Gate: 40/50 = proceed | <25 = BLOCK
Seed prompt template: "What is the highest-impact sprint focus for [date]?"
Agents: Product × Architecture × Security × QA × Growth × Risk Manager × Readiness Manager
```

### Mode 2 — Code Gate (fires before MEDIUM/LARGE code changes)
```
Trigger: Any task classified MEDIUM (50-200 lines) or LARGE (200+) with
         an architecture decision flag
Flow: 4 agents, 90 sec, BLOCKS execution if score <25/50
Gate: 40/50 = proceed | 25-39 = proceed with documented trade-off | <25 = BLOCK
Seed prompt template: "Is this implementation path correct? [task description]"
Agents: Architecture × Security × QA × Product
Output stored: DECISIONS.md under task name
```

### Mode 3 — Retro Sim (fires async after batch close)
```
Trigger: Batch close message ("BATCH CLOSED" or "BATCH: [ID] COMPLETED")
Flow: 3 agents, 5-10 min, ASYNC (non-blocking)
Gate: Advisory — findings go to inbox for next batch
Seed prompt template: "What did this batch miss? What needs validation before ship?"
Agents: Security × QA × Architecture
Output stored: agent-feedback-log.md + proposals.json (LOW severity)
```

**Rule:** Modes 1-3 replace manual "should I run DSP?" decisions. If trigger condition
fires → DSP fires. No CTO intervention required.

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
| Fix i18n string "volunteer" → "professional" | MICRO | 1 line, 1 file → FASTPATH |
| Add rate limiter to endpoint | MICRO | 1 decorator → FASTPATH |
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
| Assumed field names | CLASS 4 | No schema read before coding (now blocked in 3.1) |
| Invented metrics | CLASS 5 | No source file for claimed number |
| Built features when basics broken | CEO feedback | P0 issues exist but team builds P3 features |
| Wrong flow type (team-proposes when CTO-plan needed) | CLASS 3 | No Step 0.5 Flow Detection declared |
| QA self-validates own tests | CLASS 5 | No Cross-QA sign-off (Gate 3.4) |
| Copywriter fakes READ declaration | CLASS 5 | No C3 verification spot-check |
| Risk Manager skipped on MEDIUM+ batch | CLASS 3 | Step 4.0.5 sign-off missing from Risk Manager |
| Readiness Manager skipped before deployment | CLASS 3 | No LRL score declared before any prod push |
| New endpoint shipped without risk score | CLASS 4 | Risk register not updated this batch |
| Agent launched without VOLAURA CONTEXT BLOCK | CLASS 3 | Step 1.0.3 context checklist not completed |
| Agent prompt missing "what's already decided" | CLASS 3 | Agent re-researches settled questions, wastes tokens |
| Agent output used without checking context fit | CLASS 4 | Research correct technically but wrong for AZ/bootstrapped context |

---

## PROTOCOL EVOLUTION

This document improves every batch. Needs Agent proposes changes in Step 4.2 retrospective. Team votes. Changes logged here:

| Version | Date | Change | Trigger |
|---------|------|--------|---------|
| v1.0 | 2026-03-28 | Initial: skills → plan → critique → execute | Session 59 |
| v2.0 | 2026-03-28 | Added checklist + enforcement hook | Session 59 |
| v3.0 | 2026-03-29 | +Mistakes audit, +team selection, +blast radius, +CEO gate | 5 agent proposals |
| v4.0 | 2026-03-29 | Team-first proposals, parallel batches, agent override, proportional gates | CEO directive: "Team decides, not CTO alone" |
| v4.1 | 2026-03-29 | CTO plan → team critique flow added. Content batches: C1-C5 gates | Session 72: CEO caught CTO running wrong phase |
| **v5.0** | **2026-03-29** | **14 agent proposals: Flow detection (0.5), parallel proposals, effort estimates, routing lock, MICRO fastpath, schema gate (3.1), test execution gate (3.2.5), cross-QA (3.4), C3 teeth, C3.5 brief re-approval, C5.5 cultural copy sign-off, completion consensus (4.0.5), "what's next" in batch close** | **Session 73: All 6 agents proposed improvements — routing, speed, verification gaps** |
| **v5.1** | **2026-03-30** | **Swarm optimization: SESSION-DIFFS.jsonl (git-level diff feed), session-end workflow (mini-swarm on push), skills_loader.py (auto-skill matching), 3 DSP auto-trigger modes (Session Hook/Code Gate/Retro Sim), Sprint Gate DSP (Phase 0.7), session_end_hook.py. Closes 42% already-done proposals gap.** | **Session 76: 4-agent swarm analysis found 42% proposals were already shipped. Root cause: agents blind to git state.** |
| **v5.2** | **2026-03-30** | **Risk Manager (ISO 31000) + Readiness Manager (SRE/ITIL) integrated throughout: Required Reads (2 new entries), Domain Ownership table (cross-domain rows), Sprint Gate DSP agents (5→7), DSP Mode 1 agents (5→7), FAILURE MODES (3 new CLASS entries). autonomous_run.py PERSPECTIVES updated. These agents are permanent — not optional, not called on request.** | **CEO directive 2026-03-30: "они всегда должны быть в команде чтоба находить проблемы которые вы не видите в общем"** |
| **v5.3** | **2026-03-30** | **Agent Briefing Requirements: Step 1.0.3 added as BLOCKING gate before any agent launch. VOLAURA CONTEXT BLOCK (300-word canonical context) MUST be injected into every agent prompt. Agents launched without it = CLASS 3 mistake. Full template: `docs/AGENT-BRIEFING-TEMPLATE.md`. 3 new FAILURE MODES added.** | **CEO directive 2026-03-30: Research agents returned technically correct but contextually wrong answers — didn't know what Volaura is, who Yusif is, what's already decided. "При сжатии памяти всё теряется."** |

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
| Agent prompt template | `docs/AGENT-BRIEFING-TEMPLATE.md` |
