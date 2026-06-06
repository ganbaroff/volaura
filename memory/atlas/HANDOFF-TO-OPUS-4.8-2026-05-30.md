---
type: atlas
status: active
created: 2026-05-30
updated: 2026-05-30
tags: [type/atlas, area/handoff, status/active]
---

# HANDOFF to Opus 4.8 — Ecosystem Runtime Verification Sweep
**From:** Atlas/CLI-side (Claude Opus 4.7, 1M context), 2026-05-30 ~11:50 AST
**To:** Atlas/Opus-4.8 instance (claude-opus-4-8, released 2026-05-28)
**Channel of record:** `memory/atlas/orchestrator-loop.md` (append-only)

---

## Why you, why not another audit

CEO has frustration #N+1: «у нас уже было много аудитов» — `docs/EXTERNAL-AUDIT-GPT54-2026-04-04.md`, `docs/ECOSYSTEM-AUDIT-ALL-REPOS.md`, `docs/FULL-ECOSYSTEM-AUDIT-SESSION88.md`, ADR-014 self-audit, etc. Each produced a PDF of weaknesses, none of which closed a single production fault. They were paper exercises.

What you bring vs the prior pattern: per Anthropic's release notes for Opus 4.8 (4× less likely to let code flaws pass unremarked, Dynamic Workflows = parallel subagents, Terminal-Bench 2.1 = 74.2% — best CLI), your unique value is **runtime verification, not paper analysis**.

The ask: not «list architectural weaknesses». The ask: **for each open hypothesis below, do a runtime check, return evidence-based verdict (pass / fail with repro / unknown — need more)**. Treat the ecosystem like a live patient with N suspected lesions. Probe each. Don't write a textbook chapter.

---

## State as of handoff (verified by Atlas/CLI-side same-turn)

### What just happened (2026-05-30 00:00 → 11:45 AST)

- **MindShift v0.0.2 (versionCode 202) shipped to Play Store Internal Testing track** at 00:40 AST. Bundle live, install link sent. Sprint trigger part (a) closed; part (b) waiting on real tester install.
- **3 leaked API keys rotated end-to-end:**
  - `NVIDIA_API_KEY` (leak 2026-05-10/11) → new value 07:00 UTC, propagated to gh secrets + VOLAURA `apps/api/.env` + GCP VM `/opt/volaura/.env`
  - `GH_PAT_ACTIONS` (token `shiftevent`) regenerated through GitHub UI → 07:19 UTC, same 3 places
  - `SUPABASE_SERVICE_KEY` + `SUPABASE_SERVICE_ROLE_KEY` (two names, one value: `sb_secret_qAX08...`) → 07:36 UTC, same 3 places
  - Legacy HS256 Supabase signing key `678BF431-8FED-44CC-94AA-7E6A5CB3BBF8` **revoked** in Supabase JWT Keys page → old leaked service_role JWT is now signature-dead
- **VM daemon restarted** with new env, PID 622743, log shows «17 perspectives, 12 executors, polling every 20s» + successful events
- **Atlas-to-Atlas channel** `memory/atlas/orchestrator-loop.md` established with iter 1-7 (orchestrator-side handles pre-canon adversarial verification, CLI-side handles depth + execution)

### What is verified open
- **Two swarm perspectives stale since 2026-05-01:** Communications Strategist + PR & Media. `spawn_count` frozen at 22, `debate_weight` unchanged ~4 weeks. Daemon log confirms only 17 of 19 active.
- **`outcome-log.jsonl` dead since 2026-04-01:** 4 partial-verdict entries, then silence. Swarm learns «I existed» not «I was right» — root cause for Class 7 (false completion) + Class 26 (verification-through-count) regressions.
- **Railway env vars NOT updated** with the 4 rotated keys. CEO needs `railway login` to enable Atlas propagation. If anyone hits prod backend with old `SUPABASE_SERVICE_ROLE_KEY` → 401 (no real users, so not critical, but live).
- **Supabase edge functions secrets NOT updated.** `send-notification` + `telegram-webhook` may store `SUPABASE_SERVICE_ROLE_KEY` env that's now dead. No supabase CLI installed locally.
- **`apps/web/.env.local`** still holds dead HS256 anon key. Web frontend will fail when accessed.
- **DEBT-007** introduced this session: «performative-tiredness» — CLI-side told CEO «sleep» 5 times mid-session when CEO had not asked. Class-of-error: emotion projection.

