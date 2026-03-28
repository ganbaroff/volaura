# Swarm Innovation Research — 2026-03-29

**Session:** 63 | **Protocol:** TASK-PROTOCOL v2.0 | **Agents used:** 5 research + 1 adversarial

---

## Key Finding: Two Isolated Swarms

`autonomous_run.py` (runs daily) and `engine.py` (never runs automatically) are architecturally separate.
80% of the swarm's sophistication (ReasoningGraph, HiveExaminer, ResearchLoop, AutonomousUpgrade) is built but not activated.

---

## What Was Implemented (Sprints B1-B2)

### B1: StructuredMemory Persistence
- **File:** `packages/swarm/structured_memory.py`
- **Change:** `SWARM_DATA_DIR` env var support. GitHub Actions now sets `memory/swarm/structured`.
- **Impact:** Hindsight (arXiv:2512.12818) shows 83.6% vs 39% with structured memory. We were getting 39% because memory was lost after every runner.
- **File:** `.github/workflows/swarm-daily.yml` — `git pull --rebase` prevents concurrent push conflict.

### B2: Convergent Idea Detection
- **Files:** `packages/swarm/inbox_protocol.py`, `packages/swarm/autonomous_run.py`
- **Change:** Post-hoc Jaccard word overlap (threshold=0.35) detects proposals that emerged independently from 2+ agents.
- **Impact:** Convergent ideas = highest quality signal. Now flagged with `convergent: true` + sent to Telegram with 🎯.
- **Why post-hoc (not real-time):** Adversarial critic correctly identified anchoring risk if agents see each other's proposals before submitting. Post-hoc avoids herding.

---

## Next Sprint: B3 (Reflexion-style mistakes.md)

**Based on:** Reflexion paper (arXiv:2303.11366, NeurIPS 2023) — 91% vs 80% on HumanEval.

**Current state:** `mistakes.md` stores lessons (conclusions) without the evidence (input/output trace).
**Target state:** When `agent_memory.py` logs `was_correct=False`, also store:
- Full agent prompt (what it received)
- Full agent response (what it returned)
- What the correct answer was (post-calibration)

**Implementation:**
1. In `agent_memory.py:log_experience()` — add `full_prompt: str` and `full_response: str` optional fields
2. In `engine.py` — pass prompt+response when logging incorrect outcomes
3. In `get_context_for_agent()` — include trace for WRONG entries: "You wrote: X. The correct answer was: Y."

**Expected outcome:** Agents stop repeating known mistakes because they see the full failure trace, not just the lesson label.

---

## Deferred: Decision Table

| Innovation | Why Deferred | Prerequisites |
|-----------|-------------|---------------|
| ReasoningGraph in daily run | Data model mismatch (AgentResult vs dict). 2x API cost. | Refactor `_call_agent()` to return `AgentResult` objects |
| AutonomousUpgrade in Actions | Ephemeral backup (no recovery if job crashes). Self-classified risk. | Persistent backup (S3 or git-committed), independent risk classifier |
| DSPy prompt optimization | No labeled training data. CEO approval ≠ quality signal. Agents drift to Product domain. | 50+ calibrated proposal outcomes with outcome tracking pipeline |
| Darwin Gödel Machine (arXiv 2025) | Research-only. Our `autonomous_upgrade.py` is linear; DGM requires population/Archive Trees. | Extend autonomous_upgrade to population model; significant architecture work |

---

## External Repos Found (live research, 2026-03-29)

| Repo | Stars | What It Does | Our Verdict |
|------|-------|-------------|-------------|
| mem0ai/mem0 | ~37k | Hybrid memory (vector + KV + graph). MCP server. Supabase/pgvector backend. agent_id scoping. | Our StructuredMemory is more domain-specific. Add if we need MCP integration for Claude Code to query swarm memory directly. |
| getzep/graphiti | ~20k | Temporal knowledge graph (arXiv:2501.13956). Facts have temporal validity windows. 94.8% DMR benchmark. Needs Neo4j (separate infra). | **B4 candidate** — `agent-feedback-log.md` is append-only; Graphiti would enable "Session 48 finding superseded by Session 51" without deletion. |
| letta-ai/letta | ~16k | OS-inspired memory hierarchy (core/archival/episodic). `.af` agent-file format — serialized agent state. | Skip for now (requires running Letta server). `agent-file` format maps onto our `agent-roster.md` concept — revisit when agents need portable state. |
| topoteretes/cognee | ~? | ECL pipeline (Extract→Cognify→Load). Reads .md files natively. Cross-agent knowledge sharing. | Can ingest existing `memory/swarm/` markdown into queryable graph. Low migration effort. Evaluate if semantic search over swarm memory becomes a bottleneck. |
| MemTensor/MemOS | ~? | MemCubes (arXiv:2507.03724, EMNLP 2025). OpenClaw Plugin = "Persistent skill memory for cross-task skill reuse and evolution." 159% improvement in temporal reasoning. | **Conceptually identical to our skill-evolution-log.md** — but automated. **B4-B5 candidate**. Linux-ready. |
| stanfordnlp/dspy | ~25k | Systematic prompt optimization (SIMBA/MIPROv2). Needs 20-50+ labeled examples. | Implement after 50+ calibrated outcomes exist. |
| noahshinn/reflexion | NeurIPS 2023 | Verbal post-mortems stored as episodic memory. 91% vs 80% on HumanEval. | Implement as B3. |
| Darwin Gödel Machine | arXiv 2025 | Population-based agent evolution with Archive Trees. SWE-bench 20%→50%. | Research-only for now. Our `autonomous_upgrade.py` is the linear version. |

---

## Temperature Finding (from swarm-freedom-architecture.md)

temp 0.7 → fake consensus, all "hybrid" verdicts
temp 1.0 → 2/5 convergent innovations (never at 0.7)

Rule: Strategic decisions → temp 1.0. Code review → temp 0.7.
**Status: Documented but not enforced in autonomous_run.py. B4 candidate.**
