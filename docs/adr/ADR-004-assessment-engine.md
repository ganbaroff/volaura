# ADR-004: Assessment Engine

**Status:** Accepted
**Date:** 2026-03-22
**Deciders:** Yusif (product owner), Claude (architecture)
**Related:** [[ADR-001-system-architecture]], [[ADR-002-database-schema]], [[ADR-005-aura-scoring]]

## Context

Volaura's core value is verifying volunteer quality through rigorous competency assessment. Volunteers must be evaluated across 8 competencies (communication, reliability, english_proficiency, leadership, event_performance, tech_literacy, adaptability, empathy_safeguarding) using a combination of behavioral scales, multiple choice, and LLM-evaluated open text responses.

The assessment engine must:

1. **Deliver fast, engaging assessments** in unstable WiFi (major event venue, 5000 concurrent volunteers)
2. **Prevent cheating** while remaining accessible to diverse literacy levels
3. **Provide immediate feedback** while enabling robust LLM evaluation
4. **Support offline-first design** (assessment works without connectivity)
5. **Scale to adaptive testing** via Item Response Theory (IRT) / Computerized Adaptive Testing (CAT)
6. **Be maintainable by one dev** (clear, simple question selection initially)

## Decision

### Eight Competencies with AURA Weights

The assessment evaluates 8 competencies with fixed weights (defined in [[ADR-005-aura-scoring]]):

| Competency | Weight | Question Count (MVP) | Primary Question Types |
|------------|--------|----------------------|------------------------|
| communication | 20% | 4–5 | BARS, Open Text |
| reliability | 15% | 3–4 | BARS, Open Text |
| english_proficiency | 15% | 4–5 | MCQ, Open Text |
| leadership | 15% | 4–5 | BARS, Open Text |
| event_performance | 10% | 2–3 | MCQ, Open Text |
| tech_literacy | 10% | 3–4 | MCQ, BARS |
| adaptability | 10% | 3–4 | BARS, Open Text |
| empathy_safeguarding | 5% | 2–3 | Open Text, BARS |

**Total assessment:** 25–33 questions across 40–50 minutes.

All weights are **FINAL** and must not be changed without explicit cross-organizational agreement.

---

### Three Question Types

#### 1. BARS (Behaviorally Anchored Rating Scale)

**Purpose:** Measure soft skills via realistic scenarios with behavioral anchors.

**Format:**
- 7-point scale (1–7)
- Volunteer reads a scenario, then selects the response that best matches their behavior
- Each response level is anchored with a specific behavior description

**Example (Communication):**

```
Scenario: A team member disagrees with your event plan in front of volunteers.

1. Ignores the conflict; moves forward without addressing
2. Acknowledges disagreement but doesn't engage further
3. Listens to their perspective; explains your rationale
4. Listens deeply; asks clarifying questions to understand root concern
5. Validates their concern; proposes a joint discussion offline
6. Facilitates real-time dialogue; finds common ground; proposes compromise
7. Facilitates structured dialogue; documents resolution; prevents future conflict
```

**Scoring:** Direct mapping to 0–100 scale via formula:
```
score = ((selection - 1) / 6) * 100
```

**Evaluation:** Immediate, no LLM required. Validates response is 1–7.

**Storage:** `assessment_responses.bars_score` (0–100), `bars_anchor_selected` (1–7)

---

#### 2. MCQ (Multiple Choice Questions)

**Purpose:** Assess factual knowledge (english_proficiency, tech_literacy, event_performance).

**Format:**
- 4 options per question
- One correct answer or ranked by quality
- Each option has a score weight (0.0–1.0)

**Example (English Proficiency):**

```
What is the correct plural of "person"?

A) persons      [weight: 0.4]
B) peoples      [weight: 0.1]
C) people       [weight: 1.0]  ← Correct
D) persones     [weight: 0.0]
```

**Scoring:** Immediate.
```
score = selected_option_weight * 100
```

**Storage:** `assessment_responses.mcq_score` (0–100), `mcq_option_selected` (A/B/C/D)

**Security:** Option text is sent to client, but correct answer and weights are NEVER revealed until assessment completion.

---

#### 3. Open Text (LLM-Evaluated)

**Purpose:** Assess complex reasoning, communication quality, and judgment in authentic scenarios.

**Format:**
- Volunteer writes free-form response (200–500 words recommended)
- Gemini 2.5 Flash evaluates against a rubric
- Returns structured JSON with score, reasoning, and competency signals

**Example (Leadership):**

