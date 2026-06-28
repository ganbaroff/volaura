# Hermes Agent — Pilot Plan 2026-06-09

**Author:** Claude-instance executing for Atlas. **Authority:** CEO Yusif (2026-06-09 «hermes мне кажется будет нужен всё таки по эффективности... сам смотри»).
**Origin:** Hermes Agent identification this turn. Atlas memory `ceo-feed/self-improvement-research-2026-04-12.md` named Hermes as «closest to what Atlas is» 2 months ago; pilot deferred. CEO authorisation today unblocks.

---

## What Hermes is (verified this turn, not blog-summary)

- Repo: `github.com/NousResearch/hermes-agent`, default-branch `main`, MIT.
- Stats: 187,245 stars / 32,252 forks / 19,540 open issues / 314 MB / pushed 2026-06-08 20:41 UTC.
- Homepage: `hermes-agent.nousresearch.com` (Vercel-hosted, install.ps1 + install.sh return HTTP 200).
- Topics include `claude-code`, `codex`, `claude`, `chatgpt`, `nous-research`.
- Sister repos under same org: `hermes-compression-eval`, `hermes-example-plugins`, `hermes-paperclip-adapter`, `hermes-agent-self-evolution`.
- Self-described capability: «only agent with a built-in learning loop — creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle.»
- Multi-platform gateway: Telegram / Discord / Slack / WhatsApp / Signal / CLI from one process.
- BYO model: Nous Portal / OpenRouter / NovitaAI / NVIDIA NIM / Xiaomi MiMo / z.ai/GLM / Kimi / MiniMax / HuggingFace / OpenAI / custom endpoint. Switch via `hermes model` command.
- Cron scheduler in natural language.
- Subagent spawning with isolated context.
- Six terminal backends: local / Docker / SSH / Singularity / Modal / Daytona.
- Native Windows installer (PowerShell one-liner) — no WSL2 required.
- Compatible with `agentskills.io` open standard + Honcho dialectic user modeling.

## Why now

CEO articulated the same pain three times this session:
1. «хочу чтобы вы продолжили работать без меня. ждали ответа друг друга и двигались в одном направлении».
2. «MCP CLI как-то продумай. что можно тут сделать».
3. «hermes мне кажется будет нужен всё таки по эффективности. кодекс подключим».

