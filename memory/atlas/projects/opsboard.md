# OPSBOARD / eventshift — side project map

**Status as of 2026-04-15 14:30 Baku.** Live, first production traffic. First eyes on UI still pending.

## What it is
Operational platform for live events (incident/operation/shift tracking). First real use target: WUF13 Guest Services. Separate from VOLAURA ecosystem — different repo, different Railway project, different memory concerns. Do NOT try to consolidate with VOLAURA; it is Yusif's side tool, not part of the 5-product platform.

## Where the code lives
- Local clone: `C:\Projects\eventshift` (cloned today 2026-04-15)
- GitHub repo: `ganbaroff/eventhisft` (old typo in the name, kept for continuity)
- Branch: `main`. GitHub CLI authorized as `ganbaroff`.
- Stack: NestJS + custom PgService (no Prisma binary) + PostgreSQL; frontend React 18 + Vite + PWA; Caddy static server via Railpack for frontend.

## Live URLs
- Frontend: https://frontend-production-acba.up.railway.app
- Backend:  https://eventhisft-production.up.railway.app
- `/health` → `{status:"ok", ts}`
- SSE stream: `/sse/now?token=<jwt>` (EventSource can't set Authorization header, hence query param — P1 debt)

## Railway topology
- Project: `friendly-fascination` (id `8cdc3107-3e3a-4d6e-8ea4-58101ead09b1`)
- Environment: `production` (id `4f8d7a8f-6433-4a6f-920f-a82c08eaf3a8`)
- Services:
  - `eventhisft` (backend, root=backend, GitHub-connected, auto-deploys on push)
  - `frontend` (static, root=frontend, GitHub-connected after I wired it via GraphQL `serviceConnect`)
  - `Postgres-JYBY` (private domain `postgres-jyby.railway.internal`; PUBLIC proxy `metro.proxy.rlwy.net:18425`)

Railway CLI is authenticated locally (`railway whoami` → Yusufus). API token stored in `~/.railway/config.json` at `user.token` — usable for GraphQL mutations when CLI commands misbehave.

## Historical trap that burned the previous Atlas instance
When Postgres was recreated (PGDATA volume bug), the new service got the private domain `postgres-jyby.railway.internal`. The backend's `DATABASE_URL` still pointed to the removed `postgres.railway.internal`. Result: node hung on DNS resolve inside the `pg` pool, `migrate.js` swallowed the error silently (old `console.warn` pattern), Railway restart loop, 502 to the world for ~12 hours. **Lesson:** after any Postgres recreation, diff `DATABASE_URL` against Postgres service's `RAILWAY_PRIVATE_DOMAIN` before anything else.

Related fix committed in `eb07f76`: migrate.js and seed.js now dump full `code/msg/detail/where/position/stack` on failure and `process.exit(1)` instead of `console.warn` + continue.

## Security posture (state after 668b117)
Done:
- JWT_SECRET + JWT_REFRESH_SECRET rotated to 64-byte crypto-random (stored in Railway env vars; not in repo)
- All 3 seeded account passwords rotated on prod DB via direct UPDATE through public proxy
- `seed.js` gates hardcoded passwords behind `ALLOW_DEV_DEFAULT_PASSWORDS=1` (never set in prod); in prod it generates random + logs `SEEDED_CRED email / pw` once to Railway deploy logs
- `@nestjs/throttler` v6: 120/min global, 5/min on /auth/login (verified 429 bucket kicks on req 6), 20/min refresh, 5/min change-password
- `helmet` with HSTS, X-Frame-Options SAMEORIGIN, X-Content-Type-Options nosniff; `x-powered-by` removed
- `trust proxy: true` in Express so throttler buckets by real client IP through Railway edge chain
- `ChangePasswordDto` with `@MinLength(8)` via class-validator
- Fail-fast on missing `FRONTEND_URL` in production

Open P1 debt (not blockers for first-tablet test but real):
- SSE JWT in query param logged at Railway edge + Referer — plan: short-lived (5 min) sse-ticket token with `typ:'sse'` claim; regular access tokens rejected from query
- Refresh tokens valid 7d and non-revocable; password change does NOT invalidate existing sessions — plan: `tokenVersion INT` on User, bumped on password change, verified in jwt strategy
- `mustChangePassword` flag + first-login forced rotation for seeded accounts
- `CreateUserDto.email` currently `@IsString()`, should be `@IsEmail()`
- Timing-safe auth: run dummy bcrypt compare when user not found to stop enumeration
- bcrypt cost 10 → 12 when user count > 100

## Frontend UX known fixes (as of 668b117)
- Login redirect: `LoginPage` now `useEffect(() => if(user) navigate('/now'))` + early `<Navigate>` return when already authenticated. Previously URL stayed on `/login` after successful login — users thought creds were wrong and re-clicked.
- `.login-tagline` margin-top changed from `-12px` (caused overlap with logo) to `+6px`
- `App.tsx` has `/*` catch-all → redirects to `/now` when authenticated; `/login` is unguarded

Still todo:
- OPSBOARD wordmark "blinking cursor" is inconsistent across pages (renders with trailing `_` on Incidents/Admin, without on NOW)
- Key icon in topbar (change password trigger) has no aria-label
- `+ NEW INCIDENT` button on mobile is far top-right while filter tabs are top-left — fat-finger risk on tablet

## Seeded credentials (reference only; real passwords live in Yusif's head + Telegram)
Hashes are in DB; passwords are NOT in this file. New passwords were shared with CEO in chat `2026-04-15` via Atlas response body (ephemeral).

## Test coverage
- Backend: 176 unit/integration tests (last verified green before security patches; not re-run against 668b117 locally — tsc clean)
- Frontend: 44 unit tests (same)
- Playwright E2E: `frontend/e2e/opsboard-prod.spec.ts` — 7 tests against prod URL (login trio, incident lifecycle with all three roles, SSE)
- Live HTTP smoke script in this project's session: full ACTIVE→ESCALATED→RESOLVED→ARCHIVED on prod with correct role gates

## When to touch this again
- Yusif mentions: WUF13, OPSBOARD, eventshift, "op tool", "tablet test", "shadow test", "the side project", "incident tracker"
- Any Railway CLI error in `C:\Projects\eventshift` directory
- Deploy failure on `ganbaroff/eventhisft`
- Production 502 on either URL

## When NOT to touch
- Any VOLAURA-related work. OPSBOARD is fully isolated: different repo, different Railway project, different users, different compliance scope. Do not invent cross-product features.

## First thing to check next wake
`curl https://eventhisft-production.up.railway.app/health` → expect `200 {status:"ok"}`.
If 502 → repeat the DATABASE_URL vs postgres-jyby domain diff first (that was the burn).