```
Scenario: Your volunteer event has poor attendance. The team is demoralized.
Write how you would handle the situation.

Rubric:
- Does response take accountability?
- Does response propose concrete actions?
- Is tone empowering or blame-focused?
- Does response show forward-thinking?
```

**Evaluation Pipeline:**

```python
async def evaluate_open_text(
    question: Question,
    response: str,
    user_id: UUID
) -> EvaluationResult:
    """
    Evaluate volunteer response using Gemini 2.5 Flash.
    Cache at submit_answer time (NEVER re-evaluate).
    """

    prompt = f"""You are evaluating a volunteer's response for the competency: {question.competency}

Scenario: {question.content}

Rubric: {question.rubric}

Volunteer's response:
{response}

Evaluate and return ONLY valid JSON (no markdown, no extra text):
{{
    "score": <integer 0-100>,
    "reasoning": "<2-3 sentences explaining the score>",
    "competency_signals": ["<signal1>", "<signal2>", "<signal3>"],
    "red_flags": ["<concern1>" or empty array]
}}"""

    # Try Gemini 2.5 Flash first
    try:
        result = await gemini_client.generate_content(
            prompt,
            model="gemini-2.5-flash"
        )
        parsed = json.loads(result.text)

        # Validate schema
        if not (0 <= parsed.get("score", -1) <= 100):
            raise ValueError("Invalid score range")

        return EvaluationResult(
            score=parsed["score"],
            reasoning=parsed["reasoning"],
            competency_signals=parsed.get("competency_signals", []),
            red_flags=parsed.get("red_flags", []),
            model_used="gemini-2.5-flash",
            cached=False
        )

    except Exception as e:
        logger.error(
            "LLM evaluation failed",
            question_id=question.id,
            user_id=user_id,
            error=str(e)
        )

        # Fallback: Mark as pending_review, notify admin
        return EvaluationResult(
            score=None,
            reasoning="Pending manual review",
            status="pending_review",
            model_used=None,
            cached=False,
            error=str(e)
        )

@router.post("/assessments/{assessment_id}/answers")
async def submit_answer(
    assessment_id: UUID,
    answer: AnswerRequest,  # question_id, response_text (for open), etc.
    db: SupabaseUser,
    user_id: CurrentUserId
) -> AnswerResponse:
    """Submit assessment answer; LLM evaluation cached here."""

    # Fetch question
    question = await db.table("questions") \
        .select("*") \
        .eq("id", answer.question_id) \
        .single() \
        .execute()

    # Score based on type
    if question.data["question_type"] == "bars":
        score = ((answer.selection - 1) / 6) * 100

    elif question.data["question_type"] == "mcq":
        # Fetch options (with weights)
        option = answer.selected_option  # e.g., "C"
        weight = question.data["options"][option]["weight"]
        score = weight * 100

    elif question.data["question_type"] == "open_text":
        # Evaluate with Gemini, cache immediately
        evaluation = await evaluate_open_text(
            question.data,
            answer.response_text,
            user_id
        )
        score = evaluation.score if evaluation.score else None
        # Cache evaluation result
        await db.table("assessment_responses").insert({
            "assessment_id": assessment_id,
            "question_id": answer.question_id,
            "response_text": answer.response_text,
            "score": score,
            "llm_evaluation": {
                "reasoning": evaluation.reasoning,
                "competency_signals": evaluation.competency_signals,
                "red_flags": evaluation.red_flags,
                "model_used": evaluation.model_used
            },
            "evaluation_status": evaluation.status or "completed"
        }).execute()

        return AnswerResponse(
            question_id=answer.question_id,
            score=score,
            status=evaluation.status or "completed"
        )

    # Store BARS/MCQ response
    await db.table("assessment_responses").insert({
        "assessment_id": assessment_id,
        "question_id": answer.question_id,
        "score": score,
        "evaluation_status": "completed"
    }).execute()

    return AnswerResponse(
        question_id=answer.question_id,
        score=score,
        status="completed"
    )
```

**Caching:** Evaluation result is **cached at submit_answer time**. This prevents:
- Double-billing on LLM API (cost savings)
- Inconsistent scores if volunteer views result multiple times
- Cascading failures if Gemini is down later

**Storage:** `assessment_responses.llm_evaluation` (JSONB), `assessment_responses.score` (0–100 or NULL)

---

### Assessment Session Flow

