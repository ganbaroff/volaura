# Active Chunk — single deliverable both bodies work on

**Rule:** ONE chunk at a time. CLI and Cowork align here. No parallel tracks until chunk ships.

---

## CHUNK CLOSED: Vercel deploy → volaura.app live (2026-04-18 13:30 Baku)
curl https://volaura.app → 200. Verified.

---

## CHUNK CLOSED: Auth flow verified on prod (2026-04-18 14:10 Baku)
All pages 200. INC-018 REV2 in main (84eab94). Google OAuth consent in Testing mode — CEO action: switch to Production in Google Cloud Console. Both CEO accounts admin=true.

---

## CHUNK CLOSED: Obligation system deployed to prod (2026-04-18 15:00 Baku)
6 obligations seeded. RPC list_open_obligations() returns live data. 83(b) = 10 days urgent.

## CHUNK CLOSED: Assessment 409 fix (2026-04-18 15:05 Baku)
Admin bypass for stale sessions + audit logging. Strange v2 Gate 1 passed (Gemini).

---

## Current chunk: volunteer_ table rename migration

**Status:** DEFERRED to next sprint. 3 tables (volunteer_badges, volunteer_behavior_signals, volunteer_embeddings) used in activity.py + embeddings.py + 6 test files. Breaking change needs coordinated migration + code + test update. Not a quick fix.

---

## Current chunk: Admin panel live verification on prod

**Goal:** CEO opens volaura.app/en/admin, sees 5 KPI cards + obligations + live feed.

**Who does what:**
- CLI: verify Vercel deployed latest, check /admin renders
- Cowork: do NOT touch admin components

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
