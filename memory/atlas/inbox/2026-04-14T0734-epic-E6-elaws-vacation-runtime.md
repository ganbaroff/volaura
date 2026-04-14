# Epic E6 — E-LAWs + Vacation Mode → Runtime

**Owner:** Atlas
**Duration:** 2 days
**Priority:** P1 — Atlas reliability story
**Source:** E-LAWs spec (7 Atlas Emotional Laws), Vacation Mode v0 ("Bali Mode") spec, SYNC §3

## Goal
Specs become running code. 23:00 UTC digest fires. 6h cooldown respected. Vacation toggle works. 99.0%/24h SLO measurable.

## Tasks

1. **23:00 UTC daily digest**
   - GitHub Actions workflow: `.github/workflows/atlas-daily-digest.yml`
   - Cron: `0 23 * * *`
   - Script: reads `memory/atlas/journal.md` last 24h + `memory/atlas/inbox/` new + proposals.json unread
   - Posts to CEO Telegram: 3 bullets max — what happened, what's pending, what needs decision
   - Tone: calm, no urgency unless actual P0

2. **6h cooldown**
   - Where: Telegram notifier in swarm
   - Logic: don't send same category of notification within 6h window
   - Storage: simple SQLite or JSON in `memory/atlas/notification-log.json`
   - Categories: `escalation`, `digest`, `error`, `proposal`

3. **Vacation mode toggle**
   - File: `memory/atlas/vacation.json` with `{ "active": bool, "until": ISO8601, "reason": str }`
   - When active: notifier suppresses everything except CRITICAL
   - CEO can toggle via committing change to file OR future UI command
   - Digest still runs but goes to a file instead of Telegram

4. **SLO instrumentation**
   - Metric: swarm-daily.yml success rate over 24h rolling window
   - Store: `memory/atlas/slo-log.json` — append {timestamp, success, duration}
   - Read: digest includes "SLO: X.X% (target 99.0)"

5. **Wire E-LAWs**
   - Document which law maps to which runtime behavior
   - `docs/atlas/E-LAWS-RUNTIME.md` — spec ↔ code map
   - Example: Law "don't panic" → cooldown; Law "tell CEO what matters" → digest filter

## Files to touch
- `.github/workflows/atlas-daily-digest.yml` (new)
- `packages/swarm/notifier.py` (or create)
- `memory/atlas/vacation.json` (new, default inactive)
- `memory/atlas/notification-log.json` (new)
- `memory/atlas/slo-log.json` (new)
- `docs/atlas/E-LAWS-RUNTIME.md` (new)

## Definition of Done
- [ ] Daily digest actually fires on schedule (verify 1 cycle)
- [ ] Test: trigger same alert twice within 6h → second suppressed, logged
- [ ] Set `vacation.active=true, until=+1h` → test alert suppressed → revert
- [ ] `slo-log.json` accumulates entries after 2 cron runs
- [ ] Runtime doc maps each of 7 E-LAWs to code location

## Dependencies
E1 (memory gate + mem0) helps but not required.

## Artifacts
- Runtime mapping doc
- Decision log `memory/decisions/2026-04-1X-elaws-runtime-cut.md` if any E-LAW intentionally deferred
- Journal entry with first-digest screenshot/text
