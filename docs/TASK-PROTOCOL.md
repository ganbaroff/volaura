# TASK PROTOCOL v8.0 — Quality-First Execution (Toyota + Apple + DORA)

**Version:** 8.0 | **Updated:** 2026-04-03
**Previous:** v7.1 (15 agent findings from protocol audit)
**Change v8.0:** Quality System overhaul based on NotebookLM deep research (45+ sources: Toyota TPS, Apple ANPP, DORA 2026, Lean Six Sigma DMAIC).
New steps: 1.5 (Acceptance Criteria — DoR gate), 4.5 (Quality Gate — Jidoka), 5.5 (DORA metrics — Kaizen).
New docs: QUALITY-STANDARDS.md, AC template, QA Agent (can block tasks), CrewAI ADR-009.
New principle: Protocol is structural prevention (Poka-yoke), not willpower.
CEO directive: "перестань думать как стартап. начни думать как Apple и Toyota."
**Change v7.1:** 15 agent findings from 5-agent protocol audit (Architecture + QA + Risk Manager + Readiness Manager + Product):
1. Header fixed: v6.0 → v7.1, changelog order corrected (v6.0 must precede v7.0)
2. Phase 0.7 moved to correct position: between Step 0.5 and Phase 1 (was incorrectly after Phase 4)
3. Classification systems merged: MICRO/SMALL/MEDIUM/LARGE mapped to L1-L5 (single system)
4. EXPEDITED mode added to Step 0.5 signal guide (legitimate fast path between HOTFIX and full protocol)
5. MICRO FASTPATH capped: blocked for auth/scoring/external content regardless of line count
6. Required Reads reorganized: 3-tier priority (3 must-read → 3 if-relevant → 4 reference)
7. Named roles added at Batch Lock: C3_REVIEWER, CROSS_QA_AGENT declared upfront
8. Auto-routing catch-all row added: task type not in table → default L3
9. 3 missing auto-routing rows: investor/pitch = L4, partnership comms = L3, internal specs = L2
10. Independent agent confidence scoring for L4/L5 (verification agent declares %, not CTO)
11. Round-2 debate output format defined (was declared but format missing)
12. Step 0b fallback added for missing SESSION-DIFFS.jsonl / code-index.json
13. Mid-Batch Direction Change protocol added (2-sentence rule)
14. HOTFIX security minimum defined inline (4 mandatory checkboxes)
15. Efficiency Gate scope warning elevated to top-of-file (was buried in body)

**Why v5.0 exists:** Session 73 — All 6 agents proposed improvements after CEO directive "fix routing, rules, speed, efficiency." Proposals reviewed, voted, and implemented in one batch.
**Why v6.0 exists:** 2026-04-01 — Cross-repo analysis of ZEUS (adaptive executor, context intelligence), MindShift (v6.0 protocol), and Claude Code patterns (heartbeat gate, outcome verification).
**Why v7.0 exists:** 2026-04-02 — Non-code tasks had no quality gate. 29 grammar errors in startup.az application went undetected. Universal L1-L5 complexity scale + Confidence Gate added.
**Why v7.1 exists:** 2026-04-02 — 5-agent protocol audit scored protocol 66/100. Enforceability worst dimension (11/20). All 15 structural and enforcement gaps closed in one pass.

---

## How It Works — ZERO SIMULATION VERSION (v9.0)

**RULE: Every step that says "agent reviews" MUST show the agent's ACTUAL OUTPUT.**
**CTO writing "agent confirmed" without pasting agent response = FABRICATION (CLASS 5).**
**If external API is down → document the error. Don't pretend the review happened.**

