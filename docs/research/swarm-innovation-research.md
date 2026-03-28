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

## Sprint Roadmap: B3-B6

### B3 (next): Reflexion traces + EvoSkill raw trajectories

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

**+ EvoSkill upgrade** (sentient-agi/EvoSkill): `skill_evolution.py` currently uses distilled summaries from `agent-feedback-distilled.md`. EvoSkill uses **raw failed trajectory logs**. Change: log full agent task traces to a structured `agent-trajectories.jsonl` file, feed those to `skill_evolution.py` alongside summaries. One-sprint change, closes the gap between our evolution engine and VOYAGER/EvoSkill state of the art.

### B4: VOYAGER verification gate for skills

Before new skills enter `memory/swarm/skills/`, require them to pass a simulated task:
1. `skill_evolution.py` proposes a new skill (currently goes straight to `skill-evolution-log.md`)
2. Run the skill against a synthetic scenario ("Given a proposal from a Security Agent, does this skill produce a structured output with: trigger, output, cross-refs?")
3. Only add to library if it passes — prevents library rot (current health: 70/100)

### B5: ADAS meta-agent (1 new agent/week)

ADAS (arXiv:2408.08435, ICLR 2025) — meta-agent writes new agents, tests them, promotes successful ones.
Our `agent-feedback-log.md` + `career-ladder.md` = already the archive ADAS needs.
Practical first step: weekly GitHub Action that:
1. Reads `agent-feedback-log.md` (failures) + `career-ladder.md` (promotions)
2. Asks Gemini: "Based on these patterns, design 1 new agent role that would catch what current agents missed"
3. Proposes new agent as a skill file + routing table entry
4. CTO reviews before activating

### B6: DSPy prompt optimization

Only after B3-B5 generate 50+ calibrated outcomes with proper trajectory logging.

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
| stanfordnlp/dspy | ~25k | Systematic prompt optimization (SIMBA/MIPROv2). Needs 20-50+ labeled examples. | B6 — implement after 50+ calibrated outcomes. |
| noahshinn/reflexion | NeurIPS 2023 | Verbal post-mortems stored as episodic memory. 91% vs 80% on HumanEval. | B3. |
| sentient-agi/EvoSkill | ? | Skill discovery from raw failed trajectories. `skill_only` + `prompt_only` modes. Git branches for evolution history. | **B3** — closest architectural match to `skill_evolution.py`. Add raw trajectory logging. |
| ShengranHu/ADAS | ICLR 2025, arXiv:2408.08435 | Meta-agent writes new agents, tests them, promotes to archive. Outperforms hand-designed state-of-the-art. | **B5** — highest leverage. Our `agent-feedback-log.md` = the archive ADAS needs. |
| MineDojo/Voyager | arXiv:2305.16291 | Ever-growing skill library with self-verification gate before entry. Compositional skills. | **B4** — skill verification gate. Prevents library rot (current: 70/100). |
| Darwin Gödel Machine | arXiv 2025 | Population-based agent evolution with Archive Trees. SWE-bench 20%→50%. | Research-only for now. Our `autonomous_upgrade.py` is the linear version. |

---

## Framework Comparison Verdict (live research)

**Do not replace `packages/swarm/` with any external framework.**

Volaura's hand-coded swarm already has capabilities that no external framework provides:
- Multi-provider mixing (Groq + Gemini + DeepSeek) with dynamic dead-weight filtering
- Domain-weighted calibration via sliding accuracy window (AgentHive)
- MoA-style cross-group LLM synthesis (from ACL 2025 + MoA papers)
- Research loop with web grounding (WebResearcher → StructuredMemory)

What frameworks would ADD (only one is genuine):
- **LangGraph**: durable execution / checkpointing that survives Railway restarts mid-decision. Not a real problem at current 30-second decision timeout. **Consider if daily swarm run grows beyond 5 minutes.**
- Everything else: CrewAI/AutoGen/Swarm add nothing we don't already have, at the cost of framework lock-in.

**Confirmed by:** live comparison of framework capabilities vs `packages/swarm/engine.py` implementation.

---

## Temperature Finding (from swarm-freedom-architecture.md)

temp 0.7 → fake consensus, all "hybrid" verdicts
temp 1.0 → 2/5 convergent innovations (never at 0.7)

Rule: Strategic decisions → temp 1.0. Code review → temp 0.7.
**Status: Documented but not enforced in autonomous_run.py. B4 candidate.**
