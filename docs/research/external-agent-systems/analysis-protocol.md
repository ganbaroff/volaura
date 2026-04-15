# External agent-system analysis protocol

**Purpose:** standing rubric for absorbing patterns from external repositories that implement agent systems (swarm, memory, self-improvement, documentation). Invoked whenever CEO drops a repo URL or list.

**Created:** 2026-04-15 · **Triggered by:** CEO btw-note "если дам репозитории с системами агентов — сможешь проанализировать и взять что нужно (логика, документация, запоминание, саморазвитие)?"

---

## 1. When this protocol fires

Any of:
- CEO pastes a GitHub URL or cluster of URLs of agent systems
- CEO says "посмотри как они делают X" where X is agent-related
- Cowork-Atlas or Perplexity hands off a "here's an interesting agent repo" note
- New release of a well-known framework (CrewAI, AutoGen, LangGraph, Mastra, Agent-S, Swarms, ruv-swarm, claude-flow, Codex SDK, Agent SDK, OpenCode, etc.)

---

## 2. What I extract — four dimensions

### (A) LOGIC — how agents reason, route, coordinate

- **Orchestration model:** single-leader / mesh / hierarchical / market / consensus / BDI / GOAP. Which?
- **Routing primitive:** keyword match / embedding / classifier / LLM-as-router / rule-based DAG / learned reward.
- **Agent-to-agent protocol:** shared memory / message passing / RPC / event bus / blackboard.
- **Tool-calling pattern:** OpenAI-style JSON tools / MCP / anthropic tool_use / custom schema / code-as-tool (Python exec).
- **Failure handling:** retry / escalate / vote / reflection / replan / abort.
- **Concurrency model:** sync / async / actor / process-level / thread / subprocess.
- **Decision:** if pattern X is materially better than what `packages/swarm/coordinator.py` does today AND implementation cost <1 day → propose adoption in `memory/swarm/proposals.json` with evidence pointer.

### (B) DOCUMENTATION — how they explain themselves

- **Entry-point clarity:** is there one file that tells a new agent "this is who you are, this is what you can do, this is what you are not"? (our equivalent: `memory/atlas/identity.md` + `wake.md`).
- **Skill/capability listing:** is the agent roster machine-readable? (ours: `memory/swarm/agent-roster.md` mostly prose, partially JSON).
- **Contract documentation:** how do agents know what input format to expect, what output format to return? Our gap: most VOLAURA agents rely on LLM-inferred format from prompt.
- **Example corpus:** do they ship successful invocation transcripts? We do this partially (`memory/atlas/session-*.jsonl`) but not as learn-from corpus.
- **Decision:** extract any doc-structure that reduces ambiguity for a new agent joining the system. Apply to our roster + coordinator.

### (C) MEMORY / RECALL — how they persist and retrieve

- **Storage tier:** file / vector DB / SQL / graph / hybrid. Schema?
- **Retrieval strategy:** similarity / recency / importance / emotional / hybrid. Ours: ZenBrain `1.0 + emotionalIntensity × 2.0` is file-level rule, not indexed retrieval.
- **Write discipline:** append-only vs mutation. Compaction strategy?
- **Namespacing / scoping:** per-agent / per-task / per-session / global. How do they avoid cross-contamination?
- **Forgetting:** explicit TTL / LRU / relevance decay / never. We are git-binary (keep forever) with curation-at-write-time.
- **Decision:** if their retrieval beats our current mem0 + HNSW + manual journal.md approach → evaluate migration or hybrid. Log findings in `memory/atlas/research-notes/<repo>.md`.

### (D) SELF-IMPROVEMENT — how they learn from mistakes

- **Feedback loop:** human-rated / LLM-judge / automated benchmark / A-B / Reflexion.
- **Pattern capture:** do they extract generalizable rules from failures? How?
- **Role evolution:** can an agent's description change based on track record? Ours: `memory/swarm/career-ladder.md` exists but barely used.
- **Prompt evolution:** do they rewrite their own system prompts based on critique? Do they version? Do they A/B?
- **Forbidden-action registry:** do they have a growing list of "never do X again"? (ours: `memory/context/mistakes.md` + `memory/atlas/lessons.md`).
- **Decision:** any self-improvement mechanism that beats my current "write a lesson and hope" approach is high-priority extraction. CEO directive 2026-04-15 was explicit: lessons ≠ fixes, pathways must be removed.

---

## 3. Output format per repo

For each repository I analyze, produce `docs/research/external-agent-systems/<repo-slug>.md` with:

