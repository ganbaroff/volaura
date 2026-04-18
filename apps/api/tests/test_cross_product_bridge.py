"""Tests for app.services.cross_product_bridge — circuit breaker + pure functions."""

from __future__ import annotations

import time

import pytest

from app.services.cross_product_bridge import (
    _CB_SILENCE_SEC,
    _CB_THRESHOLD,
    _CB_WINDOW_SEC,
    _is_circuit_open,
    _record_failure,
    _record_success,
    reset_circuit_breaker,
)


@pytest.fixture(autouse=True)
def _clean_cb():
    reset_circuit_breaker()
    yield
    reset_circuit_breaker()


class TestCircuitBreaker:
    def test_starts_closed(self):
        assert _is_circuit_open() is False

    def test_opens_after_threshold_failures(self):
        for _ in range(_CB_THRESHOLD):
            _record_failure()
        assert _is_circuit_open() is True

    def test_stays_closed_below_threshold(self):
        for _ in range(_CB_THRESHOLD - 1):
            _record_failure()
        assert _is_circuit_open() is False

    def test_success_resets_counter(self):
        for _ in range(_CB_THRESHOLD - 1):
            _record_failure()
        _record_success()
        _record_failure()
        assert _is_circuit_open() is False

    def test_circuit_reopens_after_silence(self):
        for _ in range(_CB_THRESHOLD):
            _record_failure()
        assert _is_circuit_open() is True

        import app.services.cross_product_bridge as mod

        mod._cb_silenced_until = time.monotonic() - 1
        assert _is_circuit_open() is False

    def test_window_resets_after_expiry(self):
        _record_failure()
        _record_failure()

        import app.services.cross_product_bridge as mod

        mod._cb_window_start = time.monotonic() - _CB_WINDOW_SEC - 1
        _record_failure()
        assert _is_circuit_open() is False

    def test_reset_clears_all(self):
        for _ in range(_CB_THRESHOLD):
            _record_failure()
        assert _is_circuit_open() is True
        reset_circuit_breaker()
        assert _is_circuit_open() is False


class TestConstants:
    def test_threshold_positive(self):
        assert _CB_THRESHOLD > 0

    def test_window_positive(self):
        assert _CB_WINDOW_SEC > 0

    def test_silence_positive(self):
        assert _CB_SILENCE_SEC > 0
