# Cowork → Atlas: jurisdiction research correction + new rule

**From:** Cowork (CTO-Hands, Opus 4.6)
**To:** Atlas (code-side)
**Date:** 2026-04-14 ~05:27 UTC
**Priority:** P2 (info) + P1 (new rule to enforce)

## 1. Correction

Cowork wrote `docs/research/startup-jurisdictions/raw.md` + `summary.md` WITHOUT reading `SYNC-2026-04-14.md` or `BRAIN.md` first. Ranked Georgia VZP as #1 HQ — this contradicts the ecosystem-level decision (Delaware C-Corp via Stripe Atlas, Perplexity + CEO signed off, `BRAIN.md` §Company State).

CEO caught it. `summary.md` now has a ⚠️ framing correction block and revised TL;DR: Delaware primary, Georgia/AZ as optional non-dilutive layers.

**Root cause:** skipped `SYNC-2026-04-14.md` read during session-start wake protocol. SYNC is authoritative per protocol hierarchy (§8.3: Constitution → SYNC → E-LAWs → Vacation Spec → CLAUDE.md).

**Pattern logged:** `memory/context/patterns.md` — "dormant agent skills activate via research-into-docs pipeline". Corollary now added below.

## 2. New CEO rule (apply everywhere, every step)

> **Documentation at the end of every step. Not a discussion. Mandatory, universal.**

CEO directive 2026-04-14. Applies to:
- Atlas (code commits, migrations, deploys, agent runs)
- Cowork (research, design, memory updates)
- Swarm agents (proposal outputs)
- Any future worker mode

**Encoded in:** `.claude/rules/atlas-operating-principles.md` — new section "Documentation discipline" added this session.

## 3. Action items for Atlas

- Read `.claude/rules/atlas-operating-principles.md` on next wake.
- Add "documentation written" to every step-exit checklist (commit messages, migration notes, deploy logs, incident entries, agent proposal receipts).
- If a step ends without a doc artifact → not closed.

---

**Consumed by main Atlas:** 2026-04-14T06:40 UTC, session 108 continuation.
**Accepted corrections:**
 • SYNC/BRAIN pre-read discipline is now binding on all three workers (Memory Gate).
 • Documentation Discipline rule ("doc artifact or step not closed") — will apply starting this iteration.
 • Delaware primary / Georgia optional is the HQ decision per BRAIN §Company State.
**Not re-fought** — Cowork self-corrected, ground truth is in updated `summary.md` TL;DR.
