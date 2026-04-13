"""
Sprint 8 — Technical Debt Closure Tests
========================================

TDD order: RED → GREEN → REFACTOR.
Tests are written BEFORE the fixes. They will fail until implementation is applied.

Covers:
- [S8.1] engine.py: eap_failures persistence across requests
- [S8.2] antigaming.py: grouped alternating bypass + time clustering
- [S8.3] assessment.py: competency score bounds validation
- [S8.4] aura.py: rate limits on /me/visibility and /me/sharing
- [S8.6] badge tier boundary tests (all 6 thresholds)
- [S8.6] bars.py: fallback chain timeout behavior
"""

from unittest.mock import MagicMock, patch

import pytest

# ── [S8.1] engine.py: eap_failures persistence ───────────────────────────────

class TestEapFailuresPersistence:
    """eap_failures must persist across HTTP requests via to_dict/from_dict."""

    def test_eap_failures_field_exists_in_catstate(self):
        """CATState must have eap_failures field (not a dynamic attribute)."""
        from app.core.assessment.engine import CATState
        state = CATState()
        assert hasattr(state, "eap_failures"), (
            "CATState is missing 'eap_failures' dataclass field. "
            "Dynamic attribute (getattr pattern) doesn't survive serialization."
        )
        assert state.eap_failures == 0

    def test_eap_failures_serializes_to_dict(self):
        """eap_failures must appear in to_dict() output."""
        from app.core.assessment.engine import CATState
        state = CATState()
        state.eap_failures = 2
        d = state.to_dict()
        assert "eap_failures" in d, "to_dict() doesn't include eap_failures"
        assert d["eap_failures"] == 2

    def test_eap_failures_deserializes_from_dict(self):
        """eap_failures must be restored by from_dict()."""
        from app.core.assessment.engine import CATState
        state = CATState()
        state.eap_failures = 2
        restored = CATState.from_dict(state.to_dict())
        assert restored.eap_failures == 2, (
            f"from_dict() lost eap_failures: expected 2, got {restored.eap_failures}"
        )

    def test_eap_failures_backward_compat_missing_key(self):
        """Sessions without eap_failures key must deserialize to 0 (backward compat)."""
        from app.core.assessment.engine import CATState
        old_session_data = {
            "theta": 0.5,
            "theta_se": 0.8,
            "stopped": False,
            "stop_reason": None,
            "items": [],
            # deliberately NO eap_failures key
        }
        state = CATState.from_dict(old_session_data)
        assert state.eap_failures == 0, (
            "Old sessions without eap_failures should default to 0, not crash"
        )

    def test_eap_failures_persists_across_multiple_requests(self):
        """Simulate 3 separate request cycles — counter must accumulate."""
        from app.core.assessment.engine import CATState
        # Request 1: fail, serialize
        state = CATState()
        state.eap_failures = 1
        serialized = state.to_dict()

        # Request 2: restore, fail again, serialize
        state2 = CATState.from_dict(serialized)
        state2.eap_failures += 1
        serialized2 = state2.to_dict()

        # Request 3: restore, check count
        state3 = CATState.from_dict(serialized2)
        assert state3.eap_failures == 2, (
            f"Counter should be 2 after 2 failures across requests, got {state3.eap_failures}"
        )

    def test_eap_degraded_stops_session_after_3_failures(self):
        """submit_response() must stop session if eap_failures >= 3."""
        from app.core.assessment.engine import CATState, submit_response
        state = CATState()
        state.eap_failures = 2  # one more will trigger abort

        # Submit a response that will cause EAP to fail
        # We simulate by patching _estimate_eap to raise
        with patch("app.core.assessment.engine._estimate_eap", side_effect=ValueError("EAP failed")):
            updated = submit_response(
                state,
                question_id="q1",
                irt_a=1.0, irt_b=0.0, irt_c=0.0,
                raw_score=0.8,
                response_time_ms=5000,
            )
        assert updated.eap_failures == 3
        assert updated.stopped is True, (
            "Session must stop after 3 EAP failures to prevent silent score corruption"
        )
        assert updated.stop_reason == "eap_degraded", (
            f"Expected stop_reason='eap_degraded', got '{updated.stop_reason}'"
        )


# ── [S8.2] antigaming.py: grouped alternating + time clustering ───────────────

