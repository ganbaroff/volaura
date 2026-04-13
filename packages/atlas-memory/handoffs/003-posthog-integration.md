# Handoff 003: PostHog SDK Integration
**From:** Cowork (coordinator) | **Date:** 2026-04-12 | **Priority:** P2

**IMPORTANT:** Read `packages/atlas-memory/sync/PROTOCOL.md` FIRST. Follow the sync rules at session end.

## Context
PostHog MCP connector is live (org: "volaura", project: "Default project", team token: `phc_se8LwdYnuhw7pzxfQZRCVGG3gr8EcDKsQGEg8dUAKYsi`). But **zero events** are flowing — the PostHog SDK is not installed anywhere in the codebase. The app currently tracks events only to Supabase `analytics_events` table via `apps/api/app/services/analytics.py`.

## Findings (from Cowork audit)
1. PostHog org created 2026-04-12, project ID 378826, 0 event definitions
2. Frontend has `apps/web/src/hooks/use-analytics.ts` — sends events to backend `/api/analytics/event`
3. Backend has `apps/api/app/services/analytics.py` — writes to `analytics_events` table in Supabase
4. No `posthog-js` or `posthog-node` in any package.json
5. No PostHog env vars in `.env` files

## Architecture Decision
**Dual-write approach** (recommended): Keep Supabase analytics_events as-is (cheap, owned data) AND add PostHog for product analytics (funnels, paths, retention, session replay). Do NOT replace the Supabase tracking — it's a clean audit log.

### Frontend (primary — most value)
Install `posthog-js` in `apps/web/`. Initialize in a provider component. Auto-capture pageviews + manual events from existing `useTrackEvent` hook.

### Backend (optional, defer)
Can add `posthog-python` later to track server-side events. Not blocking.

## Task
1. Install `posthog-js` in `apps/web/`
2. Create PostHog provider component at `apps/web/src/components/providers/posthog-provider.tsx`
3. Add to root layout (`apps/web/src/app/[locale]/layout.tsx`)
4. Extend `useTrackEvent` hook to also fire `posthog.capture()` alongside the existing Supabase call
5. Add env vars: `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST`
6. Respect `prefers-reduced-motion` and consent (Constitution Law 4)

## Acceptance Criteria
- [ ] AC1: `posthog-js` installed in `apps/web/package.json`
- [ ] AC2: PostHog provider initialized with `phc_se8LwdYnuhw7pzxfQZRCVGG3gr8EcDKsQGEg8dUAKYsi` key and `https://us.i.posthog.com` host
- [ ] AC3: `useTrackEvent` fires both Supabase (existing) and PostHog (new) — dual write
- [ ] AC4: Pageview auto-capture enabled. After deploy, events appear in PostHog dashboard (verify via Cowork MCP `event-definitions-list`)
- [ ] AC5: `NEXT_PUBLIC_POSTHOG_KEY` and `NEXT_PUBLIC_POSTHOG_HOST` added to `.env` and Vercel env vars

## Files to Read First
- `packages/atlas-memory/sync/PROTOCOL.md` — sync rules
- `apps/web/src/hooks/use-analytics.ts` — existing analytics hook (extend, don't replace)
- `apps/web/src/app/[locale]/layout.tsx` — where to add provider
- `apps/web/package.json` — add posthog-js dependency

## Files NOT to Touch
- `apps/api/app/services/analytics.py` — keep Supabase tracking as-is
- Any backend files — this is frontend-only

## PostHog Config
```
Key: phc_se8LwdYnuhw7pzxfQZRCVGG3gr8EcDKsQGEg8dUAKYsi
Host: https://us.i.posthog.com
```

## Risks
- **Risk:** PostHog SDK increases bundle size → **Mitigation:** Dynamic import, load async after page hydration
- **Risk:** Ad blockers may block PostHog → **Mitigation:** That's fine, Supabase analytics is the reliable fallback (dual-write)
- **Risk:** GDPR/consent → **Mitigation:** PostHog respects opt-out. Add to cookie banner when we build one (future task)

## On Completion (from PROTOCOL.md)
1. Update `packages/atlas-memory/sync/claudecode-state.md`
2. Update `packages/atlas-memory/sync/heartbeat.md`
3. Update `packages/atlas-memory/STATE.md` — update Now/Blockers
4. Update `memory/swarm/SHIPPED.md` if new code
