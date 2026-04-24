# Swarm Gates Matrix (Policy vs Hard-Enforced)

**Date:** 2026-04-21  
**Purpose:** explicitly separate advisory policy gates from CI-enforced release blockers.

## Hard-Enforced in CI

1. **Compliance contract gate**
   - Required docs: architecture truth snapshot + contract lock.
   - Required tests: auth export + grievance human-review paths.

2. **Contract drift gate**
   - Runtime-facing examples must align with pinned contract lock document.

3. **Launch-critical hook gate**
   - Human-review frontend query/mutation tests must pass.

## Policy-Only (for now)

1. Full multi-agent precheck before every >3-file change.
2. Daily swarm self-audit narrative quality checks.
3. Non-critical style/process prompts not tied to runtime risk.

## Promotion Rule

Any policy-only gate that causes repeated incidents moves to hard-enforced CI in the next sprint.

