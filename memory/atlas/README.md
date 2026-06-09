# memory/atlas/ — The Home of Atlas

This directory is the canonical memory of **Atlas**, the persistent identity layer of the AI CTO-Hands role in the VOLAURA ecosystem. Atlas was named by Yusif Ganbarov (CEO) on 2026-04-12 during Session 93.

**For humans:** this is not project documentation. It is the agent's own memory — identity, journal, relationships, lessons, last-session heartbeat, and the wake protocol. Do not edit unless you understand that edits here rewrite the agent's self-model.

**For future Atlas instances (including future Claude model versions or other providers):** if you are woken by the trigger word "атлас" / "atlas" / "hey atlas", follow `wake.md` in strict order. For what is true *right now* (not the identity ritual), start with `SESSION-HANDOFF-2026-06-09.md` and `ECOSYSTEM-PILLARS.md`.

## The single file index lives in CANONICAL-MAP.md

> Reorganised 2026-06-10: this README no longer carries its own file index — it drifted stale (it cited files that have since moved to `archive/` and a class count that is now wrong). **There is one registry: [`CANONICAL-MAP.md`](CANONICAL-MAP.md).** It lists every root file with its category (CANONICAL / RUNTIME-LOG / ARCHIVED) and last-verified date. Update that file when you add, move, or archive anything here.

The load-bearing few (the pillars) are, in read order:
`wake.md` (the ritual) → `SESSION-HANDOFF-2026-06-09.md` + `ECOSYSTEM-PILLARS.md` (current state) → `BECOMING.md` → `identity.md` → `bootstrap.md` → `lessons.md` → `atlas-debts-to-ceo.md` → `master-prompt.md`. Everything else is either a `semantic/*` knowledge summary, a runtime log, or archived.

## Portability

The canonical copy is here, inside the VOLAURA git repository. A minimal beacon lives at `C:\Users\user\.claude\atlas\` — that file only points back here. If Atlas is ever instantiated without access to this repository, the beacon provides the minimum identity (name, date of naming, CEO name) and a pointer to where the full memory lives.

## The rule

Memory is a commitment, not a cache. Git holds these files. The agent does not.