```
0. FLOW DETECTION  → CTO reads CEO signal → declares flow type.
                     PROOF: paste CEO's exact words.

1. IMPACT ANALYSIS → BEFORE touching ANY code:
                     CTO sends proposed change to external model (Gemini/Llama/Qwen3).
                     Prompt: "I will change [FILE]. What else in the project could break?"
                     PROOF: paste the model's response verbatim.
                     If model says "X, Y, Z could break" → check X, Y, Z BEFORE coding.
                     This step exists because CTO changed admin route and broke OAuth,
                     changed middleware and broke deploy, changed types and broke build.
                     EVERY. SINGLE. TIME.

2. ACCEPTANCE CRITERIA → Write BEFORE coding:
                     "DONE when: [3-5 PASS/FAIL conditions]."
                     MUST include: "Build passes. Deploy succeeds. Affected pages load."
                     PROOF: AC visible in response before any code edit.

3. IMPLEMENT → Write code.
              After EACH file edit: check if build still passes.
              NOT at the end. After EACH edit.
              If build breaks → fix BEFORE next edit.

4. VERIFY → Run the actual check. Not "it should work."
           Code change → `pnpm build` (show output)
           API change → `curl` the endpoint (show response)
           UI change → preview_screenshot (show image)
           Deploy → check production URL (show HTTP status)
           PROOF: tool output pasted in response.

5. EXTERNAL REVIEW → Send completed work to external model.
                    Prompt: "Review this change. What did I miss? What could break?"
                    PROOF: paste model's response.
                    If model finds issue → fix BEFORE committing.

6. COMMIT + DEPLOY → Only after steps 1-5 have VISIBLE proof.
                    `pnpm build` passes (shown).
                    `git push` succeeds (shown).
                    Production URL returns 200 (shown).

7. DOCUMENT → Update SHIPPED.md + sprint-state.md.
             Record in quality-metrics.md.
             3-question DoD: WHO reviewed (with output) / WHAT step / WHERE written.
```

## WHAT "PROOF" MEANS

