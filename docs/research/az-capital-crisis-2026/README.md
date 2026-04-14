# AZ Capital Crisis 2026 — Research Module

**Started:** 2026-04-14
**Owner:** Atlas (Cowork instance as CTO-hands)
**Requested by:** CEO Yusif Ganbarov, Session 111
**Type:** Deep research + decision engine + personal application
**Status:** Sprint 0 — scaffolding + macro layer started

---

## What this module is

A reusable decision-engine for "emerging-market capital crisis under currency peg stress." Built universal-first (macro + asset classes + profiles), then applied to CEO's specific situation. Designed so future users (CEO's family, team, friends, or product users) can pass their inputs through the same layers and get a calibrated answer.

**Not** one-off financial advice. **Is** a repeatable analytical framework with documented assumptions, sources, and sensitivity analysis.

## Why this exists

CEO is in Azerbaijan. He feels a macro crisis approaching in 2-3 weeks (intuition, not data). Has assemblable capital ~100K AZN across: Leobank 50K credit (signing tomorrow), Changan car sale 35K, mother's gold ~30K, relative's apartment structure 125K (alternative). Personal cash 1K. Monthly burn 1.2-1.5K. Existing debt 6K. VOLAURA zero revenue. Wants to know: real estate vs gold vs USD vs EUR vs CNY vs mix.

Previous pass (started same session) went directly into his context. CEO stopped and reframed: *"не задрачивайся именно моим контекстом. сначала общая ситуация. потом моя. потом это модуль для любых инпутов."* Correct call — removes bias, produces reusable tool.

## Architecture (6 layers)

| Layer | What | Universal or Personal | ETA |
|-------|------|----------------------|-----|
| 1 | AZ macro scenarios (peg / oil / reserves / M2 / external debt) — 4 scenarios with probabilities and trigger indicators | Universal | 2026-04-14 evening |
| 2 | Asset classes in AZ (real estate, gold physical/paper/ETF, AZN/USD/EUR/CNY/CNH, crypto USDT/USDC, AZN bonds, deposits) — per each: expected return, volatility, liquidity, AZ-operational risk, spreads — on each macro scenario | Universal | 2026-04-15 |
| 3 | Capital profiles (5-6 archetypes: zero-liquid + credit leverage / mid-liquid / high-liquid / pensioner / family-with-apartment / expatriate-with-USD) — optimal allocation per profile per scenario | Universal | 2026-04-15 |
| 4 | Red flags and regime-switch triggers (CBAR reserves, oil, black vs official FX, exchange booth queues, banking withdrawal limits, political signals, Caspian geopolitics) | Universal | 2026-04-16 |
| 5 | Decision engine (input: profile + horizon + constraints → output: allocation + trigger-based rebalance rules) | Universal | 2026-04-16 |
| 6 | Application to CEO's specific case (his 100K + constraints + family liabilities + VOLAURA runway + depression-if-inaction psychological input) | Personal | 2026-04-17 |

## Files in this module

```
docs/research/az-capital-crisis-2026/
├── README.md                          (this file — module overview)
├── 00-sprint-plan.md                  (what Atlas does, how, when, which tools)
├── 01-macro-scenarios.md              (Layer 1 — AZ 4 scenarios)
├── 01-sources.md                      (Layer 1 — raw source extracts, CBAR / IMF / Fitch)
├── 02-asset-classes.md                (Layer 2 — per-asset analysis)
├── 03-capital-profiles.md             (Layer 3 — archetypes)
├── 04-regime-triggers.md              (Layer 4 — monitoring indicators)
├── 05-decision-engine.md              (Layer 5 — input/output spec)
├── 06-ceo-application.md              (Layer 6 — Yusif's kase)
├── blind-spots.md                     (what Atlas doesn't know, needs from CEO or local intel)
├── assumptions-log.md                 (every number and claim traced to source or marked speculative)
└── disclaimers.md                     (what this is and is not — psychological + regulatory framing)
```

## Operating principles in this sprint

1. **Universal first, personal second.** Bias prevention.
2. **Every number sourced or marked as estimate.** No vibes-math.
3. **Assumptions log continuously updated.** Future-me can audit.
4. **Blind-spots explicit.** What Atlas can't see → flagged for CEO/local intel input.
5. **CEO's psychological input named, not hidden.** "Depression if inaction" is a real input to the model.
6. **Compress not expand.** CEO is cognitively loaded. Output = 2-3 options with clear trigger rules, not 15-option menu.
7. **Time-asymmetry modelled.** Cost of being early is real. Probability distribution over timing, not point prediction.

## Parallel threads (not in this module but tracked)

- **Leobank contract review checklist** — drafted tomorrow morning before CEO's signing.
- **Changan sale playbook** — posting strategy (Turbo.az, Tap.az, Instagram auto-bloggers), pricing, photos, inspection talking points. 1-week urgency.
- **Stripe Atlas step-by-step for AZ founder** — US phone workaround (MySudo / Ultra Mobile eSIM), virtual US address (iPostal1), EIN without SSN (Form SS-4 fax), Mercury alternatives (Relay, Wise Business), longer-term risk of AZ-jurisdiction account closure.
- **Brother apartment sale advice** — deferred (relational risk unresolved, housing-backup needed first).

## Next step

Create `00-sprint-plan.md` with file-by-file execution plan. Then start Layer 1 macro scenarios with CBAR last bulletin + oil forwards + IMF Article IV latest.

---

## Links

- CEO vault (context) → [[memory/ceo/README.md]]
- CEO financial context → [[memory/ceo/13-financial-context.md]]
- Ecosystem constitution → [[docs/ECOSYSTEM-CONSTITUTION.md]]
- Atlas operating principles → [[.claude/rules/atlas-operating-principles.md]]

## Backlinks

- Atlas journal → `memory/atlas/journal.md` (sprint-start entry)
- Sprint state → `memory/context/sprint-state.md`
