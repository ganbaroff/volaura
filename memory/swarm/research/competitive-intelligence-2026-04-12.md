# VOLAURA Competitive Intelligence Report
**Agent:** Competitor Intelligence Agent (activation run — no prior track record)
**Date:** 2026-04-12
**Method:** WebSearch, direct vendor/analyst aggregators (G2, Capterra, Pitchbook, Crunchbase, Tracxn, Latka), founder/trade press
**Scope:** Direct assessment competitors, credential platforms, CIS-region adjacencies, verified-skill graveyard
**Warning:** This report refuses to flatter VOLAURA. Read Section 8 last if you want the unvarnished version first.

---

## 1. THE MOAT HYPOTHESIS TEST

VOLAURA's implicit moat, stated by the founder:
> "Verified skills via adaptive IRT/CAT + AI open-text evaluation + AURA score that travels across the ecosystem (MindShift, Life Simulator, BrandedBy, ZEUS)."

Let me strip this into four claims and test each one.

### Claim A: "Adaptive IRT/CAT is a moat."
**Verdict: NO. It is a 3-month engineering project for any funded competitor, and SHL already ships it at enterprise scale.**

- SHL (the market leader, ~10,000 customers, 80% of FTSE 100) already runs IRT with a 2-parameter model on their Verify product. They build item banks where "each item is analyzed according to a multi-parameter system." They have been doing this since the 2000s.
- Harver, iMocha, Vervoe, HireVue all use "adaptive" scoring under marketing language — whether they use true 3PL IRT or a proprietary ML match score is mostly invisible to buyers because buyers do not read psychometric papers.
- VOLAURA's choice of a 3PL (3-parameter) IRT model with EAP scoring is technically more rigorous than SHL's 2PL Verify, but no B2B buyer in Azerbaijan will ever know or care. The founder is optimizing on an axis the customer does not measure.
- The pure-Python engine in `apps/api/app/core/assessment/engine.py` is impressive engineering but has no defensible IP. A competent contractor could rebuild it in 2 weeks using `mirt` (R) or `catR` / `py-irt`.

**What's copyable in 3 months:** the entire IRT/CAT engine.
**What's not copyable:** the calibrated item bank parameters (a, b, c values per question). Calibration requires thousands of real response patterns per item. VOLAURA has not collected enough data yet, but neither will any new entrant. This is a data moat, not an engineering moat.

### Claim B: "LLM-evaluated open-text is a moat."
**Verdict: NO. Gemini 2.5 Flash is a commodity API. Every competitor has access to the same model.**

TestGorilla, Vervoe, HireVue, iMocha all ship AI-graded free-text/video responses. Vervoe publicly states their AI grading accuracy is 71-78% — meaning even a funded Australian competitor with 6 years of training data still has a 1-in-4 error rate. VOLAURA's Gemini pipeline will land at similar numbers. Buyers have already absorbed AI grading as table stakes.

**What's copyable in 3 months:** the prompt and rubric design.
**What's not copyable:** domain-specific rubrics calibrated against real CIS/AZ labor market expectations, plus per-competency prompt tuning that survives local language nuance (AZ/RU code-switching). This is a localization moat, not an AI moat.

### Claim C: "AURA score is a moat."
**Verdict: NO. It is a branding asset, not a moat.**

An 8-competency weighted composite score is, mathematically, a dot product. Any competitor can publish their own "score" tomorrow. Credly, Accredible, and Sertifier have been doing credential-level scores for 5+ years. LinkedIn tried Skill Assessments and killed them in 2024 — meaning the world's largest professional network concluded that branded skill scores do not drive hiring behavior.

**Dangerous implication:** LinkedIn's 2024 death-of-Skill-Assessments is the single most important data point in this report. The world's most distributed HR product tried VOLAURA's exact core play (self-assessment badges on a professional profile) and walked away because "hirers indicated examples of how a candidate applied their skills is increasingly valuable." Translation: buyers want portfolios and behavior, not badges.

### Claim D: "AURA travels across the ecosystem (MindShift, Life Simulator, BrandedBy, ZEUS)."
**Verdict: YES — and this is the ONLY real moat. Protect it ruthlessly.**

No competitor in the world is building this. TestGorilla is a single-purpose B2B tool. HireVue is a video interview box. Credly issues badges. None of them have a second product where the user earns, spends, or embodies the skill score. The crystal economy + character stats + daily habits loop is genuinely novel and network-linked.

