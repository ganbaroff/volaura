# ECOSYSTEM PILLARS — the spine the whole project runs on

> Built 2026-06-10 from a 3-agent read of disk (canon layer / code layer / C:/Projects sprawl), all facts confirmed against the filesystem. This is the map: the ~35 load-bearing files, and a justified verdict on everything else. The honest one-liner — **the project is not broken, it is buried.** Two products work; the rest is clutter, stalled experiments, and notes mixed into the code folder. Do NOT rebuild from scratch — consolidate.

## Product reality (the truth on disk vs the Constitution's "5 products")

| Product | On disk | Reality | Verdict |
|---|---|---|---|
| **VOLAURA** (assessment) | `C:/Projects/VOLAURA` monorepo, ~160 api tests, committed daily | **LIVE** | Canonical. The revenue product. |
| **MindShift** (focus PWA) | `C:/Projects/mindshift`, prod v1.0 | **LIVE** | Canonical. Second real product. |
| **Life Simulator** (agent office) | `C:/Projects/openclaw-office` | **PARKED** — stalled ~8 weeks | Prototype. Not close to done, not load-bearing. Park. |
| **ZEUS** (agent/swarm tooling) | `VOLAURA/packages/swarm` + `octogent` + `OpenManus` | **OPS LAYER, not a product** | Keep swarm (ops spine); octogent/OpenManus = parked tooling. |
| **BrandedBy** (AI twin) | **28 files INSIDE the VOLAURA monorepo** — router, schemas, 2 services + refresh worker, 5 api test files, 2 web pages, hooks + tests, CI workflow | **BUILT FEATURE** (not a separate product/repo) | Built + tested in-repo; completeness/quality NOT yet assessed. *(Corrected 2026-06-10 — see erratum.)* |

**Constitution amendment candidate #1:** replace the "5 equal products" framing with this reality ledger (LIVE / PARKED / OPS / BUILT-FEATURE / CONCEPT) so the supreme law stops implying work that doesn't exist — **and stops mislabeling work that DOES exist** (the BrandedBy erratum below is the reason this caveat was added).

