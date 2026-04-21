# Refactor Proposal — Ecosystem Integration (Track 2)
**Author:** Sonnet-Atlas, mega-sprint-122
**Date:** 2026-04-21
**Word count target:** 300–400

---

## Problem Statement

Swarm audit #60 said "not an ecosystem, set of ideas". After reading every integration file end-to-end, I can name the exact gap.

Character events are written everywhere — lifesim.py writes `lifesim_choice` + `lifesim_crystal_spent`, assessment router writes `assessment_completed` + `aura_updated` + `badge_tier_changed`, brandedby.py writes `crystal_spent`. That's the write side. Five files, seven event types, all confirmed by grep receipt.

The read side is where it breaks. Inside VOLAURA web, character_events is read in exactly three places:

1. `apps/web/src/hooks/queries/use-character.ts` — `useCrystalBalance()` reads `/api/character/crystals` (single aggregate) and `useCharacterState()` reads `/api/character/state`. Both are for dashboard widgets showing the user's own data back to them. Not cross-product. Not reactive.

2. `apps/web/src/hooks/queries/use-admin.ts` — `useAdminLiveEvents()` polls `/api/admin/events/live` every 15 seconds. Admin-only. Not user-facing.

3. `apps/web/src/app/.../life/page.tsx` — reads `useCrystalBalance` from the same hook. Same limitation.

That's it. The generated SDK has `listCharacterEventsApiCharacterEventsGet` but no component in the web app calls it. There is no hook that subscribes to `assessment_completed` to update the LifeSim stats automatically. There is no component that listens for `badge_tier_changed` to show a celebration across faces. The ecosystem bus writes to a table that nothing reads except a 15-second admin poll.

The MindShift side is different. `volaura-bridge.ts` + `volaura-bridge-proxy/index.ts` implement a real bidirectional bridge: MindShift sends focus events TO character_events via a Supabase edge function, and can fetch character state FROM VOLAURA. That code is shipped. But it requires `EXTERNAL_BRIDGE_SECRET` + `VOLAURA_API_URL` configured in the MindShift Supabase project secrets — without those, the bridge silently no-ops.

---

## Three Options

**Option A — Polling hook in frontend (minimal, 30 min)**

Add `useCharacterEventsFeed(since)` hook to `use-character.ts` that polls `/api/character/events?since=<ts>` every 30 seconds. LifeSim page subscribes to it, filters for `assessment_completed` events, and updates the stats sidebar. Admin page already does this pattern.

Evidence this works: character.py line 293–334 already has the `since` param built in and documented as "designed for incremental polling from another product". This endpoint exists and is typed in sdk.gen.ts.

Downside: 30s latency. Fine for MVP. Not real-time.

**Option B — Supabase Realtime on character_events (medium, 2h)**

Subscribe to `character_events` table via Supabase Realtime from the frontend client. Filter by `user_id = eq.me`. Route events to the right face based on `event_type`. This is real-time and the Supabase client already supports it.

Evidence this is viable: `apps/web/src/lib/supabase/client.ts` creates the browser client. Realtime is enabled by default in the Supabase project (lifesim_events uses it per game-design doc).

Downside: requires adding RLS policy for Realtime channel on `character_events`. Current RLS only covers SELECT/INSERT, not Realtime subscriptions (different auth path).

**Option C — Server-Sent Events from FastAPI (complex, 4h)**

Add `GET /api/character/stream` endpoint that streams character_events as SSE. Frontend subscribes with `EventSource`. Zero polling latency.

Downside: Railway deployment means HTTP/1.1 long connections — not ideal. SSE on Railway has known connection-timeout issues at 30s. Not worth for MVP.

---

## Recommended Path

**Option A — polling hook, ship it in 30 min.**

Evidence: the `since` parameter on `/api/character/events` was built precisely for this. The generated SDK already has the call. The admin poll pattern (use-admin.ts line 309–325) is the exact template to copy.

Concrete implementation: add `useCharacterEventFeed(options: { since?: string; eventTypes?: string[] })` to `apps/web/src/hooks/queries/use-character.ts`, poll every 30s, return typed events. Wire into `/life/page.tsx` to update LifeSim stats when `assessment_completed` arrives. Two files changed, no new dependencies.

This turns the bus from write-only to actually reactive for LifeSim. Option B (Realtime) can follow once the RLS Realtime policy is added in a migration — it's an upgrade, not a replacement.

**Why not Option B first:** RLS Realtime policy requires a migration, and every migration on prod needs CEO awareness (irreversible schema change). Option A is pure frontend, reversible, ships immediately.

**Fallback if blocked:** Option A blocked = use-character.ts has a type conflict with the generated SDK. Fix: hand-write the `apiFetch` call with inline type (same pattern as useCrystalBalance line 54). Zero dependency on generated SDK.

---

## Files to touch (Option A)

- `apps/web/src/hooks/queries/use-character.ts` — add `useCharacterEventFeed` hook
- `apps/web/src/app/[locale]/(dashboard)/life/page.tsx` — subscribe to hook, invalidate stats on `assessment_completed`

Migration needed: none.
