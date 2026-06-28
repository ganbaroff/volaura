# Codex Next Sprint Queue — 2026-06-06

## Source

Atlas handoff pasted by CEO on 2026-06-06.

This file records claims to verify next. It is not a proof ledger.

## Key claims to verify

1. `PR #103` is not merge-ready unless daemon proof is CI-real:
   - `tests/test_atlas_swarm_daemon_lock.py` may have hardcoded `C:/Projects/VOLAURA/...`
   - `.github/workflows/ci.yml` may run `apps/api/tests/` but not repo-root `tests/`
   - required fix: repo-relative daemon path + explicit repo-root daemon test CI step

2. Launch blocker remains legal/compliance, not known P0 code bugs:
   - Art. 9 memo
   - SADPP filing
   - vendor DPA / voice / ASR external status

3. B2B GTM wedge may not exist in code:
   - CEO offer: resume / CV / experience based personalized assessment
   - possible reality: `assessment-generator` is internal-only question-bank tooling, not per-user resume-based testing
   - verify endpoints, DB columns, docs, and tests before deciding build vs reposition

4. Mainline docs may still drift from current canon:
   - `memory/projects/volaura.md` still says volunteer platform
   - provider chain may still mention Cerebras as locked
   - `docs/ARCHITECTURE.md` ADR index may be stale
   - `CURRENT-SPRINT.md` may be stale
   - ADR-013 / ADR-015 may be absent from main

5. Atlas self-critique to keep in view:
   - avoid absolute "no bugs" claims
   - distinguish branch/worktree truth from `origin/main`
   - read `memory/atlas/` before asking CEO for solved blockers
   - do not use "not checked" sections as a shield

## Recommended next verification order

1. Verify `PR #103` state and CI daemon coverage.
2. Verify B2B personalized-assessment wedge exists or does not exist.
3. Verify docs drift on `origin/main`.
4. Only then decide: fix PR #103, docs truth-lock, or GTM wedge sprint.

## User gate

CEO condition remains active: no users until we can say there are no known user-blocking bugs from current audit, and external/legal gate is clear.