```
┌────────────────────────────────────────────────────────────────────┐
│ USER STARTS ASSESSMENT                                             │
│ → Click "Start Assessment" button                                  │
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                  ┌────────────────────────────┐
                  │ POST /assessments/start     │
                  │                            │
                  │ Backend:                   │
                  │ • Create assessment record │
                  │   (status: in_progress)    │
                  │ • Fetch all 25–33 questions│
                  │ • Send to client           │
                  │ • Set 45-min timeout       │
                  └────────────────────────────┘
                               │
                               ▼
                  ┌────────────────────────────────────────┐
                  │ FRONTEND: PRE-FILL INDEXEDDB           │
                  │ • Store question set locally           │
                  │ • Enable offline mode                  │
                  │ • Show: "Ready to assess offline"      │
                  └────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
            (No internet)         (Online)
                    │                     │
                    ▼                     ▼
        ┌──────────────────┐   ┌──────────────────┐
        │ OFFLINE MODE     │   │ ONLINE MODE      │
        │ • Questions in   │   │ • Stream answers │
        │   IndexedDB      │   │   to backend     │
        │ • Answers queued │   │ • Real-time      │
        │   locally        │   │   scoring        │
        └──────────────────┘   └──────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
              (For each question: 1–33)
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ GET /assessments/{id}/next-q     │
                │                                  │
                │ Algorithm (MVP v1):              │
                │ • Select by competency balance   │
                │ • Apply difficulty trajectory    │
                │ • Exclude already-answered       │
                │ • Return: question + metadata    │
                └──────────────────────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ FRONTEND: DISPLAY QUESTION       │
                │ • Load from IndexedDB (offline)  │
                │ • or fetch fresh (online)        │
                │ • Show timer: 60s–300s           │
                └──────────────────────────────────┘
                               │
                    (Volunteer responds)
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ POST /assessments/{id}/answers    │
                │                                  │
                │ For BARS/MCQ: immediate score    │
                │ For Open Text: Gemini eval       │
                │  (cached at submit time)         │
                │                                  │
                │ Returns: score, feedback         │
                └──────────────────────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ FRONTEND: SHOW FEEDBACK          │
                │ • Display score (0–100)          │
                │ • Show brief explanation         │
                │ • "Next Question" button         │
                └──────────────────────────────────┘
                               │
                    (Loop until all answered)
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ POST /assessments/{id}/complete   │
                │                                  │
                │ Backend:                         │
                │ • Calculate competency scores    │
                │ • Compute AURA composite         │
                │ • Assign badge tier              │
                │ • Generate result card           │
                │ • Trigger "score_ready" email    │
                │ • Set status: completed          │
                └──────────────────────────────────┘
                               │
                               ▼
         ┌─────────────────────────────────────────┐
         │ FRONTEND: RESULTS DASHBOARD             │
         │ • Display AURA score + badge            │
         │ • Competency breakdown chart (radar)    │
         │ • Share card generation (LinkedIn, etc) │
         │ • "View Public Profile" link            │
         └─────────────────────────────────────────┘
```

---

### Question Selection Algorithm (MVP Phase 1)

**Approach:** Difficulty-stratified random selection with competency balancing.

```python
async def get_next_question(
    assessment_id: UUID,
    db: SupabaseUser
) -> Question:
    """
    Select next question for assessment.

    MVP strategy: Balance competency coverage + adaptive difficulty.
    """

    # Fetch assessment session
    assessment = await db.table("assessments") \
        .select("*") \
        .eq("id", assessment_id) \
        .single() \
        .execute()

    # Get already-answered questions
    answered = await db.table("assessment_responses") \
        .select("question_id") \
        .eq("assessment_id", assessment_id) \
        .execute()
    answered_ids = {r["question_id"] for r in answered.data}

    # Count responses per competency
    responses = await db.table("assessment_responses") \
        .select("questions(competency), score") \
        .eq("assessment_id", assessment_id) \
        .execute()

    competency_counts = {}
    competency_avg_scores = {}
    for r in responses.data:
        comp = r["questions"]["competency"]
        competency_counts[comp] = competency_counts.get(comp, 0) + 1
        if comp not in competency_avg_scores:
            competency_avg_scores[comp] = []
        if r["score"] is not None:
            competency_avg_scores[comp].append(r["score"])

    # Calculate which competency needs more coverage
    target_per_competency = {
        "communication": 5,
        "reliability": 4,
        "english_proficiency": 5,
        "leadership": 5,
        "event_performance": 3,
        "tech_literacy": 4,
        "adaptability": 4,
        "empathy_safeguarding": 3
    }

    # Find least-covered competency
    underrepresented = min(
        target_per_competency.keys(),
        key=lambda c: competency_counts.get(c, 0)
    )

    # Determine difficulty trajectory
    # If avg score >= 75: try hard
    # If avg score < 50: try easy
    # Otherwise: medium
    avg = sum(competency_avg_scores.get(underrepresented, [0])) / \
          max(len(competency_avg_scores.get(underrepresented, [0])), 1)

    if avg >= 75:
        difficulty = "hard"
    elif avg < 50:
        difficulty = "easy"
    else:
        difficulty = "medium"

    # Fetch candidate questions
    candidates = await db.table("questions") \
        .select("*") \
        .eq("competency", underrepresented) \
        .eq("difficulty", difficulty) \
        .not_in("id", list(answered_ids)) \
        .execute()

    if not candidates.data:
        # Fallback: any difficulty for this competency
        candidates = await db.table("questions") \
            .select("*") \
            .eq("competency", underrepresented) \
            .not_in("id", list(answered_ids)) \
            .execute()

    if not candidates.data:
        # Fallback: pick from any competency
        candidates = await db.table("questions") \
            .select("*") \
            .not_in("id", list(answered_ids)) \
            .execute()

    # Return random selection
    if candidates.data:
        return random.choice(candidates.data)
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ASSESSMENT_COMPLETE",
                "message": "All questions answered"
            }
        )
```

