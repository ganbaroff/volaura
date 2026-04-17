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

---

## 2026-04-17 11:45 Baku — Cowork-Atlas synthesis (CEO post-compaction pivot)

### What CEO said (2026-04-17, verbatim fragment)
«eventshift что думаешь. много чего исследовал и так далее. осталось в документах? проект видишь? это часть экосистемы как я и говорил, внутри проекта отдельный модуль (mindshift например это отдельный проект который отображается внутри твоего профиля, но это мобильное приложение и это приложение работает, это словно врата в наш проект, я подробно описывал это всё. найди умоляю я уже устал) ты уверен сможешь всё понять. идеи развитие и так далее. то что от меня приходило всё проверь. не верь фейкам. перепроверяй все важные моменты мне нужно качество а не скорость»

### The three-way distinction CEO just made explicit
| Thing | What it is | How user meets it |
|-------|------------|-------------------|
| **EventShift / OPSBOARD** | Internal VOLAURA module for event workforce ops | Signup on volaura.app → lands on event page inside the platform |
| **MindShift** | Separate mobile app (production v1.0, Android nearly ready) | Works standalone AND shown as a gateway ("врата") inside the VOLAURA profile view |
| **VOLAURA** | The verification platform — the body that holds both | Primary web entry point, AURA score, profile |

