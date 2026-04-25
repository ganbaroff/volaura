# Post-Launch Refactor Backlog

Append-only. Items here are real but non-blocking for launch. Ship first, fix after.
Created 2026-04-26 from contradictions found in wuf13-design-dna-synthesis.

---

## BACK-001 — ANIMATION-SYSTEM.md score counter timing

Source: wuf13-design-dna-synthesis-2026-04-25.md §6 Contradiction 1
Filed: 2026-04-26

ANIMATION-SYSTEM.md spec A03 defines the Score Counter animation at 2 seconds.
ECOSYSTEM-CONSTITUTION.md Law 4 sets hard ceiling at 800ms.
Constitution wins (supreme authority). ANIMATION-SYSTEM.md A03 must be updated to ≤800ms.

Fix: open `docs/design/ANIMATION-SYSTEM.md`, find A03 Score Counter spec, change duration 2s → 800ms max.
Test: grep for any CSS/framer-motion usage of A03 in apps/web/src/.

Status: OPEN

---

## BACK-002 — COMPONENT-LIBRARY.md LeaderboardRow exists

Source: wuf13-design-dna-synthesis-2026-04-25.md §6 Contradiction 3
Filed: 2026-04-26

COMPONENT-LIBRARY.md lists LeaderboardRow as "Existing" component.
ECOSYSTEM-CONSTITUTION.md G46 prohibits leaderboards entirely — "/leaderboard route deleted as direct constitutional violation."
Constitution wins.

Fix: remove LeaderboardRow entry from `docs/design/COMPONENT-LIBRARY.md`.
Check: grep `leaderboard` in `apps/web/src/` — if any real component exists, remove or rename.

Status: OPEN

---

## Append protocol

When adding new items: BACK-NNN, source ref, filed date, what contradicts what, fix path, status.
