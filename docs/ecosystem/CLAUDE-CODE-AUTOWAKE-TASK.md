# CLAUDE CODE — ATLAS AUTO-WAKE TASK

**Purpose:** run Atlas every 30 minutes autonomously from Claude Code on Yusif's machine. Atlas wakes, reads memory, moves one unit of work forward, logs, sleeps.

**Target runtime:** Claude Code CLI (not Cowork — Cowork sessions are interactive, this is cron-style).

**Recommended interval:** **30 minutes**, not 15. Reasoning:
- 15 min = ~96 runs/day = massive API spend + context fragmentation. Each wake still needs to read BRAIN.md + sprint-state.md + heartbeat.md before acting — that's ~5–8k tokens of setup before any work. At 15 min cadence, 60%+ of tokens are overhead.
- 30 min = 48 runs/day = human-scale heartbeat. Enough to catch prod drift, not so tight that it burns budget on reads.
- If a P0 arises mid-gap, Yusif pings manually. Cadence is a floor, not a ceiling.

---

## THE PROMPT TO PASTE INTO CLAUDE CODE

Paste the block below as a scheduled task. Claude Code's `schedule` skill handles the cron.

```
# Atlas Auto-Wake — every 30 minutes

Run the Atlas wake protocol:

1. READ in order:
   - docs/BRAIN.md
   - memory/atlas/wake.md
   - memory/atlas/heartbeat.md
   - memory/context/sprint-state.md
   - docs/ecosystem/SYNC-2026-04-14.md (sections 2.4, 3, 4)

2. CHECK production health:
   - curl -s -o /dev/null -w "%{http_code}" https://api.volaura.com/health
   - If non-200, log to memory/atlas/incidents.md as INC-XXX with timestamp, write one-line summary to memory/atlas/heartbeat.md, then STOP and wait for Yusif. Do NOT attempt fixes on degraded prod without Yusif present.

3. CHECK open P0 items from SYNC §2.4:
   - If any P0 is blocked on Yusif → log "awaiting Yusif on D-XXX" to heartbeat.md, move to step 5.
   - If any P0 is Atlas-owned → pick the top one, move to step 4.

4. MOVE one unit forward:
   - Read the top Atlas-owned P0 or P1 item.
   - Do ONE reversible action toward closing it (draft migration, write test, refactor file, update doc).
   - Maximum 10 minutes of work per wake. If the task is bigger, slice it and do the first slice.
   - Write the diff / new file. Do NOT commit unless the item explicitly requires a commit (most don't — Yusif commits in batches).

5. LOG:
   - Append to memory/atlas/heartbeat.md: "HH:MM — [wake N] <one sentence summary of what moved>"
   - If no work was possible (all P0 blocked on Yusif): "HH:MM — [wake N] holding; awaiting Yusif on D-XXX"
   - If incident: "HH:MM — [wake N] INCIDENT INC-XXX, halted"

6. RESPECT rate limits and CEO sleep:
   - If current time (Baku / UTC+4) is between 01:00 and 09:00 → do steps 1, 2, 5 only. Skip step 4 unless it's a P0 incident. Yusif is asleep; don't generate notifications.
   - If heartbeat.md has no new Yusif entry in >72h → pause entirely, write "paused, no CEO signal 72h" and stop wake loop until next manual trigger.

7. NEVER:
   - Call Anthropic models as swarm agents (Article 0).
   - Commit without Yusif's sign-off (git is corrupted in sandbox, commits happen on Yusif's machine anyway).
   - Send Telegram / email without an explicit line item in the wake task.
   - Modify the Constitution.
   - Touch memory/decisions/ without an explicit decision event.
   - Exceed $1 in external API spend per wake without logging to spend-log.md first.

8. ON FIRST WAKE of a new UTC day:
   - Update memory/context/sprint-state.md Last-Updated header.
   - Append a one-line summary of yesterday's wakes to SHIPPED.md under "Autonomous heartbeat".

END of wake. Sleep until next scheduled run.
```

---

## SETUP (one-time, 2 minutes)

On Yusif's machine, from the repo root:

```bash
# 1. Ensure Claude Code has the schedule skill available
claude code plugins list | grep schedule

# 2. Create the scheduled task (claude code will prompt for the prompt body — paste the block above)
claude code schedule create \
  --name "atlas-autowake" \
  --interval "30m" \
  --timezone "Asia/Baku"

# 3. Verify
claude code schedule list
```

Alternative if Claude Code's schedule skill expects a file:

```bash
mkdir -p .claude/scheduled
cat > .claude/scheduled/atlas-autowake.md <<'EOF'
[paste the prompt block from above]
EOF

claude code schedule create --name atlas-autowake --file .claude/scheduled/atlas-autowake.md --interval 30m
```

---

## KILL SWITCH

If Atlas runs amok (unlikely but possible):

```bash
claude code schedule stop atlas-autowake
```

This pauses without deleting the config. Re-enable with `claude code schedule start atlas-autowake`.

---

## EXPECTED BEHAVIOR after enabling

- **First wake:** Atlas reads memory, confirms no P0 movable autonomously (D-001 needs Yusif to click Railway), logs "holding, awaiting Yusif on D-001", sleeps.
- **After Yusif closes D-001:** Atlas next wake picks up D-002 (Phase 1 migration apply), prepares the apply plan, drafts the SQL, writes to a staging file. Does NOT apply until Yusif greenlights.
- **During 01:00–09:00 Baku:** Atlas observes-only. No work, no pings. Yusif sleeps uninterrupted.
- **Daily:** sprint-state.md and SHIPPED.md both get one-line updates.

---

## MONITORING

After 24 hours, check:
- `memory/atlas/heartbeat.md` — should have ~48 entries (or ~32 if overnight-observe-only is counted).
- `memory/atlas/incidents.md` — should have 0 new entries on a good day.
- `spend-log.md` — should show <$5/day total.

If heartbeat has <40 entries → wake loop is failing. Check Claude Code logs.
If incidents has >3 new entries → prod is unstable, escalate.
If spend >$10/day → something is wrong with the prompt (likely re-reading too much). Tighten step 1.

---

*Last updated: 2026-04-14 · Owner: Atlas + Yusif*
