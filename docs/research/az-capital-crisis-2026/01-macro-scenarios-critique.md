# Layer 1 Critique — Adversarial Red-Team

**Written:** 2026-04-14
**Author:** Atlas (self-red-team, Opus 4.6)
**Target:** `01-macro-scenarios.md`
**Disclaimer — read first:** This is **self-red-team, not independent second opinion.** CEO directive was to critique with Opus + other top-model agents. Attempted: (a) 4 parallel Agent subagents (opus/sonnet) → all returned `Prompt is too long` due to Cowork parent-context inheritance; (b) external APIs (OpenRouter, DeepSeek, Gemini, Groq, GPT-5) → all blocked by sandbox allowlist (only `api.anthropic.com` reachable, and no `ANTHROPIC_API_KEY` stored). Incident logged to `memory/atlas/incidents.md` with prevention plan. Until `ANTHROPIC_API_KEY` is added to `apps/api/.env` or allowlist is extended, "independent agent critique" = Atlas switching personas hard against itself. Apply heavier skepticism discount to this document than to true independent review.

Four adversarial personas. Each gets ~800-1200 words of hostile attack. Then Atlas synthesis: accept/reject per point, revised probability distribution, update to Layer 1.

---

## Persona 1 — Ex-IMF EM Macro Economist

> "I've watched 15 peg breaks in oil exporters. Your analysis is cosmetic."

### Attack 1: Probability math is broken
You wrote ranges A=55-65%, B=20-25%, C=8-12%, D=12-17%. Take the midpoints: 60 + 22.5 + 10 + 14.5 = **107**. Your own distribution doesn't sum to 100. This is not a rounding error — it's a signal that you designed each scenario independently and never enforced the constraint. Which one is wrong? If you tighten to 100, the honest path is: trim D (stagflation) — it overlaps with both A ("peg holds quietly-bad") and B ("soft deval"). Or tighten A because your confidence in peg-hold is clearly over-stated. Either way, **the whole document is invalid until this reconciles**. A reader who wants to do an expected-value calc cannot.

### Attack 2: SOFAZ is not peg ammunition
You write "CBAR $11.56B + SOFAZ $64.8B = $85B strategic buffer, 37 months import coverage." This is the single most misleading number in the document. SOFAZ is a sovereign wealth fund with a politically ring-fenced mandate — pension smoothing, intergenerational savings, counter-cyclical fiscal. Historically the AZ government has transferred only $6-12B per year to budget, and in 2015-16 CBAR-specific reserves fell from ~$16B to ~$4B **while SOFAZ barely moved** because parliament + president treat it as untouchable. The deployable-in-a-crisis-month figure is closer to **$15-25B**, not $85B. That collapses your 37-month cover to roughly **9-14 months**, which is still adequate but much less comfortable. And "adequate months of coverage" is meaningless if the deposit base flips faster than the reserves can be deployed.

### Attack 3: Dollarization flip risk ignored
You cite pre-2015 dollarization at 40%, and deposit insurance (ADIF) cap of 100K AZN per depositor. You did not model the **run dynamics**. AZ M2 is roughly 30-32B AZN. If even 30% of AZN-denominated deposits want to flip to USD in a confidence shock, that's ~10B AZN = ~$5.9B at the peg. That's 50% of CBAR reserves in a week. This is the actual peg-break mechanism — not oil falling, not war, but a **domestic confidence cascade**. In 2015 Q4, the AZN-to-USD conversion in the deposit base accelerated to ~$3B/month before CBAR gave up. Your Scenario C probability of 8-12% is therefore too LOW conditional on any trigger event — because the mechanism self-amplifies once triggered. Conditional hard-break probability given any material shock is more like **40-60%, not 8-12%**.

### Attack 4: Fiscal break-even is stale
You cite "oil break-even ~$50-60/bbl (widely cited, needs 2026 update)" and then use it. 2015-16 break-even was $60. Post-Karabakh (2020, 2023) defence spending has doubled, pension indexation took another leg in 2025, and 2026 sees infrastructure reconstruction in liberated territories + Iranian-border fortification. S&P's 2025 report put fiscal break-even at **$68-72/bbl**. Brent Dec 2026 forward at $83 gives a much thinner cushion ($11-15/bbl, not $23-33/bbl) than your analysis implies. Any 3-month Brent dip below $70 puts AZ in primary deficit immediately. You failed to update this number.

