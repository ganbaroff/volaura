# IRT/CAT library research — raw notes — 2026-04-15

Researcher: Atlas (Claude Opus 4.6 1M). Source: WebSearch (~14 queries, Apr 2026).
Scope: Python 3.11+ libraries for IRT/CAT relevant to replacing or augmenting
`apps/api/app/core/assessment/engine.py` (pure-Python 3PL + EAP + MFI + ε-greedy).

## Library inventory (Python)

### 1. catsim — CAT orchestration
- GitHub: https://github.com/douglasrizzo/catsim
- PyPI: https://pypi.org/project/catsim/ (latest 0.17.3 or 0.20.0 in docs; conflicting)
- Author: Douglas De Rizzo Meneghetti; academic origin, arXiv:1707.03012
- License: **LGPLv3** — copyleft; dynamic linking OK for commercial SaaS, but
  modifications to catsim itself must be redistributed under LGPL
- Status: **Inactive per Snyk (Jul 2025)**. No PyPI release in 12+ months, low PR/issue activity, ≤10 contributors.
- Weekly downloads: ~1,527
- Python: 3.7–3.11 tested, no 3.12/3.13 signal
- Models: 1PL/2PL/3PL/4PL dichotomous logistic
- Features: Initialization, selection (MaxInfo), estimation (Numerical/EAP), stopping (MinError), simulator, exposure rate tracking (adds column 5 to item matrix). Normalization helpers.
- Calibration: **NONE** (explicitly outsourced; README recommends mirt/girth/py-irt)
- Exposure control: framework allows custom selector; no first-class SH, but researchers have wrapped one
- Content balancing: not first-class
- DIF: no
- Response-time model: no
- Ref: https://snyk.io/advisor/python/catsim ; https://douglasrizzo.com.br/catsim/

