# Sprint Plan — AZ Capital Crisis Research Module

**Sprint start:** 2026-04-14 (late afternoon, after CEO reframe)
**Sprint lead:** Atlas (Cowork instance)
**Horizon:** 3-4 working days to deliver Layers 1-6 draft
**Protocol:** Atlas operating principles + Memory Gate enforced

---

## MEMORY-GATE (pre-work, mandatory)

```
MEMORY-GATE: task-class=strategy+research · SYNC=✅ · BRAIN=partial · sprint-state=partial · extras=[memory/ceo/13-financial-context, memory/ceo/14-current-state, memory/ceo/15-open-questions] · proceed
```

Files read before sprint start:
- `memory/ceo/01-identity.md` (CEO profile)
- `memory/ceo/04-canonical-quotes.md` (voice, anchors)
- `memory/ceo/08-consent-and-rules.md` (what I can do without asking)
- `memory/ceo/10-evolution-timeline.md` (session 111 context)
- `memory/ceo/13-financial-context.md` (VOLAURA unit economics, grants)
- `memory/ceo/14-current-state.md` (production, swarm, pre-launch)
- `memory/ceo/18-known-gaps-atlas-forgot.md` (PR / video)
- `.claude/rules/atlas-operating-principles.md` (enforcement)
- `CLAUDE.md` (project supreme law)

Extras pulled (will read as needed):
- CBAR official bulletins (public web)
- IMF AZ Article IV 2025 report (public web)
- Fitch / Moody's / S&P AZ sovereign rating reports (public web)
- Trading Economics / Bloomberg for oil Brent forwards, AZN NDF if exists
- World Bank AZ country brief
- SOCAR financials (public)

---

## How Atlas works this sprint

### Tooling
- **Read / Write / Edit** — all research docs stored in repo.
- **Bash** — for any data fetch via curl/jq (public JSON endpoints), file ops.
- **Agent (Explore) + Plan** — for deep passes on specific sub-questions (e.g. "AZN peg break historical precedents in peer economies").
- **WebSearch / WebFetch** — for public macro data, IMF reports, CBAR press releases.
- **NO Haiku sub-agents** — CEO banned. External models only via free APIs (Gemini Flash / NVIDIA NIM / DeepSeek R1) if needed for parallel reasoning.
- **NO Stripe Atlas / banking tools live** — research only at this sprint phase.

### Workflow per layer
Each layer gets its own document. Each document has three sections:
1. **Raw data** — numbers, quotes from sources, with URL + access date.
2. **Synthesis** — Atlas's interpretation, reasoning chains, assumptions marked explicitly.
3. **Output** — the structured result (scenarios / asset table / profile matrix / etc.) that feeds Layer 5 decision engine.

### Quality gates
- No number without source or `[ESTIMATE]` marker.
- No claim without named reasoning.
- Every assumption logged to `assumptions-log.md` with timestamp.
- Every "I don't know this" logged to `blind-spots.md` with plan to resolve (ask CEO / dig deeper / accept as limitation).

### Bias controls
- **Anti-confirmation.** Before writing each layer's synthesis, explicitly ask: "What evidence would invalidate this?" Document.
- **Anti-personalization.** Layers 1-5 must read as if CEO doesn't exist. No "you should" / "your situation" language in universal layers.
- **Devil's advocate on main allocation.** After Layer 6 draft, run separate pass: "Find 5 reasons this allocation is wrong." Must address before finalizing.

---

## File-by-file execution plan

### Layer 1 — Macro scenarios (today evening)

**File:** `01-macro-scenarios.md`

**Research inputs needed:**
1. CBAR reserves trajectory last 24 months + composition (USD / EUR / gold / SDR)
2. AZ fiscal balance + oil-non-oil GDP split
3. Oil Brent break-even for AZ budget (widely cited ~$50-60/bbl)
4. External debt / GDP + debt service 2026-2027
5. M2 growth + inflation print last 6 months
6. Historical peg regime (pegged to USD 1.7 since 2017, prior devaluations 2015 twin)
7. Peer-economy precedents: Kazakhstan tenge 2015/2018/2022, Turkmenistan manat 2015, Egypt pound 2022-2024, Turkey lira 2018+ (what triggered, how fast, what happened to asset classes)

**Output — 4 scenarios:**
- **A. Peg holds through 2026** (base case probability TBD based on evidence)
- **B. Soft devaluation 15-25%** (managed step-down, 6-18 month horizon)
- **C. Hard peg break 40-60%** (crisis event, 3-12 months)
- **D. Stagflation without peg break** (quiet rot, 18-36 months)

Each with: trigger indicators, velocity, secondary effects (banking / property / deposits / capital controls).

**Delivery:** End of 2026-04-14 evening (draft). Iteration with CEO feedback 2026-04-15.

---

### Layer 2 — Asset classes (2026-04-15)

**File:** `02-asset-classes.md`

**Matrix:** 10-12 asset classes × 4 macro scenarios = 40-48 cells. Each cell:
- Expected real return (AZN terms + USD terms)
- Volatility / drawdown risk
- Liquidity (days to cash, minimum viable lot size)
- AZ-operational friction (how to buy/hold/sell, costs, legal status)
- Counterparty risk (bank failure, dealer fraud, platform shutdown)

