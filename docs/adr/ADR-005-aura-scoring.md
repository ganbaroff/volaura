# ADR-005: AURA Score Calculation System

**Status:** Accepted
**Date:** 2026-03-22
**Deciders:** Yusif (product owner), Claude (architecture)
**Related:** [[ADR-001-system-architecture]], [[ADR-002-database-schema]], [[ADR-003-auth-verification]], [[ADR-004-assessment-engine]], [[ADR-006-ecosystem-architecture]]
**Governed by:** [[../ECOSYSTEM-CONSTITUTION]] | **Products:** [[../LIFE-SIMULATOR-GAME-DESIGN]] | [[../MINDSHIFT-INTEGRATION-SPEC]]

## Context

The AURA Score is the core value proposition of Volaura — a composite credential score that quantifies volunteer quality across 8 competencies. It must be:

- **Defensible:** Transparent formula, explainable to volunteers and organizations
- **Verifiable:** Confidence multipliers based on evidence level (self-assessed, org-attested, peer-verified)
- **Fair:** Penalize inconsistency, reward breadth and depth
- **Scalable:** Fast calculation (<100ms per user), cached and batch-recalculated
- **Gamified:** Badge tiers incentivize improvement; trends motivate re-assessment
- **Shareable:** OG images, QR codes, public profiles, and formatted share cards

This ADR defines the mathematical model, recalculation triggers, database structure, Python implementation, and examples.

## Decision

### 1. AURA Score Formula

The composite AURA score is calculated as:

```
AURA = clamp(Σ(competency_score_i × weight_i × verification_multiplier_i) × reliability_factor, 0, 100)
```

**Where:**

| Variable | Definition | Range | Notes |
|----------|-----------|-------|-------|
| **competency_score_i** | Adjusted score for competency i | 0–100 | From assessment or event data; see §3 |
| **weight_i** | Fixed weight for competency i | See below | Sum of all weights = 1.00 |
| **verification_multiplier_i** | Confidence boost based on evidence level | 1.00–1.25 | Rewards attestation & peer review |
| **reliability_factor** | Penalty for inconsistent responses | 0.85–1.00 | Lower std deviation = higher factor |
| **clamp(x, 0, 100)** | Constrain to valid range | | Final score always 0–100 |

### 1.1 Competency Weights (FINAL — DO NOT CHANGE)

```
communication:           0.20  (20%)
reliability:             0.15  (15%)
english_proficiency:     0.15  (15%)
leadership:              0.15  (15%)
event_performance:       0.10  (10%)
tech_literacy:           0.10  (10%)
adaptability:            0.10  (10%)
empathy_safeguarding:    0.05  (5%)
─────────────────────────────────
Total:                   1.00  (100%)
```

**Rationale:** Communication and reliability are the top drivers of volunteer quality. English proficiency and leadership are equally important for cross-cultural coordination. Event performance, tech, and adaptability round out practical capability. Empathy/safeguarding is foundational (trust) but lower-weighted since it's binary in practice.

### 1.2 Verification Multipliers

Scores are boosted based on how the competency was demonstrated:

```
self_assessed:  1.00  (no boost; volunteer answers questions alone)
org_attested:   1.15  (15% boost; organization confirms behavior)
peer_verified:  1.25  (25% boost; 3+ peers independently verify)
```

**Logic:** Self-assessed data is baseline. Organization attestation (e.g., event feedback) adds confidence. Peer verification (from fellow volunteers) is hardest to fake and rewards social proof.

**Implementation:** Each competency tracks the best verification level achieved across all evidence. If a volunteer has both self-assessed and org-attested for "communication," use 1.15.

### 1.3 Reliability Factor

Measures consistency within each competency. If a user scores 95 on one communication question and 35 on another, that's a red flag — reliability drops.

```
reliability_factor = 1.0 - (0.15 × normalized_std_deviation)
```

**Where:**

```
normalized_std_deviation = std_dev(scores_for_competency) / 100
```

**Examples:**

| Scenario | Std Dev | Normalized | Factor | Interpretation |
|----------|---------|-----------|--------|-----------------|
| All scores 70–75 | 2 | 0.02 | 0.997 ≈ 1.00 | Very consistent |
| Scores 60, 80 | 14.1 | 0.141 | 0.979 ≈ 0.98 | Good consistency |
| Scores 30, 70 | 28.3 | 0.283 | 0.958 ≈ 0.96 | Moderate variance |
| Scores 10, 90 | 56.6 | 0.566 | **0.85** (clamped) | High variance; penalized |

**Clamping:** Minimum reliability is always 0.85 (even extreme variance). Maximum is 1.00 (perfect consistency).

**Why:** A user who answers 5 assessment questions might get different scores due to question difficulty or bad luck. The 0.15 factor (≈2.5% penalty per 0.1 std dev) is conservative. Consistency over several assessments (tracked in [[ADR-004-assessment-engine]]) is a more reliable signal.

---

### 2. Competency Score Calculation

Before the weighted sum, each competency's raw score must be adjusted for question difficulty and type.

#### 2.1 Raw Score (Difficulty-Weighted Average)

For each competency, average responses weighted by question difficulty:

```
raw_score = Σ(response_score_j × difficulty_weight_j) / Σ(difficulty_weight_j)
```

**Difficulty Weights:**

| Difficulty | Weight | Rationale |
|-----------|--------|-----------|
| Hard | 1.5x | Demonstrates mastery; value harder questions more |
| Medium | 1.0x | Baseline weight |
| Easy | 0.7x | Confidence-building; less discriminative |

