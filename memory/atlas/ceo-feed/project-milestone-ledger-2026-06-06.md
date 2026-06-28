# Project Milestone Ledger — 2026-06-06

## Project thesis

VOLAURA is a verified competency platform that turns assessment, evidence, and discovery into a trustworthy talent product. The project is not "more features"; it is a credible, legally safe, and operationally honest talent system with assessment, AURA, discovery, ecosystem bridges, and future product surfaces layered on top.

## Milestone ledger

### M1 — Launch readiness / legal gate
**Status:** blocked externally  
**Why it matters:** users cannot be invited until the legal/compliance gate is explicit and owned.  
**Done:** engineering-side blocker list is mostly stale; core launch features exist.  
**Proof required:** Art. 9 memo, SADPP filing confirmation, key rotation confirmation, explicit CEO sign-off.  
**Next:** collect external facts and freeze the launch gate sheet.

### M2 — Assessment + AURA reliability
**Status:** functionally implemented, no known user-blocking code bugs found in current audit  
**Why it matters:** this is the heart of the product and the trust engine.  
**Done:** onboarding, notifications, forgot/reset auth, public stats, coaching, and P0 launch-gap tests are green.  
**Proof required:** P0 launch-gap tests, stats tests, coaching path tests, live smoke if needed.  
**Next:** keep regression coverage honest; no new feature churn until launch gate clears.

### M3 — Control plane / daemon / proof honesty
**Status:** completed as a repo-level cleanup line; no longer the main blocker  
**Why it matters:** we need a trustworthy runtime and CI-visible proof path.  
**Done:** daemon truth-lock work, portable test paths, CI coverage, and hermetic proof path.  
**Proof required:** daemon tests in CI, no local-path assumptions, no scope creep into unrelated routers.  
**Next:** stop spending sprint budget here unless a real regression appears.

### M4 — Truth-lock / docs canonicalization
**Status:** in progress  
**Why it matters:** stale docs keep creating fake blockers and fake certainty.  
**Done:** launch-gate sheet and current bug-ledger note exist.  
**Proof required:** docs that currently contradict `origin/main` are either updated or clearly marked stale.  
**Next:** align `memory/projects/volaura.md`, `AGENTS.md`, `memory/atlas/CURRENT-SPRINT.md`, `docs/ARCHITECTURE.md`, and `memory/atlas/continuity_roadmap.md` with current truth.

### M5 — MindShift integration
**Status:** product exists; integration is not the current blocking focus  
**Why it matters:** MindShift is one of the future-facing product surfaces.  
**Done:** product exists and has its own stack/state.  
**Proof required:** explicit bridge status and live event flow if we decide to move here.  
**Next:** frozen until launch gate and truth-lock are clean.

### M6 — LifeSim / BrandedBy / ZEUS boundary
**Status:** frozen or deferred by path / prior decisions  
**Why it matters:** these are future-facing product faces, not the immediate launch blocker.  
**Done:** boundary docs exist; some surfaces are archived or dormant.  
**Proof required:** explicit reactivation sign-off if any of these are revived.  
**Next:** do not pull this into the current sprint.

### M7 — Monetization / growth
**Status:** roadmap only  
**Why it matters:** it matters after the product is trustworthy and legally safe.  
**Done:** business logic exists in docs; not the current blocker.  
**Proof required:** launch-ready product plus verified traction path.  
**Next:** defer until launch gate and truth-lock are complete.

## Done / In progress / Next

**Done**
- No known user-blocking code bugs found in the current repo audit.
- The stale early readiness-plan blockers are implemented on `origin/main`.
- Launch-gate sheet exists and is appended to codex-loop.

**In progress**
- Truth-lock docs cleanup.
- External legal/compliance status collection.

**Next**
- Collect Art. 9 / SADPP / key-rotation statuses.
- Update stale docs so they stop contradicting current truth.

## Real problems

- External legal gate is still unresolved.
- Some docs still describe an outdated volunteer/provider story.
- The project still carries stale history in docs that can mislead future agents.

## Real strengths

- Core user-facing engineering blockers from the old readiness plan are already implemented.
- The P0 bug ledger is green.
- Coaching, stats, onboarding, notifications, and auth recovery are present on `origin/main`.
- The repo now has a clearer distinction between code proof and external launch proof.

## Gold-plating risks

- Expanding back into daemon/code before launch gate facts are known.
- Chasing new architecture before truth-lock docs are fixed.
- Treating stale planning documents as current project state.

## Recommended next step

Keep users blocked. Collect the legal/status facts, then finish truth-lock docs before any new feature sprint.