**Properties:**
- **Fair coverage:** Ensures all 8 competencies are represented
- **Adaptive difficulty:** Adjusts based on performance (simple, effective for MVP)
- **Randomized:** Reduces memorization, prevents cheating
- **Fallback-safe:** Gracefully handles edge cases

**Future (Phase 2):** Full IRT/CAT via `adaptivetesting` Python library (Item Response Theory 2PL model, theta estimation, confidence intervals).

---

### Offline Assessment Support (Major Event Critical)

Volaura must support 5,000+ concurrent volunteers on unstable WiFi at the launch event.

**Strategy: Offline-First, Online-Sync**

#### Client-Side (Frontend)

```typescript
// On assessment start: pre-fetch all questions to IndexedDB
async function startAssessment() {
  const response = await fetch("/api/assessments/start", {
    method: "POST"
  });

  const { assessment_id, questions } = await response.json();

  // Store in IndexedDB
  const db = await openDB('volaura');
  const tx = db.transaction('questions', 'readwrite');
  for (const q of questions) {
    await tx.store.put(q);
  }

  // Mark as offline-capable
  localStorage.setItem(
    `assessment_${assessment_id}_offline`,
    JSON.stringify({
      assessment_id,
      started_at: Date.now(),
      synced_answers: []
    })
  );
}

// When user submits answer
async function submitAnswer(assessmentId, answer) {
  try {
    // Try online first
    const response = await fetch(
      `/api/assessments/${assessmentId}/answers`,
      { method: "POST", body: JSON.stringify(answer) }
    );
    return await response.json();
  } catch (err) {
    if (navigator.onLine === false || err.name === "NetworkError") {
      // Store locally
      const db = await openDB('volaura');
      await db.add('pending_answers', {
        assessment_id: assessmentId,
        answer,
        timestamp: Date.now()
      });

      // Notify user
      showToast("Answer saved offline ✓", { variant: "success" });

      // Return optimistic score
      return computeLocalScore(answer);
    } else {
      throw err;
    }
  }
}

// Background Sync API: auto-retry when back online
if ('serviceWorker' in navigator && 'SyncManager' in window) {
  async function syncAssessment(assessmentId) {
    const db = await openDB('volaura');
    const pending = await db.getAll('pending_answers');

    for (const item of pending) {
      try {
        await fetch(`/api/assessments/${item.assessment_id}/answers`, {
          method: "POST",
          body: JSON.stringify(item.answer)
        });
        await db.delete('pending_answers', item.id);
      } catch (err) {
        logger.error("Sync failed", err);
      }
    }
  }

  // Register sync when coming back online
  if (navigator.connection?.saveData === false) {
    const registration = await navigator.serviceWorker.ready;
    await registration.sync.register(`sync-assessment-${assessmentId}`);
  }
}
```

#### Server-Side (Backend)

