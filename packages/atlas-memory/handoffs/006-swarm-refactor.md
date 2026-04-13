# Handoff 006 — Swarm Engine Refactor (73→25 files)
**Priority:** P1 | **From:** Cowork Session 8 | **To:** Atlas (Claude Code)
**Decision doc:** `packages/atlas-memory/knowledge/swarm-engine-decision-2026-04-13.md`

## Context
CEO granted full authority to rebuild the swarm engine. After researching 7 alternatives (Ruflo, OpenManus, CrewAI, AutoGen, LangGraph, OpenAgents, Claude Agent SDK), CTO decision: **keep custom engine, refactor from 73→25 active files**. No framework does multi-provider LLM debate (Cerebras + NVIDIA NIM + Groq + Gemini + DeepSeek simultaneously).

## Task
Move ~45 dead/superseded files from `packages/swarm/` to `packages/swarm/archive/`. Keep core engine intact.

## Files to KEEP (do NOT move these)
```
engine.py, autonomous_run.py, pm.py, inbox_protocol.py, perspective_registry.py,
agent_hive.py, structured_memory.py, middleware.py, prompts.py, swarm_types.py,
contracts.py, backlog.py, research.py, reflexion.py, memory.py, memory_logger.py,
memory_consolidation.py, session_end_hook.py, __init__.py,
coordinator.py (used by autonomous_run.py mode=coordinator, line 1272),
promote_proposals.py (connected in swarm-daily.yml, line 124)
providers/ (entire directory)
tools/ (entire directory)  
tests/ (entire directory)
skills.py, skills_loader.py (needed for v0Laura skill library)
telegram_ambassador.py (needed for CEO notifications)
```

## Files to ARCHIVE
```
adas_agent_designer.py, agent_memory.py, atlas_proactive.py, autonomous_upgrade.py,
board_heavy_run.py, code_index.py, discover_models.py, emotional_core.py,
execute_proposal.py, execution_state.py, heartbeat_gate.py, jarvis_daemon.py,
migrate_ledger.py, outcome_verifier.py, proposal_verifier.py,
reasoning_graph.py, recovery_strategies.py, report_generator.py, shared_memory.py,
simulate_users.py, skill_ab_tester.py, skill_applier.py, skill_evolution.py,
social_reaction.py, squad_leaders.py, suggestion_engine.py, task_binder.py,
task_ledger.py, team_leads.py, watcher_agent.py,
zeus_content_run.py, zeus_gateway.py, zeus_video_skill.py
```

## Steps
1. `git status` — confirm clean working tree
2. Move files listed above to `packages/swarm/archive/`
3. Run: `python -m packages.swarm.autonomous_run --mode=daily-ideation --dry-run` (if dry-run exists) or just verify imports
4. Run backend tests: `cd apps/api && python -m pytest -x`
5. Fix any import errors from archived files (update `__init__.py` if needed)
6. Run swarm tests: `cd packages/swarm && python -m pytest tests/`
7. Commit with message: "refactor(swarm): archive 35 dead modules (73→25 active files)"

## Acceptance Criteria
- [ ] `packages/swarm/` has ≤28 active .py files (excluding archive/, tests/)
- [ ] `python -c "from swarm.engine import SwarmEngine"` succeeds
- [ ] `python -c "from swarm.autonomous_run import main"` succeeds  
- [ ] Backend tests still pass (749/749)
- [ ] No imports reference archived files from kept files
- [ ] Daily cron workflow can still trigger (check .github/workflows/swarm-daily.yml)

## Risk
LOW. All archived files are already disconnected from the runtime (verified by reading engine.py imports). If anything breaks, `git checkout` the individual file back.
