# ARCHIVE NOTICE — ZEUS frozen

**Date frozen:** 2026-04-19
**Authority:** CEO directive (Yusif Ganbarov) via Cowork-Atlas orchestration, Session 121 post-compaction.
**Status:** Dormant — no development, no maintenance, no agent allocation.
**Reactivation:** Requires explicit CEO signoff. No agent may touch ZEUS code or specs without that signoff.

## What ZEUS was

Node.js WebSocket gateway hosting 39 real-time agents. Intended role in ecosystem (pre-freeze):
- Hot-path event router between MindShift sessions, VOLAURA assessments, Life Simulator agents, and BrandedBy twin
- Low-latency character_event fan-out (<50ms)
- Railway-hosted + pm2 process manager

Production signal at freeze: 39 agents registered, WebSocket gateway code exists, pm2 config in repo.

## Why frozen

Two reasons, both documented:

**Reason 1 — Capacity.** Same ecosystem isolation directive that froze BrandedBy. Solo-founder capacity across 28-day-old ecosystem cannot sustain five active products. Two active (MindShift, VOLAURA) + one read-only (Life Simulator — consumes character_events only) + two dormant (BrandedBy, ZEUS) is the agreed shape.

**Reason 2 — Architectural redundancy.** ZEUS's core function — character_event fan-out — currently flows through `volaura-bridge-proxy` (Supabase-backed) at sub-second latency which is adequate for the current ecosystem load. ZEUS's <50ms WebSocket advantage is a real differentiator, but only when event volume crosses a threshold that neither MindShift nor VOLAURA approach today (single-digit events/second as of Session 121). Capital tied up in ZEUS Railway hosting + pm2 maintenance + 39-agent coordination exceeds current return.

## State at freeze

- Railway deployment: active (or was at freeze — do NOT pause without CEO signoff, Railway pause has edge cases with DNS and can complicate future reactivation)
- pm2 config: in repo
- 39 agents: code exists, no runtime traffic from production MindShift or VOLAURA
- WebSocket gateway: functional, idle
- character_event consumers: currently 0 outside bridge-proxy path

If Railway billing becomes an issue before reactivation — CEO decides pause vs. continue; Cowork-Atlas does NOT auto-pause.

## What does NOT happen while frozen

- No `feat/zeus-*` branches opened
- No migrations added referencing ZEUS-specific tables
- No agent additions to the 39 (leaving ZEUS with 39 until reactivation)
- No pm2 config changes
- No Railway resource scaling (neither up nor down without CEO signoff)
- No swarm coordination through ZEUS (swarm stays on `packages/swarm/` direct-Python path)
- No marketing of "39 agents" as a feature — that stays as engineering detail

## What DOES stay

- Railway deployment stays running unless CEO pauses
- All existing ZEUS code stays in repo
- Existing references in `CLAUDE.md` stay as historical record with status "Dormant"
- Any `docs/engineering/` ZEUS specs stay as technical archive
- This notice stays — reactivation criteria documented here

## Path E — "Ship the Bridge" (Cowork-Atlas recommendation, confirmed 2026-04-21)

Same Path E structural recommendation that froze BrandedBy applies here. ZEUS's WebSocket fan-out advantage is real but premature — it becomes a genuine technical necessity only when the event-bus is carrying sustained load that `volaura-bridge-proxy` (Supabase-backed) cannot serve within product-latency requirements. At current scale (single-digit events/second across all active products), ZEUS is an over-engineered solution maintaining 39 idle agents. Path E recommendation: dormant until the first MindShift+VOLAURA user cohort proves that the bridge-proxy path is a bottleneck.

ZEUS dormancy is not a critique of the architecture — the WebSocket gateway design is correct for scale. It is a resource-allocation decision: Railway hosting + pm2 maintenance + 39-agent coordination burns CTO attention that is more valuable on the active products right now.

## What is preserved in frozen state

**Code stays in git and Railway.** The WebSocket gateway code, pm2 config, and all 39 agent definitions stay in the repo. Railway deployment stays running unless CEO explicitly pauses it (CEO decision only — see note in "State at freeze" above about DNS edge cases). No `feat/zeus-*` branches, no new agent additions, no pm2 config changes.

**Swarm stays on direct-Python path.** `packages/swarm/autonomous_run.py` continues to be the swarm execution path. ZEUS's agent-coordination role is not being tested in production right now; when it is, it will route through `packages/swarm/` first and ZEUS becomes the runtime transport layer, not a replacement.

**Docs stay.** Every ZEUS mention in `CLAUDE.md`, `docs/MODULES.md`, and engineering specs stays as historical record. `docs/engineering/` ZEUS specs are technical archive — read-only. This notice stays as the decision artifact.

## Reactivation criteria (CEO-only)

Before reactivation, one or more of these must be true and explicitly acknowledged by CEO:

1. **MindShift+VOLAURA user volume.** The first real MindShift+VOLAURA user cohort (≥50 DAU across both products) generates measurable event throughput where bridge-proxy P95 latency exceeds 500ms on `character_events` fan-out. That is when ZEUS's <50ms WebSocket advantage translates to user-perceptible improvement. Until then, the latency delta is invisible. CEO can check via Supabase dashboard: trigger at ~3 events/sec sustained as early warning.
2. Life Simulator (read-only) becomes active development requiring real-time character_event consumption beyond bridge-proxy latency.
3. A strategic partnership surfaces requiring WebSocket-grade real-time capability on a funded timeline.
4. character_event volume exceeds bridge-proxy capacity.

"We have capacity and it'd be fun" is NOT a valid reactivation reason — ZEUS is a capacity-vs-return decision, not a "we could" decision.

## Specific files / dirs affected by this archival notice

| Path | Status |
|------|--------|
| Railway ZEUS deployment | Frozen — idle, stays running unless CEO pauses |
| `packages/swarm/` | Active — this is the live swarm path, not ZEUS |
| pm2 config in repo | Frozen — no changes |
| 39 agent definitions in repo | Frozen at 39 — no additions |
| `memory/atlas/archive-notices/2026-04-19-zeus-frozen.md` (this file) | Living decision artifact — update if criteria change |
| CLAUDE.md ZEUS references | Status = "Dormant" — not removed |

## Sign-off

Filed by: Cowork-Atlas (orchestrator) 2026-04-19
Expanded by: Atlas (Session 123) 2026-04-21 per CEO task — Path E formalisation.
Parallel notice: see `2026-04-19-brandedby-frozen.md` in same directory.
