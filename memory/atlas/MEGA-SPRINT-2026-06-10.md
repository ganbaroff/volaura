# MEGA-SPRINT 2026-06-10 — overnight, Opus-executed, CEO asleep

> **Who runs this:** Claude **Opus 4.8** (`/model claude-opus-4-8`). NOT Fable 5 — every stage touches integrity/access/swarm code and Fable 5's safety filter blocks it (confirmed 2026-06-10). **Why a prompt, not Hermes:** Hermes is blocked on two CEO-only gates (e2-small resize + a valid Telegram token) and the owner is asleep; it adds an orchestration layer without adding capability for this sprint. So Opus executes directly. The freellmapi $0 gateway is already the real autonomy win.

## The vision (what "success" means here)
Two live products (VOLAURA assessment, MindShift), one clean code spine, tests that actually RUN, a workspace that is git-checkouts-only (not a 20-folder junkyard), and a Constitution that tells the truth about what exists. Build forward ONLY on VOLAURA + MindShift. Everything tonight serves "unbury + make the foundation trustworthy" — no new product features (those need Codex / the owner).

## Operating mode (read before acting)
You are operating autonomously; the owner is asleep and cannot answer. For reversible actions that follow from this brief, proceed without asking. Pause/stop only at the explicit STOP lines below (judgment calls reserved for the owner). When you have enough information to act, act. Before reporting progress, audit each claim against a tool result; if a test is red, say so with the output — never hide it. Checkpoint into PRs at each stage so any interruption is cheap to resume. Do the simplest thing that works; no refactoring beyond what each stage names. You have ample context; do not stop or summarize early on account of context limits.

**Branch/merge policy (overnight):** one branch per stage, open a PR, let CI run.
- Docs / canon / CI-config / test-wiring PRs that go **fully green** → you may squash-merge.
- Anything that touches product runtime code, or where CI is red/uncertain → leave the PR **open** for the owner, summarize in the morning report. Never `--admin`-merge past a red required check overnight.
- NEVER push to `origin/main` directly. NEVER delete anything with content (archive instead). NEVER touch the clones' merges, the Obsidian vault move, or the Constitution text (all reserved for the owner).

---

## STAGE 0 — Boot (~5 min)
Read, in order: `memory/atlas/ECOSYSTEM-PILLARS.md` (the map), `memory/atlas/master-prompt.md` (model + prompt rules), `memory/atlas/SESSION-HANDOFF-2026-06-09.md`, `.claude/breadcrumb.md`. Confirm `origin/main` HEAD. Reuse ONE worktree (do not create a worktree per PR — that filled the disk before).

## STAGE 1 — Land tonight's thinking (safe, ~10 min)
`memory/atlas/ECOSYSTEM-PILLARS.md` (untracked) and `memory/atlas/master-prompt.md` (modified) are uncommitted in the working copy. Commit both with `[canonical-new]` in the message (governance gate requires it for new root canon MD) → PR → merge when green.
**Done =** both files on `origin/main`.

## STAGE 2 — Repair the broken wake chain (safe, high value)
The most-executed ritual file lies. Fix it:
- `memory/atlas/wake.md` cites dead paths: a `mega-sprint-122/FINAL-REPORT.md` + `mega-sprint-122/handoffs/` directory that does not exist, and says "BRAIN.md does not exist" while `BRAIN.md` is present. Find every cited path, verify it against disk, fix or remove the dead ones.
- Three canon registries disagree and cite deleted files: `memory/atlas/CANONICAL-MAP.md`, `memory/atlas/CANONICAL-LAYERS.md`, `memory/atlas/README.md`. Rebuild **one** (`CANONICAL-MAP.md`) from actual disk state; delete or redirect the other two.
**Verify (write a tiny check):** grep every path cited in `wake.md` + the rebuilt registry and assert each exists. **Done =** 0 dead paths in the wake chain; one registry; PR green + merged.

## STAGE 3 — Close the test gap (the owner's #1 fear: "tests must run to standard")
`ci.yml` today: `Backend` job runs `pytest tests/` in `apps/api` (excellent, ~160 files). `Control Plane` job runs only a hardcoded subset (`pytest tests/test_atlas_swarm_daemon_*.py …`). These suites EXIST but run in NO job — wire them in:
- `packages/swarm/tests/` (5 files)
- `packages/atlas-core/python/tests/` (3 files)
- root `tests/` brain/daemon suites NOT in the Control-Plane subset (e.g. `test_gemma4_brain_*`, `test_openmanus_*`)
- `packages/ecosystem-compliance/` (has NO tests — note this; do not fabricate tests, just record the gap)
Approach: add the missing suites to existing jobs or add one new job in `ci.yml`. Fix import paths / install the packages as real deps if `sys.path` injection blocks collection.
**Done =** one CI run where every suite is *collected and executed*; report the pass/fail count per suite. If anything is red, leave the PR open and list the failures verbatim in the morning report — do NOT mask. This is the literal "tests exist ≡ tests run" fix.

## STAGE 4 — Investigate the clones, DO NOT merge (STOP for owner)
Read (read-only) the unmerged work and write a rescue report — do NOT merge or delete:
- `C:/Projects/VOLAURA_premerge` — 4 commits ahead of origin/main (`git log origin/main..HEAD`)
- `C:/Projects/volaura-webhook-fix` — 1 commit ahead (likely a prod webhook fix)
- `C:/Projects/VOLAURA_railway_fix` — 9 uncommitted files (likely deploy/env config)
For each: what it is, and a land/discard recommendation with reasoning.
**STOP. Done =** `memory/atlas/CLONE-RESCUE-2026-06-10.md` with a one-tap decision list for the owner. No merges, no deletes.

## STAGE 5 — Safe junk removal (reversible, via PR)
Remove only confirmed zero-content / orphaned items, via a PR (reversible):
- the ~110 vendored `claude-flow` agent directories under `.claude/agents/*` that `AGENTS-INDEX.md` itself marks "not invoked, decision pending" (keep the 15 active defs + the index)
- `packages/eslint-config` + `packages/typescript-config` (orphaned — nothing imports them; confirm with a grep first)
- committed build/scratch artifacts in the repo: `*.apk`, `tmp-*.png`, `.aider.chat.history.md`
**Verify before each removal** that nothing imports/references it. Do NOT touch the clones, the vault dirs, `freellmapi-smoke.log`, or the `ecosystem/` stub (the owner will green-light those). **Done =** PR green, tree lighter; list MB saved.

## STAGE 6 — Morning report
Write `memory/atlas/MORNING-REPORT-2026-06-10.md`: what merged (links), the Stage-3 test numbers, and the owner's one-tap decisions waiting — clone rescue (Stage 4 list), vault move to `C:/Vault`, the 3 Constitution amendment candidates, and the 2 Hermes gates. Each as a single clear action. Outcome first, evidence-cited, no hedging.

## Explicitly OUT of scope tonight (reserved)
Clone merges/deletes · Obsidian vault move (touches global CLAUDE.md paths — do with owner awake or wake breaks) · D-4 selected-answer persistence (awaiting Codex) · Hermes activation (owner's 2 gates) · Constitution text edits (owner approves each amendment) · any new product feature.
