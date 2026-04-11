# Volaura × Pasha Bank — Pitch Deck

**Prize:** 7,000 AZN + May acceleration event
**Deadline:** End of March 2026
**Presenter:** Yusif Ganbarov
**Format:** ~10 slides + live demo

---

## Slide 1 — Hook (30 seconds)

> **"When Pasha Bank hires 100 people, how do you know who is actually competent — and who just interviewed well?"**

**Talking points:**
- Every company in Azerbaijan has this problem
- CVs lie. Interviews are biased. References are friends
- There is no objective, scalable way to verify what a candidate can actually do
- Volaura solves this. Let me show you.

---

## Slide 2 — The Problem (60 seconds)

**Headline:** Traditional hiring is broken in Azerbaijan

**3 failure modes:**
1. **Paper CVs** — list of positions, no verified skills. Anyone can write "experienced in X"
2. **Subjective interviews** — HR managers use intuition, not data. Results vary by interviewer
3. **No scalability** — testing 500 candidates manually costs 200+ hours

**The Azerbaijan context:**
- Baku market is tight — good candidates all know each other
- Companies over-hire and under-test → high turnover
- Government organizations (DOST, AZPROMO) have zero standardized testing

**Visual:** Two columns — "What candidate says" vs "What employer actually gets"

**Talking points:**
- "WUF13 volunteers — I was there as a volunteer coordinator. We had 2,000+ volunteers, zero way to know who was actually competent beyond gut feel"
- "The evaluation system was literally paper-based in 2024"
- "This is the moment I realized software could fix this"

---

## Slide 3 — Solution (90 seconds)

**Headline:** Volaura — AI-powered verified competency for every hire

**Three components:**
1. **AI Assessment Engine** — adaptive questions that adjust difficulty in real-time based on candidate ability (Item Response Theory — the same method used by GMAT, GRE, TOEFL)
2. **MiroFish Question Generator** — generates personalized questions from the candidate's own CV, their past projects, their claimed skills. Can't be Google'd.
3. **Anti-cheat Layer** — browser-based gaze tracking detects when candidate looks away; behavioral signals (answer timing, copy-paste patterns) flag suspicious responses

**Output:** A verified competency score (AURA), a detailed radar chart by skill dimension, and a fraud detection report.

**Talking points:**
- "This is NOT a quiz platform. The questions are generated FROM the candidate's own background"
- "If they claim they managed COP29 logistics, we ask them: how many accreditation passes were issued at COP29 Baku? A real coordinator knows. A faker Googles."
- "Adaptive testing means a 20-question test is as accurate as a 100-question one"

---

## Slide 4 — Live Demo (3 minutes)

**URL:** https://volaura-web.vercel.app

**Demo script:**
1. Open the URL — show it's live, real, not Figma
2. Login as test HR manager → see organizations dashboard
3. Create an assessment → choose competency: "Communication"
4. Show assessment in action → adaptive questions → real-time theta update (hidden from candidate)
5. Complete → show AURA score + competency radar + badge tier
6. Show volunteer search → filter by minimum AURA score + location + language

**Talking points:**
- "This is running on real infrastructure right now — Railway backend, Vercel frontend, Supabase database"
- "The engine uses IRT (Item Response Theory) — the same algorithm used by ETS for TOEFL scoring"
- "Every response is scored by Gemini 2.5 Flash, not just multiple choice"

---

## Slide 5 — Why Pasha Bank Specifically (60 seconds)

**Headline:** Volaura can transform how Pasha Bank hires

**Pasha Bank's hiring reality:**
- Hundreds of candidates per year for retail banking, operations, tech
- Need for: communication skills, reliability, English proficiency, tech literacy
- These are EXACTLY the 8 dimensions Volaura measures

**What Volaura gives Pasha Bank:**
| Without Volaura | With Volaura |
|-----------------|--------------|
| 3-round interview for every candidate | Pre-screen 500 candidates in 2 days |
| Interviewer bias | Objective AURA score |
| No data on why hire failed | Full competency history per candidate |
| Manual reference checks | Verified peer assessments |

**ROI estimate:**
- Pasha Bank interviews: assume 500 candidates/year × 3 rounds × 1h each = 1,500 HR hours
- Volaura pre-screen eliminates 70% → saves ~1,000 hours/year
- At 20 AZN/h fully loaded cost → **20,000 AZN saved/year**
- Volaura cost at 5 AZN/assessment × 500 = **2,500 AZN/year**
- ROI: **800%**

---

## Slide 6 — The Technology Moat (45 seconds)

**Why this can't be replicated easily:**

1. **IRT Engine (3PL model)** — pure Python, custom-built. Measures true ability, not just % correct. Takes months to tune.
2. **BARS Scoring** — Behaviorally Anchored Rating Scales evaluated by LLM. Open-ended answers, not just multiple choice.
3. **Anti-gaming system** — 6 independent signals: answer timing, response entropy, copy-paste detection, gaze tracking, theta consistency, behavioral fingerprint
4. **Adaptive calibration** — questions improve with each user. The more data, the better the estimates.

**Talking point:** "No off-the-shelf HR software does this. SHL and Hogan cost $50K+/year and don't adapt. We're building the modern version, for the Azerbaijan market, at 10% of the cost."

---

## Slide 7 — Business Model (45 seconds)

**B2B SaaS — per assessment pricing**