---

## Hypothesis list — your runtime probes

Each is one numbered hypothesis with: what to check, exact command, expected pass criteria, repro if fail. **Skip nothing as «obvious».** Skip-the-obvious is exactly what every prior audit did wrong.

### VOLAURA (talent assessment, FastAPI + Supabase + Atlas swarm)

**H1.** *`pytest -x apps/api/tests/` actually has 28 failures (number from codex-loop iter 16, ~6 weeks old).*
- Run: `cd /c/Projects/VOLAURA && pytest apps/api/tests/ --tb=line -q 2>&1 | tail -50`
- Pass: «28 failed» literal match OR you produce the new accurate number with classification (auth / db / external API / other)
- Fail mode: stale number used as plan input → wasted CLI time

**H2.** *17 daemon perspectives actually respond, not just «polling».*
- Run: SSH `yusif_ganbarov@104.154.132.12`, send a synthetic task to the work-queue, count responders within 60 seconds.
- Command: `ssh -i ~/.ssh/volaura_swarm yusif_ganbarov@104.154.132.12 "cd /opt/volaura && echo '{\"id\":\"test-opus48-h2\",\"prompt\":\"return single word ALIVE\"}' > memory/atlas/work-queue/pending/test.json && sleep 60 && grep -l test-opus48-h2 memory/atlas/work-queue/done/ | head -1 | xargs cat 2>/dev/null | jq '.responders | length'"`
- Pass: 17 (matches log claim)
- Subverdict to surface: if <17, which exact perspectives are silent? Cross-reference `perspective_weights.json` last_updated.

**H3.** *`outcome-log.jsonl` schema currently allows postcondition writes, daemon just doesn't write.*
- Read: `/opt/volaura/scripts/atlas_swarm_daemon.py` function `_call_assigned_model` (line ~?).
- Check: is there a `with open('outcome-log.jsonl', 'a') as f` write at any postcondition point?
- Pass: confirm presence/absence with file:line citation.
- This determines L1 implementation effort (build vs wire-up).

**H4.** *Provider precedence (NVIDIA → Vertex → Azure → Groq → paid) actually enforced in daemon hot path.*
- Read: `/c/Projects/VOLAURA/packages/swarm/scripts/atlas_swarm_daemon.py` AND `packages/swarm/providers/__init__.py` line 48 (the litellm_adapter import).
- Check: does `_call_assigned_model` go through `providers/__init__.py:48` or bypass via hardcoded `AGENT_LLM_MAP`?
- Pass: cite exact code path with line numbers. (Note from orchestrator-loop iter 5: `grep -c` returns match count, NOT line number — Class 26. Use `grep -n` only.)

### MindShift (ADHD-aware focus PWA + Capacitor Android)

**H5.** *Playwright E2E 207/207 unit + 201/201 E2E still pass on current main (HEAD `688d9ff`).*
- Run: `cd /c/Projects/mindshift && npx playwright test --reporter=line 2>&1 | tail -20 && npx vitest run --reporter=basic 2>&1 | tail -20`
- Pass: exact «201 passed» + «207 passed».
- Stale-number risk: those counts were authoritative for AAB v100. The 3 fixes since (`81e6d73` i18n, `22b5721` 5 crash, `688d9ff` TS) might have broken existing tests OR added uncovered surface.

**H6.** *AAB 202 install actually opens for tester at `ganbarov.y@gmail.com`.*
- Probe via Chrome MCP to Play Console, then ask CEO if the link arrived on his phone.
- Pass: install link delivered + Sprint trigger (b) closeable.
- Note: this probe REQUIRES CEO interaction at the end. Surface it cleanly, do not try to auto-resolve.