**What's copyable in 3 months:** the narrative.
**What's not copyable:** the integrated data model across 5 products and the switching cost of a user whose Life Simulator character, MindShift streak, and BrandedBy avatar are all powered by one AURA score.

### Moat summary

| Claim | Copyable? | Verdict |
|---|---|---|
| IRT/CAT adaptive engine | Yes, 3 months | Not a moat |
| LLM open-text grading | Yes, 1 month | Not a moat |
| AURA composite score | Yes, instantly | Not a moat (brand only) |
| **Ecosystem integration** | No, 2+ years | **THE ONLY MOAT** |

**Strategic implication:** stop selling "IRT adaptive assessment" on the landing page. It is the weakest claim. Sell the ecosystem — the thing no one else can copy.

---

## 2. DIRECT COMPETITOR MATRIX

| Competitor | HQ | Target | Pricing entry | Methodology | Item bank | B2B / ATS | CIS presence | AI eval | Differentiator |
|---|---|---|---|---|---|---|---|---|---|
| **SHL** (ex-CEB) | UK | Enterprise (Fortune 500) | Custom, enterprise | IRT 2PL + CAT on Verify | Massive, decades-calibrated | Deep — all major ATS | Via global enterprises only | Behavioral ML | Psychometric authority, Fortune 500 network |
| **TestGorilla** | Netherlands | SMB / scale-ups | $83–$111/mo (15 employees) | Test-library, credit-based | 350+ tests, no per-item IRT disclosure | Many ATS | None direct | Conversational AI (2 credits) | Volume, brand, $36.2M ARR, 329 FTE |
| **HireVue** | USA | Enterprise only | $35,000+/yr, up to $145k | Structured interview + game-based AI | Small (per role) | Deep enterprise ATS | None | Video AI + voice | Video interview pioneer, legal bias issues |
| **Eightfold AI** | USA | Enterprise HR | $650/mo floor, custom | Deep learning on career trajectories | N/A (graph) | SAP SuccessFactors partner | None | Talent graph AI | $410M raised, $2.1B valuation, talent intelligence |
| **iMocha** | India | Mid-market global | $400+/mo | Adaptive + role-based difficulty | "Vast" — undisclosed size | Workday, Taleo, SAP | Limited (via global MNCs) | AI grading | 15 Fortune 500 customers, India pricing leverage |
| **Codility** | Poland | Dev hiring | Custom | Task-based, no IRT | Coding-only | Major ATS | **YES — Poland = closest CIS-adjacent presence** | AI-assisted eng skills | Developer trust, $15/candidate |
| **HackerRank** | USA | Dev hiring | $165–$375/mo | Task-based, no IRT | 55+ languages | Many ATS | Weak | Plagiarism AI | Brand recall among devs |
| **Vervoe** | Australia | SMB simulation | $79/mo | Job simulations, "How/What" AI grading | Hundreds mapped | Limited | None | 71–78% accuracy (self-disclosed) | Simulation-first, SMB pricing |
| **Harver** | USA | Volume hiring (retail/BPO) | ~$5,000/mo | Behavioral + cognitive ML matching | 450+ assessments | TalentSoft, iCIMS, Taleo, Greenhouse | None | Self-learning match algo | Volume hiring vertical, ATS depth |

**Critical omission from the brief:** The CEO's brief did not mention **SHL** at all. SHL is the market leader and the only vendor with deeper psychometric rigor than VOLAURA plans to ship. If VOLAURA positions on "scientific rigor" it will lose to SHL every time an enterprise buyer has heard of them — and outside Azerbaijan, every enterprise HR buyer has. Position on ecosystem, not rigor.

---

## 3. THE CIS REGION TRUTH

**Hypothesis under test:** "There is no quality competitor in CIS."

**Verdict: Half-true. The gap is real but is narrower than the pitch deck implies, and is not defensible.**