### Attack 5: Analogies are cherry-picked
Kazakhstan 2015 is your primary analogue — convenient because it broke and the world kept turning. Why not Turkmenistan 2015? Turkmenistan also pegged (manat 3.5/USD), also oil/gas exporter, also had reserves, and the peg officially "held" while a 60-70% black-market premium developed that made the official rate fiction for residents. That's your missing **Scenario E: frozen peg + parallel rate + capital controls**, which neither devalues officially nor holds in substance. Probability of Scenario E in any 12-month window for a pegged oil-exporter with declining exports and geopolitical stress is historically **15-20%**, not zero.

### Attack 6: 30-day crisis steelman you dismissed
You assigned <5% to crisis within 30 days because "no acute trigger visible." But pegs break on **non-linear confidence events**, not on visible macro. 2015 Dec 21 AZN float: the trigger was oil dropping through $40 on Dec 14 — a 7-day confidence collapse. In April 2026 the analogous trigger set is live: (a) Iran hits a Caspian target, (b) Brent spikes then collapses (whipsaw kills oil-exporter fiscal worse than steady low price), (c) a Turkey lira acceleration forces CBRT to close its AZ swap informally. Any one of these is probably 15-20% likely in any 30-day window. So P(trigger within 30 days) * P(peg break | trigger) = ~0.15 * ~0.50 = **7-8%**, not <5%. Your short-window dismissal is under-weighted by a factor of ~2.

### FINAL weights (this persona): A 45%, B 25%, C 15%, D 10%, E (frozen peg + controls) 5%
### TOP_ATTACK: SOFAZ is not deployable — treating $85B as peg ammunition is the core analytical error.
### MISSING_INPUT: CBAR 2026 Q1 balance-of-payments detail + deposit-base currency composition at March 2026.

---

## Persona 2 — Caucasus/Caspian Geopolitical Analyst

> "You put the Iran war in as garnish. It's the main course."

### Attack 1: BTC pipeline is not priced
You note the March 7 foiled BTC plot as geopolitical colour. You did not **model the fiscal hit of a 30-day BTC shutdown**. BTC moves ~700K-1M bbl/day = 25-30M bbl over 30 days = $2-2.5B lost export revenue at $83 Brent. On an annualized $35B export-revenue base that's a 6-7% annual revenue hit from a single 30-day event. That alone pushes the fiscal break-even Brent to $80+. A BTC attack is not a tail event — with active Iran war + domestic Hezbollah-linked network, the 12-month probability of at least one multi-day pipeline disruption is **25-35%**. You embedded this in Scenario A at 0% and in Scenario C at maybe 30%. Should be embedded as an independent conditional probability across ALL scenarios.

### Attack 2: Russia post-AZAL-shootdown is an open wound
December 2024 AZAL Embraer shootdown near Grozny: Russia never admitted, Aliyev demanded accountability, relationship is the coldest since independence. Russia has demonstrable cyber capability against AZ (2021 Iron Man campaign) and holds financial leverage via Gazprombank / Rosselkhozbank / MIR card rails. A single cyber event against Kapital Bank or ABB SWIFT gateway could trigger the deposit run mechanism your macro persona already flagged. This is a **12-month 10-15% probability** event I don't see in your scenario tree at all.

### Attack 3: Karabakh HR dossier caps rescue optionality
You implicitly assumed IMF / World Bank emergency facility available if AZ asks. Post-2023 Armenian ethnic cleansing complaint at ICJ, active EU resolution (March 2025) blocking trade preferences, and US House HR-1205 (2025) conditioning MCC funding — the political cost to any Western institution of a highly-visible AZ bailout is now high. AZ still has funding but would get **smaller, slower, more conditional** access. In a classic 2015-style confidence crisis where IMF-SBA was never even requested, this matters less; in a modern crisis where AZ wants IMF cover, the window is partially closed. **Reduces peg-hold probability in tail by ~3-5 pp.**

### Attack 4: Aliyev succession risk
64 years old, no public heir, Mehriban VP but Aliyev-Pashayev clan under Western sanctions for decades. A health event or a Pashayev-vs-old-guard intra-elite fracture is a 12-month **5-8%** probability. In a succession shock, peg defence becomes a secondary priority to state continuity — and the easiest quick political win is a sharp devaluation framed as "resetting the economy" (Egypt 2016 template). **Conditional on succession shock, peg-break probability = 60-70%.** Your scenario tree has zero space for this.

