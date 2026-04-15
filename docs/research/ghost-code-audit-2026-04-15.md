# Ghost-code audit — VOLAURA monorepo

**Date:** 2026-04-15 · **Authors:** 4 parallel subagents (fix-archaeology, comment-drift, dead-wiring, silent-swallow) invoked by Terminal-Atlas
**Triggered by:** CEO — "вот таких ошибок у нас по проекту много, я так чувствую. есть способ проверить?"
**Prior reference:** INC-017 (Google OAuth broken 11 days, documented in `memory/atlas/incidents.md`)

---

## Executive summary

Nineteen findings across four categories. Three are revenue- or data-affecting and should be fixed before the week closes. Five are latent risks that will surface under load. The remainder are cleanup candidates.

The dominant failure mode is NOT "bad code written from scratch" — it is **confident fix commits whose diagnosis was wrong**. INC-017 is not unique. Seven commits from the last 30 days follow the same pattern: confident commit message, short diff, claim "root cause" of a subtle async / caching / pool-level bug, silently break a different path. Team-level pattern, not one-person bug.

---

## 1. Fix-of-fix archaeology (10 suspects)

### 1.1 `cbfab59` — remove Claude fallback from model router · 2026-04-14
Self-reverted 15 minutes later by `703153d`. CEO verbal directive → impulse delete of safety net with no test that chain tail still terminates. In the 15-minute window, any user-facing LLM call with all free tiers 429 would have surfaced `None` → 503. Verify: `apps/api/app/services/model_router.py` `SAFE_USER_FACING` chain terminates at `_sonnet_last_resort`; verify all call sites handle `None`.
**Confidence:** High (proves the pattern is live — not a hypothetical risk).

### 1.2 `9c48c93` — archive 33 swarm modules · 2026-04-12
Followed by 5 fix commits (`4ba5a31`, `c0546c9`, `ebebd9f`, `0f6aa29`, `12ab7fd`) patching CI workflows and scheduled tasks that referenced archived modules by string name. Archive was done against the import graph; YAML dispatch was not in the graph. `execute_proposal.py` was created 3 days prior and archived as dead — autonomous proposal processing may be silently orphaned.
**Action:** grep every archived swarm module name across `.github/workflows/**`, `.claude/scheduled_tasks.json`, `scripts/**`. Fix any `try/except ImportError: pass` fallbacks that now run with degraded capability.
**Confidence:** High.

### 1.3 `5c0b006` — submit_answer stops pre-marking session completed · 2026-04-11
Moves the finalisation DB write from `submit_answer` to `/complete`. Client `is_complete` now derived from `state.stopped` only. If any consumer (retest cooldown queries, admin dashboards, Telegram bot) polls `assessment_sessions.status`, they get `in_progress` on naturally-finishing CAT sessions until `/complete` lands. If `/complete` ever fails mid-pipeline, session is forever `in_progress` with no AURA row.
**Verify:** `apps/api/app/services/assessment/helpers.py:146`; grep all `eq("status", "completed")` reads.
**Confidence:** Medium-High.

### 1.4 `8f8cd49` — simplify atlas wake (4-step → 1-step) · 2026-04-14
Removed curl health check + gh run list + inbox ls + breadcrumb stat. Doubled cadence. Now relies entirely on `atlas-self-wake.yml` writing heartbeat server-side. If that workflow goes red, Atlas wakes blind without knowing.
**Verify:** `atlas-watchdog.yml` actually catches this failure mode.
**Confidence:** Medium.

### 1.5 `0f6aa29` + chain — watchdog (4 patches in 4 hours) · 2026-04-14
Brand-new code patched four times same day. Final state: "exit 0 on successful alert delivery — alert IS the signal." This hides subsequent red state from CI. Cooldown relies on committing JSONL back to main from a CI job — push race with another workflow silently re-enables alert spam.
**Confidence:** Medium.

