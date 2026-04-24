# VOLAURA-First Master Execution Plan

**Date:** 2026-04-23  
**Status:** Execution canon for the current CEO + Atlas hardening push.  
**Scope:** VOLAURA-first until launch-readiness. Ecosystem remains real, but core execution priority stays on VOLAURA.

---

## 1. Executive Thesis

### Core conclusion

VOLAURA does **not** need a rewrite from scratch.

The repo already contains a real product core:

- adaptive assessment
- AURA scoring
- verified profile and discovery surfaces
- organization and event-facing layers
- compliance primitives
- ecosystem bus and bridge infrastructure

The main problem is **not** lack of features.
The main problem is **control-plane weakness**:

- runtime truth and doc truth have drifted,
- critical flows were too best-effort,
- frontend state safety was inconsistent,
- gates gave less protection than the team believed,
- autonomy was stronger as narrative than as enforced execution system.

### Strategic decision

For the current execution horizon, the correct public and technical strategy is:

- **Public story:** VOLAURA-first verified talent platform
- **Technical story:** ecosystem underneath, but not all surfaces equally mature
- **Operational story:** Atlas/swarm is internal nervous system, not the product promise

### End-state we are optimizing for

By the end of the current launch hardening cycle, VOLAURA should feel like:

- a user can register, assess, recover from interruption, receive AURA, export data, contest decisions, and manage visibility without hidden failure
- the backend can recover from partial completion failures without human babysitting
- CI meaningfully blocks launch-critical regressions
- documentation no longer lies about what is current vs target
- the agent layer starts becoming evidence-driven engineering support, not symbolic governance

---

## 2. What Success Means

## Product success for this phase

VOLAURA is considered "working like clockwork" when all of the following are true:

1. Assessment is durable.
   - Refresh, device loss, transition between competencies, and final completion do not strand the user.

2. AURA is trustworthy.
   - Completion side effects are durable, retryable, auditable, and contestable.

3. Profile state is safe.
   - No silent overwrite of privacy, discoverability, or org-visibility state.

4. Compliance is operational.
   - Export, human review, retention enforcement, and decision logging are real runtime paths, not just docs.

5. Gates are honest.
   - Core regressions fail PR/CI reliably.

6. Autonomy is evidence-driven.
   - Bugs become regression assets and repair candidates, not just notes in memory.

## North Star for this execution window

**North Star:** completed, contestable, verified AURA profiles per week.

This is the right near-term company metric because it compresses:

- acquisition activation
- assessment completion
- AURA persistence
- compliance readiness
- profile trust
- hiring/discovery utility

## Supporting launch metrics

- Assessment completion success rate
- Assessment resume recovery success rate
- AURA completion side-effect recovery rate
- Settings/profile write safety incident count
- PR hard-gate pass rate on launch-critical suite
- Formal human-review submission success rate
- Export success rate

---

## 3. Preserve / Freeze / Build / Cut

## Preserve

These are real assets and should be improved, not rewritten:

- assessment engine and adaptive logic
- AURA scoring backbone
- Supabase schema foundation and RLS posture
- grievance / human review / export compliance surfaces
- character event bus
- bridge/auth integration primitives
- EventShift domain opportunity as future module
- Atlas documentation and audit discipline

## Freeze

These areas should change only when directly needed for VOLAURA launch-readiness:

- broad ecosystem narrative docs
- non-core product faces that are not launch-critical
- speculative UI expansion for BrandedBy / Life Simulator / Atlas public surfaces
- large architecture refactors that do not reduce current launch risk

## Build aggressively

- launch-critical reliability
- profile/discovery truth and safety
- durable completion / repair lanes
- contract and gate hardening
- autonomous QA and regression generation
- documentation canon for current truth

## Cut or hide

- any stub surface that pretends to be shipped
- any doc text that describes target state as implemented state
- any automation that reports confidence without producing evidence
- any test/gate that is present only for ceremony

---

## 4. Target Architecture for This Phase

The correct architecture is not "all ecosystem pieces equal." It is layered.

## Layer 1: Trust Engine

Owns:

- assessment sessions
- adaptive selection
- scoring
- anti-gaming
- AURA update
- automated decision log
- human-reviewability

Rule:

- This layer must be durable, deterministic enough to audit, and recoverable after partial failure.

## Layer 2: Identity and Privacy Plane

Owns:

- auth
- profile
- visibility flags
- discovery preferences
- org relation
- export / deletion / consent touchpoints