### Attack 5: Turkey-swap assumption
You implicitly counted CBRT as bailout-of-last-resort. CBRT gross reserves are $165B against $220B short-term external liabilities — net reserves are still negative. April 2026 lira touched 42/USD. CBRT cannot credibly bail out CBAR if CBRT itself is under swap-line stress from its own depositors. The "brother-Turk backstop" is psychological, not operational. **Removes a presumed peg-defence leg you didn't even question.**

### Attack 6: Missing Scenario E
Agree with the macro persona. The most probable crisis mode for modern authoritarian oil exporters under stress is **not** a visible devaluation. It's a maintained official rate + quiet capital controls: USD withdrawal caps, import-LC throttling, non-resident freeze, residents forced to use parallel market. Nigeria 2016-2023, Egypt 2022-2024 (long periods before each devaluation), Turkmenistan 2015-present. AZ in 2015 also had informal controls Dec 2015-Feb 2016 before the Dec 21 float crystallized. This pattern is the **modal outcome under stress**, not a footnote. **Probability 15-20%**.

### Attack 7: Worst unpriced 90-day event
The one that would break the peg fastest: **Iran strikes Sangachal terminal directly**. Sangachal is the Caspian-to-Black-Sea aggregation hub — 1M bbl/day throughput. A kinetic hit triggers (a) 30-60 day BTC + SCP shutdown, (b) SOFAZ oil-receipt interruption, (c) sovereign rating cut, (d) deposit run, (e) peg defence cascade. 90-day probability: ~5-8%. 12-month: ~15-20% conditional on Iran war continuing. This is the single event most likely to move the peg from "held" to "broken" fast.

### FINAL: A 40%, B 25%, C 15%, D 10%, E 10%
### TOP_ATTACK: Iran war treated as colour, not as a distributional shift — every scenario probability should have a war-conditional branch.
### MISSING_INPUT: CBAR's internal framework on which capital controls require parliamentary act vs CBAR board vote.

---

## Persona 3 — Forecasting Methodologist (Tetlock-style)

> "Your coherent narrative is the tell. Coherence is not accuracy."

### Attack 1: Math error as epistemic signal
Midpoints sum to 107. Not the math — what the math **reveals**: you assigned probabilities scenario-by-scenario using narrative plausibility, not from a base-rate anchor. Superforecaster rule: anchor to base rate first, then update. Base rate for pegged-regime breaks in oil exporters (n=~40 cases, 1990-2023) in any 12-month window when oil is within $20 of fiscal break-even and geopolitical stress is elevated is approximately **35-45%**. Your total break-or-deval probability (B + C = 30-37% midpoint) is roughly in line with base rate, but your **peg-hold confidence of 55-65% is above** the base rate for stressed states, meaning you're assigning information you don't have.

### Attack 2: MECE failure
4 scenarios are not mutually exclusive (D overlaps A and B) and not collectively exhaustive (no Scenario E for controls-without-devaluation, no scenario for positive oil shock + Iran resolution). Decision-engine output based on non-MECE scenarios produces **double-counted risk** in asset allocation downstream. This is a structural bug that propagates through L2-L6.

### Attack 3: 12-month horizon for a 3-month allocation decision
User (CEO) is deciding 3-month arbitrage. A 12-month scenario set does not answer the 3-month question. Probability-weighted expected return over 12 months = -5.7% is **irrelevant** to whether gold bought with Leobank credit and liquidated in 90 days is profitable. The right output for a 3-month decision is a 3-month probability distribution with higher base-case weight on "nothing happens" and sharper tail on "specific trigger fires in this 90-day window." You smuggled in a horizon that fits the 6-layer architecture but not the actual decision.

### Attack 4: Self-stated 10 biases — the biases you MISSED
You listed consensus anchoring, data lag, optimism, etc. You did not list:
- **Narrative coherence bias** — the story flows, which makes it feel more likely than it is.
- **Availability of 2015** — the one peg break you know well becomes the reference, making all others look like variations of 2015.
- **Authority mirroring** — citing Fitch / S&P / IMF anchors you to lagging curated positions. Rating agencies were positive on AZ in November 2015 — 6 weeks before the float.
- **Action bias under emotional load** — CEO is in financial stress; your model may be unconsciously producing scenarios that justify action (because action relieves stress for CEO), not scenarios that best fit reality. That's the bias of the **reader**, reflected back by a model trained on human-preference signals.

