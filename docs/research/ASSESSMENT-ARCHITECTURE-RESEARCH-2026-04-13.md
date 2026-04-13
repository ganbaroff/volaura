# Assessment Architecture Research — Evidence + Ecosystem Integration

**Date:** 2026-04-13 | **By:** Cowork (Research Advisor)  
**Purpose:** Prove our technical choices are the best available AND design how assessment integrates into the 5-product ecosystem  
**CEO directive:** "доказать что это лучшие варианты и рабочие. продумать структуру чтобы была не отдельная республика а в экосистему вливалась"

---

## PART 1: ARE OUR CHOICES THE BEST?

### 1.1 IRT/CAT — VERDICT: CORRECT CHOICE, INDUSTRY GOLD STANDARD

**What we use:** 3PL IRT (3-Parameter Logistic) with Computerized Adaptive Testing (CAT), EAP ability estimation, Maximum Fisher Information item selection.

**Evidence it's the best:**

IRT/CAT is the same technology behind GRE, GMAT, CISSP, USMLE (medical licensing), Duolingo English Test, and Florida's statewide K-10 assessments. In 2024-2025, ISC2 migrated three more certifications (CC, SSCP, CCSP) from fixed-form to CAT because it achieves the same measurement precision with fewer items in half the time.

**Alternatives considered and why they lose:**

| Alternative | Why it's worse for VOLAURA |
|---|---|
| Fixed-form test (same questions for everyone) | Requires 2-3x more questions for same precision. Items leak easily — memorize and share. No energy adaptation possible. |
| Rasch/1PL (simpler IRT) | Assumes all items discriminate equally — wrong for our mixed MCQ + open-ended bank. Our items have discrimination (irt_a) from 1.1 to 2.4 — forcing them all to 1.0 loses real information. |
| 2PL (no guessing parameter) | Better for self-report measures where guessing isn't a factor. But our MCQs have 4-5 options — guessing IS a factor. 3PL's `c` parameter (0.08-0.20 in our bank) correctly models this. |
| Classical Test Theory (CTT) | No item-level modeling. Can't do adaptive testing. Score depends on which items you got — not comparable across different item sets. |
| Deep CAT (neural network) | Research paper from Feb 2025 (arXiv:2502.19275). Promising but requires massive training data (100K+ responses). We have ~170 responses. Won't work until we have 10K+ users. |
| BanditCAT (Duolingo's new approach) | Uses contextual bandits for item selection. Requires AutoIRT for calibration — needs automated ML pipeline. Overhead we don't need at beta scale. Worth revisiting at 5K+ users. |

**Our 3PL + MFI + EAP is the textbook correct choice for:**
- Small item bank (101 questions)
- Mixed question types (MCQ + open-ended)
- Low-data regime (<1000 examinees)
- Need for energy adaptation (Constitution Law 2 — just change stopping criteria)

**One improvement to make later:** When we reach 5K+ users, switch from manually calibrated IRT parameters to AutoIRT (machine-learning calibration from response data). Duolingo published this approach in late 2024.

---

### 1.2 BARS + LLM Evaluation — VERDICT: CORRECT CHOICE, WITH KNOWN RISKS

**What we use:** Behaviourally Anchored Rating Scale concepts with multi-provider LLM evaluation (Vertex/Gemini → Groq → OpenAI → keyword fallback). DeCE framework for per-concept explainability.

**Evidence it's the best:**

BARS has been the standard for behavioral competency assessment since Smith & Kendall (1963). It is used in medical simulation assessment (PMC9090385, 2022 — showed adequate reliability), military performance evaluation, and HR competency review across Fortune 500 companies. Unlike generic rubrics, BARS ties scores to observable behaviors, which is exactly what VOLAURA needs for event volunteering competencies.

The LLM evaluation layer is validated by 2024-2025 research: a systematic review of 49 studies (Emirtekin 2025) found that GPT-4 class models achieve QWK up to 0.99 with human raters when properly prompted. Our approach matches the best practices identified in this research: structured rubrics (expected_concepts with keywords and weights), per-concept scoring with evidence quotes (DeCE), and multi-evaluator fallback.

**Alternatives considered:**

| Alternative | Why it's worse |
|---|---|
| Simple rubric without BARS anchors | Vague criteria ("good communication") → inconsistent scoring. BARS provides concrete behavioral descriptions per concept. |
| Human-only evaluation | Impossible at scale. $2-5 per evaluation × 8 competencies × 15 questions = $240 per user. Latency: 24-48 hours. |
| Single LLM provider | Single point of failure. Our 4-provider chain (Vertex → Gemini → Groq → OpenAI → keyword) survived every provider outage in beta. |
| Fine-tuned model | Requires 10K+ labeled examples per competency. We have ~170. Also removes flexibility — can't add new competencies without retraining. |
| AutoSCORE (multi-agent LLM, 2025) | Interesting: separates rubric extraction from scoring using two specialized agents. Worth investigating when we need higher precision. Currently our single-prompt DeCE approach works. |

**Known risk (documented in ADR-010):** keyword_fallback can inflate scores — blind cross-test showed buzzwords scoring 0.77 vs real experts 0.59-0.89. Mitigation: degraded mode flagging, auto-reeval worker, Telegram alerts. Research confirms this is the right approach — "rubric interpretation drift" is a known LLM limitation (Rulers framework, 2025).

**One improvement to make later:** Adopt the "Rulers" approach (arXiv:2601.08654, 2025) — treat rubrics as executable specifications, not flexible advice. This would make our BARS evaluation more deterministic.

---

### 1.3 Anti-Gaming — VERDICT: CORRECT AND BETTER THAN MOST

**What we use:** 7 behavioral detection methods (timing, patterns, clustering) + progressive penalty multiplier.

**Evidence it's the best:**

The $1.99B proctoring industry (2029 projection) relies primarily on camera/microphone surveillance — invasive, expensive, and hated by test-takers. VOLAURA's approach is the opposite: statistical detection from response patterns, zero hardware requirements, zero privacy invasion.

Our 7 checks catch the most common cheating behaviors identified in the literature: rapid guessing (rushing < 3s), pattern-matching (alternating/identical), and time-based anomalies. The progressive penalty (0.15 per flag, minimum 0.1) is proportional — one flag doesn't destroy a score, but systematic gaming does.

**What competitors do:**

| Platform | Approach | Privacy cost |
|---|---|---|
| ProctorU | Live proctor + AI webcam monitoring | High — room scan, ID verification, face tracking |
| HackerEarth | Browser lockdown + AI proctoring | Medium — blocks tools, monitors screen |
| Adaface | Question randomization + plagiarism detection | Low |
| **VOLAURA** | **Statistical behavioral analysis + IRT mismatch detection** | **Zero — no camera, no lockdown** |

Our approach is unique: the RT-IRT rapid guessing check (comparing response time to expected time given item difficulty) is a psychometric signal, not a surveillance signal. This is academically defensible and privacy-preserving.

**One improvement to make:** Add response similarity detection across users — if two users answer open-ended questions with suspiciously similar text within a short time window, flag for review. This catches the "share answers via WhatsApp" scenario at live events.

---

### 1.4 AURA Weighted Scoring — VERDICT: CORRECT FOR NOW, UPGRADE PATH EXISTS

**What we use:** Fixed weighted average of 8 competency scores, with weights defined by CEO (communication 0.20, reliability 0.15, etc.).

**Evidence:**

Research shows that weighted composites are the most transparent and explainable scoring method — critical for VOLAURA's promise of verifiable credentials. The weights were set by domain expertise (CEO's direct experience at WUF13, COP29, CIS Games), not arbitrary.

