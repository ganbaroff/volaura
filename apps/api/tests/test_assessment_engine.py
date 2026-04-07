"""Unit tests for IRT/CAT engine, anti-gaming, BARS, and AURA calculation."""

import pytest

from app.core.assessment import antigaming
from app.core.assessment.aura_calc import (
    calculate_overall,
    get_badge_tier,
    is_elite,
)
from app.core.assessment.bars import _aggregate, _keyword_fallback, _parse_json_scores
from app.core.assessment.engine import (
    CATState,
    ItemRecord,
    select_next_item,
    should_stop,
    submit_response,
    theta_to_score,
)


# ── CATState serialisation ────────────────────────────────────────────────────

def test_cat_state_round_trip():
    state = CATState(theta=0.5, theta_se=0.4)
    state.items.append(ItemRecord(
        question_id="q1", irt_a=1.0, irt_b=0.0, irt_c=0.0,
        response=1, raw_score=0.8, response_time_ms=5000,
    ))
    restored = CATState.from_dict(state.to_dict())
    assert restored.theta == 0.5
    assert restored.theta_se == 0.4
    assert len(restored.items) == 1
    assert restored.items[0].question_id == "q1"
    assert restored.items[0].raw_score == 0.8


# ── theta_to_score ────────────────────────────────────────────────────────────

def test_theta_zero_maps_to_50():
    score = theta_to_score(0.0)
    assert abs(score - 50.0) < 0.1


def test_theta_positive_above_50():
    assert theta_to_score(2.0) > 50.0


def test_theta_negative_below_50():
    assert theta_to_score(-2.0) < 50.0


def test_theta_clamped():
    assert theta_to_score(100.0) <= 100.0
    assert theta_to_score(-100.0) >= 0.0


# ── select_next_item ──────────────────────────────────────────────────────────

MOCK_QUESTIONS = [
    {"id": f"q{i}", "irt_a": 1.0, "irt_b": float(i - 3), "irt_c": 0.0,
     "question_type": "mcq", "question_en": f"Q{i}", "question_az": f"Q{i}az",
     "options": None, "competency_id": "comp1"}
    for i in range(6)
]


def test_select_first_item_with_empty_state():
    state = CATState()
    q = select_next_item(state, MOCK_QUESTIONS)
    assert q is not None
    assert q["id"] in {m["id"] for m in MOCK_QUESTIONS}


def test_select_skips_answered():
    state = CATState()
    state.items.append(ItemRecord(
        question_id="q0", irt_a=1.0, irt_b=-3.0, irt_c=0.0,
        response=1, raw_score=1.0, response_time_ms=5000,
    ))
    q = select_next_item(state, MOCK_QUESTIONS)
    assert q is not None
    assert q["id"] != "q0"


def test_select_returns_none_when_all_answered():
    state = CATState()
    for q in MOCK_QUESTIONS:
        state.items.append(ItemRecord(
            question_id=q["id"], irt_a=1.0, irt_b=0.0, irt_c=0.0,
            response=1, raw_score=1.0, response_time_ms=5000,
        ))
    result = select_next_item(state, MOCK_QUESTIONS)
    assert result is None


# ── submit_response ───────────────────────────────────────────────────────────

def test_submit_response_appends_item():
    state = CATState()
    state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.8, 5000)
    assert len(state.items) == 1
    assert state.items[0].question_id == "q1"
    assert state.items[0].response == 1  # 0.8 >= 0.5 → binary 1


def test_submit_response_binary_threshold():
    state = CATState()
    state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.3, 5000)
    assert state.items[0].response == 0  # 0.3 < 0.5 → binary 0


def test_submit_response_updates_theta():
    state = CATState()
    # 5 correct answers on hard items (b=2.0) → theta should rise above initial 0
    for i in range(5):
        state = submit_response(state, f"q{i}", 1.0, 2.0, 0.0, 1.0, 5000)
    assert state.theta > 0.0


