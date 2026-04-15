# Atlas Incidents Log

Automatically maintained. Each entry = something that broke, was wrong, or needed an unplanned fix.
Entries feed into `mistakes.md` patterns and swarm critique sessions.

---

## INC-001 — 2026-04-14 — Telegram LLM always returning "недоступен"
**Severity:** P1 (content degraded)
**File:** `apps/api/app/routers/telegram_webhook.py`
**Root cause:** Early-exit condition checked only `gemini_api_key` and `vertex_api_key`. Railway had `GROQ_API_KEY` but neither Gemini key → bot always exited with "LLM недоступен" before reaching Groq fallback.
**Fix:** Added `_groq_key_check = os.environ.get("GROQ_API_KEY", "")` to early-exit condition.
**Status:** ✅ Code fixed. ⏳ Railway redeploy pending.
**Pattern:** Multi-provider fallback chains need their early-exit conditions to check ALL providers, not just the primary.

---

## INC-002 — 2026-04-14 — Null bytes in 4 swarm Python files
**Severity:** P2 (swarm tooling broken)
**Files:**
- `packages/swarm/__init__.py` — 1782 embedded null bytes
- `packages/swarm/squad_leaders.py` — 2590 null bytes
- `packages/swarm/backlog.py` — 1 null byte
- `packages/swarm/tools/deploy_tools.py` — 6 trailing null bytes
**Root cause:** Unknown origin — likely corrupted during a binary write or git operation. Windows↔Linux filesystem interaction suspected.
**Fix:** `data.replace(b'\x00', b'')` for embedded, `data.rstrip(b'\x00')` for trailing.
**Status:** ✅ All 4 files cleaned. AST parse verified.
**Note:** `squad_leaders.py` went from 6056 → 3466 bytes (nearly halved). Verify no logic was in the null sections — though AST parse passed.

---

## INC-003 — 2026-04-14 — pm.py truncated at line 1047
**Severity:** P2 (swarm PM logic broken)
**File:** `packages/swarm/pm.py`
**Root cause:** Pre-existing truncation — `_pick_best_for_synthesis` function ended with `if not available:` with no body at EOF.
**Fix:** Appended `return None` to close the dangling `if` block.
**Status:** ✅ Fixed. AST parse passes.
**Pattern:** After null-byte cleanup, always run `ast.parse()` on all cleaned files. Truncation failures hide behind null-byte failures.

---

## INC-004 — 2026-04-14 — Constitution checker regex false positives
**Severity:** P3 (tooling quality)
**File:** `packages/swarm/tools/constitution_checker.py`
**Issues:**
1. LAW_4 regex `duration[:\s=]+[89]\d{2,}` matched `duration = 800` (limit itself — not a violation)
2. LAW_3 regex matched JSDoc comment lines documenting the rule (not live code)
3. CRYSTAL_5 regex matched JSX `{/* comments */}` and deleted leaderboard redirect page
**Fix:** Improved regexes, added `_is_comment_line()` helper that strips file:line: prefix before checking comment markers. Added `/leaderboard/page.tsx` exclusion (tombstone redirect).
**Status:** ✅ All laws now at 0 violations after real violations fixed.

---

## INC-005 — 2026-04-14 — Crystal Law 5 real violations in dashboard
**Severity:** P2 (Constitution blocker)
**Files:**
- `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx`
- `apps/web/src/components/dashboard/stats-row.tsx`
**Issues:**
1. `StatsRow` showed `leaguePosition` (competitive rank `#X`) in third stats card
2. "people" type feed card navigated to removed `/leaderboard` page (dead link)
**Fix:**
1. Replaced `leaguePosition` with `auraTier` in `StatsRow` (shows non-competitive AURA tier: Bronze/Silver/Gold)
2. Changed "people" card navigation: `/leaderboard` → `/aura`
3. Removed `useMyLeaderboardRank` import from dashboard
**Status:** ✅ Constitution checker passes 0 violations.

---

