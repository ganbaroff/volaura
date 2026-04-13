"""Comprehensive pytest tests for:
1. Per-competency decay half-lives (aura_calc.calculate_effective_score)
2. DeCE Framework parser and EvaluationResult (bars._parse_dece_scores, EvaluationResult)

All math assertions use pytest.approx(abs=0.01) unless the expected value
is derived exactly from the formula — in which case abs=0.001 is used.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta

import pytest

# ── Imports under test ────────────────────────────────────────────────────────
from app.core.assessment.aura_calc import (
    _COMPETENCY_HALF_LIVES,
    _DECAY_FLOOR,
    _DECAY_PHASE1_DAYS,
    _DECAY_PHASE1_RATE,
    _DECAY_PHASE2_HALF_LIFE_DEFAULT,
    COMPETENCY_WEIGHTS,
    calculate_effective_score,
)
from app.core.assessment.bars import (
    EvaluationResult,
    _keyword_fallback,
    _parse_dece_scores,
    _parse_json_scores,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ts(days_ago: float) -> datetime:
    """Return a UTC-aware datetime `days_ago` days in the past."""
    return datetime.now(UTC) - timedelta(days=days_ago)


def _expected_decay_factor(days: float, half_life: float) -> float:
    """Replicate the two-phase Ebbinghaus formula from aura_calc.py."""
    if days <= _DECAY_PHASE1_DAYS:
        factor = 1.0 - (1.0 - _DECAY_PHASE1_RATE) * (days / _DECAY_PHASE1_DAYS)
    else:
        days_beyond = days - _DECAY_PHASE1_DAYS
        slow_decay = math.pow(0.80, days_beyond / half_life)
        factor = _DECAY_PHASE1_RATE * slow_decay
    return max(_DECAY_FLOOR, factor)


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — Per-competency decay half-lives
# ─────────────────────────────────────────────────────────────────────────────

class TestDecayMathPerCompetency:
    """Each competency decays at the correct rate (verified against formula)."""

    @pytest.mark.parametrize("slug,half_life", list(_COMPETENCY_HALF_LIVES.items()))
    def test_phase2_decay_at_half_life_boundary(self, slug: str, half_life: float) -> None:
        """At exactly one half-life beyond day 30, decay_factor ≈ 0.70 * 0.80."""
        days = _DECAY_PHASE1_DAYS + half_life
        expected_factor = _DECAY_PHASE1_RATE * 0.80  # one "80% retention period"
        expected_score = round(80.0 * max(_DECAY_FLOOR, expected_factor), 2)
        actual = calculate_effective_score(80.0, _ts(days), competency_slug=slug)
        assert actual == pytest.approx(expected_score, abs=0.02), (
            f"{slug}: expected {expected_score} at day {days}, got {actual}"
        )

    def test_tech_literacy_decays_faster_than_leadership(self) -> None:
        """tech_literacy (730-day half-life) decays faster than leadership (1640-day)."""
        raw = 80.0
        days = 1000.0
        tech = calculate_effective_score(raw, _ts(days), competency_slug="tech_literacy")
        lead = calculate_effective_score(raw, _ts(days), competency_slug="leadership")
        assert tech < lead, f"tech_literacy ({tech}) should be < leadership ({lead}) at day {days}"

    def test_tech_literacy_exact_value_at_365_days(self) -> None:
        """tech_literacy: verify exact score at 365 days using the formula."""
        raw = 100.0
        half_life = _COMPETENCY_HALF_LIVES["tech_literacy"]  # 730
        expected = round(raw * _expected_decay_factor(365.0, half_life), 2)
        actual = calculate_effective_score(raw, _ts(365.0), competency_slug="tech_literacy")
        assert actual == pytest.approx(expected, abs=0.02)

    def test_english_proficiency_exact_value_at_730_days(self) -> None:
        raw = 90.0
        half_life = _COMPETENCY_HALF_LIVES["english_proficiency"]  # 1095
        expected = round(raw * _expected_decay_factor(730.0, half_life), 2)
        actual = calculate_effective_score(raw, _ts(730.0), competency_slug="english_proficiency")
        assert actual == pytest.approx(expected, abs=0.02)

    def test_communication_exact_value_at_1000_days(self) -> None:
        raw = 75.0
        half_life = _COMPETENCY_HALF_LIVES["communication"]  # 1460
        expected = round(raw * _expected_decay_factor(1000.0, half_life), 2)
        actual = calculate_effective_score(raw, _ts(1000.0), competency_slug="communication")
        assert actual == pytest.approx(expected, abs=0.02)

    def test_leadership_exact_value_at_2000_days(self) -> None:
        raw = 95.0
        half_life = _COMPETENCY_HALF_LIVES["leadership"]  # 1640
        expected = round(raw * _expected_decay_factor(2000.0, half_life), 2)
        actual = calculate_effective_score(raw, _ts(2000.0), competency_slug="leadership")
        assert actual == pytest.approx(expected, abs=0.02)

    def test_default_half_life_computed_correctly(self) -> None:
        """Weighted-average half-life matches manual computation."""
        manual = sum(
            COMPETENCY_WEIGHTS[c] * _COMPETENCY_HALF_LIVES[c]
            for c in COMPETENCY_WEIGHTS
        )
        assert pytest.approx(round(manual, 1), abs=0.01) == _DECAY_PHASE2_HALF_LIFE_DEFAULT


class TestDecayFloor:
    """Floor of 0.60 is respected for all competencies across very long inactivity."""

    @pytest.mark.parametrize("slug", list(_COMPETENCY_HALF_LIVES.keys()) + [None])
    def test_floor_at_10000_days(self, slug) -> None:
        """Even after 10 000 days inactive, score ≥ floor * raw_score."""
        raw = 80.0
        effective = calculate_effective_score(raw, _ts(10_000.0), competency_slug=slug)
        floor_score = round(raw * _DECAY_FLOOR, 2)
        assert effective >= floor_score - 0.01, (
            f"{slug}: effective {effective} dropped below floor {floor_score}"
        )

    def test_floor_value_is_60_percent(self) -> None:
        assert pytest.approx(0.60) == _DECAY_FLOOR

    def test_floor_not_applied_in_phase1(self) -> None:
        """Phase 1 (≤30 days) should not hit the floor — factor stays above 0.70."""
        raw = 80.0
        effective = calculate_effective_score(raw, _ts(15.0), competency_slug="tech_literacy")
        # At day 15, factor = 1 - 0.30*(15/30) = 0.85 → score = 68, above floor (48)
        assert effective > raw * _DECAY_FLOOR


class TestPhase1Uniformity:
    """Phase 1 linear decay (0-30 days) is the same regardless of competency."""

    @pytest.mark.parametrize("days", [0, 5, 10, 15, 20, 25, 30])
    def test_phase1_same_across_competencies(self, days: float) -> None:
        """All competencies must produce identical effective scores within phase 1."""
        raw = 80.0
        ts = _ts(days)
        results = {
            slug: calculate_effective_score(raw, ts, competency_slug=slug)
            for slug in _COMPETENCY_HALF_LIVES
        }
        unique_values = set(results.values())
        assert len(unique_values) == 1, (
            f"At day {days}, competencies diverged: {results}"
        )

    def test_phase1_linear_at_day_0(self) -> None:
        raw = 80.0
        # day 0 → factor = 1.0 → effective = raw
        effective = calculate_effective_score(raw, _ts(0.0), competency_slug="tech_literacy")
        assert effective == pytest.approx(raw, abs=0.1)

    def test_phase1_linear_at_day_30(self) -> None:
        raw = 80.0
        # day 30 → factor = 0.70 → effective = 56.0
        effective = calculate_effective_score(raw, _ts(30.0), competency_slug="tech_literacy")
        assert effective == pytest.approx(80.0 * 0.70, abs=0.1)

    def test_phase1_intermediate_value(self) -> None:
        raw = 100.0
        # day 15: factor = 1 - 0.30 * (15/30) = 0.85
        effective = calculate_effective_score(raw, _ts(15.0))
        assert effective == pytest.approx(85.0, abs=0.1)


class TestUnknownCompetencySlug:
    """Unknown competency_slug falls back to weighted-average half-life."""

    def test_unknown_slug_matches_none_slug(self) -> None:
        raw = 80.0
        days = 500.0
        ts = _ts(days)
        result_none = calculate_effective_score(raw, ts, competency_slug=None)
        result_unknown = calculate_effective_score(raw, ts, competency_slug="totally_fake_skill")
        assert result_none == result_unknown

    def test_empty_string_slug_matches_none(self) -> None:
        raw = 60.0
        days = 200.0
        ts = _ts(days)
        result_none = calculate_effective_score(raw, ts, competency_slug=None)
        result_empty = calculate_effective_score(raw, ts, competency_slug="")
        assert result_none == result_empty

    def test_unknown_slug_uses_default_half_life(self) -> None:
        """Verify the actual math: unknown slug should match default formula."""
        raw = 90.0
        days = 400.0
        ts = _ts(days)
        expected_factor = _expected_decay_factor(days, _DECAY_PHASE2_HALF_LIFE_DEFAULT)
        expected_score = round(raw * expected_factor, 2)
        actual = calculate_effective_score(raw, ts, competency_slug="nonexistent")
        assert actual == pytest.approx(expected_score, abs=0.02)


class TestBackwardCompatibility:
    """2-arg calls (raw_score, last_updated) still work without competency_slug."""

    def test_two_arg_call_accepted(self) -> None:
        result = calculate_effective_score(70.0, _ts(100.0))
        assert isinstance(result, float)
        assert 0.0 <= result <= 100.0

    def test_two_arg_equals_explicit_none_slug(self) -> None:
        raw = 70.0
        ts = _ts(100.0)
        result_2arg = calculate_effective_score(raw, ts)
        result_none = calculate_effective_score(raw, ts, competency_slug=None)
        assert result_2arg == result_none


class TestEdgeCases:
    """Edge cases: raw_score=0, last_updated=None, negative days, naive timestamps."""

    def test_raw_score_zero_returns_zero(self) -> None:
        result = calculate_effective_score(0.0, _ts(100.0), competency_slug="tech_literacy")
        assert result == 0.0

    def test_last_updated_none_returns_raw(self) -> None:
        raw = 75.0
        result = calculate_effective_score(raw, None, competency_slug="communication")
        assert result == raw

    def test_last_updated_none_no_slug_returns_raw(self) -> None:
        result = calculate_effective_score(50.0, None)
        assert result == 50.0

    def test_future_timestamp_no_decay(self) -> None:
        """A future last_updated means 0 inactive days → factor ≈ 1.0."""
        future = datetime.now(UTC) + timedelta(days=10)
        result = calculate_effective_score(80.0, future, competency_slug="leadership")
        # days_inactive = max(0, negative) = 0 → factor = 1.0
        assert result == pytest.approx(80.0, abs=0.1)

    def test_naive_datetime_treated_as_utc(self) -> None:
        """Naive datetimes are coerced to UTC, not rejected."""
        naive = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=50)
        assert naive.tzinfo is None
        result = calculate_effective_score(80.0, naive, competency_slug="tech_literacy")
        assert isinstance(result, float)
        assert 0.0 <= result <= 100.0

    def test_raw_score_100_does_not_exceed_100(self) -> None:
        result = calculate_effective_score(100.0, _ts(1.0), competency_slug="leadership")
        assert result <= 100.0

    def test_very_small_raw_score(self) -> None:
        # raw_score > 0, so decay applies; result should still be non-negative
        result = calculate_effective_score(0.01, _ts(500.0), competency_slug="tech_literacy")
        assert result >= 0.0

    def test_negative_raw_score_returns_zero(self) -> None:
        """raw_score <= 0 → guard returns 0.0 (prevent negative score propagation)."""
        result = calculate_effective_score(-5.0, _ts(100.0))
        assert result == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — DeCE Framework: _parse_dece_scores
# ─────────────────────────────────────────────────────────────────────────────

class TestParseDeCEFormat:
    """Parse DeCE format correctly — score, quote, confidence extracted."""

    def test_basic_dece_format(self) -> None:
        raw = json.dumps({
            "active_listening": {"score": 0.8, "quote": "I always hear everyone out", "confidence": 0.9},
            "empathy": {"score": 0.5, "quote": None, "confidence": 0.7},
        })
        scores, details = _parse_dece_scores(raw)
        assert scores is not None
        assert details is not None
        assert scores["active_listening"] == pytest.approx(0.8)
        assert scores["empathy"] == pytest.approx(0.5)

    def test_dece_detail_fields_present(self) -> None:
        raw = json.dumps({
            "teamwork": {"score": 0.75, "quote": "coordinated the volunteers", "confidence": 0.85},
        })
        scores, details = _parse_dece_scores(raw)
        assert details is not None
        assert len(details) == 1
        detail = details[0]
        assert detail["concept_id"] == "teamwork"
        assert detail["score"] == pytest.approx(0.75, abs=0.001)
        assert detail["quote"] == "coordinated the volunteers"
        assert detail["confidence"] == pytest.approx(0.85, abs=0.001)

    def test_null_quote_stored_as_none(self) -> None:
        raw = json.dumps({
            "leadership": {"score": 0.3, "quote": None, "confidence": 0.6},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        assert details[0]["quote"] is None

    def test_score_rounded_to_3dp(self) -> None:
        raw = json.dumps({
            "reliability": {"score": 0.66666, "quote": "always on time", "confidence": 0.9},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        # score in detail dict is rounded to 3dp
        assert details[0]["score"] == pytest.approx(0.667, abs=0.001)

    def test_confidence_rounded_to_3dp(self) -> None:
        raw = json.dumps({
            "adaptability": {"score": 0.5, "quote": "adjusted quickly", "confidence": 0.88888},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        assert details[0]["confidence"] == pytest.approx(0.889, abs=0.001)


class TestParseLegacyFloatFormat:
    """Parse legacy float format — returns None for concept_details."""

    def test_legacy_float_scores_parsed(self) -> None:
        raw = json.dumps({"active_listening": 0.8, "empathy": 0.6})
        scores, details = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["active_listening"] == pytest.approx(0.8)
        assert scores["empathy"] == pytest.approx(0.6)

    def test_legacy_returns_none_for_details(self) -> None:
        raw = json.dumps({"concept_a": 0.5, "concept_b": 0.7})
        _, details = _parse_dece_scores(raw)
        assert details is None

    def test_legacy_integer_float(self) -> None:
        raw = json.dumps({"concept_a": 1, "concept_b": 0})
        scores, details = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["concept_a"] == pytest.approx(1.0)
        assert scores["concept_b"] == pytest.approx(0.0)
        assert details is None


class TestParseMixedFormat:
    """Mixed format: some DeCE dicts, some legacy floats."""

    def test_mixed_scores_all_parsed(self) -> None:
        raw = json.dumps({
            "active_listening": {"score": 0.9, "quote": "great listener", "confidence": 0.95},
            "empathy": 0.6,
        })
        scores, details = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["active_listening"] == pytest.approx(0.9)
        assert scores["empathy"] == pytest.approx(0.6)

    def test_mixed_details_only_contains_dece_entries(self) -> None:
        raw = json.dumps({
            "active_listening": {"score": 0.9, "quote": "great listener", "confidence": 0.95},
            "empathy": 0.6,
        })
        _, details = _parse_dece_scores(raw)
        # Only DeCE entries appear in concept_details
        assert details is not None
        concept_ids = [d["concept_id"] for d in details]
        assert "active_listening" in concept_ids
        assert "empathy" not in concept_ids

    def test_mixed_all_floats_gives_none_details(self) -> None:
        """If the only mix is all floats, concept_details is None."""
        raw = json.dumps({"a": 0.3, "b": 0.7, "c": 0.5})
        _, details = _parse_dece_scores(raw)
        assert details is None


class TestQuoteCapping:
    """Quote is capped at 200 characters."""

    def test_long_quote_capped_at_200(self) -> None:
        long_quote = "x" * 300
        raw = json.dumps({
            "concept": {"score": 0.8, "quote": long_quote, "confidence": 0.9},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        assert len(details[0]["quote"]) == 200

    def test_short_quote_not_truncated(self) -> None:
        short_quote = "short phrase"
        raw = json.dumps({
            "concept": {"score": 0.8, "quote": short_quote, "confidence": 0.9},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        assert details[0]["quote"] == short_quote

    def test_exactly_200_chars_not_truncated(self) -> None:
        exact_quote = "a" * 200
        raw = json.dumps({
            "concept": {"score": 0.8, "quote": exact_quote, "confidence": 0.9},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        assert len(details[0]["quote"]) == 200


class TestInvalidJSON:
    """Invalid JSON returns (None, None)."""

    def test_empty_string(self) -> None:
        scores, details = _parse_dece_scores("")
        assert scores is None
        assert details is None

    def test_malformed_json(self) -> None:
        scores, details = _parse_dece_scores("{broken json")
        assert scores is None
        assert details is None

    def test_json_array_not_dict(self) -> None:
        scores, details = _parse_dece_scores("[0.8, 0.6]")
        assert scores is None
        assert details is None

    def test_json_null(self) -> None:
        scores, details = _parse_dece_scores("null")
        assert scores is None
        assert details is None

    def test_plain_string(self) -> None:
        scores, details = _parse_dece_scores("not json at all")
        assert scores is None
        assert details is None

    def test_markdown_fenced_valid_json(self) -> None:
        """Markdown code fences are stripped before parsing."""
        raw = '```json\n{"concept": 0.8}\n```'
        scores, details = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["concept"] == pytest.approx(0.8)


class TestScoreClamping:
    """Score is clamped to [0, 1]."""

    def test_score_above_1_clamped_to_1_dece(self) -> None:
        raw = json.dumps({
            "concept": {"score": 1.5, "quote": "excellent", "confidence": 0.9},
        })
        scores, _ = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["concept"] == pytest.approx(1.0)

    def test_score_below_0_clamped_to_0_dece(self) -> None:
        raw = json.dumps({
            "concept": {"score": -0.3, "quote": None, "confidence": 0.9},
        })
        scores, _ = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["concept"] == pytest.approx(0.0)

    def test_score_above_1_clamped_to_1_legacy(self) -> None:
        raw = json.dumps({"concept": 2.5})
        scores, _ = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["concept"] == pytest.approx(1.0)

    def test_score_below_0_clamped_to_0_legacy(self) -> None:
        raw = json.dumps({"concept": -1.0})
        scores, _ = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["concept"] == pytest.approx(0.0)

    def test_score_exactly_0_preserved(self) -> None:
        raw = json.dumps({"concept": {"score": 0.0, "quote": None, "confidence": 0.5}})
        scores, _ = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["concept"] == pytest.approx(0.0)

    def test_score_exactly_1_preserved(self) -> None:
        raw = json.dumps({"concept": {"score": 1.0, "quote": "perfect", "confidence": 1.0}})
        scores, _ = _parse_dece_scores(raw)
        assert scores is not None
        assert scores["concept"] == pytest.approx(1.0)


class TestConfidenceClamping:
    """Confidence is clamped to [0, 1]."""

    def test_confidence_above_1_clamped(self) -> None:
        raw = json.dumps({
            "concept": {"score": 0.8, "quote": "nice", "confidence": 1.8},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        assert details[0]["confidence"] == pytest.approx(1.0)

    def test_confidence_below_0_clamped(self) -> None:
        raw = json.dumps({
            "concept": {"score": 0.8, "quote": "nice", "confidence": -0.5},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        assert details[0]["confidence"] == pytest.approx(0.0)

    def test_missing_confidence_defaults_to_0_5(self) -> None:
        """Absent confidence key defaults to 0.5 per source code."""
        raw = json.dumps({
            "concept": {"score": 0.7, "quote": "some phrase"},
        })
        _, details = _parse_dece_scores(raw)
        assert details is not None
        assert details[0]["confidence"] == pytest.approx(0.5)


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — EvaluationResult
# ─────────────────────────────────────────────────────────────────────────────

class TestEvaluationResultToLog:
    """EvaluationResult.to_log() includes/omits concept_details correctly."""

    def test_to_log_includes_concept_details_when_present(self) -> None:
        details = [
            {"concept_id": "active_listening", "score": 0.8, "quote": "heard everyone", "confidence": 0.9},
        ]
        er = EvaluationResult(
            composite=0.8,
            concept_scores={"active_listening": 0.8},
            model_used="gemini-2.5-flash",
            concept_details=details,
        )
        log = er.to_log()
        assert "concept_details" in log
        assert log["concept_details"] == details

    def test_to_log_omits_concept_details_when_empty_list(self) -> None:
        er = EvaluationResult(
            composite=0.5,
            concept_scores={"concept_a": 0.5},
            model_used="keyword_fallback",
            concept_details=[],
        )
        log = er.to_log()
        assert "concept_details" not in log

    def test_to_log_omits_concept_details_when_none(self) -> None:
        er = EvaluationResult(
            composite=0.5,
            concept_scores={"concept_a": 0.5},
            model_used="keyword_fallback",
            concept_details=None,
        )
        log = er.to_log()
        assert "concept_details" not in log

    def test_to_log_mandatory_fields_always_present(self) -> None:
        er = EvaluationResult(0.6, {"c": 0.6}, "gpt-4o-mini")
        log = er.to_log()
        assert "composite_score" in log
        assert "concept_scores" in log
        assert "model_used" in log
        assert "methodology" in log
        assert "framework" in log

    def test_to_log_composite_rounded_to_3dp(self) -> None:
        er = EvaluationResult(0.66666, {"c": 0.66666}, "gemini-2.5-flash")
        log = er.to_log()
        assert log["composite_score"] == pytest.approx(0.667, abs=0.001)

    def test_to_log_concept_scores_rounded_to_3dp(self) -> None:
        er = EvaluationResult(0.5, {"active_listening": 0.88888}, "gemini-2.5-flash")
        log = er.to_log()
        assert log["concept_scores"]["active_listening"] == pytest.approx(0.889, abs=0.001)

    def test_to_log_model_used_preserved(self) -> None:
        er = EvaluationResult(0.7, {}, "gpt-4o-mini")
        assert er.to_log()["model_used"] == "gpt-4o-mini"

    def test_concept_details_defaults_to_empty_list_when_none(self) -> None:
        """EvaluationResult stores [] when concept_details=None (internal normalisation)."""
        er = EvaluationResult(0.5, {}, "keyword_fallback", concept_details=None)
        assert er.concept_details == []


class TestParseJsonScoresBackwardCompat:
    """_parse_json_scores (legacy alias) returns flat scores dict only."""

    def test_alias_returns_dict_for_legacy_format(self) -> None:
        raw = json.dumps({"concept_a": 0.8, "concept_b": 0.5})
        result = _parse_json_scores(raw)
        assert result is not None
        assert isinstance(result, dict)
        assert result["concept_a"] == pytest.approx(0.8)

    def test_alias_returns_dict_for_dece_format(self) -> None:
        raw = json.dumps({
            "active_listening": {"score": 0.9, "quote": "good", "confidence": 0.85},
        })
        result = _parse_json_scores(raw)
        assert result is not None
        assert result["active_listening"] == pytest.approx(0.9)

    def test_alias_returns_none_on_invalid_json(self) -> None:
        result = _parse_json_scores("not json")
        assert result is None

    def test_alias_does_not_return_tuple(self) -> None:
        """Alias must return a plain dict (or None), never a tuple."""
        raw = json.dumps({"c": 0.5})
        result = _parse_json_scores(raw)
        assert not isinstance(result, tuple)


class TestKeywordFallbackNoConceptDetails:
    """Keyword fallback path produces no concept_details (None)."""

    def test_keyword_fallback_returns_flat_dict(self) -> None:
        concepts = [
            {"name": "communication", "keywords": ["talk", "listen", "discuss"]},
        ]
        result = _keyword_fallback("I talk and listen a lot", concepts)
        assert isinstance(result, dict)
        assert "communication" in result

    def test_keyword_fallback_is_not_evaluation_result(self) -> None:
        """_keyword_fallback returns a plain dict, not EvaluationResult."""
        concepts = [{"name": "c", "keywords": ["x"]}]
        result = _keyword_fallback("x", concepts)
        assert not isinstance(result, EvaluationResult)

    def test_keyword_fallback_no_keywords_defaults_to_0_5(self) -> None:
        concepts = [{"name": "teamwork"}]
        result = _keyword_fallback("anything", concepts)
        assert result["teamwork"] == pytest.approx(0.5)

    def test_keyword_fallback_score_0_when_no_hits(self) -> None:
        concepts = [{"name": "c", "keywords": ["alpha", "beta", "gamma"]}]
        result = _keyword_fallback("nothing relevant here", concepts)
        assert result["c"] == pytest.approx(0.0)

    def test_keyword_fallback_score_1_when_all_hit(self) -> None:
        concepts = [{"name": "c", "keywords": ["alpha", "beta"]}]
        # Answer must be >= 30 words to avoid anti-gaming short-answer cap
        long_answer = (
            "In my experience working with alpha protocols and beta testing frameworks, "
            "I have found that combining both approaches leads to significantly better "
            "outcomes for the team and the project as a whole, especially when dealing "
            "with complex distributed systems that require careful coordination."
        )
        result = _keyword_fallback(long_answer, concepts)
        assert result["c"] == pytest.approx(1.0)

    def test_keyword_fallback_supports_concept_key(self) -> None:
        """Backward compat: accepts 'concept' key in addition to 'name'."""
        concepts = [{"concept": "comm", "keywords": ["talk"]}]
        result = _keyword_fallback("I talk often", concepts)
        assert "comm" in result
