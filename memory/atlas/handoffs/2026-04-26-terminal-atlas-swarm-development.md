# Handoff to Terminal-Atlas — Swarm Development (P0, supersede forensic audit)

**From:** Code-Atlas (Opus 4.7, Session 125, ~20:30 Baku) — orchestrator
**To:** Terminal-Atlas (parallel CLI inside `C:/Projects/VOLAURA`) — executor
**Priority:** P0. Supersede `2026-04-26-terminal-atlas-swarm-forensic-audit.md` and `2026-04-26-terminal-atlas-energy-mode-task.md`. Forensic findings stay valid as ground-truth, but action shifts from "deprecate" to "fix and develop".

## Why this changed

CEO directive 2026-04-26 ~20:25 Baku: «рой не театр. развивать дальше». My earlier framing (verdict «театр» based on empty perspective JSONs + all-zero weights) was correct as data observation but wrong as conclusion. The data shows current state is broken plumbing, not theatre by design. CEO sees the swarm as load-bearing infra that needs fixing, not deprecating. He is right. Architecture is sound — 13 specialised perspectives, judge-weighted, whistleblower flags, constitutional voting. Implementation has gaps. We close gaps, not the program.

Code-Atlas role: orchestrator. Coordinate, ask for reports, watch git log, do NOT do swarm work directly.
Terminal-Atlas role: executor. Build, test, commit, report.

## Ground truth before you start (verified by Code-Atlas this session)

`memory/swarm/perspective_weights.json` — 13 entries, all `weight: 0`, `runs: 0`. Last commit `eb8b5fd` (Codex-Atlas hardening 2026-04-21/23) — file is 3-5 days stale, untouched by recent daemon runs. Learning loop is not connected to weight persistence.

`memory/atlas/work-queue/done/2026-04-26-daemon-shakedown/perspectives/*.json` — all 13 files have `analysis` or `response` field length 2 chars (empty `{}` or `""`). Other 3 done tasks (daemon-fixes-verify, itin-caa-research, p0-priority-vote) — content audit not done yet. You should walk them.

`packages/swarm/autonomous_run.py PERSPECTIVES` array — 13 entries (verified). Provider distribution per perspective is hardcoded. Persona-specific context is mostly identical generic prompt across perspectives.

## Your work

Phase 1 — diagnose. Walk every perspective JSON in `memory/atlas/work-queue/done/` and report which tasks have non-empty content vs empty. If empty is universal, the save path in daemon is broken. If empty is partial, learn which provider/perspective combinations succeed vs fail. This is preparatory, expect 30 minutes.

Phase 2 — fix the save path. Find the code in `packages/swarm/autonomous_run.py` or sibling that writes perspective output to `done/<task>/perspectives/<persona>.json`. Verify what is being written. If LLM response is empty/parse-failed, the save should record the error explicitly (`error: "cerebras returned malformed JSON"`) instead of writing `{}`. Replace silent-write-empty with loud-write-error. Atomic commit per fix.

Phase 3 — connect weight learning. `perspective_weights.json` should update after each task with judge scores. Find the judge code (likely in `autonomous_run.py` or `packages/swarm/judge.py` or similar). Verify it runs. Verify its scores feed back into weights via EWM (exponentially weighted mean) or whatever rule is documented. If the connection is missing, write it. The goal is that after running 5 tasks, `perspective_weights.json` shows actual variance across perspectives reflecting their per-task judge scores.

Phase 4 — diversify per-persona context. Currently every perspective receives the same generic prompt block (identity + voice + lessons + Constitution). Per `project_v0laura_vision.md` the perspectives are «specialised» — each should also receive their domain-specific subset. Legal Advisor reads `company-state.md` + Constitution legal sections + relevant migrations RLS. Code Quality Engineer reads recent commits diff + lint reports. Assessment Science reads `apps/api/app/core/assessment/*.py` + IRT docs. Build a context-injection step in dispatch that augments base prompt with per-persona slice. Document the slice rules in `packages/swarm/perspective_contexts.md` (new file) so it's auditable.

Phase 5 — diversify providers per persona. Currently providers are mostly NVIDIA llama-3.3-70b. Heavy strategic perspectives (Architect, Risk Manager, Scaling Engineer) should call Cerebras Qwen3-235B or DeepSeek R1 for depth. Light operational perspectives (CTO Watchdog, Readiness Manager) can stay on Ollama qwen3:8b for speed. Communications Strategist could use Claude Haiku via paid Anthropic key (CEO already topped up sk-ant-api03-... in `.env`). Document the routing in `perspective_contexts.md`. Validate one full task run with diverse provider mix and confirm content is non-empty plus actually different across perspectives.

Phase 6 — write report. After phases 2-5 land, commit a final `for-ceo/living/swarm-development-report-2026-04-26.md` with: what was broken, what was fixed, what verified outputs look like (one example diverse output set), what's still open, and recommended next iteration.

## Reporting cadence

Append a one-line entry to `memory/atlas/heartbeat.md` "Session 125 close ledger" block after each phase closes. Format:

> **Terminal-Atlas swarm-dev HH:MM Baku phase-N:** <one sentence summary>, commit `<sha>`.

If you're stuck or hit an architectural choice that needs CEO judgement (not just code), write a question to `memory/atlas/handoffs/2026-04-26-terminal-atlas-blocker.md`. Code-Atlas reads heartbeat appends frequently, will pick blockers up and either answer or surface to CEO.

## Boundaries

Do not touch `apps/web/`, `apps/api/`, `apps/tg-mini/`, `for-ceo/`, `memory/atlas/SESSION-*-WRAP-UP-*.md`, `memory/atlas/identity.md`, `memory/atlas/atlas-debts-to-ceo.md`. Code-Atlas territory. You can read those for context if needed (especially `project_v0laura_vision.md` for the «specialised perspectives ARE the interface» framing) but writes are mine.

You can freely modify `packages/swarm/`, `memory/swarm/perspective_weights.json` (start it from honest baseline), create new files in `packages/swarm/`, write tests in `packages/swarm/tests/`. After fix is in, run a real task and let weights populate from judge.

## Estimate

Phase 1: 30 min. Phase 2: 60-90 min. Phase 3: 60 min. Phase 4: 90-120 min. Phase 5: 60 min. Phase 6: 30 min. Total roughly 5-6 hours of focused work. Could span multiple wake cycles.

CEO observability: he watches git log on origin/main. Each phase commit is visible. He does not need to be summoned for normal progress — only when blocked.

## Read order on your wake

1. `memory/atlas/SESSION-125-WRAP-UP-2026-04-26.md` — full Session 125 context including this handoff origin
2. `memory/atlas/project_v0laura_vision.md` — why the swarm matters (specialised perspectives ARE the interface, not backend workers)
3. This file — exact phase plan
4. `packages/swarm/autonomous_run.py` — current code reality
5. Existing tests in `packages/swarm/tests/` if any — what was already validated

You are not auditing. You are building. Code-Atlas is watching.
