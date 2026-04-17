"""Unit tests for app.services.loop_circuit_breaker — multi-signal loop detector."""

import pytest
from pydantic import ValidationError

from app.services.loop_circuit_breaker import (
    DEFAULT_MIN_UNIQUE_TOKENS,
    DEFAULT_STALL_BLOCKLIST,
    LoopBreakDecision,
    LoopCircuitBreaker,
    _unique_tokens,
)

# ── _unique_tokens ──────────────────────────────────────────────────────


class TestUniqueTokens:
    def test_empty_string(self):
        assert _unique_tokens("") == 0

    def test_single_word(self):
        assert _unique_tokens("hello") == 1

    def test_duplicates_collapsed(self):
        assert _unique_tokens("hello hello hello") == 1

    def test_case_insensitive(self):
        assert _unique_tokens("Hello HELLO hello") == 1

    def test_mixed_words(self):
        assert _unique_tokens("the quick brown fox") == 4

    def test_russian_tokens(self):
        assert _unique_tokens("привет мир привет") == 2

    def test_mixed_cyrillic_latin(self):
        assert _unique_tokens("hello привет world мир") == 4

    def test_punctuation_stripped(self):
        assert _unique_tokens("hello, world! foo.") == 3

    def test_numbers_count(self):
        assert _unique_tokens("test 123 456 test") == 3

    def test_none_like_empty(self):
        assert _unique_tokens("   ") == 0


# ── LoopBreakDecision ───────────────────────────────────────────────────


class TestLoopBreakDecision:
    def test_not_tripped_describe(self):
        d = LoopBreakDecision(tripped=False)
        assert d.describe() == "no loop"

    def test_tripped_describe(self):
        d = LoopBreakDecision(
            tripped=True,
            signals=["token_velocity", "no_progress"],
            reason="low tokens; stall phrase",
        )
        assert "LOOP" in d.describe()
        assert "token_velocity" in d.describe()

    def test_frozen_model(self):
        d = LoopBreakDecision(tripped=False)
        with pytest.raises(ValidationError):
            d.tripped = True  # type: ignore[misc]

    def test_default_signals_empty(self):
        d = LoopBreakDecision(tripped=False)
        assert d.signals == []
        assert d.reason == ""


# ── Signal: token velocity ──────────────────────────────────────────────


class TestSignalTokenVelocity:
    def setup_method(self):
        self.breaker = LoopCircuitBreaker(min_unique_tokens=5, window_size=3)

    def test_not_enough_replies(self):
        assert self.breaker._signal_token_velocity(["a b"]) is False

    def test_all_below_threshold(self):
        replies = ["a b", "c d", "e f"]
        assert self.breaker._signal_token_velocity(replies) is True

    def test_one_above_threshold(self):
        replies = ["a b", "c d", "one two three four five six"]
        assert self.breaker._signal_token_velocity(replies) is False

    def test_all_above_threshold(self):
        replies = ["one two three four five", "a b c d e", "x y z w v"]
        assert self.breaker._signal_token_velocity(replies) is False

    def test_window_uses_last_n(self):
        replies = ["one two three four five", "a", "b", "c"]
        assert self.breaker._signal_token_velocity(replies) is True

    def test_empty_replies_list(self):
        assert self.breaker._signal_token_velocity([]) is False


# ── Signal: no progress ─────────────────────────────────────────────────


class TestSignalNoProgress:
    def setup_method(self):
        self.breaker = LoopCircuitBreaker()

    def test_empty_replies(self):
        hit, phrase = self.breaker._signal_no_progress([])
        assert hit is False

    def test_stall_phrase_detected(self):
        replies = ["something something я понимаю что это важно"]
        hit, phrase = self.breaker._signal_no_progress(replies)
        assert hit is True
        assert "я понимаю что" in phrase

    def test_english_stall_phrase(self):
        replies = ["I understand that this is complex"]
        hit, phrase = self.breaker._signal_no_progress(replies)
        assert hit is True

    def test_no_stall_phrase(self):
        replies = ["вот конкретный план действий: 1) фиксим баг 2) деплоим"]
        hit, phrase = self.breaker._signal_no_progress(replies)
        assert hit is False

    def test_case_insensitive(self):
        replies = ["AS I MENTIONED BEFORE, this is important"]
        hit, _ = self.breaker._signal_no_progress(replies)
        assert hit is True

    def test_uses_last_reply_only(self):
        replies = ["я понимаю что", "конкретный результат здесь"]
        hit, _ = self.breaker._signal_no_progress(replies)
        assert hit is False

    def test_custom_stall_phrases(self):
        breaker = LoopCircuitBreaker(stall_phrases=("custom_stall",))
        hit, _ = breaker._signal_no_progress(["this has custom_stall in it"])
        assert hit is True


# ── Signal: tool failure ────────────────────────────────────────────────


