# Swarm Engine Decision — Keep + Refactor
**Date:** 2026-04-13 | **By:** CTO (Cowork Session 8) | **Authority:** CEO granted full autonomy

## TL;DR
**Keep the custom engine. Refactor from 73 files to ~25. No framework replacement.**

Our swarm does something no off-the-shelf framework handles: **multi-provider LLM debate** across Cerebras, NVIDIA NIM, Groq, Gemini, DeepSeek simultaneously. Every alternative framework is designed for single-provider agent orchestration. Replacing the engine would mean re-building the exact same multi-model debate logic inside someone else's abstraction layer.

---

## Alternatives Evaluated

| Framework | Stars | Strengths | Why NOT for us |
|-----------|-------|-----------|----------------|
| **Ruflo** (ruvnet) | ~6K | Claude-specific, 314 MCP tools, WASM kernel | **Claude-only.** Violates CLAUDE.md: "Never use Claude as swarm agent." Our swarm intentionally uses diverse non-Claude models. |
| **OpenManus** | 72K | General-purpose agent, MetaGPT team | **Task execution framework**, not multi-model debate. Designed for single-agent complex tasks, not 13-perspective swarm. |
| **CrewAI** | ~40K | Role-based, task delegation, Flows+Crews | ADR-009 approved Phase 1 but never implemented. Good for role enforcement, but doesn't handle multi-provider routing (Cerebras/NVIDIA/Groq). |
| **AutoGen** (MS) | ~35K | Multi-party conversation | **Maintenance mode.** Microsoft shifted to Microsoft Agent Framework. Dead-end dependency. |
| **LangGraph** | ~15K | Graph workflows, production-grade | Best orchestration layer, but **doesn't replace** multi-model debate. Could wrap our engine as a node. |
| **OpenAgents** | ~5K | Workspace platform | Not an orchestration engine. Different use case (human-agent workspace). |
| **Claude Agent SDK** | N/A | Subagents, hooks, MCP, streaming | Already decided for Phase 2 (Cowork↔Atlas handoff). Not a swarm replacement — it's for structured agent delegation. |

## What Makes Our Swarm Unique (don't lose this)

1. **Multi-provider simultaneous execution** — 8 providers, 13 agents, 4-wave DAG
2. **EMA-weighted perspectives** — agents gain/lose influence based on judge scores
3. **Hive lifecycle** — PROBATIONARY→MEMBER→SENIOR→LEAD, competency exams
4. **Dead weight filtering** — auto-removes unreliable models from dispatch
5. **Proposals→Telegram→CEO** — full escalation pipeline with severity routing
6. **Research autonomy** — agents propose research topics, WebResearcher executes
7. **Structured memory** — 4-network system (World/Experience/Opinion/Failure)
8. **Diverse LLMs by design** — Cerebras Qwen3-235B, Gemini, Groq, NVIDIA NIM, DeepSeek

No framework provides items 1-4 out of the box.

## Decision: Refactor, Don't Replace

### Phase 1 — Clean (Handoff 006, P1)
Archive ~45 files that are dead code or superseded. Target: 73 → ~25 active files.

**KEEP (core engine):**
- `engine.py` — SwarmEngine v7
- `autonomous_run.py` — daily cron entry point
- `pm.py` — PM agent orchestration
- `inbox_protocol.py` — proposal management
- `perspective_registry.py` — EMA weights
- `agent_hive.py` — lifecycle management
- `structured_memory.py` — 4-network memory
- `middleware.py` — token counting, middleware chain
- `providers/` — all 8 provider implementations
- `tools/` — code_tools, constitution_checker, deploy_tools, llm_router, web_search
- `prompts.py` — prompt templates
- `swarm_types.py` — type definitions
- `contracts.py` — agent contracts
- `backlog.py` — task tracking
- `research.py` — WebResearcher
- `reflexion.py` — Reflexion traces
- `memory.py` + `memory_logger.py` + `memory_consolidation.py` — memory subsystem
- `session_end_hook.py` — session cleanup
- `tests/` — keep all tests

**ARCHIVE (dead/superseded):**
- `adas_agent_designer.py` — unused designer
- `agent_memory.py` — superseded by structured_memory
- `atlas_proactive.py` — superseded by atlas_memory
- `autonomous_upgrade.py` — self-upgrade (disabled)
- `board_heavy_run.py` — unused variant
- `code_index.py` — unused indexer
- ~~`coordinator.py`~~ — **KEEP**: used by autonomous_run.py mode=coordinator (line 1272)
- `discover_models.py` — one-time discovery script
- `emotional_core.py` — unused emotional model
- `execute_proposal.py` — disconnected from runtime
- `execution_state.py` — unused state tracker
- `heartbeat_gate.py` — old heartbeat
- `jarvis_daemon.py` — daemon concept, never deployed
- `migrate_ledger.py` — one-time migration
- `outcome_verifier.py` — unused verifier
- ~~`promote_proposals.py`~~ — **KEEP**: connected in swarm-daily.yml (line 124), written today
- `proposal_verifier.py` — unused verification
- `reasoning_graph.py` — v4 feature, partially integrated
- `recovery_strategies.py` — unused recovery
- `report_generator.py` — unused reporter
- `shared_memory.py` — superseded by structured_memory
- `simulate_users.py` — simulation tool, not runtime
- `skill_ab_tester.py` — unused A/B testing
- `skill_applier.py` — unused applier
- `skill_evolution.py` — unused evolution tracker
- `skills.py` + `skills_loader.py` — skill library (keep if v0Laura needs)
- `social_reaction.py` — unused social reaction
- `squad_leaders.py` — old leadership model
- `suggestion_engine.py` — unused suggestions
- `task_binder.py` + `task_ledger.py` — unused task system
- `team_leads.py` — superseded by agent_hive
- `telegram_ambassador.py` — keep if Telegram active
- `watcher_agent.py` — unused watcher
- `zeus_content_run.py` + `zeus_gateway.py` + `zeus_video_skill.py` — ZEUS features, not yet needed

### Phase 2 — Integrate (with Agent SDK, after Phase 1)
- Wrap SwarmEngine as MCP server → any Claude instance can call `swarm.run_debate(topic)`
- Replace Cowork↔Atlas handoff with Agent SDK subagent calls
- Add Langfuse instrumentation to all provider calls

### Phase 3 — LangGraph Wrapper (optional, after v0Laura)
- If v0Laura skill routing becomes complex, wrap skill→swarm→result flow as LangGraph graph
- Not urgent. Current `POST /api/skills/{skill_name}` is simple enough.

## Supersedes
- ADR-009 (CrewAI adoption) — status changed to **SUPERSEDED**. CrewAI was never implemented. Multi-provider requirement makes it unsuitable.

## Risk
- Refactoring 73→25 files could break the daily cron. Mitigation: Atlas runs full swarm test before + after.
- Archive doesn't mean delete. All files preserved in `packages/swarm/archive/`.