Multidimensional IRT (MIRT) provides slightly higher reliability than weighted composites, but requires all competencies to be measured simultaneously in one session. VOLAURA measures one competency per session — MIRT can't apply until we have enough users taking multiple competencies.

**Upgrade path:** When 50%+ of users have completed 3+ competencies, we can fit a MIRT model to optimize weights empirically. The current CEO-defined weights become the Bayesian prior; data updates them. This gives the best of both worlds: domain expertise + statistical optimization.

**Current formula is defensible because:**
- Weights sum to 1.0 (mathematically correct, verified in DB)
- DB RPC function `calculate_aura_score` matches the Python code exactly
- Badge tiers (40/60/75/90) provide intuitive cut-points
- Percentile rank computed per-user → relative positioning is fair

---

## PART 2: ECOSYSTEM INTEGRATION ARCHITECTURE

### The Problem CEO Identified

Assessment is currently a "separate republic" — it runs, scores, and stores data, but doesn't flow into the other 4 products. The Constitution governs all 5 products, but the assessment data only stays in VOLAURA tables.

### Current Data Flow (isolated)

```
[User] → /start → /answer → /complete → aura_scores → public profile
                                      → analytics_events (fire-and-forget)
                                      → character_events (crystal rewards only)
```

Nothing flows to MindShift, Life Simulator, BrandedBy, or ZEUS.

### Proposed: Assessment as Ecosystem Nerve Center