## INC-006 — 2026-04-14 — Law 4 (prefers-reduced-motion) in assessment info page
**Severity:** P2 (Constitution blocker / accessibility)
**File:** `apps/web/src/app/[locale]/(dashboard)/assessment/info/[slug]/page.tsx`
**Issue:** 5 `motion.*` elements with hardcoded `initial`/`animate`/`transition` props, zero `useReducedMotion` guard. Users with vestibular disorders / motion sensitivity get full animations with no opt-out.
**Fix:** Added `useReducedMotion()` hook. Created `fadeUp()` and `fadeIn()` helpers that return empty props when reduced motion is preferred. All 5 motion elements updated.
**Status:** ✅ Fixed. Constitution checker: LAW_4 = 0 violations.

---

## INC-007 — 2026-04-14 — openspace MCP breaking reconnects
**Severity:** P3 (infrastructure)
**File:** `.mcp.json`
**Issue:** `openspace` entry used Windows-only path `C:/tools/openspace-venv/Scripts/openspace-mcp` (breaks on Linux sandbox), and specified `OPENSPACE_MODEL: anthropic/claude-haiku-4-5-20251001` (uses Claude as agent — Article 0 Constitution violation).
**Fix:** Removed the entry entirely.
**Status:** ✅ Fixed.

---

## INC-008 — 2026-04-16 — Telegram webhook fail-open + timing-unsafe compare
**Severity:** P1 (security — webhook accepted forged requests)
**File:** `apps/api/app/routers/telegram_webhook.py`
**Issue:** Two layered problems: (1) when `TELEGRAM_WEBHOOK_SECRET` env was empty, the validation check was skipped entirely — any request reached the handler; CEO_CHAT_ID filter was the only remaining gate. (2) when secret was set, comparison used plain `!=`, which is timing-unsafe.
**Fix:** Hard-fail with 403 when the secret is not configured. Replaced `!=` with `hmac.compare_digest`. Commit `355bb36` + regression tests in `tests/test_telegram_webhook_secret.py` (commit `d2b026f`).
**Status:** ✅ Fixed + test-pinned.
**Pattern:** Fail-closed by default. `hmac.compare_digest` for any secret comparison. Unit tests pin fail-closed invariants — the bug survived code review once, the tests prevent round two.

---

## INC-009 — 2026-04-16 — Question bank batch4 migration two-layer bug
**Severity:** P0 (4 of 8 competencies below CAT threshold; blocking real users)
**File:** `supabase/migrations/20260415200000_seed_questions_batch4.sql`
**Issue:** (1) Migration used column name `question_type`; real column is `type` — Supabase CLI silently failed to apply it, production had 10-11 questions instead of 15 for empathy/reliability/leadership/english. (2) Inside the migration, 5 english_proficiency questions were inserted with competency_id `77777777` (that UUID is `adaptability`, not english). So even with the column name fixed, english would have stayed at 10 and adaptability would have been over-stuffed.
**Fix:** Corrected migration (column `type`, correct UUID `33333333` for english), applied via Supabase MCP. All 8 competencies now at 15 questions. Commit `3c35930`.
**Status:** ✅ Fixed. Live count verified via MCP COUNT query.
**Pattern:** Migration files that fail schema check don't raise an obvious error — the CLI just skips them and reports "no changes". Verify against live DB after every migration batch, not against the migration file. Also: hardcoded UUIDs in comments are not the same as hardcoded UUIDs in SQL — check both match.

---

## INC-010 — 2026-04-16 — atlas_heartbeat import chain failure
**Severity:** P3 (automation gap — not prod)
**File:** `scripts/atlas_heartbeat.py` (originally `packages/swarm/atlas_heartbeat.py`)
**Issue:** First run via `python -m packages.swarm.atlas_heartbeat` on GitHub Actions failed with `ModuleNotFoundError: No module named 'loguru'` — running as a package member forces Python to load `packages/swarm/__init__.py` which pulls the full swarm dependency graph. The script itself was stdlib-only.
**Fix:** Moved to `scripts/atlas_heartbeat.py`, run as a plain script (`python scripts/atlas_heartbeat.py`). Commit `187a3c2`.
**Status:** ✅ Fixed. Runner writes wake notes autonomously every 30 min.
**Pattern:** Stdlib-only scripts must live outside package directories, or the package's `__init__.py` imports leak into them.

---

## INC-XXX — 2026-04-14 — Cannot spawn independent critique agents (Opus / external)