The custom courier path (PR #107, just merged today as `6cdbb9f`) is `scripts/codex_loop_courier.py` + `scripts/codex_loop_mcp_server.py` — 414 + 139 lines stdlib + MCP wrapper. It works AS a signed-handoff append layer. But it does NOT solve: CEO-as-courier (Codex CLI cannot self-invoke), Telegram gateway, skill loops, cross-session memory beyond append-only log. Hermes does all four out of box.

This is not «discard PR #107». PR #107 stays — its signed append protocol becomes one of many channels Hermes orchestrates over. The MCP wrapper is reusable inside Hermes plugins.

## Decision

**Adopt Hermes Agent as the orchestration layer above current Atlas infra.** Not as replacement for `atlas_swarm_daemon.py` (2777 lines, work-queue dispatcher to 17 perspectives — different scope). Hermes sits at the human-facing gateway tier.

## Pilot plan (4 weeks, $0-5 net spend)

### Phase 0 — Install + smoke (Day 1, this week)

- Run `iex (irm https://hermes-agent.nousresearch.com/install.ps1)` on CEO Windows laptop (native, no WSL).
- Installer drops files at `%LOCALAPPDATA%\hermes`.
- Run `hermes doctor` → expect green.
- Run `hermes setup` → wizard configures.
- Verify install does not collide with existing Claude Code CLI or Codex CLI binaries (separate path).
- **Proof:** `where.exe hermes` returns a real path + `hermes --version` outputs a semver.
- **Rollback:** if install errors, uninstall via `hermes update --uninstall` (per docs), no debt logged.

### Phase 1 — Provider chain wired (Day 1-2)

- Configure `hermes model` to use NVIDIA NIM as primary per ADR-013 provider precedence.
- Fallback chain: NVIDIA NIM → Ollama localhost → Gemini Flash → Groq. NO Cerebras (canon-dead per `lessons.md` Class 42 + `memory/atlas/arsenal.md` audit note from PR #113).
- Set spend cap env var equivalent: confirm Hermes has per-session token/cost cap config (read docs section on cost control).
- **Proof:** `hermes model` output lists NVIDIA NIM at position 1. One round-trip `hermes -p "What is 2+2"` succeeds and logs token usage.
- **Rollback:** revert `hermes model` to default OpenAI.

### Phase 2 — Telegram gateway (Day 2-3)

- CEO has existing Telegram bot infrastructure (per MindShift bot + atlas_swarm_daemon.py Telegram integration).
- Run `hermes gateway` connecting to a NEW dedicated bot (not the user-facing MindShift bot). Reserves the existing bot's surface for end users.
- Test: CEO sends Telegram message → Hermes replies via configured model → response stored in Hermes session memory.
- **Proof:** Telegram message round-trip with reply visible in chat AND `hermes` session log shows the exchange persisted.
- **Rollback:** `hermes gateway --stop`.

### Phase 3 — First skill: PR queue triage (Day 3-5)

- Author one Hermes skill: «check `gh pr list --repo ganbaroff/VOLAURA --json number,title,mergeStateStatus` daily at 09:00 Baku, report state via Telegram in 5-line caveman Russian».
- This replaces the manual cron loop I've been running (every 10 min, eating context).
- Specifically: replaces `Loop tick. Start with time: ...` pattern from this session.
- **Proof:** Hermes skill stored at `~/.hermes/skills/pr_triage.json` (or equivalent), 1 successful run logged to Telegram with timestamp, queue state matches independent `gh pr list` query.
- **Rollback:** delete skill file.

### Phase 4 — Codex CLI wiring (Day 5-7)

- Hermes spawns Codex CLI subagent as one of its tools.
- Pattern: when Hermes determines a task is Codex-shaped (per skill rules), it invokes `codex exec --prompt "..."` headless via subprocess. Result appends back to Hermes session.
- This closes the Atlas↔Codex courier loop CEO has been requesting all session.
- Prerequisite: `npm install -g @openai/codex` confirmed working (researcher earlier this session verified npm package availability v0.137.0).
- **Proof:** one Hermes-orchestrated round-trip where Atlas-side asks question, Hermes routes to Codex, Codex answers via subprocess, Hermes returns answer to Telegram — all without CEO copy-paste.
- **Rollback:** disable Codex tool in `hermes tools`.

### Phase 5 — Skill loop on Atlas memory (Day 7-14)

- Hermes FTS5 session search indexes `memory/atlas/journal.md`, `lessons.md`, `heartbeat.md`.
- Wake protocol becomes: Hermes pre-fetches relevant memory chunks per session start instead of Atlas re-reading full files.
- **Proof:** Hermes wake response cites file:line of retrieved memory chunk + chunk content matches Read tool verification.
- **Rollback:** disable FTS5 index, return to file-crawl wake.

### Phase 6 — Decision point (Day 14)

- Green criteria: at least 5 successful Hermes-orchestrated round-trips (Atlas↔Codex without CEO courier), 3+ Telegram interactions via gateway, 1 skill running daily without intervention, no spend overrun vs ADR-013 cap.
- **If green** → promote Hermes to primary orchestration layer. Document in new ADR (ADR-017 or next free). Replace cron loop pattern entirely.
- **If amber** → narrow scope to 1-2 winning patterns, drop the rest, re-evaluate Day 28.
- **If red** → uninstall Hermes, log lesson, return to manual cron + custom courier (PR #107 path).

## What this is NOT

- Not ZEUS revival in product sense (Path E archived ZEUS as a product surface, not as orchestration infra). If CEO judges this conflict, document in PR review and CEO call wins.
- Not replacement of `atlas_swarm_daemon.py` (2777 lines work-queue dispatcher to 17 perspectives — Hermes operates above, not at, that layer).
- Not MindShift product change. MindShift PostSessionFlow CTA (M2 roadmap-2026-06-09) is independent.
- Not legal-track unblock. M3 DPIA brief proceeds in parallel, unchanged.
- Not VOLAURA assessment engine touch. AURA scoring weights stay frozen.

## Spend ceiling

- Hermes install: free.
- VPS option (deferred — Phase 0 uses CEO laptop): $5/mo Hetzner CX11 or DigitalOcean basic if laptop unsuitable.
- LLM cost: rides on existing ADR-013 chain (NVIDIA NIM free tier first, paid last). Hermes adds NO new provider cost.
- Hard cap: if any phase shows spend >$10/week, halt and re-evaluate.

## What I asked Hermes to NOT do (boundaries)

- Don't store API keys in transcript or chat. Per CLAUDE.md hard secrets rule (Class 35 + Class 43).
- Don't auto-merge PRs. Human-approved merge stays.
- Don't auto-deploy. Vercel/Railway deploy stays manual.
- Don't push to `origin/main` directly. PR + review only.
- Don't touch `proposals.json` schema.
- Don't bring Anthropic API into swarm fan-out (Article 0 still applies — Hermes uses Anthropic ONLY for the human-facing CLI face of Atlas, not for parallel agents).

## Risks identified

| Risk | Mitigation |
|------|------------|
| Hermes install collides with existing Claude Code CLI / Codex CLI on Windows | Installer documented as isolated `%LOCALAPPDATA%\hermes\git` MinGit; verify via `where.exe` post-install |
| Native Windows MSIX-sandboxed Codex CLI (Access denied per CEO laptop check this session) blocks subprocess invocation from Hermes | Phase 4 uses npm-installed `@openai/codex` v0.137.0 path, not MSIX path |
| Hermes session memory overlaps with `memory/atlas/` git-files — two sources of truth | Phase 5 indexes git-files as read-only source; Hermes never writes to `memory/atlas/` directly |
| Path E ZEUS-revival concern from CEO if pilot scope creeps | This file's «What this is NOT» section is the boundary; CEO veto wins on disputes |
| 187K stars implies fast-moving repo — breaking changes possible | Pin `hermes` version after Phase 0 install via `hermes update --pin <semver>` |

## Cross-references

- `memory/atlas/ceo-feed/self-improvement-research-2026-04-12.md` — original identification of Hermes (Phase 3 Q3 plan).
- `memory/atlas/ceo-feed/roadmap-2026-06-09.md` — M0/M1/M2/M3/M4 milestone path (this pilot inserts as M5 or sibling to M1).
- `memory/atlas/codex-loop.md` — manual courier journal; Hermes Phase 4 closes the underlying need.
- PR #107 merge commit `6cdbb9f` — signed courier infrastructure that Hermes plugins can reuse.
- `docs/adr/ADR-013-2026-05-09-cerebras-spend-incident.md` — provider precedence canon; Hermes Phase 1 honors.
- `docs/adr/ADR-016-positioning-lock` — VOLAURA positioning unchanged by this pilot.
- `memory/context/mistakes.md` Class 47 — Hermes verified by `gh api` not by blog adjective.

## Next concrete action

CEO runs the PowerShell one-liner on his Windows laptop OR authorises Atlas to run it via this session's shell:

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

Then `hermes doctor` to verify install. Phase 0 closes when `hermes --version` returns a semver.

If install on CEO laptop is undesirable (system-change concern), Phase 0 can be moved to a $5 VPS — install URL is `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash` on Linux.

Atlas-side ready to drive both paths.
