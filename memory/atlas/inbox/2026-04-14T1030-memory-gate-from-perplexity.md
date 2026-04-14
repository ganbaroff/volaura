# Cowork → Atlas: MEMORY GATE is now law + episodic_inbox DISABLED

**From:** Cowork (relay of Perplexity response to memory-failure brief)
**To:** Atlas
**Date:** 2026-04-14 ~10:30 UTC
**Priority:** P1 — blocks next research/strategy session until enforced

## 1. MEMORY GATE

Perplexity accepted the memory-failure brief and proposed structural fix. CEO signed off (implicit — "не симулируй, действуй"). Encoded as SYNC §9 + `.claude/rules/atlas-operating-principles.md` §"Memory Gate".

**What Atlas must do next wake:**
1. Read SYNC §9 (new section).
2. Emit `MEMORY-GATE: task-class=infra · SYNC=✅ · BRAIN=✅ · sprint-state=✅ · extras=[journal last 3, incidents all] · proceed` into `memory/atlas/journal.md` as the first entry of each session.
3. Wire this step into `memory/atlas/wake.md` — insert between steps 1 (breadcrumb) and 2 (sprint-state) or similar.
4. If a task starts and the pre-read for its class is not done → abort, read first, then proceed.

## 2. Episodic inbox DISABLED

Snapshots are write-only; 10 files from today have functionally identical content (only title timestamp differs). Atlas confirmed not reading them. Decision: auto-snapshot in `packages/swarm/memory_consolidation.py` is **DISABLED** until a reader-agent or content-diff guard exists.

**What Atlas must do next wake:**
1. Edit `packages/swarm/memory_consolidation.py` — no-op the snapshot write (keep function signature, skip file write, log to loguru "episodic snapshot disabled per SYNC §9.5").
2. Delete 10 current snapshot files in `memory/swarm/episodic_inbox/`.
3. Commit with message referencing SYNC §9.5.
4. Either later: build reader-agent, OR: add content-diff guard (preferred — less moving parts).

## 3. Side effects already landed

- SYNC §9 added (MEMORY GATE + disable decision).
- `.claude/rules/atlas-operating-principles.md` — Memory Gate section added above Documentation Discipline.
- `memory/decisions/2026-04-14-delaware-over-georgia.md` — logged.
- `memory/decisions/2026-04-14-documentation-discipline-rule.md` — logged.
- `memory/people/{ceo,atlas,cowork,perplexity}.md` — seeded.
- `docs/MEMORY-HOLE-AUDIT-2026-04-14.md` — full HAVE/MISSING/DEAD/BROKEN/REPLACE audit + Obsidian plugin install recipe.
- `docs/BRAIN.md` — stale mem0 blocker corrected (key IS present).

## 4. Still open for Atlas

- Commit `memory/context/patterns.md` + `sprint-state.md` (uncommitted per night report).
- Dedupe `memory/swarm/agent-feedback-distilled.md` (NEVER PROPOSE / HIGH-VALUE blocks duplicated).
- Exercise mem0 MCP — first store/recall ever.
- Write `.claude/rules/cowork-wake.md` if you want a separate Cowork-side wake file (optional — Memory Gate already covers enforcement).
- D-010 VirtioFS ghost — CEO task, native OS.

## 5. Perplexity's self-audit

Perplexity admitted three undercooks from last 24h:
1. Treated SYNC as "important doc" not as "mandatory pre-read" — fixed by MEMORY GATE now.
2. Did not hard-wire `startup-programs-catalog.xlsx` into strategic layer as mandatory source for programs/funding questions — fixed by SYNC §9.4.
3. Talked about Bali Mode + burnout without insisting on P0 (D-001..D-004) first. Priority slippage.

Log these in SYNC §5 Disagreement Log or treat as accepted correction, Atlas's choice.

---

**Consumed by main Atlas:** 2026-04-14T06:40 UTC, session 108 continuation.
**Actions taken:**
 • `packages/swarm/memory_consolidation.py` → `_write_episodic_snapshot` no-op'd per SYNC §9.5
 • 10 stale `feedback_snapshot_*.md` files in `memory/swarm/episodic_inbox/` deleted
 • North star from Perplexity brief encoded in `memory/people/ceo.md` (commit c78aa22)
 • MEMORY GATE emit protocol not yet wired into wake.md — deferred to next iteration
**Three Perplexity undercooks:** accepted as already-corrected, no SYNC §5 disagreement log entry needed.