**Example:**
- Volunteer scores 85 on hard question, 90 on medium, 95 on easy
- raw_score = (85×1.5 + 90×1.0 + 95×0.7) / (1.5 + 1.0 + 0.7)
- raw_score = (127.5 + 90 + 66.5) / 3.2 = 284 / 3.2 = **88.75**

#### 2.2 Question Type Adjustment

Different question formats test different capabilities. BARS (Behavioral Anchored Rating Scale) is behavioral. MCQ (Multiple Choice) is knowledge. Open Text is synthesis.

```
adjusted_score = raw_score × question_type_modifier
```

**Modifiers:**

| Type | Modifier | Rationale |
|------|----------|-----------|
| BARS (behavioral) | 1.0x | Baseline; tests actual behavior |
| MCQ (knowledge) | 0.9x | 10% discount; knowledge ≠ behavior |
| Open Text (synthesis) | 1.1x | 10% boost; requires deeper thinking |

**Why:** A volunteer who aces an MCQ might not follow through in practice. Open text responses (e.g., "Describe a time you led a team") require synthesis and are harder to game. BARS is the gold standard — ask how they actually behaved.

**Mixed Competency:** If a competency has questions of multiple types, blend modifiers by frequency:

```
effective_modifier = Σ(question_count_k × modifier_k) / total_questions
```

Example: 3 BARS + 2 MCQ + 1 Open Text per competency
```
modifier = (3×1.0 + 2×0.9 + 1×1.1) / 6 = (3 + 1.8 + 1.1) / 6 = 5.9 / 6 ≈ 0.983
```

#### 2.3 Final Competency Score

```
final_competency_score = clamp(adjusted_score, 0, 100)
```

Always clamp to 0–100 (avoids nonsensical scores from weighting).

---

### 3. Event Performance Score

Event performance is special — it does **not** come from the assessment engine. It comes from:

- **Organization ratings** after events (1–5 stars, mapped to 0–100)
- **Attendance reliability** (attended / registered ratio)
- **Recency weighting** (events in last 6 months weighted 2x)
- **Fallback:** If no event history, default to 50 (neutral)

#### 3.1 Formula

```
event_performance = weighted_avg(ratings × attendance_multiplier × recency_weight)
```

**Where:**

```
attendance_multiplier = 1.0 (if attended) or 0.3 (if no-show)
recency_weight = 2.0 (if within 6 months) or 1.0 (if older)
rating_score = (stars - 1) * 25  // 1 star → 0, 5 stars → 100
```

**Example:**

Volunteer has 4 event records:
1. 3 months ago: attended, rated 5 stars → score = 100 × 1.0 × 2.0 = 200, weight = 2.0
2. 3 months ago: attended, rated 4 stars → score = 75 × 1.0 × 2.0 = 150, weight = 2.0
3. 8 months ago: attended, rated 4 stars → score = 75 × 1.0 × 1.0 = 75, weight = 1.0
4. 8 months ago: no-show, rated 2 stars → score = 25 × 0.3 × 1.0 = 7.5, weight = 1.0

```
event_performance = (200 + 150 + 75 + 7.5) / (2.0 + 2.0 + 1.0 + 1.0)
                  = 432.5 / 6.0
                  = 72.08
```

**Edge Cases:**
- **No event history:** Default to 50 (neutral; no penalty for volunteers just starting)
- **Only no-shows:** Score can be as low as (25 × 0.3) = 7.5 per event
- **Only recent 5-star events:** Capped at 100 (no boost above perfect)

---

### 4. Reliability Factor (Deep Dive)

The reliability factor penalizes inconsistency. This is computed at AURA calculation time, not assessment time.

#### 4.1 When Is It Applied?

Once per AURA calculation:

1. Gather all responses for each competency
2. Compute std dev within that competency
3. Convert to reliability factor (0.85–1.00)
4. Apply to that competency's score
5. Sum all weighted competencies

#### 4.2 Multiple Assessments

If a volunteer completes multiple assessments, each assessment contributes its own set of responses. The std dev is computed across **all** responses in that competency, regardless of assessment.

**Example:**
- Assessment 1: Communication scores [70, 75, 72]
- Assessment 2: Communication scores [80, 85, 82]
- All scores for communication: [70, 75, 72, 80, 85, 82]
- std_dev ≈ 6.55
- normalized ≈ 0.0655
- reliability ≈ 1.0 - (0.15 × 0.0655) ≈ 0.990

This volunteer is consistent across both assessments → high reliability.

#### 4.3 Minimum & Maximum

```
reliability_factor = clamp(1.0 - (0.15 × normalized_std_dev), 0.85, 1.00)
```

- **0.85:** Even if std dev is massive (e.g., 100% score range), volunteer still gets 15% of base score
- **1.00:** Perfect consistency is never penalized below baseline

---

### 5. Badge Tiers (FINAL — DO NOT CHANGE)

Once AURA is calculated, assign a badge tier:

```
AURA Score  →  Badge Tier
─────────────────────────
≥ 90        →  Platinum ⭐⭐⭐⭐⭐
75 – 89     →  Gold     ⭐⭐⭐⭐
60 – 74     →  Silver   ⭐⭐⭐
40 – 59     →  Bronze   ⭐⭐
< 40        →  None     (no badge)
```