> **ERRATUM — 2026-06-10:** the original BrandedBy row claimed "0 files / CONCEPT ONLY." That was wrong. Verified against `origin/main` (`737cd28`) via `git ls-tree -r origin/main | grep brandedby`: **28 files** exist inside the VOLAURA monorepo (router, schemas, 2 services + a refresh worker, 5 api test files, 2 web pages, hooks + tests, a CI workflow). Root cause of the error: the building read searched `C:/Projects/` for a BrandedBy **repo/dir** (none exists — it's not a separate product) and concluded "0 files," missing the in-monorepo feature. Lesson: classify products by searching INSIDE the monorepo, not only the workspace top-level. Completeness/quality of the BrandedBy feature is still unverified — "built + tested files exist" ≠ "shippable."

---

## LAYER 1 — Canon / governance pillars (~13 of ~200 files)

The "how the project thinks and operates" layer. ~200 files today → should collapse to these:

1. `docs/ECOSYSTEM-CONSTITUTION.md` — supreme law. PILLAR.
2. `VOLAURA/CLAUDE.md` — project entry (tight, the model for what canon should look like). PILLAR.
3. `~/.claude/CLAUDE.md` — global Atlas protocol (loads every session everywhere). PILLAR.
4. `memory/atlas/identity.md` — who Atlas is. PILLAR.
5. `memory/atlas/bootstrap.md` — portable identity seed (best-designed file in the layer). PILLAR.
6. `memory/atlas/wake.md` — wake ritual. PILLAR **but BROKEN** — cites dead paths (`mega-sprint-122/`, "BRAIN.md does not exist" while it does). Must fix, not park.
7. `memory/atlas/lessons.md` — 48 failure classes + cures. PILLAR.
8. `memory/atlas/master-prompt.md` — model-routing + prompt rules (new). PILLAR.
9. `mindshift/CLAUDE.md` — MindShift working memory. PILLAR **but bloated** (60KB; ~40-row sprint history must move to `docs/SPRINT-HISTORY.md`).
10. `mindshift/.claude/rules/guardrails.md` — 10 enforceable ADHD-safe rules. PILLAR.
11. `.claude/agents/AGENTS-INDEX.md` + the **15 active** agent defs — the real team. PILLAR-adjacent.
12. `memory/atlas/semantic/*` (10 compact knowledge files) + `atlas-debts-to-ceo.md` — keep.
13. **ONE** canon registry — today there are **three that disagree** (`CANONICAL-MAP.md`, `CANONICAL-LAYERS.md`, `README.md`, all citing deleted files). Merge into one rebuilt `CANONICAL-MAP.md`; delete the other two.

**Park to `archive/`:** `codex-loop.md` (185KB log), `wake-log.md` (133KB), `orchestrator-loop.md`, and ~40 dated one-offs (`SESSION-*`, `TELEGRAM-*`, `HANDOFF-*`, `arsenal*`). This is the bulk of the felt clutter.
**Delete as junk:** ~110 vendored `claude-flow` agent dirs (AGENTS-INDEX itself: "not invoked, decision pending"); `skills-matrix.md` stub.
**Bloat to trim:** `atlas-operating-principles.md` (45KB, always-loaded → 1-page core + appendices). Voice rules are triplicated (global CLAUDE.md + voice.md + operating-principles) — keep one.

---

## LAYER 2 — Code spine pillars (~9 across both products)

VOLAURA's chain is the entire product; treat as untouchable:

1. `apps/api/app/core/assessment/` — IRT/CAT scoring, BARS, quality-gate, aura math (~2,600 lines, densely tested). PILLAR — "this is what VOLAURA is."
2. `apps/api/app/routers/` — 31 routers, the public HTTP surface, each with endpoint tests. PILLAR.
3. `apps/api/app/services/` — LLM routing, matching, B2B, cross-product bridge. PILLAR.
4. `apps/api/app/core/reliability/` + `middleware/` + `schemas/` — integrity + data-access plumbing + contracts. Keep.
5. `apps/web/src/app/[locale]/` — Next.js App Router; the auth→assessment→dashboard user journey. PILLAR.
6. `apps/web/src/{lib/api(generated),hooks,stores,components}` — the typed contract binding web↔api. PILLAR.
7. `apps/tg-mini/` — Telegram mini-app, ops surface, CI-gated. Keep (small).
8. `packages/swarm/` — 39-agent ops swarm + the Telegram alert gate the api imports. PILLAR (ops, not product).
9. `mindshift/src/` — coherent single app, `tsc -b && vite build` gate + vitest + 21 e2e. PILLAR.

**Park:** `packages/atlas-memory` (markdown miscategorized as a code package → move to docs), `packages/remotion` (marketing tool, not in product graph), `atlas-core` TS half (unused; only the Python `voice` validator is imported).
**Delete as junk:** `packages/eslint-config` + `packages/typescript-config` — orphaned, nothing imports them.
**Repo-root cruft:** committed APKs (~22MB), `tmp-*.png`, `.aider.chat.history.md` (834KB) — scratch artifacts bloating the tree.

---

## The "tests must work to standard" answer (his Q1 / ZEUS)

The api suite is **excellent and CI-gated** (~160 pytest files: endpoints, engine, schema, data-subject-rights, data-access-rules). The gap is **fragmentation, not absence**:
- `packages/swarm/tests` (5 files) and `packages/atlas-core/python/tests` (3) run in **NO CI job** — tests exist but never execute. *This is the exact failure he fears.*
- Root `tests/` brain/daemon suite is only **partially** gated (the `gemma4_brain` and `openmanus` tests are never run).
- `packages/ecosystem-compliance` ships in the api import path with **zero tests**.

**Fix = one unified CI gate** so "tests exist" ≡ "tests run." Plus install `atlas-core`/`ecosystem-compliance` as real deps instead of `sys.path` injection. This is the concrete path to "tests to standard." (Do this work on Opus — it touches integrity code; Fable 5 safety filter blocks it.)

---

## Workspace target layout (collapse 20 dirs → 3 roots)

```
C:/Projects/   → code ONLY: VOLAURA (canonical), mindshift (canonical), _parked/ (octogent, OpenManus, openclaw-office, eventshift, vellum-code)
C:/Vault/      → all Obsidian notes: _MOC, _Schema, _Templates, memory, wuf13-knowledge-base, LEGAL…, plans, handoffs
C:/_Archive/   → VOLAURA_premerge+webhook-fix+railway_fix (after rescue), assessment_release, VOLAURA.zip (520MB), clawstack-fresh
```

## Cleanup — staged, reversible (nothing destructive without per-stage go)

- **Stage 1 — zero-risk junk delete:** 0-byte files (`Untitled.md`, `hinstall/hkill.txt`), empty `ecosystem` Obsidian stub, scratch logs (`hdone/hfinal/hpoll/hverify.txt`, `freellmapi-smoke.log`), ~110 vendored claude-flow agent dirs, orphaned `eslint-config`+`typescript-config`. Nothing to lose.
- **Stage 2 — rescue then archive the clones:** `VOLAURA_premerge` (4 commits ahead), `volaura-webhook-fix` (1 commit — likely a prod fix), `VOLAURA_railway_fix` (9 dirty files — deploy config) → land the unmerged work into canonical FIRST, then archive. `VOLAURA_assessment_release` (0 ahead) → archive/delete. `VOLAURA.zip` 520MB → off-disk archive.
- **Stage 3 — separate notes from code:** move the Obsidian vault to `C:/Vault`; rescue `vellum-assistant/docs/SESSION-HANDOFF-*.md` (cited by global CLAUDE.md) into the vault; update the paths in global CLAUDE.md so wake doesn't break.
- **Stage 4 — fix the protocol:** repair `wake.md` dead paths; collapse 3 canon registries → 1; extract MindShift sprint-history out of its CLAUDE.md; trim `atlas-operating-principles.md`.
- **Stage 5 — park experiments:** create `C:/Projects/_parked/` and move octogent, OpenManus, openclaw-office (LifeSim), eventshift, vellum-code with a one-line status each.

## Constitution amendment candidates (each needs CEO approval)
1. **Product Reality Ledger** (above) — supreme law reflects LIVE/PARKED/OPS/CONCEPT, not "5 equal products."
2. **Canon-singleton clause** — exactly one canonical registry; new root canon files require a `[canonical-new]` tag (gate already exists) AND a line in that registry.
3. **Workspace-hygiene clause** — code dir holds only git checkouts; notes live in the vault; one canonical checkout per repo (the 6-clone sprawl is what buried the owner).
