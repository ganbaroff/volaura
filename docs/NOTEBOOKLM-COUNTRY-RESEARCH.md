# NotebookLM Country Research — CEO Onboarding Guide

**Purpose:** Use NotebookLM to research each target country's legal, regulatory, and market requirements — so Volaura can adapt before entering each market.
**Audience:** CEO (Yusif) + Legal Advisor agent.
**Time per country:** 2–3 hours first time. 45 min for subsequent countries (reuse the template).

---

## What You're Researching (and Why It Matters for Volaura)

Before Volaura can operate in a new country, you need answers to:

| Question | Why It Matters |
|----------|---------------|
| Does the country have data localization? | If yes, Supabase EU/US hosting may block you. Need local server or exemption. |
| Is an AI scoring system regulated? | EU AI Act = HIGH risk class. May require bias audit + human oversight. |
| Are "volunteer" roles labor by another name? | If yes, your B2B product creates org liability. ToS must disclaim. |
| What's the VAT/GST rate on SaaS? | Affects pricing. Some countries (Russia, Turkey) require local VAT registration from day 1. |
| Is there a WHT on payments from Polar/Stripe? | AZ has 10% WHT on SWIFT. Affects your take-home revenue from that market. |
| What language must legal notices be in? | Some countries (France, Turkey, China) require local language ToS/Privacy Policy. |

---

## Step-by-Step: Setting Up a Country Notebook

### Step 1 — Create the Notebook