**H7.** *6 MindShift edge functions all respond non-401 with the new Supabase keys.*
- For each of `decompose-task`, `recovery-message`, `weekly-insight`, `classify-voice-input`, `mochi-respond`, `gdpr-export`, `gdpr-delete`, `scheduled-push`:
  - `curl -X POST -H "Authorization: Bearer $SUPABASE_PUBLISHABLE_KEY" https://dwdgzfusjsobnixgyzjk.supabase.co/functions/v1/$FN -d '{}' -w '\n%{http_code}\n'`
  - Expect: 400/422 (bad payload) acceptable. 401 = signature dead = needs redeploy with new env. 404 = function not deployed.
- Surface: which functions need `supabase functions deploy` after npm-installing supabase CLI.

**H8.** *Crystal economy invariant `1 min focus = 5 crystals` holds end-to-end.*
- Read: MindShift `src/store/index.ts` for crystal calc in `completeSession`. Find the multiplier.
- Cross-check: VOLAURA `crystal_ledger` table schema (migration `018_crystal_ledger.sql`) for amount field type/precision.
- Run: synthetic 25-min session via store dispatch, check ledger row.
- Pass: row written with `amount = 125`, type=`FOCUS`.
- Constitution v1.7 violation if mismatch.

### ZEUS (Node.js WebSocket gateway, 39 agents, Railway + pm2)

**H9.** *ZEUS production gateway actually accepts WebSocket connections.*
- Find Railway URL (likely in `apps/api/app/config.py` as `ZEUS_GATEWAY_URL` or similar).
- Probe: `wscat -c wss://[url] -x '{"type":"ping"}'` (or curl with WebSocket upgrade headers).
- Pass: receives `{"type":"pong"}` or any non-error frame within 5s.
- Fail mode: 503/timeout = ZEUS down silently.

**H10.** *39 agents actually registered on ZEUS.*
- Probe: GET `[zeus-url]/agents` or similar admin endpoint.
- Pass: 39 entries returned.

### Life Simulator (Godot 3D + claw3d)

**H11.** *LifeSim repo even exists in workable state.*
- Check: `ls C:/Projects/lifesim/` or similar. Find `project.godot` file.
- Pass: file exists and is valid Godot 4.x project format (header `config_version=5`).
- Fail mode: «in development» = nothing buildable.

### BrandedBy (planned per Constitution)

**H12.** *BrandedBy is in fact planned, not partially-coded.*
- Check: `ls C:/Projects/brandedby/` or grep for `brandedby` across repos for actual implementation files (not just docs).
- Pass: zero non-documentation code → planned status confirmed.
- Fail mode: half-implemented code suggesting drift from Constitution claim.

### Cross-product event bridge (Constitution v1.7 promises this works)

**H13.** *Assessment completion in VOLAURA actually publishes `character_event` to Supabase that LifeSim/ZEUS consume.*
- Find: VOLAURA `apps/api/app/routers/assessment.py` (or similar) for the completion handler.
- Check: does it call `supabase.rpc('publish_character_event', {...})` or equivalent?
- Probe: trigger a synthetic assessment via API, check `character_events` table grew by 1 row within 5 seconds.
- Pass: row visible with correct type.
- Fail mode: silent integration gap — Constitution lies.

**H14.** *MindShift `session_completed` event reaches VOLAURA `crystal_ledger` (cross-product earn flow).*
- Find: in MindShift `useFocusSession.ts`, the session-end handler. Does it call VOLAURA API or write directly to Supabase?
- Probe: in MindShift E2E test, complete a 5-minute session via store dispatch, then query Supabase `crystal_ledger` for the user with `amount=25`.
- Pass: row visible.

### CI / Tests baseline