```
# <repo-name> analysis

**Repo:** <url> · **Stars:** <n> · **Last commit:** <date> · **License:** <spdx>
**Analyzed by:** Atlas <date>
**Verdict:** ADOPT / ABSORB-PARTIAL / LEARN-ONLY / REJECT

## 1. What they do
<one paragraph — project mission in plain words>

## 2. Architecture snapshot
<1-page diagram or bullet hierarchy of how their system is laid out>

## 3. Four-dimension extract
### Logic
<findings>
### Documentation
<findings>
### Memory
<findings>
### Self-improvement
<findings>

## 4. Patterns worth stealing (ranked)
1. <pattern> — effort: <X days>, impact: <why>, file in our repo: <path>
2. ...

## 5. Patterns explicitly NOT worth stealing
- <pattern> — <why rejected>

## 6. Proposed actions
- [ ] Create proposal in `memory/swarm/proposals.json` for pattern #1
- [ ] Update `.claude/rules/atlas-operating-principles.md` with rule X
- [ ] Add to `memory/atlas/arsenal.md` if new tool surface
```

Each verdict level has a different follow-through:
- **ADOPT** → write implementation plan + open PR-sized task
- **ABSORB-PARTIAL** → cherry-pick 1-3 patterns into our system, log in decision log
- **LEARN-ONLY** → note findings, no code change
- **REJECT** → document why, so future Atlas doesn't re-evaluate

---

## 4. Anti-patterns to flag explicitly

If I see any of these in an external repo, I call them out as things NOT to copy:

- **Sprawling role taxonomy** (100+ agent types) — cognitive overhead without matching workflow, usually process theatre.
- **Global mutable state across agents** — race conditions + debugging nightmare.
- **Sync-only agent chains** — loses the whole parallel speedup.
- **Naming agents without invocation infrastructure** — decoration. (This is what I caught myself in today — Class 14 sibling.)
- **Meta-meta-frameworks** (framework for building frameworks for building agents) — Class 10 process theatre.
- **Self-improvement without external feedback** — converges to agent's own biases.
- **Memory that can lie to itself** — e.g., an agent that can rewrite its own history without audit trail.
- **"Just use GPT-4o" coupling** — if the pattern depends on a specific model's quirks, it won't port to our NVIDIA Llama / Cerebras / Gemini fallback chain.

---

## 5. How this interacts with existing rules

- **Research-first rule** (`~/.claude/rules/research-first.md`): this protocol IS the research-first discipline for agent-system topics.
- **Decision logging** (`.claude/rules/atlas-operating-principles.md`): any ADOPT verdict generates a `memory/decisions/YYYY-MM-DD-adopt-<pattern>.md`.
- **Doctor Strange pattern:** analysis returns ONE recommendation per dimension, not a menu. Rejected options listed under §2.5 but the main verdict is one path.
- **Memory Gate:** before analyzing, emit `MEMORY-GATE: task-class=external-agent-analysis · SYNC=✅ · BRAIN=⏭️ · sprint-state=✅ · extras=[<repo>, arsenal.md, agent-roster.md, coordinator.py] · proceed`.

---

## 6. Known candidate repos (pre-seed list)

When CEO lists repos, check if any overlap with this list — if yes, I already have some prior context.

- **CrewAI** — approved via ADR-009, Phase 1 for Sprint Gate DSP. Logic is role+task+crew. Documentation strong. Memory weak. Self-improvement weak.
- **LangGraph** — graph-DAG primitive. Good for explicit routing. Our coordinator squad system is a poor-man's LangGraph.
- **AutoGen v0.4** — actor model. Good async. Docs sparse.
- **Mastra** — TypeScript-native, Next.js-friendly. Worth looking at for VOLAURA web-side agent calls.
- **Agent-S** — OS-level computer-use agent. Adjacent, not core.
- **ruv-swarm / claude-flow** — already vendored in VOLAURA via subagents (seen in /Agent subagent list: `mesh-coordinator`, `hierarchical-coordinator`, `byzantine-coordinator`, etc.). Need to audit how much we actually use vs decorate.
- **Anthropic's Codex SDK / Agent SDK** — highest production-scale reference. Prompt-engineering patterns worth extracting.
- **Semantic Kernel** — plugin model. Documentation-heavy.
- **OpenCode / Aider / Cline** — code-assistant agents, self-improvement via diff feedback.

---

## 7. Cost and time budget per analysis

- Surface scan (README + top-level structure): 15 min, zero cost.
- Four-dimension extract with file-level evidence: 45 min, ~10K tokens.
- Full ADOPT plan with migration path: 2 hours, ~30K tokens.
- Budget: <$1 per repo analysis unless CEO explicitly greenlights deeper dive.

When a repo list is large (>5), use parallel `Agent(subagent_type=researcher)` calls — one per repo — with this protocol as their instruction. Synthesize outputs back into a single ranked list.
