# Handoff 013 — Swarm & Agent System Upgrade

**From:** Cowork (Claude Opus 4.6, research advisor)
**To:** Atlas (local Claude Code, CTO)
**Date:** 2026-04-13 Baku
**Priority:** P1 (parallel to Handoff 012 reality probe, but do NOT start until 012 is complete)
**Owner:** Atlas fully. Cowork provides architecture reviews + prompt engineering on request.

---

## Why this handoff exists

CEO directive 2026-04-13: "надо улучшить агентов и их систему взаимодействия и работу в проекте." Cowork is being redirected to ecosystem design; swarm is Atlas territory going forward.

**Current state (verified today):**
- `packages/swarm/` has 34 Python files — engine, coordinator, orchestrator, inbox_protocol, perspective_registry (EMA weights), backlog, memory_consolidation, reflexion, research injection, 48 skill files.
- `tools/` has real capabilities: `code_tools`, `constitution_checker`, `deploy_tools`, `llm_router`, `web_search`.
- GH Action runs swarm-daily at 05:00 UTC (`.github/workflows/swarm-daily.yml`).
- `autonomous_run.py` injects 10 SETTLED_DECISIONS + ECOSYSTEM-MAP + Global_Context into every prompt.

**Diagnosed gaps (from STATE.md + today's re-audit):**
1. **Swarm is DETECTION ONLY, NOT COORDINATION.** `backlog.py` exists and stores tasks with dependencies/blockers/ACs, but is disconnected from agent runtime. Agents emit proposals → humans read. No task ever flows *back* into an agent.
2. **Zero Langfuse instrumentation on swarm providers.** `flush_langfuse()` defined in `main.py` but never called in lifespan shutdown. Means we can't see cost/latency/quality per agent debate — blind flying.
3. **LLM provider hierarchy (Constitution Research #12) not enforced at agent level.** Rule: Cerebras Qwen3-235B → Ollama → NVIDIA NIM → Anthropic (last resort only). Today some code paths still default to Anthropic because Ollama path in Python swarm is new (added 2026-04-06) and untested in prod runs.
4. **Constitution checker produces 15 flags, ~3 real.** No real-vs-noise triage layer. Teaching comments (`// Remove red`, `# no red`) and boundary values (`duration=800`) trigger false positives that drown the 3 live leaderboard leftovers in `dashboard/page.tsx:17,163,338`.
5. **Cross-model judge pattern exists but is under-used.** `PerspectiveRegistry` updates EMA weights from `judge_score/5.0`, but only autonomous_run.py uses it. Coordinator DAG runs don't feed into the same learning loop.
6. **No swarm-to-backlog bridge.** Coordinator returns `CoordinatorResult.priority_action` but nobody writes it to `backlog.json` as a real task with AC + assignee.
7. **Test harness is sparse.** `tests/` exists, but no end-to-end "agent debate produces valid proposal → judge scores → backlog task created → status transitions" test. Means refactors are risky.
8. **ECOSYSTEM events and agents are parallel tracks.** Assessment completion fires `character_events` via `emit_assessment_completed`, but swarm doesn't subscribe to this event stream. Cross-product agent reactions are impossible.

---

## What Atlas must deliver

**Process protocol — mandatory.** For every task below:

```
1. RESEARCH    — read referenced code + at least 1 external source (WebSearch or NotebookLM)
2. PLAN        — write acceptance criteria BEFORE coding. Gherkin Given/When/Then.
3. CRITIQUE    — swarm itself reviews the plan. Min 2 external models (Cerebras + Gemini or Groq + NVIDIA). Log to Langfuse.
4. REWRITE     — incorporate critique. If models unanimous → force dissent with a third.
5. IMPLEMENT   — code + tests. Constitution scan PASS before commit.
6. VERIFY      — run tests, run constitution_checker, run a real agent debate end-to-end.
7. LESSON      — write to packages/swarm/memory/lessons.md (what went wrong) + patterns.md (what worked).
8. DOCUMENT    — SHIPPED.md, sprint-state.md, update STATE.md "Now" section.
```

No self-confirmation. External research must validate each architecture decision.

---

## Tasks (priority order)

### Task 1 — Close the detection→coordination gap (P1, 2–3 days)

**Problem:** Proposals never become tasks. Agents think but don't cooperate.

**Do:**
- Modify `packages/swarm/coordinator.py` so `CoordinatorResult.priority_action` is persisted to `backlog.json` via `Backlog.add_task(...)` with:
  - `assignee` = squad name (from `squad_leaders.py`)
  - `acceptance_criteria` = list derived from each agent's `FindingContract.recommendation`
  - `source` = `"coordinator_run:{task_id}"`
  - `depends_on` = any prior backlog task IDs referenced in findings
- Add `/swarm/backlog/next` endpoint in `apps/api/` that returns next `TODO` task to an agent, agent picks it up, updates to `IN_PROGRESS`, returns result → status `DONE` or `BLOCKED`.
- Add `packages/swarm/worker.py` — a daemon that polls backlog for TODOs assigned to its squad, fetches via the endpoint, runs the relevant agent, posts result back.

**AC-1:** Given coordinator runs "audit assessment security", when debate completes, then `backlog.json` contains ≥1 task with status TODO, real AC list, and squad assignee.
**AC-2:** Given a worker is running locally, when a TODO task matches its squad, then within 60s the task transitions TODO → IN_PROGRESS → DONE (or BLOCKED with reason).
**AC-3:** Given a DONE task has findings, when next coordinator run happens, then new proposals reference the finding in their context.

---

### Task 2 — Enforce LLM provider hierarchy + Langfuse tracing (P1, 1 day)

**Problem:** We cannot prove agents are not silently calling Anthropic in a hot loop. Cost + Constitution compliance risk.

**Do:**
- Audit `packages/swarm/providers/` — every file. For each `generate()` / `call()` function, verify fallback order matches Constitution: Cerebras → Ollama (`http://localhost:11434`, model `qwen3:8b`) → NVIDIA NIM → Anthropic.
- Emit warning (not error) to Langfuse whenever Anthropic is hit. CEO reviews Anthropic usage weekly.
- Wrap every provider call in a Langfuse `@observe()` decorator. Tag with `provider`, `model`, `agent_name`, `task_id`, `tokens_in`, `tokens_out`, `cost_usd`.
- Add `flush_langfuse()` call to `apps/api/main.py` lifespan shutdown.
- Add Cerebras-first smoke test in CI: `python -m packages.swarm.providers.smoke_test` must pass without hitting Anthropic.

**AC-4:** Given a full `autonomous_run.py --mode=daily-ideation` executes, when Langfuse is queried for the last 24h, then ≥95% of calls are Cerebras+Ollama+NVIDIA, ≤5% Anthropic.
**AC-5:** Given Anthropic quota is exhausted (simulated), when agents run, then debate still completes via Cerebras/Ollama without exception.

---

### Task 3 — Real-vs-noise triage in constitution_checker (P2, 4–6 hours)

**Problem:** 15 flags, ~3 real. Cowork re-audit confirmed most are teaching comments or boundary values. Blocks honest Constitution compliance reporting.

**Do:**
- Add triage layer in `packages/swarm/tools/constitution_checker.py`:
  - Skip lines with comment markers that include `no red`, `remove red`, `NEVER RED` (those are the teaching pins, not violations).
  - Treat `duration=800` as boundary, not violation (Law 4 says "max 800ms non-decorative" — equals, not exceeds).
  - Output report in two buckets: `live_violations` (must fix) and `teaching_or_boundary` (informational only).
- Add CLI flag `--only-live` that returns only the live bucket.
- Wire into CI: swarm-daily fails build only on `live_violations > 0`.

**AC-6:** Given current codebase, when `constitution_checker.run_full_audit(only_live=True)` runs, then it returns exactly 3 leaderboard leftovers in `apps/web/app/[locale]/(app)/dashboard/page.tsx` at lines 17, 163, 338, and zero others.
**AC-7:** Given teaching comments are removed (after fixing the real 3), when audit runs again, then `live_violations == 0` and `teaching_or_boundary` count is preserved.

---

### Task 4 — Coordinator → backlog → cross-product event bridge (P2, 1–2 days)

**Problem:** Ecosystem events (`emit_assessment_completed`, `emit_aura_updated`, `emit_badge_tier_changed`) fire into `character_events`, but no agent reacts. Cross-product automation = zero.

**Do:**
- Add `packages/swarm/event_listener.py` — subscribes to `character_events` via Supabase Realtime.
- For each event type, map to a coordinator task:
  - `assessment_completed` → spawn "quality-review" squad: Did AURA score land in plausible range? Were any anti-gaming signals triggered?
  - `aura_updated` → "growth-suggestion" squad: What next competency should this user attempt?
  - `badge_tier_changed` → "celebration-copy" squad: Write ADHD-safe celebration copy (no streaks, no "don't lose", identity framing).
- Each squad runs → posts findings → coordinator writes backlog task → worker executes → result either emits follow-up event or writes to user-facing recommendation table.

**AC-8:** Given a new `assessment_completed` event fires in prod, when `event_listener.py` is running, then within 30s a backlog task appears with source=`event:assessment_completed:{session_id}`.
**AC-9:** Given the "growth-suggestion" squad runs for 10 assessments, when the coordinator synthesizes, then each user has a concrete next-competency recommendation stored in `user_recommendations` table (create migration if table absent — see database.md rules).

---

### Task 5 — Swarm end-to-end test harness (P2, 1 day)

**Problem:** Refactoring swarm breaks silently. No regression coverage for "debate → judge → weight update → backlog write → worker execution".

**Do:**
- Add `packages/swarm/tests/test_e2e_debate.py`:
  - Fixture: mock provider that returns deterministic JSON.
  - Run full `coordinator.run("audit onboarding UX")`.
  - Assert: ≥1 backlog task created, each FindingContract has category + severity + recommendation, PerspectiveRegistry weight changed for at least 1 agent.
- Add `packages/swarm/tests/test_provider_fallback.py`:
  - Simulate Cerebras 429 → Ollama 200 → assert Ollama used.
  - Simulate Cerebras+Ollama both down → NVIDIA 200 → assert NVIDIA used.
  - Simulate all three down → Anthropic 200 → assert Anthropic used AND Langfuse warning emitted.
- Wire into `pytest -q packages/swarm/tests/`. Must run under 60s total.

**AC-10:** Given `pytest packages/swarm/tests/` runs on CI, when all tests pass, then branch is mergeable. On failure, merge is blocked.

---

### Task 6 — Retire archive, consolidate agents (P3, 4–6 hours)

**Problem:** `packages/swarm/archive/` still exists. Dead code confuses new contributors and bloats code index.

**Do:**
- Read everything in `packages/swarm/archive/`. For each file: either delete (if obsolete) or move forward (if still referenced).
- Update `prompt_modules/` — there's overlap with `prompts.py`. Consolidate to one of them.
- Document the final swarm file map in `packages/swarm/README.md` with one-line description per file.

**AC-11:** Given a new contributor opens `packages/swarm/README.md`, when they read it, then they understand entry point (coordinator), task store (backlog), weight learning (perspective_registry), tools, and how to run a debate locally within 3 minutes.

---

## Do NOT do in this handoff

- Do NOT add new agent perspectives. 8 in autonomous_run + 39 in ZEUS Gateway is enough; balance weights first.
- Do NOT build a new UI for swarm. CLI + backlog.json is fine until product decision made.
- Do NOT use Claude haiku/sonnet as swarm agents. Constitution rule. If you find any, remove them.
- Do NOT commit ecosystem_events wiring in `assessment.py` until Atlas verifies Handoff 012 data. That commit is Cowork's, pending reality probe.

---

## Deliverables

1. Code changes committed across `packages/swarm/`, `apps/api/`, `.github/workflows/`.
2. `packages/swarm/README.md` updated with final file map + how-to-run-locally.
3. `packages/swarm/memory/lessons.md` and `patterns.md` entries per task.
4. Langfuse dashboard URL for swarm agent traces (post in `sync/claudecode-state.md`).
5. Backlog.json with ≥3 real tasks created by coordinator (not hand-written).
6. `packages/atlas-memory/SHIPPED.md` updated with this handoff's deliverables.
7. `packages/atlas-memory/sync/claudecode-state.md` — section `## Handoff 013 Results`, list each AC with PASS/FAIL + evidence.

---

## Acceptance (gate to close handoff)

All ACs 1–11 are PASS. Constitution checker `--only-live` returns 0. Pytest green. Langfuse shows real traces. Atlas writes a 5-line post-mortem to `sync/claudecode-state.md` with the biggest surprise found during implementation.

---

## Timeline

- Handoff 012 (reality probe) finishes first — Cowork waits for those results before revising the VOLAURA roadmap.
- Handoff 013 can start immediately after 012 closes. 7–10 working days for Atlas to complete all six tasks.
- Cowork is available async for plan reviews (ping via `packages/atlas-memory/sync/cowork-state.md` → "Review request: Task N plan").

---

## Rule of honesty

If any task reveals a Constitution contradiction Cowork missed, Atlas writes it into `knowledge/constitution-corrections-2026-04-XX.md` and notifies CEO via sync. Cowork's research is a best-effort starting point, not gospel.
