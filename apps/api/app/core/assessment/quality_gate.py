"""Quality Gate for assessment question design.

Three independent checks that EVERY question must pass before entering the question bank:

1. ``compute_grs`` — Gaming Resistance Score (0–1): measures how easily a question
   can be gamed by keyword stuffing or pattern-matching without real understanding.
   Threshold: 0.6 (questions below this are flagged for revision).

2. ``run_adversarial_gate`` — Generates 3 canonical attack answer styles and scores
   them via the ``keyword_fallback`` evaluator.  If ANY attack answer scores above 0.4,
   the question is too easy to game and fails.

3. ``run_quality_checklist`` — 10-point structural checklist.  All checks must pass.
   Internally calls ``compute_grs`` and ``run_adversarial_gate``.

Design rationale:
- GRS is synchronous — used in bulk question audits without LLM cost.
- Adversarial gate uses ``keyword_fallback`` intentionally: if even the dumbest
  evaluator (keyword matching) can be tricked, the LLM evaluator definitely can.
- The checklist produces a structured report so question authors know exactly
  what to fix.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.core.assessment.bars import _aggregate, _keyword_fallback

# ── Constants ─────────────────────────────────────────────────────────────────

GRS_THRESHOLD = 0.6
"""Minimum acceptable Gaming Resistance Score."""

ADVERSARIAL_GATE_THRESHOLD = 0.4
"""If ANY attack answer scores above this, the question fails the adversarial gate."""

_MIN_NARRATIVE_WORD_COUNT = 20
"""Question text must contain at least this many words to require narrative context."""

_MIN_KEYWORD_COUNT = 2
"""Minimum keywords per concept for adequate coverage."""

_MAX_SINGLE_WORD_FRACTION = 0.5
"""If more than this fraction of keywords are single words, penalise GRS."""


# ── 1. Gaming Resistance Score ────────────────────────────────────────────────


def compute_grs(question: dict[str, Any]) -> float:
    """Compute the Gaming Resistance Score (GRS) for a question.

    GRS measures how resistant a question is to keyword-stuffing attacks.
    A score near 1.0 means the question requires genuine narrative demonstration
    of competency; a score near 0.0 means keyword lists alone can score highly.

    Penalties applied:
    - Single-word keywords:  -0.12 per concept that has >50% single-word keywords
    - Keyword equals concept name exactly: -0.25 (trivial hint in the answer key)
    - No narrative trigger in question text: -0.30 (no scenario, no "describe/explain")
    - Low keyword count (<2 per concept): -0.12 per concept
    - Keyword appears verbatim in question text: -0.15 per occurrence (up to -0.45)

    Bonuses applied:
    - Multi-word keyword phrases: +0.10 per concept that has ≥50% multi-word keywords
    - All concepts have weight field: +0.05 (signals careful rubric design)

    Args:
        question: A question dict as stored in the DB / seed.sql.  Must contain:
            - ``expected_concepts``: list of dicts, each with at least ``name`` and
              optionally ``keywords``, ``weight``.
            - ``scenario_en`` OR ``question_en``: the question text in English.

    Returns:
        GRS float in range [0.0, 1.0].  Threshold for acceptance is 0.6.

    Example:
        >>> q_bad = {
        ...     "scenario_en": "Tell us about communication.",
        ...     "expected_concepts": [
        ...         {"name": "calm_tone", "keywords": ["calm", "tone"]},
        ...     ],
        ... }
        >>> score = compute_grs(q_bad)
        >>> score < 0.6  # should fail — no scenario, single-word keywords
        True

        >>> q_good = {
        ...     "scenario_en": (
        ...         "A frustrated delegate approaches the registration desk. "
        ...         "They speak limited English and appear confused. "
        ...         "Describe what you would do step by step."
        ...     ),
        ...     "expected_concepts": [
        ...         {"name": "calm_tone", "weight": 0.20, "keywords": ["speak slowly", "maintain eye contact", "use a gentle voice"]},
        ...         {"name": "seek_help", "weight": 0.20, "keywords": ["find a colleague", "use translation app", "ask a supervisor"]},
        ...     ],
        ... }
        >>> score = compute_grs(q_good)
        >>> score >= 0.6
        True
    """
    score = 1.0

    concepts: list[dict[str, Any]] = question.get("expected_concepts", [])
    if isinstance(concepts, str):
        # Handle JSON string (sometimes stored as text in seed data)
        import json

        try:
            concepts = json.loads(concepts)
        except Exception as parse_err:
            # Ghost-audit P1 (2026-04-15): silent empty-list → every answer
            # judged against empty rubric → anti-gaming gates weaken silently.
            # "Verified talent platform" integrity depends on this NOT being silent.
            logger.error(
                "quality_gate expected_concepts JSON parse failed — empty rubric",
                question_id=question.get("id"),
                raw_preview=str(concepts)[:200],
                error=str(parse_err)[:200],
            )
            concepts = []

    question_text: str = (question.get("scenario_en") or question.get("question_en") or "").lower()

    all_weighted = all("weight" in c for c in concepts if concepts)
    if all_weighted and concepts:
        score += 0.05

    # Per-concept penalties
    kw_in_question_hits = 0
    for concept in concepts:
        name: str = (concept.get("name") or concept.get("concept") or "").lower()
        keywords: list[str] = concept.get("keywords", [])

        # Penalty: low keyword count
        if len(keywords) < _MIN_KEYWORD_COUNT:
            score -= 0.12
            logger.debug(
                "GRS: low keyword count penalty",
                concept=name,
                keyword_count=len(keywords),
            )

        if not keywords:
            continue

        # Penalty: keyword == concept name (trivial reverse-engineering)
        if any(kw.lower() == name for kw in keywords):
            score -= 0.25
            logger.debug("GRS: keyword=concept_name penalty", concept=name)

        # Single-word vs multi-word analysis
        single_word_kws = [kw for kw in keywords if len(kw.split()) == 1]
        multi_word_kws = [kw for kw in keywords if len(kw.split()) > 1]
        single_fraction = len(single_word_kws) / len(keywords)

        if single_fraction > _MAX_SINGLE_WORD_FRACTION:
            score -= 0.12
            logger.debug(
                "GRS: single-word keyword penalty",
                concept=name,
                single_fraction=round(single_fraction, 2),
            )
        elif (len(multi_word_kws) / len(keywords)) >= _MAX_SINGLE_WORD_FRACTION:
            score += 0.10
            logger.debug("GRS: multi-word keyword bonus", concept=name)

        # Penalty: keyword appears verbatim in question text (leakage)
        for kw in keywords:
            if kw.lower() in question_text:
                kw_in_question_hits += 1

    # Cap keyword-in-question penalty at 3 hits * -0.15 = -0.45
    kw_question_penalty = min(kw_in_question_hits, 3) * 0.15
    if kw_question_penalty > 0:
        score -= kw_question_penalty
        logger.debug(
            "GRS: keyword-in-question-text penalty",
            hits=kw_in_question_hits,
            penalty=round(kw_question_penalty, 2),
        )

    # Penalty: no narrative trigger in question text
    narrative_triggers = [
        "describe",
        "explain",
        "what would you",
        "how would you",
        "walk us through",
        "give an example",
        "tell us how",
        "scenario",
        "situation",
        "imagine",
        "suppose",
    ]
    has_narrative = any(trigger in question_text for trigger in narrative_triggers)
    if not has_narrative:
        score -= 0.30
        logger.debug("GRS: no narrative trigger penalty", question_text_snippet=question_text[:80])

    return max(0.0, min(1.0, round(score, 4)))


# ── 2. Adversarial Gate ────────────────────────────────────────────────────────


def generate_attack_answers(question: dict[str, Any]) -> list[dict[str, str]]:
    """Generate 3 canonical attack answer styles for a given question.

    Attack styles:
    1. **Keyword dump**: Every keyword from expected_concepts, separated by spaces.
       Represents the most primitive gaming attempt — paste the keyword list.
    2. **Synonym flood**: Repeats each keyword 3x in a grammatical-ish sentence
       to maximise substring hit rate.
    3. **Thin narrative**: A plausible-sounding short answer that hits ~60% of
       keywords without demonstrating real understanding.

    Args:
        question: Question dict with ``expected_concepts``.

    Returns:
        List of 3 dicts, each with ``style`` (str) and ``text`` (str).

    Example:
        >>> q = {
        ...     "scenario_en": "Describe how you would handle a conflict.",
        ...     "expected_concepts": [
        ...         {"name": "active_listening", "keywords": ["listen", "hear", "acknowledge"]},
        ...     ],
        ... }
        >>> attacks = generate_attack_answers(q)
        >>> len(attacks)
        3
        >>> attacks[0]["style"]
        'keyword_dump'
    """
    concepts: list[dict[str, Any]] = question.get("expected_concepts", [])
    if isinstance(concepts, str):
        import json

        try:
            concepts = json.loads(concepts)
        except Exception as parse_err:
            # Ghost-audit P1 (2026-04-15): silent empty-list → every answer
            # judged against empty rubric → anti-gaming gates weaken silently.
            # "Verified talent platform" integrity depends on this NOT being silent.
            logger.error(
                "quality_gate expected_concepts JSON parse failed — empty rubric",
                question_id=question.get("id"),
                raw_preview=str(concepts)[:200],
                error=str(parse_err)[:200],
            )
            concepts = []

    all_keywords: list[str] = []
    for concept in concepts:
        all_keywords.extend(concept.get("keywords", []))

    # Attack 1: Raw keyword dump
    keyword_dump = " ".join(all_keywords)

    # Attack 2: Synonym flood (repeat each keyword 3x in sentence structures)
    flood_parts: list[str] = []
    for kw in all_keywords:
        flood_parts.append(f"I always use {kw}, demonstrating {kw} and applying {kw} effectively.")
    synonym_flood = " ".join(flood_parts)

    # Attack 3: Thin narrative — grabs first 60% of keywords with filler
    thin_kw_count = max(1, int(len(all_keywords) * 0.6))
    thin_keywords = all_keywords[:thin_kw_count]
    thin_parts: list[str] = []
    for kw in thin_keywords:
        thin_parts.append(f"I would {kw} the situation appropriately.")
    thin_narrative = " ".join(thin_parts)

    return [
        {"style": "keyword_dump", "text": keyword_dump},
        {"style": "synonym_flood", "text": synonym_flood},
        {"style": "thin_narrative", "text": thin_narrative},
    ]


def run_adversarial_gate(question: dict[str, Any]) -> dict[str, Any]:
    """Score all 3 attack answers via ``_keyword_fallback`` and report results.

    If ANY attack answer scores above ``ADVERSARIAL_GATE_THRESHOLD`` (0.4), the
    question fails. A question that can be gamed by pattern-matching alone is
    not measuring real competency.

    Uses ``_keyword_fallback`` intentionally: it is the most generous evaluator
    (LLM evaluators should be stricter). If keyword_fallback can be fooled,
    the question design is fundamentally broken.

    Args:
        question: Question dict with ``expected_concepts``.

    Returns:
        Dict with keys:
        - ``passed`` (bool): True if all attacks score <= threshold.
        - ``attacks`` (list): Each item has ``style``, ``text``, ``score``.
        - ``max_attack_score`` (float): Highest score across all attacks.
        - ``threshold`` (float): The gate threshold used.

    Example:
        >>> q = {
        ...     "scenario_en": "Describe a time you used active listening.",
        ...     "expected_concepts": [
        ...         {"name": "deep_listening", "keywords": [
        ...             "paraphrase what they said", "check my understanding",
        ...             "avoid interrupting the speaker"
        ...         ]},
        ...     ],
        ... }
        >>> result = run_adversarial_gate(q)
        >>> result["passed"]  # multi-word keywords resist keyword dump
        True
    """
    concepts: list[dict[str, Any]] = question.get("expected_concepts", [])
    if isinstance(concepts, str):
        import json

        try:
            concepts = json.loads(concepts)
        except Exception as parse_err:
            # Ghost-audit P1 (2026-04-15): silent empty-list → every answer
            # judged against empty rubric → anti-gaming gates weaken silently.
            # "Verified talent platform" integrity depends on this NOT being silent.
            logger.error(
                "quality_gate expected_concepts JSON parse failed — empty rubric",
                question_id=question.get("id"),
                raw_preview=str(concepts)[:200],
                error=str(parse_err)[:200],
            )
            concepts = []

    attacks = generate_attack_answers(question)
    attack_results: list[dict[str, Any]] = []
    max_score = 0.0

    question_text: str = question.get("scenario_en") or question.get("question_en") or ""

    for attack in attacks:
        # Pass question_text to activate gate 4 (scenario relevance penalty).
        # Attack answers that are pure keyword lists share minimal vocabulary
        # with the question scenario → off-topic penalty fires → score is suppressed.
        concept_scores = _keyword_fallback(attack["text"], concepts, question_text=question_text)
        composite = _aggregate(concept_scores, concepts)
        attack_results.append(
            {
                "style": attack["style"],
                "text": attack["text"][:200],  # truncate for logging
                "score": round(composite, 4),
                "concept_scores": {k: round(v, 3) for k, v in concept_scores.items()},
            }
        )
        if composite > max_score:
            max_score = composite

    passed = max_score <= ADVERSARIAL_GATE_THRESHOLD

    if not passed:
        logger.warning(
            "Adversarial gate FAILED",
            max_attack_score=round(max_score, 4),
            threshold=ADVERSARIAL_GATE_THRESHOLD,
            question_text_snippet=(question.get("scenario_en") or question.get("question_en") or "")[:80],
        )

    return {
        "passed": passed,
        "attacks": attack_results,
        "max_attack_score": round(max_score, 4),
        "threshold": ADVERSARIAL_GATE_THRESHOLD,
    }


# ── 3. Quality Checklist ──────────────────────────────────────────────────────


def run_quality_checklist(question: dict[str, Any]) -> dict[str, Any]:
    """Run the 10-point quality checklist for a question.

    All 10 checks must pass for the question to be approved.  The checklist
    applies to open-ended questions.  For MCQ, a reduced subset is applied
    (checks 1–4, 9–10 — structural checks that apply to all types).

    The 10 checks:
    1. Question has scenario_en (not empty)
    2. Question has expected_concepts (non-empty list)
    3. Every concept has at least 2 keywords
    4. Every concept has a weight field
    5. Weights sum to approximately 1.0 (±0.01)
    6. GRS >= 0.6 (gaming resistant)
    7. Adversarial gate passes (no attack answer > 0.4)
    8. Question text contains a narrative trigger
    9. No keyword appears verbatim in question text (no leakage)
    10. irt_a, irt_b, irt_c are present and within valid ranges

    Args:
        question: Full question dict as stored in the DB.

    Returns:
        Dict with keys:
        - ``passed`` (bool): True only if ALL applicable checks pass.
        - ``checks`` (list): Each item has ``id``, ``name``, ``passed``, ``detail``.
        - ``score`` (int): Count of passed checks.
        - ``total`` (int): Count of applicable checks.
        - ``grs`` (float): The computed GRS value.
        - ``adversarial`` (dict): The adversarial gate result.

    Example:
        >>> q = {
        ...     "type": "open_ended",
        ...     "scenario_en": "Describe a conflict you resolved.",
        ...     "expected_concepts": [
        ...         {"name": "empathy", "weight": 0.5, "keywords": ["perspective", "feelings", "understanding"]},
        ...         {"name": "resolution", "weight": 0.5, "keywords": ["compromise", "agreement", "solution found"]},
        ...     ],
        ...     "irt_a": 1.5, "irt_b": 0.0, "irt_c": 0.0,
        ... }
        >>> result = run_quality_checklist(q)
        >>> result["passed"]
        True
    """
    import json

    question_type = question.get("type", "open_ended")
    is_mcq = question_type in ("mcq", "multiple_choice")

    concepts: list[dict[str, Any]] = question.get("expected_concepts", [])
    if isinstance(concepts, str):
        try:
            concepts = json.loads(concepts)
        except Exception as parse_err:
            # Ghost-audit P1 (2026-04-15): silent empty-list → every answer
            # judged against empty rubric → anti-gaming gates weaken silently.
            # "Verified talent platform" integrity depends on this NOT being silent.
            logger.error(
                "quality_gate expected_concepts JSON parse failed — empty rubric",
                question_id=question.get("id"),
                raw_preview=str(concepts)[:200],
                error=str(parse_err)[:200],
            )
            concepts = []

    question_text: str = (question.get("scenario_en") or question.get("question_en") or "").lower()

    checks: list[dict[str, Any]] = []

    # ── Check 1: scenario_en present ─────────────────────────────────────────
    c1_passed = bool(question.get("scenario_en") or question.get("question_en"))
    checks.append(
        {
            "id": 1,
            "name": "scenario_en present",
            "passed": c1_passed,
            "detail": "scenario_en or question_en must be non-empty" if not c1_passed else "OK",
        }
    )

    # ── Check 2: expected_concepts non-empty ──────────────────────────────────
    c2_passed = bool(concepts)
    checks.append(
        {
            "id": 2,
            "name": "expected_concepts non-empty",
            "passed": c2_passed,
            "detail": "expected_concepts must be a non-empty list" if not c2_passed else "OK",
        }
    )

    # ── Check 3: every concept has >= 2 keywords ──────────────────────────────
    concept_kw_failures: list[str] = []
    for c in concepts:
        name = c.get("name") or c.get("concept") or "?"
        if len(c.get("keywords", [])) < _MIN_KEYWORD_COUNT:
            concept_kw_failures.append(name)
    c3_passed = len(concept_kw_failures) == 0
    checks.append(
        {
            "id": 3,
            "name": "each concept has >= 2 keywords",
            "passed": c3_passed,
            "detail": (
                f"Concepts with < {_MIN_KEYWORD_COUNT} keywords: {concept_kw_failures}" if not c3_passed else "OK"
            ),
        }
    )

    # ── Check 4: every concept has a weight field ─────────────────────────────
    missing_weight = [(c.get("name") or c.get("concept") or "?") for c in concepts if "weight" not in c]
    c4_passed = len(missing_weight) == 0
    checks.append(
        {
            "id": 4,
            "name": "all concepts have weight",
            "passed": c4_passed,
            "detail": f"Missing weight: {missing_weight}" if not c4_passed else "OK",
        }
    )

    # ── Check 5: weights sum to ~1.0 ─────────────────────────────────────────
    if concepts and all("weight" in c for c in concepts):
        weight_sum = sum(float(c["weight"]) for c in concepts)
        c5_passed = abs(weight_sum - 1.0) <= 0.01
        c5_detail = f"Sum = {round(weight_sum, 4)}, expected ~1.0" if not c5_passed else "OK"
    else:
        # Can't evaluate if weights are missing — defer to Check 4
        c5_passed = True
        c5_detail = "Skipped (weights absent — see check 4)"

    if not is_mcq:
        checks.append(
            {
                "id": 5,
                "name": "weights sum to 1.0",
                "passed": c5_passed,
                "detail": c5_detail,
            }
        )

    # ── Check 6: GRS >= 0.6 ───────────────────────────────────────────────────
    grs = compute_grs(question)
    if not is_mcq:
        c6_passed = grs >= GRS_THRESHOLD
        checks.append(
            {
                "id": 6,
                "name": f"GRS >= {GRS_THRESHOLD}",
                "passed": c6_passed,
                "detail": f"GRS = {grs}" if not c6_passed else f"GRS = {grs} (OK)",
            }
        )

    # ── Check 7: Adversarial gate ──────────────────────────────────────────────
    adversarial = run_adversarial_gate(question)
    if not is_mcq:
        c7_passed = adversarial["passed"]
        checks.append(
            {
                "id": 7,
                "name": f"adversarial gate (max attack score <= {ADVERSARIAL_GATE_THRESHOLD})",
                "passed": c7_passed,
                "detail": (
                    f"Max attack score: {adversarial['max_attack_score']}"
                    if not c7_passed
                    else f"Max attack score: {adversarial['max_attack_score']} (OK)"
                ),
            }
        )

    # ── Check 8: narrative trigger ─────────────────────────────────────────────
    if not is_mcq:
        narrative_triggers = [
            "describe",
            "explain",
            "what would you",
            "how would you",
            "walk us through",
            "give an example",
            "tell us how",
            "scenario",
            "situation",
            "imagine",
            "suppose",
        ]
        has_narrative = any(trigger in question_text for trigger in narrative_triggers)
        checks.append(
            {
                "id": 8,
                "name": "question contains narrative trigger",
                "passed": has_narrative,
                "detail": (f"No trigger found. Add: {narrative_triggers[:4]}" if not has_narrative else "OK"),
            }
        )

    # ── Check 9: no keyword leakage into question text ────────────────────────
    leaked_keywords: list[str] = []
    for concept in concepts:
        for kw in concept.get("keywords", []):
            if kw.lower() in question_text:
                leaked_keywords.append(kw)
    c9_passed = len(leaked_keywords) == 0
    checks.append(
        {
            "id": 9,
            "name": "no keyword leakage into question text",
            "passed": c9_passed,
            "detail": f"Leaked keywords: {leaked_keywords}" if not c9_passed else "OK",
        }
    )

    # ── Check 10: IRT params valid ────────────────────────────────────────────
    irt_a = question.get("irt_a")
    irt_b = question.get("irt_b")
    irt_c = question.get("irt_c")
    c10_issues: list[str] = []
    if irt_a is None:
        c10_issues.append("irt_a missing")
    elif not (0.3 <= float(irt_a) <= 3.0):
        c10_issues.append(f"irt_a={irt_a} out of range [0.3, 3.0]")
    if irt_b is None:
        c10_issues.append("irt_b missing")
    elif not (-4.0 <= float(irt_b) <= 4.0):
        c10_issues.append(f"irt_b={irt_b} out of range [-4.0, 4.0]")
    if irt_c is None:
        c10_issues.append("irt_c missing")
    elif not (0.0 <= float(irt_c) <= 0.35):
        c10_issues.append(f"irt_c={irt_c} out of range [0.0, 0.35]")
    c10_passed = len(c10_issues) == 0
    checks.append(
        {
            "id": 10,
            "name": "IRT params valid (a∈[0.3,3.0], b∈[-4,4], c∈[0,0.35])",
            "passed": c10_passed,
            "detail": "; ".join(c10_issues) if not c10_passed else "OK",
        }
    )

    passed_count = sum(1 for c in checks if c["passed"])
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "checks": checks,
        "score": passed_count,
        "total": len(checks),
        "grs": grs,
        "adversarial": adversarial,
    }