### 1.6 `2b449b2` + `6aeab64` + `c8abdd4` + `e63da29` — Telegram free-text routing cascade
**Three fix-of-fix cycles on the same handler in 2 days.** Old handler saved messages → new one didn't → CEO inbox empty 48h → fix restored `_save_message` → found category mismatched DB CHECK → fix → found `message_type='atlas'` rejected by another CHECK → fix. Atlas memory silently lost data while looking healthy. Exact INC-017 pattern.
**Verify:** every DB write in `_handle_atlas` against its table's CHECK constraints.
**Confidence:** High — three documented cycles prove the pattern here specifically.

### 1.7 `d927128` — zeus RPC hardening
Self-admits: "previous migration revoked EXECUTE from PUBLIC and anon but NOT from authenticated" — the pre-fix wrong mental model of Supabase default grants, with ~10 minutes of live exposure. Verify current state covers all roles including future additions.
**Confidence:** Medium.

### 1.8 `e7518af` / `588ff69` / `ca1abaf` — Atlas provider whiplash · 2026-04-12 (2h window)
Vertex → Groq → Groq+fallback within 2 hours. Each commit confident the new chain is right. Signal: first-line diagnosis (Gemini 429) correct, response (swap provider) repeatedly made without reading the new provider's rate-limit handling.
**Confidence:** Medium.

### 1.9 `3a6b73e` — auth-bridge 5-model peer critique
Commit explicitly flags "What is still NOT verified" and rejects Nemotron + Kimi external critiques as "pattern-matching." Dismissing two external reviewers without line-level verification = INC-017 confidence profile.
**Verify:** `apps/api/app/routers/auth_bridge.py` `_create_shadow_user` race-retry `err_text` markers match actual supabase-py error strings.
**Confidence:** Medium.

### 1.10 `6aeab64` — `_classify_and_respond` declared dead code · 2026-04-12
Same class as INC-017 — "X is dead" without verifying side effects. If it had metrics / routing / audit hooks beyond `_save_message`, they're gone.
**Verify:** `git grep _classify_and_respond` — truly zero references.

### Meta-patterns

- **Provider flip-flop in one afternoon** (×2 occurrences) — root cause: CEO verbal directive → code change → no test → no read of all call sites. Fix gate: any change to `model_router.SAFE_USER_FACING` must include unit test asserting chain tail never returns None.
- **Archive-as-dead without YAML dispatch check** — swarm modules found by name in workflows, not by import graph. Fix gate: pre-archive checklist = grep all `.github/workflows/`, `.claude/scheduled_tasks.json`, `scripts/` for the module name.
- **Handler consolidation losing silent obligations** — telegram_webhook lost save + category mapping + message_type in three cycles. Fix gate: any handler consolidation must enumerate the OLD handler's DB constraints and port them as explicit asserts.
- **Overconfident commit on short diff** (×3) — inverse correlation between diff size and blast radius. Fix gate: any commit claiming "Root cause:" with delta <20 lines on auth/async/middleware requires a regression test in the same commit.
- **Dismissing external critique by argument** — when 2+ reviewers flag the same line, verify by reading the line, not by asserting they were wrong.

---

## 2. Comment-vs-code drift (5 findings)

### 2.1 `supabase/migrations/20260324000015_rls_audit_fixes.sql:290-294` — RLS under-enforces
Comment: "Volunteers may only move their row to cancelled / All other fields must be unchanged."
Reality: `WITH CHECK (status = 'cancelled')` only checks that column. Volunteer can simultaneously self-award `coordinator_rating`, rewrite `coordinator_feedback`, alter `check_in_code`. The "enforced at application layer too" parenthetical hides RLS-alone insufficiency — exposing direct PostgREST/mobile clients.
**Confidence:** High. **Fix:** add `AND (OLD.* IS NOT DISTINCT FROM NEW.* EXCEPT status)` equivalent or convert to a stored-procedure gate.

### 2.2 `supabase/migrations/20260328000040_atomic_crystal_deduction.sql:35-36`
Comment promises atomic SELECT+INSERT per user via `pg_advisory_lock` (session-scoped).
Reality: pooled PostgREST reuses connections. If backend is killed between lock and unlock (statement timeout, OOM, signal before `EXCEPTION WHEN OTHERS`), next request on same connection sees zombie lock. Idiomatic fix: `pg_advisory_xact_lock` (transaction-scoped).
**Confidence:** Medium. **Fix:** switch to xact variant.