1. Go to [notebooklm.google.com](https://notebooklm.google.com)
2. Click "New Notebook"
3. Name it: `Volaura Legal — [Country Name] — [Year]`
   Example: `Volaura Legal — Georgia — 2026`

### Step 2 — Add Sources

Add these sources for EVERY country (paste URLs or upload PDFs):

**Tier 1 — MUST HAVE (do these first):**

| Source | Where to find it | What to look for |
|--------|-----------------|-----------------|
| National data protection law | Official parliament or justice ministry website | Data localization, consent requirements, definitions of personal data |
| Data protection authority website | Search "[country] data protection authority" | Guidance on GDPR equivalence, fines, registration requirements |
| IAPP Country Privacy Report | iapp.org/resources (free, search country name) | Pre-summarized legal overview, updated regularly |

**Tier 2 — SHOULD HAVE:**

| Source | Where to find it | What to look for |
|--------|-----------------|-----------------|
| Baker McKenzie Global Privacy Handbook | Downloadable free PDF, search "Baker McKenzie global privacy handbook" | Chapter for your target country |
| Deloitte International Tax Highlights | deloitte.com/global/en/services/tax.html | VAT/GST on digital services, WHT rates |
| EU AI Act full text | eur-lex.europa.eu | If country is in EU/EEA — check if your product is "AI system" under the Act |
| Local legal tech blog or law firm article | Search "[country] personal data saas startup 2024 2025" | Practical perspective from local lawyers |

**Tier 3 — NICE TO HAVE:**

| Source | Where to find it | What to look for |
|--------|-----------------|-----------------|
| Startup community forums (local language) | Reddit, local equivalents | Real founder experiences |
| Stripe Atlas country guides | stripe.com/atlas/guides | Payment, incorporation context |
| US Embassy commercial service reports | trade.gov/country-commercial-guides | For CIS countries — objective market analysis |

### Step 3 — Ask These Questions in NotebookLM

Copy and paste these questions, one by one, into the NotebookLM chat:

**Block A — Data Protection:**
```
1. Does [country] require personal data of its citizens to be stored on servers located within [country]? What are the specific legal requirements and any exemptions?

2. What is the legal basis required under [country] law to process professional performance data (such as skill assessment scores) for the purpose of professional matching? Is "legitimate interests" or "explicit consent" the recommended basis?

3. What are the user rights under [country] data protection law? Specifically: right to erasure, right to access (DSAR), right to object to automated decision-making.

4. What are the notification/registration requirements for Volaura as a data controller in [country]? Is there a data protection authority registration required before operating?

5. Does [country] have a data breach notification law? What is the required timeline and who must be notified?
```

**Block B — AI & Employment:**
```
6. Does [country] have any regulations specifically addressing the use of artificial intelligence or algorithmic scoring in hiring or employment decisions? What are the requirements?

7. How does [country] law classify "volunteers" for labor law purposes? At what point does an unpaid volunteer role become a labor relationship requiring employer obligations?

8. What anti-discrimination laws apply in [country] to professional assessment tools? What protected characteristics are relevant (e.g., age, gender, ethnicity, disability)?
```

**Block C — Business & Payments:**
```
9. What is the VAT/GST rate on digital services (SaaS) sold to customers in [country]? At what revenue threshold does a foreign company need to register for VAT in [country]?

10. Does [country] impose withholding tax (WHT) on payments made from [country] businesses to foreign companies via digital payment platforms (Stripe, Polar, PayPal)? What is the rate and are there treaty exemptions?

11. What language(s) are legally required for Terms of Service and Privacy Policy for a platform targeting [country] users?

12. Does [country] require a local legal entity to operate a B2B SaaS platform targeting [country] organizations? Or can a foreign company (e.g., Georgian LLC) contract with [country] businesses directly?
```

**Block D — Platform-Specific:**
```
13. Based on the sources, what is the single highest legal risk Volaura faces in [country]?

14. What must Volaura do BEFORE acquiring its first user in [country] to be legally compliant?

15. Is local licensed legal counsel required for [country] entry, or can Volaura self-service compliance based on the legal framework?
```

### Step 4 — Generate the Country Legal Profile

After asking all questions, ask NotebookLM to synthesize:

```
Based on all sources and our conversation, please generate a structured Country Legal Profile for Volaura entering [country]. Use this format:

COUNTRY LEGAL PROFILE: [Country]
1. DATA PROTECTION LAW — name, key obligations, localization requirement, risk level
2. EMPLOYMENT/LABOR CLASSIFICATION — volunteer definition, AI-in-hiring, risk level
3. PAYMENT & FINANCIAL COMPLIANCE — VAT rate, WHT, currency, risk level
4. PLATFORM LIABILITY — intermediary law, required disclaimers, risk level
5. RECOMMENDED ACTIONS — P0 (before first user), P1 (before 100 users), P2 (before paying customer)
6. LOCAL COUNSEL NEEDED — Yes/No + why
```

### Step 5 — Save and Share

1. Export the NotebookLM conversation as PDF or copy the Country Legal Profile
2. Save to: `docs/legal/[country-code]-legal-profile.md` in the Volaura repo
3. Tag the Legal Advisor agent when you want a deeper analysis or action items

---

## Priority Country Queue

Research these countries in order:

| # | Country | Why | Priority |
|---|---------|-----|----------|
| 1 | **Georgia** | Likely company registration location (DSP recommends). Need to understand GEO law as the operating entity's home. | P0 |
| 2 | **Azerbaijan** | Primary market. All users live here. AZ personal data law + payment WHT must be understood before any B2B revenue. | P0 |
| 3 | **Kazakhstan** | Largest CIS market after Russia. High potential for B2B (large orgs). Data localization law exists. | P1 |
| 4 | **Uzbekistan** | Fastest growing CIS economy. No data law maturity = simpler entry but changing fast. | P1 |
| 5 | **EU (Germany)** | First EU market. GDPR applies. EU AI Act may apply (AI scoring = HIGH risk class). Hardest compliance. | P2 |
| 6 | **Turkey** | Large professional population. KVKK (Turkish PDPA) is GDPR-like. WHT varies. | P2 |
| 7 | **Russia** | Data localization required (Roskomnadzor). Significant complexity. Defer until clear strategy. | P3 — DEFER |

---

## What Happens After the Research

1. **NotebookLM produces Country Legal Profile** → saved to repo
2. **Legal Advisor agent reviews profile** → adds Volaura-specific risk analysis
3. **CTO implements P0 actions** (consent screens, Privacy Policy updates, etc.)
4. **CEO hires local counsel for P1/P2** (agent briefs the counsel with the profile)
5. **Legal Advisor updates CLAUDE.md Skills Matrix** when new jurisdiction is entered

---

## Adding Legal Advisor to Your Team Workflow

The Legal Advisor agent activates via `memory/swarm/skills/legal-advisor.md`.

**Load it automatically when:**
- Any new feature stores a new data type
- Any new country is targeted
- B2B contract or ToS needs to be written
- An organization asks "how do you handle our employee data?"

It's in the Skills Matrix in CLAUDE.md. The team will load it on these triggers.

---

## Quick Reference — Already-Researched Risks

From the platform audit and AZ founder research (no full NotebookLM run yet):

| Risk | Status |
|------|--------|
| AZ 10% WHT on SWIFT payments | Known — Polar (Stripe Connect) avoids this |
| GDPR data processor agreement with Supabase | **NOT DONE** — needed before EU users |
| Google (Gemini) as data processor disclosure | **NOT DONE** — needed in Privacy Policy |
| AZ data localization for AZ citizen data | **UNCLEAR** — NotebookLM research needed |
| ToS & Privacy Policy for platform | **NOT DONE** — P0 before public launch |
| EU AI Act HIGH risk classification | **UNASSESSED** — NotebookLM research needed |

---

*NotebookLM Country Research Guide v1.0 — Created 2026-04-02. CEO directive: "онбординг сделайте чтобы notebook lm использовать мог чтобы сделать ресёрч по каждой стране чтобы адаптироваться могли мы." Update this doc as countries are researched and profiles are saved.*