```python
@router.post("/assessments/{assessment_id}/answers")
async def submit_answer(
    assessment_id: UUID,
    answer: AnswerRequest,
    db: SupabaseUser,
    user_id: CurrentUserId
) -> AnswerResponse:
    """
    Accept answer submission from online OR offline-synced client.
    Idempotent: if answer already exists, return existing score.
    """

    # Check if this exact answer already exists
    existing = await db.table("assessment_responses") \
        .select("id, score") \
        .eq("assessment_id", assessment_id) \
        .eq("question_id", answer.question_id) \
        .execute()

    if existing.data:
        # Already submitted; return cached score
        return AnswerResponse(
            question_id=answer.question_id,
            score=existing.data[0]["score"]
        )

    # New answer; process
    # (... scoring logic as above ...)
```

**Benefits:**
- Volunteers start assessment even if WiFi drops
- Answers queue locally; sync when back online
- No lost work
- UI shows "Answers saved offline" indicator
- Idempotent API prevents double-scoring on offline resubmit

---

### Anti-Cheating Measures

#### 1. Response Time Anomaly Detection

```python
# Track time per question
@router.post("/assessments/{assessment_id}/answers")
async def submit_answer(...):
    time_on_question = answer.submitted_at - answer.question_shown_at

    # Flag suspicion
    if answer.question_type == "open_text" and time_on_question < 3:
        logger.warning(
            "Suspiciously fast open_text response",
            user_id=user_id,
            time_seconds=time_on_question
        )
        # Mark response as low_confidence
        # Future: admin review before badge issuance
```

#### 2. Copy-Paste Detection (LLM)

```python
# In evaluate_open_text() prompt
prompt = f"""
...

Check for copy-paste or AI-generated content:
- Is the response too polished / unnaturally formal?
- Are there identical phrases to the scenario text?
- Signs of ChatGPT-like phrasing?

Return "authenticity_score" (0-100) in JSON.
"""
```

#### 3. Device Fingerprinting + Session Binding

```python
# Lightweight: browser user-agent + IP + screen resolution
@router.post("/assessments/start")
async def start_assessment(...):
    device_fingerprint = {
        "user_agent": request.headers.get("user-agent"),
        "ip": request.client.host,
        "screen": request.query_params.get("screen_res"),
        "timezone": request.query_params.get("tz")
    }

    # Store with assessment
    await db.table("assessments").insert({
        "assessment_id": ...,
        "device_fingerprint": device_fingerprint
    })

    # If user restarts assessment on different device: flag for manual review
```

#### 4. Rate Limiting + Cool-Down

```python
# Max 3 assessments per 24 hours per user
@router.post("/assessments/start")
async def start_assessment(user_id: CurrentUserId, db: SupabaseUser):
    recent = await db.table("assessments") \
        .select("id") \
        .eq("user_id", user_id) \
        .gt("created_at", f"now() - interval '24 hours'") \
        .execute()

    if len(recent.data) >= 3:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMITED",
                "message": "Max 3 assessments per 24 hours"
            }
        )

    # Check cool-down: 7 days between reassessments
    last_completed = await db.table("assessments") \
        .select("completed_at") \
        .eq("user_id", user_id) \
        .eq("status", "completed") \
        .order("completed_at", ascending=False) \
        .limit(1) \
        .execute()

    if last_completed.data:
        last_time = parse_iso(last_completed.data[0]["completed_at"])
        if now() - last_time < timedelta(days=7):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "COOL_DOWN_ACTIVE",
                    "message": f"Can reassess in {7 - (now() - last_time).days} days"
                }
            )
```

---

### Question Bank Management

#### Data Model

```sql
CREATE TABLE public.questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    competency TEXT NOT NULL,  -- e.g., "communication"
    question_type question_type NOT NULL,  -- bars, mcq, open_text
    difficulty difficulty_level NOT NULL,  -- easy, medium, hard
    content TEXT NOT NULL,  -- Scenario or question text
    rubric TEXT,  -- For open_text; scoring guidance

    -- MCQ options (only for MCQ)
    options JSONB,  -- {"A": {"text": "...", "weight": 1.0}, "B": {...}, ...}

    -- BARS anchors (only for BARS)
    bars_anchors JSONB,  -- {"1": "...", "2": "...", ..., "7": "..."}

    -- IRT parameters (for future CAT)
    irt_difficulty FLOAT DEFAULT NULL,  -- b parameter (difficulty)
    irt_discrimination FLOAT DEFAULT NULL,  -- a parameter

    -- Translations
    translations JSONB DEFAULT '{}',  -- {"en": {...}, "az": {...}}

    -- Metadata
    author_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN DEFAULT true,
    is_archived BOOLEAN DEFAULT false
);

-- Index for fast question selection
CREATE INDEX idx_questions_competency_difficulty
ON questions(competency, difficulty, is_active);
```

