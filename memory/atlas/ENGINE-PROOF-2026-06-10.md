# Assessment engine — proof of function + standards reality (evidence-only)

> 2026-06-10, Atlas. CEO asked: prove the test system meets the standard our docs claim, that it works as asked; run agents that actually take the test; show how generation continues; confirm languages; check if a better path exists. This is the evidence. Method: 6 synthetic personas took the LIVE prod assessment end-to-end through the real API (`scripts/sim_assessment_personas.py`), + strange-protocol on the engine path.

## 1. Agents took the live test — results (prod `volauraapi-production`, communication competency, 2026-06-10)

| Persona | answered | score | aura_updated | gaming_flags | early /complete | mangles seen | ru served |
|---|---|---|---|---|---|---|---|
| perfect (oracle-correct) | 14 | **87.81** | yes | none | **409 (gate held)** | 0 | null ×14 |
| rapid (correct but 300ms) | 14 | 61.45 | yes | **excessive_rushing, time_clustering** | — | 0 | null |
| random | 14 | 30.46 | yes | none | — | 0 | null |
| lowenergy (energy=low) | **5** | 26.19 | yes | none | — | 0 | null |
| lang_az (AZ, random MCQ) | 14 | 17.48 | yes | none | — | 0 | null |
| worst (oracle-wrong) | 14 | **10.72** | yes | **all_identical_responses** | — | 0 | null |

**What this PROVES (each = a behavior the CEO asked to verify):**
- **Answers drive the score.** Perfect 87.81 vs worst 10.72 — a **77-point spread** on identical items. The score is not random/hardcoded; correctness flows answer→θ→AURA. (Refutes the old fear from the D-1 era.)
- **D-1 gate is live.** `perfect` hit `/complete` after 1 answer → **HTTP 409**, scoring refused until the energy-floor min items. No more 1-answer fake badge.
- **Anti-gaming works.** `rapid` (300 ms/answer) flagged `excessive_rushing`+`time_clustering`; `worst` (same option every time) flagged `all_identical_responses`. Caught live, not in theory.
- **Energy adaptation (Constitution Law 2) works.** `lowenergy` completed at **5 items** vs 14 for full energy — the low floor was honored end-to-end.
- **FIX-1 holds through the API.** Across ~75 served questions, **0 rebrand mangles** — the repair is real at the surface a candidate sees, not just in the DB.
- **AZ works end-to-end; RU does not exist.** `lang_az` completed and scored in Azerbaijani. Every served question had `question_ru = null` (×14) — confirms RC-1: a Russian user gets English. FIX-2 still required.

**Honest caveats on these numbers:**
- `lang_az` 17.48 is NOT an AZ-grading verdict — that persona answered MCQs randomly + one thin transliterated open answer. It proves AZ items are *served and gradeable end-to-end*, not that grading quality is high.
- `perfect` = 87.81 not ~100 because 3PL guessing floors + LLM/BARS open grading don't yield a clean 1.0; expected and fine.
- 6 synthetic users now exist in prod auth (`atlas-sim-*@sim.volaura.app`), undeletable until D-2 (GDPR delete 500) is fixed. Documented residue, not silent.

## 2. Does it meet the standard "prescribed in our project"? — honest answer
- **What the docs prescribe:** `ADR-004` specifies IRT 3PL + CAT + BARS + LLM-eval across 8 weighted competencies. The engine **implements that method faithfully** (verified prior turn: 3PL/EAP/MFI in `engine.py`, weights match Python↔SQL, anti-gaming live).
- **What the docs do NOT contain:** a grep across the repo for named external psychometric standards (**ITC Guidelines, AERA/APA/NCME Standards, ISO 10667, EFPA**) returns **nothing**. So "соответствие международным стандартам" is currently a **method claim, not a certified-conformance claim.** We use the same family of math as GRE/GMAT-class tests; we have **not** demonstrated conformance to a named standard, and the honest blocker is **empirical calibration** — our IRT a/b/c are expert priors, not estimated from a real respondent sample (chicken-and-egg pre-beta).
- **Recommendation:** adopt the **ITC Guidelines on Computer-Based and Internet-Delivered Testing** + **AERA/APA/NCME Standards** as the explicit yardstick, write an ADR mapping each clause to our state (met / partial / pending-calibration). Until calibrated, deck/docs say "expert-calibrated, empirical calibration in progress" — **never "certified"** (already the FIX-5 rule). This turns a vague claim into an auditable checklist.