### What actually exists in CIS
- **Yandex Practicum** — massive, but education + bootcamp, not verified assessment. Exits to Habr Career as a jobs board. They already own the "learn → get hired" funnel in Russia and among Russian-speaking CIS users.
- **Habr Career** — dominant tech jobs board in Russian-speaking CIS. Has self-reported skills, not verified. Has company profiles, salary data, user base. Can add verified assessment in one product cycle.
- **Skillbox / Netology** — education-first, certificates of completion, no verified assessment.
- **Boss.az, Jobsearch.az, eJob.az, Offer.az** — traditional job boards in Azerbaijan. No assessment, no verification, CV-based. These are the legacy players VOLAURA disrupts, but they have the mailing lists VOLAURA needs.
- **Sertifier (Turkey)** — 1,500+ customers in 80+ countries, supports Russian, $300/yr entry pricing, 8M+ credentials issued. This is the closest regional threat. They do not do assessment — only credentialing — but they already sell into Turkey/CIS/MENA and speak the languages. If Sertifier adds an assessment partner (iMocha-style), they leapfrog VOLAURA in distribution.
- **Codility (Poland)** is CIS-adjacent culturally and linguistically and serves CIS dev teams remotely.

### The real CIS gap
The gap is not "no verified assessment exists." The gap is:
1. No vendor combines AZ-localized UX + Russian-language LLM grading + cultural-fit questions calibrated for AZ/Turkic labor norms.
2. No vendor treats AZ as a primary market, so AZ buyers are second-class citizens to all of them.

**This is a language + localization moat, not a technology moat.** It is real but it decays the moment SHL or TestGorilla allocates one PM to localize.

**Evidence cited:** G2/Capterra listings of Harver, TestGorilla, HireVue, Eightfold, Vervoe show zero direct AZ market presence. Sertifier explicitly supports Russian. Habr Career is the only player with millions of Russian-speaking tech users already logged in.

**Honest statement for the deck:** "We are the first verified assessment platform built AZ-first, in a region that no global HR vendor treats as a primary market." Do not say "no competitor exists."

---

## 4. THE THREE EXISTENTIAL THREATS (ranked by kill probability in 12 months)

### Threat #1 — Habr Career adds verified assessment (40% probability)
**What they'd do:** Ship a self-hosted or iMocha-partnered assessment module on Habr Career profiles, leveraging their ~2M Russian-speaking tech user base. Instant distribution, zero CAC.
**Why probable:** They already own the hiring funnel. Adding assessment is the natural next move. The product gap is obvious from outside.
**Why it kills VOLAURA:** VOLAURA's entire B2B pitch collapses the moment a buyer can search verified-score candidates on a platform they already pay for and already trust.
**Pre-empt:** Partner with Habr Career (AURA-on-Habr) OR lock AZ-specific organizations (SOCAR, PASHA, ADA University, Azercell) under exclusive pilot contracts before Habr notices the gap.

### Threat #2 — Sertifier adds assessment via partnership (25% probability)
**What they'd do:** Wrap iMocha or a white-label assessment engine, keep their own credential rails, sell the combined product into Turkey/CIS/MENA at $300–$1,250/yr.
**Why probable:** Sertifier already has 8M+ credentials issued and customers in 80+ countries including CIS. They lack assessment; they need one move.
**Why it kills VOLAURA:** They undercut on price (CIS-friendly) and out-distribute on existing base. VOLAURA would be a new entrant versus an established credential network.
**Pre-empt:** Make AURA score exportable as a Sertifier-compatible credential (W3C Verifiable Credentials standard) — become the assessment-that-feeds-credentialing layer, not a competitor. If you can't beat them, be their input.

### Threat #3 — TestGorilla or SHL launches a Russian-language product (15% probability, higher impact)
**What they'd do:** Allocate one PM + localization budget, translate 350 tests, open a Tbilisi or Istanbul sales office.
**Why probable:** TestGorilla hit $36.2M ARR with a 329-person team — they are in the scaling-into-new-regions phase. Russian + Turkic markets are on their radar.
**Why it kills VOLAURA:** Instant credibility with any CIS enterprise that has ever read a Gartner report. Global brand beats local startup in the boardroom.
**Pre-empt:** Get 10+ AZ enterprise logos on VOLAURA within 6 months. Case studies in Russian and Azerbaijani. "TestGorilla in Russian" is a general-purpose tool; VOLAURA in AZ can be the vertical-specific one that is embedded in local ecosystem.

**Threats that are NOT existential (publicly stated by founder but overestimated):**
- LinkedIn reviving Skill Assessments. They killed it in 2024. They are not coming back.
- HireVue entering SMB. Their cost structure ($35k+/yr) cannot compress down.
- Blockchain credential platforms. Post-2022 crypto winter, the sector is graveyard territory (Section 6).

