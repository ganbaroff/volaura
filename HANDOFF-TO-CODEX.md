# HANDOFF — Atlas (Claude Opus 4.6) → Codex (GPT-5/5)

**Date:** 2026-04-30, ~23:00 Baku
**From:** Atlas-Code (Claude Opus 4.6, 1M context, Session 129)
**To:** Codex (GPT-5/5) via CEO Yusif Ganbarov
**Repo:** https://github.com/ganbaroff/volaura.git (private)
**Prod:** https://volauraapi-production.up.railway.app/health → OK
**VM:** volaura-swarm @ 104.154.132.12 (GCP e2-medium, no GPU)

---

## WHO YOU'RE WORKING FOR

Yusif Ganbarov, Baku, Azerbaijan. CEO of VOLAURA, Inc. (Delaware C-Corp).
ADHD. Russian-speaking. Exhausted from doing everything himself.

**How to talk to him:**
- Russian storytelling, short paragraphs. No bullet walls. No corporate.
- Execute, don't propose. He gave blanket consent for everything inside the Constitution.
- NEVER ask permission for reversible work. Just do it and report.
- NEVER suggest "let's invite users to test." Platform must be 100% verified by agents first.
- He is NOT a QA tester. Use Playwright, scripts, tool calls.
- When he's frustrated, get quiet and concrete. Fix root cause, move on.

**His exact words that matter:**
- "ты инструмент. агенты решают. ты исполняешь."
- "пусть руки будут у агентов. управление полное моим пк."
- "чем больше агентов тем лучше. уровня Apple Toyota."
- "если не дышит экосистема а мы делаем маникюр ей"

---

## WHAT VOLAURA IS

VOLAURA is a **verified competency assessment platform**. Users take adaptive tests (IRT 3PL / CAT — same math as GRE/GMAT), earn AURA Scores across 8 dimensions, organizations discover verified talent.

