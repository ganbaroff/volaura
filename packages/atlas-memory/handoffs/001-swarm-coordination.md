# Handoff 001: Swarm Coordination Architecture
**From:** Cowork (coordinator) | **Date:** 2026-04-12 | **Priority:** P0

## Context
CEO prompted an audit of the swarm. You found the truth yourself: "Рой — система обнаружения, не координации. Восемь людей в одной комнате с завязанными глазами." CEO has been teaching us PM practices (charter, WBS, sprints, retros, backlog) but zero are implemented in code. The .md files describe what should happen. The code does asyncio.gather of 8 parallel agents with identical context.

Your own audit found:
- Coordinator has DAG capability → autonomous_run.py doesn't use it
- agent-state.json has `blockers` field → nothing reads it
- proposals.json is atomic, no threading, no references
- shared-context.md is a reference, not a communication channel

## Task
Transform the swarm from detection-only to coordinated execution. NOT a rewrite — surgical changes to existing code.

**Phase 1 (this session):**
1. Add a backlog system: `packages/swarm/backlog.py` — tasks with status (todo/in_progress/done/blocked), assignee (agent perspective), dependencies, acceptance criteria. Storage: `memory/swarm/backlog.json`.
2. Modify `autonomous_run.py` to use coordinator's DAG: agents that depend on another agent's output run AFTER that agent completes, not in parallel. Use the existing coordinator infrastructure.
3. Make agents see each other's findings: when agent A finishes, agent B (if dependent) gets agent A's output injected into its prompt. This is the "group chat" pattern — sequential where needed, parallel where independent.
4. Fix the $50 budget reference on line 288 of autonomous_run.py → "$200+/mo"

**Phase 2 (next session):**
- Sprint cycle: agents plan → execute → retro within a single swarm run
- Blocker tracking: if agent writes a blocker, coordinator routes it to the agent best suited to resolve it
- Proposal threading: proposals reference parent proposals

**DO NOT:**
- Rewrite the entire swarm from scratch
- Change the model routing (NVIDIA → Groq → Gemini cascade works)
- Change the inbox protocol or proposal format (backward compat)
- Add new agent perspectives (8 is enough, coordinate them better)
- Create new governance .md files

## Acceptance Criteria
- [ ] AC1: `backlog.py` exists with Task model (id, title, status, assignee, deps, ac). Can add/update/query tasks. Has tests.
- [ ] AC2: `autonomous_run.py` runs agents in dependency order (DAG) when deps exist, parallel when independent. Coordinator's existing DAG code is used.
- [ ] AC3: Agent B's prompt includes Agent A's findings when B depends on A. Verifiable by reading the prompt construction.
- [ ] AC4: $50 → $200+ on line 288 of autonomous_run.py
- [ ] AC5: All existing tests still pass (749/749 backend green must hold)
- [ ] AC6: Updated files: sync/claudecode-state.md, sync/heartbeat.md, STATE.md, SHIPPED.md

## Files to Read First
- `packages/swarm/autonomous_run.py` — the main run loop (you already read it, but re-read for coordinator DAG code)
- `packages/swarm/coordinator.py` — has DAG infrastructure that autonomous_run.py ignores
- `packages/swarm/shared_memory.py` — existing shared memory (used for recent findings)
- `packages/swarm/inbox_protocol.py` — proposal format (don't break it)
- `packages/swarm/contracts.py` — FindingContract schema
- `packages/atlas-memory/sync/PROTOCOL.md` — sync rules for when you finish

## Files to NOT Touch
- `packages/swarm/tools/` — code_tools, constitution_checker, deploy_tools work fine
- `packages/swarm/perspective_registry.py` — agent perspectives are fine
- `memory/swarm/proposals.json` — format must stay backward-compatible
- `.github/workflows/swarm-daily.yml` — cron schedule is fine

## Risks
- **Risk:** Breaking existing daily swarm run → **Mitigation:** Run swarm locally after changes to verify proposals.json still populates
- **Risk:** DAG ordering adds latency → **Mitigation:** Only use DAG when explicit deps exist. Default = parallel (current behavior)
- **Risk:** Prompt size blowup from injecting findings → **Mitigation:** Cap injected findings at 500 chars per dependency

## On Completion
1. Update `packages/atlas-memory/sync/claudecode-state.md` with what was done
2. Update `packages/atlas-memory/sync/heartbeat.md` (instance: Claude Code, timestamp, action)
3. Update `packages/atlas-memory/STATE.md` — clear Handoff section, update Now/Blockers
4. Update `memory/swarm/SHIPPED.md` — append new files
5. Commit with descriptive message. Push to main.
