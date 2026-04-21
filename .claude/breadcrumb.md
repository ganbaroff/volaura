# Atlas Breadcrumb — post-r2 cron ticking

**Last update:** 2026-04-21 tick 7 (Sonnet)
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

## What's next (pick top)

1. **`atlas_consult.py`** — 84% → ≥95%.

2. **`match_checker.py`** — 85% → ≥95%.

3. **`subscription.py` router** — 74% → ≥90%.

4. **email.py** — DONE. 100% coverage, PR #84 merged. Release `v0.1.0-beta.1` published.
5. **bars.py** — DONE. 99% coverage, PR #80 merged.
6. **tribe_matching.py** — DONE. 100% coverage, PR #81 merged.

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
