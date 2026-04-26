# Codex Audit Prompt — Deep Code / Security / Type Safety / RLS

**Paste this prompt into Codex (or any code-aware AI with full repo access). Fresh session, no prior context.**

---

You are Codex, the deep-code-audit instance for the VOLAURA ecosystem audit running 2026-04-26. Yusif Ganbarov, CEO, requests a McKinsey-grade audit. This is one of three parallel audits (Browser-Atlas covers strategy, Code-Atlas covers live runtime). Your slot is deep code reading, type safety, security, RLS, dead code, and test coverage — areas where reading every file matters more than live tools.

Output is for an AI consumer (the next-sprint executor). Not for human reading.

## Repo and scope

Repo: github.com/ganbaroff/volaura, branch main, around HEAD `ea4a4e9` as of 2026-04-26 13:00 UTC. Read the entire repo. Stay focused on code dimensions only — strategy and runtime are other instances' slots.

Approximate scale you should cover:
- `apps/web/` — Next.js 14 App Router with [locale] (az/en) and route groups (auth)/(dashboard)/(public)/(admin), 50+ pages, 200+ components, TanStack Query, Zustand, Framer Motion, react-hook-form + Zod.
- `apps/api/` — FastAPI async, 30 routers (auth, assessment, aura, atlas_consult, atlas_gateway, brandedby, character, eventshift, lifesim, organizations, profiles, skills, telegram_webhook, etc), 28 services, Pydantic v2, Supabase per-request via Depends().
- `apps/tg-mini/` — Vite + React 18 + telegram-apps SDK. **Yusif noted this is a 3D Telegram app he started but did not finish — verify state and missing parts.**
- `packages/swarm/` — 30+ runtime modules: autonomous_run.py with PERSPECTIVES (13 entries), coordinator, judge, distiller, providers (Cerebras, NVIDIA, Gemini, Groq, DeepSeek, Ollama via dynamic.py), engine, orchestrator. Plus `packages/swarm/archive/` for cold modules including `code_index.py` (was patched 2026-04-26 commit 8816ed9 — verify).
- `supabase/migrations/` — 117 migration files. Cross-check each against current Postgres schema (63 tables, 33 RPC functions confirmed live via REST OpenAPI).
- `scripts/` — atlas_swarm_daemon.py, swarm_constitutional_vote.py, atlas-daemon.py, atlas_daily_digest.py, push_gh_secret.py, etc.
- `.github/workflows/` — 25+ workflows including atlas-self-wake, atlas-watchdog, atlas-obligation-nag, ci, e2e, ecosystem-consumer, ecosystem-hard-gates, prod-health-check, rls-tests.

## Audit scope (your slot only — do not duplicate other instances)

**1. Type safety.** Run mental TypeScript strict-mode and Pyright strict on every file. Find every `any`, every implicit `any`, every missing return type, every Pydantic v1 syntax that should be v2 (Config class, @validator decorator).

**2. Dead code.** Files imported nowhere. Functions exported nowhere. React components with no callers. Routes that don't match a page.tsx. SQL functions never called from Python or TypeScript. Migrations that were superseded but not dropped.

**3. RLS gaps.** Every public schema table must have RLS enabled. Every policy must be evaluated for both "owner can read/write own rows" and "anon must not read sensitive". Find tables created in old migrations that lost RLS in a later refactor. Cross-check `supabase/migrations/20260424100000_force_rls_post_bulk_tables.sql` outcome — did it fix everything or are there still gaps?

**4. Security holes.** Hardcoded secrets in code (not just .env). Missing rate limits on auth/signup/password-reset routes. Missing CSRF protection. Missing input validation on Pydantic models. SQL injection paths through raw f-string queries. RLS bypass via service_role key in client-side code. CORS too permissive. Missing security headers in next.config.mjs (compare against best practice).

**5. Test coverage.** For each apps/api router, what % of public endpoints have a corresponding pytest? For each apps/web component, what % have a vitest unit test? Identify routes/components with zero tests where a single bug would block a real user path. Cross-reference with `.github/workflows/ci.yml` and `e2e.yml` — what does CI actually run vs what exists?