Rule:

- no UI may write to this layer from untrusted defaults
- all client-facing semantics for auth and errors must be consistent

## Layer 3: Opportunity Plane

Owns:

- public proof/profile
- organization search
- event and opportunity surfaces
- org-facing discovery interactions

Rule:

- this layer must consume verified state from Layers 1 and 2, never infer around it

## Layer 4: Ecosystem Bus

Owns:

- `character_events`
- bridge-safe cross-product signals
- crystal/reputation event propagation

Rule:

- this is the integration spine, not the user promise
- producers and consumers must be explicitly documented and testable

## Layer 5: Control Plane

Owns:

- hard gates
- regression suites
- health probes
- repair queues
- runtime truth docs
- contract synchronization

Rule:

- no critical path should depend on memory or discipline alone if it can be enforced in code or CI

## Layer 6: Autonomy Plane

Owns:

- incident ingestion
- failure classification
- regression generation
- safe patch lane
- audit trail for AI-driven repair work

Rule:

- autonomy must be evidence-driven and sandboxed
- auto-repair can touch tests/docs/safe copy freely
- product logic, migrations, auth, scoring, and data integrity changes always stop at review

---

## 5. What the Ecosystem Means Right Now

The ecosystem is still important, but its role during this phase is constrained.

## Current truth

- MindShift is a real adjacent product and bridge participant.
- EventShift is a real module opportunity and future revenue arm.
- BrandedBy and Life Simulator remain ecosystem-valid but are not launch-critical for VOLAURA.
- Atlas/swarm is useful as internal operating system, audit memory, and execution layer.

## Execution rule

The ecosystem may inform architecture, but it must not steal focus from VOLAURA reliability.

In practical terms:

- ecosystem work is allowed when it directly improves VOLAURA core
- ecosystem storytelling is not allowed to outrun shipped truth
- module architecture remains underneath, but launch effort goes to the core path first

---

## 6. Workstreams

## Workstream A — Assessment and AURA Reliability

Goal:

- make `assessment -> completion -> AURA -> compliance trail` non-fragile

Already improved:

- resume path fix
- multi-competency integrity
- durable completion job registry
- autonomous background repair lane

Still required:

- stable CI validation of completion repair lane
- dedicated tests for reconciler worker behavior
- tighter observability for stuck/partial jobs
- explicit blast-radius rules for duplicate-safe side effects

Exit criteria:

- completion jobs do not silently die
- replay is idempotent enough for real retry behavior
- failure states are inspectable from data, not only logs

## Workstream B — Identity / Profile / Discovery Safety

Goal:

- prevent silent corruption of user-facing truth

Already improved:

- settings page fail-safe loading and write gating
- visibility mapping fix
- some auth/error semantics normalized

Still required:

- full audit of `profile/edit` and settings-adjacent forms
- inventory of all profile writers
- normalized mutation error handling across profile/discovery surfaces
- verification that public and org-facing discovery read the same canonical fields

Exit criteria:

- no launch-critical profile surface can write false defaults
- auth expiry and permission errors remain semantically distinguishable everywhere

## Workstream C — Compliance Operations

Goal:

- make compliance real in runtime, not just present in endpoints

Already improved:

- export flow
- human review flow
- decision logging in main assessment path
- retention enforcement RPC

Still required:

- verify retention and review flows in CI/runtime
- audit dashboard/reporting for compliance operations
- single canonical documentation for current runtime obligations

Exit criteria:

- compliance claims can be defended with code, workflows, and operational evidence

## Workstream D — Gate Hardening

Goal:

- make core regressions expensive to merge

Already improved:

- CI filter honesty
- expanded hard-gate coverage
- stronger E2E intent

Still required:

- convert push-only protections into PR-required protections
- ensure E2E is authoritative, not ornamental
- add completion repair lane verification
- add workflow responsibility map so checks do not drift or duplicate

Exit criteria:

- no one can merge a launch-critical regression unnoticed

## Workstream E — Contract and Truth Sync

Goal:

- eliminate the team-cost of conflicting reality maps

Already improved:

- current-vs-target architecture note
- multiple docs synchronized

Still required:

- continue narrowing docs to runtime truth
- pin key payload contracts to actual schemas
- keep handoff, baseline, and architecture docs current after each hardening pass

Exit criteria:

- current runtime truth is locatable in one pass
- contributors are not forced to infer architecture from conflicting documents