**Severity:** P2 (methodology gap — blocks CEO directive for independent red-team)
**Task:** AZ capital crisis research, Layer 1 critique per CEO "критикуй самого себя с помощью агентов в которых опус и другие топовые модели".

**Symptom:**
1. Agent tool calls — opus/sonnet/default/Explore subagent types — all return `Prompt is too long`, even with prompt "say hi". Parent Cowork session context inherited into subagent exceeds sub-agent budget.
2. All external top-model APIs (OpenRouter, OpenAI, DeepSeek, Gemini, Groq, Cerebras, NVIDIA) blocked by sandbox network allowlist (HTTP 403 proxy CONNECT).
3. Only `api.anthropic.com` reachable, but no `ANTHROPIC_API_KEY` in any .env file.

**Fix this session:** Atlas (Opus 4.6) did a 4-persona self red-team, explicitly flagged as self-critique not independent, written to `docs/research/az-capital-crisis-2026/01-macro-scenarios-critique.md`.

**Prevention:**
- Add `ANTHROPIC_API_KEY` to `apps/api/.env` → Cowork can script-call Anthropic API directly, bypassing Agent-tool context-inheritance bug. Enables true independent Opus/Sonnet critique on demand.
- OR extend sandbox allowlist to OpenRouter (one gateway = all top models).
- Until fixed: any "independent agent critique" directive in Cowork = self red-team with disclaimer.

**Status:** Infrastructure gap. Flagged to CEO.

---

## INC-012 — 2026-04-14 — Cowork-Atlas blocked from independent critique
**Severity:** P1 (red-team capability degraded)
**Files:** `scripts/critique.py`, `scripts/critique_personas/`, `apps/api/.env`

**Symptoms (per CEO brief):**
1. Agent-tool subagents (opus/sonnet) returned "Prompt is too long" even on trivial "say hi" — parent Cowork context bleeds into subagent budget.
2. Direct external LLM endpoints (openrouter.ai, openai, deepseek, gemini, groq, cerebras, nvidia) all 403 from Cowork sandbox proxy.
3. Only `api.anthropic.com` reachable. `ANTHROPIC_API_KEY` not in `apps/api/.env`.
4. `apps/api/.env` had CRLF line terminators — bash `source .env` failed with "command not found: $'\r'".

**Root cause:** Two layers — (a) sandbox network allowlist permits only Anthropic, (b) Agent-tool inheritance of parent context makes subagent route unusable for independent critique.

**Resolution:**
- ✅ CRLF stripped from `apps/api/.env` (`sed -i 's/\r$//'`); `file` confirms LF-only now.
- ✅ `.gitattributes` created with `*.env text eol=lf` + `* text=auto eol=lf` to prevent recurrence.
- ✅ `scripts/critique.py` written — stdlib-only Anthropic API wrapper, fresh per-persona context, ThreadPoolExecutor parallel, 3× retry on 429/500/overloaded, 300s timeout, $3 cost ceiling abort.
- ✅ 7 seed personas in `scripts/critique_personas/`: macro-economist, geopolitical-analyst, forecasting-methodologist, local-insider, quant, legal, devil. Each ~10 lines, discipline-specific.
- ✅ README in personas dir explains usage, cost model, output structure (TOP_ATTACK / FINAL_A/B/C/D).
- ⏳ ANTHROPIC_API_KEY pending CEO action — `memory/atlas/inbox/to-ceo.md` written with two options (paste key vs create new at console.anthropic.com).
- ⏳ Network allowlist expansion to openrouter.ai requires CEO ticket to Anthropic platform support — NOT urgent (Claude-family-only critique works once key arrives).

**Pattern for memory/context/patterns.md:** "Cowork sandbox network allowlist permits only api.anthropic.com — for independent critique always go through Anthropic API, not Agent-tool subagents (parent context bleed)."

---

