# Active Chunk — single deliverable both bodies work on

**Rule:** ONE chunk at a time. CLI and Cowork align here. No parallel tracks until chunk ships.

---

## CHUNK CLOSED: Vercel deploy → volaura.app live (2026-04-18 13:30 Baku)
curl https://volaura.app → 200. Verified.

---

## Current chunk: Auth flow end-to-end on prod

**Goal:** signup → Google OAuth → dashboard → start assessment → complete → AURA badge visible. On volaura.app, not localhost.

**Acceptance:** walk the flow in browser, screenshot or curl proof of each step.

**Who does what:**
- CLI (Terminal Atlas): test auth flow, fix any blockers found
- Cowork: do NOT touch apps/web/src/app/[locale]/(auth)/ or callback/ until chunk closes

**Non-overlapping safe zone for Cowork:**
- memory/atlas/ updates
- docs/ content
- MindShift repo
- backend files not in auth path

---

## Queue (next chunks, in order)

1. Auth flow works end-to-end (signup → assessment → AURA badge) on volaura.app
2. Admin panel accessible at /admin with real data
3. EventShift feature flag removal (when 1+2 verified)

---

## Coordination protocol

- Finishing a chunk: author writes "CHUNK CLOSED: <name>" at top, moves to queue[0]
- Conflict prevention: before editing any file, check `git log -1 -- <path>` — if other body touched it in last 2 hours, coordinate via this file first
- No sprint documents longer than this file. Sprint = sequence of chunks.