#### Admin Panel API

```python
@router.post("/admin/questions")
async def create_question(
    question: CreateQuestionRequest,
    db: SupabaseAdmin,
    user_id: CurrentUserId
) -> QuestionResponse:
    """Create new assessment question (admin only)."""

    # Verify admin role
    user = await get_user_role(db, user_id)
    if user.role != "admin":
        raise HTTPException(status_code=403)

    # Validate
    if question.question_type == "bars":
        assert len(question.bars_anchors) == 7
    elif question.question_type == "mcq":
        assert 3 <= len(question.options) <= 4
        assert any(opt.get("weight") == 1.0 for opt in question.options.values())

    # Insert
    result = await db.table("questions").insert({
        "competency": question.competency,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "content": question.content,
        "rubric": question.rubric,
        "bars_anchors": question.bars_anchors,
        "options": question.options,
        "author_id": user_id,
        "translations": question.translations
    }).execute()

    logger.info(
        "Question created",
        question_id=result.data[0]["id"],
        competency=question.competency
    )

    return QuestionResponse(**result.data[0])

@router.put("/admin/questions/{question_id}")
async def update_question(
    question_id: UUID,
    updates: UpdateQuestionRequest,
    db: SupabaseAdmin,
    user_id: CurrentUserId
) -> QuestionResponse:
    """Update question (author or admin only)."""

    # Verify ownership
    question = await db.table("questions") \
        .select("author_id") \
        .eq("id", question_id) \
        .single() \
        .execute()

    user_role = await get_user_role(db, user_id)
    if user_role.role != "admin" and question.data["author_id"] != user_id:
        raise HTTPException(status_code=403)

    # Update
    result = await db.table("questions") \
        .update(updates.dict(exclude_unset=True)) \
        .eq("id", question_id) \
        .execute()

    return QuestionResponse(**result.data[0])
```

---

### LLM Evaluation Pipeline

#### Gemini 2.5 Flash Configuration

```python
# app/services/llm.py

from google import genai
from loguru import logger

class LLMService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    async def evaluate_open_text(
        self,
        question: dict,
        response: str,
        user_id: UUID
    ) -> EvaluationResult:
        """
        Evaluate open-text response using Gemini 2.5 Flash.

        Returns structured JSON with score, reasoning, signals.
        """

        system_prompt = f"""You are an expert evaluator assessing volunteer competencies.
Evaluate responses on the competency: {question['competency']}

Be fair, encouraging, and constructive. Consider:
- Clarity of thought
- Evidence of the competency
- Authenticity (not copy-pasted)
- Relevance to the scenario

Return ONLY valid JSON, no markdown."""

        user_prompt = f"""Scenario: {question['content']}

Rubric for evaluation:
{question['rubric']}

Volunteer's response:
{response}

Evaluate and return JSON:
{{
    "score": <integer 0-100>,
    "reasoning": "<2-3 sentences>",
    "competency_signals": ["signal1", "signal2", "signal3"],
    "red_flags": [],
    "authenticity_score": <0-100>
}}"""

        try:
            response_obj = await self.client.aio.generate_content(
                model=self.model,
                contents=[
                    {"role": "user", "parts": [{"text": user_prompt}]}
                ],
                system_instruction=system_prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 500,
                    "response_mime_type": "application/json"
                }
            )

            # Parse response
            result_text = response_obj.text
            parsed = json.loads(result_text)

            # Validate schema
            assert 0 <= parsed["score"] <= 100
            assert isinstance(parsed["reasoning"], str)
            assert isinstance(parsed["competency_signals"], list)

            logger.info(
                "LLM evaluation succeeded",
                question_id=question["id"],
                user_id=user_id,
                score=parsed["score"]
            )

            return EvaluationResult(
                score=parsed["score"],
                reasoning=parsed["reasoning"],
                competency_signals=parsed["competency_signals"],
                red_flags=parsed.get("red_flags", []),
                authenticity_score=parsed.get("authenticity_score", 100),
                model_used="gemini-2.5-flash",
                cached=False
            )

        except (json.JSONDecodeError, KeyError, AssertionError) as e:
            logger.error(
                "LLM response validation failed",
                question_id=question["id"],
                user_id=user_id,
                error=str(e),
                raw_response=result_text[:200]
            )

            # Return pending_review
            return EvaluationResult(
                score=None,
                reasoning="Failed to parse LLM response; pending manual review",
                status="pending_review",
                model_used=None,
                cached=False
            )

        except Exception as e:
            logger.error(
                "LLM API error",
                question_id=question["id"],
                user_id=user_id,
                error=str(e)
            )

            # Fallback to pending_review
            return EvaluationResult(
                score=None,
                reasoning="LLM service temporarily unavailable; pending manual review",
                status="pending_review",
                model_used=None,
                cached=False
            )

# Dependency injection in FastAPI
@router.post("/assessments/{assessment_id}/answers")
async def submit_answer(
    ...,
    llm_service: LLMService = Depends(get_llm_service)
):
    # Use llm_service
```