### 2.3 `apps/api/app/routers/telegram_webhook.py:695` — TOCTOU claim false
Comment: "Atomic write: temp file + rename prevents TOCTOU race (P1-02)."
Reality: `os.replace` prevents partial-write corruption. The TOCTOU window is between `json.load` (line 680) and `os.replace`. Two CEO button presses on different proposals both read same snapshot, second write clobbers first's decision.
**Confidence:** High. **Fix:** file lock (fcntl.flock) around read+write, or move state to a DB row with optimistic versioning.

### 2.4 `apps/api/app/core/assessment/engine.py:354-357` — math mismatch
Comment justifies ±20 clamp (sigmoid saturation); code clamps at ±500. No immediate bug (exp(500) < float max), but trap for future editor widening past 709.
**Confidence:** Medium. **Fix:** update comment to match constant or tighten clamp.

### 2.5 `apps/web/src/lib/supabase/middleware.ts:40-44` — refresh claim partial
Comment: "Refresh the auth token — this is the critical call."
Reality: refresh only propagates when the SAME response object is returned. On the unauth-protected-route branch, `NextResponse.redirect(loginUrl)` is a new response — any Set-Cookie from `setAll` is discarded. Rare but real.
**Confidence:** Medium. **Fix:** explicitly copy cookies onto redirect response.

---

## 3. Dead wiring (2 hard + 1 soft)

### 3.1 `DID_API_KEY` — declared, never read
`apps/api/app/config.py:135`. No other reference anywhere. Planned D-ID Lite integration never shipped. Cleanup candidate per ADR-007.

### 3.2 `DEEPSEEK_API_KEY` in `apps/api/app/`
Declared in `config.py:37`, used by `packages/swarm/` (engine, research, providers) but **never referenced inside `apps/api/app/`**. ADR-007 flags for deletion. Live in swarm, dead in API.

### 3.3 `useRealtimeNotifications` — subscriber without confirmed publisher (soft)
`apps/web/src/hooks/queries/use-notifications.ts:106` subscribes to `postgres_changes` INSERT on `public.notifications`. Couldn't confirm any backend path INSERTs into that table.
**Action:** grep `notifications" ` table writes in `apps/api/` — if zero, the realtime hook is a phantom listener.

**All 28 FastAPI routers are wired** in `apps/api/app/main.py:192-220`. No dead backend endpoints. No dead Next.js route handlers detected. Background workers (`reeval_worker`, `video_generation_worker`) both launched in `main.py:94,97`.

---

## 4. Silent swallows (3 P0 + 5 P1)

### P0-1 — Stripe subscription.updated / deleted revenue loss
**File:** `apps/api/app/routers/subscription.py:446-489`
**Bug:** `_handle_subscription_updated` and `_handle_subscription_deleted` return None. In the webhook dispatcher (line 318, 322), return is discarded. `_update_profile_subscription` returns False if no profile matches `stripe_customer_id`. For `.created` a False raises 500 so Stripe retries. For `.updated/.deleted` False is dropped, event marked processed, webhook returns 200.
**Impact:** Cancelled subscriptions stay `active` forever. Downgrades ignored. Paid users lose access with no trace. **Unrecoverable without manual SQL reconciliation.**
**Fix:** mirror `.created` path — capture bool, raise 500 on False.
**Severity:** P0. **Money-affecting.** Should ship before any Stripe traffic goes live if it isn't already.

### P0-2 — `pending_aura_sync` flag write silently dropped
**File:** `apps/api/app/routers/assessment.py:811-819`
**Bug:** After RPC retry for `upsert_aura_score` fails, code tries to set `pending_aura_sync=True`. If that flag write also fails → `except Exception: pass`. No log, no retry queue.
**Impact:** User finished assessment, AURA never persisted, no marker, no background reconciler will ever pick it up. Ghost session.
**Fix:** `logger.error`; long-term add `assessment_sync_deadletter` table.