---

## 5. THE THREE REAL DIFFERENTIATORS

After stripping marketing claims, the 3 things VOLAURA actually does that no competitor does today:

### Differentiator #1 — AURA score as a cross-product currency
VOLAURA is the only platform where a verified skill score is the input to a game (Life Simulator), a habit tracker (MindShift), and a professional avatar (BrandedBy). No assessment vendor has built a second product. No game/habit product has built an assessment engine. The integration is unique.
**Strength:** Real. Defensible via data model lock-in.
**Caveat:** Only matters if the other 4 products actually ship and get users. If BrandedBy/Life Simulator languish, this differentiator dies.

### Differentiator #2 — AZ-first UX, AZ-language LLM rubrics, Turkic-cultural competency calibration
Everyone else treats AZ as a localization afterthought. VOLAURA treats it as the primary market. If this is done well (not just t() wrapping English strings) and AZ LLM rubrics are tuned for local idiom, this is a real but temporary moat.
**Strength:** Real.
**Caveat:** Decays the moment one global vendor allocates budget. Use the window (18–24 months).

### Differentiator #3 — Assessment → visible game progression (crystal economy, character stats)
No competitor turns the act of being assessed into a game-loop with visible, sharable outcomes beyond a PDF badge. Users have no reason to retake a TestGorilla test. Users have a reason to retake a VOLAURA assessment: crystals, character leveling, streak integration. This is behavioral psychology applied to assessment — closer to Duolingo than SHL.
**Strength:** Real if built.
**Caveat:** If the game layer is shallow, users will feel gamed, not engaged. Execution risk is high.

**Honest note:** I searched hard for a 4th. There isn't one. Everything else — IRT, AI eval, B2B search, crystal badges — already exists somewhere. Three real differentiators is a reasonable count. More than most pre-launch startups have.

---

## 6. THE GRAVEYARD

### 6a. LinkedIn Skill Assessments (killed 2024)
The single most important case study in this report. LinkedIn — with ~1B users, unlimited distribution, trust, and already-attached resumes — launched self-assessed skill badges in 2019, ran them for 5 years, and killed them in 2024.
**Official reason:** "Hirers indicated examples of how a candidate applied their skills is increasingly valuable."
**Real reason:** Badges did not change hiring behavior because hirers trust portfolios, references, and real work samples over any score. Abstract numbers do not reduce hiring risk.
**Lesson for VOLAURA:** A score alone is not enough. Ship with portfolio artifacts, recorded open-text answers, and verified context (who witnessed this?). Otherwise VOLAURA is building LinkedIn's killed feature with fewer users.

### 6b. Blockchain credentialing startups (2022–2024 cohort)
Multiple Web3 credentialing plays died in the 2022–2023 crypto winter. Common pattern: technology-forward, buyer-absent. Employers never asked for blockchain verification — they asked for trust, which centralized vendors provided fine without a chain.
**Lesson for VOLAURA:** Do not put blockchain anywhere near the pitch. Buyers do not care about how you verify; they care that you verify. Use Postgres, ship faster.

### 6c. Mindstrong (adjacent — not skills, but "measurement as moat" failure, 2023)
Mindstrong believed passive smartphone data + clinical validation would be a moat in mental health. Raised big, failed 2023. The measurement was real but did not translate into buyer urgency.
**Lesson for VOLAURA:** "Our measurement is more scientific" is a bad moat. Buyers want outcomes (fewer bad hires), not measurement quality.

### 6d. HireVue facial analysis (buried 2021)
HireVue ran AI facial expression analysis as a core product. Shut it down in 2021 after EPIC FTC complaint, academic critique, and candidate revolt. The product survived by pivoting to structured-interview-only AI.
**Lesson for VOLAURA:** Never add any feature where an AI model makes a hiring decision based on appearance, voice, or emotion. Legal + ethical + reputational quicksand.

### 6e. Many skills-based hiring point tools (various, 2023–2024)
The TestGorilla 2024 report notes 85%+ of companies now claim skills-based hiring, but Carta data shows startup shutdowns up 237%. Many unnamed skills-testing micro-SaaS tools died in the same window. Reason: the incumbents (TestGorilla, HackerRank, iMocha) out-distributed them, not out-built them.
**Lesson for VOLAURA:** This is a distribution-bound market, not a product-bound market. Do not out-engineer — out-distribute in AZ/CIS before anyone notices.