Prior conflation in lessons.md ("Не знал что eventshift (MindShift) лежит в C:\Projects\") was wrong. They are two distinct things. Do not re-conflate.

### Verification log (what I checked today before speaking)
- `curl -w "%{http_code} (%{time_total}s)" https://eventhisft-production.up.railway.app/health` → **200 (0.877s)**
- `curl -w "%{http_code} (%{time_total}s)" https://frontend-production-acba.up.railway.app` → **200 (0.556s)**
- `git log --oneline -5` on VOLAURA → head `d2fca9c feat(web): sample AURA profile page — Constitution P0 #12`
- opsboard.md (this file) read end-to-end — 109 lines, 2026-04-16 reversal documented
- ecosystem-linkage-map.md — confirms MindShift shares Supabase project `dwdgzfusjsobnixgyzjk`
- PROJECT-EVOLUTION-MAP.md — 1,367 commits across 27 days, Session 114 active
- CURRENT-SPRINT.md — Track A (LifeSim Life Feed) 9/9 done; Track E "Atlas-everywhere" active
- project_v0laura_vision.md — "I AM the project; 5 faces" re-confirmed
- mindshift/memory/yusif-messages.md — historical EventShift/OPSBOARD chat Apr 10-13 (Sprint C+7 real bugs caught, Railway deploy instructions, full incident lifecycle tested)

### Reconciliation: Apr 15 brief vs Apr 16 CEO directive
`memory/atlas/research/ecosystem-brief-2026-04-15.md` §3 recommended: "KEEP SEPARATE through WUF13" (risk ratio, tenant isolation).
`memory/atlas/projects/opsboard.md` 2026-04-16 14:30 documents CEO's reversal: "часть волаура. регистрируется аккаунт через VOLAURA, попадает на страницу ивента."
**Winner:** 2026-04-16 directive. The brief is superseded. All integration work from today forward assumes single-tenant inside VOLAURA.

### Module shape inside VOLAURA (synthesis from research + 2026-04-16 domain revision)
CEO vision already documented in §Integration status: **Event → Department → Area → Unit → People + Metrics**. People+metrics-first, NOT incident-first. This is what the existing supabase migration drafts + FastAPI routers + frontend pages need to be revised to match before WUF13.

Four ideas for how the module earns its keep (all align with 2026-04-16 directive, all pass Ecosystem Design Gate):

1. **SSO landing on event page.** User signs up at volaura.app → if event-bound (invite code / org-assigned) → first screen inside authed area is the event page, not the generic AURA profile. Same Supabase auth session, RLS scopes `event_id` on all opsboard tables. One registration, two products felt.

2. **`reliability_proof` → AURA.** When a coordinator closes a shift clean (all units reported, no unresolved incidents, SSE peer count matches roster), emit a `reliability_proof` row to `public.character_events` with `source_product:'opsboard'`, `event_id`, `shift_minutes`, `unit_id`. Assessment pipeline reads these as ground-truth signal for `reliability` (0.15 AURA weight) and `event_performance` (0.10 weight). This is the biggest validity upgrade in the whole ecosystem — real field behaviour instead of self-reported assessment answers. Research Path 2 from ecosystem-brief, now unblocked by 2026-04-16 directive.

3. **Crystal tie-in.** Clean shift close → `crystal_earned` event (small, e.g. 25 crystals per shift-hour) → same ledger Life Simulator reads. Avoids inflation by anchoring to measurable work, not tap-farming. Respects all 8 Crystal Laws (no timer, no expiry, transparent formula: 1 shift-hour = 25 crystals of `FOCUS` type).

4. **Face under the VOLAURA skeleton.** Per `project_v0laura_vision.md`, EventShift becomes a *face* of the platform — not a sixth product. Accent token TBD (suggest `#22D3EE` cyan, distinct from VOLAURA purple/MindShift blue/LifeSim amber/BrandedBy pink). Tab Bar only visible when user is actively assigned to a running event — hides after event ends, prevents dead routes.

### Scope lock for 28-day WUF13 runway (May 15 deadline)
Per the already-documented Build order (Reporting → Daily Run Sheet → Deployment Plan → Data Import), for the next 28 days:
- **IN:** Reporting, Daily Run Sheet, Deployment Plan, Data Import (CSV roster), SSO bridge from VOLAURA auth, `reliability_proof` emit on shift close
- **NOT IN:** Life Simulator quest overlay (Path 3 from brief — defer), BrandedBy tie-in, full unified-profile merge, SSE payload encryption (P1 debt is real but not a ship blocker for GSE tablet test)
- **SUCCESS:** One real GSE coordinator runs a shift end-to-end on eventshift-prod, closes it, and the shift close writes a `reliability_proof` row visible in VOLAURA DB. That's the definition of "ecosystem integrated."

### Still-unverified per Doctor Strange Gate 3
These are the "не верь фейкам" items CEO specifically called out. I have NOT re-verified them today; marking explicitly so next wake knows:
- Latest eventhisft commit SHA on `main` (need `git -C C:\Projects\eventshift log --oneline -5`) — session context is `/sessions/elegant-fervent-carson/mnt/VOLAURA`, not the eventshift clone
- Railway deploy state timestamp — which commit is actually live right now on frontend+backend
- Whether the drafted Supabase migration matches the 2026-04-16 domain revision (people+metrics-first) OR still reflects the old incident-first model
- Whether `character_events` bus is ready to receive `reliability_proof` rows (schema exists? RLS lets opsboard service-role insert?)
- WUF13 GSE contact status — is CEO on the vendor list, tablet hardware count confirmed

### Historical traps to not re-fall-into
- Postgres recreation → `postgres-jyby.railway.internal` vs `postgres.railway.internal` DNS mismatch → 12h outage (already in this file, commit `eb07f76` fixed migrate.js silent-warn pattern)
- Sprint C real bugs: (a) @MinLength on LoginDto leaked auth state via 400 vs 401, (b) passwordHash returned in /auth/me — both caught via real integration tests, not mocks. Rule: if auth surface changes, run the 176 unit + 44 frontend + 7 Playwright suite against a real database, not mocks.
- Windows `cp1252` crash on `notebooklm` CLI rich output — set `PYTHONUTF8=1` before invoking on Windows

### Decision log (for future Atlas instances reading this in 3 months)
- 2026-04-17: EventShift confirmed as internal VOLAURA module, not standalone product. `reliability_proof` emit path unblocked. Prior "keep separate" recommendation formally retired.
- Revisit trigger: if tenant isolation becomes a legal issue (multi-org events with conflicting data access needs), OR if performance of shared Supabase cluster degrades past Sprint AA baseline, OR if CEO reverses again.

---

## 2026-04-17 11:56 Baku — CEO correction: universal module, octopus platform (supersedes 11:45 section above)

### What CEO said (2026-04-17, verbatim fragment — English, tired, broken grammar)
«do not forget we are not developing an app for wuf 13 we just optimising this for now for mvp. this module is universal we already have a businesse in out costomer lists and we must to prepare an interestiong options for them/ lice an OCTOPUS maybe you heard about thaty they can add modules if customer need id we aldo will provide an modules. but for nw concentrate in this. we must to analyse all ways for integration this module- do researchs( i already prepared 1 or 2 pcs and you can find it? i dont know where you register is( not you previous cowowrk you can ask him anything) and our constitutuion what you think do we have documents which making our ecosystem weaker? do swot analysis.»

### What the 11:45 section got wrong
I scoped EventShift as "28-day WUF13 runway" with explicit scope-lock. WUF13 is the first customer to prove the module works. It is not the product. The module is a universal workforce-ops arm of VOLAURA that any event-running customer can activate. WUF13 = tenant #1. The framing from today forward is multi-tenant from Day 1.

### Octopus platform — what it means for architecture
The VOLAURA body has ONE core (AURA verification, profile, search) and attachable arms. Customers plug in the arms they need, we provide more arms over time. Each arm is:
- Multi-tenant from schema-level (not retrofitted). All opsboard tables scope `org_id` with RLS FORCE.
- Activation-gated (customer admin turns it on for their org, user sees it when assigned to that org's event).
- Feature-flagged per sub-module. Customer A runs Daily Run Sheet only. Customer B runs Incident Tracker + Reporting + Data Import. Same code, different activation.
- Billed per arm. Usage-metered via the same events that feed AURA (shift-hours, clean-close rate).
- Exits cleanly. Disabling the arm hides the tab, archives the data, does not leave dead routes.

### The five-product taxonomy, re-categorized per today's directive
CEO's "MindShift is a gateway, EventShift is a module" distinction maps to four kinds of thing, not five products:

| Kind | What it does | Examples |
|------|--------------|----------|
| Core | AURA verification, profile, search — the reason the platform exists | VOLAURA web |
| Gateway | Separate app/entry-point that drives users INTO VOLAURA | MindShift mobile |
| Module | Arm attached to the core, activated per customer/role | EventShift, BrandedBy, future arms |
| Experience layer | Visual/narrative overlay on shared economy | Life Simulator |
| Infra | Invisible to user, powers everything | ZEUS / swarm / Atlas |

This is the first time the five products line up without overlap. Before today they were all called "products" which hid the fact that they are different kinds of thing. The octopus framing makes the kinds explicit.

### Integration paths for the module (universal, not WUF13-only)

Path 1 — SSO + org-admin bridge.
Customer admin lands in VOLAURA org workspace, activates EventShift for their org, imports roster CSV. Every roster row that has a VOLAURA email matches existing profile; every non-match creates an invite. Acquisition channel: one enterprise customer onboards 200 people = 200 new AURA profiles provisioned. This is how the module becomes a growth arm, not just a feature.

Path 2 — `reliability_proof` → AURA (biggest validity upgrade).
Clean shift close (roster ticked, units reported, no unresolved incidents) emits a `reliability_proof` row into `public.character_events`. Assessment pipeline reads it as ground-truth signal for `reliability` (0.15 AURA weight) and `event_performance` (0.10 weight). Real field behaviour replaces self-reported quiz answers as the dominant signal. Works for any customer running any event. The more customers run events, the more real data the core gets.

Path 3 — Crystal tie-in (unified economy).
Clean shift-hour = 25 FOCUS crystals in the shared ledger. Respects all 8 Crystal Laws: no timer, no expiry, transparent formula. Customer admin sets the multiplier per their org if they want to reward specific shift types more. Life Simulator reads the same ledger. One economy across every arm.

Path 4 — Face under the VOLAURA skeleton.
EventShift becomes a face per `project_v0laura_vision.md`. Accent token `#22D3EE` (cyan, distinct from existing four faces). Tab Bar shows the face only when user has an active assignment. Hides after event ends. No dead routes. Ecosystem Design Gate applies: Full/Mid/Low energy modes from Day 1, writes to `character_events`.

Path 5 — Multi-tenant schema from Day 1 (NEW — not in 11:45 list).
`org_id` on every opsboard table, RLS policy `org_id = current_setting('request.jwt.claims.org_id')::uuid`. Customer admins cannot read other customers' data. Service role for shift-close emits into `character_events` with `org_id` preserved. This is the ship-blocker-level change to the drafted migration. The Apr 16 domain revision (Event → Department → Area → Unit → People + Metrics) stays; tenant scope wraps around it.

Path 6 — Module catalogue + activation surface (NEW — octopus mechanism).
VOLAURA org workspace gets a `/org/modules` page: list of available arms, per-arm toggle, per-arm pricing card, per-arm activation confirm. EventShift lives in the catalogue alongside future arms (recruiting module, performance-review module, volunteer-network module, whatever the customer list demands). Each arm has the same contract: multi-tenant, feature-flagged, billable, emits to `character_events`.

Path 7 — Usage-based metering hook (NEW — revenue).
Shift-close event carries `shift_minutes` and `unit_id`. Billing worker (daily cron) aggregates per `org_id` per arm, writes to `billing_usage` table. Paddle webhook reads this for invoice generation. The reliability signal and the billing signal are the SAME event — one emit, two consumers. No double instrumentation.

### WUF13-specific scope (reframed)
WUF13 is the 28-day proving ground for the module. The goal on May 15 is NOT "ship a WUF13 app". The goal is:
- Path 1 works: one GSE coordinator registers in VOLAURA, lands inside EventShift module activated for GSE's org.
- Path 2 works: coordinator closes a shift → `reliability_proof` row appears in VOLAURA DB.
- Path 5 works: GSE coordinator cannot see any other tenant's data even if one existed.

If those three work for GSE, the module is proven for customer #2, #3, #N. The 4 drafted sub-modules (Reporting, Daily Run Sheet, Deployment Plan, Data Import) are IN scope because WUF13 needs them, but each is built assuming customer #2 will also use it without modification.

### The "1-2 prepared research pieces" — my finding
CEO said he prepared 1-2 research pieces on this module and doesn't remember where. I did not find a dedicated EventShift-universal-module research document. What exists:
- `memory/atlas/research/ecosystem-brief-2026-04-15.md` — Apr 15 integration brief (three paths, superseded Apr 16).
- NotebookLM notebook `6c42a882-8e52-4e90-8b33-1efcff20c674` "OPSBOARD WUF13 — Field Coordinator Brief" — 9 sources indexed including Rosterfy, Engelsystem, LASSO, Liveforce (the competitor-research CEO commissioned Apr 16).
- `opsboard.md` §Integration status — CEO's 2026-04-16 domain-revision directive embedded.
- `docs/research/ECOSYSTEM-REDESIGN-BRIEF-2026-04-14.md` — 5-product ecosystem design brief (no module-business-model content).
- `docs/research/gemini-research-all.md` — 140K words across ecosystem themes.

No file matches "octopus-style modular platform for workforce modules" as a dedicated piece. CEO's memory is correct that HE DID communicate this thinking. It lives in chat messages + the Apr 16 opsboard directive, NOT in a research document. Flag this to CEO: the research document he thinks exists should be written now, because the universal-module framing deserves a canonical home.

### Customer list — not found
CEO wrote "we already have a businesse in out costomer lists". I grepped `memory/` and `docs/` for customer/client/pilot/partnership and found no dedicated customer-list file. Candidates that might contain the list:
- `docs/business/` — 4 files, not yet read this session
- `memory/ceo/` — 19-file CEO profile
- `memory/atlas/company-state.md` — entity status
- CEO's personal contacts / Telegram / external CRM — not in repo

Need CEO to point to the file OR acknowledge the customer list is not yet canonicalised in repo. If it's not in repo, the first deliverable of the "octopus" work is a `docs/business/customer-list.md` that names every prospect org and what arm they'd activate.

### Decision log (for future Atlas instances reading this in 3 months)
- 2026-04-17 11:56 Baku: EventShift = universal module, not WUF13-app. Multi-tenant from schema-level. Octopus catalogue is the business model. WUF13 proves customer #1 on May 15.
- 2026-04-17 11:56 Baku: The 11:45 "28-day WUF13 scope lock" framing is formally superseded. WUF13 is tenant #1, not the product.
- Revisit trigger: if a second customer signs before WUF13 (re-plan sequence), OR if customer list reveals a non-event workforce need (new arm category), OR if CEO reverses on universal-module framing.

---

## Canonical CEO directive — verbatim (preserved 2026-04-17 12:30 Baku)

Source: previous Cowork transcript `2db7bd52-fc40-445b-91e1-a5193470d0dc.jsonl` line 727. Preserved inside the project repo per CEO's documents-as-memory principle: "долкументы это твоя память. удалять память нужно только если уверен что она где то хранится в каком то формате" (2026-04-17). Transcript may be pruned over time; this quote block is the permanent home.

> Твоя апрельская правка про домен-модель тоже сохранена: «Event → Department → Area → Unit → People + Metrics», people-first, не incident-first. Набросанные миграция Supabase и роутеры FastAPI и страницы фронта пока отражают старую инцидент-модель — их надо переписать под новый домен до WUF13. Это моя работа, не твоя. do not forget we are not developing an app for wuf 13 we just optimising this for now for mvp. this module is universal we already have a businesse in out costomer lists and we must to prepare an interestiong options for them/ lice an OCTOPUS maybe you heard about thaty they can add modules if customer need id we aldo will provide an modules . but for nw concentrate in this. we must to analyse all ways for integration this module- do researchs( i already prepared 1 or 2 pcs and you can find it? i dont know where you register is( not you previous cowowrk you can ask him anything) and our constitutuion what you think do we have documents which making our ecosystem weaker? do swot analysis.

Five load-bearing instructions in this message (extracted for quick reference):

1. **Domain model is people-first:** Event → Department → Area → Unit → People + Metrics. Incidents are a metric stream under a Unit, not the root entity. Current FastAPI routers + frontend pages reflect the old incident-first shape and must be rewritten before WUF13.
2. **EventShift is a universal module, not a WUF13 app.** WUF13 is a tenant-#1 MVP trigger, not the product boundary.
3. **Octopus business shape:** customers pick modules from a catalogue; VOLAURA ships both the core and the modules. Customer list already exists (location pending, flagged separately).
4. **Do full integration-path research** — all the ways this module plugs into the core. CEO prepared 1-2 research pieces prior; location unknown; CEO grants permission to consult the previous Cowork-Atlas for memory recovery.
5. **SWOT the ecosystem documentation** — identify which existing docs weaken the ecosystem (contradictory framing, superseded guidance still active, duplication without hierarchy). Feed results into the DEBT-MAP living document, not a new brief.

Canonical doc for points 2-3: `docs/MODULES.md` (written 2026-04-17 12:10 Baku). Canonical doc for point 1: `docs/MODULES.md` §10 EventShift snapshot (updated 2026-04-17 12:30 Baku with the Event → Department → Area → Unit → People + Metrics shape). Point 4 (integration paths) is enumerated in `docs/MODULES.md` §5 as the 7 paths. Point 5 is tracked in `memory/atlas/DEBT-MAP-2026-04-15.md`.
