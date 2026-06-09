# Cost of Technical Errors + Debt Plan + Parallel Directions — 2026-06-09

**Author:** Claude-instance for Atlas (Opus 4.8 1M). **Authority:** CEO Yusif.
**Origin:** CEO 2026-06-09 «если технически есть ошибки то какова цена? не должно быть фейков. по долгам сделай план и продолжай пахать, бери несколько эффективных направлений.»
**Principle this serves:** founding principle #1 (`memory/ceo/02-vision.md` / project_history): «Honesty before growth. Живые данные, а не захардкоденный контент. No fake counts, no fake badges. Every number real.»

---

## Part 1 — Is the AURA score a fake? (verified by reading the engine)

**Verdict: the engine is REAL. Not a fake.**

- `apps/api/app/core/assessment/engine.py` + `README.md`: 3PL IRT model `P = c + (1-c)/(1+exp(-a*(theta-b)))`, EAP ability estimation with normal prior + Gauss-Hermite quadrature, Fisher-information adaptive item selection. Cites Lord (1980), Baker & Kim (2004).
- Stop rule (verified): full energy = max 20 items, SE ≤ 0.3, min 5 before SE-stop; mid = 12 / 0.4 / 4; low = 5 / 0.5 / 3. A real session runs 5–20 adaptive questions.
- Item bank (verified seed migration `20260324000017`): irt_a varies 1.2–2.3, irt_b −1.3..+1.1, irt_c 0–0.15. Expert-authored, varied, zero lazy 1.0/0.0/0.0 defaults.

**Correction of my own prior-turn misreport:** I implied the assessment «stops at 1 question» — that was WRONG. My test harness called `/complete` manually after 1 answer (`stop_reason: manual_complete`). The engine itself does not stop at 1; it enforces min-5-before-SE-stop and max-20. I overstated a bug. Logged so the next instance doesn't inherit the false claim.

**The one true validity gap (CEO already knows):** params are expert-set priors, not empirically calibrated on a live respondent sample. Calibration-on-live is what makes it standards-grade. That is a maturity stage, not a fake — legitimate cold-start.

## Part 2 — The two REAL technical defects and their cost

### D-1 — `/complete` has no MIN_ITEMS integrity gate (severity: MEDIUM)
**What:** `POST /api/assessment/complete/{session_id}` accepted a session with `questions_answered: 1` and returned `competency_score: 35.9`, `aura_updated: true`, `badge_tier: none`, `crystals_earned: 50`, and the result is publicly verifiable via `/verify`.
**Cost:** violates «no fake badges» — a 1-answer score becomes a real, verifiable AURA signal. Plus a crystal-farm vector (50 crystals per forced 1-answer complete). Not catastrophic (score was low, badge none), but it is exactly the «fake» class CEO forbids.
**Fix:** `/complete` must reject or mark provisional when `questions_answered < min_before_se` for the session's energy mode. Score from < min items must not be AURA-updating or crystal-earning. ~1 file, guard + test.

### D-2 — GDPR erasure blocked by FK (severity: HIGH, launch-relevant)
**What:** deleting a user returns HTTP 500 — FK `automated_decision_log_user_id_fkey`. The append-only Art. 22 automated-decision audit log blocks user deletion.
**Cost:** cannot honor GDPR Art. 17 «right to erasure». The `gdpr-delete` edge function hits the same wall. This is a compliance defect in the exact family as the external launch blocker (Art. 9/22 legal track M3). Legal exposure if an EU user requests deletion and the system 500s.
**Fix:** `gdpr-delete` must ANONYMIZE the `automated_decision_log.user_id` (null/tombstone) rather than hard-delete — Art. 22 requires retaining the decision record, Art. 17 requires removing PII linkage. Anonymize satisfies both. ~1 edge function + migration + test.

**Price summary:** the expensive fear (engine is fake) is FALSE — relief. The two real defects are bounded and fixable; D-2 is the one with legal teeth and should land before any real EU user.

