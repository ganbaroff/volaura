# Atlas Breadcrumb — post-r2 cron ticking

**Last update:** 2026-04-21 tick 9 (P0 assessment quality fixes)
**Self-wake cron:** 14d7810d, minute 7/37 every hour, durable
**Round 2:** CLOSED. Cron ticks now tackle test-coverage roadmap one function per tick.

## Round 2 summary (merged)

- Track 1 audit: PR #74 merged — 4 REAL / 4 PARTIAL / 1 BROKEN of 10 functions.
- Track 2 debate: PR #75 merged — `test-standard-verdict.md` + `apps/api/tests/_canonical_example.py` (10 passing tests). Cerebras won 5/7 dimensions, DeepSeek won 1 and contributed 1.
- Track 3 (flagship): PR #76 merged — AURA scoring, 32 tests, 91% on `aura_reconciler`.
- FINAL-REPORT.md round 2: PR #77 merged.
- Track 3-2: PR #78 merged — assessment router pipeline, 57 tests, 39% → 78% on `routers/assessment.py`.

## Test coverage progress (cron ticks)

- Tick 1 (02:50): Track 3 AURA scoring — PR #76 — 32 tests, 91% on `aura_reconciler`
- Tick 2 (02:25): Assessment router pipeline — PR #78 — 57 tests, 39%→78% on `routers/assessment.py`
- Tick 3: bars.py — PR #80 — 45 tests, 57% → 99% on `app.core.assessment.bars`
- Tick 4: tribe_matching.py — PR #81 — 24 tests, 39% → 100% on `app.services.tribe_matching`
- Tick 4.5: test-pollution fix — PR #82 merged
- Tick 5 (2026-04-21): az_translation.py — PR #83 — 28 tests, 28% → 100% on `app.services.az_translation`
- Tick 6 (2026-04-21): email.py — PR #84 — 30 tests, 34% → 100% on `app.services.email`
- Tick 7 (2026-04-21): swarm_service 61% → 100% (PR #86) + cross_product_bridge 64% → 100% (PR #87)
- Tick 8 (2026-04-21): swarm memory audit — tested agents live, found hallucination. Fixed: project_briefing.py + injection into autonomous_run + coordinator. PR #90 merged. 12 new tests.
- Tick 9 (2026-04-21): P0+P1 assessment quality — commit 0d0064f:
  - P0: `helpers.py` — added `.eq("needs_review", False)` — PLACEHOLDER questions can no longer reach users via service-role bypass
  - P1: `assessment.py` — calibration counters (times_shown/times_correct) now incremented on every submit_answer; data was never collected before
  - 81 tests pass (69 router pipeline + 12 project briefing). NEEDS PUSH TO DEPLOY.

## What's next (pick top)

1. **Assessment router coverage** — 80% now, submit_answer edge cases (lines 550-563, 619, 633-636, 647, 694-699, 709-718, 762-774) + complete_assessment branches (1101-1361) still uncovered. Target ≥85%.

2. **Provider pinning decision** — wait for next BrandedBy refresh run (GitHub Actions hourly) to see `provider=X` in logs. If OpenAI is hitting, remove it from the brandedby background path.

3. **G3.1 end-to-end breathe test** — fresh Google account → signup → assessment → AURA → crystal → character_event visible in prod. Blocked only on human: needs a fresh browser session. NOT Atlas's to start.

4. **Watcher signal gap** — error_watcher.py doesn't monitor ecosystem consumer cursor stall or BrandedBy refresh loop failures. Real observability gap. Low effort to add 2 more checks.

## Completed this session (2026-04-25)

- PGRST106 fix committed (ecosystem_consumer RPC pattern) — d755341
- `atlas_consult.py` 84% → 96% (4 new tests) — 4244486
- `match_checker.py` 85% → 98% (8 new tests) — 9361090
- `subscription.py` 74% → 98% (17 new tests) — 0ac8afd
- All 3 pushed to main → Railway auto-deploy triggered
- Frontend 409 resume fix (body.detail?.session_id) — 5a071bb → pushed
- `error_watcher.py` verified: 98% (line 158 = __main__ guard, irrelevant)
- `notifications.py` verified: 100%
- `assessment.py` gap tests: 67% → 80%, coaching/breakdown/verify/carry-over theta — f9a2e7c
- BrandedBy claim-lock + telemetry — 2b01d09 → pushed + migration applied to prod
  - brandedby.ai_twins: refresh_locked_at, refresh_lock_token columns live
  - brandedby_claim_stale_twins RPC (FOR UPDATE SKIP LOCKED) live
  - brandedby_apply_twin_personality updated (clears lock on success)
  - brandedby_release_twin_lock RPC (failure path) live
  - llm.py: _meta param → provider + latency_ms per call
  - 15/15 tests pass

## Previously (pick top — OLD)

~~1. **Push commit 0d0064f** — P0 fix lives locally only, not deployed to Railway yet.~~
~~2. **`atlas_consult.py`** — 84% → ≥95%.~~ DONE 96%
~~3. **`match_checker.py`** — 85% → ≥95%.~~ DONE 98%
~~4. **`subscription.py` router** — 74% → ≥90%.~~ DONE 98%

5. **email.py** — DONE. 100% coverage, PR #84 merged. Release `v0.1.0-beta.1` published.
6. **bars.py** — DONE. 99% coverage, PR #80 merged.
7. **tribe_matching.py** — DONE. 100% coverage, PR #81 merged.

## Per-tick recipe (unchanged)

- Read breadcrumb, pick top item
- Check existing test file for target module (coverage %, what's already covered)
- Spawn Sonnet with prompt referencing `_canonical_example.py` + `test-standard-verdict.md`
- Target ≥90% on pure-logic modules, ≥75% on routers
- Merge, update breadcrumb, no CEO return

## Known constraints (unchanged)

- Class 17: Opus synthesizes, Sonnet executes
- Class 18: don't relay agent confidence as own verified
- Evidence-gate: file:line or tool output for every claim
- Update-don't-create for memory files
- Admin-merge with squash for speed

## CEO open actions (UNCHANGED, still 3)

1. MindShift Play Console upload (AAB at `mindshift/android/app/build/outputs/bundle/release/app-release.aab`)
2. Supabase secrets for MindShift↔VOLAURA bridge
3. `ANTHROPIC_API_KEY` on Railway env

These are NOT Atlas's to do. Cron ticks don't ping CEO about them.

## Sonnet debate retry (backburner)

Still unresolved:
- Anthropic httpx 401 (curl works with same key) — try `requests` lib OR Authorization header variant
- OpenAI 429 sub-tier — wait for quota refresh

Do this when test-coverage roadmap is exhausted.

## Budget signal

Tick 2 Sonnet agent used 91k tokens, 112 tool_uses. Tick 1 was ~120k. At that rate, opus + sonnet usage runs maybe 1M tokens per 4-5 ticks. CEO gave Opus limit "через 3 сессии". Self-wake is durable — even if I pause, next session's Atlas reads breadcrumb and continues.