## Workstream F — Evidence-Driven Autonomy

Goal:

- turn Atlas/swarm from documentation-heavy execution support into a real repair system

Target loop:

1. detect incident or regression
2. classify root cause area
3. generate or update regression test from real failure evidence
4. run a constrained patch lane
5. re-run targeted gates
6. produce auditable report

Inputs to autonomy:

- CI failures
- production health checks
- E2E failures
- bugfix diffs
- hot-file change frequency
- contract drift between OpenAPI and web usage
- partial completion jobs and reconciler statistics

Hard rule:

- autonomy may propose or prepare risky patches, but cannot silently merge them on protected logic

Exit criteria:

- at least one real lane exists where incidents become tests automatically

---

## 7. Phase Plan Through Launch Hardening

## Phase 1 — Truth Lock and Runtime Verification

Objective:

- ensure that the recent hardening work is real, reproducible, and CI-verifiable

Tasks:

- run stable CI verification for latest assessment and completion changes
- add tests for `assessment_completion_reconciler`
- verify cron workflow assumptions and secrets
- document workflow responsibility clearly

Deliverables:

- green CI evidence for assessment durability lane
- no ambiguity around completion repair ownership

## Phase 2 — Profile and Discovery Integrity

Objective:

- remove remaining silent-state corruption risk

Tasks:

- audit all profile write surfaces
- normalize auth/error contracts in remaining high-traffic hooks
- map canonical user visibility fields and downstream readers
- verify public proof loop and org-discovery reads

Deliverables:

- safe profile write path
- clear canonical field contract

## Phase 3 — Launch Gate Enforcement

Objective:

- make reliability enforceable before merge and before deploy

Tasks:

- promote relevant workflows to required gates
- tighten browser/API journey ownership
- remove ceremonial checks and duplicate gates
- add status mapping documentation for workflows

Deliverables:

- a coherent gate stack
- branch protection aligned with actual launch-critical flows

## Phase 4 — Autonomous QA Foundation

Objective:

- make the first real evidence-to-test loop operational

Tasks:

- define incident input schema
- add failure-to-regression generation for one lane first
- store generated regression assets in a predictable location
- connect the repair lane to targeted validation only

Deliverables:

- first autonomous regression generation lane

## Phase 5 — Launch Readiness Review

Objective:

- make a final honest decision about external readiness

Tasks:

- rerun the full launch-critical checklist
- verify compliance paths
- review docs against runtime one more time
- freeze non-essential surfaces

Deliverables:

- explicit launch recommendation: ready / not ready
- final blocker list if not ready

---

## 8. Immediate Next 10 Actions

1. Add focused tests for `assessment_completion_reconciler`.
2. Verify completion repair lane in stable CI.
3. Create a workflow responsibility map for CI/E2E/repair jobs.
4. Audit `profile/edit` and all profile-adjacent mutation flows.
5. Normalize auth/error semantics in remaining launch-critical hooks.
6. Map canonical profile/discovery visibility fields and all writers/readers.
7. Tighten E2E from "push confidence" to "merge protection."
8. Add observability/reporting for partial completion jobs and repair outcomes.
9. Start the first evidence-to-regression lane using CI failures and completion repair incidents.
10. Re-run a launch-readiness audit with updated evidence after these steps land.

---

## 9. What We Explicitly Will Not Do Right Now

- We will not rewrite the whole repo.
- We will not expand public promises around all ecosystem modules.
- We will not spend the current cycle polishing non-core faces while core reliability still has seams.
- We will not confuse “autonomous coding” with uncontrolled production mutation.
- We will not let documentation drift back into target-state fiction.

---

## 10. CEO-Level Guidance for the Current Mode

The CEO does **not** need to manage day-to-day technical sequencing right now.

What the CEO should continue doing:

- hold VOLAURA-first focus
- prevent scope drift
- decide only on irreversible questions:
  - public market claims
  - legal/compliance acceptance
  - destructive infra moves
  - money-sensitive platform choices

What Atlas should continue doing:

- operate as execution CTO
- document every hardening pass
- tighten runtime truth
- cut decorative or misleading surfaces
- escalate only real strategic forks

---

## 11. Final Strategic Verdict

The current path is correct.

Not because everything is already strong, but because the sequence is now finally rational:

- first reliability
- then enforceability
- then autonomy
- then wider ecosystem leverage

This is how VOLAURA becomes a real platform instead of a clever but fragile organism.