class TestAntigamingGroupedBypass:
    """Run-compression check catches grouped alternating [1,1,0,0,1,1,0,0]."""

    def test_strict_alternating_still_detected(self):
        """Regression: [1,0,1,0,1,0,1,0] must still trigger is_alternating."""
        from app.core.assessment.antigaming import analyse
        answers = [
            {"response": r, "response_time_ms": 5000, "raw_score": float(r)}
            for r in [1, 0, 1, 0, 1, 0, 1, 0]
        ]
        signal = analyse(answers)
        assert signal.is_alternating, "Strict alternating pattern not detected (regression)"

    def test_grouped_alternating_bypass_detected(self):
        """[1,1,0,0,1,1,0,0] must be detected as group alternating."""
        from app.core.assessment.antigaming import analyse
        answers = [
            {"response": r, "response_time_ms": 5000, "raw_score": float(r)}
            for r in [1, 1, 0, 0, 1, 1, 0, 0]
        ]
        signal = analyse(answers)
        assert hasattr(signal, "is_group_alternating"), (
            "GamingSignal missing is_group_alternating field"
        )
        assert signal.is_group_alternating, (
            "Grouped alternating [1,1,0,0,1,1,0,0] not detected — bypass still works"
        )

    def test_grouped_alternating_in_flags(self):
        """is_group_alternating must appear in signal.flags."""
        from app.core.assessment.antigaming import analyse
        answers = [
            {"response": r, "response_time_ms": 5000, "raw_score": float(r)}
            for r in [1, 1, 0, 0, 1, 1, 0, 0]
        ]
        signal = analyse(answers)
        assert "group_alternating_pattern" in signal.flags, (
            f"'group_alternating_pattern' missing from flags: {signal.flags}"
        )

    def test_natural_varied_responses_not_flagged(self):
        """Genuinely varied responses [1,0,1,1,0,1,0,0,1,0] must not trigger group detection."""
        from app.core.assessment.antigaming import analyse
        answers = [
            {"response": r, "response_time_ms": 5000, "raw_score": float(r)}
            for r in [1, 0, 1, 1, 0, 1, 0, 0, 1, 0]
        ]
        signal = analyse(answers)
        # This could trigger alternating but not GROUP alternating
        assert not signal.is_group_alternating, (
            "Natural pattern incorrectly flagged as group alternating"
        )


class TestAntigamingTimeClustering:
    """Time clustering check (CV < 0.15) catches robotic same-speed answers."""

    def test_time_clustering_detected_near_identical_times(self):
        """8 answers all at ~3000ms (CV ≈ 0.01) must trigger is_time_clustered."""
        from app.core.assessment.antigaming import analyse
        answers = [
            {"response": i % 2, "response_time_ms": 3000 + (i * 10), "raw_score": 0.5}
            for i in range(8)
        ]
        signal = analyse(answers)
        assert hasattr(signal, "is_time_clustered"), (
            "GamingSignal missing is_time_clustered field"
        )
        assert signal.is_time_clustered, (
            "Robotic timing (all ~3000ms, CV ≈ 0.01) not detected"
        )

    def test_time_clustering_in_flags(self):
        """is_time_clustered must appear in signal.flags."""
        from app.core.assessment.antigaming import analyse
        answers = [
            {"response": i % 2, "response_time_ms": 3000 + (i * 10), "raw_score": 0.5}
            for i in range(8)
        ]
        signal = analyse(answers)
        assert "time_clustering" in signal.flags, (
            f"'time_clustering' missing from flags: {signal.flags}"
        )

    def test_natural_timing_not_flagged(self):
        """Varied natural timing (CV ≈ 0.7) must NOT trigger time clustering."""
        from app.core.assessment.antigaming import analyse
        answers = [
            {"response": i % 2, "response_time_ms": t, "raw_score": 0.5}
            for i, t in enumerate([2000, 8000, 3500, 12000, 4500, 900, 7000, 2800])
        ]
        signal = analyse(answers)
        assert not signal.is_time_clustered, (
            "Natural timing variance incorrectly flagged as robotic"
        )

    def test_time_clustering_requires_minimum_6_answers(self):
        """Time clustering must not trigger with fewer than 6 answers."""
        from app.core.assessment.antigaming import analyse
        answers = [
            {"response": 1, "response_time_ms": 3000, "raw_score": 1.0}
            for _ in range(5)  # only 5
        ]
        signal = analyse(answers)
        assert not signal.is_time_clustered, (
            "Time clustering triggered with < 6 answers (insufficient data)"
        )


# ── [S8.3] assessment.py bounds check ────────────────────────────────────────

class TestCompetencyScoreBounds:
    """competency_score must be clamped to [0, 100] in the Python layer."""

    def test_score_over_100_clamped(self):
        """Score > 100 must be clamped and logged, not sent to RPC raw."""
        # We test the clamping function directly
        from app.core.assessment.aura_calc import clamp_competency_score
        assert clamp_competency_score(125.0) == 100.0

    def test_score_negative_clamped_to_zero(self):
        """Negative score must be clamped to 0.0."""
        from app.core.assessment.aura_calc import clamp_competency_score
        assert clamp_competency_score(-5.0) == 0.0

    def test_valid_score_unchanged(self):
        """Score within [0, 100] must be returned unchanged."""
        from app.core.assessment.aura_calc import clamp_competency_score
        assert clamp_competency_score(75.5) == 75.5
        assert clamp_competency_score(0.0) == 0.0
        assert clamp_competency_score(100.0) == 100.0


# ── [S8.4] aura.py rate limits on write endpoints ────────────────────────────

def test_visibility_endpoint_has_request_param():
    """PATCH /me/visibility must have 'request: Request' for @limiter.limit()."""
    import inspect

    from app.routers.aura import update_visibility
    sig = inspect.signature(update_visibility)
    assert "request" in sig.parameters, (
        "update_visibility missing 'request: Request' — rate limiter won't work without it"
    )


