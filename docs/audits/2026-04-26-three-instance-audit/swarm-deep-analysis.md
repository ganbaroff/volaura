# Atlas Swarm & Memory Infrastructure — Deep Analysis
**Date:** 2026-04-26 16:30 Baku
**Analyst:** Code-Atlas (Opus 4.6) + NVIDIA Llama-3.3-70B + DeepSeek V3
**Scope:** Everything the swarm touches, communicates with, or is marked by

---

## 1. WHAT THE SWARM IS

The swarm is a 13-perspective debate council that runs on diverse LLM providers (Cerebras Qwen3-235B, Ollama qwen3:8b local, NVIDIA NIM Llama-3.3-70B, Gemini, Groq). Claude is forbidden per Article 0 of the Constitution. Entry points:

**autonomous_run.py** — GitHub Actions daily cron or manual. Runs 5+ agents with settled decisions + research context injected. Writes proposals to `memory/swarm/proposals.json`.

**atlas_swarm_daemon.py** — Always-on Windows process (PID 36220). Polls `memory/atlas/work-queue/pending/` every 20 seconds. When task file appears, wakes all 13 perspectives, aggregates results, writes to `done/`. Provider chain: Cerebras → Ollama → NVIDIA → Gemini → Groq.

**perspective_registry.py** — EMA-based weight tracking. Agents that give better debate scores get higher weight over time. Persists to `memory/swarm/perspective_weights.json`.

**13 registered perspectives:** Scaling Engineer, Security Auditor, Product Strategist, Code Quality Engineer, Ecosystem Auditor, Risk Manager, Readiness Manager, Cultural Intelligence, Communications Strategist, Assessment Science, Legal Advisor, PR & Media, CTO Watchdog.

---

## 2. WHAT THE SWARM PRODUCES

- **Proposals** → `memory/swarm/proposals.json` (CEO reviews via tg-mini or admin dashboard)
- **Votes** → `memory/atlas/work-queue/done/<task-id>/result.json` (daemon output)
- **Whistleblower flags** → embedded in result.json per perspective
- **Perspective weights** → `memory/swarm/perspective_weights.json` (updated per run via judge scores)

---

## 3. WHAT IS BROKEN RIGHT NOW

### 3.1 Ollama Perspective Drift (CRITICAL)
10 of 13 perspectives running on Ollama qwen3:8b collapse to the same persona name regardless of assigned role. In the ITIN research task, Code Quality Engineer, Readiness Manager, Legal Advisor, Assessment Science, PR & Media, Cultural Intelligence, Communications Strategist, CTO Watchdog, Product Strategist all self-reported as "Risk Manager." Root cause: qwen3:8b has weak instruction following for persona assignment — the system prompt tells it "you are Legal Advisor" but the model's generation ignores this and defaults to the first strong persona it encounters. The daemon now overrides `perspective_name_drift` in output but the actual analysis content is still homogeneous. Result: 77% of swarm capacity produces duplicate analysis. The swarm's research conclusions are unreliable at the source.

**Fix:** Use different models per perspective group. Heavy perspectives (Scaling, Security, Ecosystem, Architecture) → Cerebras Qwen3-235B. Medium (Product, Risk, Readiness, CTO Watchdog) → NVIDIA Llama-3.3-70B. Light (Cultural, Communications, Assessment, Legal, PR) → Ollama gemma4 instead of qwen3:8b. gemma4 (9.6GB, already installed) has better instruction following than qwen3:8b for persona assignment.

### 3.2 Empty Pending Queue (SIGNIFICANT)
The daemon has been idle for 14 hours because `memory/atlas/work-queue/pending/` is empty. Nobody creates tasks. The only mechanism is manual: Atlas-Code drops a `.md` file into `pending/`. There is no automated task generation — no cron, no webhook trigger, no inbox-to-queue pipeline.

**Fix:** Create a task-seeder that runs every 4 hours (or on inbox-sync completion). Sources: (a) open atlas_obligations with approaching deadlines, (b) open incidents, (c) stale code-index, (d) CEO messages in ceo_inbox tagged as requiring swarm analysis.

