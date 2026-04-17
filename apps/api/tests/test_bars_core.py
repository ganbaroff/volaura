"""Unit tests for app.core.assessment.bars — BARS evaluator pure functions."""

import pytest

from app.core.assessment.bars import (
    EvaluationResult,
    _aggregate,
    _answer_relevance_penalty,
    _cache_key,
    _is_incoherent_dump,
    _is_negated,
    _keyword_fallback,
    _parse_dece_scores,
    _parse_json_scores,
)

# ── _cache_key ──────────────────────────────────────────────────────────────


class TestCacheKey:
    def test_deterministic(self):
        k1 = _cache_key("q", "a", '["c"]')
        k2 = _cache_key("q", "a", '["c"]')
        assert k1 == k2

    def test_different_inputs_different_keys(self):
        k1 = _cache_key("q1", "a", '["c"]')
        k2 = _cache_key("q2", "a", '["c"]')
        assert k1 != k2

    def test_sha256_length(self):
        k = _cache_key("q", "a", '["c"]')
        assert len(k) == 64

    def test_long_answer_truncated(self):
        short = _cache_key("q", "a" * 100, '["c"]')
        long = _cache_key("q", "a" * 3000, '["c"]')
        assert short != long


# ── _parse_dece_scores ──────────────────────────────────────────────────────


class TestParseDeCEScores:
    def test_dece_format(self):
        raw = '{"listening": {"score": 0.8, "quote": "I hear", "confidence": 0.9}}'
        scores, details = _parse_dece_scores(raw)
        assert scores == {"listening": 0.8}
        assert len(details) == 1
        assert details[0]["concept_id"] == "listening"
        assert details[0]["quote"] == "I hear"

    def test_legacy_float_format(self):
        raw = '{"listening": 0.8, "empathy": 0.6}'
        scores, details = _parse_dece_scores(raw)
        assert scores == {"listening": 0.8, "empathy": 0.6}
        assert details is None

    def test_mixed_format(self):
        raw = '{"listening": {"score": 0.8, "quote": null, "confidence": 0.5}, "empathy": 0.6}'
        scores, details = _parse_dece_scores(raw)
        assert "listening" in scores
        assert "empathy" in scores
        assert len(details) == 1

    def test_strips_markdown_fences(self):
        raw = '```json\n{"listening": 0.8}\n```'
        scores, _ = _parse_dece_scores(raw)
        assert scores == {"listening": 0.8}

    def test_invalid_json(self):
        scores, details = _parse_dece_scores("not json")
        assert scores is None
        assert details is None

    def test_non_dict_json(self):
        scores, details = _parse_dece_scores("[1, 2, 3]")
        assert scores is None

    def test_score_clamped_to_0_1(self):
        raw = '{"x": {"score": 1.5, "quote": null, "confidence": 0.5}}'
        scores, _ = _parse_dece_scores(raw)
        assert scores["x"] == 1.0

    def test_negative_score_clamped(self):
        raw = '{"x": {"score": -0.5, "quote": null, "confidence": 0.5}}'
        scores, _ = _parse_dece_scores(raw)
        assert scores["x"] == 0.0

    def test_null_string_quote_treated_as_none(self):
        raw = '{"x": {"score": 0.5, "quote": "null", "confidence": 0.5}}'
        _, details = _parse_dece_scores(raw)
        assert details[0]["quote"] is None

    def test_html_escaped_quote(self):
        raw = '{"x": {"score": 0.5, "quote": "<script>alert(1)</script>", "confidence": 0.5}}'
        _, details = _parse_dece_scores(raw)
        assert "<script>" not in details[0]["quote"]

    def test_long_quote_truncated(self):
        long_quote = "a" * 300
        raw = f'{{"x": {{"score": 0.5, "quote": "{long_quote}", "confidence": 0.5}}}}'
        _, details = _parse_dece_scores(raw)
        assert len(details[0]["quote"]) <= 200


# ── _parse_json_scores (legacy wrapper) ─────────────────────────────────────


class TestParseJsonScores:
    def test_returns_flat_scores(self):
        raw = '{"listening": 0.8}'
        scores = _parse_json_scores(raw)
        assert scores == {"listening": 0.8}

    def test_returns_none_on_bad_input(self):
        assert _parse_json_scores("bad") is None


# ── _aggregate ──────────────────────────────────────────────────────────────


class TestAggregate:
    def test_equal_weights(self):
        scores = {"a": 0.8, "b": 0.6}
        concepts = [{"name": "a"}, {"name": "b"}]
        result = _aggregate(scores, concepts)
        assert result == pytest.approx(0.7, abs=0.01)

    def test_weighted(self):
        scores = {"a": 1.0, "b": 0.0}
        concepts = [{"name": "a", "weight": 3.0}, {"name": "b", "weight": 1.0}]
        result = _aggregate(scores, concepts)
        assert result == pytest.approx(0.75, abs=0.01)

    def test_empty_scores(self):
        assert _aggregate({}, [{"name": "a"}]) == 0.0

    def test_missing_concept_in_scores(self):
        scores = {"a": 0.8}
        concepts = [{"name": "a"}, {"name": "b"}]
        result = _aggregate(scores, concepts)
        assert result == pytest.approx(0.4, abs=0.01)

    def test_clamped_0_1(self):
        scores = {"a": 1.5}
        concepts = [{"name": "a"}]
        result = _aggregate(scores, concepts)
        assert 0.0 <= result <= 1.0

    def test_concept_key_compatibility(self):
        scores = {"a": 0.5}
        concepts = [{"concept": "a"}]
        result = _aggregate(scores, concepts)
        assert result == pytest.approx(0.5, abs=0.01)


