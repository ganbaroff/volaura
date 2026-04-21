"""Coverage tests for app.services.cross_product_bridge — tick 7b.

Targets missing lines:
  53-54   _mindshift_url: body (url present, url absent)
  96-137  _post_event: httpx success, 4xx failure, timeout, generic exception,
          circuit-open skip, unconfigured (no base url)
  161-174 push_crystal_earned: payload construction + ensure_future
  201-214 push_skill_verified: payload construction + ensure_future
  238-249 push_xp_earned: payload construction + ensure_future

asyncio_mode = "auto" (pyproject.toml) — no @pytest.mark.asyncio needed.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.cross_product_bridge as mod
from app.services.cross_product_bridge import (
    _is_circuit_open,
    _mindshift_url,
    _post_event,
    push_crystal_earned,
    push_skill_verified,
    push_xp_earned,
    reset_circuit_breaker,
)


# ── Module-state reset (circuit breaker globals) ──────────────────────────────


@pytest.fixture(autouse=True)
def _reset_cb():
    """Reset circuit breaker before and after every test in this file."""
    reset_circuit_breaker()
    yield
    reset_circuit_breaker()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_settings(**kwargs: object) -> SimpleNamespace:
    defaults = {"mindshift_url": "https://mindshift.example.com"}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_httpx_response(status_code: int, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


# ── _mindshift_url (lines 53-54) ──────────────────────────────────────────────


class TestMindshiftUrl:
    def test_returns_stripped_url_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """URL with trailing slash gets stripped (line 54)."""
        monkeypatch.setattr(mod, "settings", _fake_settings(mindshift_url="https://ms.example.com/"))
        result = _mindshift_url()
        assert result == "https://ms.example.com"

    def test_returns_url_without_trailing_slash(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """URL without trailing slash returned as-is."""
        monkeypatch.setattr(mod, "settings", _fake_settings(mindshift_url="https://ms.example.com"))
        result = _mindshift_url()
        assert result == "https://ms.example.com"

    def test_returns_none_when_not_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns None when mindshift_url is falsy (line 54 not reached)."""
        monkeypatch.setattr(mod, "settings", _fake_settings(mindshift_url=None))
        assert _mindshift_url() is None

    def test_returns_none_when_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty string mindshift_url also returns None."""
        monkeypatch.setattr(mod, "settings", _fake_settings(mindshift_url=""))
        assert _mindshift_url() is None


# ── _post_event (lines 96-137) ────────────────────────────────────────────────


class TestPostEvent:
    """Cover all branches of _post_event."""

    async def test_no_base_url_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No MINDSHIFT_URL configured → returns True (not a failure)."""
        monkeypatch.setattr(mod, "settings", _fake_settings(mindshift_url=None))
        result = await _post_event("/api/character/events", {"x": 1}, None)
        assert result is True

    async def test_circuit_open_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Circuit open → returns False without making HTTP call."""
        monkeypatch.setattr(mod, "settings", _fake_settings())
        # Trip the circuit breaker
        for _ in range(mod._CB_THRESHOLD):
            mod._record_failure()
        assert _is_circuit_open() is True

        result = await _post_event("/api/character/events", {}, "token")
        assert result is False

    async def test_success_2xx_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """2xx response → _record_success called, returns True."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=_make_httpx_response(200))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _post_event("/api/character/events", {"k": "v"}, "jwt-token")

        assert result is True
        assert mod._cb_failures == 0  # reset on success

    async def test_success_201_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """201 Created is still < 300 → success path."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=_make_httpx_response(201))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _post_event("/api/character/events", {}, None)

        assert result is True

    async def test_4xx_response_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """4xx response → _record_failure called, returns False."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=_make_httpx_response(422, "Unprocessable"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _post_event("/api/character/events", {}, "jwt")

        assert result is False
        assert mod._cb_failures == 1

    async def test_5xx_response_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """5xx response → failure recorded."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=_make_httpx_response(503, "Service Unavailable"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _post_event("/api/character/events", {}, None)

        assert result is False

    async def test_timeout_exception_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """httpx.TimeoutException → failure recorded, returns False."""
        import httpx

        monkeypatch.setattr(mod, "settings", _fake_settings())

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _post_event("/endpoint", {}, None)

        assert result is False
        assert mod._cb_failures == 1

    async def test_generic_exception_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Any other exception → failure recorded, returns False."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = AsyncMock(side_effect=OSError("network unreachable"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _post_event("/endpoint", {}, "jwt")

        assert result is False
        assert mod._cb_failures == 1

    async def test_jwt_injected_into_authorization_header(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """user_jwt ends up in Authorization: Bearer header."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        captured_headers: dict = {}

        async def _capture_post(url: str, json: dict, headers: dict) -> MagicMock:
            captured_headers.update(headers)
            return _make_httpx_response(200)

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = _capture_post
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await _post_event("/api/character/events", {}, "my-jwt-token")

        assert captured_headers.get("Authorization") == "Bearer my-jwt-token"

    async def test_no_jwt_no_authorization_header(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """user_jwt=None → no Authorization header added."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        captured_headers: dict = {}

        async def _capture_post(url: str, json: dict, headers: dict) -> MagicMock:
            captured_headers.update(headers)
            return _make_httpx_response(200)

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = _capture_post
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await _post_event("/api/character/events", {}, None)

        assert "Authorization" not in captured_headers

    @pytest.mark.parametrize(
        "endpoint, status, expected_result",
        [
            pytest.param("/api/character/events", 200, True, id="успех_200"),
            pytest.param("/api/character/events", 404, False, id="не_найдено_404"),
            pytest.param("/api/character/events", 500, False, id="ошибка_сервера_500"),
        ],
    )
    async def test_parametrize_status_codes(
        self,
        endpoint: str,
        status: int,
        expected_result: bool,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Status code determines return value across common scenarios."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        with patch("app.services.cross_product_bridge.httpx.AsyncClient") as mock_cls:
            instance = AsyncMock()
            instance.post = AsyncMock(return_value=_make_httpx_response(status))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _post_event(endpoint, {}, None)

        assert result is expected_result


# ── push_crystal_earned (lines 161-174) ──────────────────────────────────────


def _draining_ensure_future(coro: object) -> MagicMock:
    """Close the coroutine immediately to prevent 'never awaited' warnings."""
    import inspect
    if inspect.iscoroutine(coro):
        coro.close()  # type: ignore[union-attr]
    return MagicMock()


class TestPushCrystalEarned:
    """Cover push_crystal_earned payload + ensure_future call."""

    async def test_schedules_future(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ensure_future is called — fire-and-forget queued."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        with patch(
            "app.services.cross_product_bridge.asyncio.ensure_future",
            side_effect=_draining_ensure_future,
        ) as mock_ef:
            await push_crystal_earned("user-abc", amount=50, skill_slug="communication")
        mock_ef.assert_called_once()

    async def test_logger_debug_called(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """logger.debug fires after queuing."""
        monkeypatch.setattr(mod, "settings", _fake_settings())

        with (
            patch(
                "app.services.cross_product_bridge.asyncio.ensure_future",
                side_effect=_draining_ensure_future,
            ),
            patch("app.services.cross_product_bridge.logger") as mock_logger,
        ):
            await push_crystal_earned("uid-x", amount=25, skill_slug="empathy")

        mock_logger.debug.assert_called_once()

    @pytest.mark.parametrize(
        "user_id, amount, skill_slug",
        [
            pytest.param("uid-1", 10, "communication", id="маленькое_количество"),
            pytest.param("uid-2", 9999, "leadership", id="большое_количество"),
            pytest.param("uid-3", 0, "reliability", id="нулевое_количество"),
        ],
    )
    async def test_various_amounts(
        self, user_id: str, amount: int, skill_slug: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Function executes without error for various crystal amounts."""
        monkeypatch.setattr(mod, "settings", _fake_settings())
        with patch(
            "app.services.cross_product_bridge.asyncio.ensure_future",
            side_effect=_draining_ensure_future,
        ):
            await push_crystal_earned(user_id, amount=amount, skill_slug=skill_slug)


# ── push_skill_verified (lines 201-214) ──────────────────────────────────────


class TestPushSkillVerified:
    """Cover push_skill_verified payload + ensure_future call."""

    async def test_schedules_future(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ensure_future is called."""
        monkeypatch.setattr(mod, "settings", _fake_settings())
        with patch(
            "app.services.cross_product_bridge.asyncio.ensure_future",
            side_effect=_draining_ensure_future,
        ) as mock_ef:
            await push_skill_verified("uid-1", "communication", "gold", 78.5)
        mock_ef.assert_called_once()

    async def test_logger_debug_called(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """logger.debug fires."""
        monkeypatch.setattr(mod, "settings", _fake_settings())
        with (
            patch(
                "app.services.cross_product_bridge.asyncio.ensure_future",
                side_effect=_draining_ensure_future,
            ),
            patch("app.services.cross_product_bridge.logger") as mock_logger,
        ):
            await push_skill_verified("uid-x", "leadership", None, 55.0)
        mock_logger.debug.assert_called_once()

    @pytest.mark.parametrize(
        "badge_tier, aura_score",
        [
            pytest.param("platinum", 92.0, id="платина_высокий_балл"),
            pytest.param("bronze", 35.5, id="бронза_низкий_балл"),
            pytest.param(None, 60.0, id="нет_значка"),
        ],
    )
    async def test_various_badge_tiers(
        self, badge_tier: str | None, aura_score: float, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Function completes for all badge tier values including None."""
        monkeypatch.setattr(mod, "settings", _fake_settings())
        with patch(
            "app.services.cross_product_bridge.asyncio.ensure_future",
            side_effect=_draining_ensure_future,
        ):
            await push_skill_verified("uid-1", "communication", badge_tier, aura_score)


# ── push_xp_earned (lines 238-249) ───────────────────────────────────────────


class TestPushXpEarned:
    """Cover push_xp_earned payload + ensure_future call."""

    async def test_schedules_future(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ensure_future is called."""
        monkeypatch.setattr(mod, "settings", _fake_settings())
        with patch(
            "app.services.cross_product_bridge.asyncio.ensure_future",
            side_effect=_draining_ensure_future,
        ) as mock_ef:
            await push_xp_earned("uid-1", amount=200, reason="profile_complete")
        mock_ef.assert_called_once()

    async def test_logger_debug_called(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """logger.debug fires."""
        monkeypatch.setattr(mod, "settings", _fake_settings())
        with (
            patch(
                "app.services.cross_product_bridge.asyncio.ensure_future",
                side_effect=_draining_ensure_future,
            ),
            patch("app.services.cross_product_bridge.logger") as mock_logger,
        ):
            await push_xp_earned("uid-x", amount=50, reason="first_assessment")
        mock_logger.debug.assert_called_once()

    @pytest.mark.parametrize(
        "amount, reason",
        [
            pytest.param(100, "profile_complete", id="профиль_завершён"),
            pytest.param(500, "first_assessment", id="первая_оценка"),
            pytest.param(1, "daily_login", id="ежедневный_вход"),
        ],
    )
    async def test_various_xp_reasons(
        self, amount: int, reason: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Function completes for common XP reason slugs."""
        monkeypatch.setattr(mod, "settings", _fake_settings())
        with patch(
            "app.services.cross_product_bridge.asyncio.ensure_future",
            side_effect=_draining_ensure_future,
        ):
            await push_xp_earned("uid-2", amount=amount, reason=reason)
