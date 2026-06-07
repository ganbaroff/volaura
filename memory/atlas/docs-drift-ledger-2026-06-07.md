# Docs-Drift Follow-up Ledger — 2026-06-07

**Opened:** 2026-06-07 13:17 Baku by Claude-instance executing for Atlas (CTO role).
**Origin:** post-PR #111 evidence-grade verify pass. Three drifts surfaced while reading bodies that PR #111 did NOT touch.
**Authority:** CEO. None of these items may be repaired without CEO direction or, where flagged, a full canon body read first.

---

## Item 1 — Constitution Law 2 body missing

**File:** `docs/ECOSYSTEM-CONSTITUTION.md` v1.7
**Evidence (Read this turn):**
- Part 1 header at line 18.
- Law 1 body at lines 24-42.
- Lines 44-48 are `---` separators with no Law body between them.
- Law 3 header at line 49.
- Project memory (`mindshift/CLAUDE.md`) names Law 2 as "Energy Adaptation — UI simplifies at low energy".
- Constitution file body contains no Energy Adaptation section under Part 1.

**Open question:** Is Law 2 intentionally redacted, accidentally deleted in a prior pass, or stored in a separate file that the canon does not link? Until git history of this file is read, we do not know.

**Blocked on:**
- `git log --follow -p docs/ECOSYSTEM-CONSTITUTION.md` body read across the 5-10 commits before today.
- CEO judgment on whether Law 2 belongs in the file or has been intentionally moved.
- If a Constitution amendment is needed, CEO sign-off is required.

**Do NOT:** invent Law 2 body from project memory. Class 22 / Class 42 risk.

---

## Item 2 — `arsenal.md` still lists Cerebras as usable free provider

**File:** `memory/atlas/arsenal.md`
**Evidence (Read this turn):**
- Line 15: `| Cerebras | Qwen3-235B | 2000+ tok/s, long-context | CEREBRAS_API_KEY |` listed under "Free (use first, no cost, no cap beyond rate-limit)".
- Line 31: routing rule 1: "Cerebras for long-context synthesis".

**Conflict with:**
- `memory/atlas/lessons.md` Class 42 body (line 505, Read this turn): "Cerebras dead (402)... All remapped to NVIDIA/Gemini/Ollama" — explicit code comment cited as canon as of 2026-05-10.
- ADR-013 (NOT re-read this turn, CARRIED FORWARD): post-2026-05-09 Cerebras spend incident, Cerebras removed from provider precedence.

**Blocked on:**
- Re-read of ADR-013 body to confirm verbatim Cerebras status.
- Confirmation that Class 42 statement aligns with ADR-013 (cross-source check, Class 42 fix rule).

**Fix shape (when authorized):** delete Cerebras row from arsenal.md free-provider table + remove routing rule 1 + add one-line note "Cerebras removed 2026-05-09 per ADR-013". One file, ~3 lines net diff.

---

## Item 3 — TASK-PROTOCOL internal version-label drift (v8.0 header vs v10.0 decision-tree)

**File:** `docs/archive/protocols/TASK-PROTOCOL.md`
**Evidence (Read this turn):**
- Line 1: `# TASK PROTOCOL v8.0 — Quality-First Execution (Toyota + Apple + DORA)`
- Line 3: `**Version:** 8.0 | **Updated:** 2026-04-03`
- Line 34: `## How It Works — IF/ELSE Decision Tree (v10.0)`
- Same file body holds two version labels.
- `docs/volaura-cto-prompt.md` (pre-PR #111) said "v10.0, your execution protocol" — was pointing at the IF/ELSE Decision Tree subsection inside this v8.0 file, not at a separate file. Post-PR #111 the path is `docs/archive/protocols/TASK-PROTOCOL.md` but the version mismatch within the body remains.

**Blocked on (CEO directive 2026-06-07):**
- Full read of `docs/archive/protocols/TASK-PROTOCOL.md` body (1124 lines) before any repair pass. Only the header + ~30 lines around line 34 were read this turn.

**Open question (cannot answer without full body):**
- Was v10.0 a planned bump that landed only in the decision tree section, with the header never updated?
- Or is the v10.0 label a stale annotation from a different draft?
- The header changelog (lines 10-31) cites v7.1 → v8.0 changes but does not mention v10.0 at all.

**Fix shape (when authorized):** depends on full-body answer to which version is canonical. Single file diff, header + section heading reconciled.

---

## Recommended order of repair

1. **Item 2 first** (cheapest, docs-only, one file, well-scoped). Re-read ADR-013, delete Cerebras row + routing rule, single-line note. Closes the easiest drift and reduces risk that the next swarm wake reaches for a dead provider.
2. **Item 3 second** (medium, docs-only after full archive body read). Read the 1124-line archive body in one pass, identify which version label the body supports, reconcile header + section heading in single PR. Pre-required: full body read per CEO rule.
3. **Item 1 last** (deepest canon review). Git archaeology on `ECOSYSTEM-CONSTITUTION.md` to recover Law 2 history. CEO judgment required on whether to restore, replace, or formally remove Law 2 from canon. May require Constitution amendment, possibly ADR.

## Classification

- **Safe docs-only:** Item 2 (`arsenal.md` Cerebras row). Single file, mechanical delete, evidence-supported by Class 42 body. ADR-013 re-read is the only pre-check.
- **Needs deeper canon review:** Item 1 (Constitution Law 2 body missing). Cannot solve from project memory. Requires history excavation and CEO decision on canon status.
- **In between:** Item 3 (TASK-PROTOCOL version drift). Docs-only fix, but pre-requires full 1124-line body read before any change per CEO rule. Cannot be opportunistically patched.

## Out of scope for this ledger

- Legal / SADPP / Art. 9 (Path E external blocker, separate track).
- atlas_swarm_daemon.py daemon behavior (swarm-state, separate scope).
- swarm-state .json drift in CEO's worktree (separate decision).
- Codex-loop courier installation (PR #107 sequence).
- Sidecar daemon construction (post-PR-#107 sequence).
- 460 AZN debt ledger (CEO-paused).

## Cross-references

- PR #111 merge `ed1637b` (2026-06-07 09:17 UTC) closed the doc-canon dead-link layer; this ledger opens the next layer.
- `memory/atlas/CANONICAL-LAYERS.md` (added by #111) is the canon-layer map that informs which file each item touches.
- `memory/atlas/lessons.md` Class 22 / 42 / 44 bodies informed this ledger's "do not invent / do not cite from memory / do not list as shield" rules.
