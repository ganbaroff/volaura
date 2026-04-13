# PLAN: Product Trust Architecture — Privacy, Transparency, Adoption

**Date:** 2026-03-25
**Author:** CTO
**Status:** v2 — post agent review (5 agents, scores 5.5-6.5/10)
**Scope:** Ideas #7, #8, #9 from IDEAS-BACKLOG + Telegram chat fix (#10)

---

## Problem Statement

CEO identified 4 connected problems that block B2B adoption:

1. **Score Inversion Risk**: If coordinator scores higher than their manager → organizational conflict → organizations refuse Volaura
2. **Black Box Problem**: Nobody explains WHY a score is what it is → users don't trust results
3. **Fear of Weakness**: People avoid assessment because they fear low scores → adoption problem
4. **CEO Communication Channel Broken**: 6 Telegram messages with zero replies → agent team unreachable

These are not independent features. They form a TRUST ARCHITECTURE — the foundation that makes organizations and individuals willing to use Volaura.

---

## Plan

### Phase 1: Privacy-First Assessment (Idea #7) — CRITICAL, blocks B2B

**What changes:**

1. **Role selection at assessment start**
   - User picks their role: Volunteer / Coordinator / Specialist / Manager / Senior Manager
   - Stored in `assessment_sessions.role_level` (new column)
   - Question pool and difficulty calibration adjusted per role level

2. **Role-calibrated scoring curves**
   - Same raw score → different percentile depending on role
   - Coordinator scoring 85 = "excellent coordinator" (not "better than managers")
   - Prevents cross-role comparison that causes organizational conflict
   - Implementation: `role_percentile_curves` table with role_level + competency + percentile breakpoints

3. **PUBLIC by default, hide on demand** (CHANGED after Leyla critique: privacy-first kills adoption)
   - Badge + score VISIBLE to organizations by default — this IS the value prop
   - User can HIDE specific competencies or full profile (opt-out, not opt-in)
   - New column: `aura_scores.visibility` ENUM ('public', 'badge_only', 'hidden') DEFAULT 'public'
   - Organization dashboard shows: aggregate team stats + all public profiles
   - Rationale: volunteer takes test TO BE SEEN. Hiding by default = 2-step activation = nobody shares

4. **Organization aggregate dashboard**
   - Org admin sees: "Average AURA: 72. Communication: 81. Leadership: 65."
   - Does NOT see individual scores unless volunteer shared
   - Prevents managers from comparing themselves against subordinates

**DB changes:**
- `assessment_sessions`: add `role_level VARCHAR(20)`
- `aura_scores`: add `visibility VARCHAR(20) DEFAULT 'private'`
- `role_percentile_curves`: new table (role_level, competency_id, p25, p50, p75, p90)
- RLS: users see own scores only; org admins see aggregate + opted-in

