# TASK PROTOCOL v7.1 — Quick Reference Card

**For fast lookup during execution. Full protocol: `docs/TASK-PROTOCOL.md`**
**Updated: 2026-04-02**

---

## 5-Step Flow (which one are you in?)

```
CEO says "загрузи протокол и делай"    →  TEAM PROPOSES
CEO says "что дальше / propose"        →  CTO PLAN
CEO says "срочно / P0"                 →  HOTFIX  (keep security 4-box)
CEO says "быстро / today"              →  EXPEDITED (1 critique round, keep security)
```

---

## Before EVERY Batch (2 minutes)

```
□ Read: sprint-state.md → WHERE ARE WE
□ Read: mistakes.md → what NOT to repeat
□ Read: SHIPPED.md → what code EXISTS
□ Declare flow type (above)
□ Step 0a: SWARM RETROSPECTIVE (mandatory, skip only for HOTFIX)
  → 2 external models critique previous sprint in parallel
  → 3 questions: what went wrong / what pattern repeats / what to change
  → CTO documents: "Swarm retro: [findings]. Adjusting: [what]."
□ Step 5.4: LLM PROVIDER CHECK (if swarm ≥3 agents)
  → Read .env → assign different providers → declare assignments
□ Phase 0.7 Sprint Gate DSP → if "загрузи протокол"
```

---

## 3-Question DoD (Pareto: covers 76.4% of defects)

```
Before marking ANY task DONE:

1. WHO ELSE REVIEWED?   → "Nobody" = NOT DONE
2. WHAT STEP FOLLOWED?  → "None" = NOT DONE
3. WHERE IS IT WRITTEN?  → "Nowhere" = NOT DONE
```

That's it. 3 questions > 15-item checklist at 0% compliance.

---

## Task Level (declare BEFORE executing)

| Level | Type | Agents needed |
|-------|------|--------------|
| L1 | ≤10 lines, not auth/scoring/external | None — FASTPATH |
| L2 | 10-50 lines OR internal doc | 1 domain agent |
| L3 | 50-200 lines OR LinkedIn post / partnership comms | 2 agents |
| L4 | 200+ lines OR AZ formal doc / gov application / investor pitch | 3-4 agents + confidence gate |
| L5 | Legal / ToS / production deploy / irreversible | Full 7-agent + CEO |

**Not in table? → Default L3. Never self-assign L1 for unknown type.**

---

## Before Launching ANY Agent (2 minutes)

```
□ SESSION CONTEXT filled (decisions today, what's done, CEO said what)
□ VOLAURA CONTEXT BLOCK pasted (what Volaura is, founder, budget)
□ "What's already decided" filled (prevents re-research)
□ Output format specified
```
**All 4 empty = CLASS 3 mistake. Takes 2 minutes, saves hours.**

---

## L3+ Confidence Gate (before delivery)

```
CONFIDENCE GATE:
  Task type + Level: [e.g., AZ formal doc, L4]
  CTO confidence: [%]  ← AZ language starts at 50%
  Agents verified: [list]
  Ready: YES (≥85%) / NO
```

---

## HOTFIX Security Minimum (4 boxes — always)

```
□ Rate limiting preserved?
□ RLS policies unaffected?
□ Pydantic validation on new input paths?
□ Auth/session logic unchanged or Security agent reviewed?
```

---

## Batch Lock Declares (once, at lock)

```
C3_REVIEWER:    [agent]
CROSS_QA_AGENT: [agent — cannot be QA author]
BATCH_AGENT_COUNT: [N]
```

---

## "Done" requires

```
□ Tests RAN and PASSED (not just "tests exist")
□ User journey verified (not just unit tests)
□ Memory updated (SHIPPED.md / sprint-state.md)
□ Agent Completion Consensus (Step 4.0.5)
```

---

## Top 8 Failure Modes (CLASS reference)

| What happened | CLASS |
|--------------|-------|
| CTO decided without team | CLASS 3 (15x — dominant) |
| "Done" without test evidence | CLASS 1 |
| Memory not updated | CLASS 2 |
| Wrong field names assumed | CLASS 4 |
| Invented numbers | CLASS 5 |
| Agent launched without context | CLASS 3 |
| Efficiency Gate misapplied to agent routing | CLASS 3 |
| AZ document without grammar agents | CLASS 3 |

---

## Efficiency Gate SCOPE (violations in Session 82)

Efficiency Gate = "skip DSP if obvious." Applies ONLY to DSP.
**NEVER applies to:** Step 5.5 (agent routing) · Step 1.0.3 (context block) · Step 1.0.3b (session context)
