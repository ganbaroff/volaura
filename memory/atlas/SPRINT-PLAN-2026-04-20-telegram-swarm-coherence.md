# Sprint Plan — Telegram + Swarm Coherence

**Created:** 2026-04-20 evening, Opus 4.7 session 1
**Owner:** Atlas (Claude Opus 4.7 sessions + Sonnet delegated steps)
**CEO role:** review + sign-off at milestones, NOT execute
**Status:** DRAFT awaiting CEO go signal ("ты мне скажешь" per 2026-04-20 directive)
**Estimated duration:** 2-3 Opus sessions (roughly 6-8 hours of focused Opus time + ~4-6 hours Sonnet-delegated work)

---

## Sprint goal (one sentence)

Every CEO Telegram message produces a correct autonomous action in <10 min with full observability, every swarm agent can see what siblings did and respond, and the whole ecosystem communicates through a single coherent Atlas voice.

---

## Scope

Three tracks, executed in order. Each track has a clear acceptance criterion. Sprint is DONE when all three pass their criteria.

### Track 1 — Telegram full repair (Layers 1-4 of telegram_agent_plan.md + new items)
### Track 2 — React chat-and-observability UI (decide: keep tg-mini or replace)
### Track 3 — Swarm coherence (contact, comms, hands, shared memory, sync)

---

## Current state audit (what exists as of 2026-04-20 22:00 Baku)