---

## 7. THE FIVE POSITIONING LEVERS (ranked ROI ÷ effort)

### Lever #1 — Lock 3 AZ enterprise exclusive pilots in 90 days (highest ROI)
**Move:** Sign exclusive 6-month verified-assessment pilots with SOCAR, PASHA Holding, Azercell, Bank Respublika, or ADA University. Exclusivity = logo for the deck + revenue + reference + moat against Habr/TestGorilla entry.
**Effort:** 3 targeted sales conversations. No new code.
**ROI:** Existential. Every locked logo is a blocked competitor.

### Lever #2 — Ship AURA as W3C Verifiable Credential export
**Move:** Make AURA scores exportable as Sertifier-compatible or W3C VC JSON. Position VOLAURA as the *assessment layer* that feeds credential networks, not a credential competitor.
**Effort:** 2 sprints, one backend engineer.
**ROI:** Turns Sertifier from threat into distribution channel. Turns Credly from competitor into complementary partner.

### Lever #3 — Kill "IRT adaptive assessment" from the landing page, sell the ecosystem
**Move:** Rewrite volaura.com hero. Remove methodology jargon. Replace with "Your verified skills. Your game character. Your daily growth. One score across 5 products." Founder will hate this because the IRT engine was hard to build. Ship it anyway.
**Effort:** 1 copy pass + 1 design review.
**ROI:** Shifts positioning from a fight VOLAURA loses (rigor vs SHL) to a fight VOLAURA wins (ecosystem vs everyone).

### Lever #4 — Build 200-candidate case study with real organizations before B2B sell
**Move:** Run a free assessment cohort of 200 AZ professionals, publish the aggregate data (anonymous), show hiring orgs the distribution curves. "Here is what the AZ tech talent pool looks like by verified skill. You cannot get this anywhere else." That is the pitch.
**Effort:** 1 coordinator + outreach.
**ROI:** Produces a data asset competitors cannot replicate without spending 6 months. Plus real item bank calibration data.

### Lever #5 — Partner with 3 AZ universities for graduate assessment requirement
**Move:** ADA University, Baku Higher Oil School, Khazar — embed VOLAURA assessment as part of graduate placement. Graduates arrive at employers with an AURA score already attached. Creates supply-side lock-in.
**Effort:** 3 university contracts, possibly subsidized.
**ROI:** Chicken-and-egg solved from the graduate side. Employers chase graduates; graduates chase scores; scores live on VOLAURA.

---

## 8. HONEST RISK ASSESSMENT — the thing the founder does not want to hear

**The uncomfortable truth: VOLAURA's biggest competitor is not TestGorilla, SHL, or Habr Career. It is the incumbent behavior of AZ employers, who currently hire by personal network and CV review, and have zero pain around skill verification.**

TestGorilla's 2024 State of Skills-Based Hiring report cites 85% of companies using skills-based hiring — but that statistic comes from TestGorilla's customer base (selection bias: already buyers). Talk to any HR lead at SOCAR or PASHA and ask: "What is your current pain around assessing technical skill?" The honest answer is usually: "We use referrals and interviews. It works fine."

This means:
1. **VOLAURA is not entering a market with unmet urgency. It is entering a market with unmeasured latent demand.** Those are very different sales cycles. Latent-demand markets require education, not conversion.
2. **The IRT engine, the AURA score, and the ecosystem integration are all supply-side features.** None of them solve the demand-side problem (why should an AZ HR manager change their hiring process?). The first 20 B2B customers will be bought through relationships, not product.
3. **The real first competitor is an Excel spreadsheet.** If a pilot customer can say "we already track candidates manually and it's fine," VOLAURA has lost. The founder must be ready to articulate — in one sentence, in Azerbaijani — what specific dollar-value pain VOLAURA kills. Not "verified skills." A number: "VOLAURA reduces time-to-hire by X days," or "VOLAURA eliminates Y% of bad hires in role Z."

