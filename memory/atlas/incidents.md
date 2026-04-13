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