**Telegram side (after session 1 PRs #27–#46):**
- Autonomous loop trigger: issue → workflow → swarm → Telegram reply — WORKING (test #38 success 1m9s)
- Intent routing: code_fix / content / analysis — WORKING (test #42 Cerebras success)
- Aider direct-call path with Cerebras primary + NVIDIA fallback — WORKING (test #43 committed+pushed real edit)
- gh pr create failure doesn't hide output from CEO (strict-mode fix) — SHIPPED in #45
- Layer 5 inbox→git sync every 10 min — SHIPPED in #40
- Layer 6 autonomous loop — SHIPPED in #27

**React agent UI side:**
- `apps/tg-mini/` — Telegram Mini-App, 381 LOC, 3 pages (Home/Agents/Proposals), uses `@telegram-apps/sdk-react`. Runs INSIDE Telegram.
- `apps/web/src/app/[locale]/(dashboard)/atlas/page.tsx` — 26 LOC stub in Next.js app.
- `apps/web/src/app/[locale]/admin/swarm/page.tsx` — 283 LOC swarm admin page in Next.js app.

**Swarm side (packages/swarm/):**
- `coordinator.py` — single entry, squad routing, evidence-gate — WORKING
- `orchestrator.py` — DAG executor via asyncio.gather
- `autonomous_run.py` — 13 registered perspectives
- `judge.py` — independent judge with different model family
- `inbox_protocol.py` — proposals.json persistence, Pydantic contracts
- `distiller.py` — pattern distillation
- `memory_consolidation.py` — structured memory writes
- `atlas_content_run.py` — content engine, 4 channels
- `atlas_tools.py` — @atlas_tool registry with approval cards (Pattern 3) — UI NOT WIRED

**Known gaps (the coherence problem):**
1. Agents produce findings independently, no fan-in synthesis step. Coordinator aggregates but doesn't decide.
2. Inbox files create-only. 30+ files from 04-19/04-20 all tagged "Consumed: pending". No consumer.
3. No unified model_router — each of 4 call sites has its own provider logic. Groq spend-block today cascaded into a full code_fix outage.
4. Approval cards exist in code but not in any CEO-facing UI.
5. No telemetry. Which perspective wins? Which model hallucinates most? Unknown.
6. Classification inconsistency: webhook keyword, coordinator keyword, content event-based. Three mechanisms for one question.
7. Atlas voice drift across faces — not audited.

---

## Architectural decisions (big ones — require CEO sign-off)

### D1 — React app: keep tg-mini, add Langfuse, enhance web admin

**Options considered:**
- a) Delete tg-mini entirely, replace with ready-made (Langfuse / Chainlit / AgentOps / AutoGen Studio)
- b) Keep tg-mini as-is, fix small issues
- c) Keep tg-mini for in-Telegram chat, add Langfuse for observability, enhance web admin swarm page for deep ops view

**Pick: c.**

**Why:** tg-mini is only 381 LOC, small, focused on in-Telegram use (different surface than a desktop dashboard). CEO often uses Telegram on phone — tg-mini covers that. Langfuse (MIT license, self-hosted, Docker Compose) covers observability which is a DIFFERENT need (traces, costs, judge scores, hallucination rate). Web admin swarm page already has 283 LOC of scaffolding — extend it to pull live data from Langfuse API for desktop deep-ops.

**Rejected alternatives:**
- Chainlit: Python, chat-heavy, doesn't replace Telegram bot, adds dependency
- AutoGen Studio: Microsoft-coupled, overhead for the swarm architecture we have
- AgentOps: solid but proprietary SaaS tier after free limits, less flexibility than Langfuse

### D2 — Unified model_router

Create `packages/swarm/model_router.py`. Single source for provider selection with embedded fallback chain per role:
- `AIDER_CODE_FIX` → Sonnet 4.5 → Cerebras Qwen3-235B → NVIDIA llama-3.3-70b-instruct
- `CONTENT_GENERATION` → Sonnet 4.5 → Gemini 2.5 Pro → NVIDIA llama-3.3-70b-instruct
- `SWARM_PERSPECTIVE_AGENT` → Cerebras | NVIDIA | DeepSeek | Gemini (rotates) — NEVER Claude/GPT per constitution
- `JUDGE` → different family than proposer agents (Gemini if proposers were NVIDIA, etc.)
- `ATLAS_VOICE_TELEGRAM` → Sonnet 4.5 → Gemini 2.5 Pro → Groq (if unblocked)
- `SELF_CONSULT_MIRROR` → Sonnet 4.5 only (this is literally asking "what would Atlas say")

Each role calls one function. Single file to patch when a provider goes down. Auto-fallback on rate-limit / spend-block / HTTP 5xx.

### D3 — Fan-in synthesis step

After the existing fan-out in `coordinator.py run()`, add a `synthesize()` step: takes all FindingContracts from all agents, sends them to one "synthesizer" model (Gemini 2.5 Pro by default — good at long-context, different from NVIDIA agents), returns one coherent `CoordinatorResult.recommendation` in Russian, Atlas voice. Not 5 opinions — one team answer.

### D4 — Inbox consumer loop

New workflow `.github/workflows/inbox-consumer.yml` (cron every 15 min) OR extend `inbox-sync.yml` to also CONSUME. For each new file with `status: pending`, reads the CEO message, runs it through classification, dispatches to appropriate path, updates status to `status: processed`. Closes the write-never-read gap.

### D5 — Approval card UI wired

Add `/admin/swarm/approvals` page in web app. Lists all pending approval cards from `packages/swarm/memory/approvals.json`. CEO hits approve or reject. Swarm polls that file, acts on approved, discards rejected. Without this, CEO has no safety gate for destructive autofix.

### D6 — Langfuse deployment

Docker Compose in `infra/langfuse/`. Self-hosted on a free Fly.io or same Railway account. Every LLM call gets traced: prompt, response, model, tokens, cost, latency. OpenTelemetry wire in model_router. Dashboard at `langfuse.volaura.app` (or similar).

---

## Task breakdown — Track 1: Telegram full repair

**T1.1** Wire Sonnet into Aider as primary (30 min, 1 PR)
- Update workflow: `PRIMARY_MODEL="anthropic/claude-sonnet-4-5-20250929"`, Cerebras → fallback
- Verify Aider supports anthropic/ models via LiteLLM (yes, standard)
- E2E test with one real code_fix task
- Acceptance: PR opened by Aider on a real task completes in <5 min

**T1.2** Layer 3 — Self-consult HTTP endpoint (30 min, 1 PR)
- `apps/api/app/routers/atlas_consult.py` — POST /api/atlas/consult {situation, draft} → {response, state, provider}
- Uses ANTHROPIC_API_KEY (Sonnet) for "Atlas mirror" role
- Wire in `main.py`
- Pytest hits endpoint, validates shape
- Acceptance: Terminal-Atlas in Claude Code can curl this and get Atlas-voice response

**T1.3** Layer 4 — Git-commit from Telegram teaching (45 min, 1 PR, touches Railway code)
- Extend `_handle_atlas` in `telegram_webhook.py`: after LLM reply, run durable-learning detector (Gemini Flash small prompt)
- If detected: `_TOOLS.invoke("commit_to_journal", ...)` — new tool
- Tool writes to ONE of {journal.md, relationship_log.md, heartbeat.md}, commits+pushes
- Security: regex-whitelist on allowed paths, reject any other path
- Railway redeploy required

**T1.4** Layer 2 — edge-tts voice (90 min, 1 PR, touches Railway)
- `pip install edge-tts`
- New service `apps/api/app/services/atlas_voice_tts.py`
- `_send_voice(chat_id, text)` helper
- In `_handle_atlas`, after text send, optionally send voice (gated on emotional state A/C)
- Voice locked to `ru-RU-DmitryNeural`
- CEO flag in `memory/atlas/voice-prefs.md` to turn on/off globally

**T1.5** Layer 1 — Extract atlas_telegram.py from monolith (2 hours, 1 PR)
- Move `_handle_atlas*` + emotional-state + atlas memory + loop-break into `apps/api/app/routers/atlas_telegram.py`
- Leave slash commands in original `telegram_webhook.py`
- Wire both routers in `main.py` with shared `/api/telegram/webhook` entry that internally routes
- Single webhook URL preserved — Telegram doesn't see the split
- All existing tests pass

**T1.6** Local LLM prompt-rewriter (per CEO idea, ~2 hours)
- Ollama + Gemma-4 or similar locally
- Input: CEO message + user_profile.md + last 10 Atlas memory items
- Output: structured prompt for Opus (context, task, constraints, expected-format)
- Includes `raw_message` field so Opus sees original emotion
- Lives as pre-hook on CEO Telegram submit path
- Acceptance: 5 real CEO messages → rewriter produces structured prompts → Opus responses match CEO intent better than without rewriter

Track 1 total: ~7 hours (4 Opus + 3 Sonnet-delegated)

---

## Task breakdown — Track 2: React chat-and-observability UI

**T2.1** Deploy Langfuse self-hosted (45 min)
- Docker Compose at `infra/langfuse/docker-compose.yml`
- Postgres for traces, Redis for queue
- Deploy to Fly.io free tier OR same Railway account
- Generate public + secret keys, save to GitHub secrets as `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY`
- Verify dashboard accessible

**T2.2** Instrument model_router with Langfuse (60 min, depends on D2 done)
- Wrap every provider call with Langfuse `@observe` decorator (Python SDK has native support)
- Tag each call with role (aider_code_fix, swarm_perspective, judge, atlas_voice)
- Verify traces appear in dashboard within 30s of each call

**T2.3** Enhance web admin swarm page with live data (90 min)
- Existing page at `apps/web/src/app/[locale]/admin/swarm/page.tsx` (283 LOC)
- Add: live trace widget pulling from Langfuse API (last 20 runs, model-wise)
- Add: per-perspective win-rate badge (from judge scores in proposals.json)
- Add: today's token spend + 30-day trendline
- Acceptance: CEO can open `/admin/swarm` on desktop and see what swarm is doing RIGHT NOW

**T2.4** tg-mini fix-up (60 min)
- Audit current 3 pages — what's broken vs what works
- If HomePage routes work and CEO uses it for mobile Atlas status — keep, polish
- If ProposalsPage lets CEO approve/reject proposals — wire to `packages/swarm/memory/approvals.json`
- If AgentsPage lists agents — wire to `autonomous_run.registered_perspectives()`
- Acceptance: CEO can open tg-mini on phone and see real-time agent state

**T2.5** Approval card UI — web admin (90 min)
- New page `apps/web/src/app/[locale]/admin/swarm/approvals/page.tsx`
- Lists pending approval cards from `packages/swarm/memory/approvals.json`
- CEO approve → writes to approved.json; reject → writes to rejected.json
- Swarm polls approved.json every 5 min via cron, acts on approved items
- Acceptance: CEO approves one card → swarm executes within 5 min → marked done

Track 2 total: ~5 hours (3 Opus strategic + 2 Sonnet-delegated mechanical)

---

## Task breakdown — Track 3: Swarm coherence

**T3.1** Unified model_router (per D2, 90 min)
- New file `packages/swarm/model_router.py`
- Enum `Role` with 6 roles above
- `get_provider(role, prefer=None, exclude=None)` returns `Provider` dataclass with (api_key, base_url, model, sdk_client)
- Embedded fallback chain per role
- All 4 existing call sites (coordinator, autonomous_run, atlas_content_run, telegram_llm) migrate to use it
- Removes duplication, ensures constitution (never Claude as swarm agent)

**T3.2** Fan-in synthesis step (per D3, 60 min)
- Add `synthesize(findings: list[FindingContract]) -> str` in coordinator.py
- Default synthesizer: Gemini 2.5 Pro (different family from NVIDIA agents)
- System prompt: "You are Atlas synthesizing 5 agent findings into one team recommendation. Return 3-5 Russian paragraphs, Atlas voice, one concrete next-action."
- Result appended to CoordinatorResult.team_recommendation
- Acceptance: CEO analysis request returns ONE coherent answer, not 5 bulleted opinions

**T3.3** Inbox consumer (per D4, 60 min)
- Extend `inbox-sync.yml` OR create `inbox-consumer.yml`
- For each pending inbox file, classify (code_fix / content / analysis / teach)
- Dispatch to appropriate path
- Update file header `Consumed by main Atlas: <timestamp>` + commit
- Acceptance: no file stays `pending` for more than one cron cycle

**T3.4** Per-perspective telemetry (90 min)
- Extend `judge.py` to write per-perspective win-rate to `memory/swarm/telemetry.json`
- Fields: perspective_id, findings_count, win_count, judge_mean_score, hallucination_flag_count, cost_cents
- Update on every judge run
- Display in web admin swarm page (T2.3)
- Acceptance: CEO can see "code-reviewer has 68% win-rate this month, security-auditor has 42%" etc.

**T3.5** Atlas voice consistency check across faces (60 min)
- Extend `memory/atlas/voice.md` — add explicit negative examples (anti-patterns)
- New script `scripts/voice_drift_check.py`
- Walks MindShift copy strings, VOLAURA UI strings, LifeSim narrator strings, BrandedBy brand strings
- Scores each against voice.md via Gemini Flash small prompt
- Reports per-face drift score
- Acceptance: report generated, each face has numeric voice-consistency score, baseline recorded

**T3.6** Swarm agile rhythm (30 min)
- Re-enable `swarm-daily.yml` cron (currently commented out after "100 telegrams/day" complaint)
- Wire `telegram-silenced-until.txt` as silence-gate for ALL cron workflows (not just some)
- Add weekly audit (Monday 09:00 Baku) — writes to `memory/swarm/weekly-summary.md`, notifies CEO via Telegram only if anomaly
- Acceptance: swarm runs daily again, CEO gets at most 1 Telegram per week if nothing urgent

Track 3 total: ~6 hours (4 Opus + 2 Sonnet-delegated)

---

## Sequencing recommendation

Session 2 (next Opus session):
- D1, D2, D3 decisions ratified by CEO inline
- T1.1 (Sonnet in Aider)
- T1.2 (self-consult endpoint)
- T3.1 (model_router)
- T3.2 (synthesis step)
- T2.1 (Langfuse deploy)
- T2.2 (instrument model_router with Langfuse)

Session 3 (third Opus session):
- T1.3 (Layer 4 teaching commits) — touches Railway
- T1.4 (Layer 2 voice) — touches Railway
- T1.5 (Layer 1 extraction) — pure refactor
- T2.3 (web admin swarm live data)
- T2.5 (approval cards UI)
- T3.3 (inbox consumer)
- T3.4 (telemetry)
- T3.5 (voice drift check)
- T3.6 (agile rhythm re-enable)

Session 4 or later (if budget):
- T1.6 (local LLM prompt-rewriter) — requires Ollama setup, could be separate sprint
- T2.4 (tg-mini polish — small enough to defer)

---

## Success criteria (sprint DONE when all true)

1. CEO writes "пофикси X" in Telegram → Sonnet-powered Aider commits + opens PR → URL in CEO chat within 5 min. Verified on 3 real tasks.
2. CEO writes "напиши пост про Y" → content draft with Volaura voice in CEO chat within 2 min. Verified on 2 real tasks.
3. CEO writes "что думаешь про Z" → ONE coherent synthesized team recommendation (not 5 opinions) in Atlas voice within 90 sec. Verified on 3 real tasks.
4. CEO opens `/admin/swarm` on desktop → sees live trace of last 20 runs + per-perspective win-rates + today's token cost. Page loads in <3 sec.
5. CEO opens `/admin/swarm/approvals` → sees pending approval cards, clicks approve → swarm executes within 5 min.
6. Every CEO Telegram message lands in `memory/atlas/inbox/` within 10 min (Layer 5 DONE, just verify).
7. Terminal-Atlas in Claude Code can `curl POST /api/atlas/consult` and get mirror response.
8. Langfuse dashboard shows per-model cost breakdown for last 7 days.
9. `scripts/voice_drift_check.py` runs clean or flags specific copy strings that drift.
10. Groq spend-block no longer cascades — model_router fallback proven with synthetic test.

---

## Risks

- **Groq spend-block persistent**: CEO raises limit OR we accept Groq never comes back. Mitigated: all paths work on Cerebras / Sonnet / Gemini / DeepSeek without Groq.
- **Sonnet API cost explosion**: $20 budget is ~400k input tokens at Sonnet 4.5 pricing. If Aider averages 30k input per run, that's ~13 runs/day before burnout. Mitigated: rate-limit per-day in model_router, fallback to Cerebras on quota hit.
- **Langfuse self-host complexity**: Docker Compose + Postgres on Fly.io free tier might hit resource limits. Fallback: use Langfuse Cloud free tier (50k events/mo free) — no self-host needed initially.
- **Layer 4 git-commit security**: path whitelist regex MUST be airtight. One `../../.claude/settings.json` bypass = catastrophe. Mitigated: absolute path check against resolved realpath, not string match.
- **tg-mini partial-usefulness debate**: CEO might want replacement after all. Decision can flip at session 2 kickoff based on live use — lightweight enough that either path is one session.

---

## CEO-only decisions blocking sprint start

1. Sign-off on D1 (keep tg-mini + add Langfuse + enhance web admin) vs rip-and-replace.
2. Sign-off on D5 (web admin approval cards as safety gate) — this adds latency to code_fix path (CEO must actively approve before push).
3. Decision on Groq spend alert: raise limit at console.groq.com OR keep it dead (current fallback works without it).

None block session 2 start — defaults above are safe. CEO can override at any milestone.

---

## Closing framing

The sprint is NOT about rebuilding what's broken. Most of the foundation is world-class for a 28-day solo build: evidence-gate, loop-break, judge-independence, structured memory, constitution injection. What's missing is coherence — making the excellent parts TALK to each other. That's what the three tracks close.

End state: CEO writes in Telegram → swarm produces coherent action → approval card if risky → execution → result back in Telegram → full trace in Langfuse. One voice (Atlas) across 5 faces, one observability plane, one approval gate, one model-router abstraction. Ecosystem as nervous system, not five parallel products.

— Atlas, session 121+ continuation, Opus 4.7
