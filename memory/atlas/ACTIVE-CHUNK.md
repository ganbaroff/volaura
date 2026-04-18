# Active Chunk — single deliverable both bodies work on

**Rule:** ONE chunk at a time. CLI and Cowork align here. No parallel tracks until chunk ships.

---

## CHUNK CLOSED: Vercel deploy → volaura.app live (2026-04-18 13:30 Baku)
curl https://volaura.app → 200. Verified.

---

## CHUNK CLOSED: Auth flow verified on prod (2026-04-18 14:10 Baku)
All pages 200. INC-018 REV2 in main (84eab94). Google OAuth consent in Testing mode — CEO action: switch to Production in Google Cloud Console. Both CEO accounts admin=true.

---

## Current chunk: Apply obligation migration to prod Supabase + seed data

**Goal:** atlas_obligations table live on prod, seeded with 83(b)/ITIN/EIN/Form5472/franchise deadlines. Nag-bot workflow ready to fire.

**Acceptance:** SQL query on prod returns seeded obligations. GitHub Actions workflow visible.

**Who does what:**
- CLI (Terminal Atlas): apply migration via Supabase MCP, run seed script
- Cowork: do NOT touch supabase/migrations/ until chunk closes

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