**Risks + Mitigations (from agent review):**
- Role self-selection gaming: coordinator picks "volunteer" for easier curve (+15-20 points inflation)
  - Mitigation: ORG-ASSIGNED role by default (Nigar's recommendation). Self-select only for solo users.
  - If user disagrees with assigned role → can request change with explanation → org admin reviews
- Role percentile curves EMPTY at launch (0 users = 0 data for calibration)
  - Mitigation: Bootstrap with IRT-theoretical percentiles until N=50 per role. Show "Estimated" label until real data.
  - Weekly RPC recalculates percentiles from real data once N>50
- Org with <5 users: aggregate data identifies individuals
  - Mitigation: k-anonymity. Hide aggregate stats if org <5. Tier counts <3 → merge with adjacent tier.
- Score inversion visible to managers → conflict
  - Mitigation: Nigar's recommendation — DUAL scoring: (a) global comparable score (same scale for everyone), (b) role-specific sub-report showing within-role strength. Never hide the global score.
- evaluation_log JSONB → 4.5GB/year at 100K users → blows $50/mo budget at ~3K users
  - Mitigation: Archive evaluation_log to Cloudflare R2 after 30 days. Keep only {score, confidence, model_version} in DB (200B vs 1.5KB)
- Consent model missing between org and volunteer
  - Mitigation: New table `sharing_permissions(user_id, org_id, permission_type, granted_at, revoked_at)`
  - Volunteer controls per-org visibility. Org requests access, volunteer approves/denies.

### Phase 2: Transparent Evaluation Logs (Idea #8) — HIGH

**What changes:**

1. **Store evaluation rationale per answer**
   - Currently: BARS evaluator returns score (1-5) + brief reasoning
   - Change: Store full reasoning in `assessment_answers.evaluation_log` (JSONB)
   - Format: `{ criteria_used: [...], score_breakdown: {...}, rationale: "...", research_basis: "..." }`

2. **"Why this score?" API endpoint**
   - `GET /api/aura/me/explanation` → returns per-competency breakdown
   - Each competency: which answers contributed, how they were scored, what framework was used
   - References: ISO 10667-2, Heckman (2006) non-cognitive skills framework, BARS methodology

3. **UI: Expandable explanation per competency**
   - Radar chart node → tap → "Your Leadership: 72/100"
   - Below: "Based on: Answer to Q4 (crisis decision-making, +12), Answer to Q7 (conflict avoidance, -8)"
   - Bottom: "Methodology: BARS framework aligned with ISO 10667-2"

4. **Share with explanation**
   - Current share: badge with score only
   - New option: "Share with reasoning" → generates mini-report showing WHY

**DB changes:**
- `assessment_answers`: add `evaluation_log JSONB` (store per-answer rationale)
- No new tables needed — evaluation data lives alongside answers

**Risks:**
- LLM explanations can be wrong or inconsistent
- Mitigation: template-based explanations (not freeform LLM text). LLM provides structured data, UI renders consistent format
- Privacy: explanation reveals question content → only visible to score owner, not org

### Phase 3: Adoption Strategy (Idea #9) — MEDIUM

**What changes:**

1. **Free tier for first 100 users** — no code change needed, just a counter
2. **Progress framing in UI** — show delta ("↑15 since last assessment") not just absolute score
3. **Share progress, not score** — "I improved from 63 to 78" button alongside "Share badge"
4. **Pricing tiers implementation** — later, after adoption proves product-market fit

**DB changes:**
- `aura_scores`: already has `created_at`, can compute delta from previous assessment
- No new tables for MVP pricing (manual for first 100)

### Phase 4: CEO ↔ Agent Telegram Chat (Idea #10) — HIGH

**What changes:**

1. **Telegram bot receives CEO message**
2. **Classifier routes message** to relevant agent domain (architecture/content/business/security)
3. **Agent processes + generates response**
4. **Bot sends reply** in same Telegram thread
5. **All conversations logged** in `memory/swarm/ceo-chat-log.md`

**Implementation:** Edge function or cron-triggered script that checks for new messages, dispatches agents, returns responses.

---

## Execution Order

1. Phase 1 (Privacy) — FIRST. Without this, B2B demo is risky.
2. Phase 2 (Transparency) — alongside Phase 1. They share DB migration.
3. Phase 4 (Telegram) — can run in parallel, independent.
4. Phase 3 (Adoption) — after 1+2 are live.

## Estimated Effort (REVISED after Scaling Engineer critique: 7 → 11 sessions)

| Phase | Backend | Frontend | DB Migration | Added by agents | Total |
|-------|---------|----------|-------------|-----------------|-------|
| 1. Privacy + Consent | 2 sessions | 1 session | 1 migration | +0.5 (sharing_permissions) | 3.5 sessions |
| 2. Transparency | 1 session | 1 session | same migration | +0.7 (R2 archive service) | 2.7 sessions |
| 3. Adoption | 0.5 session | 0.5 session | none | +0.5 (percentile bootstrap) | 1.5 sessions |
| 4. Telegram | 1 session | 0 | 0 | +0.5 (spoofing protection) | 1.5 sessions |
| 5. Testing | — | — | — | +1.0 (edge cases, load test) | 1.0 session |
| **Total** | | | | | **~10.2 sessions** |

## Open Questions (RESOLVED after agent review)

1. ~~Should role be self-selected or org-assigned?~~ → **ORG-ASSIGNED** (Nigar). Self-select only for solo users.
2. ~~How detailed should evaluation logs?~~ → **Per-competency summary for MVP** (Nigar). Per-answer in v1.1 after I/O psychometrist validation.
3. ~~Aggregate dashboard free or paid?~~ → **Free: team averages. Paid ($20/mo): heatmap + trends + export** (Nigar).
4. ~~Telegram sync or async?~~ → **Async** (reply when ready, notify CEO via message).

## New Questions (from agents)
1. How to handle retakes? → Supersede old session, show both in history, leaderboard = latest only
2. What if user scores LOWER on retake? → Show variance context: "±8 points is normal. Focus on [areas]"
3. "Share with explanation" but user disagrees with AI assessment? → Add "Comment" field per competency (Leyla)
4. Assessment interrupted mid-session? → Auto-save every 60s, resume on return

## Agent Review Results

| Agent | Score | Key Change Accepted |
|-------|-------|-------------------|
| Leyla (5.5/10) | PUBLIC by default, not private | ✅ Changed |
| Nigar (6/10) | Org-assigned roles, dual scoring, consent table | ✅ Changed |
| Attacker | Role gaming + Telegram spoofing mitigations | ✅ Added |
| Scaling (6.5/10) | R2 archive, 11 sessions not 7, budget model | ✅ Changed |
| QA | 12 edge cases, retake spec, k-anonymity | ✅ Added |

## CTO Root Cause Analysis (what I got wrong)

| Пропуск | Root Cause | Lesson |
|---------|------------|--------|
| Privacy kills adoption | Designed for compliance not user value | Always ask: "Does the user get value from step 1?" |
| Empty percentile curves | Designed schema without data lifecycle | Always ask: "Where does the initial data come from?" |
| No consent model | Thought about actors separately | Always map inter-actor flows before schema |
| 4.5GB/year storage | No cost calculation | Always do back-of-envelope math before JSONB columns |
| 7→11 sessions | No buffer | Always add 50% buffer to estimates |

---

## CEO's Words to Team

> "Мы становимся стандартом. Не просто платформой — точкой отсчёта которой доверяют. Никаких ошибок. Никаких 'ой извините перепутали'. Мы даём точный результат и умеем его объяснить. Каждый балл — аргументирован. Каждый критерий — задокументирован. Прозрачность и точность — это наш бренд."
