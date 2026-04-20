# Atlas Breadcrumb — Session 122 round 2 CLOSED, post-r2 in flight

**Last update:** 2026-04-21 ~02:50 Baku (cron tick #1 after CEO directive)
**Self-wake cron:** 14d7810d, fires at minute 7 and 37 every hour, durable
**Round 2 status:** ALL 3 TRACKS CLOSED + FINAL-REPORT shipped

## Round 2 closed (this tick)

- PR #74 Track 1 audit: MERGED. 4 REAL / 4 PARTIAL / 1 BROKEN of 10 functions.
- PR #75 Track 2 verdict + canonical example: MERGED earlier. Cerebras won 5/7 dimensions, DeepSeek 1/7 + naming convention. 10 canonical tests pass in 50ms.
- PR #76 Track 3 real AURA scoring tests: MERGED. 32 tests, 91% coverage on aura_reconciler.
- PR #77 FINAL-REPORT.md: MERGED. Opus synthesis of all 3 tracks.

## Test coverage roadmap (next ticks pick top of list)

REAL functions still without test coverage (per Track 1 audit):
1. **Assessment IRT engine** (apps/api/app/services/assessment.py if exists, OR within routers/assessment.py 1589 lines) — highest leverage, scoring math, anti-gaming. Hardest to mock cleanly because of CAT adaptive logic.
2. **Organizations semantic search** (apps/api/app/routers/organizations.py:470) — pgvector + rule-based fallback. Critical for B2B journey. Test the fallback chain explicitly.
3. **Telegram bot _handle_atlas** (apps/api/app/routers/telegram_webhook.py:1818) — fresh code, complex (classifier + memory load + LLM call + GitHub issue creation). Mock LLM via Pydantic structured output.
4. Sign-up via Supabase (auth.py:135) — already has invite-gate G2.3 tests probably; verify with grep before duplicating.

Use apps/api/tests/_canonical_example.py as template + test-standard-verdict.md as standard.

## Per-tick task pattern

Each cron tick (every 30 min):
1. Read this breadcrumb.
2. git fetch + check open PRs.
3. Pick top item from "Test coverage roadmap" above.
4. Spawn Sonnet agent with prompt template:
   "Read mega-sprint-122-r2/test-standard-verdict.md and apps/api/tests/_canonical_example.py.
    Write test_<function_slug>.py for <target file:line> with ≥90% coverage on the target module.
    Use pytest.parametrize, dependency_overrides for Supabase, Pydantic Literal[] for LLM regressions.
    Open PR mega-sprint-r2 [track-3-N]: <function> tests."
5. Wait, merge.
6. Update breadcrumb with what shipped, what's next.
7. NO CEO return — per directive "пока лимит не закончится".

## Sonnet/GPT debate retry (lower priority)

- Anthropic 401 from httpx — try the `requests` library instead, OR explicit `User-Agent: atlas-debate/1.0` header. curl works with same key, so it's a python httpx quirk.
- OpenAI 429 — check `gh secret list` for OPENAI tier; if free, retry hourly.
- When both work, re-run scripts/swarm_test_debate.py and re-synthesize verdict if their input materially differs.

## CEO open actions (UNCHANGED, still 3)

1. MindShift Play Console upload (AAB ready in mindshift/android/app/build/outputs/bundle/release/)
2. Supabase secrets for MindShift↔VOLAURA bridge (VOLAURA_API_URL + EXTERNAL_BRIDGE_SECRET on MindShift, MINDSHIFT_BRIDGE_SECRET on VOLAURA Railway)
3. ANTHROPIC_API_KEY on Railway VOLAURA env (for /api/atlas/consult activation + swarm team_recommendation activation in CI runs)

These are NOT for me to do. Cron ticks do not poke CEO about these — see CEO-ACTIONS.html in mega-sprint-122/.

## Known constraints

- Don't push directly to main; always PR + merge --admin.
- Class 17: Opus does synthesis, Sonnet does hands.
- Class 18: read artifact, don't relay subagent confidence as own.
- Update-don't-create on memory files.
- AC.md merge conflicts come up sometimes; accept origin/main version.
- main branch CI sometimes fails on session-end heartbeat commits — non-blocking, don't chase.

## Self-wake budget tracking

CEO concern: 7-day cron expiry, plus token budget. If subsequent ticks burn through opus tokens fast, consider spawning Sonnet-only orchestrator (still keep synthesis on Opus, but for routine "read breadcrumb, pick task, spawn sub-agent" the orchestrator can be Sonnet). Decision deferred to when budget pressure shows up.