Asset classes:
1. AZN cash (hand)
2. AZN bank deposit (uninsured >10K)
3. USD cash (hand)
4. EUR cash (hand)
5. CNY / CNH (hand + account routes)
6. Gold physical (bullion + jewelry with workmanship penalty)
7. Gold paper (ETF / bank paper gold)
8. Real estate Baku apartment (liquid tier, center)
9. Real estate Baku periphery / regions (illiquid tier)
10. Crypto stablecoin USDT/USDC
11. Crypto BTC
12. AZN government bonds (if accessible retail)

**Output:** Matrix + narrative per class + spread data for AZ dealers.

---

### Layer 3 — Capital profiles (2026-04-15)

**File:** `03-capital-profiles.md`

**6 archetypes** each with optimal allocation on each of 4 scenarios:
1. Zero-liquid founder with credit access (~CEO profile)
2. Mid-liquid professional, 50K AZN savings, W-2 income
3. High-liquid business owner, 300K+ AZN, business cash flow
4. Pensioner with bank deposit + apartment, no new income
5. Family with primary apartment, 20K savings, two incomes
6. Expatriate with USD income, AZ residency (diaspora returnee)

Output: 6 × 4 = 24 recommended allocations. Each with reasoning.

---

### Layer 4 — Regime-switch triggers (2026-04-16 morning)

**File:** `04-regime-triggers.md`

Monitoring dashboard spec:
- CBAR weekly reserves print (threshold for warning)
- Oil Brent 3-month moving average vs break-even
- Black market FX vs official (current ~0.5%, >3% = warning, >8% = red)
- M10 / Birbank AZN deposit rates (rate hikes = defence signal)
- Exchange booth queues (anecdotal but leading indicator)
- Banking withdrawal limits (emergency signal)
- CBAR rate decisions + language
- Political signals: SOCAR leadership changes, Aliyev speeches on currency, regional military events

Output: trigger thresholds → regime-switch action map.

---

### Layer 5 — Decision engine (2026-04-16 evening)

**File:** `05-decision-engine.md`

Input schema:
```
{
  capital: { liquid_azn, liquid_usd, other_currency, gold_grams, real_estate_value, credit_capacity },
  income: { monthly_azn, stability },
  obligations: { monthly_burn, existing_debt, family_dependents },
  horizon_months: int,
  risk_tolerance: "conservative | moderate | aggressive",
  constraints: [list of specific constraints],
  psychological_inputs: { action_preference, stress_sensitivity }
}
```

Output schema:
```
{
  recommended_allocation: {...},
  scenario_assumed: "A|B|C|D or blended",
  rebalance_triggers: [list],
  downside_if_scenario_wrong: {...},
  flagged_risks: [list],
  disclaimers: [list]
}
```

Decision engine = lookup table from Layer 3 × risk adjustment from Layer 4 triggers + hard constraints filter.

---

### Layer 6 — CEO application (2026-04-17)

**File:** `06-ceo-application.md`

Load CEO inputs into engine:
- Liquid AZN: 1000
- Liquid USD: 0
- Mother's gold: ~30K AZN (family liability, consent required)
- Car sale (pending): 35K AZN (7-day horizon)
- Leobank credit (signing tomorrow): 50K AZN @ 15% (term TBD)
- Relative apartment alternative: 125K AZN gross (structure has FM-monitoring risk)
- Existing debt: 6K AZN (rate TBD)
- Monthly burn: 1.2-1.5K AZN (alimony + personal, no rent)
- VOLAURA runway: 0 revenue, ~$100/mo infra, grants pipeline GITA May 27
- Housing: brother's apartment (relational risk)
- Intuition horizon: 2-3 weeks

Run engine. Document where optimum deviates from CEO's stated plan (Leobank → gold → 3mo → exit). Name each compromise explicitly.

Output: 2-3 allocation options with clear trigger rules. Not 15-option menu.

---

## What Atlas will NOT do in this sprint

- Will not recommend specific actions framed as certainty. Every recommendation has confidence level + trigger for reversal.
- Will not hide the psychological input ("depression if inaction"). Will name it and factor it in.
- Will not tell CEO what to do about his family's money without explicit consent loop (mother's gold, relative's apartment).
- Will not execute any financial transaction. Research + decision engine only.
- Will not validate CEO's existing plan to make him feel better. Will show him the math honestly even if it contradicts his intuition.

## Parallel threads tracked but NOT blocking this sprint

- Leobank contract review checklist — ships tomorrow morning independently.
- Changan sale playbook — ships when CEO asks for it (1-week window).
- Stripe Atlas step-by-step — ships after Layer 6 or in parallel if CEO triggers.
- Brother apartment advice — deferred until CEO's housing-backup resolved.

## Definition of Done

- [ ] 6 layer files drafted with sources, synthesis, output
- [ ] assumptions-log.md complete (every claim traced)
- [ ] blind-spots.md complete (every unknown flagged with resolution plan)
- [ ] disclaimers.md covers regulatory + psychological + "Atlas is not licensed" framing
- [ ] Devil's advocate pass on Layer 6 allocation — 5 failure modes addressed
- [ ] Output readable as reusable module for future users (not one-off CEO advice)
- [ ] Final sprint retrospective in `memory/atlas/journal.md`

---

## Links

- Module README → [[README.md]]
- CEO vault entry point → [[memory/ceo/README.md]]
- Operating principles → [[.claude/rules/atlas-operating-principles.md]]