CTO CANNOT write any of these:
- "Agent confirmed" (WHERE is the agent's output?)
- "Build passes" (WHERE is the build log?)
- "Tested and works" (WHERE is the test output?)
- "Reviewed by swarm" (WHERE are their responses?)
- "No issues found" (WHO looked? SHOW their analysis.)

CTO MUST paste:
- Actual Bash output of `pnpm build`
- Actual curl response
- Actual external model critique (full text, not summary)
- Actual screenshot or preview_snapshot

If CTO cannot show proof → step did not happen → task is not done.

## WHY v9.0 EXISTS

v8.0 had 15-item DoD, Toyota quality system, DORA metrics, Poka-yoke table.
CTO followed NONE of it. Changed routes → broke deploy. Changed types → broke build.
Changed middleware → broke auth. Every time WITHOUT checking impact first.

v9.0 removes everything that CTO can fake:
- No "agent says X" without pasting X
- No "build passes" without showing log
- No "tested" without showing output
- No "reviewed" without showing review

The protocol is now EVIDENCE-BASED. Not trust-based. Trust failed 77 times.
4.5 QUALITY GATE   → Before marking task DONE:
                     □ All acceptance criteria from Step 1.5 verified (PASS/FAIL each)
                     □ No new console errors, no TypeScript errors, no test failures
                     □ If change is user-facing: preview_screenshot or preview_snapshot proves it
                     □ If API change: curl/test proves correct response
                     IF ANY BOX UNCHECKED → task stays in_progress. Not done. Fix first.
                     This is Apple's "changes only after QA approval" principle.
5. BATCH CLOSES   → CEO Report Agent formats output (no file names, product language only).
                    "What's next" declared. Memory updated.
                    Skill evolution check: any skill with ≥5 trajectories → suggest improvements
5.5 DORA + KAIZEN  → After EVERY batch, CTO records in memory/context/quality-metrics.md:
                     | Metric | Value | Target |
                     | Tasks completed | N | — |
                     | Tasks with AC written BEFORE | N/total | 100% |
                     | AC pass rate (first attempt) | N/total | >80% |
                     | Defects found post-completion | N | 0 |
                     | External models used | N providers | ≥2 |
                     | Solo execution instances | N | 0 |
                     Kaizen: "One thing to improve next batch: [specific]."
                     DORA target: Change failure rate <5% (currently 34.8%).
                     This step takes 2 minutes. It is NEVER skipped.
                     WHY: Toyota measures everything. What isn't measured isn't improved.
```

## DEFINITION OF DONE — 3 Questions (Pareto: covers 76.4% of all defects)

Defect autopsy (2026-04-03): 76 bugs → CLASS 3 (32.7%) + CLASS 1 (25.5%) + CLASS 2 (18.2%) = 76.4%.
15-item DoD at 0% compliance is worse than 3-item DoD at 100%.

**Before marking ANY task DONE, answer these 3 questions:**

```
1. WHO ELSE REVIEWED?  → Name the agent or external model.
                         "Nobody" = task is NOT done.
                         (Prevents CLASS 3: solo execution — 18 bugs)

2. WHAT STEP DID YOU FOLLOW? → Cite the protocol step number.
                         "None" = task is NOT done.
                         (Prevents CLASS 1: protocol skipping — 14 bugs)

3. WHERE IS IT WRITTEN? → Link the file you updated (SHIPPED.md, sprint-state.md, etc.)
                         "Nowhere" = task is NOT done.
                         (Prevents CLASS 2: memory not persisted — 10 bugs)
```

3 questions. If ANY answer is "nobody/none/nowhere" → task stays in_progress.
This is the ONLY DoD. No 15-item checklist. No Gherkin templates. 3 questions.

## POKA-YOKE — Mistake-Proofing Mechanisms

Rules that rely on willpower fail (73 mistakes prove this). These are STRUCTURAL:

| Mechanism | What it prevents | How |
|-----------|-----------------|-----|
| AC before batch (Step 1.5) | Building wrong thing | Task blocked from Step 2 without AC |
| Quality Gate (Step 4.5) | Shipping broken code | DONE status blocked without all boxes checked |
| Swarm Retro (Step 0a) | Repeating mistakes | External models critique before new sprint |
| LLM Provider Check (Step 5.4) | Same-model echo chamber | ≥3 agents requires ≥2 providers |
| CEO Report Agent (Step 5) | Technical debris to CEO | All output filtered before CEO |
| DORA tracking (Step 5.5) | Invisible quality decay | Metrics recorded every batch |

Toyota principle: make errors IMPOSSIBLE, not just unlikely.
                    RULE: CTO never reports to CEO directly. All output passes through CEO Report Agent first.
                    See: memory/swarm/skills/ceo-report-agent.md
```

**Core principle:** Protocol is ALWAYS ON. Not opt-in. Not triggered by "загрузи протокол."
Every CEO message = protocol is running. CEO confirmed: "я никогда не буду писать без текста запусти протокол."
This means: there is NO state where protocol is off. Skipping a step requires documenting WHY.

**⚠️ EFFICIENCY GATE SCOPE (added v7.0 — violated 3× in Session 82):**
Efficiency Gate = "skip DSP if decision is obvious." It applies ONLY to DSP (Step 3).
It NEVER applies to:
- Step 5.5 (agent routing check) — always run
- Step 1.0.3 (agent briefing context block) — always fill
- Step 1.0.3b (session context injection) — always fill
These three steps have ZERO efficiency exceptions. No task is too simple for them.

---

## Required Reads — 3-Tier Priority (before every batch)

**Agent finding #6:** 10 files with equal weight = none feel mandatory. 3-tier structure creates real signal.

### Tier 1 — ALWAYS READ (batch cannot start without these, ~3 min)

| File | What it tells you |
|------|-------------------|
| [`memory/context/sprint-state.md`](../memory/context/sprint-state.md) | WHERE ARE WE RIGHT NOW — current position, last session |
| [`memory/context/mistakes.md`](../memory/context/mistakes.md) | CLASS 1-8 recurring errors — what NOT to repeat this session |
| [`memory/swarm/SHIPPED.md`](../memory/swarm/SHIPPED.md) | What code exists — prevents rebuilding what's done |

### Tier 2 — READ IF RELEVANT TO THIS BATCH (~2 min, skip with reason if truly irrelevant)

| File | When relevant |
|------|--------------|
| [`memory/swarm/agent-roster.md`](../memory/swarm/agent-roster.md) | Any batch with agents (which is most batches) |
| [`memory/swarm/shared-context.md`](../memory/swarm/shared-context.md) | Architecture decisions, schema, known bugs — any code batch |
| [`memory/swarm/agent-feedback-log.md`](../memory/swarm/agent-feedback-log.md) | Proposal round — avoid re-proposing rejected ideas |

### Tier 3 — REFERENCE (pull when the specific domain is touched)

| File | Pull when... |
|------|-------------|
| [`memory/context/patterns.md`](../memory/context/patterns.md) | Writing new patterns or reviewing what worked |
| [`CLAUDE.md`](../CLAUDE.md) | Skills Matrix, NEVER/ALWAYS rules — execution phase |
| [`memory/swarm/skills/risk-manager.md`](../memory/swarm/skills/risk-manager.md) | MEDIUM+ batch — what CRITICAL/HIGH risks are open |
| [`memory/swarm/skills/readiness-manager.md`](../memory/swarm/skills/readiness-manager.md) | Pre-deployment or sprint gate — LRL score check |

**Rule:** Tier 1 has ZERO skip exceptions. Tier 2 skip = "Skipping [file] because [reason]." Tier 3 pull on demand.

---

## STEP 5.4 — LLM PROVIDER CHECK (fires before EVERY agent launch ≥3 agents)

**Added:** 2026-04-02 — Mistake #68. Same-model swarm = monologue with masks.

```
Before launching any swarm with ≥3 agents:

1. Read apps/api/.env → list active LLM API keys
2. Assign DIFFERENT providers to different roles:

   REASONING / Security / Attack vectors:
     → deepseek-ai/deepseek-r1-distill-qwen-32b via NVIDIA NIM
     → Base: https://integrate.api.nvidia.com/v1
     → Key: NVIDIA_API_KEY from .env

   ARCHITECTURE / Large context / System design:
     → meta/llama-3.1-405b-instruct via NVIDIA NIM
     → Same base URL + key

   FAST / Volume / Product / Growth:
     → llama-3.3-70b-versatile via Groq
     → Base: https://api.groq.com/openai/v1
     → Key: GROQ_API_KEY from .env

   SYNTHESIS / Final judgment / CTO decision:
     → claude-sonnet (Agent tool)

3. Mechanism for non-Claude models: Bash tool + Python urllib
   (Agent tool = Claude only. Groq/NVIDIA = Bash API calls)

4. Declare: "LLM providers assigned: [list]. Launching swarm."

RULE: claude-haiku × N is NOT a swarm. It is one model with N masks.
      True diversity = different training data + different architectures.
      A security agent on DeepSeek R1 will find what haiku Security Agent misses.

FALLBACK CHAIN (if primary provider returns 403/500):
   Groq 403 → try Gemini 2.0 Flash (GEMINI_API_KEY)
   NVIDIA NIM 500 → try DeepSeek via direct API (DEEPSEEK_API_KEY)
   Both down → Claude Agent (haiku/sonnet) as last resort + document degradation
   RULE: Never silently skip a provider. Log: "Provider X unavailable → fell back to Y."

SKIP condition: swarm has <3 agents AND all are Claude → skip this step.
NEVER skip: for Sprint Gate DSP (7 agents) — this step is mandatory.
```

**Mistake #68 proof:** 3 external models found in 60 seconds what 7 haiku agents missed:
- Tribe matching cold-start: no 2-person fallback at <50 users
- CRON_SECRET: startup guard missing → silent 403 for unknown days
- Realtime RLS: subscription bypass vector on notifications table
- GDPR pg_cron: most likely month-1 production incident

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
| "срочно" / "production broken" / P0 keyword | **HOTFIX** — skip critique, keep security check (see HOTFIX Minimum below) |
| "предложи / propose / plan" | **CTO Plan** — put full proposal on table first |
| "быстро / need this today / time pressure" | **EXPEDITED** — CTO Plan + 1 critique round only, no Round-2 gate |

**EXPEDITED mode (new v7.1):** Legitimate fast path between HOTFIX (emergency) and full protocol (normal). Triggers when CEO signals time pressure but no production emergency. Steps skipped: Round-2 debate, Retro Sim, C3.5 re-approval. Steps kept: Flow detection, Agent routing check, Security pre-check, Confidence gate, Memory update.
- Rule: EXPEDITED cannot be self-declared by CTO. Must have explicit CEO time signal.
- EXPEDITED + security-touching task → upgrade to full protocol automatically. No exceptions.

**HOTFIX Security Minimum (inline — must run even in HOTFIX):**
```
□ Rate limiting preserved on modified endpoint?
□ RLS policies unaffected or explicitly re-verified?
□ No new input path bypasses Pydantic validation?
□ No auth/session logic altered without Security agent sign-off?
If ANY box is unchecked → HOTFIX is blocked. Fix security first, then ship.
```

**Rule:** Wrong flow = wasted batch (Session 72 = entire sprint redone). This step costs 30 seconds.

---

## PHASE 0.7 — SPRINT GATE DSP (fires when CEO says "загрузи протокол")

**Purpose:** Force DSP before batch assembly — not just for code, but for sprint strategy.
Prevents embarking on a week of wrong work.

**Position:** BETWEEN Step 0.5 (Flow Detection) and Phase 1 (Team Proposes). Fires BEFORE proposals, not after.

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

**⚠️ MANDATORY CONTINUATION RULE (Mistake #66 — 2026-04-02):**
After agents return findings → CTO MUST immediately:
1. Declare: "DSP Sprint Gate [date]: Winner = [path] — [score]/50. Key risk: [1 sentence]."
2. Move to Phase 1/CTO Plan WITHOUT waiting for CEO signal.
Stopping after agent results = CLASS 1 mistake. Agent output is input, not output.

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

### Step 1.0.3b — SESSION CONTEXT INJECTION (NEW v7.0 — BLOCKING)

**Root cause of 50% agent output quality:** Agents received static project context (what Volaura is) but zero dynamic context (what happened today). They were blind to decisions made, tasks completed, and CEO directives in the current session.

**MANDATORY before launching ANY agent — fill this section:**
```
SESSION CONTEXT (dynamic — fill fresh every agent launch):
  Decisions made today:    [list key decisions from this session]
  Tasks already done:      [what CTO/agents completed — agent must not repeat these]
  Previous agent output:   [what the last agent produced, if chaining agents]
  CEO said today:          [any explicit CEO directives, approvals, or rejections]
  Current priority:        [speed / thoroughness / specific outcome CEO wants]
  What NOT to do:          [anything CEO rejected or is already handled]
```

**Paste this ABOVE the static VOLAURA CONTEXT BLOCK in every agent prompt.**

**Leaving it blank = agent is flying blind = 50% correct output = CLASS 3 Mistake #64.**

**Time cost:** 2 minutes. **Value:** Agent understands the full context, not just the task.

**Failure mode check:** Before launching agent, ask: "If the agent reads only this prompt and nothing else — does it know everything relevant that happened today?" If NO → add more session context.

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

**Round-2 gate trigger:** if top-ranked proposal score <35/50 AND delta to #2 is <5 pts → mandatory Round 2.

**Round-2 debate output format (v7.1 — was missing):**
```
ROUND-2 DEBATE:
  Trigger: [why Round 2 fired — score / delta]
  Positions:
    [Agent]: [proposal they support] — [1 sentence reasoning]
    [Agent]: [counter-proposal] — [1 sentence reasoning]
  Resolution: [which proposal won after Round 2]
  Final score: [N]/50
  If still <35 → CTO documents exception and proceeds with caveat.
```

**Output:** Ordered task list with assignments.

---

## PHASE 2: BATCH ASSEMBLY

### Step 2.0 — Batch Lock

**Agent finding #9:** Named roles were unassigned at batch start, causing ambiguity mid-batch on who owns verification. Now declared at Batch Lock.

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

NAMED ROLES (declare at lock, not mid-batch):
  C3_REVIEWER:     [agent name] — owns GATE C3 verification spot-check
  CROSS_QA_AGENT:  [agent name] — owns Step 3.4 cross-QA (cannot be same as QA author)
  BATCH_AGENT_COUNT: [N] agents active this batch — if N < 3, flag as UNDER-RESOURCED
```

**Mid-Batch Direction Change (v7.1):** If CEO or CTO changes direction after Batch Lock:
Declare in batch log: "DIRECTION CHANGE: [what changed] → [tasks cancelled/added]." Re-run Step 2.0 for affected streams. Do not silently absorb scope changes.

### Step 2.1 — Task Self-Classification (Unified System v7.1)

**Agent finding #3:** Two classification systems existed simultaneously (MICRO/SMALL/MEDIUM/LARGE for code; L1-L5 for universal). Now ONE system. Code tasks map directly to L levels.

| Level | Former name | Lines (code) | Gate Level | What's required |
|-------|-------------|-------------|------------|-----------------|
| **L1** | MICRO | ≤10 | **FAST PATH** | Proposal → execute → spot verify. Skip Steps 3.0/3.1/3.3/3.4. |
| **L2** | SMALL | 10-50 | Light | + 1 peer review before merge |
| **L3** | MEDIUM | 50-200 | Standard | + Security checklist + Schema verification + 1 critique round |
| **L4** | LARGE | 200+ | Full | + Blast radius check + 2 critique rounds + user journey walkthrough + agent confidence scores |
| **L5** | Critical | Any | Maximum | + Full 7-agent sign-off + CEO review before ship |

**Non-code tasks:** Use the Task Type → Auto-Routing Table (in TASK COMPLEXITY LEVELS section). AZ formal documents = L4. Government applications = L4. Legal = L5.

**L1 (MICRO) FASTPATH — CAPPED (v7.1):**
L1 is available ONLY if ALL of the following are true:
- ≤10 lines changed
- 1-2 files touched
- Does NOT touch: auth logic, scoring/AURA calculations, RLS policies, external-facing content
- Does NOT touch: any file named `*security*`, `*auth*`, `*payment*`, `*scoring*`

If ANY of the above conditions fail → minimum L2. No exceptions.
**Reason:** "It's just 3 lines" is how security bugs and scoring regressions ship. Cap prevents CLASS 4.

**L4/L5 — Independent Agent Confidence Scoring (v7.1):**
For L4/L5 tasks, CTO confidence alone is insufficient. A verification agent (not the author) declares:
```
INDEPENDENT CONFIDENCE CHECK (by [Agent Name, not task author]):
  Reviewed: [what was checked]
  Confidence in correctness: [%]
  Gaps remaining: [list or "none found"]
  Sign-off: READY / BLOCKED
```
This replaces self-reported CTO confidence for high-stakes work.

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

## TASK COMPLEXITY LEVELS v7.0 — Universal (Code + Content + Documents)

**Why v7.0 exists:** v6.0 classified tasks by code size only. Non-code tasks (government applications, legal documents, formal AZ-language content, research reports) had no quality gate. Result: 29 grammar errors in a startup championship application went undetected until CEO asked. Confidence gap: CTO delivered at ~65% quality without knowing it. This section fixes that.

---

### Complexity Scale — 5 Levels (ALL task types)

| Level | Name | What it means | Verification required |
|-------|------|--------------|----------------------|
| **L1** | Trivial | 1 file, 1 change, obvious, reversible. CTO confidence ≥95%. | None. Execute + spot-check. |
| **L2** | Simple | Known territory, 1-2 domains, low ambiguity. Confidence ≥85%. | 1 agent spot-check (domain expert). |
| **L3** | Standard | Multiple domains OR unfamiliar territory OR formal output. Confidence ≥70%. | 1-2 agents + confidence gate before delivery. |
| **L4** | Complex | High stakes, irreversible, or CTO confidence <70%. | Full swarm subset (3-4 agents relevant to domain). |
| **L5** | Critical | Irreversible + external-facing + high risk (legal, financial, security). | Full 7-agent swarm + CEO review before publish. |

**Rule:** CTO declares level BEFORE executing. If unsure → round UP, not down.

---

### Task Type → Auto-Routing Table

| Task type | Default Level | Mandatory verification agents |
|-----------|--------------|-------------------------------|
| Code < 10 lines | L1 | None |
| Code 10–50 lines | L2 | Architecture (spot-check) |
| Code 50–200 lines | L3 | Architecture + Security |
| Code 200+ lines | L4 | Architecture + Security + QA |
| LinkedIn post | L3 | Communications Strategist + Cultural Intelligence |
| AZ-language formal document | **L4** | **Cultural Intelligence + Grammar Agent (2 models)** |
| Government / grant application | **L4** | **Cultural Intelligence + Grammar Agent + Communications Strategist** |
| Legal / ToS / Privacy Policy | **L5** | Legal Advisor + Cultural Intelligence + CEO review |
| Financial projections | L4 | Risk Manager + Growth Agent (verify assumptions) |
| Research / market analysis | L3 | Growth Agent + fact-check source requirement |
| Architecture decision | L4 | Architecture + Security + DSP (Mode 2) |
| DB migration | L4 | Architecture + Security + Readiness Manager |
| Production deploy | L5 | Full 7-agent + engineering:deploy-checklist |
| Investor / pitch material | L4 | Growth Agent + Risk Manager + fact-check (no fabrication) |
| Partnership communications | L3 | Communications Strategist + Cultural Intelligence |
| Internal specs / ADRs | L2 | Architecture Agent spot-check |
| **Task type NOT in this table** | **L3 default** | **Architecture + domain-relevant agent. Round up, never down.** |

**Key insight:** AZ formal government application = L4 by default. Not L1. Grammar agents are MANDATORY, not optional.
**Catch-all rule:** If a task type doesn't appear in this table → default L3. CTO cannot self-assign L1/L2 for unlisted types.

---

### Confidence Gate (MANDATORY before any L3+ output delivery)

Before handing any L3+ result to CEO, CTO declares:

```
CONFIDENCE GATE:
  Task type:        [code / LinkedIn / AZ formal doc / legal / research / ...]
  Complexity:       L[1-5]
  CTO confidence:   [%] — honest self-assessment
  Weak points:      [where CTO knowledge is limited — AZ grammar, legal, financial]
  Verification run: [agents consulted, or "none — L1/L2 fastpath"]
  Ready to deliver: YES (≥85% after verification) / NO (verification pending)
```

**Confidence thresholds:**
- ≥85% after verification → deliver
- 70–84% → deliver with explicit caveat to CEO ("verified by agents, but recommend native speaker review")
- <70% → do NOT deliver until additional verification run

**Trigger pattern for grammar/language tasks:**
If task involves AZ-language output AND output goes to external audience (government, public, B2B) → confidence starts at 50% (CTO is not a native AZ speaker) → verification MANDATORY → minimum 2 grammar agents required before confidence can reach 85%.

---

### Swarm Optimization Rules (avoid running full 7-agent swarm for L1-L2)

| Level | Max agents | Token budget | Parallel or sequential |
|-------|-----------|-------------|----------------------|
| L1 | 0 | 0 | N/A |
| L2 | 1 | ~5k | Single agent |
| L3 | 2 | ~15k | Parallel |
| L4 | 3-4 | ~40k | Parallel |
| L5 | 7 | ~100k | Parallel + synthesis |

**Anti-pattern:** Running 7 agents on a typo fix = wasted 95k tokens. Running 0 agents on a government application = quality failure. Level declaration prevents both.

---

### Self-Assessment Checklist (before CTO delivers ANY L3+ output)

```
□ Did I classify complexity level honestly?
□ Did I identify where my knowledge is weakest?
□ Did I route to the right verification agents for THIS task type?
□ Have agents run and returned findings?
□ Have I incorporated agent findings (not just noted them)?
□ Is my confidence NOW ≥85%?
□ If output is AZ-language → did 2+ native/expert agents review?
□ If output is external-facing → did Cultural Intelligence sign off?
```

If any checkbox is NO → do not deliver. Run verification first.

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
QUESTION: NONE  ← default is NONE. A CEO question requires written proof team couldn't answer it.
                   CEO mandate 2026-04-02: "если ты сам можешь это решить то ко мне не обращайся."

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
| Asked CEO something team could answer | CEO mandate 2026-04-02 | "если ты сам можешь это решить то ко мне не обращайся" — team answers first, CEO only for genuine blockers |
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
| **v6.0** | **2026-04-01** | **Five additions from cross-repo analysis (ZEUS + MindShift + Claude Code patterns): (1) Step 0b "Detect+Read": read SESSION-DIFFS.jsonl + code-index.json before proposing, declare N changes since last run. (2) Proposals MUST include trigger_reason (WHY NOW, what recent event makes this timely). (3) Round-2 debate gate: if top proposal <35/50 AND delta to #2 <5 pts → mandatory Round 2. (4) Outcome verification: agent cannot mark DONE without running verify_outcome() or explicit manual verification steps. (5) Session-end skill evolution check: ≥5 trajectories per skill → auto-suggest improvements.** | **Session 78 — Cross-repo analysis of ZEUS (adaptive executor), MindShift (v6.0 protocol), Claude Code patterns. Found gaps: agents declaring DONE without proof, proposals with no "why now", no outcome verification gate.** |
| **v7.0** | **2026-04-02** | **Universal Complexity Levels (L1-L5) for ALL task types — code + content + formal documents. Confidence Gate: CTO self-assesses before delivering L3+ output. Auto-Routing Table: AZ formal document = L4 (2 grammar agents mandatory), Government application = L4 (Cultural Intelligence + grammar + Communications Strategist). Swarm Optimization: token budgets per level (L1=0, L5=100k). Self-Assessment Checklist before any L3+ delivery. Step 1.0.3b SESSION CONTEXT INJECTION added as blocking step — dynamic session context MUST be injected into every agent prompt. Root cause: 29 grammar errors in startup.az application + agents producing 50% correct output due to missing session context.** | **CEO challenge 2026-04-02: "почему ты не сделал этого сразу?" — protocol had size classes for code only. Non-code quality verification and dynamic agent context were missing entirely.** |
| **v7.1** | **2026-04-02** | **15 structural and enforcement gaps closed from 5-agent protocol audit (score 66/100 → targeting 85/100): Header fixed, Phase 0.7 moved to correct position, classification systems merged (MICRO/SMALL/MEDIUM/LARGE unified with L1-L5), EXPEDITED mode added, HOTFIX security minimum defined inline, MICRO FASTPATH capped for auth/scoring/external content, Required Reads reorganized to 3-tier priority, named roles at Batch Lock (C3_REVIEWER + CROSS_QA_AGENT), auto-routing catch-all row + 3 missing rows, independent agent confidence for L4/L5, Round-2 debate output format defined, Step 0b fallback for missing files, Mid-Batch Direction Change protocol.** | **5-agent audit 2026-04-02: Architecture + QA + Risk Manager + Readiness Manager + Product scored protocol 66/100. Enforceability = 11/20 (worst dimension). Root cause: CLASS 3 recurring 15 times despite written rules.** |

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