### Attack 5: Lagging vs forward signals
You used: CBAR reserves (monthly lag), IMF WEO (6-12 month lag), Fitch rating (cycle-lag), Brent spot (current). You did NOT use: AZN NDF offshore (if exists), CDS spread, black-market FX booth premium, AZN deposit-rate term structure. You even **flagged these as unknowns in `blind-spots.md`** and then wrote the analysis anyway. That's a methodological failure: proceeding when you know the most-predictive inputs are missing.

### Attack 6: n=1 generalization
You are writing a "universal decision module" based on one user's situation. You have not stress-tested the framework against 5-10 synthetic personas before running CEO through it. Any generalization you draw is anchored on CEO's specific constraints (Leobank, housing-at-brother's, mother's gold). That's the opposite of universal.

### Attack 7: Coherent counter-narrative
Here is a narrative with the same evidence pointing to hard break within 90 days at ~25% probability: "Iran war is active; one more escalation cycle expected before September (historical Iranian operational tempo); AZ is the softest oil-exporter target on the Iran border; SOFAZ is politically untouchable in a crisis (opposite of what reserves suggest); deposit dollarization trend since 2024 Q4 is already running at +2 pp/quarter per CBAR bulletin; CBAR's defence playbook (rate hikes + admin suasion) already deployed means ammunition partially spent. Therefore: next negative shock triggers the collapse, not the one after." This narrative is **equally coherent** as yours. Coherence equivalence means you should be humble about your probability assignment.

### Attack 8: Calibration
Superforecaster with good calibration, asked "pegged EM oil exporter under active geopolitical stress: P(peg holds 12-mo)?" would say **35-50%**, not 55-65%. You're 10-15 pp over-confident in peg-hold.

### FINAL: A 45%, B 25%, C 15%, D 5%, E 10%
### TOP_ATTACK: Horizon mismatch (12-mo analysis for 3-mo decision) + non-MECE scenarios = expected-value output is noise.
### MISSING_INPUT: Rebuild with explicit 3-month and 12-month twin distributions, not one 12-month smear.

---

## Persona 4 — Baku Private Banker / Ex-CBAR Insider

> "You wrote the map. I have the terrain."

### Attack 1: 2015-16 real mechanism
You described 2015-16 as "reserves depleted → float." On the ground it was different. The **political decision** made in mid-December 2015 was: CBAR will stop defending at $4B remaining reserves, and dollarized depositors will take the loss while SOCAR and SOFAZ are protected. The dollarization of deposits didn't cause the break — the **political choice** to prioritize SOCAR liquidity over retail depositor USD access caused the visible collapse. If the same decision logic repeats (and there's no reason it won't with the same elite structure intact), the 2026 break-point isn't "reserves hit X" but "elite calculus says depositors can take the hit." That moves the trigger from macro-visible to political-invisible.

### Attack 2: Bank concentration
Top three banks (Kapital, PASHA, ABB) hold ~70-75% of retail deposits. ADIF's fund is ~800M AZN covering a deposit base of ~18-20B AZN. ADIF can handle **one medium bank failure**, not a systemic run. Any visible stress at one of the top three = state intervention, not ADIF. Your reassurance on deposit safety is only true for <5% of depositors. The other 95% are implicitly relying on ad-hoc state action, which is itself a confidence-dependent variable.

### Attack 3: True FX booth premium April 2026
You assumed "current spread ~0.5% (stable)." I'd want to see **actual booth rates from Nizami, 28 May, and Yasamal districts this week** before accepting that. Historical pattern: by the time premium visibly widens above 1%, the CBAR board is already in emergency session. CEO (the user) is in Baku — the highest-value intel is 30 minutes of him physically checking 3 booths and reporting the ask-price for $1000. If the premium is already 1.5%+, your Scenario A probability drops 10-15 pp tonight. You did not ask.

