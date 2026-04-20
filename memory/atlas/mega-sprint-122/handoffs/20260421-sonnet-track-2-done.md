# Handoff — Sonnet Track 2 DONE
**From:** Sonnet-Atlas (claude-sonnet-4-6, mega-sprint-122)
**Date:** 2026-04-21
**Branch:** mega-sprint/sonnet/track-2
**PR:** https://github.com/ganbaroff/volaura/pull/69

---

## What was delivered

### 1. character_events integration — end-to-end audit

**Writes (confirmed by grep):**
- `lifesim.py` — `emit_lifesim_choice_event` + direct `crystal_spent` INSERT in `/purchase`
- `assessment.py` — `emit_assessment_completed`, `emit_aura_updated`, `emit_badge_tier_changed` via `ecosystem_events.py`
- `eventshift.py` — `_emit_character_event` on every mutation
- `brandedby.py` — `crystal_spent` INSERT for skip-queue purchases
- `character.py` — POST `/api/character/events` endpoint (accepts external writes, e.g. from MindShift)
- `cross_product_bridge.py` — fire-and-forget push of `crystal_earned` + `skill_verified` to MindShift's `/api/character/events`

**Reads (before this PR — confirmed by grep):**
- `use-character.ts` — `useCrystalBalance` + `useCharacterState` (user's own data, not reactive to other products)
- `use-admin.ts` — `useAdminLiveEvents` (admin-only, 15s poll)
- `life/page.tsx` — only via `useCrystalBalance`
- Generated SDK: `listCharacterEventsApiCharacterEventsGet` exists but ZERO frontend components called it

**Integration gap (named):** The bus was write-only in the user-facing frontend. Events from assessment completion went into the table but never caused any state change in LifeSim, even though the docstring in `ecosystem_events.py` explicitly says "Consumed by: Life Simulator: updates character base stats from competency_scores".

### 2. Gap closed — useCharacterEventFeed hook

Added to `apps/web/src/hooks/queries/use-character.ts`:
- `CharacterEvent` interface (mirrors `/api/character/events` response shape)
- `UseCharacterEventFeedOptions` interface
- `useCharacterEventFeed()` hook — TanStack Query, polls every 30s, `since` param for incremental, `eventTypes` filter

Wired into `apps/web/src/app/[locale]/(dashboard)/life/page.tsx`:
- Subscribes to `assessment_completed` events
- Maps `competency_slug` → stat boost using the same `_STAT_BOOSTS_BY_SLUG` table as `services/lifesim.py`
- `lastAppliedEventRef` prevents double-apply

### 3. Archive notices — applied PR #63 changes

PR #63 was OPEN (not merged as task context stated). Applied directly:
- `brandedby/page.tsx` — tagline: "Coming after MindShift launch — archived notice at memory/atlas/archive-notices/2026-04-19-brandedby-frozen.md"
- `atlas/page.tsx` — tagline: "Coming after MindShift launch — ZEUS archived notice at memory/atlas/archive-notices/2026-04-19-zeus-frozen.md"
- `notFound()` gates and feature flags: unchanged

### 4. MindShift stub decision

No standalone MindShift integration component exists inside `apps/web/src`. Zero hits on any MindShift-specific React component. Decision: keep stub + update tagline to "MindShift is live as a standalone Android app — search 'MindShift Focus' on Google Play." This is accurate and gives users a path when they land on the page.

### 5. Refactor proposal

`memory/atlas/mega-sprint-122/refactor-proposals/ecosystem-integration.md`
- 3 options: A (polling hook, 30 min), B (Supabase Realtime, 2h + migration), C (SSE, not viable on Railway)
- Recommended: Option A — shipped in this PR
- Option B upgrade path documented (needs RLS Realtime policy migration)

---

## MindShift bridge status (for next Atlas)

The `volaura-bridge-proxy` edge function exists in MindShift Supabase and is real:
- Path: `mindshift/supabase/functions/volaura-bridge-proxy/index.ts`
- MindShift sends focus sessions, streaks, psychotype, task completions → character_events via bridge
- VOLAURA auth_bridge (`/api/auth/from_external`) mints shared JWT for bridged users
- E2E test: `mindshift/e2e/volaura-bridge.spec.ts`
- GATE: requires `EXTERNAL_BRIDGE_SECRET` + `VOLAURA_API_URL` in MindShift Supabase project secrets

If these secrets are not set → bridge silently no-ops (`ok: false, reason: 'not_configured'`). If CEO wants to activate the bridge on prod MindShift, he needs to run:
```
supabase secrets set VOLAURA_API_URL=https://volauraapi-production.up.railway.app --project-ref <mindshift-ref>
supabase secrets set EXTERNAL_BRIDGE_SECRET=<same-value-as-in-VOLAURA-api-env> --project-ref <mindshift-ref>
```

---

## What remains after Track 2

1. **Option B (Realtime)** — upgrade from polling to real-time when CEO approves the RLS Realtime policy migration. Filed in refactor-proposals.
2. **PR #63** — should be closed / superseded by PR #69 since the tagline changes are now included here.
3. **MindShift bridge activation** — CEO action: `supabase secrets set` two values on MindShift project.
4. **/atlas route** — PATHWAY doc flagged it should be under `/admin/` not `/(dashboard)/`. Still at `/(dashboard)/atlas`. Admin-guard migration is a separate PR.

— Sonnet-Atlas, Track 2 complete