---

### Assessment Completion & AURA Calculation

When a volunteer completes the assessment:

```python
@router.post("/assessments/{assessment_id}/complete")
async def complete_assessment(
    assessment_id: UUID,
    db: SupabaseUser,
    user_id: CurrentUserId
) -> AssessmentCompleteResponse:
    """
    Mark assessment complete, calculate scores, trigger notifications.
    """

    # Fetch all responses
    responses = await db.table("assessment_responses") \
        .select("*, questions(competency, question_type)") \
        .eq("assessment_id", assessment_id) \
        .execute()

    # Group scores by competency
    competency_scores = {}
    for resp in responses.data:
        comp = resp["questions"]["competency"]
        if comp not in competency_scores:
            competency_scores[comp] = []
        if resp["score"] is not None:
            competency_scores[comp].append(resp["score"])

    # Calculate mean per competency
    competency_means = {
        comp: sum(scores) / len(scores)
        for comp, scores in competency_scores.items()
        if scores
    }

    # Calculate AURA composite (see [[ADR-005-aura-scoring]])
    aura_score = calculate_aura_composite(competency_means, user_id, db)
    badge_tier = get_badge_tier(aura_score)

    # Update assessment
    await db.table("assessments").update({
        "status": "completed",
        "completed_at": now(),
        "aura_score": aura_score,
        "badge_tier": badge_tier
    }).eq("id", assessment_id).execute()

    # Insert AURA history
    await db.table("aura_scores").insert({
        "user_id": user_id,
        "assessment_id": assessment_id,
        "aura_score": aura_score,
        "badge_tier": badge_tier,
        "competency_scores": competency_means
    }).execute()

    # Trigger email notification
    await send_assessment_complete_email(user_id, aura_score, badge_tier)

    logger.info(
        "Assessment completed",
        assessment_id=assessment_id,
        user_id=user_id,
        aura_score=aura_score,
        badge_tier=badge_tier
    )

    return AssessmentCompleteResponse(
        assessment_id=assessment_id,
        aura_score=aura_score,
        badge_tier=badge_tier
    )
```

---

### Data Model References

Key tables (full schema in [[ADR-002-database-schema]]):

#### assessments

```sql
CREATE TABLE public.assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    status assessment_status DEFAULT 'in_progress',

    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,  -- 45 min timeout

    aura_score FLOAT,
    badge_tier badge_tier,

    device_fingerprint JSONB,
    ip_address INET,

    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### assessment_responses

```sql
CREATE TABLE public.assessment_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),

    -- Scoring
    score FLOAT,  -- 0–100, null if pending_review
    evaluation_status TEXT DEFAULT 'completed',  -- completed, pending_review

    -- Response data (varies by type)
    bars_selection INT,  -- 1–7
    mcq_selection CHAR(1),  -- A, B, C, D
    response_text TEXT,  -- For open_text

    -- LLM metadata (for open_text)
    llm_evaluation JSONB,  -- {score, reasoning, competency_signals, red_flags}
    llm_model_used TEXT,  -- gemini-2.5-flash, fallback note, etc.

    -- Timing
    time_on_question_seconds INT,
    submitted_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### questions