## 3. How generation continues — ADR-017 (already on main, #140)
Two layers: calibrated CAT core = only AURA input; CV-grounded Experience Interview verifies claimed experience (PoC proven on founder CV, `scripts/poc_cv_item_generation.py`). Same multi-agent pipeline drafts standardized items into the `needs_review` queue → human approval → bank grows 117→30+/competency → enables calibration (§2). Current bank: 99 MCQ (93 servable) + 24 open-ended.

## 4. Better path? — strange-protocol (external adversary, Gate 1 → my counter-evidence, Gate 2)
External model (Groq llama-3.3-70b, `scripts/strange_gate1_engine_path.py`) attacked the plan. Its 3 failure modes + my tool-checked counter-evidence:
- **FM1 — CV-grounded signals may be biased/inaccurate.** CONCEDED-PARTIAL. Mitigation already in ADR-017 (bias-reviewer agent + human gate; signals are *separate* from AURA, never pollute the comparable score). Residual risk: real. Keep Experience Interview as a *labeled* signal, not a score.
- **FM2 — multi-agent pipeline needs heavy human review; backlog/cost.** CONCEDED. This is true and the PoC showed 2/8 weak items. Mitigation: items enter `needs_review=true` and are NOT served until approved (verified: prod fetch filters `needs_review=false`; 6 such rows exist, 0 servable). So bad items can't reach candidates — the cost is reviewer time, not validity. Acceptable.
- **FM3 — calibration needs volume the bank may never reach.** CONCEDED — this is the real ceiling (§2). It's a *volume/time* problem, identical for ANY self-built path.
- **Adversary VERDICT:** license an existing calibrated item bank instead.
- **My Gate-2 counter-evidence (why we do NOT license, this turn):** (a) **money** — licensed banks are real cash/seat; we have **$0 cash budget**, $60k *cloud* credits that don't buy IP licenses. (b) **fit** — commercial banks are English/Western-normed and generic; our wedge is **AZ/EN/AZ-CIS context + 8 bespoke competencies** — a licensed bank is neither localized nor on-construct. (c) **differentiation** — "CV-grounded verification" is the product; licensing erases it. (d) the adversary's own valid points (FM2/FM3) are about *calibration & review effort*, which licensing trades for *licensing cost + loss of fit/moat* — a worse trade for THIS company. **Verdict held: two-layer plan stays.** BUT adopt one adversary-driven change: **make ITC/AERA conformance explicit (§2)** so "standards" stops being a soft claim.
- **Gate 3 (retro trigger):** after FIX-2/FIX-3 + first 30-item calibrated batch, re-run this exact persona harness + a second external adversary on the calibrated bank. If calibration stalls (FM3 signal: <50 responses/item after real users flow), revisit licensing for a *seed* calibrated subset only.

## 5. Did I think of everything / does it fully work? — honest status
- **Works, proven live:** scoring direction, D-1 gate, anti-gaming, energy adaptation, AZ end-to-end, FIX-1 surface.
- **Does NOT fully work yet:** RU absent (FIX-2), selected-answer not stored so honest review impossible (FIX-3/D-4), bank small + uncalibrated (FIX-4/5), no named-standard conformance doc (§2), GDPR-delete 500 (D-2). Outreach stays FROZEN until FIX-1..3 + a clean RU/AZ human pass.

## Provenance
Sim harness + raw results: `scripts/sim_assessment_personas.py`, `sim_results.json` (Temp). Strange Gate 1: `scripts/strange_gate1_engine_path.py` + `strange_gate1.txt`. All scores via prod API; correctness oracle via service-role read of `questions.correct_answer`. Bank counts: live SQL `dwdgzfusjsobnixgyzjk`.