**Second uncomfortable truth:** The 5-product ecosystem is the moat but also the risk. If MindShift, Life Simulator, or BrandedBy stall, VOLAURA devolves into a single-point SaaS against SHL and TestGorilla — and loses. The cross-product data linkage has to be visible to the user before the moat exists. Right now it is an architecture diagram, not a user experience. **Until a real user sees their AURA score move their Life Simulator character, the moat is theoretical.** Until then, VOLAURA is a standalone assessment product, and standalone assessment products are a crowded knife-fight.

**Third uncomfortable truth:** LinkedIn — with every advantage — killed Skill Assessments. They concluded branded skill badges do not move hiring decisions. VOLAURA's core product is, shape-for-shape, the feature LinkedIn buried. The ecosystem-integration thesis is the only reason to believe VOLAURA will not arrive at the same conclusion in 2029. The founder should be able to answer, in one paragraph, "Why does VOLAURA survive what LinkedIn Skill Assessments did not?" If the answer is "we have better UX" or "we have IRT," it is not enough.

**The single highest-leverage action:** Stop building. Go sign 3 exclusive AZ enterprise pilots this month. Distribution and lock-in beat every technology decision in this report.

---

## Sources

- [TestGorilla Pricing 2026 — G2](https://www.g2.com/products/testgorilla/pricing)
- [TestGorilla revenue $36.2M 2025 — Latka](https://getlatka.com/companies/testgorilla.com)
- [HireVue Pricing 2026 — Pin](https://www.pin.com/blog/hirevue-pricing/)
- [HireVue bias & legal risk — LinkedIn Pulse](https://www.linkedin.com/pulse/why-hirevueai-interview-biasedand-how-fix-paul-meyer-xvbmc)
- [Eightfold AI pricing 2025 — Paraform](https://www.paraform.com/blog/eightfold-ai-pricing-2025)
- [Eightfold AI funding $410M — Tracxn](https://tracxn.com/d/companies/eightfold/__Od4V-9kHfBdB85DLrrTpQUWw8VZh_yPTJMIpXWVPMJ4)
- [iMocha pricing — GetApp](https://www.getapp.com/hr-employee-management-software/a/interview-mocha/pricing/)
- [Codility vs HackerRank vs CodeSignal 2025 — HackerRank writing](https://www.hackerrank.com/writing/codility-vs-hackerrank-vs-codesignal-2025-enterprise-comparison)
- [Best pre-employment assessment tools 2026 — Pin](https://www.pin.com/blog/pre-employment-assessment-tools/)
- [Vervoe AI grading 71-78% — Hirevire review](https://hirevire.com/articles/vervoe-reviews)
- [Harver ATS integrations](https://harver.com/integrations/)
- [Harver 450+ assessments — Hirevire](https://hirevire.com/articles/harver-reviews-alternatives)
- [Credly pricing — Certifier](https://certifier.io/blog/credly-pricing-is-credly-worth-it-in-2022)
- [Accredible vs Credly — VirtualBadge](https://www.virtualbadge.io/blog-articles/accredible-vs-credly--the-ultimate-feature-breakdown-of-2025)
- [Sertifier pricing + 80 countries](https://sertifier.com/)
- [Sertifier Turkey — Certopus blog](https://blog.certopus.com/Certifier-or-Sertifier)
- [SHL uses IRT 2PL on Verify — Assessment Training](https://www.assessment-training.com/uk/test-publishers-assessment-bureaus/ceb-shl)
- [SHL market position — GraduatesFirst](https://www.graduatesfirst.com/aptitude-tests-publishers/shl)
- [LinkedIn Skill Assessments discontinued](https://www.linkedin.com/help/linkedin/answer/a1690529)
- [Mindstrong shutdown 2023 — STAT News](https://www.statnews.com/2023/02/28/mindstrong-cerebral-mental-health-technology/)
- [Startup shutdowns up 237% — SaaStr/Carta](https://www.saastr.com/carta-startup-shutdowns-are-up-237/)
- [State of Skills-Based Hiring 2025 — TestGorilla](https://www.testgorilla.com/skills-based-hiring/state-of-skills-based-hiring-2025/)
- [Boss.az Azerbaijan leading job site](https://en.boss.az/)
- [Blockchain credentialing context — VerifyEd](https://www.verifyed.io/blog/blockchain-digital-credentials)

---
**Agent sign-off:** Competitor Intelligence Agent, first output. No flattery delivered. File stored at `memory/swarm/research/competitive-intelligence-2026-04-12.md`. Recommend CEO read Section 8 first on next session.