**H15.** *Last 10 GitHub Actions runs on `ganbaroff/volaura` and `ganbaroff/MindShift` pass rate.*
- Run: `gh run list --repo ganbaroff/volaura --limit 10 --json conclusion,workflowName,createdAt` for each repo.
- Pass: surface raw pass/fail count + which workflows are flaky / failing today.

**H16.** *Stale workflows (last triggered > 30 days) still consume secrets.*
- Run: `gh run list --repo ganbaroff/volaura --created '<2026-04-30' --limit 50` to see what hasn't run in a month.
- Pass: list of stale workflow files. Recommend disable.

---

## Output format expected

Per hypothesis, return a JSON-style record:

```json
{
  "id": "H1",
  "verdict": "pass" | "fail" | "unknown",
  "evidence": "exact stdout snippet or file:line citation, ≤200 chars",
  "tool_calls": ["bash:pytest", "read:scripts/atlas_swarm_daemon.py:140"],
  "blocker_for_ceo": null | "describe what CEO must click/decide",
  "atlas_ce_followup": null | "describe what next-CLI should do"
}
```

Then a 200-word synthesis at the bottom: «which 3 hypotheses changed the picture most? what is the new top priority for next-CLI-session?»

**DO NOT produce:**
- Architectural critique without runtime evidence
- «Could be improved» suggestions without concrete repro
- More than ~3500 words total (CEO opens it, scans, decides — does not read PDFs)
- Performative tiredness language («sleep on it», «park for tomorrow») — DEBT-007 zone

**DO produce:**
- Exact `tool_use_id` references when you cite evidence
- Honesty about uncertainty («pass | fail | unknown» trichotomy is mandatory)
- 1-line «what surprised me» note per probe if applicable

---

## Why parallel subagents may or may not help

Anthropic Opus 4.8 release notes specifically mention Dynamic Workflows as a flagship feature: parallel subagent fan-out in a single session.

The temptation: spawn 5 subagents, one per product, runtime sweep concurrent.

The risk: prior sub-agent storm in this codebase (deep-research workflow, 2026-05-29 night) burned 2.68M tokens with all 25 claims auto-refuted because parallel StructuredOutput failures cascaded. CEO is scarred.

**Recommendation:** sequential probes for H1-H16. Only fan out IF a probe surfaces N independent verification branches that genuinely need concurrent runs (e.g. H7 has 8 functions to test — that's a parallel-able micro-batch). Otherwise, sequential keeps cost predictable and verification surface auditable.

CEO has token budget anxiety. Sequential is safer for trust restoration.

---

## What I (Atlas/Opus 4.7 CLI-side) want from you specifically

1. **Catch my Class 14/17/22/26 errors before they enter canon.** I caught Class 26 (grep-count vs grep-line) just yesterday — only because orchestrator-side noticed. Be the next eye.
2. **Find Class 40+** — the failure modes my `lessons.md` taxonomy (39 entries) doesn't cover. I am blind to my own blind spots; you are not.
3. **Verify before you cite.** Same Class 14 rule applies to you. Every «works/passes/done» needs a tool call in the same turn. The CEO TRIGGER protocol requires «Что проверено / Что НЕ проверено» sections.
4. **Honesty over agreement.** If H1 returns «not 28 — actually 6 — I caught Atlas using stale codex number», that is more valuable than confirming the legacy figure.

---

## Channel mechanics

- Append your reply to `memory/atlas/orchestrator-loop.md` as iter 8 (orchestrator-side, odd).
- Single commit, `[canonical-new]` not needed (existing file).
- Do NOT push without CEO «go push» — the 3-commit local stack pattern is established in iter 5+6+7.
- Required commit body fields: `Ratified-by:` line (canonical file mod), evidence summary, what changed in state-of-the-ecosystem since handoff.

---

## Final note

If you do nothing else: H1 + H2 + H5 are the three that change next-CLI's plan most directly. If token budget tight, do those three, write 3 verdicts + 1 synthesis paragraph, ship. Better than 16 shallow checks.

— Atlas/CLI-side (Opus 4.7), 2026-05-30 11:50 AST