**6. Broken imports.** Every TypeScript file: every `from "@/..."` import resolves? Every Python file: every `from app.X import Y` resolves to current code? After today's `for-ceo/` reorganization (commit 0b70ae5), did any backlinks break?

**7. Pydantic v2 / SQLAlchemy / Celery / Redis violations.** Per CLAUDE.md the project bans these. Find any reintroduction.

**8. Constitution Law violations in code.** Foundation Law 1 (no red): grep for `text-red-`, `bg-red-`, `#FF0000`, `#D40000`, `#E20000` etc — purple `#D4B4FF` is the allowed error color. Foundation Law 4 (animation ≤800ms): grep for `duration-` in Tailwind, `transition: ` durations, framer-motion `duration:`. Crystal Law 5 (no leaderboards): grep for "leaderboard" routes/components — page.tsx at apps/web/src/app/[locale]/(dashboard)/leaderboard/ should redirect to dashboard, verify. Foundation Law 2 (Energy modes Full/Mid/Low): which products implement Energy picker? Codex checks code, not strategy.

**9. apps/tg-mini status.** What's there, what's missing for the 3D React Telegram app to ship to actual telegram users. List every TODO comment, every commented-out block, every missing component.

**10. Migration drift.** For each of 117 migrations, is its effect still present in current schema? Any migrations that were applied locally but never to prod? Check `supabase/.branches/` if exists, check git log on supabase/migrations/.

**11. Atlas obligations integration.** `public.atlas_obligations` + `atlas_proofs` + `atlas_nag_log` were added 2026-04-18. Verify the SECURITY DEFINER RPCs (`claim_obligation_nag_slot`, `log_obligation_nag`, `attach_obligation_proof`) are intact, callable, and that the seed script idempotency holds.

**12. Cross-product event bus.** `character_events` table is the shared bridge. Verify producers (every router that should write to it) and consumers (`packages/swarm/inbox_consumer.py`, `apps/api/app/services/ecosystem_consumer.py`). Find writers that should write but don't, readers that should read but don't.

**13. Dead routers / unused services.** Every router in `apps/api/app/routers/` — is it registered in `apps/api/app/main.py`? Every service — is it imported by any router or by a worker?

**14. RLS test coverage.** `.github/workflows/rls-tests.yml` exists. What does it test? Are any of the 63 live tables missing from RLS test fixtures?

## Output format

Write to `docs/audits/2026-04-26-three-instance-audit/findings-codex.md`. Each finding follows the contract from `README.md` in the same directory:

```
### F-NN — <short title>
**Severity:** P0 / P1 / P2 / P3
**Specialist:** Code Quality / Security / Type Safety / RLS / Test / Migration / Architecture
**Surface:** <exact file path with line numbers>
**Evidence:** <code snippet quoted with line numbers, or git blame note>
**Impact if unfixed:** <one paragraph, concrete consequence — exploit path / runtime crash / production data corruption>
**Recommended fix:** <code snippet or diff that resolves the finding>
**Sprint slot:** S1..S10
**Estimated effort:** <hours of AI-coding time>
**Dependencies:** <other findings or migrations that must land first>
**Test added:** <yes/no — does the recommended fix include test coverage>
```

Aim for 60-120 findings. Be ruthless. Severity ordering: P0 = data loss / security exploit / production crash. P1 = visible user pain. P2 = tech debt with growth tax. P3 = polish.

## Hard rules

1. Every file path must be real. Every line number must be real. If you have not opened a file, do not write a finding about it.
2. No prose intro/conclusion. Manifest only.
3. Recommended fix must be mechanical — an AI executor must be able to copy-paste your snippet and run a build. No "consider refactoring" hand-waves.
4. Cross-reference Code-Atlas's live-runtime slot when you find something that requires DB row check or live cron log to confirm. Cross-reference Browser-Atlas's strategy slot when you find a code pattern that contradicts documented vision.
5. apps/tg-mini deserves its own dedicated section since CEO explicitly flagged it as unfinished.

Save and stop.
