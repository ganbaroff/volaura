"""Coverage tests for app.services.email — async send functions.

Targets lines 112-165 (send_aura_ready_email) and 214-248 (send_ghosting_grace_email).
Expected: ≥90% coverage when combined with test_email_service.py.
asyncio_mode = "auto" in pyproject.toml — no @pytest.mark.asyncio needed.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

import app.services.email as email_mod

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_settings(monkeypatch):
    fake = SimpleNamespace(
        email_enabled=True,
        resend_api_key="re_test_key",
        app_url="https://volaura.app",
    )
    monkeypatch.setattr("app.services.email.settings", fake)
    return fake


def _mock_client(status_code: int = 200, text_body: str = "ok", raises=None):
    """Build a mock httpx.AsyncClient context manager."""
    instance = AsyncMock()
    if raises is not None:
        instance.post = AsyncMock(side_effect=raises)
    else:
        resp = MagicMock(status_code=status_code, text=text_body)
        instance.post = AsyncMock(return_value=resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=instance)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm, instance


# ---------------------------------------------------------------------------
# send_aura_ready_email — kill switch + no-key
# ---------------------------------------------------------------------------

class TestAuraReadyKillSwitch:
    async def test_disabled_returns_none_no_http(self, mock_settings):
        mock_settings.email_enabled = False
        with patch("app.services.email.httpx.AsyncClient") as mock_cls:
            result = await email_mod.send_aura_ready_email(
                "u@x.com", "Leyla", "communication", 80.0, "Gold", 5
            )
        assert result is None
        mock_cls.assert_not_called()

    async def test_no_api_key_returns_none(self, mock_settings):
        mock_settings.resend_api_key = ""
        with patch("app.services.email.httpx.AsyncClient") as mock_cls:
            result = await email_mod.send_aura_ready_email(
                "u@x.com", "Leyla", "communication", 80.0, "Gold"
            )
        assert result is None
        mock_cls.assert_not_called()


# ---------------------------------------------------------------------------
# send_aura_ready_email — HTTP status scenarios
# ---------------------------------------------------------------------------

class TestAuraReadyHttpScenarios:
    @pytest.mark.parametrize(
        "status_code,expected",
        [
            pytest.param(200, None, id="успех_200"),
            pytest.param(400, None, id="клиентская_ошибка_400"),
            pytest.param(500, None, id="пятисотка_500"),
        ],
    )
    async def test_http_status_codes(self, mock_settings, status_code, expected):
        cm, _ = _mock_client(status_code=status_code)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_aura_ready_email(
                "u@x.com", "Leyla", "adaptability", 75.0, "Silver", 10
            )
        assert result is expected

    async def test_request_error_returns_none_no_raise(self, mock_settings):
        """httpx.RequestError must NOT propagate — function returns None."""
        cm, _ = _mock_client(raises=httpx.RequestError("timeout"))
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_aura_ready_email(
                "u@x.com", "Leyla", "leadership", 60.0, "Bronze"
            )
        assert result is None

    async def test_timeout_exception_returns_none(self, mock_settings):
        cm, _ = _mock_client(raises=httpx.TimeoutException("read timeout"))
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_aura_ready_email(
                "u@x.com", "Leyla", "teamwork", 55.0, "Bronze"
            )
        assert result is None

    async def test_generic_exception_returns_none(self, mock_settings):
        cm, _ = _mock_client(raises=RuntimeError("boom"))
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_aura_ready_email(
                "u@x.com", "Leyla", "initiative", 50.0, "Bronze"
            )
        assert result is None


# ---------------------------------------------------------------------------
# send_aura_ready_email — payload & header verification
# ---------------------------------------------------------------------------

class TestAuraReadyPayload:
    async def test_post_payload_shape(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "user@test.com", "Kamran", "problem_solving", 88.4, "Gold", 20
            )
        call_kwargs = instance.post.call_args
        assert call_kwargs is not None
        json_body = call_kwargs.kwargs.get("json") or call_kwargs.args[1] if len(call_kwargs.args) > 1 else call_kwargs.kwargs["json"]
        assert json_body["to"] == ["user@test.com"]
        assert "Problem Solving" in json_body["subject"]
        assert json_body["from"] == "VOLAURA <noreply@volaura.app>"
        assert "<html" in json_body["html"].lower()

    async def test_auth_header_bearer(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "user@test.com", "Kamran", "communication", 70.0, "Silver"
            )
        call_kwargs = instance.post.call_args
        headers = call_kwargs.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer re_test_key"
        assert headers.get("Content-Type") == "application/json"

    async def test_score_rounded_in_html(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "u@x.com", "Ali", "adaptability", 77.6, "Gold"
            )
        html = instance.post.call_args.kwargs["json"]["html"]
        assert ">78<" in html

    async def test_crystals_in_html_when_positive(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "u@x.com", "Ali", "communication", 80.0, "Gold", crystals_earned=15
            )
        html = instance.post.call_args.kwargs["json"]["html"]
        assert "+15 crystals earned" in html

    async def test_no_crystals_when_zero(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "u@x.com", "Ali", "communication", 80.0, "Gold", crystals_earned=0
            )
        html = instance.post.call_args.kwargs["json"]["html"]
        assert "crystals earned" not in html


# ---------------------------------------------------------------------------
# send_aura_ready_email — display_name fallback + slug fallback
# ---------------------------------------------------------------------------

class TestAuraReadyFallbacks:
    async def test_display_name_none_uses_there(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "u@x.com", None, "communication", 70.0, "Silver"
            )
        html = instance.post.call_args.kwargs["json"]["html"]
        assert "there" in html

    async def test_display_name_empty_uses_there(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "u@x.com", "", "communication", 70.0, "Silver"
            )
        html = instance.post.call_args.kwargs["json"]["html"]
        assert "there" in html

    async def test_unknown_slug_humanized(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "u@x.com", "User", "critical_thinking", 65.0, "Bronze"
            )
        json_body = instance.post.call_args.kwargs["json"]
        assert "Critical Thinking" in json_body["subject"]

    async def test_known_slug_problem_solving(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_aura_ready_email(
                "u@x.com", "User", "problem_solving", 72.0, "Silver"
            )
        json_body = instance.post.call_args.kwargs["json"]
        assert "Problem Solving" in json_body["subject"]


# ---------------------------------------------------------------------------
# send_ghosting_grace_email — kill switch + no-key
# ---------------------------------------------------------------------------

class TestGhostingGraceKillSwitch:
    async def test_disabled_returns_false(self, mock_settings):
        mock_settings.email_enabled = False
        with patch("app.services.email.httpx.AsyncClient") as mock_cls:
            result = await email_mod.send_ghosting_grace_email("u@x.com", "Ali")
        assert result is False
        mock_cls.assert_not_called()

    async def test_no_api_key_returns_false(self, mock_settings):
        mock_settings.resend_api_key = ""
        with patch("app.services.email.httpx.AsyncClient") as mock_cls:
            result = await email_mod.send_ghosting_grace_email("u@x.com", "Ali")
        assert result is False
        mock_cls.assert_not_called()


# ---------------------------------------------------------------------------
# send_ghosting_grace_email — HTTP status scenarios
# ---------------------------------------------------------------------------

class TestGhostingGraceHttpScenarios:
    @pytest.mark.parametrize(
        "status_code,expected",
        [
            pytest.param(200, True, id="успех_200"),
            pytest.param(400, False, id="клиентская_ошибка_400"),
            pytest.param(500, False, id="пятисотка_500"),
        ],
    )
    async def test_http_status_codes(self, mock_settings, status_code, expected):
        cm, _ = _mock_client(status_code=status_code)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_ghosting_grace_email(
                "u@x.com", "Leyla", locale="en"
            )
        assert result is expected

    async def test_httpx_error_returns_false_no_raise(self, mock_settings):
        """httpx.RequestError — must NOT propagate."""
        cm, _ = _mock_client(raises=httpx.RequestError("network err"))
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_ghosting_grace_email("u@x.com", "Leyla")
        assert result is False

    async def test_timeout_exception_returns_false(self, mock_settings):
        cm, _ = _mock_client(raises=httpx.TimeoutException("read timeout"))
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_ghosting_grace_email("u@x.com", "Leyla")
        assert result is False

    async def test_generic_exception_returns_false(self, mock_settings):
        cm, _ = _mock_client(raises=OSError("socket closed"))
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_ghosting_grace_email("u@x.com", "Leyla")
        assert result is False


# ---------------------------------------------------------------------------
# send_ghosting_grace_email — locale and display_name
# ---------------------------------------------------------------------------

class TestGhostingGraceLocaleAndName:
    async def test_locale_az_in_html(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_ghosting_grace_email("u@x.com", "Kamran", locale="az")
        html = instance.post.call_args.kwargs["json"]["html"]
        assert "/az/assessment" in html

    async def test_locale_en_in_html(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_ghosting_grace_email("u@x.com", "Kamran", locale="en")
        html = instance.post.call_args.kwargs["json"]["html"]
        assert "/en/assessment" in html

    async def test_display_name_none_uses_there(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_ghosting_grace_email("u@x.com", None)
        html = instance.post.call_args.kwargs["json"]["html"]
        assert "there" in html

    async def test_display_name_empty_uses_there(self, mock_settings):
        cm, instance = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            await email_mod.send_ghosting_grace_email("u@x.com", "")
        html = instance.post.call_args.kwargs["json"]["html"]
        assert "there" in html

    async def test_returns_true_on_200(self, mock_settings):
        cm, _ = _mock_client(200)
        with patch("app.services.email.httpx.AsyncClient", return_value=cm):
            result = await email_mod.send_ghosting_grace_email("u@x.com", "Leyla")
        assert result is True
