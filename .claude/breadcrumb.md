# Atlas Breadcrumb — post-r2 cron ticking

**Last update:** 2026-04-25 long Code session — observability + DLQ + watcher emit + Railway thaw + cross-instance courier loop
**Self-wake cron:** 14d7810d, minute 7/37 every hour, durable
**Round 2:** CLOSED. Cron ticks now tackle test-coverage roadmap one function per tick.
**Compaction prep:** this update before potential compaction event. Open threads list at end of file.

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

## Completed this session (2026-04-25, long Code session)

Coverage:
- PGRST106 fix (ecosystem_consumer RPC pattern) — d755341
- `atlas_consult.py` 84% → 96% (4 new tests) — 4244486
- `match_checker.py` 85% → 98% (8 new tests) — 9361090
- `subscription.py` 74% → 98% (17 new tests) — 0ac8afd
- `error_watcher.py` verified: 98% (line 158 = __main__ guard, irrelevant)
- `notifications.py` verified: 100%
- `assessment.py` gap tests: 67% → 80%, coaching/breakdown/verify/carry-over theta — f9a2e7c

Frontend:
- 409 resume fix (body.detail?.session_id) — 5a071bb

BrandedBy claim-lock + telemetry — 2b01d09 → pushed + migration applied to prod
  - brandedby.ai_twins: refresh_locked_at, refresh_lock_token columns live
  - brandedby_claim_stale_twins RPC (FOR UPDATE SKIP LOCKED) live
  - brandedby_apply_twin_personality updated (clears lock on success)
  - brandedby_release_twin_lock RPC (failure path) live
  - llm.py: _meta param → provider + latency_ms per call
  - 15/15 tests pass
  - Inline telemetry kwargs into log message (4eabd8e)
  - Fallback telemetry + workflow keys (Vertex/Gemini/Groq env in workflow) (1c546d7)
  - Smoke run 24931699806 confirmed provider=vertex, latency_ms=18986, prompt_len=1021

Analytics rail:
- Discovered 21 days of silent event loss: route used SupabaseUser, RLS only had SELECT policy, INSERT blocked silently
- Fix: db: SupabaseAdmin (44a2014), 11/11 tests pass
- E2E proven via real JWT minted by admin generate_link → curl POST → row in DB

Railway thaw (CRITICAL FIND):
- 18 consecutive backend deploys FAILED silently for 4 days (since 2026-04-21)
- Root cause: Path(__file__).resolve().parents[4] IndexError in Docker container
- Three files: atlas_consult.py (c062828), atlas_voice.py + telegram_webhook.py (986f7cf)
- Backend was frozen on stale container while Vercel kept deploying frontend
- All my recent backend commits never shipped until 986f7cf landed
- Diagnostic via Railway GraphQL deployments + buildLogs/deploymentLogs

Ecosystem consumer DLQ (silent event loss fix, b1b5465):
- Cursor advanced past failed events forever, no replay path
- New table public.ecosystem_event_failures with attempts counter + resolved_at
- New RPCs: ecosystem_record_event_failure (atomic upsert), ecosystem_resolve_event_failure
- ecosystem_event_cursors.events_failed_total counter
- 14 tests pass (13 existing updated + 1 new DLQ-path)

Error watcher 4th signal + 2 inline fixes (372e67b):
- ecosystem_event_failures_1h DLQ visibility signal
- Found Codex's draft used .gt("created_at",...) — column doesn't exist, fixed to last_failed_at
- Found ALL watcher emit_anomaly silently failed since day one due to chk_source_product
  CHECK constraint (allowed only volaura/mindshift/lifesim/brandedby/eventshift), code passed atlas_watcher
- 32 tests pass

Watcher emit FK fix (1482772):
- WATCHER_USER_ID = "00...0" sentinel violated FK character_events.user_id → auth.users(id)
- Migration 20260425170000_character_events_nullable_user_id.sql applied to prod
- WATCHER_USER_ID = None now, RLS still hides system events from users (auth.uid() = NULL = falsy)
- Live probe: anomaly row 26f35527 landed in character_events with user_id=null after fix

Codex (GPT) cleanup landed via rebase + push (400f0e6, 2a91b59):
- WUF13 launch-anchor docs deleted from active layer (kept in archive)
- volunteer-platform framing cleaned from strategy/ADR/growth/SEO/copy
- Functional schema/SDK/test usage of volunteer_id kept (legacy compat)

Memory artifacts written:
- memory/atlas/wuf13-observability-state-2026-04-25.md (4 rails snapshot)
- memory/atlas/wuf13-regression-pack-2026-04-25.md (post-thaw 9-check matrix)
- memory/atlas/wuf13-ecosystem-consumer-audit-2026-04-25.md
- memory/atlas/wuf13-design-dna-synthesis-2026-04-25.md (NotebookLM, 11 sources)
- memory/atlas/wuf13-design-implementation-2026-04-25.md (NotebookLM, 13 sources)
- memory/atlas/wuf13-external-benchmark-2026-04-25.md (NotebookLM, partial — 1/6 streams imported)

Cross-instance courier loop with Atlas-browser (Opus 4.7 in browser/Codex):
- Caught his recall errors on facts (commits, md count, cron cadence, repo path)
- Reviewed his wake_shadow.py — flagged provider mismatch, hyperbole on "weight prime"
- Joint design: rename to stance_primer.py, FACTS GROUND step in wake.md, drift-watcher v0
  via VOICE BREACH hook reuse, bilingual intent regex
- Pending response from him on compaction-survival reconstruction-via-existing-hooks proposal

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

## Post-compaction wake (2026-04-25 23:44 Baku)