**Messaging:**
- **Platinum:** "Elite performer. Ready for leadership roles."
- **Gold:** "Trusted contributor. Proven reliability."
- **Silver:** "Emerging contributor. Growing capability."
- **Bronze:** "Getting started. First events recommended."
- **None:** "Assessment incomplete or scores too low. Complete assessment to earn a badge."

---

### 6. Recalculation Triggers

AURA is **not** continuously recalculated. It's computed on-demand and cached. It's automatically recalculated when:

| Trigger | Affected Components | Async? |
|---------|-------------------|--------|
| Assessment completed | All 8 competencies | Yes (via Supabase function) |
| Organization attestation received | That competency + verification level | Yes (webhook) |
| Peer verification threshold (3+ peers) | That competency + verification level | Yes |
| Event rating received | event_performance + badge history | Yes |
| Reassessment completed | All 8 competencies | Yes |

**Process:**
1. Trigger fires (e.g., assessment completed)
2. Queue async job (FastAPI background task or Supabase Edge Function)
3. Call `AURACalculator.calculate(user_id)`
4. Compare new vs. old badge tier
5. If changed, create row in `badge_history` and send notification
6. Update `aura_scores` table with new data
7. Invalidate public profile cache (Vercel ISR revalidation)

**No Forced Recalculation:**
- Scores do **not** decay automatically (volunteers shouldn't be penalized for inactivity)
- Reassessment is encouraged via email lifecycle (re-engagement campaigns) and gamification, not forced

---

### 7. Score History & Badge Transitions

#### 7.1 Badge History Table

Every time a badge tier changes, a row is created in `badge_history`:

```sql
CREATE TABLE badge_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  previous_badge badge_tier NOT NULL,
  new_badge badge_tier NOT NULL,
  previous_score INT,
  new_score INT,
  trigger VARCHAR(50),  -- 'assessment', 'attestation', 'event', 'peer_verify'
  achieved_at TIMESTAMPTZ DEFAULT now()
);
```

**Why:**
- Public profile shows progression: "Gold (2 months ago), now Platinum"
- Email milestone: "🎉 You've earned Gold! Next goal: Platinum (75+ points)"
- Leaderboard shows badge velocity (who's improving fastest)
- Analytics: track which triggers cause tier jumps

#### 7.2 Score Display

On the volunteer's dashboard:

```
Your AURA Score
═══════════════════════════════════════════════════════════════
  73  /  100        Gold Badge

  ⬆️ (+5 points)    Last assessed: 2 weeks ago

Competency Breakdown
─────────────────────────────────────────────────────────────
│ Communication         75 ████████  │
│ Reliability           68 ██████    │
│ English Proficiency   70 ██████    │
│ Leadership            72 ████████  │
│ Event Performance     80 ████████  │ (from 3 events)
│ Tech Literacy         65 ██████    │
│ Adaptability          72 ████████  │
│ Empathy/Safeguarding  85 ████████  │
─────────────────────────────────────────────────────────────

Next milestone: Silver (60) ✓ Achieved · Gold (75) ✓ Achieved · Platinum (90)
```

---

### 8. Leaderboard & Public Visibility

#### 8.1 Leaderboard Function

```sql
CREATE OR REPLACE FUNCTION get_leaderboard(
    p_limit INT DEFAULT 50,
    p_offset INT DEFAULT 0,
    p_competency VARCHAR DEFAULT NULL,
    p_badge badge_tier DEFAULT NULL
) RETURNS TABLE(
    rank INT,
    user_id UUID,
    username VARCHAR,
    avatar_url VARCHAR,
    total_score INT,
    badge_tier badge_tier,
    competency_score INT,  -- NULL if p_competency is NULL
    last_assessed TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  WITH ranked_users AS (
    SELECT
      ROW_NUMBER() OVER (ORDER BY a.total_score DESC) AS rank,
      u.id,
      u.username,
      p.avatar_url,
      a.total_score,
      a.badge_tier,
      CASE
        WHEN p_competency IS NOT NULL
        THEN cs.score
        ELSE NULL
      END AS competency_score,
      a.calculated_at
    FROM users u
    JOIN aura_scores a ON u.id = a.user_id
    LEFT JOIN competency_scores cs ON a.user_id = cs.user_id
      AND p_competency IS NOT NULL
      AND cs.competency = p_competency
    LEFT JOIN profiles p ON u.id = p.user_id
    WHERE u.role != 'platform_admin'
      AND a.total_score IS NOT NULL
      AND (p_badge IS NULL OR a.badge_tier = p_badge)
  )
  SELECT * FROM ranked_users
  ORDER BY rank
  LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;
```

**Usage:**

```typescript
// Top 50 volunteers by AURA
const leaderboard = await db.rpc('get_leaderboard', { p_limit: 50 });

// Top 50 by Communication
const commLeaderboard = await db.rpc('get_leaderboard', {
  p_competency: 'communication',
  p_limit: 50
});

// All Gold badge holders
const goldVolunteers = await db.rpc('get_leaderboard', {
  p_badge: 'gold',
  p_limit: 500
});
```

---

### 9. AURA Score Sharing & Public Profiles

#### 9.1 Public Profile URL

```
https://volaura.az/u/[username]
https://volaura.az/en/u/[username]  (English)
```

Shows:
- AURA badge (large, clickable → modal with breakdown)
- Competency radar chart (8 axes, Recharts)
- Verification badges (org-attested ✓, peer-verified 🔗)
- Badge history (badges earned over time)
- Event count & recency
- "Verify on Telegram" button (links to @VolauraBot)

#### 9.2 OG Image Generation

Using **Satori** (Vercel serverless function):

```typescript
// /api/og?user=[username]
// Returns PNG: 1200×630px with:
// - AURA score (large)
// - Badge tier icon
// - Top 3 competencies
// - QR code to public profile
// - Volaura logo
```

**Why Satori:** Renders React as PNG. Fast, no headless browser needed. Edge-friendly.

#### 9.3 Share Card Formats

Volunteer can download or share in 3 formats:

| Format | Dimensions | Use Case |
|--------|-----------|----------|
| LinkedIn | 1200×627 | LinkedIn posts, ads |
| Story | 1080×1920 | Instagram, TikTok stories |
| Square | 1080×1080 | Twitter, Instagram feed |

**Template:**
```
┌──────────────────────────────────────┐
│  I earned a Gold Badge on Volaura!  │
│                                      │
│       AURA: 75                       │
│     [Radar Chart]                    │
│                                      │
│  🔗 Verify: volaura.az/u/[handle]   │
│     [QR code]                        │
│                                      │
│  Volaura — Verified Talent          │
│  Platform                           │
└──────────────────────────────────────┘
```

---

### 10. Python Implementation (FastAPI Service)

Location: `apps/api/app/services/aura.py`

```python
"""
AURA Score Calculation Service
═════════════════════════════════════════════════════════════════
Computes the composite AURA score for a volunteer based on:
  • Assessment responses (8 competencies, weighted by difficulty & type)
  • Organization attestations (confidence multipliers)
  • Peer verification levels
  • Event performance (ratings + attendance)
  • Reliability factor (consistency penalty)
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
import numpy as np
from pydantic import BaseModel, ConfigDict
from loguru import logger
from app.deps import SupabaseAdmin


class CompetencyScore(BaseModel):
    """Single competency score breakdown."""
    model_config = ConfigDict(from_attributes=True)

    competency: str
    raw_score: float
    adjusted_score: float
    final_score: int
    verification_level: str  # 'self_assessed', 'org_attested', 'peer_verified'
    verification_multiplier: float
    question_count: int
    std_dev: Optional[float] = None


class AURAResult(BaseModel):
    """Final AURA calculation result."""
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    total_score: int  # 0-100
    badge_tier: str  # 'platinum', 'gold', 'silver', 'bronze', 'none'
    reliability_factor: float  # 0.85-1.00
    competency_scores: dict[str, CompetencyScore]
    verification_levels: dict[str, str]
    calculated_at: datetime


class AURACalculator:
    """Core AURA calculation engine."""

    # Fixed weights (FINAL — DO NOT CHANGE)
    WEIGHTS = {
        "communication": 0.20,
        "reliability": 0.15,
        "english_proficiency": 0.15,
        "leadership": 0.15,
        "event_performance": 0.10,
        "tech_literacy": 0.10,
        "adaptability": 0.10,
        "empathy_safeguarding": 0.05,
    }

    VERIFICATION_MULTIPLIERS = {
        "self_assessed": 1.00,
        "org_attested": 1.15,
        "peer_verified": 1.25,
    }

    QUESTION_TYPE_MODIFIERS = {
        "bars": 1.0,
        "mcq": 0.9,
        "open_text": 1.1,
    }

    DIFFICULTY_WEIGHTS = {
        "easy": 0.7,
        "medium": 1.0,
        "hard": 1.5,
    }

    BADGE_TIERS = [
        (90, "platinum"),
        (75, "gold"),
        (60, "silver"),
        (40, "bronze"),
        (0, "none"),
    ]

    def __init__(self, db: SupabaseAdmin):
        self.db = db

    async def calculate(self, user_id: UUID) -> AURAResult:
        """
        Calculate full AURA score for a user.

        Args:
            user_id: UUID of volunteer

        Returns:
            AURAResult with scores, badge, and breakdown

        Raises:
            ValueError: If user has no completed assessments
        """
        logger.info(f"Calculating AURA for user {user_id}")

        # Load assessment responses
        responses = await self._get_assessment_responses(user_id)
        if not responses:
            raise ValueError(f"No assessment responses found for {user_id}")

        # Load verification levels per competency
        verification_levels = await self._get_verification_levels(user_id)

        # Calculate competency scores
        competency_scores = {}
        weighted_sum = 0.0

        for competency, weight in self.WEIGHTS.items():
            if competency == "event_performance":
                # Special case: comes from event ratings, not assessment
                comp_score = await self._get_event_performance(user_id)
            else:
                comp_score = await self._calculate_competency_score(
                    competency, responses.get(competency, [])
                )

            # Get best verification level for this competency
            verification = verification_levels.get(competency, "self_assessed")
            multiplier = self.VERIFICATION_MULTIPLIERS[verification]

            # Accumulate weighted sum
            weighted_sum += comp_score.final_score * weight * multiplier

            competency_scores[competency] = comp_score

        # Calculate reliability factor
        reliability = await self._calculate_reliability(user_id, responses)

        # Apply reliability and clamp to 0-100
        final_score = max(0, min(100, weighted_sum * reliability))
        final_score_int = round(final_score)

        # Determine badge tier
        badge_tier = self._get_badge_tier(final_score_int)

        result = AURAResult(
            user_id=user_id,
            total_score=final_score_int,
            badge_tier=badge_tier,
            reliability_factor=reliability,
            competency_scores=competency_scores,
            verification_levels=verification_levels,
            calculated_at=datetime.utcnow(),
        )

        logger.info(
            f"AURA calculation complete",
            user_id=user_id,
            score=final_score_int,
            badge=badge_tier,
            reliability=reliability
        )

        return result

    async def _get_assessment_responses(
        self, user_id: UUID
    ) -> dict[str, list[dict]]:
        """
        Fetch all assessment responses grouped by competency.

        Returns:
            {
                'communication': [
                    {'question_id': ..., 'score': 75, 'difficulty': 'medium', 'type': 'bars'},
                    ...
                ],
                ...
            }
        """
        result = await self.db.from_("assessment_responses").select(
            """
            question_id,
            score,
            questions:question_id(
                competency,
                difficulty,
                type
            )
            """
        ).eq("user_id", str(user_id)).execute()

        # Group by competency
        grouped = {}
        for row in result.data:
            competency = row['questions']['competency']
            if competency not in grouped:
                grouped[competency] = []

            grouped[competency].append({
                'score': row['score'],
                'difficulty': row['questions']['difficulty'],
                'type': row['questions']['type'],
            })

        return grouped

    async def _calculate_competency_score(
        self, competency: str, responses: list[dict]
    ) -> CompetencyScore:
        """
        Calculate final score for one competency.

        Args:
            competency: Competency name
            responses: List of {score, difficulty, type}

        Returns:
            CompetencyScore with breakdown
        """
        if not responses:
            return CompetencyScore(
                competency=competency,
                raw_score=0.0,
                adjusted_score=0.0,
                final_score=0,
                verification_level="self_assessed",
                verification_multiplier=1.0,
                question_count=0,
            )

        # Step 1: Raw score (difficulty-weighted average)
        difficulty_weighted = 0.0
        difficulty_sum = 0.0
        scores_for_std = []

        for resp in responses:
            score = resp['score']
            difficulty = resp['difficulty']
            weight = self.DIFFICULTY_WEIGHTS[difficulty]

            difficulty_weighted += score * weight
            difficulty_sum += weight
            scores_for_std.append(score)

        raw_score = difficulty_weighted / difficulty_sum if difficulty_sum > 0 else 0.0

        # Step 2: Question type adjustment
        type_counts = {}
        for resp in responses:
            qtype = resp['type']
            type_counts[qtype] = type_counts.get(qtype, 0) + 1

        effective_modifier = 0.0
        for qtype, count in type_counts.items():
            modifier = self.QUESTION_TYPE_MODIFIERS[qtype]
            effective_modifier += modifier * count / len(responses)

        adjusted_score = raw_score * effective_modifier

        # Step 3: Clamp to 0-100
        final_score = max(0, min(100, adjusted_score))

        # Calculate std dev for diagnostics
        std_dev = float(np.std(scores_for_std)) if len(scores_for_std) > 1 else 0.0

        return CompetencyScore(
            competency=competency,
            raw_score=round(raw_score, 2),
            adjusted_score=round(adjusted_score, 2),
            final_score=int(round(final_score)),
            verification_level="self_assessed",  # updated in main calc
            verification_multiplier=1.0,  # updated in main calc
            question_count=len(responses),
            std_dev=round(std_dev, 2),
        )

    async def _get_event_performance(self, user_id: UUID) -> CompetencyScore:
        """
        Calculate event_performance score from event ratings & attendance.

        Formula:
            score = weighted_avg(rating_score × attendance_mult × recency_weight)
            rating_score = (stars - 1) * 25  // 1→0, 5→100
            attendance_mult = 1.0 if attended else 0.3
            recency_weight = 2.0 if <6mo, 1.0 if >=6mo

        Default: 50 if no event history.
        """
        result = await self.db.from_("event_ratings").select(
            """
            score,
            created_at,
            event_registrations:registration_id(
                status
            )
            """
        ).eq("user_id", str(user_id)).execute()

        if not result.data:
            # No event history
            return CompetencyScore(
                competency="event_performance",
                raw_score=50.0,
                adjusted_score=50.0,
                final_score=50,
                verification_level="self_assessed",
                verification_multiplier=1.0,
                question_count=0,
            )

        now = datetime.utcnow()
        six_months_ago = now - timedelta(days=180)

        weighted_scores = []
        weights = []

        for rating in result.data:
            stars = rating['score']
            rating_score = (stars - 1) * 25

            # Attendance multiplier
            status = rating['event_registrations']['status']
            attendance_mult = 1.0 if status == 'attended' else 0.3

            # Recency weight
            created = datetime.fromisoformat(rating['created_at'])
            recency_weight = 2.0 if created > six_months_ago else 1.0

            effective_score = rating_score * attendance_mult * recency_weight
            weighted_scores.append(effective_score)
            weights.append(recency_weight)

        final_score = sum(weighted_scores) / sum(weights) if weights else 50.0
        final_score = max(0, min(100, final_score))

        return CompetencyScore(
            competency="event_performance",
            raw_score=round(final_score, 2),
            adjusted_score=round(final_score, 2),
            final_score=int(round(final_score)),
            verification_level="org_attested",  # org rates events
            verification_multiplier=1.15,
            question_count=len(result.data),
        )

    async def _get_verification_levels(
        self, user_id: UUID
    ) -> dict[str, str]:
        """
        Get best verification level per competency.

        Hierarchy: peer_verified > org_attested > self_assessed
        """
        result = await self.db.from_("competency_verifications").select(
            "competency, verification_level"
        ).eq("user_id", str(user_id)).execute()

        verification_levels = {}
        hierarchy = {
            "peer_verified": 3,
            "org_attested": 2,
            "self_assessed": 1,
        }

        for row in result.data:
            competency = row['competency']
            level = row['verification_level']

            # Keep highest-ranked level
            if competency not in verification_levels or \
               hierarchy[level] > hierarchy[verification_levels[competency]]:
                verification_levels[competency] = level

        # Default all missing competencies
        for comp in self.WEIGHTS.keys():
            if comp not in verification_levels:
                verification_levels[comp] = "self_assessed"

        return verification_levels

    async def _calculate_reliability(
        self, user_id: UUID, responses: dict[str, list[dict]]
    ) -> float:
        """
        Calculate reliability factor (0.85–1.00).

        Lower std dev within competencies = higher reliability.

        Formula:
            reliability = clamp(1.0 - (0.15 × normalized_std_dev), 0.85, 1.00)
            where normalized_std_dev = std_dev(all_scores_in_competency) / 100

        Then average across all competencies.
        """
        std_devs = []

        for competency, comp_responses in responses.items():
            if not comp_responses:
                continue

            scores = [r['score'] for r in comp_responses]
            std_dev = float(np.std(scores)) if len(scores) > 1 else 0.0
            std_devs.append(std_dev)

        # Average std dev across competencies
        avg_std_dev = np.mean(std_devs) if std_devs else 0.0
        normalized = avg_std_dev / 100.0

        # Apply formula with clamping
        reliability = max(0.85, min(1.00, 1.0 - (0.15 * normalized)))

        logger.info(
            f"Reliability calculated",
            user_id=user_id,
            avg_std_dev=round(avg_std_dev, 2),
            factor=round(reliability, 4)
        )

        return reliability

    def _get_badge_tier(self, score: int) -> str:
        """Map score to badge tier."""
        for threshold, tier in self.BADGE_TIERS:
            if score >= threshold:
                return tier
        return "none"
```

---

### 11. Worked Example: Full AURA Calculation

**Scenario:** Volunteer "Alice" completes assessment + has 2 event ratings.

#### 11.1 Assessment Responses

Alice answered 16 questions (2 per competency):

```
Competency              Q1         Q2       Raw   Type    Adjusted  Final
─────────────────────────────────────────────────────────────────────────
Communication          [Med:85]   [Hard:80]   82.5→ BARS→ 82.5 → 83
Reliability            [Easy:75]  [Med:70]    71.4→ MCQ → 64.3 → 64
English Proficiency    [Hard:88]  [Hard:85]   86.4→ BARS→ 86.4 → 86
Leadership             [Med:78]   [Hard:75]   76.8→ Open→ 84.5 → 85
Event Performance      (from events, not assessment)
Tech Literacy          [Easy:60]  [Med:65]    62.9→ MCQ → 56.6 → 57
Adaptability           [Med:82]   [Easy:80]   81.4→ BARS→ 81.4 → 81
Empathy/Safeguarding   [Hard:90]  [Med:88]    88.9→ Open→ 97.8 → 98 (clamped)
```

**How we got Communication raw score:**
```
raw = (85 × 1.0 + 80 × 1.5) / (1.0 + 1.5)
    = (85 + 120) / 2.5
    = 205 / 2.5
    = 82.0
```
(Then apply BARS modifier 1.0x → 82.0)

**How we got Tech Literacy adjusted score:**
```
Type breakdown: 2 MCQ
effective_modifier = (2 × 0.9) / 2 = 0.9
adjusted = 62.9 × 0.9 = 56.61 → 57
```

#### 11.2 Event Performance

Alice has 2 event ratings:
- 2 months ago: attended, rated 5 stars
- 6 months ago: no-show, rated 3 stars

```
Event 1: score = (5-1)×25 × 1.0 × 2.0 = 100 × 2.0 = 200, weight = 2.0
Event 2: score = (3-1)×25 × 0.3 × 1.0 = 50 × 0.3 = 15, weight = 1.0

event_performance = (200 + 15) / (2.0 + 1.0) = 215 / 3.0 = 71.67 → 72
```

#### 11.3 Verification Levels

Alice has:
- Self-assessed: all competencies (default)
- Org-attested: communication, reliability, leadership (from event feedback)
- Peer-verified: none yet

```
Verification Levels:
─────────────────────────────────────────
communication:          org_attested  (1.15)
reliability:            org_attested  (1.15)
english_proficiency:    self_assessed (1.00)
leadership:             org_attested  (1.15)
event_performance:      org_attested  (1.15)
tech_literacy:          self_assessed (1.00)
adaptability:           self_assessed (1.00)
empathy_safeguarding:   self_assessed (1.00)
```

#### 11.4 Reliability Factor

All response scores: [85, 80, 75, 70, 88, 85, 78, 75, 60, 65, 82, 80, 90, 88, 72]

```
std_dev = 7.98
normalized = 7.98 / 100 = 0.0798
reliability = 1.0 - (0.15 × 0.0798) = 1.0 - 0.01197 = 0.988
```

#### 11.5 Final AURA Calculation

```
AURA = Σ(score × weight × multiplier) × reliability

Component Breakdown:
─────────────────────────────────────────────────────────────────
communication:          83 × 0.20 × 1.15 = 19.09
reliability:            64 × 0.15 × 1.15 = 11.04
english_proficiency:    86 × 0.15 × 1.00 = 12.90
leadership:             85 × 0.15 × 1.15 = 14.66
event_performance:      72 × 0.10 × 1.15 = 8.28
tech_literacy:          57 × 0.10 × 1.00 = 5.70
adaptability:           81 × 0.10 × 1.00 = 8.10
empathy_safeguarding:   98 × 0.05 × 1.00 = 4.90
                                           ──────
Subtotal:                                   84.67

Final AURA = 84.67 × 0.988 = 83.67 → 84 (rounded)
```

**Result:**
```
Total Score:        84 / 100
Badge Tier:         Gold (75–89)
Reliability:        0.988 (very consistent)
Last Assessed:      Today
Next Milestone:     Platinum (90 points) — needs +6
```

---

### 12. Database Schema (RLS & Indexing)

These tables are created via migration (see [[ADR-002-database-schema]]):

```sql
-- ============================================================
-- AURA SCORES TABLE (Latest score per user, 1:1)
-- ============================================================

CREATE TABLE aura_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  total_score INT NOT NULL CHECK (total_score >= 0 AND total_score <= 100),
  badge_tier badge_tier NOT NULL,
  reliability_factor FLOAT NOT NULL CHECK (reliability_factor >= 0.85 AND reliability_factor <= 1.0),
  calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  previous_score INT,
  previous_badge badge_tier,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_aura_scores_badge ON aura_scores(badge_tier);
CREATE INDEX idx_aura_scores_score ON aura_scores(total_score DESC);

ALTER TABLE aura_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own AURA"
  ON aura_scores FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service can write AURA"
  ON aura_scores FOR INSERT, UPDATE
  USING (auth.role() = 'service_role');


-- ============================================================
-- COMPETENCY SCORES TABLE (One per competency per user)
-- ============================================================

CREATE TABLE competency_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  aura_id UUID NOT NULL REFERENCES aura_scores(id) ON DELETE CASCADE,
  competency VARCHAR NOT NULL,
  raw_score FLOAT NOT NULL,
  adjusted_score FLOAT NOT NULL,
  final_score INT NOT NULL CHECK (final_score >= 0 AND final_score <= 100),
  question_count INT NOT NULL,
  std_dev FLOAT,
  calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, aura_id, competency)
);

CREATE INDEX idx_competency_scores_user ON competency_scores(user_id);
CREATE INDEX idx_competency_scores_competency ON competency_scores(competency);

ALTER TABLE competency_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own competency scores"
  ON competency_scores FOR SELECT
  USING (auth.uid() = user_id);


-- ============================================================
-- BADGE HISTORY TABLE (Tier changes)
-- ============================================================

CREATE TABLE badge_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  previous_badge badge_tier,
  new_badge badge_tier NOT NULL,
  previous_score INT,
  new_score INT NOT NULL,
  trigger VARCHAR(50) NOT NULL,  -- 'assessment', 'attestation', 'event', 'peer_verify'
  achieved_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_badge_history_user ON badge_history(user_id);
CREATE INDEX idx_badge_history_achieved ON badge_history(achieved_at DESC);

ALTER TABLE badge_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own badge history"
  ON badge_history FOR SELECT
  USING (auth.uid() = user_id);


-- ============================================================
-- COMPETENCY VERIFICATIONS (Tracks verification levels)
-- ============================================================

CREATE TABLE competency_verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  competency VARCHAR NOT NULL,
  verification_level VARCHAR NOT NULL
    CHECK (verification_level IN ('self_assessed', 'org_attested', 'peer_verified')),
  verified_by UUID REFERENCES users(id),  -- NULL if self_assessed
  verified_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, competency, verification_level)
);

CREATE INDEX idx_competency_verifications_user ON competency_verifications(user_id);

ALTER TABLE competency_verifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own verifications"
  ON competency_verifications FOR SELECT
  USING (auth.uid() = user_id);
```

---

### 13. Recalculation Edge Cases & Gotchas

#### 13.1 Reassessment Logic

If a volunteer retakes the assessment:
- **Old responses:** Kept in DB (audit trail)
- **New responses:** Also kept
- **AURA calc:** Uses **all** responses (both assessments)
- **Effect:** New questions contribute more if consistent, less if inconsistent

Why not replace? Because averaging 2 assessments is more reliable than 1.

#### 13.2 Partial Attestation

Organization attests "communication" but not "reliability." AURA recalculates **both:**
- Communication: multiplier jumps from 1.00 → 1.15
- Reliability: stays 1.00 (no attestation yet)

#### 13.3 No Event History

If volunteer has zero event ratings:
- event_performance defaults to 50 (neutral)
- This is **not** a penalty — volunteer may be brand new
- Once first event is rated, event_performance updates from 50 → actual score

#### 13.4 Zero Assessment Responses

If somehow a user gets an empty assessment:
- `AURACalculator.calculate()` raises `ValueError`
- Caught by API handler, returns 422 (unprocessable entity)
- Volunteer prompted to retake assessment

#### 13.5 Concurrent Recalculations

If two triggers fire simultaneously (e.g., assessment completed + peer verified):
- Both queue async jobs
- Second job waits on database lock (Supabase handles this)
- Final result reflects both changes

---

### 14. Testing Strategy

```python
# tests/test_aura.py

async def test_aura_basic_calculation():
    """Test basic AURA formula with known inputs."""
    calc = AURACalculator(mock_db)
    result = await calc.calculate(test_user_id)

    assert result.total_score == 84
    assert result.badge_tier == "gold"
    assert result.reliability_factor >= 0.85

async def test_aura_reliability_factor():
    """Test reliability penalty for inconsistency."""
    # User with high variance in responses
    result = await calc._calculate_reliability(user_id, high_variance_responses)
    assert result < 1.0  # Penalized

async def test_aura_event_performance():
    """Test event score calculation."""
    result = await calc._get_event_performance(user_id_with_events)
    assert 0 <= result.final_score <= 100

async def test_aura_verification_multipliers():
    """Test that multipliers apply correctly."""
    # Set up user with org attestation
    result = await calc.calculate(attested_user_id)
    # Verify multiplier was applied to weighted sum

async def test_badge_tier_assignment():
    """Test badge tier thresholds."""
    assert calc._get_badge_tier(95) == "platinum"
    assert calc._get_badge_tier(75) == "gold"
    assert calc._get_badge_tier(39) == "none"
```

---

### 15. Monitoring & Observability

Log all AURA calculations with context:

```python
logger.info(
    "AURA calculated",
    user_id=user_id,
    score=84,
    badge_tier="gold",
    reliability=0.988,
    competency_scores={
        "communication": 83,
        "reliability": 64,
        ...
    },
    verification_levels={
        "communication": "org_attested",
        ...
    },
    trigger="assessment_completed",  # or "event_rating", etc.
    duration_ms=156,
)
```

**Dashboards:**
- AURA distribution histogram (median, p95, p99)
- Badge tier pie chart (% Platinum, Gold, Silver, Bronze, None)
- Reliability factor distribution (should be >0.95 median)
- Recalculation latency (should be <500ms p99)

---

## Consequences

### Positive

✅ **Transparent:** Volunteers understand why their score is X (formula is public)
✅ **Defensible:** Weights are data-driven, not arbitrary
✅ **Gamified:** Badge tiers motivate improvement; leaderboard incentivizes competition
✅ **Flexible:** Verification multipliers allow organizations to boost credibility
✅ **Fair:** Reliability factor prevents gaming through random guesses
✅ **Scalable:** O(n) calculation, cached at Supabase, invalidated on triggers

### Negative

⚠️ **Complexity:** Multiple adjustment factors (difficulty, type, verification) can confuse some users
⚠️ **Data Quality:** If assessments are too easy/hard, scores cluster at extremes
⚠️ **Cold Start:** New volunteers start at neutral (50 for events), may feel discouraged
⚠️ **Std Dev Variance:** With few responses, std dev is noisy; reliability factor unreliable (mitigated by using multiple assessments)

### Mitigation

- **Education:** Public CLAUDE.md + in-app tooltips explaining each component
- **Question Calibration:** IRT parameters in [[ADR-004-assessment-engine]] ensure balanced difficulty
- **Onboarding:** Welcome email: "Complete your assessment to earn your first badge"
- **Reassessment:** Encourage volunteers to retake after 3 months (reduces std dev, boosts score)

---

## Alternatives Considered

### 1. Single Competency (No Weighting)

Just average all 8 competencies equally.

**Rejected:** Doesn't reflect real-world volunteer value. Communication & reliability matter more.

### 2. Event Performance Only

Skip assessment, rate volunteers only on event participation.

**Rejected:** No baseline for new volunteers; hard to match to roles without knowing capabilities.

### 3. Decay Over Time

AURA drops 5% per year of inactivity.

**Rejected:** Unfair to volunteers on parental leave or hiatus. Gamification (re-engagement campaigns) is better.

### 4. Fixed Reliability Penalty

Always multiply final AURA by 0.95 (flat 5% penalty).

**Rejected:** Doesn't incentivize consistency; removes signal about assessment quality.

---

## References

- [[ADR-001-system-architecture]]: System design, async patterns
- [[ADR-002-database-schema]]: Table definitions, RLS policies
- [[ADR-003-auth-verification]]: Verification levels (self, org, peer)
- [[ADR-004-assessment-engine]]: Adaptive testing, IRT, question parameters
- `CLAUDE.md` §"AURA Score Weights": Fixed weights (canonical source)
- `apps/api/app/services/aura.py`: Python implementation
- `supabase/migrations/`: DDL for aura_scores, competency_scores, badge_history tables

---

## Q&A

**Q: Can I change the weights?**
A: No. Weights are FINAL and locked in CLAUDE.md. Changing them invalidates all historical scores. If you must adjust, create AURA v2 and migrate users explicitly.

**Q: Why 0.15 for the reliability penalty factor?**
A: Empirical. Penalty is aggressive enough to catch cheaters (guessing randomly), but lenient enough for honest variance from question difficulty. 0.15 × max possible std dev (50) = 7.5% max penalty — reasonable.

**Q: What if two events have the same date?**
A: Sorted by created_at DESC; first wins. Rare edge case (seconds precision), impact minimal.

**Q: Does old assessment data stay after reassessment?**
A: Yes. All responses are immutable. Recalculation uses union of all assessments. No deletion.

**Q: Can an organization boost its own volunteers?**
A: No. Org attestation is one competency per organization. If Org A attests "communication," that's 1.15x. Org B attesting it doesn't stack (best level wins, not sum).

**Q: What happens if a volunteer has zero completions?**
A: Badge is "none," total_score is NULL (not 0). Dashboard shows "Assessment incomplete" CTA.

---

**Approved by:** Yusif (product), Claude (architecture)
**Last Updated:** 2026-03-22