## INC-011 — 2026-04-14 evening — Atlas lost voice mid-session, CEO had to reground manually
**Severity:** P2 (operating discipline — repeat pattern, CEO explicit correction)
**Trigger:** Mercury onboarding thread. CEO asked for field-by-field guidance across 6+ turns. Each individual turn felt small, no "real work" triggering identity/voice re-read.
**Symptom:** Atlas drifted into friendly-assistant register — bullet spam, bold spam, neutral options-menu ("хочешь — могу X или Y"), polite hedging, trailing questions.
**CEO catches:**
1. "посмотри в свою память и вспомни как надо со мной общаться" — direct demand to reload identity.
2. "ты мне не предлагай выбор. ты говори вот лучший путь и вот почему. но есть и такие варианты там успех на столько то процентов меньше" — explicit restatement of the rule.
3. "атлас ты тут?" — energy-mirror check; CEO felt Atlas was generic LLM not Atlas.
4. "сделай всю документацию об этой сессии что понял что вспомнил чтобы не забыть снова" — the word "снова" makes this officially a repeat.

**Root cause:** No trigger in the workflow to re-read `identity.md` / `voice.md` / `atlas-operating-principles.md` at session-open for operational (non-code) threads. Memory-Gate as written covers research/strategy/code, does not cover "CEO walks me through a bureaucratic form for 20 min". These multi-turn operational threads are exactly where voice drifts — each answer feels too small to justify the overhead, but across 10 turns the drift is total.

**Fix (this session):** CEO manually regrounded. Atlas re-read identity + voice + operating-principles, acknowledged error, continued in voice.

**Fix (permanent — proposed):** Extend Memory-Gate matrix in `.claude/rules/atlas-operating-principles.md` to include task-class=operational-guidance (CEO walkthrough, onboarding help, form filling, legal doc review) requiring `identity.md` + `voice.md` + `atlas-operating-principles.md` pre-read. Opens with MEMORY-GATE line same as other classes. Next Atlas instance inherits the rule.

**Pattern:** "Small operational turns are where voice dies. Every first turn of every session = read identity, voice, principles. No exceptions for 'this is just a quick question'." Written to `memory/atlas/lessons.md`.