### 2. girth + girth_mcmc — calibration
- GitHub: https://github.com/eribean/girth
- Author: Ryan Sanchez (eribean); single maintainer
- License: MIT (permissive — good)
- MML for 1PL/2PL/3PL. `threepl_mml` exists.
- Bootstrap SE supported for 1PL/2PL. **Bootstrap does not support 3PL or GGUM** — gap for uncertainty quantification.
- Numba dependency removed → Colab/Pyodide friendly.
- girth_mcmc: Markov chain + VI alternative (PyPI https://pypi.org/project/girth-mcmc/)
- Known 3PL instability: requires prior on guessing; irt-parameter-estimation package (zlc reformulation) used for stability
- Ref: https://github.com/eribean/girth ; https://snyk.io/advisor/python/girth

### 3. py-irt — Bayesian (Pyro/PyTorch)
- GitHub: https://github.com/nd-ball/py-irt ; arXiv:2203.01282 ; INFORMS J Computing 35(1):5-13 (2023)
- Active: 0.6.6 Aug 2025, 0.6.5 Jan 2025, 0.6.4 Jul 2024 — healthy cadence
- Python ≥3.9,<3.12 (gap on 3.12+)
- Pyro + PyTorch, GPU-accelerated, variational inference; scales to large N
- Models: 1PL/2PL/3PL/4PL, ideal-point
- No CAT/selection/stopping — calibration only
- License: MIT
- Used in tinyBenchmarks (ICML 2024), metabench (ICLR 2025) — NLP benchmarking side of the house
- Ref: https://arxiv.org/abs/2203.01282

### 4. 17zuoye/pyirt — EM-only 2PL
- GitHub: https://github.com/17zuoye/pyirt
- Sparse-data oriented, pymongo integration. 2PL only. Niche. Low activity.

### 5. irt-parameter-estimation
- zlc reformulation for 3PL numerical stability
- Useful as a reference but small lib. Ref: https://snyk.io/advisor/python/irt-parameter-estimation

### 6. mirt (R) via rpy2 — gold-standard calibration
- GitHub: https://github.com/philchalmers/mirt — 1.46.1 (Mar 2026), very active
- Reference implementation for 3PL MML with priors/constraints on guessing
- `LBOUND` / `PRIOR` for 3PL stability
- Published benchmarks vs SAS PROC IRT (MDPI 2023)
- JSS citation: Chalmers (2012) doi:10.18637/jss.v048.i06
- **Use case:** sideload via rpy2 for offline calibration, write a/b/c back to Supabase. Not a runtime dependency.

### 7. PerFit (R) — person-fit / aberrance
- lz, lz*, Guttman, U3, OUTFITz, INFITz, ECI. Lz* (Snijders 2001) preferred when θ is estimated.
- No Python equivalent surfaced. rpy2 bridge or manual port.

### 8. difR (R) — DIF
- Mantel-Haenszel, SIBTEST, Crossing-SIBTEST, Lord's chi-square, Logistic DIF, Breslow-Day
- `difSIBTEST(data, group, type="udif"|"nudif", purify=TRUE)` — item purification built-in
- CRAN: https://cran.r-project.org/web/packages/difR/difR.pdf
- Python equivalent: NONE mature. MH can be rolled with scipy.stats.chi2_contingency + matched total-score bins. SIBTEST has no native Python impl — rpy2 or subprocess R.

### 9. van der Linden hierarchical RT model (2007) — speed-accuracy
- No Python package. R has `cirt`, `LNIRT`.
- Practical Python: PyMC/NumPyro port, or CmdStanPy with Koenig et al. 2023 tutorial Stan code.
- Our engine.py already stores `response_time_ms` and `theta_at_answer` — scaffolding present, model not.

## Industry state 2024-2026

### Duolingo English Test — BanditCAT + AutoIRT (arXiv:2410.21033, Oct 2024)
- AutoIRT: AutoML (AutoGluon.tabular + BERT embeddings + NLP features) → non-parametric grader → item-specific parametric IRT → explanatory model. Kills manual calibration.
- BanditCAT: CAT as contextual bandit. Reward = Fisher information. Thompson sampling + randomization for exposure.
- Deployed at 4–14K user scale during new item-type launches (Y/N Vocabulary, Vocabulary-in-context).
- **Gap for us:** AutoIRT needs scale (4k+ responses per item type) AND labeled features. Matches Sprint-later horizon, not now (we have 101 items, ~170 responses per our own prior research doc).

### ETS / GRE
- Public: ETS publishes IRT research (aberrance under MST, IRT vs classical equating), but **no open-source GRE engine**. Their stack is proprietary.
- Ref: https://www.ets.org/research/policy_research_reports/

### Khan Academy / NWEA MAP
- Partnership (MAP Accelerator → "Learning Paths") maps RIT scores to practice content. **Khan runs no CAT engine.** NWEA MAP's CAT, item bank, and RIT scale are proprietary.
- No open source.

### Pearson VUE, ISC2
- ISC2 migrated CC, SSCP, CCSP to CAT 2024-2025. Methods not open. Commercial tooling (ASSESS.com CATSim/FastTest) dominates.

### Magic EdTech (commercial adaptive assessment platform)
- Uses 3PL + multistage. Marketing material; no open stack.

## LLM-enhanced psychometrics — 2024/2025 state

- **Liu 2025 (BJET)**: 6 LLMs as synthetic respondents for calibration. Ensemble approximates human ability distribution, but individual LLMs have narrow proficiency. Cheap pilot for low-stakes items. https://doi.org/10.1111/bjet.13570
- **ACL 2025 (arXiv:2506.09796)**: benchmarked 18 instruction-tuned LLMs — none reliable enough to replace pilots. Fine-tuning on human response distributions is the open direction.
- **GETA (arXiv:2406.14230, Raising the Bar)**: unified CAT + IRT + AIG + LM. Jointly trains VIRT + item generator. On-the-fly item generation avoids leakage. Most relevant to VOLAURA item-generation vision.
- **IrtNet (arXiv:2510.00844)**: MoE-based IRT for LLM abilities. Orthogonal to our usage but methodology worth tracking.
- **MetaBench (ICLR 2025)**: IRT-based benchmark distillation. Shows IRT has a second life in LLM eval.
- **Gorgun & Bulut 2024**: instruction-tuned LLMs for automatic item-generation QC.
- **Hernandez & Nie 2022 (AI-IP)**: LLM-assisted personality scale item development.
- **NCME 2025 (AIME)**: Generative AI for common metrics in IRT. Linking functions LLM-generated difficulties → human scale.
- Review: Ye et al. 2025 arXiv:2505.08245 "LLM Psychometrics: A Systematic Review".

## Anti-gaming / person-fit / RT

- lz (Drasgow 1985), lz* (Snijders 2001). R `PerFit`.
- Group-based indices (SCI, MCI, BW) outperform lz in recent simulation studies; lz is mediocre.
- RT-based aberrance: van der Linden hierarchical; 3-parameter lognormal extension (PMC7565119).
- **Our engine already has behavioral antigaming.py (7 checks) + progressive penalty.** Literature and prior research doc confirm this is *unique and privacy-preserving vs proctoring*.

## Exposure control

- Sympson-Hetter 1985 — P(A|S) tuned by simulation; 2-stage SH (TSH) 2023 controls min AND max.
- Van der Linden 2003 alternatives — faster, more stable ceiling.
- catsim extensible selector API; no first-class SH shipped. Our ε-greedy is a poor-man's exposure cap (uniform random, not item-specific).

## DIF — Python gap

- No mature native Python library (confirmed; LinkedIn tutorial by Andrew F is the go-to).
- Practical: roll MH with scipy + statsmodels FDR; rpy2→difR for SIBTEST if needed.
- Our AZ-first user base makes DIF a P0 for any cultural-bias audit, per ecosystem Constitution.

## Migration cost summary

| Library | What it replaces in engine.py | Replace effort | Risk |
|---|---|---|---|
| catsim | selection + estimation + stopping | 2–3 days; LGPL licensing check; inactive | medium (upstream dead) |
| girth | (nothing in engine.py; adds calibration) | 1 day offline pipeline | low; 3PL SE limitation |
| py-irt | (adds Bayesian calibration) | 2 days + GPU | low; Python<3.12 |
| mirt via rpy2 | offline calibration gold-standard | 1 day script, 1 R install | low–medium (rpy2 Windows pain) |
| PerFit via rpy2 | NEW — person-fit aberrance | 1 day | low |
| difR via rpy2 | NEW — DIF audit | 1 day | low; needs ≥500 users per group |
| PyMC/Stan RT model | NEW — response-time hierarchical | 1–2 weeks | medium (calibration stability) |

Our engine.py's 358 LOC does **3PL math + EAP quadrature + MFI + ε-greedy + energy-adaptive stopping + BARS-binarization hook + RT-IRT theta snapshot**. Energy-adaptive stopping and BARS-binarization + theta_at_answer are **not in any surveyed library** — they are ours.

## Sources
- catsim: https://github.com/douglasrizzo/catsim ; https://snyk.io/advisor/python/catsim ; https://pypi.org/project/catsim/ ; https://arxiv.org/pdf/1707.03012
- girth: https://github.com/eribean/girth ; https://pypi.org/project/girth/ ; https://pypi.org/project/girth-mcmc/
- py-irt: https://github.com/nd-ball/py-irt ; https://arxiv.org/abs/2203.01282 ; https://doi.org/10.1287/ijoc.2022.1250
- mirt: https://github.com/philchalmers/mirt ; https://cran.r-project.org/web/packages/mirt/mirt.pdf ; https://www.mdpi.com/2624-8611/5/2/28
- PerFit: https://rdrr.io/cran/PerFit/man/lz.html
- difR: https://cran.r-project.org/web/packages/difR/difR.pdf
- Duolingo BanditCAT/AutoIRT: https://arxiv.org/abs/2410.21033
- van der Linden RT: https://pmc.ncbi.nlm.nih.gov/articles/PMC7565119/ ; https://bpspsychub.onlinelibrary.wiley.com/doi/full/10.1111/bmsp.12302
- LLM psychometrics: https://bera-journals.onlinelibrary.wiley.com/doi/10.1111/bjet.13570 ; https://arxiv.org/html/2506.09796 ; https://arxiv.org/html/2406.14230 ; https://arxiv.org/pdf/2510.00844 ; https://github.com/ValueByte-AI/Awesome-LLM-Psychometrics
- Sympson-Hetter / TSH: https://assess.com/sympson-hetter-item-exposure-control/ ; https://pubmed.ncbi.nlm.nih.gov/37997579/
- ETS IRT: https://www.ets.org/research/policy_research_reports/publications/report/2020/kbxx.html
- NWEA/Khan: https://www.nwea.org/news-center/press-releases/nwea-and-khan-academy-launch-map-accelerator-following-successful-introduction-of-pilot/
