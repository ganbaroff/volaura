# Current Sprint — Atlas v1: Stitch Frankenstein

**Pivoted:** 2026-06-26 Baku (CEO directive: "у нас работа по АТЛАСУ!!! атлас агент рой. зашить франкенштейна.")
**Owner:** Atlas (all bodies)
**Previous sprint:** Ideal Assessment Module (2026-06-13, PAUSED — not cancelled)

## Atlas v1 = DONE bar (4 acceptance criteria)

1. **Telegram round-trip with emotion** — CEO sends message, Atlas replies using ANUS brain with PAD emotion read + Pulse tone. DONE-check: real transcript showing emotion-adapted reply.
2. **Memory across sessions** — reply reflects at least one fact from a prior session; session is written to episodes/ and survives the next body. DONE-check: episode exists + read on next wake.
3. **Provider failover** — live health probe (not key-presence) routes around a dead provider. DONE-check: kill freellmapi, message still answered by next provider.
4. **Swarm from Telegram** — CEO sends "/swarm <task>" or "рой, <task>", multiple perspectives analyze in parallel, synthesized result returned. DONE-check: real multi-perspective response in Telegram.

Everything else (VOLAURA assessment, MindShift Academy, Life Sim, BrandedBy, ZEUS gateway) is a SEPARATE product, paused for Atlas v1 purposes.

## Progress (updated 2026-06-26 14:30)

- [x] Item 1: Telegram brain + emotion — ALREADY WORKED before this sprint
- [x] Item 4: Swarm from Telegram — WIRED (commit 2e4b4ae in ANUS, /swarm + "рой" trigger)
- [ ] Item 2: Memory across sessions — write-back on shutdown ADDED (2e4b4ae), needs end-to-end test
- [ ] Item 3: Provider failover — routeModelWithFallback exists, needs live health probe (not just key-check)
- [x] Self-Wake fix: PR #153 cherry-picked to main, waiting CI checks

## Bonus stitches done (2026-06-26)

- /status command wired to Telegram (runs ATLAS control plane status.mjs)
- /models command shows available LLM providers
- Session summary write-back on SIGINT/SIGTERM (journal.md + heartbeat.md)

## Outcome

An assessment module that fully realizes the project's prescribed ideas (ADR-004, ADR-005, `docs/research/dynamic-assessment-engine/RESEARCH-2026-04-18.md`), with questions PROVEN correct + calibrated + agent-validated — not a completion number measured on sand.

## Canon (what should be — read these, don't reinvent)

- `docs/adr/ADR-004-assessment-engine.md` — 8 competencies, BARS/MCQ/open-text, IRT/CAT, anti-cheat, **option answer-key NEVER served to client (line 108)**.
- `docs/research/dynamic-assessment-engine/RESEARCH-2026-04-18.md` — the full target: AIG pipeline (role→generate→quality-gate→pre-calibrate→CAT), AutoIRT, O*NET/ESCO, §6 calibration sample sizes (3PL needs 1000+/item), §9.5 generated-item validity.
- `packages/swarm/prompt_modules/current_gaps.md` Gap 9 (eye-tracking anti-cheat), Gap 8 (role-specific generation).

## Reality map (what is — verified 2026-06-13, receipts)

- Prod DB: 123 questions (99 MCQ, 24 open), all have IRT params **in valid ranges but LLM-ESTIMATED, not empirically calibrated** (no response data; no `calibration_status`/`response_count` columns).
- `apps/api/app/core/assessment/`: 3PL IRT/CAT engine, BARS multi-LLM evaluator, quality_gate (GRS+adversarial+10-point) — BUILT.
- `scripts/question-evolution/`: 5 sprints of agent-generated, agent-voted role questions (8 roles) using a RICHER paradigm — `evaluation_rubric`/`london_delta`, AZ-institution-grounded. sprint-5 agent scores 86-96/100. **NOT loaded to prod; prod bars.py can't evaluate rubric paradigm.**
- Generation pipeline as code (item_generator / irt_calibrator / role_mapper / dynamic_assessment): **DOES NOT EXIST**.

## Checkpoints (done = receipt)

1. [x] **Proof harness built** — `scripts/validate_question_bank.py`: deterministic, no-LLM, validates both paradigms + answer-key-leak + IRT sanity, cross-checks agent voting, CI-gateable. Replaces broken 2-question stub. sprint-5: 70/70 (100%), agrees with agent voting; caught+fixed a real defect (prof-hr-s5-009 duplicate empty option). (commit this session)
2. [x] **Calibration proof built** — `scripts/calibration_proof.py`: runs 1000 synthetic candidates of known θ through the REAL CAT engine (select_next_item + submit_response + should_stop) + test-information coverage map. Proven on live prod bank (fixture `scripts/fixtures/prod-bank-2026-06-13.json`): ENGINE SOUND (ability-recovery r=0.891, RMSE=0.457, ~0 bias) but BANK TOO THIN (8/8 competencies exhaust 15-16 items before SE≤0.30; precision only θ∈[-1,1], blind at tails). Self-critiqued (was testing evo bank not prod; report didn't diagnose exhaustion-vs-bad-params) → fixed both. Exit 0 = engine sound. (commit this session)
   REMAINING: full item-parameter recovery (JMLE/AutoIRT — recover a,b,c from responses, not just θ) is a deeper follow-on; this proof covers ability-recovery + precision ceiling, which is the gate before real candidates.
3. [ ] **Wire the agent-evolved corpus** — load sprint-5 (rubric paradigm) into the bank behind the harness gate; extend bars.py to score against `evaluation_rubric` (5-level) not just keyword concepts. Done when: a rubric question scores end-to-end on prod via the runner.
4. [ ] **Generation pipeline (code)** — item_generator + LLM pre-calibration per research §5-6, every generated item must pass `validate_question_bank` before entering the bank. Done when: generate→gate→store produces a harness-passing item.
5. [ ] **Calibration-tracking columns** — add `calibration_status` / `response_count` / `generation_source` (research §8.4) so "estimated vs proven" is queryable, not invisible.

## DELETED per CEO (2026-06-13)

- "First real completion / completion-rate measured" as a goal — REMOVED. A completion number is meaningless until the questions feeding it are proven (this sprint). Dashboard stat replaced with "Калибровка вопросов: не доказана".

## Foundation already shipped (history, not this sprint's goal)

Candidate runner on v2 (PR #150), camera anti-cheat v0 (Gap 9), answer-key-leak fix (PR #151 — 22 MCQ served per-option score, violated ADR-004 line 108), anonymous pilot sessions. These make the module *reachable*; this sprint makes it *correct*.

## Read order on wake

1. This file
2. `docs/research/dynamic-assessment-engine/RESEARCH-2026-04-18.md`
3. `scripts/validate_question_bank.py` (run it: `PYTHONUTF8=1 python scripts/validate_question_bank.py`)
4. `apps/api/app/core/assessment/quality_gate.py`
