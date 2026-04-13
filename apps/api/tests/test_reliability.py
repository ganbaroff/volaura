"""Unit tests for the reliability scoring engine."""


from app.core.reliability.scoring import (
    BEHAVIORAL_MAX,
    BEHAVIORAL_MIN,
    BehavioralSignals,
    EventHistory,
    behavioral_score,
    blended_score,
    calculate,
    proven_score,
    reliability_status,
)

# ── behavioral_score ──────────────────────────────────────────────────────────

def test_behavioral_all_zero_signals():
    BehavioralSignals()  # all 0.5 default for onboarding/sjt, 0 others
    score = behavioral_score(BehavioralSignals(
        onboarding_velocity=0, assessment_completion=0, profile_completeness=0,
        sjt_reliability=0, contact_verification=0, availability_specificity=0,
    ))
    assert score == BEHAVIORAL_MIN


def test_behavioral_all_full_signals():
    s = BehavioralSignals(
        onboarding_velocity=1, assessment_completion=1, profile_completeness=1,
        sjt_reliability=1, contact_verification=1, availability_specificity=1,
    )
    assert behavioral_score(s) == BEHAVIORAL_MAX


def test_behavioral_clamped():
    # Weights * 1.0 = 1.0 → max score
    s = BehavioralSignals(
        onboarding_velocity=1, assessment_completion=1, profile_completeness=1,
        sjt_reliability=1, contact_verification=1, availability_specificity=1,
    )
    score = behavioral_score(s)
    assert BEHAVIORAL_MIN <= score <= BEHAVIORAL_MAX


def test_behavioral_mid_signals():
    s = BehavioralSignals(
        onboarding_velocity=0.5, assessment_completion=0.5, profile_completeness=0.5,
        sjt_reliability=0.5, contact_verification=0.5, availability_specificity=0.5,
    )
    score = behavioral_score(s)
    assert BEHAVIORAL_MIN < score < BEHAVIORAL_MAX


# ── proven_score ──────────────────────────────────────────────────────────────

def test_proven_no_history():
    h = EventHistory()
    assert proven_score(h) == 50.0


def test_proven_perfect_attendance():
    h = EventHistory(total_registered=5, total_attended=5, total_no_shows=0)
    score = proven_score(h)
    assert score > 100.0 * 0.9  # attendance + bonuses


def test_proven_ghost_penalty():
    h = EventHistory(total_registered=3, total_attended=2, total_no_shows=1, no_show_types=["ghost"])
    score_clean = proven_score(EventHistory(total_registered=3, total_attended=2, total_no_shows=0))
    score_ghost = proven_score(h)
    assert score_ghost < score_clean


def test_proven_coordinator_rating_bonus():
    h_good = EventHistory(total_registered=1, total_attended=1, coordinator_avg_rating=5.0)
    h_bad = EventHistory(total_registered=1, total_attended=1, coordinator_avg_rating=1.0)
    assert proven_score(h_good) > proven_score(h_bad)


def test_proven_score_clamped():
    h = EventHistory(
        total_registered=10, total_attended=10, total_no_shows=0,
        no_show_types=[], coordinator_avg_rating=5.0,
    )
    assert proven_score(h) <= 100.0


# ── blended_score ─────────────────────────────────────────────────────────────

def test_blend_zero_events_is_behavioral():
    assert blended_score(60.0, 80.0, 0) == 60.0


def test_blend_five_events_is_proven():
    assert blended_score(60.0, 80.0, 5) == 80.0


def test_blend_intermediate():
    result = blended_score(60.0, 80.0, 2)
    assert 60.0 < result < 80.0


def test_blend_increases_with_events():
    scores = [blended_score(40.0, 90.0, n) for n in range(6)]
    assert scores == sorted(scores)


# ── reliability_status ────────────────────────────────────────────────────────

def test_status_zero_events():
    assert reliability_status(0) == "behavioral"


def test_status_building():
    assert reliability_status(3) == "building"


def test_status_proven():
    assert reliability_status(5) == "proven"
    assert reliability_status(10) == "proven"


# ── calculate (integration) ───────────────────────────────────────────────────

def test_calculate_new_user():
    signals = BehavioralSignals(
        onboarding_velocity=0.8, assessment_completion=0.5, profile_completeness=0.7,
        sjt_reliability=0.6, contact_verification=1.0, availability_specificity=0.4,
    )
    history = EventHistory()
    result = calculate(signals, history)

    assert "reliability_score" in result
    assert result["reliability_status"] == "behavioral"
    assert result["events_attended"] == 0
    assert result["events_no_show"] == 0
    assert BEHAVIORAL_MIN <= result["reliability_score"] <= BEHAVIORAL_MAX


def test_calculate_experienced_volunteer():
    signals = BehavioralSignals(
        onboarding_velocity=1.0, assessment_completion=1.0, profile_completeness=1.0,
        sjt_reliability=0.9, contact_verification=1.0, availability_specificity=1.0,
    )
    history = EventHistory(
        total_registered=6, total_attended=6, total_no_shows=0,
        coordinator_avg_rating=4.5,
    )
    result = calculate(signals, history)

    assert result["reliability_status"] == "proven"
    assert result["events_attended"] == 6
    assert result["reliability_score"] > 70.0