Assessment data should be the **source of truth** that every product reads from. Not a separate system, but the core signal.

```
                         ┌─────────────────────────────────────────┐
                         │         ASSESSMENT ENGINE               │
                         │  IRT/CAT → BARS → AURA Score            │
                         │  (lives in VOLAURA, serves everyone)    │
                         └──────────────┬──────────────────────────┘
                                        │
                         ┌──────────────▼──────────────────────────┐
                         │        character_events (EVENT BUS)      │
                         │  source_product | event_type | payload   │
                         └──┬─────────┬─────────┬─────────┬────────┘
                            │         │         │         │
                ┌───────────▼──┐ ┌────▼─────┐ ┌▼────────┐│┌─────────▼──┐
                │  MindShift   │ │Life Sim  │ │BrandedBy│││  ZEUS      │
                │              │ │          │ │         │││  Gateway   │
                │ AURA →       │ │ AURA →   │ │ AURA → │││ AURA →     │
                │ coaching     │ │ character │ │ content │││ agent      │
                │ paths        │ │ stats    │ │ unlock  │││ decisions  │
                └──────────────┘ └──────────┘ └─────────┘│└────────────┘
                                                         │
```

### Integration Points per Product

**1. VOLAURA → MindShift (Mental wellness)**

| Data from Assessment | MindShift Uses It For |
|---|---|
| Competency gaps (low scores) | Suggest specific coaching modules |
| Energy level chosen | Adapt MindShift session intensity |
| Assessment completion streak | Fuel "growth trajectory" visualization |
| Gaming flags | Trigger "honest self-reflection" nudge (shame-free, Law 3) |

**Event:** `assessment_completed` → MindShift reads `competency_slug`, `score`, `energy_level` from `character_events` → personalizes next coaching session.

**2. VOLAURA → Life Simulator (Gamified growth)**

| Data from Assessment | Life Simulator Uses It For |
|---|---|
| AURA score | Character base stats |
| Badge tier | Unlock character visual upgrades |
| Competency profile shape | Generate scenario challenges matching weak areas |
| Assessment history (improvement) | "Growth arc" narrative in game |

**Event:** `aura_updated` → Life Simulator reads `competency_scores` JSONB → updates character sheet → generates scenarios targeting lowest competencies.

**3. VOLAURA → BrandedBy (Personal brand)**

| Data from Assessment | BrandedBy Uses It For |
|---|---|
| Verified badge (Silver+) | Unlock "Verified Professional" content templates |
| Top competency | Auto-generate professional tagline |
| AURA trend (improving) | Content suggestion: "Share your growth story" |
| Org attestation | "Endorsed by [Org]" badge on content |

**Event:** `badge_tier_changed` → BrandedBy reads new tier → unlocks content creation tools appropriate to verified level.

**4. VOLAURA → ZEUS Gateway (Agent infrastructure)**

| Data from Assessment | ZEUS Uses It For |
|---|---|
| Full AURA profile | Agent personality calibration |
| Competency gaps | Agent proactively suggests assessments |
| User's energy pattern | Agent adapts communication style |
| Anti-gaming flags | Agent honesty calibration |

**Event:** ZEUS reads `aura_scores` + `assessment_sessions` directly (same DB). Agent context includes: "User's communication is 37/100, reliability untested. Suggest reliability assessment next."

### The Event Bus Already Exists

`character_events` table is already in the DB schema:
```sql
-- Already exists:
character_events (
  id UUID,
  user_id UUID,          -- who
  source_product TEXT,    -- 'volaura', 'mindshift', 'lifesim', 'brandedby'
  event_type TEXT,        -- 'assessment_completed', 'aura_updated', 'badge_changed'
  payload JSONB,          -- competency_scores, badge_tier, etc.
  created_at TIMESTAMPTZ
)
```

Assessment already emits `crystal_earned` and `skill_verified` to this table. We need to add:
- `assessment_completed` (competency, score, energy_level, items_answered)
- `aura_updated` (new total, new badge, changed competencies)
- `badge_tier_changed` (old_tier, new_tier)

These 3 events make assessment data available to ALL products without any product knowing about assessment internals.

### Shared Services (Not Duplicate)

| Service | Lives in | Used by |
|---|---|---|
| `embeddings.py` (profile → vector) | VOLAURA API | Discovery, ZEUS agent search |
| `llm.py` (4-provider chain) | VOLAURA API | BARS eval, coaching, MindShift content gen |
| `aura_calc.py` (scoring math) | VOLAURA API | AURA page, Life Sim stats, BrandedBy badge |
| `character_events` | Supabase | ALL 5 products (read/write) |
| AURA weights | DB RPC function | Guaranteed single source of truth |