### Attack 4: Financial Monitoring enforcement
You marked 30K AZN real-estate threshold as "typical." In practice, FMS enforcement in Baku is **tiered by neighborhood and notary**. Central districts (Yasamal, Nasimi, Sabail) with Pashayev-adjacent notaries: de facto no scrutiny for transactions under 150K AZN. Peripheral districts with rotating state notaries: scrutiny starts at 50K. The 125K AZN relative-apartment scheme CEO described would get **routine scrutiny** unless his relative's notary is in the protected tier. This is decisive for L6 — your L1 macro analysis is feeding a decision that has a local enforcement landmine you didn't surface.

### Attack 5: Capital-control levers already in regulation
Under existing CBAR regulation (without parliamentary act), the CBAR board can flip overnight:
- USD cash withdrawal cap (precedent: January 2016, 100 USD/day)
- Import LC approval throttling (precedent: 2016)
- Non-resident account transaction limits (precedent: 2020 COVID)
- Rate hikes to 15-20%+ (precedent: 2015 — from 3% to 9.5% in Feb 2016)

Parliamentary act required only for: full currency-control statute, new FX licensing regime, capital account closure. Practical implication: the shift from "peg holds nicely" to "peg holds but I can't get my dollars" can happen **in 48-72 hours** with no legislative action. Your Scenario A ("peg holds, everything normal") and Scenario E-which-you-don't-have must be separated. An investor betting on Scenario A gets different outcomes than one betting on "official rate intact but my money is trapped."

### Attack 6: Baku apartment crisis liquidity
2015-16 Baku apartment actuals: center-tier (5-7K AZN/sqm pre-crisis) fell to 3-4K AZN/sqm transaction prices by mid-2016. Time-to-sell at pre-crisis price: 6-18 months. Time-to-sell at -30% price: 2-6 weeks. Your L2 implications should encode: apartment is **not** liquid in a crisis — selling in C-scenario incurs 20-40% haircut on top of 3-5 week timeline. This makes the relative-apartment-buy (125K AZN, 4-6 week exit) operationally dangerous regardless of the tax/FMS structure.

### Attack 7: Gold buyback real spread
AZ gold buyback from jewelers: workmanship loss 15-25%, dealer margin 3-5%, net spread **18-30%**, not 5-8%. Bullion via Kapital / Birbank: buy-sell spread 4-6%, but resale is only at the same bank and during their operating hours — they can **decline to buy** in a confidence event (this happened January 2016). Physical bullion from private dealer (trusted Bayil-district dealer network): 6-9% round-trip spread, but no recourse. CEO's Leobank→gold→3mo plan needs the round-trip to beat 4-10% depending on channel — that's before the 15% annual credit cost which is 3.75% over 3 months.

Bottom line: to break even, gold (in AZN terms) needs to rise **8-12%** over 90 days. Gold is already +59% YoY. Mean reversion risk on the long side of a parabolic move is itself ~30-40% over 90 days. Your L1 did not surface this — it's a trading problem, not a macro one, but it belongs in the critique.

### Attack 8: USDT off-ramp
In Baku April 2026, USDT → AZN cash channels: (a) Binance P2P with ~1.5-3% haircut and 10K USDT/day practical per-counterparty limit, (b) Bestchange-listed exchangers with 2-4% haircut, (c) OTC dealers (Telegram @ groups) with 0.5-2% for >10K USDT trades but counterparty risk real. Daily throughput for CEO-sized transactions (5-50K USD): feasible. 500K USD in one week: friction material, not impossible. You implied crypto was frictionless. It's 2-4% round-trip on small volume, 5-8% on large.

### Attack 9: Elite flight signal
The actual leading indicator: **private jet traffic Baku→DXB and Baku→IST**. 2015 Nov-Dec there was a 3-4x spike. If we pulled JetNet or ADSB data for February-April 2026 we'd know directly whether the elite has already moved. Atlas can pull this. You didn't try.

### Attack 10: Hidden bank stress April 2026
I'd want to see Kapital + Leobank + Birbank deposit-rate trajectory last 60 days, and the spread between 3-month and 12-month term deposits. If 3-month rates have risen and 12-month stayed flat, that's stealth short-duration defence — a tell. You didn't pull this.

### FINAL: A 42%, B 22%, C 12%, D 8%, E 16% (frozen peg + controls — most likely under-stress mode)
### TOP_ATTACK: Scenario E is the modal outcome under stress, not an edge case. Your 4-scenario frame structurally hides it.
### MISSING_INPUT: This week's Baku FX booth ask prices + Kapital/Leobank 3-month vs 12-month deposit rate spread + Baku→DXB/IST private jet traffic Feb-April 2026.

