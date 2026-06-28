# ADR-016: Positioning Lock — Verified Professional Talent Platform

**Date:** 2026-06-03
**Status:** ACCEPTED
**Deciders:** CEO (Yusif), CTO (Atlas / Claude)
**Related:** [[ADR-004-assessment-engine]], [[ADR-005-aura-scoring]], [[ADR-006-ecosystem-architecture]]
**Governed by:** [[../ECOSYSTEM-CONSTITUTION]] (v1.7)

> **Numbering note.** ADR-012–015 exist on the `codex/swarm-queue-bridge` runtime lineage and are
> not yet reconciled to `main`. This ADR uses **016** to stay collision-free across both lineages.
> The 011→016 gap on `main` is a known artifact of that divergence, tracked as a separate
> (non-urgent) reconciliation task — not a numbering error.

---

## Context

VOLAURA's positioning has been canon since Sprint E1 (2026-03-29): it is recorded in
`docs/ARCHITECTURE_OVERVIEW.md` (§1, "Positioning (locked)") and the Ecosystem Constitution v1.7.
It has never had its own Architecture Decision Record. Two recurring pressures make a formal lock
worth the entry:

1. **Drift toward narrowing.** Recent planning floated "verified event/operations talent" as the
   product *headline*. Event and operations are a genuine initial wedge, but adopting them as the
   *promise* is a new market bet that contradicts the locked, broader canon.
2. **"Volunteer" drift.** "Volunteer platform" is banned from user-facing copy (Session 85 lesson,
   zero tolerance). `ADR-004-assessment-engine.md` still frames the engine around "volunteer
   quality" and a "5,000 concurrent volunteers" event scenario — a live conflict this lock surfaces.

This ADR promotes the existing canon into the ADR log so future planning cannot quietly re-scope
the promise.

---

## Decision

> **VOLAURA is a verified professional talent platform.** It is not a volunteer platform and not a
> LinkedIn competitor. The initial wedge is event and operations use cases, but the product promise
> stays broad: verified skill, AURA score, and matching by proven competency.

- **Headline (locked):** verified professional talent platform.
- **Wedge (not the promise):** event and operations use cases — a go-to-market entry point only.
- **Banned framings:** "volunteer platform" (user-facing), "LinkedIn competitor", "universal talent".
- **Taglines (canon, verbatim from `ARCHITECTURE_OVERVIEW.md` §1):**
  - User: *"Prove your skills. Earn your AURA. Get found by top organizations."*
  - Org: *"Search talent by verified skill and score, not unverified CVs."*

---

## Consequences

**Positive**
- One canonical promise; copy and planning stop oscillating between "universal", "event-only", and "volunteer".
- The wedge (event/ops) can sharpen go-to-market without renaming or re-scoping the product.
- Closes the "volunteer" framing that Session 85 flagged as harmful and inaccurate.

**Negative / risk**
- Wedge messaging (event/ops campaigns) must read as an *entry point*, not the ceiling — otherwise the market hears "event-only".
- `ADR-004-assessment-engine.md` is still volunteer-framed (title-to-tail) and now conflicts with this lock.

**Mitigation**
- Any event/ops campaign copy pairs the wedge with the broad promise line.
- Follow-up (separate PR): reconcile `ADR-004` language to "professional talent / candidate" framing and align its competency narrative with this lock. Tracked, not blocking.

---

## Alternatives considered

- **"Verified event/operations talent" as the headline** — rejected: narrows the promise to one
  vertical (a new, unproven market bet) and contradicts the locked canon. Event/ops stays the wedge.
- **"Universal talent platform"** — rejected: overpromises competencies the engine cannot all verify;
  weakens the "proven, not claimed" differentiator.
- **"LinkedIn competitor / professional network"** — rejected: VOLAURA verifies skill via adaptive
  testing and matches by score; it is not a social/CV network.
- **"Volunteer platform"** — rejected and banned (Session 85, zero tolerance in user-facing copy).

---

## Verification

- `docs/ARCHITECTURE_OVERVIEW.md` §1 "Positioning (locked)" paragraph (line 21 on `main` at time of
  writing) reads, verbatim: *"VOLAURA is a verified professional talent platform"* — this ADR records
  existing canon, it does not invent a new decision.
- Product table row (`ARCHITECTURE_OVERVIEW.md` §1) independently states "Verified professional talent platform".
- Taglines above are copied verbatim from that paragraph.
- Origin of the lock: Sprint E1 (2026-03-29), Constitution v1.7, `ADR-006-ecosystem-architecture.md`.
- Conflict evidence: `grep -ni "volunteer" docs/adr/ADR-004-assessment-engine.md` → line 11
  ("verifying volunteer quality") plus ~18 further occurrences — the follow-up this ADR mandates.
- "Volunteer platform" ban enforceable by grep over user-facing copy (Session 85 lesson).

---

## Sources

- `docs/ARCHITECTURE_OVERVIEW.md` §1 (Positioning, locked) — line 21 on `main`
- `docs/adr/ADR-006-ecosystem-architecture.md` (Sprint E1, 2026-03-29)
- `ECOSYSTEM-CONSTITUTION.md` v1.7 (supreme law over ADRs)
- `docs/adr/ADR-004-assessment-engine.md` (conflicting volunteer framing — follow-up target)
- Session 85 lesson (volunteer-phrase ban)