### P0-3 — Telegram `_save_message` log-and-proceed
**File:** `apps/api/app/routers/telegram_webhook.py:100-114`
**Bug:** DB save fails (RLS, timeout) → logged, caller proceeds as if saved. Conversation persistence desyncs, `_get_recent_context` returns stale.
**Impact:** Atlas loses thread; CEO can't audit. Silently.
**Fix:** escalate via out-of-band channel OR local-file fallback queue.

### P1 (5)
1. `assessment.py:862, 894, 912, 946` — crystal events, badge-tier events, analytics, email on assessment complete all `except Exception: pass`. Comment says "must never fail assessment completion" — correct intent, wrong implementation (no log, no deadletter). **Life Simulator doesn't get crystals. BrandedBy doesn't know about badge tier. MindShift doesn't route.** User sees new badge in VOLAURA, zero crystals in game. This undermines the whole ecosystem-integration story.
2. `core/assessment/quality_gate.py:115, 239, 311, 412` — malformed `concepts` JSON → empty list silently → anti-gaming gates weaken. "Verified talent platform" marketing collides with silent gate bypass.
3. `assessment/[sessionId]/page.tsx:266` — mid-assessment API swallow with "still usable" comment. No way to verify in prod.
4. `assessment/[sessionId]/complete/page.tsx:208, 218` — AURA + username fetch failures on results page render empty without retry.
5. `assessment.py:168` — admin role check exception → fail-closed (correct) but no log. DB outage = every admin silently rate-limited.

### P2 — intentional non-blocking with comment (11 locations — listed in raw agent output)

Includes Langfuse flush, optional JWT personalisation, Stripe idempotency insert (race-safe), LLM provider fallback chain (documented), browser Web Share fallback, analytics failures documented non-blocking.

---

## 5. Recommended actions (ranked)

**Ship this week (revenue + data integrity):**
1. **Stripe P0-1** — symmetric error handling on `.updated`/`.deleted`. Single file, ~10 lines. Ship before any Stripe traffic matters.
2. **Assessment P0-2 + ecosystem P1** — convert `except: pass` to `except: logger.error` + add `character_events_deadletter` table for failed crystal/badge/email events. One migration + one wrapper function.
3. **Swarm archive aftermath** — grep-audit `.github/workflows/` against 9c48c93 archived modules. Fix any silent ImportError fallbacks.

**Ship this sprint (attack surface):**
4. **RLS under-enforce on registrations** — tighten `WITH CHECK` to prevent rating/feedback tampering.
5. **TOCTOU on proposals.json** — file lock or DB migration with optimistic version.
6. **Model router chain None-handling** — unit test asserting `SAFE_USER_FACING` tail.

**Cleanup (non-urgent):**
7. Delete `DID_API_KEY`, `DEEPSEEK_API_KEY` from API config per ADR-007.
8. Update comment on engine.py:354 to match code.
9. Middleware.ts:40-44 — copy cookies to redirect response.
10. Decide `useRealtimeNotifications` — wire publisher or remove subscriber.
11. Telegram webhook handler constraint enumeration (prevent 4th cascade fix).

**Process changes (prevent next INC-017):**
- Pre-commit check: any `git commit -m "fix(...): Root cause:..."` on `auth|middleware|webhook|subscription|rls` paths with diff <20 lines → CI requires an accompanying regression test.
- Pre-archive check: grep module names across YAML + scheduled-tasks JSON before moving to `archive/`.
- Team rule: when 2 external reviewers (Nemotron, Kimi, any peer) flag the same line, verify with a tool call, not an argument.

---

## 6. Raw agent outputs

Full reports from each of the four agents are preserved in the turn transcript (2026-04-15). If needed for audit, they contain additional file-line citations per finding.

**Token cost for this audit:** ~358K tokens across 4 parallel agents (NVIDIA/Cerebras/Anthropic mix via subagent_type default routing). Wall time ~6 minutes. $0 direct cost (free tiers).