```sql
CREATE TABLE public.questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    competency TEXT NOT NULL,
    question_type question_type NOT NULL,
    difficulty difficulty_level NOT NULL,
    content TEXT NOT NULL,
    rubric TEXT,

    options JSONB,  -- For MCQ
    bars_anchors JSONB,  -- For BARS (1–7)

    irt_difficulty FLOAT,  -- For future CAT
    irt_discrimination FLOAT,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Consequences

### Positive

1. **Fast assessment:** MVP (non-adaptive) completes in 30–50 minutes; no complex algorithms to debug
2. **Offline-ready:** Event WiFi issues don't block assessment flow; IndexedDB + Background Sync handle syncing
3. **Fair & flexible:** BARS, MCQ, and LLM evaluation together measure different facets of competency
4. **Scalable:** Gemini 2.5 Flash is cheap (~$0.00075/eval), caching prevents re-evals
5. **Anti-cheat:** Device fingerprinting, time anomaly detection, LLM authenticity scoring
6. **Maintainable:** Simple random + difficulty trajectory is 100x easier than full IRT/CAT for solo dev
7. **Future-proof:** IRT parameters pre-computed in DB; adaptivetesting library drop-in when ready

### Negative

1. **Not optimal:** MVP difficulty selection is heuristic, not statistically optimal (IRT would be better)
2. **LLM dependency:** Open text eval relies on Gemini API; fallback is manual review (slow for event)
3. **No CAT logic yet:** Each question takes ~3–5 mins; full assessment can't adaptively shorten
4. **Offline score display:** Scoring visible offline is approximate (no LLM evals until sync)
5. **Cool-down friction:** 7-day wait between reassessments may frustrate some volunteers

### Mitigation

- **IRT Phase 2:** Implement CAT after MVP launch (use seed IRT parameters from literature + initial cohort calibration)
- **LLM resilience:** Pre-compute Gemini batch evals during low-traffic hours; keep fallback pool of pre-evaluated responses
- **Offline scoring:** Store "expected score" estimates locally based on question difficulty + user history
- **Cool-down policy:** Revisit after 6 months; may relax to 3–7 days based on feedback

---

## Alternatives Considered

### Option A: Full Adaptive Testing (IRT/CAT from Day 1)

| Aspect | Assessment |
|--------|-----------|
| **Accuracy** | Optimal theta estimation; typically 10–20 question assessments |
| **Implementation** | Complex; requires item calibration via Rasch analysis |
| **Solo dev feasibility** | Low; adaptivetesting library requires IRT parameters |
| **Time to launch** | +4–6 weeks (not compatible with launch event timeline) |
| **Decision** | **Rejected:** Optimize for launch speed; CAT is Phase 2 |

### Option B: Static Difficulty (No Adaptation)

| Aspect | Assessment |
|--------|-----------|
| **Simplicity** | Trivial; just randomize questions |
| **Fairness** | Low; some volunteers get harder assessment than others |
| **Game-ability** | Medium; volunteers could memorize hard questions |
| **Decision** | **Rejected:** Unfair; MVP difficulty trajectory is minimal overhead |

### Option C: Async LLM Evaluation (No Caching)

| Aspect | Assessment |
|--------|-----------|
| **Complexity** | Medium; requires job queue (Celery/Redis) |
| **Cost** | High; double-billing if score viewed multiple times |
| **UX** | Poor; no immediate feedback for open text |
| **Decision** | **Rejected:** Evaluate at submit time; cache result |

### Option D: Pure Behavioral Assessment (No LLM)

| Aspect | Assessment |
|--------|-----------|
| **Simplicity** | Maximum; BARS + MCQ only, no LLM needed |
| **Coverage** | Limited; can't assess free-form reasoning |
| **Cheating resistance** | Medium; BARS anchors are game-able |
| **Decision** | **Rejected:** Open text necessary for authenticity; LLM is cost-effective |

---

## Related Decisions

- [[ADR-001-system-architecture]]: FastAPI monolith handles assessment engine; Edge Functions not suitable for complex question selection
- [[ADR-002-database-schema]]: Full schema for assessments, questions, responses
- [[ADR-005-aura-scoring]]: Weighted composite calculation across 8 competencies
- **Future:** ADR-006 (IRT Calibration & CAT Implementation)

---

## Sign-Off

**Approved by:**
- Yusif (Product Owner, Volaura) — 2026-03-22
- Claude (Architecture, AI-assisted development) — 2026-03-22

**Next Steps:**
1. Implement MVP question bank with 80–100 questions (20+ per competency, 3 difficulty levels)
2. Seed Gemini eval rubrics with education/volunteering domain expertise
3. Deploy assessment flow to staging; test with 50 volunteers at internal event
4. Gather feedback on question clarity, time-per-question, LLM eval quality
5. Plan Phase 2 IRT calibration using initial cohort data (min 500 responses)
# Four Question Types

#### 1. BARS (Behaviorally Anchored Rating Scale)

#### 2. MCQ (Multiple Choice Questions)

#### 3. Open Text (LLM-Evaluated)

#### 4. Scenario-Based Questions
    # Add scenario-based question type
    # This will allow for more diverse and realistic question formats
