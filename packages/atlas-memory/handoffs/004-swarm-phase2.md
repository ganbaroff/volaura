# Handoff 004: Swarm Phase 2 — Sprint Cycle + Proposal Threading
**From:** Cowork (coordinator) | **Date:** 2026-04-12 | **Priority:** P1

**IMPORTANT:** Read `packages/atlas-memory/sync/PROTOCOL.md` FIRST. Follow the sync rules at session end.

## Context
Phase 1 (Handoff 001) delivered: `backlog.py` with Pydantic task model, 3-wave DAG execution in `autonomous_run.py`, findings injection between waves. The swarm can now **detect** issues AND **pass findings forward** between agents.

**Gap:** The swarm still can't:
1. Pick tasks from the backlog and execute them (backlog.py is disconnected from runtime)
2. Track which proposals led to which backlog tasks (no threading)
3. Route blockers to the right agent/squad for resolution

The existing infrastructure to build on:
- `packages/swarm/backlog.py` — task CRUD, DAG ordering, dependency tracking (177 lines, tested)
- `packages/swarm/coordinator.py` — keyword routing to squads, makes subtask plans
- `packages/swarm/orchestrator.py` — DAG-aware task runner with completion callbacks
- `packages/swarm/autonomous_run.py` — 3-wave agent execution (Wave 0→1→2 with findings)
- `packages/swarm/inbox_protocol.py` — proposal ingestion, Telegram escalation
- `memory/swarm/backlog.json` — 5 tasks (1 done, 4 todo)
- `memory/swarm/proposals.json` — canonical proposal history

## Task

### 1. Backlog → Runtime Bridge
Add a new mode to `autonomous_run.py`: `--mode=sprint-execute`

When triggered:
1. Load `backlog.json` via `Backlog` class
2. Call `backlog.ready()` to get tasks with all deps satisfied
3. For each ready task, use `coordinator.make_plan()` to break into subtasks
4. Execute subtasks via `orchestrator.run_all()`
5. On completion: update task status in backlog.json (`done` or `blocked` with reason)
6. Write results to `wave_findings` for downstream visibility

This connects the backlog (what to do) to the agent runtime (how to do it).

### 2. Proposal → Backlog Threading
When a swarm run produces proposals (via `inbox_protocol.py`), auto-create backlog tasks for `approved` proposals.

In `autonomous_run.py` post-processing (after proposals are written):
1. For each new proposal with severity HIGH/CRITICAL: create a `BacklogTask` with `source=proposal.id`
2. Set `acceptance_criteria` from the proposal title + recommendation
3. Set `assignee` from the proposal's `agent` field (the agent who found it knows most)

### 3. Blocker Routing
When a task in backlog has `status=blocked`:
1. Read `blocked_by` field (human-readable reason)
2. Use `coordinator.make_plan(blocked_by)` to find which squad can unblock it
3. Create a new backlog task: "Unblock: {original_task.title}" with `depends_on=[blocker_resolution_task.id]`
4. Original task's `depends_on` updated to include the resolution task

## Acceptance Criteria
- [ ] AC1: `python -m packages.swarm.autonomous_run --mode=sprint-execute` runs without error and processes `ready()` tasks
- [ ] AC2: After a sprint-execute run, `backlog.json` tasks that were processed are updated to `done` or `blocked` (not left as `todo`)
- [ ] AC3: New proposals with severity HIGH/CRITICAL auto-create corresponding `BacklogTask` entries with `source` field pointing to proposal ID
- [ ] AC4: `backlog.board()` output shows the sprint-execute results cleanly
- [ ] AC5: Unit test: mock agent runner, verify task flows through ready→execute→done pipeline
- [ ] AC6: Sync files updated per PROTOCOL.md

## Files to Read First
- `packages/atlas-memory/sync/PROTOCOL.md` — sync rules
- `packages/swarm/backlog.py` — the task model and operations (Phase 1 output)
- `packages/swarm/autonomous_run.py` — current runtime, add sprint-execute mode here
- `packages/swarm/coordinator.py` — make_plan() for routing tasks to squads
- `packages/swarm/orchestrator.py` — DAG runner with completion callbacks
- `packages/swarm/inbox_protocol.py` — where proposals are created (add threading here)

## Files NOT to Touch
- `packages/swarm/pm.py` — synthesis layer, not relevant to this task
- `packages/swarm/engine.py` — core agent engine, don't change
- `apps/api/` — no backend changes
- `apps/web/` — no frontend changes

## Implementation Hints
- `Backlog.ready()` already returns tasks with satisfied deps — use it directly
- `coordinator.make_plan(task.title)` routes by keywords — task titles should be descriptive
- `Orchestrator.on_complete` callback is where to update backlog task status
- Keep sprint-execute idempotent: if a task is already `done` or `in_progress`, skip it
- Cap concurrent tasks at 3 to control LLM API costs

## Risks
- **Risk:** sprint-execute picks up tasks with no clear agent instructions → **Mitigation:** Only process tasks with non-empty `acceptance_criteria`
- **Risk:** Blocker routing creates infinite loops (task A blocks B blocks A) → **Mitigation:** Check for cycles in `depends_on` before adding new deps
- **Risk:** LLM API cost from executing multiple agents per task → **Mitigation:** Cap at 3 concurrent tasks, use cheapest model (Cerebras/Ollama first per Constitution)

## On Completion (from PROTOCOL.md)
1. Update `packages/atlas-memory/sync/claudecode-state.md`
2. Update `packages/atlas-memory/sync/heartbeat.md`
3. Update `packages/atlas-memory/STATE.md` — update Now/Blockers
4. Update `memory/swarm/SHIPPED.md` if new code
