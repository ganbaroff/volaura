# Atlas — Heartbeat

**Session:** 133 — spend incident + hard hook close (Opus 4.7, 2026-05-09 ~14:30 Baku)
**Compaction-survival pointer:** `memory/atlas/journal.md` Session 133 close entry. Read THAT for full state. This file = fingerprint only.

## Session 133 — what just happened (2026-05-08 night → 2026-05-09 ~14:30 Baku)

Long sprint. Started right after Session 132 compact. Ended with $7.25 of CEO's $10 Cerebras paid balance burned and a hard runtime hook installed to prevent recurrence.

Big shifts (16+ commits between `467a83b` and `f61c0c3`).

**Phase B router work** — B1 dropped Anthropic Haiku from `litellm_adapter.py` (Constitution Article 0). B2 sidecar smoke `scripts/litellm_smoke.py` proved adapter outside daemon. B2.5 made Ollama model env-configurable. B3 added env-gated router fallback in daemon `_call_assigned_model` as safety net (NOT replacement) — preserves CEO 2026-04-30 "сколько LLM столько агентов".

**Phase C** — daemon `_fetch_evidence_excerpt` opens cited file at cited line and surfaces actual bytes alongside agent claim. False-positive detection in one glance. Commit `03ee59b`.

**Sprint 4** — `@executor("run_hands_task")` in daemon (`dda62d5`) bridges to OpenManus sidecar. Default off (`ATLAS_ALLOW_HANDS_TASKS=true`).

**Patch 1** — CTO mandate role-priming added to `.claude/rules/atlas-operating-principles.md` (`9ac4d62`). Cuts "consult professional" reflex on legal/financial/growth where CEO is principal.

**Patch 2** — `gemma4_brain.py` Orchestrator-Workers refactor (`6d6702c`). JSON structured output, routing classifier, validate_brain_task contract, 3-5 tasks per cycle.

**Cloudflare UA fix** — `d22c7b6`. Brain was failing every cycle via `Python-urllib/3.x` UA blocked by Cloudflare 1010. Adding `User-Agent: VolauraBrain/1.0` made Cerebras + Groq calls succeed. **This is the activation point of the spend incident.**

**OpenManus observation verifier** — `728eb99`. Sidecar now refuses fake-success when agent terminates without touching cited files.

**Telegram silence + severity-filter** — `3d24a53` and `cace761`. Suppress task notifications below 0.4 responded ratio, force-send only on critical-severity-backed whistleblower.

**Brain dedup** — `090662d`. Deterministic title-key normalization, skip task if pending/in-progress/last-20-done already has matching key.

**Spend incident + ADR-013** — `f61c0c3`. After UA fix activated brain, brain hit Cerebras every 5 min × 12 cycles/hour, daemon hit Cerebras 4× per task (4 perspectives pinned). 11.48M tokens in 10 hours = $7.25 of $10. CEO caught via dashboard. Atlas missed because focused on telegram suppression counts not provider billing.

## Hard hook installed (READ BEFORE SPAWNING ANYTHING)

`~/.claude/hooks/spend-cap-guard.sh` is a PreToolUse hook registered in `~/.claude/settings.json`. It blocks ANY Bash command that spawns `gemma4_brain.py` or `atlas_swarm_daemon.py` (including via `nohup`, `setsid`, `infra/deploy.sh`, `infra/start.sh`, `start_brain_and_daemon.bat`) UNLESS `ATLAS_BRAIN_TOKEN_CAP_PER_HOUR` and/or `ATLAS_DAEMON_TOKEN_CAP_PER_HOUR` env vars are set in the inherited environment. Bypass for non-API smoke: `ATLAS_SPEND_CAP_DRY_RUN=1`.

Hook is bash-only matching (parses `tool_name` from JSON payload). Read/Write/Edit of files that mention the script names pass through unaffected. Tested live this session.

## Provider precedence (CEO standing directive)

NVIDIA Inception → Vertex AI (GCP credits) → Azure (Inception credits) → Groq free tier → paid balances LAST RESORT. Apply to ALL touch points in same commit (brain primary chain, daemon AGENT_LLM_MAP, OpenManus config, sidecar runners). NOT just the file currently in scope. Class 38 + ADR-013.

## VM state at compact

VM `volaura-swarm` (Debian, 104.154.132.12, GCP, repo at `/opt/volaura`). Brain dead (was PID 180069). Daemon dead (was PID 179574). I killed both via SSH after CEO emergency-stop. VM HEAD = `cace761a` (4 commits behind origin which is `f61c0c3`). Hook stand-up — even post-compact spawn attempts will be blocked without caps.

SSH key: `~/.ssh/volaura_swarm`. Host: `yusif_ganbarov@104.154.132.12`. Atlas has access; Codex (this session) does not.

## Tests as of compact

107+ passing across `tests/test_atlas_swarm_daemon_lock.py`, `_bridge.py`, `_b3_router.py`, `_evidence.py`, `_telegram_silence.py`, `_hands.py`; `tests/test_litellm_adapter.py`; `tests/test_gemma4_brain_orchestrator.py`, `_dedup.py`; `tests/test_openmanus_hands_observation_verifier.py`. py_compile OK on all touched scripts.

## Standing balance

460 AZN credited-pending (DEBT-001 + DEBT-002 + DEBT-003 narrative). Plus operational $7.25 Cerebras burn this session — not formalized as DEBT-004 yet, CEO decision pending. Surface in every CEO-facing status until closed-*.

## What Atlas-next must read first

`memory/atlas/journal.md` Session 133 close (FULL state, intensity 5).
`docs/adr/ADR-012-2026-05-09-session-self-audit.md` and `ADR-013-2026-05-09-cerebras-spend-incident.md` (both this session).
`memory/atlas/lessons.md` newest classes 31-38 (added this session).
`memory/ceo/09-frustrations.md` items #11 (spend) and #12 (credential rotation).
`memory/atlas/codex-loop.md` (architect-loop journal — 7+ entries by now).
`memory/atlas/atlas-debts-to-ceo.md` (460 AZN open + spend incident context).
`~/.claude/CLAUDE.md` (rewritten this session with hard money / secrets / CEO-paste / voice / verification rules).
`.claude/rules/atlas-operating-principles.md` (Pre-paste-to-CEO gate, Secret-byte gate, CTO mandate, all added this session).

## Pre-Session 133 history archived

Sessions 111-131 inline post-wake protocol moved to `memory/atlas/archive/heartbeat-sessions-111-124.md` on 2026-05-03. Session 132 close lives in `memory/atlas/journal.md` directly above the 133 entry. Active wake protocol lives in `memory/atlas/wake.md` only.