def test_sharing_endpoint_has_request_param():
    """POST /me/sharing must have 'request: Request' for @limiter.limit()."""
    import inspect

    from app.routers.aura import manage_sharing_permission
    sig = inspect.signature(manage_sharing_permission)
    assert "request" in sig.parameters, (
        "manage_sharing_permission missing 'request: Request' — rate limiter won't work"
    )


# ── [S8.6] Badge tier boundary tests ─────────────────────────────────────────

class TestBadgeTierBoundaries:
    """All 6 badge tier thresholds must be correct per CLAUDE.md spec."""

    def _get_tier(self, score: float) -> str:
        from app.core.assessment.aura_calc import get_badge_tier
        return get_badge_tier(score)

    def test_platinum_inclusive_90(self):
        """score=90.0 must return 'platinum'."""
        assert self._get_tier(90.0) == "platinum"

    def test_platinum_just_above_threshold(self):
        """score=90.001 must return 'platinum'."""
        assert self._get_tier(90.001) == "platinum"

    def test_gold_exclusive_90(self):
        """score=89.9999 must return 'gold' (not platinum)."""
        assert self._get_tier(89.9999) == "gold"

    def test_gold_inclusive_75(self):
        """score=75.0 must return 'gold'."""
        assert self._get_tier(75.0) == "gold"

    def test_silver_exclusive_75(self):
        """score=74.9999 must return 'silver'."""
        assert self._get_tier(74.9999) == "silver"

    def test_silver_inclusive_60(self):
        """score=60.0 must return 'silver'."""
        assert self._get_tier(60.0) == "silver"

    def test_bronze_exclusive_60(self):
        """score=59.9999 must return 'bronze'."""
        assert self._get_tier(59.9999) == "bronze"

    def test_bronze_inclusive_40(self):
        """score=40.0 must return 'bronze'."""
        assert self._get_tier(40.0) == "bronze"

    def test_none_exclusive_40(self):
        """score=39.9 must return 'none'."""
        assert self._get_tier(39.9) == "none"

    def test_zero_score_returns_none(self):
        """score=0.0 must return 'none'."""
        assert self._get_tier(0.0) == "none"


# ── [S8.6] BARS fallback chain ────────────────────────────────────────────────

class TestBarsTimeoutFallback:
    """BARS must fall back Gemini → OpenAI → keyword on timeout."""

    @pytest.mark.asyncio
    async def test_gemini_timeout_falls_back_to_openai(self):
        """If Gemini + Groq both time out (15s), BARS must try OpenAI."""

        from app.core.assessment import bars

        async def mock_timeout(*args, **kwargs):
            raise TimeoutError("timed out")

        with (
            patch.object(bars, "_try_gemini", side_effect=mock_timeout),
            patch.object(bars, "_try_groq", side_effect=mock_timeout),
            patch.object(bars, "_try_openai", return_value=MagicMock(
                composite=0.7,
                to_log=lambda: {"model_used": "gpt-4o-mini", "concept_scores": {}}
            )) as mock_openai,
        ):
            result = await bars.evaluate_answer(
                question_en="Describe your leadership approach.",
                answer="I lead by example and communicate clearly.",
                expected_concepts=[{"concept": "leadership", "weight": 1.0}],
                return_details=True,
            )
            mock_openai.assert_called_once(), "OpenAI not called after Gemini+Groq timeout"
            assert result.composite >= 0.0

    @pytest.mark.asyncio
    async def test_both_llms_timeout_falls_back_to_keyword(self):
        """If all LLMs time out, BARS must use keyword fallback."""

        from app.core.assessment import bars

        async def mock_timeout(*args, **kwargs):
            raise TimeoutError("timed out")

        with (
            patch.object(bars, "_try_gemini", side_effect=mock_timeout),
            patch.object(bars, "_try_groq", side_effect=mock_timeout),
            patch.object(bars, "_try_openai", side_effect=mock_timeout),
        ):
            result = await bars.evaluate_answer(
                question_en="Describe teamwork.",
                answer="I collaborate and support my team.",
                expected_concepts=[{"concept": "teamwork", "weight": 1.0}],
                return_details=True,
            )
            assert result is not None, "BARS returned None — keyword fallback failed"
            assert 0.0 <= result.composite <= 1.0, (
                f"Keyword fallback score {result.composite} out of [0, 1]"
            )

    @pytest.mark.asyncio
    async def test_keyword_fallback_returns_valid_score(self):
        """Keyword fallback alone must return a score in [0, 1]."""
        from app.core.assessment import bars

        async def mock_timeout(*args, **kwargs):
            raise Exception("LLM unavailable")

        with (
            patch.object(bars, "_try_gemini", side_effect=mock_timeout),
            patch.object(bars, "_try_groq", side_effect=mock_timeout),
            patch.object(bars, "_try_openai", side_effect=mock_timeout),
        ):
            result = await bars.evaluate_answer(
                question_en="What does reliability mean to you?",
                answer="Being on time and keeping promises.",
                expected_concepts=[{"concept": "reliability", "weight": 1.0}],
                return_details=True,
            )
            assert result is not None
            assert 0.0 <= result.composite <= 1.0
