"""Comprehensive unit tests for app.core.reliability.scoring.

Covers:
  - SIGNAL_WEIGHTS sum
  - behavioral_score: defaults, all-zeros, all-ones, clamping, per-signal impact,
    overrange inputs, individual weight contributions
  - proven_score: zero events, perfect attendance, every no-show penalty type,
    coordinator rating bonus/penalty, recovery bonuses, clamping, combined effects
  - blended_score: 0 / 5+ events boundaries, each intermediate event count,
    monotonicity, negative events, large event counts
  - reliability_status: each phase boundary
  - calculate: output shape, correct status routing, value ranges
  - Edge cases: negative inputs, values > 1.0, empty no_show_types, None rating
"""

from app.core.reliability.scoring import (
    BEHAVIORAL_MAX,
    BEHAVIORAL_MIN,
    NO_SHOW_PENALTIES,
    PHASE_BLEND_START,
    PHASE_FULL_PROVEN,
    SIGNAL_WEIGHTS,
    BehavioralSignals,
    EventHistory,
    behavioral_score,
    blended_score,
    calculate,
    proven_score,
    reliability_status,
)

# ── SIGNAL_WEIGHTS ────────────────────────────────────────────────────────────


def test_signal_weights_sum_to_one():
    total = sum(SIGNAL_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"SIGNAL_WEIGHTS sum = {total}, expected 1.0"


def test_signal_weights_all_positive():
    for name, w in SIGNAL_WEIGHTS.items():
        assert w > 0, f"Weight for '{name}' must be positive"


def test_signal_weights_keys():
    expected = {
        "onboarding_velocity",
        "assessment_completion",
        "profile_completeness",
        "sjt_reliability",
        "contact_verification",
        "availability_specificity",
    }
    assert set(SIGNAL_WEIGHTS.keys()) == expected


# ── behavioral_score ──────────────────────────────────────────────────────────


def test_behavioral_all_zeros_returns_min():
    s = BehavioralSignals(
        onboarding_velocity=0.0,
        assessment_completion=0.0,
        profile_completeness=0.0,
        sjt_reliability=0.0,
        contact_verification=0.0,
        availability_specificity=0.0,
    )
    assert behavioral_score(s) == BEHAVIORAL_MIN


def test_behavioral_all_ones_returns_max():
    s = BehavioralSignals(
        onboarding_velocity=1.0,
        assessment_completion=1.0,
        profile_completeness=1.0,
        sjt_reliability=1.0,
        contact_verification=1.0,
        availability_specificity=1.0,
    )
    assert behavioral_score(s) == BEHAVIORAL_MAX


def test_behavioral_default_signals_in_range():
    """Default BehavioralSignals should produce a score in [30, 70]."""
    score = behavioral_score(BehavioralSignals())
    assert BEHAVIORAL_MIN <= score <= BEHAVIORAL_MAX


def test_behavioral_half_signals_midpoint():
    s = BehavioralSignals(
        onboarding_velocity=0.5,
        assessment_completion=0.5,
        profile_completeness=0.5,
        sjt_reliability=0.5,
        contact_verification=0.5,
        availability_specificity=0.5,
    )
    score = behavioral_score(s)
    # raw=0.5 → scaled = 30 + 0.5*(70-30) = 50.0
    assert score == 50.0


def test_behavioral_clamp_upper_over_one():
    """Values > 1.0 should clamp to BEHAVIORAL_MAX."""
    s = BehavioralSignals(
        onboarding_velocity=2.0,
        assessment_completion=2.0,
        profile_completeness=2.0,
        sjt_reliability=2.0,
        contact_verification=2.0,
        availability_specificity=2.0,
    )
    assert behavioral_score(s) == BEHAVIORAL_MAX


def test_behavioral_clamp_lower_negative():
    """Negative values should clamp to BEHAVIORAL_MIN."""
    s = BehavioralSignals(
        onboarding_velocity=-1.0,
        assessment_completion=-1.0,
        profile_completeness=-1.0,
        sjt_reliability=-1.0,
        contact_verification=-1.0,
        availability_specificity=-1.0,
    )
    assert behavioral_score(s) == BEHAVIORAL_MIN


def test_behavioral_single_signal_sjt_weight():
    """sjt_reliability has weight 0.30 — highest single signal."""
    s_high = BehavioralSignals(
        onboarding_velocity=0.0,
        assessment_completion=0.0,
        profile_completeness=0.0,
        sjt_reliability=1.0,
        contact_verification=0.0,
        availability_specificity=0.0,
    )
    s_low = BehavioralSignals(
        onboarding_velocity=0.0,
        assessment_completion=0.0,
        profile_completeness=0.0,
        sjt_reliability=0.0,
        contact_verification=0.0,
        availability_specificity=0.0,
    )
    diff = behavioral_score(s_high) - behavioral_score(s_low)
    # expected: 0.30 * (70-30) = 12.0
    assert abs(diff - 12.0) < 0.01


def test_behavioral_single_signal_profile_completeness_weight():
    """profile_completeness has weight 0.10."""
    s_high = BehavioralSignals(
        onboarding_velocity=0.0,
        assessment_completion=0.0,
        profile_completeness=1.0,
        sjt_reliability=0.0,
        contact_verification=0.0,
        availability_specificity=0.0,
    )
    s_low = BehavioralSignals(
        onboarding_velocity=0.0,
        assessment_completion=0.0,
        profile_completeness=0.0,
        sjt_reliability=0.0,
        contact_verification=0.0,
        availability_specificity=0.0,
    )
    diff = behavioral_score(s_high) - behavioral_score(s_low)
    # expected: 0.10 * 40 = 4.0
    assert abs(diff - 4.0) < 0.01


def test_behavioral_score_monotone_with_single_signal():
    """Increasing one signal while holding others constant must increase score."""
    scores = []
    for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
        s = BehavioralSignals(
            onboarding_velocity=v,
            assessment_completion=0.0,
            profile_completeness=0.0,
            sjt_reliability=0.0,
            contact_verification=0.0,
            availability_specificity=0.0,
        )
        scores.append(behavioral_score(s))
    assert scores == sorted(scores)


def test_behavioral_returns_float():
    assert isinstance(behavioral_score(BehavioralSignals()), float)


def test_behavioral_precision_two_decimal_places():
    s = BehavioralSignals(
        onboarding_velocity=0.3,
        assessment_completion=0.3,
        profile_completeness=0.3,
        sjt_reliability=0.3,
        contact_verification=0.3,
        availability_specificity=0.3,
    )
    score = behavioral_score(s)
    # round() in source rounds to 2dp — result should equal round(score, 2)
    assert score == round(score, 2)


# ── proven_score ──────────────────────────────────────────────────────────────


def test_proven_zero_events_returns_neutral():
    assert proven_score(EventHistory()) == 50.0
    assert proven_score(EventHistory(total_registered=0)) == 50.0


def test_proven_perfect_attendance_no_noshow_no_rating():
    h = EventHistory(total_registered=5, total_attended=5, total_no_shows=0)
    score = proven_score(h)
    # base=100, bonus=5 + 4*5=25 → 125 → clamped to 100
    assert score == 100.0


def test_proven_all_ghost_penalty():
    h = EventHistory(
        total_registered=5,
        total_attended=0,
        total_no_shows=5,
        no_show_types=["ghost", "ghost", "ghost", "ghost", "ghost"],
    )
    score = proven_score(h)
    # base=0, penalty=5*(-15)=-75, bonus=0 → -75 → clamped to 0
    assert score == 0.0


def test_proven_same_day_penalty():
    h_clean = EventHistory(total_registered=3, total_attended=2, total_no_shows=1)
    h_penalty = EventHistory(
        total_registered=3,
        total_attended=2,
        total_no_shows=1,
        no_show_types=["same_day"],
    )
    assert proven_score(h_penalty) < proven_score(h_clean)
    delta = proven_score(h_clean) - proven_score(h_penalty)
    assert abs(delta - abs(NO_SHOW_PENALTIES["same_day"])) < 0.01


def test_proven_within_24h_penalty():
    h_clean = EventHistory(total_registered=3, total_attended=2)
    h_penalty = EventHistory(
        total_registered=3,
        total_attended=2,
        no_show_types=["within_24h"],
    )
    delta = proven_score(h_clean) - proven_score(h_penalty)
    assert abs(delta - abs(NO_SHOW_PENALTIES["within_24h"])) < 0.01


def test_proven_within_48h_penalty():
    h_clean = EventHistory(total_registered=3, total_attended=2)
    h_penalty = EventHistory(
        total_registered=3,
        total_attended=2,
        no_show_types=["within_48h"],
    )
    delta = proven_score(h_clean) - proven_score(h_penalty)
    assert abs(delta - abs(NO_SHOW_PENALTIES["within_48h"])) < 0.01


def test_proven_advance_cancel_no_penalty():
    h_clean = EventHistory(total_registered=3, total_attended=2)
    h_advance = EventHistory(
        total_registered=3,
        total_attended=2,
        no_show_types=["advance"],
    )
    assert proven_score(h_clean) == proven_score(h_advance)


def test_proven_unknown_noshow_type_no_penalty():
    h_clean = EventHistory(total_registered=3, total_attended=2)
    h_unknown = EventHistory(
        total_registered=3,
        total_attended=2,
        no_show_types=["future_type_xyz"],
    )
    assert proven_score(h_clean) == proven_score(h_unknown)


def test_proven_empty_noshow_types():
    h = EventHistory(total_registered=3, total_attended=3, no_show_types=[])
    score = proven_score(h)
    # base=100, bonus=5+2*5=15 → 115 → clamped 100
    assert score == 100.0


def test_proven_coordinator_rating_5_bonus():
    h = EventHistory(total_registered=1, total_attended=1, coordinator_avg_rating=5.0)
    score = proven_score(h)
    # base=100, rating_delta=(5-3)*5=+10, bonus=5 → 115 → 100
    assert score == 100.0


def test_proven_coordinator_rating_1_penalty():
    h = EventHistory(total_registered=1, total_attended=1, coordinator_avg_rating=1.0)
    h_no_rating = EventHistory(total_registered=1, total_attended=1)
    assert proven_score(h) < proven_score(h_no_rating)
    # h_no_rating: base=100, bonus=5 → 105 → clamped 100
    # h_rated:     base=100 + rating_delta(1→-10) + bonus=5 → 95
    # delta = 100 - 95 = 5
    delta = proven_score(h_no_rating) - proven_score(h)
    assert abs(delta - 5.0) < 0.01


def test_proven_coordinator_rating_3_neutral():
    h_rated = EventHistory(total_registered=1, total_attended=1, coordinator_avg_rating=3.0)
    h_none = EventHistory(total_registered=1, total_attended=1, coordinator_avg_rating=None)
    assert proven_score(h_rated) == proven_score(h_none)


def test_proven_coordinator_rating_none_no_effect():
    h = EventHistory(total_registered=2, total_attended=2, coordinator_avg_rating=None)
    # base=100, bonus=5+1*5=10 → 110 → 100
    assert proven_score(h) == 100.0


def test_proven_first_event_bonus_applied():
    h1 = EventHistory(total_registered=1, total_attended=1)
    h0 = EventHistory(total_registered=1, total_attended=0, total_no_shows=1)
    # h1 should be higher due to first_event_bonus
    assert proven_score(h1) > proven_score(h0)


def test_proven_successful_attendance_bonus_per_extra():
    h1 = EventHistory(total_registered=2, total_attended=1)
    h2 = EventHistory(total_registered=2, total_attended=2)
    assert proven_score(h2) > proven_score(h1)


def test_proven_score_clamp_upper():
    h = EventHistory(
        total_registered=20,
        total_attended=20,
        total_no_shows=0,
        coordinator_avg_rating=5.0,
    )
    assert proven_score(h) == 100.0


def test_proven_score_clamp_lower():
    h = EventHistory(
        total_registered=1,
        total_attended=0,
        total_no_shows=1,
        no_show_types=["ghost"],
        coordinator_avg_rating=1.0,
    )
    # base=0, penalty=-15, rating_delta=-10 → -25 → 0
    assert proven_score(h) == 0.0


def test_proven_mixed_no_show_types():
    h = EventHistory(
        total_registered=5,
        total_attended=2,
        total_no_shows=3,
        no_show_types=["ghost", "same_day", "within_48h"],
    )
    expected_penalty = NO_SHOW_PENALTIES["ghost"] + NO_SHOW_PENALTIES["same_day"] + NO_SHOW_PENALTIES["within_48h"]
    h_clean = EventHistory(total_registered=5, total_attended=2)
    delta = proven_score(h_clean) - proven_score(h)
    assert abs(delta - abs(expected_penalty)) < 0.01


def test_proven_attendance_rate_computation():
    h = EventHistory(total_registered=4, total_attended=2)
    # base = (2/4)*100 = 50
    # bonus: attended>=1 → +5, attended>1 → +5*(2-1)=5 → total bonus=10
    # score = 50 + 10 = 60
    assert proven_score(h) == 60.0


def test_proven_returns_float():
    assert isinstance(proven_score(EventHistory()), float)


# ── blended_score ─────────────────────────────────────────────────────────────


def test_blended_zero_events_is_behavioral():
    assert blended_score(60.0, 90.0, 0) == 60.0


def test_blended_negative_events_treated_as_zero():
    assert blended_score(60.0, 90.0, -5) == 60.0


def test_blended_five_events_is_proven():
    assert blended_score(60.0, 90.0, 5) == 90.0


def test_blended_more_than_five_is_proven():
    assert blended_score(60.0, 90.0, 100) == 90.0


def test_blended_one_event_partial():
    result = blended_score(60.0, 90.0, 1)
    # t = (1-1)/(5-1) = 0 → result = 60.0
    assert result == 60.0


def test_blended_two_events_partial():
    result = blended_score(60.0, 90.0, 2)
    # t = (2-1)/4 = 0.25 → 60*(0.75) + 90*(0.25) = 45 + 22.5 = 67.5
    assert abs(result - 67.5) < 0.01


def test_blended_three_events_partial():
    result = blended_score(60.0, 90.0, 3)
    # t = 2/4 = 0.5 → 60*0.5 + 90*0.5 = 75.0
    assert abs(result - 75.0) < 0.01


def test_blended_four_events_partial():
    result = blended_score(60.0, 90.0, 4)
    # t = 3/4 = 0.75 → 60*0.25 + 90*0.75 = 15 + 67.5 = 82.5
    assert abs(result - 82.5) < 0.01


def test_blended_monotone_0_to_5():
    scores = [blended_score(40.0, 90.0, n) for n in range(6)]
    assert scores == sorted(scores), f"Not monotone: {scores}"


def test_blended_equal_scores_always_same():
    for n in range(8):
        assert blended_score(70.0, 70.0, n) == 70.0


def test_blended_behavioral_higher_than_proven():
    """If behavioral > proven, score should decrease as events increase."""
    scores = [blended_score(90.0, 40.0, n) for n in range(6)]
    assert scores == sorted(scores, reverse=True)


def test_blended_returns_float():
    assert isinstance(blended_score(50.0, 70.0, 3), float)


def test_blended_precision_two_decimal_places():
    result = blended_score(33.33, 66.67, 2)
    assert result == round(result, 2)


# ── reliability_status ────────────────────────────────────────────────────────


def test_status_zero_events_is_behavioral():
    assert reliability_status(0) == "behavioral"


def test_status_negative_events_is_behavioral():
    assert reliability_status(-1) == "behavioral"


def test_status_one_event_is_building():
    assert reliability_status(PHASE_BLEND_START) == "building"


def test_status_two_events_is_building():
    assert reliability_status(2) == "building"


def test_status_four_events_is_building():
    assert reliability_status(PHASE_FULL_PROVEN - 1) == "building"


def test_status_five_events_is_proven():
    assert reliability_status(PHASE_FULL_PROVEN) == "proven"


def test_status_ten_events_is_proven():
    assert reliability_status(10) == "proven"


def test_status_large_count_is_proven():
    assert reliability_status(9999) == "proven"


def test_status_returns_string():
    for n in range(8):
        assert isinstance(reliability_status(n), str)


# ── calculate (integration) ───────────────────────────────────────────────────


REQUIRED_KEYS = {"reliability_score", "reliability_status", "events_attended", "events_no_show"}


def test_calculate_output_shape():
    result = calculate(BehavioralSignals(), EventHistory())
    assert set(result.keys()) >= REQUIRED_KEYS


def test_calculate_new_user_behavioral_phase():
    result = calculate(BehavioralSignals(), EventHistory())
    assert result["reliability_status"] == "behavioral"
    assert result["events_attended"] == 0
    assert result["events_no_show"] == 0
    assert BEHAVIORAL_MIN <= result["reliability_score"] <= BEHAVIORAL_MAX


def test_calculate_building_phase():
    signals = BehavioralSignals(onboarding_velocity=1.0, sjt_reliability=1.0)
    history = EventHistory(total_registered=3, total_attended=2, total_no_shows=1)
    result = calculate(signals, history)
    assert result["reliability_status"] == "building"
    assert result["events_attended"] == 2


def test_calculate_proven_phase():
    signals = BehavioralSignals(
        onboarding_velocity=1.0,
        assessment_completion=1.0,
        profile_completeness=1.0,
        sjt_reliability=1.0,
        contact_verification=1.0,
        availability_specificity=1.0,
    )
    history = EventHistory(
        total_registered=5,
        total_attended=5,
        total_no_shows=0,
        coordinator_avg_rating=5.0,
    )
    result = calculate(signals, history)
    assert result["reliability_status"] == "proven"
    assert result["reliability_score"] == 100.0


def test_calculate_score_in_valid_range():
    for attended in [0, 1, 3, 5, 10]:
        h = EventHistory(total_registered=attended, total_attended=attended)
        result = calculate(BehavioralSignals(), h)
        assert 0.0 <= result["reliability_score"] <= 100.0, (
            f"Score out of range for attended={attended}: {result['reliability_score']}"
        )


def test_calculate_events_attended_passthrough():
    h = EventHistory(total_registered=7, total_attended=6, total_no_shows=1)
    result = calculate(BehavioralSignals(), h)
    assert result["events_attended"] == 6
    assert result["events_no_show"] == 1


def test_calculate_zero_events_uses_behavioral_score():
    signals_high = BehavioralSignals(
        onboarding_velocity=1.0,
        assessment_completion=1.0,
        profile_completeness=1.0,
        sjt_reliability=1.0,
        contact_verification=1.0,
        availability_specificity=1.0,
    )
    signals_low = BehavioralSignals(
        onboarding_velocity=0.0,
        assessment_completion=0.0,
        profile_completeness=0.0,
        sjt_reliability=0.0,
        contact_verification=0.0,
        availability_specificity=0.0,
    )
    r_high = calculate(signals_high, EventHistory())
    r_low = calculate(signals_low, EventHistory())
    assert r_high["reliability_score"] > r_low["reliability_score"]


def test_calculate_five_events_ignores_behavioral():
    """At 5+ events, different behavioral signals should not change final score."""
    history = EventHistory(total_registered=5, total_attended=5)
    r1 = calculate(BehavioralSignals(), history)
    r2 = calculate(
        BehavioralSignals(
            onboarding_velocity=1.0,
            assessment_completion=1.0,
            sjt_reliability=1.0,
        ),
        history,
    )
    assert r1["reliability_score"] == r2["reliability_score"]
