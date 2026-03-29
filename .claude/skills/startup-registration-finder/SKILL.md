---
name: startup-registration-finder
description: Find optimal jurisdictions for startup registration. Compares tax efficiency, visa access, grant eligibility, banking, and ecosystem strength. Universal — works for any founder nationality, startup stage, and sector. Includes research protocol and cost calculators.
---

# Startup Registration Finder

## When to Use
- Founder asks "where should I register my startup?"
- Comparing countries for tax/visa/grant benefits
- Planning multi-jurisdiction strategy
- Need specific registration steps for a country
- Evaluating relocation vs remote registration

## Research Protocol (ALWAYS run before recommending)

**NEVER recommend a jurisdiction without checking:**

1. **Current tax regime:** Search `[country] corporate tax rate startups [current year]` — rates change
2. **Startup visa status:** Search `[country] startup visa [founder nationality] [current year]`
3. **Banking accessibility:** Search `[country] bank account opening [founder nationality]` — some countries block certain passports
4. **Grant programs:** Search `[country] startup grants innovation agency [current year]`
5. **Registration cost:** Search `[country] LLC registration cost foreign founder [current year]`

**Source hierarchy:** Government websites > Embassy sites > Established legal firms > Blog posts

## Decision Framework

### Step 1: Define Founder Profile

```
FOUNDER PROFILE:
- Nationality: [country]
- Current residence: [city, country]
- Dependents: [number, ages]
- Budget for registration: $[X]
- Timeline: [when needed by]
- Primary market: [where customers are]
- Funding goal: [grants / VC / bootstrapped]
- Travel flexibility: [can relocate / remote only]
```

### Step 2: Score Jurisdictions

For each candidate country, score (1-10):

```
JURISDICTION SCORE =
  Tax_Efficiency × 2 +
  Grant_Access × 3 +        ← highest weight for early-stage
  Banking_Ease × 2 +
  Visa_Access × 1.5 +
  Ecosystem × 1.5
  ─────────────────
        10

Tax_Efficiency: Lower effective rate = higher score. 0% = 10, 25% = 5
Grant_Access: More/bigger grants accessible = higher. $250K grant = 10
Banking_Ease: Can open account remotely without visit? 10 = online, 1 = impossible
Visa_Access: Startup visa available for nationality? 10 = easy, 1 = restricted
Ecosystem: Accelerators, VCs, talent in country? 10 = SF/London, 1 = no ecosystem
```

### Step 3: Compare Top 3

Output table format:
```
| Criterion | [Country 1] | [Country 2] | [Country 3] |
|-----------|-------------|-------------|-------------|
| Corporate tax | X% | X% | X% |
| Startup tax exemption | Yes/No | Yes/No | Yes/No |
| Registration cost | $X | $X | $X |
| Timeline | X weeks | X weeks | X weeks |
| In-person required | Yes/No | Yes/No | Yes/No |
| Bank account | Easy/Hard | Easy/Hard | Easy/Hard |
| Grant programs | [list] | [list] | [list] |
| Max grant amount | $X | $X | $X |
| Startup visa | Yes/No | Yes/No | Yes/No |
| TOTAL SCORE | X/10 | X/10 | X/10 |
```

## Country Profiles (verify — data may be stale)

### Georgia
- **Tax:** 0% corporate (Virtual Zone, non-Georgian revenue), 15% (Georgian revenue)
- **Registration:** $78 express (1 day government), total ~$300-500 with agent
- **Remote registration:** YES (Power of Attorney + apostille from home country)
- **Bank:** TBC Bank, Bank of Georgia — foreign-friendly, 2-5 days
- **Grants:** GITA Matching Grants ($35K-$250K, 0% equity, 10% matching required)
- **Special:** Virtual Zone = 0% tax on software exports. Apply via GITA post-registration.
- **Timeline:** 3-4 weeks total (including apostille from home country)

### Turkey
- **Tax:** 20-25% corporate. Tech zones have incentives.
- **Registration:** ~$500-1,000 with agent
- **Remote registration:** Partially (some in-person steps)
- **Bank:** Moderate difficulty for non-residents
- **Grants:** KOSGEB (~$50K, 80% coverage, requires entrepreneurship training)
- **Special:** Large market (85M), bridge to EU
- **Timeline:** 4-6 weeks

