"""Unit tests for rate limiter backend selection."""

from __future__ import annotations

from unittest.mock import patch

from app.middleware import rate_limit


def test_build_limiter_defaults_to_memory_when_redis_missing():
    with patch.object(rate_limit.settings, "redis_url", ""):
        limiter, backend = rate_limit._build_limiter()

    assert backend == "memory"
    assert limiter is not None


def test_build_limiter_uses_redis_when_configured():
    fake_limiter = object()
    with (
        patch.object(rate_limit.settings, "redis_url", "redis://localhost:6379/0"),
        patch.object(rate_limit, "Limiter", return_value=fake_limiter) as mock_limiter,
    ):
        limiter, backend = rate_limit._build_limiter()

    assert backend == "redis"
    assert limiter is fake_limiter
    mock_limiter.assert_called_once_with(
        key_func=rate_limit._key_func,
        storage_uri="redis://localhost:6379/0",
    )
