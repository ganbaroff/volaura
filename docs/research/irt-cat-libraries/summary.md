# IRT/CAT library research — 2026-04-15

**Scope:** Should VOLAURA replace `apps/api/app/core/assessment/engine.py` (358 LOC: 3PL + EAP + MFI + ε-greedy + energy-adaptive stopping) with a production Python library?

## TL;DR (Doctor Strange)

**KEEP-CUSTOM for the runtime engine. ABSORB-PARTIAL via R (rpy2) for offline tooling we don't have: calibration (mirt), DIF (difR), person-fit (PerFit).**

Evidence: no Python CAT library ships our energy-adaptive stopping or BARS-binarized RT-IRT. The top candidate (catsim) is flagged **inactive** by Snyk (Jul 2025, no PyPI release in 12+ months), LGPLv3, and does not do calibration anyway. py-irt / girth do calibration only (zero CAT loop). Industry leaders (ETS, NWEA, Pearson, ISC2) publish research but release **zero open-source engines** — the proprietary-engine norm is the reason Python's CAT ecosystem is thin. Our engine.py is already textbook-correct (ref: ASSESSMENT-ARCHITECTURE-RESEARCH-2026-04-13.md §1.1). What we're actually missing is **calibration automation, DIF audit, and person-fit aberrance** — all solved by R via thin rpy2 bridges, none worth rewriting.

## Top 5 libraries

| Library | Role | License | Status | Verdict | Migration from engine.py |
|---|---|---|---|---|---|
| **catsim** | CAT orchestration | LGPLv3 | Inactive (Snyk Jul 2025) | REJECT as runtime dep | Would replace ~60% of engine.py but loses energy stopping + RT snapshot; dead upstream |
| **girth / girth_mcmc** | MML calibration (1PL/2PL/3PL) | MIT | Active | ADOPT for offline calibration | Orthogonal — adds, doesn't replace |
| **py-irt** | Bayesian IRT (Pyro) | MIT | Active (0.6.6 Aug 2025) | ADOPT later (at 5k+ users) | Orthogonal; Python <3.12 |
| **mirt (R) via rpy2** | Gold-standard 3PL MML with priors | GPL-3 (R side) | Active (1.46.1 Mar 2026) | ADOPT now for calibration | Orthogonal; rpy2 Windows setup pain |
| **difR / PerFit (R)** | DIF + person-fit | GPL | Active | ADOPT via rpy2 | NEW capability; needs ≥500/group for DIF |

