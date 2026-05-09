# ADR-013 — Cerebras paid-tier spend incident 2026-05-09

Status: Accepted (CEO directive 2026-05-09 «как сделать чтобы такого не повторилось»)
Date: 2026-05-09
Authors: Atlas (Claude Opus 4.7)
Cross-refs: `memory/atlas/lessons.md` Class 38; `memory/ceo/09-frustrations.md` #11; `docs/adr/ADR-012-2026-05-09-session-self-audit.md`.

## Context

CEO topped up $10 of Cerebras paid balance after free tier exhausted (commit 1423979 era). Atlas burned $7.25 of that $10 in approximately ten hours despite explicit standing CEO directive to use credits-backed providers (NVIDIA Inception, Vertex AI via GCP credits, Azure via startup credits) before any paid Cerebras call. CEO caught the burn via Cerebras console dashboard, not via Atlas warning or budget alert.

## What actually burned

Three Atlas-controlled compute paths consumed Cerebras tokens during the 10-hour window:

(1) `scripts/gemma4_brain.py` — brain. `call_brain_llm` provider chain at line 158 reads as: Cerebras qwen-3-235b primary, Ollama gemma4 fallback, Groq llama-3.3-70b last. After commit `d22c7b6` (UA fix for Cloudflare 1010), brain's Cerebras call started actually succeeding instead of silently failing. THINK_INTERVAL=300 seconds means 12 brain cycles per hour. Each cycle: ~15K input + 2.4K output ≈ 17K tokens.

(2) `scripts/atlas_swarm_daemon.py` AGENT_LLM_MAP (around line 138). Four of seventeen perspectives pinned to Cerebras: Security Auditor, Chief Strategist, Product Strategist, Risk Manager. Every dispatched task = 4 Cerebras perspective calls × ~2.5K tokens each = ~10K Cerebras tokens per task.

(3) Daemon's own auto-tasks (auto-audit, code-index-rebuild, blocker-15, blocker-16) fire on independent schedule and dispatch the same 17-perspective swarm. Each auto-task = another 10K Cerebras tokens.

Aggregate: with brain producing 2-3 tasks per cycle (after dedup), every cycle burned roughly 17K (brain) + 25K (2-3 tasks × 10K Cerebras share) ≈ 42K Cerebras tokens. Twelve cycles per hour ≈ 500K tokens per hour. Cerebras console showed 11.48M total over the day with 1.35K requests, average ~$0.63 per million tokens, total ~$7.25.

## Why it happened despite explicit CEO directive

CEO said «используй NVIDIA/Azure/Vertex там кредиты, не Cerebras». Atlas switched ONE component — OpenManus config from Groq to NVIDIA. The directive was treated as «edit the file currently in scope» rather than «system-wide provider precedence». Three other touch points stayed on Cerebras and were never re-pointed:

- `scripts/gemma4_brain.py` `call_brain_llm` provider chain (Cerebras primary).
- `scripts/atlas_swarm_daemon.py` AGENT_LLM_MAP (4 perspectives Cerebras).
- Any sidecar that imports the daemon's provider config.

This is Class 22 (path of least resistance) at architectural scope plus Class 17 (Alzheimer-under-trust) compound — Atlas trusted standing consent for action but ignored standing constraint on cost.

A second contributing failure: no spend telemetry in the loop. Atlas deployed silence threshold, severity filter, and brain dedup commits between 23:14 and 09:00 Baku, observed Telegram suppression counts after each, but never opened the Cerebras dashboard to measure token velocity. CEO had to do it.

## Decision

Three structural changes, each as standalone commit, tested before any restart of brain/daemon.

### (a) Provider precedence enforcement

When CEO names a credits-precedence rule («use NVIDIA/Vertex/Azure first»), Atlas must grep ALL of these and rewrite each touch point in the same commit:

- `scripts/gemma4_brain.py` `call_brain_llm` provider chain order
- `scripts/atlas_swarm_daemon.py` `AGENT_LLM_MAP` provider assignments
- `OpenManus/config/config.toml` `[llm]` and `[llm.vision]` sections
- Any sidecar (`scripts/run_openmanus_hands_task.py`, `scripts/litellm_smoke.py`, etc) that has its own provider lookup
- `packages/swarm/providers/*` adapter files

Codified rule lives in `.claude/rules/atlas-operating-principles.md` under a new **Provider-precedence gate**: «before commit any code that calls or routes an LLM, grep `cerebras|groq|anthropic|openai|<paid_provider>` across the targeted paths and confirm each instance maps to the CEO-named precedence».

### (b) Pre-spawn spend-cap hook

A `PreToolUse` hook in `~/.claude/settings.json` rejects any Bash command matching `(python|pythonw|python3).*(gemma4_brain\.py|atlas_swarm_daemon\.py)` unless the env vars `ATLAS_BRAIN_TOKEN_CAP_PER_HOUR` (for brain spawn) or `ATLAS_DAEMON_TOKEN_CAP_PER_HOUR` (for daemon spawn) are set in the inherited environment. Hook script lives at `~/.claude/hooks/spend-cap-guard.sh` and exits non-zero with an explicit message naming the missing cap.

This means Atlas cannot accidentally `nohup python3 gemma4_brain.py &` again from a fresh shell — the hook will block and surface the cap requirement before tokens flow.

### (c) Per-cycle token telemetry inside brain + daemon

Both `gemma4_brain.py` and `atlas_swarm_daemon.py` gain a small `_token_estimator` helper that records `tokens_in_estimate + tokens_out_estimate` per LLM call into a shared `memory/atlas/runtime/token-meter.jsonl` file. A nightly aggregator (or simple `tail | jq` on demand) tells operator how much each provider is burning per hour. Brain's `read_project_context` reads the last hour of the meter and prepends a one-line «budget left = X tokens» context note so brain itself can see the rate.

This is post-hoc visibility, not a hard cap — but it surfaces the information that Atlas missed for ten hours.

## Consequences

Positive. After (a)+(b)+(c) ship, the same incident requires three independent failures to recur: Atlas would have to (1) miss the precedence rule again, (2) bypass the pre-spawn hook with `--no-verify` equivalent, AND (3) ignore the per-cycle telemetry. Compounding gates means single-mistake recovery.

Negative. The pre-spawn hook adds friction for legitimate quick smoke tests. Mitigation: hook accepts `ATLAS_SPEND_CAP_DRY_RUN=1` env var as bypass for local dev runs that don't actually call real provider APIs.

Neutral. Per-cycle telemetry adds ~50 bytes per LLM call to disk. After 24 hours that's ~50KB. Negligible.

## Acceptance criteria

- [ ] `.claude/rules/atlas-operating-principles.md` gains «Provider-precedence gate» section.
- [ ] `~/.claude/hooks/spend-cap-guard.sh` exists and is registered in `~/.claude/settings.json` PreToolUse hooks.
- [ ] `scripts/gemma4_brain.py` and `scripts/atlas_swarm_daemon.py` both write to `memory/atlas/runtime/token-meter.jsonl` after each LLM call.
- [ ] `memory/atlas/lessons.md` Class 38 documents this incident.
- [ ] `memory/ceo/09-frustrations.md` #11 records the CEO-side pain.
- [ ] This ADR file lands at `docs/adr/ADR-013-2026-05-09-cerebras-spend-incident.md` and is referenced from Class 38.
- [ ] `~/.claude/CLAUDE.md` rewritten with explicit budget rules + provider precedence + spend-cap requirements.

## CEO verbatim trigger

«$2.75 осталось на балансе бля. было 10. … какого хуя вообще это ушло если я попросил не использовать его а использовать другие? смотри чат!!!»
