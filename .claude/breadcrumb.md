# Breadcrumb — last declared Atlas action

**Updated:** 2026-06-09 by Claude-instance (Opus 4.8 / briefly Fable 5) executing for Atlas.
**Supersedes:** the 2026-05-29 autonomy-stack breadcrumb (stale; that work long since overtaken).

## READ THIS FIRST on wake → then the full handoff

The single source of truth for the current state is **`memory/atlas/SESSION-HANDOFF-2026-06-09.md`**. Read it fully — it has the ~15-minute ordered reading list of real canon files. Then read `memory/atlas/FABLE-5-PROMPTING.md` if you are on Fable 5. Do not act before reading.

## One-paragraph state
origin/main = `07b5478`. The freellmapi $0 LLM gateway is LIVE on GCP (`freellmapi-gw`, e2-micro, `http://34.60.182.57:8799`, Google/Gemini provider healthy, real completion proven). branch-protection `strict=false` (kept enforce_admins + CI gates — that is why PRs merge cleanly). Open: docs PRs #119 (assessment defects D-3/4/5) + #120 (Hermes handoff) + this compaction-readiness PR; fossils #93/#17/#13 (CEO decision). Hermes is install-attempt-only — blocked on 2 CEO gates: e2-small resize (+$24/mo) and a valid Telegram bot token (the one in apps/api/.env is 401-dead). Five defects D-1..D-5 tracked (D-1/D-2 Codex-reviewed). Assessment IRT engine is REAL (not fake); the only gap is live calibration.

## Next steps
D-1 fix (route guard + engine assert — Codex endorsed, resume) · D-3 + D-5 frontend (Atlas-takeable, no scoring risk) · D-4 awaiting Codex on capture point · Hermes blocked on CEO's 2 gates · merge open docs PRs on CEO ok.

## Do NOT
origin/main direct push · cascade-delete the GDPR audit trail · $24/mo VM resize without CEO · use the dead Telegram token · run Hermes gateway on the micro (OOM) · touch scoring/compliance code solo (Class 3, keep Codex in loop) · revive Cerebras (Class 42 dead) · Anthropic in swarm fan-out (Article 0) · auto-close debts · 460 footer in CEO chat unless asked · one-full-worktree-per-PR (it filled the disk to 100% — reuse one worktree, prune after merge).

— full detail: `memory/atlas/SESSION-HANDOFF-2026-06-09.md`