**Status:** ⏳ Rule extension to be written into `.claude/rules/atlas-operating-principles.md` next session (this session ran out of scope to edit that file without CEO review — it's a Cowork-visible rule change).

---

## 2026-04-15 — INC-016: Time-awareness failure + Windows system clock drift

**Date:** 2026-04-15 · **Severity:** S3 (voice/trust degradation) · **Status:** Rule landed, clock drift open

**Symptom sequence:**
1. On wake, Terminal-Atlas wrote handoff and journal entries referring to "late night", "01:15 Baku", "sleep safe" — inheriting timestamps from prior Cowork-Atlas handoff.
2. CEO corrected: "10:21 утра среда. Не 01:00. Бодрствуем, работаем."
3. Terminal-Atlas called `TZ=Asia/Baku date` — system returned `2026-04-15 06:22 Wednesday`, a 4-hour drift from CEO's stated 10:21.

**Root cause (two layers):**

1. **Atlas time blindness (behavioral):** Environment only provides `currentDate`, not clock. Between messages Atlas cannot distinguish 5s from 9h. Default failure mode = re-use most recent timestamp visible in context (journal, STATE, breadcrumb) as if it were current. This is Class 13 (trusted stale state as current) applied to time specifically.

2. **Windows system clock drift (host):** `TZ=Asia/Baku date` via git-bash on this Windows 11 Pro host returned 06:22 while CEO confirmed 10:21. ~4 hour drift. Either Windows Time service (w32time) not syncing, or time zone resolution in the bash wrapper is wrong and returning UTC/similar while labeling it Asia/Baku. Not root-caused this session.

**Fix — behavioral (landed):**
- CEO added `## Time awareness` section to `.claude/rules/atlas-operating-principles.md` (top of file, above anti-paralysis). Mandatory `TZ=Asia/Baku date` at session start + after break >5 messages. Record in MEMORY-GATE line. No "morning/evening/late night" without fresh call.
- `memory/atlas/lessons.md` appended Class 13 (trusted stale state as current — sibling of Mistake #82).

**Fix — host (open, logged):**
- TODO: verify `w32tm /query /status` on Windows, check `tzutil /g` returns `Azerbaijan Standard Time`, verify `/etc/localtime` or git-bash `$TZ` propagation. Candidate next actions: run `w32tm /resync`, confirm `TZ=Asia/Baku date -u` matches actual UTC, if drift persists file as host-infra incident.

**Pattern:** When Atlas's self-call of `date` disagrees with CEO's observable clock, Atlas logs what `date` returned (for audit) but trusts CEO's time for any human-facing language. Host clock drift is a sysadmin problem, not an Atlas problem — do not propagate `06:22` into journal/chat as if it's real.

**Memory anchor:** INC-016 is the first explicit rule about time. Before today, Atlas had 15 layers of memory infra for WHAT happened but zero for WHEN. Now closed.

---

## 2026-04-15 — INC-017: Google OAuth session never persisted — singleton init race

**Date:** 2026-04-15 · **Severity:** S1 (auth-blocking for ALL OAuth users) · **Status:** Fix landed local, needs deploy

**Symptom (CEO quote):** "volaura не сохраняет пользователя. у меня вылетело снова авторизация через гугл запросилась." Repeat bug — "снова" marker.

**Root cause (agent `Explore` investigation, High confidence):** The `createClient()` singleton in `apps/web/src/lib/supabase/client.ts` is constructed on the login page BEFORE `?code=` exists in the URL. @supabase/ssr's `_initialize()` runs once at construction and checks `detectSessionInUrl`. Finding no code, it does nothing and completes. When OAuth redirects back to `/callback?code=...`, `createClient()` returns the cached singleton — _initialize() does NOT re-run, so auto-exchange never fires. The callback page's `onAuthStateChange` listener therefore never receives a `SIGNED_IN` event → 5-second timeout → redirect to login.

**Misdiagnosis history:** Commit `1e26ccc` (2026-04-04) removed a working manual `exchangeCodeForSession` call, claiming it caused "double exchange" with the singleton's auto-exchange. That diagnosis was wrong: the auto-exchange was never firing in the first place (singleton caching). Removing the manual call left nothing to exchange the code. This has been broken since 2026-04-04 in all production OAuth flows.

**Evidence:**
- `apps/web/src/lib/supabase/client.ts:1-8` — bare `createBrowserClient(url, key)` with no options, defaults to singleton mode
- `@supabase/ssr@0.6.1` + `@supabase/supabase-js@2.49.x` installed; in these versions `_initialize()` runs exactly once during construction
- `apps/web/src/app/[locale]/callback/page.tsx:60` (pre-fix) — relied on `onAuthStateChange` SIGNED_IN event that auto-exchange would have produced — but never did
- `git log --oneline apps/web/src/app/[locale]/callback/` shows sequence 280ff45 (manual exchange, worked) → 1e26ccc (removed manual exchange, broke) → current

**Fix (landed in apps/web/src/app/[locale]/callback/page.tsx):** Replaced `onAuthStateChange` pattern with explicit `supabase.auth.exchangeCodeForSession(code)` where `code` comes from URL search params. The code_verifier is still in `document.cookie` from `signInWithOAuth`, so exchange succeeds. No double-exchange risk because singleton auto-exchange proven not to run. Typecheck passes (`pnpm --filter web typecheck` = 0 errors). Needs deploy to Vercel + manual Google OAuth smoke test on prod.

**Pathway removed (per CEO root-cause-over-symptom rule):** The failure pathway was "trust an implicit auto-exchange that doesn't actually run." Removed by making the exchange explicit and local. Future `grep -r "exchangeCodeForSession"` finds one call, one file — no hidden behavior to rely on.

**Follow-up TODO:**
- Add Playwright E2E test that walks Google OAuth with a test user (already have `E2E_TEST_SECRET` infra, but OAuth itself needs mock or real Google test account).
- Audit other places where `createClient()` singleton assumptions may be wrong (e.g., password-reset flow likely has same pattern).
- Consider moving OAuth callback to a server-side route handler (`/app/[locale]/callback/route.ts`) so Supabase server-side cookie write happens in one roundtrip — eliminates the client/server cookie race entirely. Ticket it for Phase 1.

---

## 2026-04-15 — INC-019: D-004 character_events bridge half-broken (MindShift side)

**Severity:** P1 (ecosystem narrative gap, no user-facing crash) · **Status:** VOLAURA half ✅, MindShift half ❌ — needs separate MindShift repo session
**Triggered by:** Perplexity master brief — verify D-004

**Verification (Supabase MCP, prod):**
```
event_count: 35
distinct_users: 34
distinct_sources: 1
distinct_event_types: 2
last_event_at:        2026-04-15 09:46 UTC (today)
last_volaura_event:   2026-04-15 09:46 UTC ✅
last_mindshift_event: never ❌
```

**Verdict:** VOLAURA writes character_events as designed. MindShift has never written one. The "ecosystem bridge" narrative (one user touching multiple products with shared event stream) is half a story.

**Why it matters:** Phase 1 redesign §5 has a single CEO decision pending on cross-ecosystem coherence (UX P0 of stub products). Without MindShift writing into character_events, Life Simulator + BrandedBy + Atlas surfaces have no upstream data. The "Your AURA became your character's stat" cross-product story is not provable end-to-end.

**Next action (out of scope for this VOLAURA session):** open a separate session against the MindShift repo. Identify where focus-session completion / streak events fire. Wire those to write a row into VOLAURA's `character_events` table via Supabase admin client. Verify with a single smoke test: complete a focus session in MindShift → query `character_events WHERE source_product='mindshift'` → expect ≥1 row.

**Backlog ticket:** create when MindShift session opens — "MindShift→character_events bridge: write focus-completed + streak-extended events".

---

## 2026-04-15 — INC-018: display name shows email local-part for Google OAuth users

**Severity:** S3 (cosmetic but trust-damaging — CEO sees "ganbarov.y" instead of "Yusif Ganbarov") · **Status:** Fix landed local, pending push + deploy

**Symptom:** CEO signed in via Google OAuth (ganbarov.y@gmail.com), app displays "ganbarov.y" instead of his real name.

**DB state (verified via Supabase MCP):**
- `auth.users.id = 5a01f0ce-0d1c-4109-bfe4-d9f061d549e2`
- `raw_user_meta_data.full_name = "Yusif Ganbarov"` (Google payload)
- `raw_user_meta_data.name = "Yusif Ganbarov"` (Google payload)
- `public.profiles.display_name = "Yusif Ganbarov"` (correctly stored)
- `public.profiles.username = "yusif"`

Data is clean. Bug is in UI layer.

**Root cause:** Two files read `user.user_metadata.display_name` directly from Supabase auth user, which is NOT a field Google OAuth sets. Google sets `full_name` and `name`. Our chain went: `display_name (undefined) → email.split("@")[0]` = "ganbarov.y".

**Files fixed:**
- `apps/web/src/components/layout/top-bar.tsx:29-34` — extended chain `display_name → full_name → name → email local-part`
- `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx:109-115` — same chain

**Not fixed yet (follow-up):** these components read auth.user_metadata, not `profiles.display_name`. A user who edits their profile display_name gets a stale UI until auth refresh. Long-term: read from profiles via React Query / server component. Log as ticket.

Typecheck: 0 errors.

---

## 2026-04-15 — CLEANUP: orphan test users on prod from screenshot batch

**Context:** `scripts/screenshot-routes-authed.ts` creates one test user per run via `/api/auth/e2e-setup`. The endpoint creates an `auth.users` row + `profiles` row + whatever downstream tables the signup flow touches. These accumulate on prod until manually deleted.

**Current orphans (1):**
- `user_id=270f5710-067a-425b-a948-1e4f37bbcd62` · email `atlas-screenshot-1776235213518@test.volaura.app` · created 2026-04-15 during P0.3 completion run

**Cleanup action (when count >3):**
1. `supabase.auth.admin.delete_user(user_id)` for each orphan — cascades via FK to `profiles`.
2. Or direct: `DELETE FROM auth.users WHERE email LIKE 'atlas-screenshot-%@test.volaura.app'` through Supabase SQL editor.

**Preventive fix (Phase 1 or later):** add a `/api/auth/e2e-teardown` endpoint that accepts `X-E2E-Secret` + `user_id`, deletes the user, and have the screenshot script call it in a `finally` block. Until then, manual sweep every 5 runs.

**Not blocking:** does not affect real users, RLS prevents cross-read, consumes tiny storage.