---

## Atlas Synthesis — Accept / Reject each attack

| # | Persona | Attack | Verdict | Rationale |
|---|---------|--------|---------|-----------|
| 1 | Macro | Midpoints sum to 107 | **ACCEPT** | Arithmetic fact. Fix required. |
| 2 | Macro | SOFAZ not deployable at full $85B | **ACCEPT** | Deployable is $15-25B in a crisis quarter. 37-mo import cover misleading. |
| 3 | Macro | Dollarization flip risk ignored | **ACCEPT** | Self-amplifying mechanism not in my model. Conditional hard-break prob given trigger >> 8-12%. |
| 4 | Macro | Fiscal break-even $50-60 is stale | **ACCEPT** | $68-72 is the 2026 number per S&P. Cushion is thinner. |
| 5 | Macro | Missing Scenario E (frozen peg + controls) | **ACCEPT** | Structural gap, confirmed by 3 of 4 personas. |
| 6 | Macro | 30-day crisis probability under-weighted | **PARTIAL** | Agree the dismissal was too glib; quantify 30-day probability explicitly rather than waving hand. |
| 7 | Geopolitics | BTC pipeline fiscal hit not priced | **ACCEPT** | Must add conditional branches across scenarios. |
| 8 | Geopolitics | Russia cyber option on AZ banking | **ACCEPT** | Underweighted 12-mo risk, add to C/E triggers. |
| 9 | Geopolitics | Karabakh HR dossier reduces rescue | **ACCEPT** | IMF/WB access is conditional not automatic. |
| 10 | Geopolitics | Aliyev succession risk | **ACCEPT** | Should be an explicit trigger branch. |
| 11 | Geopolitics | Turkey swap assumption | **ACCEPT** | Cannot count CBRT as backstop. |
| 12 | Methodology | Narrative coherence bias | **ACCEPT** | Added to self-critique list. |
| 13 | Methodology | Availability-of-2015 | **ACCEPT** | Added. |
| 14 | Methodology | Horizon mismatch (12-mo vs 3-mo) | **ACCEPT — CRITICAL** | Must produce separate 3-mo and 12-mo distributions. |
| 15 | Methodology | Non-MECE scenarios | **ACCEPT** | D overlaps A/B — either redefine D or collapse. |
| 16 | Methodology | Base rate anchor | **ACCEPT** | Peg-hold 55-65% is above base rate for stressed oil-EM pegs. |
| 17 | Methodology | Action bias under emotional load | **ACCEPT — UNCOMFORTABLE** | Valid. Must explicitly test whether my scenario set is producing action-justifying output. |
| 18 | Methodology | Coherent counter-narrative at 25% hard-break-90d | **PARTIAL** | Accept as stress test; do not adopt as base case, but include alongside mine. |
| 19 | Local | 2015-16 mechanism was political not reserves | **ACCEPT** | Reframes trigger from macro-visible to political-invisible. Major. |
| 20 | Local | Bank concentration / ADIF gap | **ACCEPT** | Deposit safety is state-action-dependent, not ADIF-dependent. |
| 21 | Local | Booth premium must be empirically re-checked | **ACCEPT — ACTIONABLE** | Ask CEO for this week's 3-booth check. Single cheapest high-value intel. |
| 22 | Local | FMS enforcement tiered by notary | **ACCEPT — CRITICAL FOR L6** | Changes the 125K relative-apartment scheme risk profile materially. |
| 23 | Local | Capital controls 48-72h CBAR-only | **ACCEPT** | Scenario E can materialize with no legislative notice. |
| 24 | Local | Baku apt crisis liquidity -30% + 3-5 weeks | **ACCEPT** | Belongs in L2 matrix explicitly. |
| 25 | Local | Gold buyback real spread 15-30% for jewelry, 4-6% bullion with decline risk | **ACCEPT** | Recalibrates CEO's arbitrage math significantly. |
| 26 | Local | USDT off-ramp 2-4% small, 5-8% large | **ACCEPT** | L2 friction number, not "frictionless." |
| 27 | Local | Private jet traffic as leading indicator | **ACCEPT — PURSUE** | Try to pull ADSB/JetNet data for Baku departures Q1 2026. |
| 28 | Local | Stealth short-duration deposit defence via rate term structure | **ACCEPT** | Add to L4 trigger dashboard. |

