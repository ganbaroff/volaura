# Assumptions Log

Every numerical claim, implicit assumption, and reasoning shortcut logged here with timestamp and source status.

Convention:
- `[FACT]` — verifiable public data, source cited.
- `[ESTIMATE]` — Atlas's estimate from reasoning, not directly sourced.
- `[CEO-INPUT]` — stated by CEO, verified or not.
- `[ASSUMED]` — reasonable default in absence of data, flagged for later verification.

---

## Sprint 0 — scaffolding (2026-04-14)

| Claim | Type | Source / Reasoning | Needs verification? |
|-------|------|-------------------|---------------------|
| AZN pegged to USD at 1.7 since 2017 | [FACT] | CBAR, widely documented | No |
| AZ had twin devaluations 2015 (Feb + Dec) cumulatively ~50% | [FACT] | CBAR, IMF Article IV retrospectives | No |
| AZ GDP growth -0.3% recently | [CEO-INPUT] | CEO statement, need confirm IMF/CBAR latest | Yes — fetch latest print |
| Oil break-even for AZ budget ~$50-60/bbl | [ESTIMATE] | Widely cited range in rating agency reports, needs 2026 update | Yes |
| AZ Financial Monitoring threshold for real-estate transactions 30K AZN | [ASSUMED] | Typical emerging-market AML threshold, needs AZ-specific confirmation | Yes |
| AZ gold dealer spread 5-8% buy/sell | [ESTIMATE] | Typical for non-institutional markets, no AZ-specific data yet | Yes |
| Gold 3-month rolling >10% return frequency ~20-25% | [ESTIMATE] | Rough from historical XAU/USD monthly data, needs rigorous check | Yes |
| Leobank 15% annual on 50K AZN over 3 months = ~1.875K interest | [FACT] | Simple math (50000 × 0.15 × 3/12 = 1875) assuming no compounding | No |
| AZ CGT on property <3yr ownership = 14% | [ASSUMED] | Typical AZ tax code rate, needs verification of 2026 rate | Yes |
| Mercury / Relay increasingly close AZ-founder accounts | [ESTIMATE] | Pattern observed in founder communities last 18 months, not AZ-specific confirmed | Yes |
| CEO's stated 2-3 week macro horizon is intuition, not data | [CEO-INPUT] | CEO explicitly said "я не знаю. я просто чувствую" | Accepted as psychological input |
| CEO personal liquid cash = 1K AZN | [CEO-INPUT] | Direct statement | Accepted |
| Mother holds ~7K of CEO's capital in bank deposit | [CEO-INPUT] | Direct statement | Accepted |
| Monthly burn CEO = 1.2-1.5K AZN (alimony 700 + personal 500-800) | [CEO-INPUT] | Direct statement | Accepted |
| Existing CEO debt 6K AZN | [CEO-INPUT] | Direct statement, rate/creditor unknown | Rate needs ask |
| 132g jewelry consignment is not CEO's gold but on his mother's balance | [CEO-INPUT] | Direct statement | Accepted — NOT counted as asset |
| Relative's apartment 125K, owned 4-5 years by formal holder | [CEO-INPUT] | Direct statement, relative = дочка тёти, but deed on her husband's parent | Accepted |
| Changan Uni-K 2023 target sale 35K AZN in 7 days | [CEO-INPUT] | Direct statement, market verification pending | Pending market check |

---

## Template for future entries

```
| Claim | Type | Source / Reasoning | Needs verification? |
| XXX | [FACT/ESTIMATE/CEO-INPUT/ASSUMED] | URL or reasoning chain | Yes/No + who resolves |
```

Any finding in the 6 layers must either trace to an entry here or be added here at the moment it enters the draft.