# ── _is_negated ─────────────────────────────────────────────────────────────


class TestIsNegated:
    def test_negated(self):
        assert _is_negated("i never implement security", "implement") is True

    def test_not_negated(self):
        assert _is_negated("i implement security measures", "implement") is False

    def test_dont_negation(self):
        assert _is_negated("i don't use monitoring", "monitoring") is True

    def test_far_negation_not_detected(self):
        assert _is_negated("i never said i would but i do implement things", "implement") is False

    def test_no_occurrence(self):
        assert _is_negated("this is unrelated text", "implement") is False

    def test_multiple_occurrences_one_negated(self):
        assert _is_negated("i never implement but then implement again", "implement") is True


# ── _is_incoherent_dump ─────────────────────────────────────────────────────


class TestIsIncoherentDump:
    def test_keyword_dump(self):
        answer = "vault rotate least_privilege env secret configure monitor token"
        assert _is_incoherent_dump(answer, 8) is True

    def test_coherent_answer(self):
        answer = "I would implement monitoring by deploying a dashboard and configuring alerts to track metrics"
        assert _is_incoherent_dump(answer, 4) is False

    def test_below_threshold(self):
        assert _is_incoherent_dump("some text", 2) is False


# ── _answer_relevance_penalty ───────────────────────────────────────────────


class TestAnswerRelevancePenalty:
    def test_relevant_answer(self):
        q = "How would you handle a security incident at an event?"
        a = "I would handle the security incident by following the protocol"
        assert _answer_relevance_penalty(q, a) is False

    def test_offtopic_answer(self):
        q = "How would you handle a security incident at an event?"
        a = "The quick brown fox jumps over the lazy dog repeatedly"
        assert _answer_relevance_penalty(q, a) is True

    def test_empty_question(self):
        assert _answer_relevance_penalty("", "some answer") is False

    def test_short_question(self):
        assert _answer_relevance_penalty("Hi?", "some answer text here") is False

    def test_empty_answer_content(self):
        # "a b" has no content tokens (words >= 3 chars), so a_tokens is empty → True
        # but "a" and "b" are only 1 char, _content_tokens filters words < 3 chars
        assert _answer_relevance_penalty("How would you handle security incidents at events?", "ok") is True


# ── _keyword_fallback ───────────────────────────────────────────────────────


class TestKeywordFallback:
    def test_basic_keyword_match(self):
        concepts = [{"name": "security", "keywords": ["firewall", "encryption", "access"]}]
        answer = "I would configure the firewall and set up encryption"
        scores = _keyword_fallback(answer, concepts)
        assert scores["security"] > 0.0

    def test_no_keywords_default(self):
        concepts = [{"name": "general"}]
        scores = _keyword_fallback("any text here", concepts)
        assert scores["general"] == 0.5

    def test_short_answer_capped(self):
        concepts = [{"name": "x", "keywords": ["firewall", "encryption"]}]
        answer = "firewall encryption"
        scores = _keyword_fallback(answer, concepts)
        assert scores["x"] <= 0.4

    def test_negated_keyword_not_counted(self):
        concepts = [{"name": "x", "keywords": ["monitoring"]}]
        answer = "I never use monitoring tools because they are expensive"
        scores = _keyword_fallback(answer, concepts)
        assert scores["x"] == 0.0

    def test_stuffing_penalty(self):
        keywords = [f"kw{i}" for i in range(10)]
        concepts = [{"name": "x", "keywords": keywords}]
        answer = " ".join(keywords[:8])
        scores = _keyword_fallback(answer, concepts)
        assert scores["x"] < 0.5

    def test_relevance_penalty(self):
        concepts = [{"name": "x", "keywords": ["deploy"]}]
        answer = "I would deploy the application to production using CI/CD pipelines"
        scores = _keyword_fallback(
            answer,
            concepts,
            question_text="How do you handle customer complaints about billing errors?",
        )
        assert scores["x"] <= 1.0

    def test_concept_key_compat(self):
        concepts = [{"concept": "x", "keywords": ["test"]}]
        answer = "we test everything thoroughly before deployment to production"
        scores = _keyword_fallback(answer, concepts)
        assert "x" in scores


# ── EvaluationResult ────────────────────────────────────────────────────────


class TestEvaluationResult:
    def test_to_log_full_mode(self):
        r = EvaluationResult(0.75, {"a": 0.8}, "gemini-2.5-flash")
        log = r.to_log()
        assert log["evaluation_mode"] == "full"
        assert log["composite_score"] == 0.75

    def test_to_log_degraded_mode(self):
        r = EvaluationResult(0.5, {"a": 0.5}, "keyword_fallback")
        log = r.to_log()
        assert log["evaluation_mode"] == "degraded"

    def test_to_log_with_details(self):
        details = [{"concept_id": "a", "score": 0.8, "quote": "test", "confidence": 0.9}]
        r = EvaluationResult(0.8, {"a": 0.8}, "gemini", concept_details=details)
        log = r.to_log()
        assert "concept_details" in log
        assert len(log["concept_details"]) == 1

    def test_to_log_without_details(self):
        r = EvaluationResult(0.5, {"a": 0.5}, "gemini")
        log = r.to_log()
        assert "concept_details" not in log

    def test_scores_rounded(self):
        r = EvaluationResult(0.333333, {"a": 0.666666}, "test")
        log = r.to_log()
        assert log["composite_score"] == 0.333
        assert log["concept_scores"]["a"] == 0.667
