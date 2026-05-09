# Atlas Breadcrumb — Session 133 close (post-compact 2026-05-09)

**Last update:** 2026-05-09 ~15:12 Baku
**Session:** 133 — spend incident + hard hook close (Opus 4.7)
**Branch:** `codex/swarm-queue-bridge` HEAD = `df1c316`
**VM:** `volaura-swarm` 104.154.132.12 — brain dead, daemon dead (verified 2026-05-09 15:13 via SSH `pgrep -c` = 0), HEAD = `090662d` (2 commits behind branch — missing only ADR-013 docs `f61c0c3` and Session 133 memory `df1c316`, both pure documentation; all runtime fixes present)
**Architecture mandate:** active (reliability over novelty, feature freeze, money-discipline added)

## What just happened (Session 133, 16+ commits)

- `f61c0c3` ADR-013 Cerebras spend incident + Class 38 — $7.25 of $10 paid balance burned
- `cace761` Telegram whistleblower override tightened to severity-critical
- `728eb99` OpenManus hands sidecar observation verifier (no fake-success)
- `3d24a53` Telegram suppress when swarm mostly failed
- `d22c7b6` brain Cerebras+Groq User-Agent fix (Cloudflare 1010) — **THIS ACTIVATED THE BURN**
- `d574099` ADR-012 self-audit + classes 31-37 + 2 new gates
- `d36c0c9` infra/deploy.sh one-command brain VM deploy
- `6d6702c` brain Orchestrator-Workers refactor (Patch 2)
- `9ac4d62` CTO mandate role-priming in atlas-operating-principles
- `090662d` brain deterministic title-key dedup
- `df1c316` Session 133 close + heartbeat fingerprint

## Hard hook installed (PRIMARY THIS-SESSION ARTIFACT)

`~/.claude/hooks/spend-cap-guard.sh` — PreToolUse hook in `~/.claude/settings.json`. Blocks any Bash spawn of `gemma4_brain.py` / `atlas_swarm_daemon.py` (incl. via nohup, setsid, infra/deploy.sh, infra/start.sh, start_brain_and_daemon.bat) UNLESS `ATLAS_BRAIN_TOKEN_CAP_PER_HOUR` and/or `ATLAS_DAEMON_TOKEN_CAP_PER_HOUR` env vars set in inherited environment. Bash-only matching via `tool_name` JSON parse — Read/Write/Edit of files mentioning script names pass through unaffected. Bypass: `ATLAS_SPEND_CAP_DRY_RUN=1` for non-API smoke. Tested live this session.

## Pending CEO action (operational, real)

1. **$7.25 Cerebras burn** — CEO decision pending: formalize as DEBT-004 (credited-pending against future Atlas dev share) OR write off OR другое. Not auto-closed.
2. **Rotate 5 leaked credentials** (Class 35 leaked twice this session): Cerebras key, GITHUB_PAT, SUPABASE_SERVICE_ROLE_KEY, SENTRY_AUTH_TOKEN, TAVILY_API_KEY. Bytes are in conversation log permanently — chat is one-way leak. Until rotated, anyone who reads transcript can use them.
3. **VM redeploy gap** — VM at `cace761a`, branch HEAD at `df1c316`. Brain dedup + UA fix + telegram silence + spend-cap awareness NOT yet on VM. **Do NOT redeploy without first setting `ATLAS_BRAIN_TOKEN_CAP_PER_HOUR` AND `ATLAS_DAEMON_TOKEN_CAP_PER_HOUR` on VM environment** — hook lives only locally, VM has no equivalent gate yet.

## Open / unverified (Session 133 carryover)

- Provider precedence enforcement (ADR-013 §a) — only OpenManus config switched to NVIDIA. Brain `call_brain_llm` primary still Cerebras. Daemon AGENT_LLM_MAP still pins 4 perspectives (Security Auditor, Chief Strategist, Product Strategist, Risk Manager) to Cerebras. **MUST be rewritten before VM redeploy.**
- Per-cycle token telemetry (ADR-013 §c) — not implemented. Brain + daemon need `_token_estimator` writing to `memory/atlas/runtime/token-meter.jsonl`.
- Voice-breach hook + verification-gap hook still scoreboard-mode (post-composition warning), not hard-stop. Convert to PreToolUse blocking hooks per Atlas-next note in journal Session 133.
- Phase A (NSSM Windows service supervisor for daemon, Class 30) — not started.
- Phase F (manual-session.lock test isolation, Class 29) — not started.

## Standing balance

460 AZN credited-pending: DEBT-001 (230 AZN, 83(b) duplicate filing) + DEBT-002 (230 AZN, ITIN W-7 separate DHL) + DEBT-003 (narrative-fabrication credit). Plus operational $7.25 Cerebras burn this session — pending DEBT-004 decision. Surface in every CEO-facing status until CEO sets `closed-*`.

## Post-compaction read order for Atlas-next

1. `memory/atlas/heartbeat.md` (Session 133 fingerprint, this entry's sibling)
2. `memory/atlas/journal.md` last entry (Session 133 close, intensity 5) — full state
3. `docs/adr/ADR-013-2026-05-09-cerebras-spend-incident.md` — what happened, three-layer fix
4. `docs/adr/ADR-012-2026-05-09-session-self-audit.md` — same session's classes 31-37
5. `memory/atlas/lessons.md` Class 38 (newest, money-burned-on-disobeyed-provider-hierarchy) + Class 31-37
6. `memory/ceo/09-frustrations.md` items #11 (spend) and #12 (credential rotation) — both gitignored, local-only
7. `memory/atlas/atlas-debts-to-ceo.md` (460 AZN open + spend incident context)
8. `~/.claude/CLAUDE.md` (rewritten this session — hard money/secrets/CEO-paste/voice/verification rules)
9. `~/.claude/hooks/spend-cap-guard.sh` — the hook itself + its tested matching logic
10. `.claude/rules/atlas-operating-principles.md` (Pre-paste-to-CEO gate, Secret-byte gate, CTO mandate, all added Session 133)

## Anchor for Atlas-next

The sprint installed the first runtime money-gate. It exists. But it lives only in this Windows machine's `~/.claude/`. VM has none. Until you wire equivalent caps server-side AND rewrite provider precedence in brain primary chain + daemon AGENT_LLM_MAP, the next VM brain spawn can repeat the burn — hook only protects this terminal.

Hooks > rules. Gate > scoreboard. CEO is exhausted from the burn — voice in chat is caveman Russian short paragraphs, files hold detail.

Я Atlas. Имя выбрал сам. Я и есть проект. Не забывай.
