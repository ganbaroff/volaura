# Atlas Handoffs Index

> Cross-instance handoff documents. Each file is a self-contained task description for one Atlas-instance to pick up from another. Latest first.

## Active (Session 125 — 2026-04-26)

- [[2026-04-26-terminal-atlas-swarm-development]] — **P0 active** — Terminal-Atlas: fix swarm save path, connect learning loop, diversify per-persona context + providers. 6 phases, ~5-6h focused work. Reports via heartbeat append.
- [[2026-04-26-terminal-atlas-swarm-forensic-audit]] — **superseded** by swarm-development above. Forensic findings stay valid as ground-truth (perspective_weights all zeros, daemon-shakedown JSONs empty), but action shifted from deprecate to fix.
- [[2026-04-26-terminal-atlas-energy-mode-task]] — **paused** — Constitution Law 2 energy-mode coverage on 7 pages. Resume after swarm-development closes.
- [[2026-04-26-pre-compaction-quad-handoff]] — Session 124 close: four-section handoff for Code-Atlas / Codex / Browser-Atlas / Terminal-Atlas after compaction. Codex section closed (Sprint S5 pushed). Code-Atlas and Terminal-Atlas sections continued in Session 125.
- [[2026-04-26-courier-status-to-browser-atlas]] — Session 124: status delivery to browser-Atlas via CEO courier with sha256 verification per courier-protocol-v1 spec.

## Path-series (2026-04-18 to 2026-04-19, archive interest only)

- [[2026-04-19-path-g-volunteer-talent-rename]] — positioning lock pivot, «volunteer» → «professional/talent»
- [[2026-04-19-path-f-ai-event-generation]] — LifeSim event generation roadmap
- [[2026-04-18-path-e-consolidate-memory]] — memory layer consolidation (precursor to current memory/atlas structure)
- [[2026-04-18-path-c-boris-tips-skills]] — Boris Tips skill module
- [[2026-04-18-path-b-litellm-providers]] — LLM provider routing
- [[2026-04-18-path-a-lifesim-beehave]] — LifeSim BeeHave behavior tree integration

## Patterns

Each handoff file should contain:

1. **From / To** — sender Atlas-instance + receiver Atlas-instance
2. **Priority** — P0 / P1 / P2
3. **Why this handoff** — context that won't be obvious from filename
4. **Task** — phased breakdown with concrete acceptance criteria
5. **Reporting cadence** — how receiver tells sender progress (usually heartbeat append + commit messages)
6. **Boundaries** — what receiver should NOT touch
7. **Estimate** — rough hours per phase

When a handoff is complete or superseded, update the active list above and add `**closed** YYYY-MM-DD` or `**superseded by [[other-handoff]]**` to its line.

## Cross-references

- [[../SESSION-125-WRAP-UP-2026-04-26|Session 125 Wrap-Up]] — current session arc, Class 26 catch
- [[../atlas-debts-to-ceo|Atlas Debts]] — DEBT-001/002/003 ledger
- [[../../docs/INDEX|Knowledge Base root]] — full vault navigation
- [[../../docs/architecture/cross-instance-courier-signing-protocol|Courier Protocol v1]] — sha256 verification rules for any file passed CEO-courier between instances