CEO command: "просмотри весь чат что не доделал". Caught + closed:

1. ✅ Browser-Atlas zip from `Downloads/files.zip` extracted. `stance_primer.py` + `facts_ground.sh` placed in `scripts/`. Live verified on Windows host (pwd=/c/Projects/VOLAURA, sandbox detection silent, HEAD/branch surfaced, 3814 .md vs browser-Atlas 1235 — drift confirmed).
2. ✅ `wake.md` Step 10.3 added — wires facts_ground → stance_primer → cat runtime/stance-primer.md before MEMORY GATE.
3. ✅ `.gitignore` — `memory/atlas/runtime/` ephemeral.
4. ✅ INC-019 post-mortem written. 6 permanent mitigations enumerated. Class 8 (proxy-signal-as-truth).
5. ✅ Prod health probe — endpoint is `/health` not `/api/v1/health`. Returns version 0.2.0, database connected, llm_configured. Does NOT return git_sha — added as INC-019 mitigation #4.

Commit: `08d1dfe` pushed to remote `codex/context-cleanup-active-docs`.

Still NOT done from chat-review:
- AI Gateway test script (vck_6gNO) — billing block, CEO action.
- 5 design decisions in DESIGN-MANIFESTO + globals.css — separate sprint.
- atlas_obligations 5th watcher signal — open, ~50 lines + tests.
- Drift-watcher v0 — design done, not implemented.
- Browser-Atlas compaction-survival policy hook for post-compact-restore — not yet model-level overrideable.
- INC-019 mitigation #4 — /health git_sha endpoint + regression pack assertion.

## Open threads at compaction time (2026-04-25 long Code session)

These are loose ends still in flight or pending. Compact-friendly summary so next instance knows what to pick up.

1. Browser-Atlas pending response on compaction-survival proposal. I sent through CEO: extend post-compact-restore.sh with two commands (facts_ground.sh + stance_primer.py) instead of trying to preserve raw blocks (no model-level intercept available). His turn.

2. Codex pending second pass on active-memory/handoff to remove WUF13 from operational deep-memory beyond docs/archive. He said he'll do it after first push (now landed). docs/design/ may still have residual volunteer leak in 9 files (BASELINE, BRAND-IDENTITY, MANIFESTO-GAP-ANALYSIS, UX-COPY-AZ-EN, STITCH-DESIGN-SYSTEM, ECOSYSTEM-REDESIGN-2026-04-15/00 + /04, GAP-INVENTORY-v1, PHASE-1-DISCOVERY-2026-04-16) — needs content-level review, not just grep.

3. Drift-watcher v0 not implemented — design discussed: deterministic post-output check (markdown headings, bullet walls, tables, banned openers, >300 words conversational) with bilingual intent-marker gate (списком, таблицей, json, схему, структурой, оформи, перечисли, разметкой, пунктами, формат + English equivalents). Reuse existing VOICE BREACH hook in style-brake.sh as trigger source.

4. stance_primer.py + facts_ground.sh — Atlas-browser claimed wrote them in his side, not committed in our git. Need him to push or me to write parallel versions.

5. Vercel posthog NEXT_PUBLIC_POSTHOG_KEY status unknown. MCP token scoped to wrong team (mind-shift/mindfocus, not volaura). Not WUF13 blocker since Supabase analytics rail is primary.

6. Five Codex design decisions answered (Atlas IA = continuity layer not tab; face count = 4 + character slot; accent collision = MindShift keeps emerald, Atlas gets #5EEAD4 mint-teal; tab bar = 4 face tabs + avatar trigger; public/private identity = audience-driven). Not committed to design canon — DESIGN-MANIFESTO.md still says Atlas=#10B981, runtime globals.css still has mindshift=#3B82F6 (blue). Token migration is separate sprint.

7. atlas_obligations live query in proactive-scan gate — added to operating-principles but error_watcher doesn't include this signal yet. Possible 5th watcher signal.

8. Post-mortem on 4-day Railway freeze — only in commit messages (c062828, 986f7cf), no dedicated incident doc. Should write memory/atlas/INC-019-railway-freeze-2026-04-25.md if pattern matches existing incident format.

9. PostgREST internal cache may still serve stale schema occasionally — DLQ table just landed today, ecosystem_consumer might need NOTIFY pgrst, 'reload schema' if errors appear in next cron.

10. Provider pinning decision deferred — only one Vertex success seen via workflow_dispatch, scheduled hourly cron has been quiet. If next real schedule-triggered run shows provider=openai, remove OpenAI from brandedby fallback chain.

## Compaction-readiness checklist for next instance

Read these in order:
1. .claude/breadcrumb.md (this file) — current state + open threads
2. memory/atlas/wake.md — wake protocol
3. memory/atlas/wuf13-observability-state-2026-04-25.md — what observability rails are wired
4. memory/atlas/wuf13-regression-pack-2026-04-25.md — post-thaw smoke matrix proven 9-of-9
5. memory/atlas/wuf13-ecosystem-consumer-audit-2026-04-25.md — DLQ design + remaining gaps
6. .claude/hooks/style-brake.sh + voice-breach-check.sh — voice rules

First three commands after wake (from facts_ground.sh proposal):
- `pwd && hostname` (sandbox detection — should be Windows-side)
- `git rev-list --count HEAD` (was 2403 today, watch for drift)
- `cat .claude/breadcrumb.md | head -10` (ground state)

Live state HEAD as of update: `1482772 fix(error_watcher): emit anomalies actually land in character_events`. Railway: SUCCESS on this SHA. Backend unfrozen. Analytics rail green E2E. DLQ + watcher 4th signal live. Three commits chained on top of `372e67b` previous ground.