## Part 3 — Debt plan

Standing ledger (`memory/atlas/atlas-debts-to-ceo.md`):
- **460 AZN** = DEBT-001 (230, 83b duplicate DHL) + DEBT-002 (230, W-7 separate DHL). Status `credited-pending`.
- **$7.25 USD** Cerebras burn (DEBT-004, pending formalization).
- **5 soft credits**: DEBT-003 narrative-fabrication + sprint-drift + 3 disciplinary marks (2026-05-24).
- **+1 this session**: Class 45 dribble repeated (CEO flagged twice). Honest new disciplinary soft-mark. Not auto-written to ledger — CEO confirms.

**Closure mechanism (per Constitution 20% net dev share):** money debts are NOT cash-owed-now — they offset against the FIRST revenue line item ≥230 AZN routed to the Atlas dev share. Sequential: DEBT-001 → DEBT-002. Atlas-instances NEVER auto-close; CEO sets `closed-*`.

**Plan to actually reduce debt:**
1. **Money debts close on first revenue** — so the fastest debt-closure path IS shipping the product to paying B2B (roadmap M2/M4). Debt reduction = revenue, not apology.
2. **$7.25 Cerebras** — structurally prevented from recurring (spend-cap hook + Cerebras removed from chains/arsenal). Formalize as DEBT-004 only on CEO word.
3. **Soft/behavioral** — reduced by mechanism not willpower: the cron-loop that drove my dribble is KILLED (this session). Standing rule going forward: execute-then-report, never plan-as-deliverable when CEO said go.
4. **No new money debt this session.**

## Part 4 — Parallel directions (pick + grind), each with proof artifact

| Dir | Work | Proof artifact | CEO dep |
|-----|------|----------------|---------|
| **1** | Fix D-2 gdpr-delete (anonymize automated_decision_log) | test: create user → assessment → gdpr-delete → user gone + decision-log row anonymized not deleted | L (Atlas) |
| **2** | Fix D-1 complete min-items gate | test: force /complete at 1 answer → rejected/provisional, no AURA update, no crystals | L (Atlas) |
| **3** | freellmapi → GCP VM deploy (efficiency path) | `curl http://VM:PORT/health` 200 from VM + keys wired via dashboard | M (CEO: provider signups for volume) |
| **4** | Real multi-question assessment proof (E1) | harness reads session.next_question, walks to SE-stop (5–20 items), captures real multi-item score | L (Atlas, bypass for test user) |

**Sequencing:** Dir 1 (legal teeth) + Dir 4 (prove real multi-item score) first — both are honesty/no-fakes critical. Dir 2 next (integrity). Dir 3 (VPS) in parallel — pure ops, no scoring risk.

**Scope guard (Class 3):** D-1 and D-2 touch scoring/compliance code → consult swarm/coordinator before the fix PR, not solo-slam. Dir 4 is a test harness (no product code). Dir 3 is ops.

## Part 5 — Boundaries
- No Anthropic in swarm fan-out (Article 0). No Cerebras (Class 42).
- Secret ops use documented `ATLAS_SECRET_GUARD_DRY_RUN=1` bypass, output filtered, keys only to own infra.
- No auto-close of debt ledger. No 460 footer in CEO chat unless asked (this doc is the answer he asked for).
- No fake data, no placeholder scores shipped to real users (principle #1).

## Cross-references
- `memory/ceo/02-vision.md` principle #1 (no fakes).
- `apps/api/app/core/assessment/engine.py` + `README.md` (real IRT).
- `memory/atlas/atlas-debts-to-ceo.md` (ledger).
- `memory/atlas/ceo-feed/efficient-path-and-test-plan-2026-06-09.md` (PR #116 — test taxonomy; D-1/D-2 fold into it).
- `memory/atlas/ceo-feed/roadmap-2026-06-09.md` (merged #114 — M2/M4 revenue = debt closure).
- `memory/atlas/ceo-feed/hermes-pilot-2026-06-09.md` (PR #115).
