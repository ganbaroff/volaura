# PITCH DECK — single source of truth (real, cited)

> Built 2026-06-10 from a 3-agent repo sweep (cited FILE:LINE, no fabrication). This is what the deck is allowed to say. The deck `volaura-deck-v2.pdf/html` (in Downloads) is the v2 draft — generic design, [CEO-fill] holes. v3 must: use the REAL numbers below, the LOCKED positioning, a design tool (not hand-HTML), real visuals, and be visually verified slide-by-slide before "done".

## ⛔ HARD TRUTH (no-fakes) — read first
- **There is NO current fundraise "ask" amount in any repo doc.** The only figure is a **Phase-4 Series A target $500K–$1M, 18–36 months out** (`docs/MASTER-STRATEGY.md:188`, `docs/archive/ROADMAP.md:109`). The deck "ask" lines are literal placeholders (`docs/financial-model.md:156`, `memory/swarm/skills/investor-board-agent.md:88`).
- **Runway is explicitly a NON-issue:** <$100/mo burn, savings-funded; break-even = 4 Pro subs OR 1 Starter org (`for-ceo/briefs/2026-04-questions-resolved.md:139,146`; `docs/financial-model.md:119`). So a "raise $X / N months runway" slide would be **invented**.
- **Traction is genuinely pre-beta:** verified audit 2026-04-15 = **0 real external users, 0 paying, 39 test accounts, 13 completed assessments** ("Good engine, no passengers" `docs/audits/FULL-ECOSYSTEM-AUDIT-2026-04-15.md:10,12,18-30`). VOLAURA is live on prod but **user-blocked pending legal sign-off**. Do NOT claim users.
- **Positioning is LOCKED (ADR-016):** "verified professional talent platform." **BANNED: "volunteer platform", "LinkedIn competitor", "universal talent platform"** (zero tolerance, `docs/adr/ADR-016-positioning-lock.md:38-46`). Many strategy docs still use the old "volunteer" framing — STALE, do not copy.

## TWO things only CEO can confirm (deck blocked on these)
1. **Ask framing.** Since there's no current raise, the honest ask = pick: (a) **accelerator** (YC S26 + Techstars are already in the plan, `GITA:331,340`), (b) **pilot partners** (1–3 companies), (c) **non-dilutive grants** (GITA, now a fallback), (d) signal a future **Series A $500K–1M**. NOT a fabricated seed number.
2. **Founder bio conflict.** GITA says "civil society & digital transformation" (`GITA:369`); the pitch script says **"10 years managing COP29, CIS Games, large event operations"** (`docs/financial-model.md:154`). The COP29/CIS-Games version is concrete AND matches the event/ops GTM wedge — recommend that one; CEO confirm.

## Contact (use in deck — NEW, not gmail)
`yusif.ganbarov@volaura.app` · `0556003666` · volaura.app · Baku, Azerbaijan · VOLAURA, Inc. (Delaware C-Corp, EIN 37-2231884, `memory/atlas/company-state.md:21`)

## LOCKED positioning + taglines (verbatim, ADR-016:44-46)
- Company: "VOLAURA is a verified professional talent platform."
- User tagline: **"Prove your skills. Earn your AURA. Get found by top organizations."**
- Org tagline: **"Search talent by verified skill and score, not unverified CVs."**

## Slide content — REAL, cited (recommended v3)
1. **Cover** — VOLAURA + user tagline + one-liner + contact above.
2. **Problem** — résumé/ATS bias; assessments assume one cognitive shape (energy-blind); scores are frozen + non-portable. (v2 problem slide is good; keep.)
3. **Why now** — (a) HR-tech moving off degrees: **73% of US/EU employers shifting from degree-based screening** [LinkedIn Workforce Report 2024 — SOURCED, `GITA:31,118`]; (b) inference cost collapsed → we run scoring at **$0** (free-provider gateway, live); (c) neurodiversity now a hiring category.
4. **Solution** — AURA: candidate-OWNED, portable, energy-adaptive, evidence-based score from a real adaptive psychometric engine (IRT/CAT 3PL). 8 competencies, AZ/EN/RU.
5. **Product** — VOLAURA assessment (LIVE on prod) + MindShift (LIVE, Play internal-test closed 2026-05-28). BrandedBy/LifeSim/ZEUS = **frozen** (`memory/projects/volaura.md:15`) — mention as roadmap, not "live."
6. **How it works** — energy check → IRT adaptive items (θ/SE convergence) → evidence scoring (multi-provider, $0, no single-vendor lock) → AURA persists + portable → ADHD-safe UX (never red, CI-enforced).
7. **Market** — HR-Tech **~$35B (2024)** [Gartner + Grand View Research — SOURCED, `GITA:115`]. *Use ONLY sourced numbers.* Flag/avoid the unsourced "$47B 2028" and "$4B pre-hire" unless CEO adds a source. Beachhead: AZ/CIS (AZ 1.2M LinkedIn, CIS 50M+ — label "internal estimate").
8. **Traction = de-risked execution (honest)** — real IRT engine prod-verified (200 OK, `git_sha 3293289`); ~4,235 backend test functions; 2 live products; **$60k+ credits secured** (NVIDIA Inception/Nebius $5k+$150k, Google $3.2k, Azure $5k, AWS Activate, PostHog $50k — see CREDITS-AND-RESOURCES.md); $0 inference. **Explicitly: pre-beta, legal-gated, no fake users.**
9. **Business model** — free for individuals (build AURA) → companies pay to hire on them. B2B: search by AURA / custom assessments / governance. Pricing = **NOT locked** (4+ conflicting sheets) → show as "target tiers", don't commit exact $.
10. **Roadmap** (GITA dated, positioning-correct, `GITA:215-220,343-354,145-147`) — Jun 2026 first 100 candidates · Aug 500 · Oct $50K-rev milestone · Dec 10 org partners · Y1-end 5,000 profiles/10 orgs · Y2 25,000/50 · Y3 50,000/100 · Series A $500K-1M H2 2027. Engineering P0s mostly DONE; launch gated only on legal (Art.9 consent + AZ PDPA).
11. **Team + Ask** — Yusif Ganbarov, Founder/CEO (bio per confirm above), solo + AI-augmented; hiring React+Python devs (grant-funded); B2B sales = CEO. Advisors [Pending]. Ask per confirm #1.

## Projections (if a financials slide is wanted — LABEL as projections, GITA newest)
Y1 **214,200 AZN (~$126K)** → Y2 **~$504K** → Y3 **~$2M** (`GITA:228-234`, 1 USD≈1.7 AZN). Gross margin software-grade (inference ~$0). Other models exist + conflict — GITA is newest + positioning-correct.

## DESIGN directive for v3 (why v2 failed: generic + verified-by-text-not-eyes)
Use a real design tool (Canva MCP generate/brand-template → export PDF, or pptx skill / Figma). Carry ONE visual per slide: AURA flywheel diagram, a product screenshot, the $35B market bar, the 8-competency wheel. Palette: teal #4ECDC4 / indigo #7B72FF / gold #F59E0B on dark — NEVER red. **Screenshot every slide and Read it before declaring done.** Run the humanizer skill on copy.