### Constitution Compliance Checkpoints

Every cross-product flow must pass these 5 laws:

| Law | Assessment Integration Rule |
|---|---|
| 1. Never Red | Error states in any product reading AURA → purple, not red |
| 2. Energy Adaptation | If user chose "Low energy" in assessment → other products respect this for the session |
| 3. Shame-Free | "Your communication needs work" → NEVER. "Growth opportunity in communication" → yes |
| 4. Animation Safety | AURA score display in any product → instant or max 800ms |
| 5. One Primary Action | Any screen showing AURA data → one CTA, not "retake + share + explore" |

### What Needs to Be Built (Priority Order)

| # | Task | Effort | Depends on |
|---|---|---|---|
| 1 | Emit 3 new events from `/complete` | 2 hours | Nothing — just add to existing endpoint |
| 2 | MindShift reads `assessment_completed` events | 1 day | MindShift DB listener or polling |
| 3 | Life Simulator reads `aura_updated` for character stats | 1 day | Life Sim character system |
| 4 | ZEUS agent context includes AURA profile | 4 hours | ZEUS agent prompt template |
| 5 | BrandedBy reads `badge_tier_changed` for unlocks | 1 day | BrandedBy feature system |
| 6 | Energy level propagation across products | 2 days | Shared session/preference store |

**Task 1 is P0 and should ship with Handoff 010.** The rest follow the product roadmap.

---

## PART 3: WHAT WE DON'T HAVE AND DON'T NEED YET

### CV Processing — NOT NEEDED

VOLAURA's value proposition is "prove your skills through testing, not through self-reported resumes." Adding CV parsing would undermine this core differentiator. The CVA (Certified in Volunteer Administration) — the only existing volunteer credential — also uses competency-based assessment, not resume review.

**When it becomes relevant:** Phase 2 (Universal Skills Platform) — when companies want to compare AURA scores against existing employee resumes. That's a separate product feature, not an assessment engine change.

### Job Description Alignment — FUTURE FEATURE

The infrastructure exists (pgvector embeddings + `match_volunteers` RPC), but the JD-specific pipeline doesn't. This is correct prioritization — build the assessment credibility first, then add matching.

**When it becomes relevant:** When we have 100+ organizations on the platform. Currently: 0 active orgs.

### AI Proctoring — DON'T ADD

Camera-based proctoring is a $1.99B industry that is universally hated by test-takers. Our statistical anti-gaming is more elegant, less invasive, and aligns with the Constitution's ADHD-first design philosophy (no additional cognitive load from "being watched").

---

## SOURCES

- [ISC2 CAT Migration 2025](https://www.isc2.org/Insights/2025/05/computerized-adaptive-testing-examination-format-updates)
- [Cambridge Assessment — What is CAT (2024)](https://www.cambridgeassessment.org.uk/blogs/what-is-cat-2024/)
- [BanditCAT + AutoIRT (2024)](https://arxiv.org/html/2410.21033v1)
- [Deep CAT (2025)](https://arxiv.org/html/2502.19275)
- [BARS Reliability in Medical Simulation (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9090385/)
- [LLM Automated Assessment — Systematic Review (2025)](https://www.mdpi.com/2076-3417/15/10/5683)
- [LLM Essay Scoring Reliability & Validity](https://www.sciencedirect.com/science/article/pii/S2666920X24000353)
- [Rulers: Evidence-Anchored LLM Evaluation (2025)](https://arxiv.org/html/2601.08654)
- [AutoSCORE: Multi-Agent LLM Scoring (2025)](https://arxiv.org/html/2509.21910v1)
- [Multidimensional IRT for Composite Scores](https://files.eric.ed.gov/fulltext/ED504361.pdf)
- [Optimal Weights via MIRT](https://www.tandfonline.com/doi/full/10.1080/00273171.2018.1478712)
- [Weighted vs Composite Scoring — Dental Education (2023)](https://onlinelibrary.wiley.com/doi/10.1002/jdd.13203)
- [3PL vs 2PL vs Rasch Comparison](https://assess.com/three-parameter-irt-3pl-model/)
- [Duolingo English Test — Psychometric Report](https://duolingo-papers.s3.amazonaws.com/reports/DRR-20-02.pdf)
- [CVA Certified Volunteer Administration](https://cvacert.org/)
- [Competency-Based Digital Credentials (2025)](https://www.verifyed.io/blog/competency-and-credentialing)
