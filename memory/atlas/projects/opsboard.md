# OPSBOARD / eventshift — side project map

**Status as of 2026-04-16 14:30 Baku.** CEO directive: eventshift becomes part of VOLAURA ecosystem. Not a separate side tool anymore.

## What it is
Event workforce operations module INSIDE the VOLAURA ecosystem. Manages staff deployment, shift reporting, operational metrics per zone/unit at live events. First real use target: WUF13 Guest Services department (GSE). CEO directive 2026-04-16: "часть волаура. регистрируется аккаунт через VOLAURA, попадает на страницу ивента."

**SUPERSEDES** previous directive "Do NOT try to consolidate with VOLAURA." CEO explicitly reversed this 2026-04-16.

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

## NotebookLM assets
A dedicated NotebookLM notebook exists for OPSBOARD field assets:
- Notebook ID: `6c42a882-8e52-4e90-8b33-1efcff20c674`
- Title: "OPSBOARD WUF13 — Field Coordinator Brief"
- Sources indexed: 9 internal docs (CLAUDE.md, README.md, product-definition, domain-model, workflow-rules, handoff, shadow-test-checklist, known-limitations, mvp-scope) — field-reference-card.html rejected (400)
- First artifacts generated 2026-04-15:
  - Audio brief task `a8dfd1ce-cbba-49f8-a1c9-7b667ad86baa` → `docs/field-brief.mp3`
  - Markdown briefing task `e591695d-cef7-41ed-a2de-7d651d7325d1` → `docs/field-brief.md`

Both assets targeted at field coordinators boarding a bus to WUF13, not at developers. Tone: calm, ESL-friendly, plain English, "call a Manager" as default escalation. Regenerate if the product's state machine or role matrix changes materially.

Windows gotcha (logged twice in one session 2026-04-15): the `notebooklm` CLI's `rich` output crashes on cp1252 console when printing the success checkmark. The download still works. Future invocations on Windows should set `PYTHONUTF8=1` or `PYTHONIOENCODING=utf-8` — not fatal, but noisy.

## When to touch this again
- Yusif mentions: WUF13, OPSBOARD, eventshift, "op tool", "tablet test", "shadow test", "the side project", "incident tracker"
- Any Railway CLI error in `C:\Projects\eventshift` directory
- Deploy failure on `ganbaroff/eventhisft`
- Production 502 on either URL

## When NOT to touch
- When working on non-event VOLAURA features (assessment, AURA, profile). Ops module has its own development track.

## Integration status (2026-04-16)
- CEO vision: Event → Department → Area → Unit → People + Metrics
- Research complete: Rosterfy, Engelsystem, LASSO, Liveforce analyzed. NotebookLM notebook with 7 sources.
- Domain model revised per CEO vision (not incident-first, but people-and-metrics-first)
- Supabase migration drafted (needs revision to match new domain model)
- FastAPI routers drafted (needs revision to match new domain model)
- Frontend pages drafted (needs revision to match new domain model)
- Build order: 1) Reporting 2) Daily Run Sheet 3) Deployment Plan 4) Data Import

## First thing to check next wake
`curl https://eventhisft-production.up.railway.app/health` → expect `200 {status:"ok"}`.
If 502 → repeat the DATABASE_URL vs postgres-jyby domain diff first (that was the burn).
