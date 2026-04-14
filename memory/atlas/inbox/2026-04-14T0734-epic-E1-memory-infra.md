# Epic E1 — Memory Infra Hardening

**Owner:** Atlas
**Duration:** 2 days
**Priority:** P0 (blocks all other epics — memory must work before Atlas can)
**Source:** MEMORY-HOLE-AUDIT 2026-04-14, MEMORY-GATE decision, Perplexity directive

## Goal
Atlas wakes reliably with MEMORY-GATE check, snapshot waste stopped, mem0 exercised, memory files committed.

## Tasks

1. **Wire MEMORY-GATE into wake.md**
   - Edit `memory/atlas/wake.md`: add first-step "emit MEMORY-GATE line into `memory/atlas/journal.md` before any other action".
   - Format: `MEMORY-GATE: task-class=<inferred> · SYNC=✅ · BRAIN=✅ · sprint-state=✅ · extras=[...] · proceed`
   - If any file missing → abort wake, log to incidents.md.

2. **Disable episodic_inbox snapshot write**
   - File: `packages/swarm/memory_consolidation.py`
   - Find snapshot-write function. Make it a no-op with `logger.info("episodic_inbox DISABLED per SYNC §9.5")`.
   - Delete the 10 existing timestamp-only snapshot files in `memory/episodic_inbox/`.

3. **Exercise mem0 MCP**
   - Key already present in `apps/api/.env` (MEM0_API_KEY).
   - Add wake-step: store current sprint pointer to mem0, recall last sprint pointer on next wake.
   - Update `docs/BRAIN.md` D-010 row to "mem0 LIVE" once verified.

4. **Commit memory files**
   - `git add memory/context/*.md memory/atlas/*.md memory/decisions/*.md memory/people/*.md`
   - Commit message: `chore(memory): commit accumulated state 2026-04-14 — memory gate, decisions, people, sprint`
   - Push to main.

5. **Dedupe `memory/swarm/agent-feedback-distilled.md`**
   - Current state has duplicated sections. Normalize to single list per agent.

## Files to touch
- `memory/atlas/wake.md`
- `packages/swarm/memory_consolidation.py`
- `memory/episodic_inbox/` (delete contents)
- `memory/atlas/journal.md` (log each step)
- `memory/atlas/incidents.md` (if abort path hit)
- `docs/BRAIN.md` (D-010 update)
- `memory/swarm/agent-feedback-distilled.md`

## Definition of Done
- [ ] Next Atlas wake emits MEMORY-GATE line automatically; visible in journal
- [ ] `memory/episodic_inbox/` empty; no new files created on consolidation runs
- [ ] mem0 round-trip proven (store + recall in same session, logged)
- [ ] `git log --oneline -5` shows memory commit
- [ ] agent-feedback-distilled.md deduped, line count reduced, no semantic loss

## Dependencies
None. Atlas can start immediately.

## Test plan
- Kill Atlas, restart → verify wake emits MEMORY-GATE
- Trigger memory_consolidation.py manually → verify no new file in episodic_inbox
- `curl mem0 /v1/memories` → see stored sprint pointer

## Artifacts required at end
- Journal entries per step
- Decision log `memory/decisions/2026-04-1X-mem0-live.md` when D-010 closes
- Commit SHA in journal