Secondary: **irt-parameter-estimation** (zlc reformulation reference for 3PL stability — read code, don't depend), **17zuoye/pyirt** (2PL EM only; skip).

## Published production stacks

- **Duolingo English Test (Oct 2024, arXiv:2410.21033)** — *only* Big-Tech adaptive system with a published stack: **AutoIRT** (AutoGluon + BERT + NLP features → explanatory IRT) + **BanditCAT** (contextual bandit, Thompson sampling, Fisher info reward, exposure-control randomization). Requires 4k+ responses per item type and automated ML pipeline. **Adopt-horizon: post 5k users.**
- **ETS (GRE)** — publishes IRT research (aberrance under MST, equating); proprietary engine. Not gettable.
- **NWEA MAP + Khan Academy** — partnership maps RIT → Khan practice content; **Khan runs no CAT**; MAP's engine proprietary.
- **Pearson VUE, ISC2, Magic EdTech** — 3PL + multistage + proprietary. ASSESS.com sells CATSim/FastTest commercial tooling. Nothing open.
- **Reverse-engineering signal:** everyone is on 3PL + MFI + exposure control + content balancing + DIF + person-fit. The only novelty post-2023 is (a) AutoML calibration (Duolingo), (b) LLM item generation + VIRT (GETA, ICLR 2025), (c) Thompson sampling for selection (Duolingo).

## Gaps our engine.py has (would make us worse than peers)

1. **No automated calibration.** IRT params today are manually set. At 1k+ users we should fit a, b, c from response data. **Fix:** offline rpy2 → `mirt::mirt(data, 1, itemtype='3PL', PRIOR=(g, norm, -1.5, 3))`; write back to `questions` table. Effort: ~1 day.
2. **No DIF audit.** Constitution demands DIF for AZ-first items. **Fix:** MH in scipy now (custom), SIBTEST via rpy2→difR when ≥500 users per AZ/EN group. Effort: 1–2 days.
3. **No person-fit (lz*, Guttman).** Adversarial detection is behavioral only. Adding psychometric lz* catches aberrant response patterns independent of timing. **Fix:** port lz* formula (Drasgow 1985 + Snijders 2001) on top of our existing EAP; no new dep. Effort: 1 day.
4. **No Sympson-Hetter exposure control.** ε-greedy is a blunt instrument — uniform random, not item-specific. At 1k+ users, TSH (2023 two-stage SH) prevents both over- and under-exposure. Effort: 2–3 days.
5. **No hierarchical RT model.** We store `response_time_ms` + `theta_at_answer` but never fit van der Linden's joint speed-accuracy model. Effort: 1–2 weeks PyMC/Stan — defer to post-launch.
6. **No content balancing (shadow test).** Our item bank is small; acceptable now. Post 500 items → adopt shadow-test approach.

## Gaps libraries have that our engine.py fills (our IP worth keeping)

1. **Constitution-compliant energy-adaptive stopping** (Full/Mid/Low profiles with per-energy `max_items`, `se_threshold`, `min_before_se`). Not in catsim/girth/py-irt. Core to Law 2.
2. **BARS-binarized continuous-score hook.** `raw_score` 0.0–1.0 from LLM evaluator, binarized at 0.5 for IRT. Preserves BARS evaluation_log for auditability. Nobody ships this.
3. **RT-IRT theta snapshot** (`theta_at_answer`) captured pre-update — enables response-time mismatch detection with the *correct* theta baseline. Most libs lose this.
4. **EAP failure circuit-breaker** (eap_failures ≥ 3 → stop with `eap_degraded`). Production-grade resilience; no library guards this.
5. **Quality-gate integration** (GRS + adversarial gate + checklist in quality_gate.py — 635 LOC — orthogonal to any IRT library).
6. **Anti-gaming pipeline** (7 behavioral checks, privacy-preserving; unique vs proctoring industry per prior research doc §1.3).

These would be lost in any wholesale migration. Keep.

## LLM-enhanced psychometrics (2026 edge)

Three converging themes (none ready for us to "jump to" — all complementary):

1. **LLMs as synthetic pilot respondents** (Liu BJET 2025; ACL 2025 arXiv:2506.09796). Cheap calibration pilots before real users, but ACL 2025 concluded **no instruction-tuned LLM is yet reliable enough to replace human pilots** — fine-tuning on human response distributions is the open direction. *Defer.*
2. **LLM item generation + VIRT (GETA, ICLR 2025)** — jointly trains variational IRT + item generator; on-the-fly items avoid leakage. Most aligned with VOLAURA's item-sparsity problem. *Track; revisit when our bank >500 items.*
3. **IRT applied to LLMs** (IrtNet, metabench, tinyBenchmarks). Not our use case.

**Practical 2026 move:** use Gemini/GPT-4 to *generate candidate items* + *pre-estimate difficulty* from item features; then human-pilot + AutoIRT (Duolingo) for true calibration. This is the "AI-IP" workflow (Hernandez & Nie 2022) updated with 2025 tooling.

No reason to rewrite on LLM-native psychometrics. Keep IRT as the measurement layer; let LLMs augment item generation and scoring (we already do the latter via BARS).

## Proposed path

### Week 1 (immediate — no library migration)
- **Day 1–2:** Port lz* person-fit into `antigaming.py` (Drasgow 1985 + Snijders 2001 formulas — ~80 LOC on top of existing EAP).
- **Day 3:** Implement MH DIF audit script (`scripts/dif_audit.py`) with `scipy.stats.chi2_contingency` + total-score bins + Bonferroni. Run monthly as batch.
- **Day 4–5:** Document in `docs/research/irt-cat-libraries/summary.md` (this file) + ADR-011 "KEEP-CUSTOM engine.py + R tooling for offline".

### Month 1 (offline calibration pipeline)
- **Week 2:** `rpy2` + `mirt` offline calibration worker. Nightly run: pull responses from Supabase, fit 3PL with `PRIOR=(g, norm, -1.5, 3)` and `LBOUND=(g, 0.1)`, write back a/b/c to `questions` table with `calibrated_at` timestamp. Shadow deploy — compare manual vs mirt params, flag drift >0.3 logit.
- **Week 3:** Add `difR::difSIBTEST` via rpy2 to DIF audit script (AZ vs EN group). Gate: only runs when ≥500 completed sessions per group.
- **Week 4:** Two-stage Sympson-Hetter (TSH) replaces ε-greedy. Calibrate P(A|S) from shadow simulation on historical data.

### Month 3 (LLM-enhanced + RT model)
- **LLM item pre-calibration:** Gemini prompt generates candidate items + predicts (a, b, c) from item features; human-pilot subset; compare predictions vs mirt-fitted. Track MAE per competency. (AI-IP pattern.)
- **Van der Linden hierarchical RT** in PyMC. Use Koenig et al. 2023 Stan code as reference. Joint fit speed + accuracy. Add aberrance detection on residual RT. Ship only if person-fit coverage gap persists.
- **Revisit AutoIRT** only when we hit 5k+ users and have labeled item features at scale.

### What we will NOT do (explicitly)
- Not adopt catsim as runtime dep (inactive, LGPL copyleft, no calibration, loses our energy stopping).
- Not rewrite engine.py — it's textbook + has our IP (energy stopping, RT snapshot, EAP circuit-breaker).
- Not add py-irt until we hit scale that justifies Pyro/GPU.
- Not build proprietary DIF/person-fit in Python when R has difR/PerFit — use them via rpy2.

## Sources
See `raw.md` in same directory. Key citations:
- Duolingo BanditCAT/AutoIRT: https://arxiv.org/abs/2410.21033
- py-irt INFORMS: https://doi.org/10.1287/ijoc.2022.1250
- catsim inactive status: https://snyk.io/advisor/python/catsim
- mirt reference: https://github.com/philchalmers/mirt
- difR DIF toolkit: https://cran.r-project.org/web/packages/difR/difR.pdf
- PerFit person-fit: https://rdrr.io/cran/PerFit/man/lz.html
- GETA (LLM+CAT+IRT): https://arxiv.org/html/2406.14230
- TSH exposure control: https://pubmed.ncbi.nlm.nih.gov/37997579/
- RT-IRT tutorial (Stan): https://bpspsychub.onlinelibrary.wiley.com/doi/full/10.1111/bmsp.12302
- LLM psychometrics review: https://arxiv.org/pdf/2506.09796
- Prior internal research: `docs/research/ASSESSMENT-ARCHITECTURE-RESEARCH-2026-04-13.md`