# ── should_stop ───────────────────────────────────────────────────────────────

def test_should_stop_max_items():
    state = CATState()
    for i in range(20):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped, reason = should_stop(state)
    assert stopped is True
    assert reason == "max_items"


def test_should_stop_se_threshold():
    state = CATState(theta=0.5, theta_se=0.2)
    # Add enough items to pass MIN_ITEMS_BEFORE_SE_STOP check
    for i in range(5):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped, reason = should_stop(state)
    assert stopped is True
    assert reason == "se_threshold"


def test_should_not_stop_early():
    state = CATState(theta=0.5, theta_se=0.5)
    for i in range(2):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped, _ = should_stop(state)
    assert stopped is False


# ── Energy-adaptive stopping (Constitution Law 2) ─────────────────────────────

def test_should_stop_low_energy_max_5_items():
    """Low energy caps assessment at 5 items (vs 20 for full)."""
    state = CATState(theta=0.5, theta_se=0.6)  # high SE so only max_items can stop
    for i in range(5):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped, reason = should_stop(state, energy_level="low")
    assert stopped is True
    assert reason == "max_items"


def test_should_stop_mid_energy_max_12_items():
    """Mid energy caps at 12 items."""
    state = CATState(theta=0.5, theta_se=0.6)
    for i in range(12):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped, reason = should_stop(state, energy_level="mid")
    assert stopped is True
    assert reason == "max_items"


def test_should_not_stop_low_energy_at_4_items():
    """Low energy: still running at 4 items if SE high."""
    state = CATState(theta=0.5, theta_se=0.7)
    for i in range(4):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped, _ = should_stop(state, energy_level="low")
    assert stopped is False


def test_low_energy_lax_se_threshold():
    """Low energy: SE < 0.5 triggers stop after 3 items (vs 0.3 after 5 for full)."""
    state = CATState(theta=0.5, theta_se=0.45)
    for i in range(3):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped, reason = should_stop(state, energy_level="low")
    assert stopped is True
    assert reason == "se_threshold"


def test_full_energy_requires_tighter_se():
    """Full energy: SE 0.45 is NOT enough to stop (needs < 0.3)."""
    state = CATState(theta=0.5, theta_se=0.45)
    for i in range(5):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped, _ = should_stop(state, energy_level="full")
    assert stopped is False


def test_unknown_energy_defaults_to_full():
    """Safety: invalid energy_level falls back to full profile."""
    state = CATState(theta=0.5, theta_se=0.35)
    for i in range(5):
        state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 1.0, 5000))
    stopped_unknown, _ = should_stop(state, energy_level="ultra_mega")
    stopped_full, _ = should_stop(state, energy_level="full")
    assert stopped_unknown == stopped_full  # Both should be False (SE 0.35 > 0.3)


# ── Anti-gaming ───────────────────────────────────────────────────────────────

def test_no_flags_for_clean_answers():
    # Non-alternating, varied pattern with genuinely varied timing (humans aren't robots)
    # S8.2: Using uniform timing like 10_000 for all answers now correctly triggers
    # is_time_clustered (CV=0). Real answers have natural variance.
    responses = [1, 1, 0, 1, 0, 0]
    timings = [8_000, 15_000, 6_000, 12_000, 9_000, 20_000]  # natural variance, CV ≈ 0.43
    answers = [
        {"response_time_ms": t, "response": r, "raw_score": 0.7}
        for r, t in zip(responses, timings)
    ]
    signal = antigaming.analyse(answers)
    assert signal.overall_flag is False
    assert signal.penalty_multiplier == 1.0


def test_rushing_flag():
    answers = [{"response_time_ms": 500, "response": 1, "raw_score": 1.0} for _ in range(6)]
    signal = antigaming.analyse(answers)
    assert signal.rushed_count == 6
    assert signal.overall_flag is True