### Kazakhstan
- **Tax:** 20% corporate. Astana Hub has reduced rates.
- **Registration:** ~$200-500
- **Bank:** Moderate difficulty
- **Grants:** Astana Hub ($5K-$20K)
- **Special:** CIS market access, Russian-speaking talent pool
- **Timeline:** 2-4 weeks

### UAE (Dubai/Abu Dhabi)
- **Tax:** 0% corporate (up to 375K AED), 9% above
- **Registration:** $2,000-$15,000 (free zone dependent)
- **Bank:** Easy for most nationalities
- **Grants:** Limited for startups. Hub71 (Abu Dhabi) has incentives.
- **Special:** 0% personal income tax. Strong for B2B credibility.
- **Timeline:** 1-2 weeks (free zone)

### Estonia
- **Tax:** 20% on distributed profits only (0% if reinvested)
- **Registration:** ~$300 (e-Residency), fully remote
- **Bank:** Wise Business, LHV — EU IBAN
- **Grants:** EASME, ESA (EU programs)
- **Special:** e-Residency = digital identity, fully remote management
- **Timeline:** 2-4 weeks (e-Residency card: 3-8 weeks)

### Portugal
- **Tax:** 21% standard, reduced for startups (NHR regime ended 2024)
- **Registration:** ~$500-1,000
- **Bank:** Moderate
- **Grants:** EIC Accelerator (up to $2.5M via EU entity)
- **Special:** D8 visa (digital nomad), path to EU residency
- **Timeline:** 4-8 weeks

## Multi-Jurisdiction Strategy

For maximum grant stacking:

```
SEQUENCE (not parallel — register one at a time):

1. PRIMARY: [Lowest cost, biggest grant, fastest timeline]
   → Register → Apply for grant → Wait for result

2. SECONDARY: [Next biggest opportunity]
   → Register after primary is settled
   → Apply for country-specific grants

3. TERTIARY: [Strategic, long-term]
   → Only if primary + secondary succeed
   → For market access, not grants
```

**⚠️ WARNING:** Grant multiplier math (e.g., "3 countries = $125K") is misleading.
Joint probability of ALL grants = P1 × P2 × P3, which is usually <20%.
Expected value is more honest:
```
EV = (P1 × Amount1) + (P2 × Amount2) + (P3 × Amount3)
NOT: Amount1 + Amount2 + Amount3
```

## Registration Checklist (universal)

```
BEFORE REGISTRATION:
□ Choose entity type (LLC recommended for startups)
□ Prepare founder documents (passport, proof of address)
□ Notarize Power of Attorney (if remote registration)
□ Get apostille on PoA (if cross-border)
□ Choose registered agent / legal service
□ Prepare company charter / articles of association
□ Identify legal address (virtual office acceptable in most jurisdictions)

DURING REGISTRATION:
□ File with national registry
□ Receive registration certificate
□ Get tax identification number
□ Open bank account
□ Apply for any special tax status (Virtual Zone, free zone, etc.)

AFTER REGISTRATION:
□ Set up accounting (even basic — required in most jurisdictions)
□ Apply for grants (now that entity exists)
□ Register for VAT if applicable
□ Set up payroll if hiring locally
```

## Cost Calculator Template

```
ESTIMATED COSTS FOR [COUNTRY]:

One-time:
  Government registration fee:    $___
  Agent / legal service:          $___
  Notarization + apostille:       $___
  Virtual office / legal address: $___
  Bank account setup:             $___
  SUBTOTAL ONE-TIME:              $___

Annual:
  Legal address renewal:          $___
  Basic accounting:               $___
  Tax filing:                     $___
  SUBTOTAL ANNUAL:                $___

TOTAL YEAR 1:                     $___
TOTAL YEAR 2+:                    $___
```

## Anti-Patterns

- **Don't register in a country just for tax rate.** If your customers are in AZ, a Georgia LLC doesn't help with local sales.
- **Don't register everywhere.** Each jurisdiction = annual costs + compliance. 2 is fine. 5 is a nightmare.
- **Don't skip apostille.** Most common delay. Start this FIRST.
- **Don't assume "1-day registration."** Government processing may be 1 day, but the FULL process (apostille + agent + bank) takes 3-4 weeks.
- **Don't count on grants.** Register because the jurisdiction makes sense. Grants are bonus.
