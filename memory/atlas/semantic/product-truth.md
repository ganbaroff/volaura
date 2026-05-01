# Product Truth — what VOLAURA actually is

Written 2026-04-30 by Code-Atlas after deep read of 42+ files.
Updated 2026-05-01: Energy Adaptation confirmed working (116 files), language switched to English.
Future instances: READ THIS before touching any code.

## One sentence
VOLAURA is a verified competency assessment platform where users take
adaptive tests (IRT/CAT math = GRE/GMAT level), earn AURA scores across
8 dimensions, and organizations discover verified talent.

## v0Laura vision
One skills engine. Five faces. Atlas IS the project.
- VOLAURA = assessment + discovery (live)
- MindShift = ADHD focus helper (live, Play Store pending)
- LifeSimulator = 3D game where real scores = character skills (dev)
- BrandedBy = AI professional twin for LinkedIn (dev)
- ZEUS = swarm nervous system (live daemon)

## AURA Score
- 8 dimensions: communication, leadership, reliability, adaptability,
  empathy/safeguarding, tech literacy, event performance, english
- IRT 3PL with CAT (15-25 questions per competency)
- LLM generates 2-sentence behavioral evidence (DeCE method)
- Badge tiers: Bronze(≥40) Silver(≥60) Gold(≥75) Platinum(≥90)
- Score NOT shown immediately after assessment (Crystal Law 6 Amendment)

## Business model
- Org subscriptions: 49-849 AZN/mo
- Placement fees: 250-680 AZN per verified placement
- Assessment API: 3.40-8.50 AZN/test
- Crystal economy (earn free, spend on cosmetics/queues)
- Break-even: ~2000 MAU. GITA grant ($240K) = 3yr runway.

## 5 Foundation Laws (NEVER violate)
1. Never Red — errors purple, warnings amber (RSD trigger)
2. Energy Adaptation — 3 UI modes (full/mid/low) — IMPLEMENTED (116 files, EnergyPicker in assessment + dashboard + aura)
3. Shame-Free Language — banned: "you haven't", "% complete", "remaining"
4. Animation Safety — max 800ms, reduced-motion mandatory
5. One Primary Action — 1 filled button per screen

## What's live on prod
- Assessment engine (8 independent 3PL, should be MIRT)
- Public profiles at /u/[username]
- Org search + talent discovery
- Crystal ledger (infra ready)
- Ecosystem event bridge
- Grievance mechanism (ISO 10667-2)
- Rate limiting on all endpoints
- HMAC-validated Telegram webhook