def test_alternating_pattern_flag():
    # Strict 10101010... pattern
    answers = [{"response_time_ms": 10_000, "response": i % 2, "raw_score": 0.5} for i in range(8)]
    signal = antigaming.analyse(answers)
    assert signal.is_alternating is True
    assert signal.overall_flag is True


def test_all_identical_flag():
    answers = [{"response_time_ms": 10_000, "response": 1, "raw_score": 1.0} for _ in range(10)]
    signal = antigaming.analyse(answers)
    assert signal.is_all_identical is True


def test_check_answer_timing_valid():
    result = antigaming.check_answer_timing(10_000)
    assert result["valid"] is True


def test_check_answer_timing_too_fast():
    result = antigaming.check_answer_timing(1_000)
    assert result["valid"] is False


# ── BARS helpers ──────────────────────────────────────────────────────────────

def test_parse_json_scores_valid():
    raw = '{"active_listening": 0.8, "empathy": 0.6}'
    scores = _parse_json_scores(raw)
    assert scores is not None
    assert abs(scores["active_listening"] - 0.8) < 0.01
    assert abs(scores["empathy"] - 0.6) < 0.01


def test_parse_json_scores_clamped():
    raw = '{"x": 1.5, "y": -0.2}'
    scores = _parse_json_scores(raw)
    assert scores["x"] == 1.0
    assert scores["y"] == 0.0


def test_parse_json_scores_strips_markdown():
    raw = "```json\n{\"a\": 0.7}\n```"
    scores = _parse_json_scores(raw)
    assert scores is not None
    assert abs(scores["a"] - 0.7) < 0.01


def test_keyword_fallback_partial_match():
    concepts = [{"name": "listening", "keywords": ["listen", "hear", "attentive"]}]
    scores = _keyword_fallback("I always listen carefully", concepts)
    assert scores["listening"] > 0.0


def test_keyword_fallback_no_keywords_defaults_half():
    concepts = [{"name": "empathy", "keywords": []}]
    scores = _keyword_fallback("anything", concepts)
    assert scores["empathy"] == 0.5


def test_aggregate_weighted():
    scores = {"a": 0.8, "b": 0.4}
    concepts = [{"name": "a", "weight": 0.6}, {"name": "b", "weight": 0.4}]
    result = _aggregate(scores, concepts)
    expected = 0.8 * 0.6 + 0.4 * 0.4
    assert abs(result - expected) < 0.001


# ── AURA calc ─────────────────────────────────────────────────────────────────

def test_calculate_overall_all_zeros():
    assert calculate_overall({}) == 0.0


def test_calculate_overall_all_100():
    scores = {slug: 100.0 for slug in [
        "communication", "reliability", "english_proficiency", "leadership",
        "event_performance", "tech_literacy", "adaptability", "empathy_safeguarding",
    ]}
    assert calculate_overall(scores) == 100.0


def test_calculate_overall_partial():
    scores = {"communication": 100.0}  # weight 0.20
    result = calculate_overall(scores)
    assert abs(result - 20.0) < 0.01


def test_get_badge_tier():
    assert get_badge_tier(92.0) == "platinum"
    assert get_badge_tier(80.0) == "gold"
    assert get_badge_tier(65.0) == "silver"
    assert get_badge_tier(45.0) == "bronze"
    assert get_badge_tier(30.0) == "none"


def test_is_elite_true():
    scores = {slug: 80.0 for slug in [
        "communication", "reliability", "english_proficiency", "leadership",
        "event_performance", "tech_literacy", "adaptability", "empathy_safeguarding",
    ]}
    assert is_elite(80.0, scores) is True


def test_is_elite_false_low_overall():
    scores = {slug: 80.0 for slug in ["communication", "reliability"]}
    assert is_elite(70.0, scores) is False


def test_is_elite_false_not_enough_competencies():
    scores = {"communication": 80.0}  # only 1 competency at 75+
    assert is_elite(80.0, scores) is False