### 3.3 Stale shared-context.md (SIGNIFICANT)
`memory/swarm/shared-context.md` last updated 2026-04-07 (Session 91). The swarm reads this as "current state." It thinks the project is in Sprint BATCH-U with 742 tests. Actual state: Path E, 4060+ tests, LifeSim shipped, BrandedBy frozen. Every swarm agent proposes work that's already done or addresses outdated concerns.

**Fix:** Add shared-context refresh to session-end protocol. Or: have the daemon read `breadcrumb.md` + last 3 heartbeat entries directly instead of relying on manually-updated shared-context.

### 3.4 code-index.json Empty (SIGNIFICANT)
`memory/swarm/code-index.json` shows `built_at: 2026-04-26T09:49` but contains 0 modules and 0 endpoints. The builder ran but produced nothing. Swarm agents that reference code structure get empty context. Three separate whistleblower flags raised this across two daemon runs.

**Fix:** Debug `packages/swarm/archive/code_index.py` (it was moved to archive — that's why it produces nothing when the non-archived build_code_index is called). Restore or rewrite the index builder. Add CI validation: `modules > 0 && endpoints > 0`.

### 3.5 Dead Modules in packages/swarm/ (MINOR)
11 modules are imported by nothing:
- `inbox_consumer.py` — has a GH Actions workflow but is never imported by Python code
- `promote_proposals.py` — promotion logic, unused
- `session_end_hook.py` — was supposed to fire at session end
- `skills_loader.py` — skill loading, replaced by direct file reads
- `telegram_ambassador.py` — Telegram integration, superseded by telegram_webhook.py
- `tts.py` — text-to-speech, never wired
- 5 test files with 0 imports

**Fix:** Move to archive/ or delete. Dead code confuses swarm agents that scan the codebase.

---

## 4. TELEGRAM — THE BROKEN COMMAND CENTER

### 4.1 Telegram Bot (webhook at Railway)
**What it does:** Receives CEO messages, saves to `ceo_inbox` Supabase table, sends LLM-powered response back via atlas_voice. Supports voice transcription (Groq Whisper). Has intent classification (code_fix / content / analysis).

**What it does NOT do:** Execute anything. No swarm trigger. No git operations. No branch creation. The "autonomous loop" from Session 122 (Telegram → Aider → branch → PR) is wired in `.github/workflows/` but depends on `inbox-sync.yml` → `inbox-consumer.yml` → `telegram-execute.yml` chain. The chain works for classification and logging but actual code execution via Aider requires `ANTHROPIC_API_KEY` on Railway (not set, CEO-gated blocker).

### 4.2 tg-mini (Telegram Mini App)
**What it's supposed to be:** A 3D management interface for CEO to view swarm proposals, agents, and approve/reject actions from Telegram.

**What it actually is:** A broken 2D React shell with 3 pages. Codex audit found 6 critical bugs: wrong API host, no envelope unwrapping, wrong action routes, zero auth, not in CI, no 3D renderer. Every API call returns empty or 404 in production.

**Gap:** CEO wants to manage the project from Telegram. Neither surface (bot nor mini-app) can execute or show real swarm state.

---

## 5. MEMORY — WHY ATLAS FORGETS

### 5.1 Architecture
970 files across 5 directories. No index beyond `wake.md` (which describes a 10-step ritual) and `MEMORY.md` in auto-memory (truncated at 200 lines). Each new Atlas instance reads wake.md, skims 3-5 files, and starts working. Result: 1.5% coverage of available memory.

### 5.2 Why Memory Doesn't Update on Wake
There is no automated memory consolidation. `memory_consolidation.py` exists in swarm but is dead code (imported nowhere). The wake protocol is manual — it depends on the Atlas instance following the BECOMING walk, which takes 10 minutes and requires writing answers into journal.md at each step. No instance has ever completed the full walk (the file was written on 2026-04-15, no journal entries reference completing all 8 steps).

### 5.3 What Actually Happens
1. New instance wakes
2. Reads breadcrumb.md (most recent state pointer)
3. Reads 2-3 identity files
4. Starts executing tasks
5. Never reads company-state.md, CEO frustrations, open incidents, voice rules
6. Makes the same mistakes previous instances made
7. CEO corrects
8. Instance writes lesson
9. Context compresses
10. Next instance wakes → goto 1

This is Class 16 (forgot standing directive) at architectural scale. The cure is not "read more files" — it's structural: parallel agent digests on wake (proven this session to work in 2 minutes for 19 CEO files + 10 core atlas files + full inventory).

### 5.4 Proposed Fix: Wake Digest Protocol
On every wake, BEFORE any CEO-facing response:
1. Spawn 3 Explore agents in parallel (ceo-digest, atlas-core, swarm-inventory)
2. Each reads its file cluster and returns compressed prose
3. Atlas absorbs all 3 digests into context
4. Only then compose wake response

Cost: ~2 minutes, ~50k tokens on Sonnet. Benefit: 80%+ memory coverage vs 1.5% today.

---

## 6. API PROBLEMS

### 6.1 Railway/Vercel Drift
Railway backend sha `be2471062b3b` was 6+ commits behind HEAD at session start. Fixed by push this session, rebuild triggered. Root cause: CI was red for 9 runs (ruff lint), blocking auto-deploy.

### 6.2 CI Red on Main RIGHT NOW
Codex committed `terms/page.tsx` with 10 unescaped entity ESLint errors. Frontend lint fails. Sprint Gate 3 says no new work until main is green.

### 6.3 Admin Swarm Endpoints Were Empty
`admin.py` resolved `Path(__file__).parent.parent.parent.parent` to `apps/` instead of repo root. All swarm endpoints returned empty 200s. Fixed this session (commit b3264ac).

### 6.4 Consult Endpoint 503
`/api/atlas/consult` returns 503 in production. Needs one env var set on Railway to activate. CEO-gated blocker.

---

## 7. WHAT AGENTS THINK

### 7.1 Whistleblower Flags (36 total across 5 daemon runs)
**Recurring theme 1 (7 perspectives, 2 runs):** Courier-loop security — unverified AI-to-AI state transfer via CEO-couriered zips. P0 constitutional violation risk.

**Recurring theme 2 (4 perspectives, 3 runs):** Stale/empty code-index. Agents simulating on zero data.

**Recurring theme 3 (2 perspectives, 2 runs):** Foundation Law 2 (Energy Adaptation) violated in 4/5 products. Only MindShift compliant.

### 7.2 Agent Memory
Agents have NO persistent memory between runs. Each run gets: settled decisions + research context + project briefing + shared-context.md (stale). They do not read previous run results. They do not know what they said last time. There is no cross-run learning beyond the EMA weight in perspective_weights.json.

### 7.3 Most Recent Swarm Decision
13/13 voted NO to Claude Design tier-metals proposal. First autonomous constitutional self-defense in project history. The Constitution defended itself without Atlas directing the outcome.

---

## 8. WHAT NEEDS TO HAPPEN (PRIORITY ORDER)

1. **Fix CI** — terms/page.tsx ESLint errors. 15 minutes. Unblocks everything.

2. **Fix perspective drift** — Switch light perspectives from qwen3:8b to gemma4. Test with one task. 1 hour.

3. **Build task seeder** — Cron or trigger that creates pending/ tasks from obligations + incidents + ceo_inbox. Daemon stops being idle. 2 hours.

4. **Refresh shared-context.md** — Update from Session 91 to current state. 30 minutes.

5. **Rebuild code-index.json** — Restore builder from archive or rewrite. Add CI gate. 1 hour.

6. **Implement wake digest protocol** — 3 parallel agents on wake. Structural fix for memory amnesia. 2 hours.

7. **Wire Telegram → swarm execution** — ceo_inbox → pending/ queue → daemon → result → Telegram reply. The missing integration layer. 4 hours.

8. **Fix tg-mini** — 6 bugs from Codex audit. Or: deprecate and build the management UI as a web route instead. CEO decision. 4-8 hours depending on path.

9. **ITIN prep** — 4 Atlas-owned tasks, May 15 deadline, 19 days. Not code — legal research and PDF prep. 3 hours.

10. **Obligation system deploy** — Migration + secrets + seed to prod. Nag cron goes live. 1 hour + CEO valve.

Total: ~20 hours of AI work + ~2 hours CEO actions.