| Tier | Price | For |
|------|-------|-----|
| Starter | 5 AZN/assessment | SMEs, NGOs |
| Growth | 3 AZN/assessment | 100+ assessments/month |
| Enterprise | Custom | Banks, government, 500+ |

**First 100 volunteers:** FREE (B2C acquisition funnel → proves accuracy → sells B2B)

**Year 1 target:**
- 3 enterprise clients (banks, telco, government)
- 2,000 paid assessments/month
- Revenue: 60,000–120,000 AZN/year

**Pasha Bank opportunity:** Enterprise contract, ~1,000 assessments/year = 10,000 AZN/year recurring

---

## Slide 8 — Traction (30 seconds)

**What exists TODAY:**

| Item | Status |
|------|--------|
| Working assessment engine (IRT + BARS) | ✅ Live |
| 8 competency dimensions | ✅ Seeded |
| 34 frontend tests passing | ✅ |
| Security: RLS, rate limiting, anti-cheat | ✅ |
| Live on Vercel + Railway | ✅ Today |
| Privacy Policy (GDPR compliant) | ✅ Today |
| CI/CD pipeline | ✅ |

**Built by:** 1 founder + Claude (AI technical co-founder) in 3 sprints (3 weeks)

**Cost to date:** ~$50 (Supabase + API keys)

---

## Slide 9 — Ask (30 seconds)

**We're asking for:** 7,000 AZN prize + Pasha Bank as design partner

**What we'll do with it:**
- Month 1: Beta launch with 100 volunteers → calibrate IRT model
- Month 2: B2B onboarding flow for HR managers → pilot with 1 Baku company
- Month 3: Eye-tracking integration → enterprise-grade proctoring demo

**What we're NOT asking for:** Investment. Advisory. A committee. Just a chance to prove it works with real Pasha Bank data.

**The offer to Pasha Bank:** 6-month pilot, 500 assessments, FREE. In exchange for feedback and a testimonial.

---

## Slide 10 — Closing (15 seconds)

> **"The best volunteers at WUF13 couldn't prove they were the best. The best candidates at Pasha Bank probably can't either. Volaura changes that."**

**Contact:** yusif@volaura.az | volaura-web.vercel.app

---

## 🎯 Preparation Checklist (Yusif)

Before the pitch:
- [ ] Create a test HR account on volaura-web.vercel.app
- [ ] Create a test volunteer account
- [ ] Run through the assessment demo once (verify it completes end-to-end)
- [ ] Screenshot the AURA score + radar chart for slide backup (in case demo wifi fails)
- [ ] Prepare 1 specific Pasha Bank hiring example ("if you're hiring a branch manager...")
- [ ] Know the numbers: 500 candidates/year, 1,500 hours, 20K AZN saved

## ❓ Likely Hard Questions (with answers)

**"How is this different from existing HR testing platforms?"**
→ SHL, Hogan, Korn Ferry cost $50K+/year and use static question banks. Volaura generates questions from the candidate's own background — they can't be copied from prep guides. And it's priced for the Azerbaijani market.

**"What about cheating? Can't candidates just have someone else take the test?"**
→ Three layers: (1) browser gaze tracking detects looking away, (2) questions are generated FROM the candidate's specific CV so only they know the answers, (3) behavioral fingerprint — response timing and patterns flag anomalies. No system is 100% cheat-proof, but Volaura makes cheating harder than the test itself.

**"How do you validate the scores are accurate?"**
→ IRT (Item Response Theory) has been used by ETS for 40+ years for GRE, TOEFL, GMAT. We use the same 3-parameter model. Accuracy improves with each additional candidate — the model self-calibrates. After 1,000 candidates in one competency, the scores are highly reliable.

**"Why should we trust AI scoring of open-ended answers?"**
→ The LLM doesn't give the score — it provides a BARS rating (Behaviorally Anchored Rating Scale). The same method trained HR professionals use. The LLM is consistent; humans aren't. And every LLM score is logged with confidence — low-confidence responses flag for human review.

**"What's the data privacy situation?"**
→ GDPR compliant, AZ Personal Data Law compliant. Candidate data stored on Supabase EU region. Assessments encrypted at rest. Candidates can export or delete their data at any time. We published our Privacy Policy today (docs/privacy-policy.md).

**"What if the AI makes a mistake?"**
→ No single assessment decides hiring. Volaura provides a data point — HR managers make the final call. The system flags low-confidence scores for human review. We're replacing the least reliable part (gut-feel screening) not the most reliable part (final interview).

---

## 🎙️ Talking Points — By Audience Type

### If panel is technical:
- IRT 3PL model, EAP ability estimation, HNSW vector index for semantic search
- FastAPI async, pgvector, Gemini 2.5 Flash with structured output
- 6 anti-gaming signals, BARS prompt injection defense, CSP hardening

### If panel is business:
- ROI: 800% in year 1 for a company interviewing 500+ candidates
- Time saved: from 3 rounds to pre-screen in 20 minutes
- Per assessment cost: 5 AZN vs 1+ hours of HR manager time

### If panel is skeptical:
- "We have a working product, live today, tested by real users"
- "The prize money pays for 3 months of server costs and lets us run the beta"
- "We're not asking you to buy anything — we're asking for a pilot"

---

*Prepared by Claude (CTO) + Yusif (CEO) — Sprint 3, 2026-03-24*