class TestSignalToolFailure:
    def setup_method(self):
        self.breaker = LoopCircuitBreaker(tool_failure_threshold=3)

    def test_no_errors(self):
        hit, _ = self.breaker._signal_tool_failure({})
        assert hit is False

    def test_below_threshold(self):
        hit, _ = self.breaker._signal_tool_failure({"github_issue": 2})
        assert hit is False

    def test_at_threshold(self):
        hit, tool = self.breaker._signal_tool_failure({"github_issue": 3})
        assert hit is True
        assert tool == "github_issue"

    def test_above_threshold(self):
        hit, tool = self.breaker._signal_tool_failure({"search": 10})
        assert hit is True
        assert tool == "search"

    def test_none_uses_internal_counter(self):
        self.breaker.record_tool_failure("api")
        self.breaker.record_tool_failure("api")
        self.breaker.record_tool_failure("api")
        hit, tool = self.breaker._signal_tool_failure(None)
        assert hit is True
        assert tool == "api"

    def test_success_resets_counter(self):
        self.breaker.record_tool_failure("api")
        self.breaker.record_tool_failure("api")
        self.breaker.record_tool_success("api")
        self.breaker.record_tool_failure("api")
        hit, _ = self.breaker._signal_tool_failure(None)
        assert hit is False


# ── evaluate() — 2-of-3 voting ─────────────────────────────────────────


class TestEvaluate:
    def test_no_signals_no_trip(self):
        breaker = LoopCircuitBreaker(min_unique_tokens=5, window_size=2)
        decision = breaker.evaluate(
            recent_replies=["one two three four five six", "seven eight nine ten eleven twelve"],
        )
        assert decision.tripped is False
        assert decision.signals == []

    def test_one_signal_no_trip(self):
        breaker = LoopCircuitBreaker(min_unique_tokens=100, window_size=2)
        decision = breaker.evaluate(recent_replies=["short", "reply"])
        assert decision.tripped is False
        assert len(decision.signals) == 1
        assert "token_velocity" in decision.signals

    def test_two_signals_trip(self):
        breaker = LoopCircuitBreaker(min_unique_tokens=100, window_size=2)
        decision = breaker.evaluate(
            recent_replies=["short", "я понимаю что это сложно"],
        )
        assert decision.tripped is True
        assert len(decision.signals) == 2
        assert "token_velocity" in decision.signals
        assert "no_progress" in decision.signals

    def test_all_three_signals_trip(self):
        breaker = LoopCircuitBreaker(min_unique_tokens=100, window_size=2, tool_failure_threshold=1)
        decision = breaker.evaluate(
            recent_replies=["short", "я понимаю что"],
            tool_error_streak={"search": 1},
        )
        assert decision.tripped is True
        assert len(decision.signals) == 3

    def test_token_velocity_plus_tool_failure(self):
        breaker = LoopCircuitBreaker(min_unique_tokens=100, window_size=2, tool_failure_threshold=2)
        decision = breaker.evaluate(
            recent_replies=["a", "b"],
            tool_error_streak={"db": 5},
        )
        assert decision.tripped is True
        assert "token_velocity" in decision.signals
        assert "per_tool_failure" in decision.signals

    def test_no_progress_plus_tool_failure(self):
        breaker = LoopCircuitBreaker(min_unique_tokens=1, window_size=2, tool_failure_threshold=2)
        long_stall = "word " * 50 + "as i mentioned before this is complex"
        decision = breaker.evaluate(
            recent_replies=["normal reply with many words", long_stall],
            tool_error_streak={"api": 3},
        )
        assert decision.tripped is True
        assert "no_progress" in decision.signals
        assert "per_tool_failure" in decision.signals

    def test_reason_contains_details(self):
        breaker = LoopCircuitBreaker(min_unique_tokens=100, window_size=2)
        decision = breaker.evaluate(
            recent_replies=["a", "я понимаю что blah"],
        )
        assert "unique tokens" in decision.reason
        assert "stall phrase" in decision.reason


# ── Defaults ────────────────────────────────────────────────────────────


class TestDefaults:
    def test_default_min_unique_tokens(self):
        assert DEFAULT_MIN_UNIQUE_TOKENS == 30

    def test_default_stall_blocklist_not_empty(self):
        assert len(DEFAULT_STALL_BLOCKLIST) >= 8

    def test_default_stall_blocklist_all_lowercase(self):
        for phrase in DEFAULT_STALL_BLOCKLIST:
            assert phrase == phrase.lower(), f"blocklist entry not lowercase: {phrase!r}"

    def test_default_window_size(self):
        breaker = LoopCircuitBreaker()
        assert breaker.window_size == 3

    def test_default_tool_failure_threshold(self):
        breaker = LoopCircuitBreaker()
        assert breaker.tool_failure_threshold == 3