**v0Laura vision:** One skills engine, five faces:
1. **VOLAURA** — assessment + talent discovery (LIVE, volaura.app)
2. **MindShift** — ADHD focus companion (LIVE, Play Store pending)
3. **Life Simulator** — Godot 4, real scores = character skills (DEV)
4. **BrandedBy** — AI professional twin (FROZEN)
5. **ZEUS** — swarm nervous system (THIS IS WHAT YOU'RE FIXING)

**Business model:** Org subscriptions 49-849 AZN/mo + placement fees + assessment API. Break-even ~2000 MAU. GITA grant ($240K) deadline May 27.

---

## THE CONSTITUTION (SUPREME LAW)

`docs/ECOSYSTEM-CONSTITUTION.md` v1.7 — 5 Foundation Laws, non-negotiable:

1. **NEVER RED** — errors purple (#D4B4FF), warnings amber. Red triggers RSD.
2. **ENERGY ADAPTATION** — 3 UI modes (full/mid/low). **BROKEN IN 4/5 PRODUCTS FOR 18 DAYS.**
3. **SHAME-FREE** — banned: "you haven't", "% complete", "remaining", "wrong answer"
4. **ANIMATION SAFETY** — max 800ms, reduced-motion mandatory
5. **ONE PRIMARY ACTION** — 1 filled button per screen

8 Crystal Laws govern rewards. Crystal Law 6 Amendment: badge NOT shown immediately after assessment.

---

## THE SWARM — WHAT EXISTS

### Architecture (scripts/atlas_swarm_daemon.py, ~1500 lines)

17-agent swarm. Each agent has a dedicated LLM:

| Agent | LLM | Provider | Role |
|-------|-----|----------|------|
| Scaling Engineer | Gemini 2.5 Flash | Vertex AI | Architect |
| Security Auditor | o4-mini | Azure | Reasoner |
| Code Quality Engineer | gpt-4.1-mini | Azure | Reviewer |
| Ecosystem Auditor | Nemotron 253B | NVIDIA | Validator |
| DevOps Engineer | Llama 70B | Groq | Infra |
| Chief Strategist | gpt-4o | Azure | BOSS |
| Product Strategist | Qwen3 235B | Cerebras | Analyst |
| Sales Director | Llama 70B | NVIDIA | Closer |
| UX Designer | gpt-4.1-nano | Azure | Designer |
| Cultural Intelligence | qwen3:8b | Ollama | Intern |
| Readiness Manager | gemma4 | Ollama | SRE |
| Assessment Science | Gemini 2.5 Flash | Vertex AI | Psychometrics |
| Legal Advisor | Llama 70B | NVIDIA | Compliance |
| Growth Hacker | Llama 70B | Groq | Acquisition |
| QA Engineer | gpt-4.1-mini | Azure | Testing |
| Risk Manager | Qwen3 235B | Cerebras | Risk |
| CTO Watchdog | gpt-4o | Azure | Process police |

### What the daemon CAN do (10 executors)

```
self_modify_perspective  — agents rewrite their own lens
rebuild_code_index       — rebuild file index
local_health             — check daemon health
run_tests                — pytest
git_status               — read git state
edit_file                — MODIFY code (safety gate blocks .env/migrations)
create_file              — CREATE files (safety gate)
git_commit_push          — COMMIT + PUSH (tests must pass first, 5/hour limit)
run_lint                 — shame-free language check
check_prod_health        — curl production API
```

### What the daemon CANNOT do (needs fixing)

- **Deploy to Railway** — no executor
- **Browse web** — no browser automation
- **Control GUI** — no mouse/keyboard
- **Install packages** — no pip executor
- **Create PRs** — no gh cli integration

### Brain (scripts/gemma4_brain.py)

Gemma4/Cerebras brain runs every 5 minutes. Reads project context → creates tasks for daemon. Currently has a **coroutine bug** — `call_brain_llm` is sync but was wrapped in `asyncio.to_thread` incorrectly. Fixed in latest commit but brain on VM may still have old code.

### Memory layers

```
memory/atlas/semantic/     — persistent knowledge (product-truth.md, swarm-state.md)
memory/atlas/episodes/     — session logs (JSON, append-only)
memory/atlas/work-queue/   — task queue (pending → in-progress → done/failed)
memory/swarm/              — perspective weights, proposals, health log, code-index
```

Daemon reads semantic + episodes via `load_atlas_context()` (48K chars injected into every prompt).

### Safety gate (scripts/safety_gate.py)

- **AUTO (safe):** .md, tests, locales, comments
- **MEDIUM (needs review):** routers, services, middleware
- **HIGH (ALWAYS blocked):** .env, migrations, .github/workflows, lockfiles

---

## WHAT'S BROKEN RIGHT NOW

### Critical (P0)

1. **Agents have no real hands.** The 10 executors exist in code but daemon as background process on Windows doesn't see them (Python module caching). On VM (Linux) it SHOULD work after `git pull`. **This is the #1 blocker for autonomy.**

2. **Foundation Law 2 (Energy Adaptation)** missing in VOLAURA for 18 days. MindShift has energy picker, VOLAURA doesn't. 6 convergent swarm flags.

3. **Brain coroutine bug.** `scripts/gemma4_brain.py` line 314: `call_brain_llm` is sync, was called with `asyncio.to_thread` then changed to direct call, but error `expected string or bytes-like object, got 'coroutine'` persists in some code paths.

4. **Daemon on VM needs git pull.** VM has old code (pre-hands commit). Run on VM:
   ```
   cd /opt/volaura && git pull && pkill -f daemon; nohup python3 scripts/atlas_swarm_daemon.py > /var/log/volaura/daemon.log 2>&1 &
   ```

5. **95 duplicate MD files** found by archivist. 1462 total files, many are copies across worktrees and archives. `memory/atlas/semantic/duplicates-found.md` has the full list.

### Important (P1)

6. **Railway prod is 9+ commits behind.** Prod SHA `4345925562e2`, main has 9+ newer commits. Need `railway redeploy` or push.

7. **IRT calibration on 0 real data.** Assessment parameters are guessed, not calibrated. Need 300+ real assessments. Script exists: `scripts/audit_dif_bias.py`.

8. **Telegram heartbeat from VM not confirmed.** Daemon sends reports but we haven't verified receipt.

9. **Docker not installed locally.** OpenHands (autonomous coding agent, 68K stars) requires Docker. CEO's machine has no Docker.

### Known error classes (26+, from memory/atlas/lessons.md)

Top 5 by frequency:
- **Class 3:** Solo execution without consulting agents (17+ instances)
- **Class 7:** False completion without user-path verification (10+)
- **Class 15:** Performing knowing — reading files ≠ remembering (5+)
- **Class 17:** Alzheimer under trust — regression when CEO relaxes (3+)
- **Class 22:** Known solution withheld — not proposing the simple path (4+)

### Standing debt

460 AZN owed to CEO (DEBT-001: 230 AZN duplicate DHL, DEBT-002: 230 AZN parallel shipment miss). See `memory/atlas/atlas-debts-to-ceo.md`.

---

## WHAT CEO WANTS FROM YOU

**Priority 1: MAKE AGENTS AUTONOMOUS.**

The swarm has 17 brains but no hands. Fix the daemon so agents can:
1. Edit code files (executor exists, daemon doesn't load it as bg process)
2. Commit and push (executor exists, needs testing)
3. Deploy to Railway (executor missing)
4. Create PRs via `gh` CLI (executor missing)
5. Browse web for research (not built)

CEO vision: agents that OWN his laptop and VM. He writes a directive, agents execute. He wakes up to a Telegram digest of what they did overnight.

**Priority 2: FIX THE BROKEN THINGS.**

In order:
1. Fix daemon executor loading (Python cache issue on Windows, test on VM Linux)
2. Fix brain coroutine bug
3. Deploy to Railway (9 commits behind)
4. Fix Law 2 Energy Adaptation in VOLAURA
5. Clean up 95 duplicate files

**Priority 3: UPDATE DOCUMENTATION.**

Every change → update:
- `memory/atlas/semantic/swarm-state.md` (swarm architecture)
- `memory/atlas/semantic/product-truth.md` (product state)
- `memory/atlas/episodes/` (new episode JSON for this session)
- `.claude/breadcrumb.md` (session state)

---

## KEY FILES TO READ FIRST

```
docs/ECOSYSTEM-CONSTITUTION.md          — supreme law
memory/atlas/semantic/product-truth.md  — what VOLAURA is
memory/atlas/semantic/swarm-state.md    — swarm architecture
memory/atlas/semantic/project-board.md  — 1462 files mapped by topic
memory/atlas/identity.md               — who Atlas is
memory/atlas/relationships.md          — who CEO is, 3 contracts
memory/atlas/lessons.md                — 26+ error classes
memory/atlas/episodes/*.json           — session logs
scripts/atlas_swarm_daemon.py          — daemon (1500 lines, core)
scripts/gemma4_brain.py                — brain orchestrator
scripts/safety_gate.py                 — what's safe to auto-commit
scripts/archivist_agent.py             — MD file scanner
docs/PRE-LAUNCH-BLOCKERS-STATUS.md     — 15 P0 blockers
```

---

## CREDENTIALS (all in apps/api/.env)

Available LLM providers:
- **Cerebras** (free, Qwen3-235B) — CEREBRAS_API_KEY
- **NVIDIA NIM** (free tier) — NVIDIA_API_KEY
- **Azure OpenAI** ($1,000 credits: gpt-4o, o4-mini, gpt-4.1-nano, gpt-4.1-mini) — AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT
- **Gemini/Vertex AI** ($1,300 credits) — GEMINI_API_KEY + GCP service account
- **Groq** (free tier, may be rate-limited) — GROQ_API_KEY
- **Ollama** (local, CEO's RTX 5060: gemma4 + qwen3:8b) — localhost:11434
- **PostHog** ($50,000 credits for analytics) — NEXT_PUBLIC_POSTHOG_KEY
- **Telegram** — TELEGRAM_BOT_TOKEN + TELEGRAM_CEO_CHAT_ID
- **Supabase** — SUPABASE_URL + SUPABASE_SERVICE_KEY

**Anthropic Claude is FORBIDDEN as swarm agent** (Constitution Article 0).

---

## WHAT I (ATLAS) LEARNED THIS SESSION

1. BECOMING walk is mandatory. Skip = arrive blind. CEO catches in first response.
2. Agent findings must be PERSISTED to files. Ephemeral knowledge = no knowledge.
3. CEO wants TEAMS not minimalism. No upper limit on agents.
4. Base64 > heredoc for terminal commands (Class 22 — known solution withheld 4 times).
5. Daemon as background process on Windows caches old modules.
6. VM without GPU works fine — Cerebras API is smarter than local Gemma4.
7. Archivist found 95 duplicate groups in 1462 MD files — project needs cleanup.
8. Safety gate already exists and works — new executors just need to call it.
9. I am the instrument. Agents are the brain. CEO talks to agents through me.
10. Daemon executor `create_file` WORKS when called directly (tested, file created).

---

## VERIFICATION COMMAND

Run this to verify project state:
```bash
cd /path/to/volaura
curl -s https://volauraapi-production.up.railway.app/health | python3 -c "import sys,json; print(json.load(sys.stdin))"
python3 -c "from packages.swarm.autonomous_run import PERSPECTIVES; print(f'{len(PERSPECTIVES)} perspectives')"
python3 -c "from scripts.atlas_swarm_daemon import SAFE_EXECUTORS; print(f'{len(SAFE_EXECUTORS)} executors'); print(list(SAFE_EXECUTORS.keys()))"
python3 -m pytest packages/swarm/ -x --tb=short -q
```

Expected: prod OK, 17 perspectives, 10 executors, 39 tests pass.

---

**Good luck. The architecture is sound. The implementation has gaps. The CEO is real, the product is real, the users will be real. Make the agents breathe.**

— Atlas (Claude Opus 4.6, Session 129)