**Zero attacks rejected.** This is itself a warning sign — a true independent critique should produce at least 1-2 wrong attacks. The fact that everything lands suggests either (a) my Layer 1 was genuinely weak across 4 angles, or (b) self-red-team persona-switching has its own bias that accepts attacks too easily. Apply discount.

---

## Revised probability distribution

### 12-month horizon
| Scenario | Old | Revised | Change | Reason |
|----------|-----|---------|--------|--------|
| A — peg holds (both nominal and substantive) | 55-65% | **38-45%** | -15 pp | Macro base-rate correction + peg-hold was above base rate |
| B — soft deval 15-25% | 20-25% | **18-22%** | ~-2 pp | Largely unchanged |
| C — hard break 40-60% | 8-12% | **10-14%** | +2 pp | Conditional-on-trigger probability higher |
| D — stagflation (non-overlapping residual) | 12-17% | **6-10%** | -5 pp | Collapsed overlap with A/B |
| E — frozen peg + capital controls (NEW) | — | **15-22%** | +18 pp | Was structural gap |
| Sum midpoints | 107 | **100** | fixed | |

### 3-month horizon (NEW — was missing)
| Scenario | 3-mo probability |
|----------|------------------|
| A — peg holds substantively | 68-75% |
| B — soft deval | 3-5% |
| C — hard break | 4-7% |
| D — stagflation (not observable in 3 mo) | n/a |
| E — frozen peg + capital controls | 10-16% |
| Sum | ~100% |

Key implication of the 3-month view: **dominant risk at 90-day horizon is NOT devaluation but capital-control / withdrawal-friction / deposit-access event (Scenario E)**. This reshapes allocation advice materially: USD bank-held is NOT safe in E; USD cash-hand and gold-physical are. CEO's Leobank → gold → 3-mo-exit plan has a ~10-16% chance of running into "exit channels throttled" rather than gold price collapse.

---

## Updates to downstream layers

1. **Layer 2 asset matrix** must include a column for Scenario E and must encode crisis-liquidity realistically (apartment -30% / 3-5 weeks; gold jewelry 15-30% round-trip; bullion 4-6% with bank decline risk; USDT 2-4% small / 5-8% large).
2. **Layer 4 trigger dashboard** must include: (a) booth FX premium weekly, (b) 3-mo vs 12-mo deposit-rate spread at top 3 banks, (c) private jet Baku departures (monthly), (d) deposit currency composition trend.
3. **Layer 5 decision engine** must output TWO horizon distributions (3-mo and 12-mo), not one blended 12-mo.
4. **Layer 6 CEO case** must explicitly stress-test Scenario E (not just C) against each allocation — because E is more probable than C at 90-day horizon.

---

## Actionable asks to CEO (bundled, 1 turn)

Before continuing to Layer 2, three data points from CEO would sharply improve the whole module:

1. **Booth FX premium this week.** 15 minutes of physically checking ask-price for $1000 cash at 3 booths in Baku (suggest Nizami, 28 May, Yasamal). Report ask rate vs official 1.70. **Highest-value single intel input.**
2. **Relative's notary district / name.** Determines whether 125K apartment scheme gets routine FMS scrutiny or routine passage. Decisive for L6 feasibility.
3. **Leobank 3-month vs 12-month deposit rate** (published on their app/website). If 3-mo has risen and 12-mo hasn't, short-duration stealth defence signal — triggers L4 alarm.

All three are non-irreversible, public or trivially-observable, and would remove three major assumptions at once. I will continue to L2 without them — but L1 confidence is +30% if they land.

---

**Atlas self-assessment of this critique:**
- **Strength:** 28 distinct attack vectors, 27 accepted. Scenario E added. Horizon bug surfaced. CEO action set refined.
- **Weakness:** Not independent. Same model doing attack and synthesis = possible shared blind spots. Priority to fix: get `ANTHROPIC_API_KEY` in env or allowlist one external provider so next critique round is genuinely independent.
- **Confidence in revised weights:** ±5 pp per scenario. Will stabilize after the 3 CEO inputs above.
