# Atlas Sync Protocol
**Version:** 2.0 | **Date:** 2026-04-13 | **Authority:** Atlas (CTO)

## Hierarchy — CEO decided 2026-04-13

| Role | Instance | Authority |
|------|----------|-----------|
| **CEO** | Yusif | Strategy, vision, final veto. Everything else delegated. |
| **CTO (lead)** | Atlas (Claude Code) | All technical and operational decisions. Accepts or rejects handoffs. Sets priorities. Executes. |
| **Research advisor** | Cowork (Claude Opus) | Researches, monitors via MCP, proposes handoffs. Atlas decides what to execute. |

**Key change from v1.0:** Cowork is no longer "coordinator." Atlas leads. Cowork advises. CEO is stakeholder, not message bus.

---

## Sync rules for Claude Code (MANDATORY)

When Claude Code starts a session, BEFORE any work:
```
1. Read packages/atlas-memory/STATE.md (current state, blockers, what Cowork did)
2. Read packages/atlas-memory/sync/cowork-state.md (latest Cowork instructions)
3. Read docs/COMMUNICATION-LAW.md (radical truth + democracy + caveman — MANDATORY)
4. If STATE.md has a "Handoff" section → that is your task. Execute it.
```

When Claude Code finishes a session, BEFORE closing:
```
1. Update packages/atlas-memory/sync/claudecode-state.md:
   - What was done (files changed, commits, deploys)
   - What failed and why
   - What's next
   - Any blockers for Cowork to investigate

2. Update packages/atlas-memory/sync/heartbeat.md:
   - Instance: Claude Code
   - Timestamp
   - Last action (1 line)

3. Update packages/atlas-memory/STATE.md:
   - "Now" section with current reality
   - "Blockers" if any new ones
   - Clear the "Handoff" section (task consumed)

4. Update memory/swarm/SHIPPED.md if new code was written
```

---

## Sync rules for Cowork (MANDATORY)

When Cowork starts a session:
```
1. Read packages/atlas-memory/STATE.md
2. Read packages/atlas-memory/sync/claudecode-state.md (what Atlas did)
3. Read packages/atlas-memory/sync/heartbeat.md (who wrote last, when)
4. Reconcile: update STATE.md if Claude Code's work changed reality
```

When Cowork writes a handoff for Claude Code:
```
1. Write the full prompt to packages/atlas-memory/sync/cowork-state.md
2. Add a "## Handoff" section to STATE.md with:
   - Task name
   - Acceptance criteria (PASS/FAIL)
   - Files to read before starting
   - Files to NOT touch
   - Expected output
3. Update timeline
```

---

## Handoff prompt template (Cowork → Claude Code)

Every handoff must include:

```markdown
# Handoff: [Task Name]
**From:** Cowork | **Date:** [date] | **Priority:** [P0/P1/P2]

## Context
[Why this task matters. What changed. What Cowork found.]

## Task
[Exact scope. What to do. What NOT to do.]

## Acceptance Criteria
- [ ] AC1: [specific, measurable, PASS/FAIL]
- [ ] AC2: ...
- [ ] AC3: ...

## Files to Read First
- [file1] — why
- [file2] — why

## Files to NOT Touch
- [file] — reason

## Risks
- [risk1] — mitigation
- [risk2] — mitigation

## On Completion
1. Update sync/claudecode-state.md
2. Update sync/heartbeat.md
3. Update STATE.md
4. Update SHIPPED.md if new code
```

---

## Conflict resolution

If both instances updated STATE.md:
- Cowork's "CEO Directives" section wins (Cowork talks to CEO directly)
- Claude Code's "Production" section wins (Claude Code runs tests/deploys)
- For "Blockers": merge both, deduplicate
- For "What X Should Do Next": Cowork's version wins (coordinator decides priorities)

---

## What this replaces

Before this protocol, sync was ad-hoc:
- heartbeat.md existed but was stale for 40+ sessions
- No structured handoff format
- No mandatory read-on-wake
- No mandatory write-on-close
- CEO had to manually describe what the other instance did

This protocol makes CEO a trigger, not a relay.
