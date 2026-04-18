"""Tests for middleware modules: request_id, rate_limit, security_headers, error_alerting."""

import hashlib
import time
from unittest.mock import MagicMock, patch

import pytest

from app.middleware.rate_limit import RATE_AUTH, RATE_DEFAULT, RATE_DISCOVERY, _key_func
from app.middleware.request_id import _MAX_ID_LEN, _get_or_generate_request_id

# ---------------------------------------------------------------------------
# request_id — _get_or_generate_request_id
# ---------------------------------------------------------------------------


def _make_request(headers: dict | None = None) -> MagicMock:
    req = MagicMock()
    req.headers = headers or {}
    return req


class TestGetOrGenerateRequestId:
    def test_generates_uuid_when_no_header(self):
        req = _make_request({})
        rid = _get_or_generate_request_id(req)
        assert len(rid) == 36
        assert rid.count("-") == 4

    def test_passes_through_valid_header(self):
        req = _make_request({"x-request-id": "my-trace-123"})
        assert _get_or_generate_request_id(req) == "my-trace-123"

    def test_rejects_too_long_header(self):
        req = _make_request({"x-request-id": "x" * (_MAX_ID_LEN + 1)})
        rid = _get_or_generate_request_id(req)
        assert rid != "x" * (_MAX_ID_LEN + 1)
        assert len(rid) == 36

    def test_rejects_non_ascii_header(self):
        req = _make_request({"x-request-id": "трейс-ид-кириллица"})
        rid = _get_or_generate_request_id(req)
        assert rid != "трейс-ид-кириллица"
        assert len(rid) == 36

    def test_accepts_max_length_header(self):
        val = "a" * _MAX_ID_LEN
        req = _make_request({"x-request-id": val})
        assert _get_or_generate_request_id(req) == val

    def test_empty_header_generates_new(self):
        req = _make_request({"x-request-id": ""})
        rid = _get_or_generate_request_id(req)
        assert len(rid) == 36


# ---------------------------------------------------------------------------
# rate_limit — _key_func
# ---------------------------------------------------------------------------


class TestKeyFunc:
    def test_unauthenticated_returns_ip(self):
        req = MagicMock()
        req.headers = {}
        with patch("app.middleware.rate_limit.get_remote_address", return_value="1.2.3.4"):
            key = _key_func(req)
        assert key == "1.2.3.4"

    def test_authenticated_returns_ip_plus_hash(self):
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.sig"
        req = MagicMock()
        req.headers = {"authorization": f"Bearer {token}"}
        expected_hash = hashlib.sha256(token.encode()).hexdigest()[:24]
        with patch("app.middleware.rate_limit.get_remote_address", return_value="10.0.0.1"):
            key = _key_func(req)
        assert key == f"10.0.0.1:{expected_hash}"

    def test_different_tokens_different_keys(self):
        req1 = MagicMock()
        req1.headers = {"authorization": "Bearer token-aaa"}
        req2 = MagicMock()
        req2.headers = {"authorization": "Bearer token-bbb"}
        with patch("app.middleware.rate_limit.get_remote_address", return_value="1.1.1.1"):
            k1 = _key_func(req1)
            k2 = _key_func(req2)
        assert k1 != k2

    def test_non_bearer_treated_as_unauthenticated(self):
        req = MagicMock()
        req.headers = {"authorization": "Basic dXNlcjpwYXNz"}
        with patch("app.middleware.rate_limit.get_remote_address", return_value="5.5.5.5"):
            key = _key_func(req)
        assert key == "5.5.5.5"


class TestRateLimitConstants:
    def test_auth_rate_is_strict(self):
        assert RATE_AUTH == "5/minute"

    def test_discovery_rate_is_tight(self):
        assert RATE_DISCOVERY == "10/minute"

    def test_default_rate_is_relaxed(self):
        assert RATE_DEFAULT == "60/minute"


# ---------------------------------------------------------------------------
# error_alerting — _send_telegram_alert cooldown + message format
# ---------------------------------------------------------------------------


class TestErrorAlertingCooldown:
    @pytest.mark.asyncio
    async def test_cooldown_prevents_spam(self):
        import app.middleware.error_alerting as ea

        ea._last_alert_time = time.time()
        result = await ea._send_telegram_alert(500, "/api/test", "GET")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_token_skips_silently(self):
        import app.middleware.error_alerting as ea

        ea._last_alert_time = 0
        with patch.object(ea, "settings") as mock_settings:
            mock_settings.telegram_bot_token = ""
            mock_settings.telegram_ceo_chat_id = ""
            result = await ea._send_telegram_alert(500, "/api/test", "POST")
        assert result is None


# ---------------------------------------------------------------------------
# security_headers — CSP policy content
# ---------------------------------------------------------------------------


class TestSecurityHeadersCSP:
    def test_csp_blocks_all_default_src(self):
        from app.middleware.security_headers import _CSP_PRODUCTION

        assert "default-src 'none'" in _CSP_PRODUCTION

    def test_csp_blocks_frames(self):
        from app.middleware.security_headers import _CSP_PRODUCTION

        assert "frame-ancestors 'none'" in _CSP_PRODUCTION

    def test_csp_blocks_form_action(self):
        from app.middleware.security_headers import _CSP_PRODUCTION

        assert "form-action 'none'" in _CSP_PRODUCTION

    def test_csp_blocks_base_uri(self):
        from app.middleware.security_headers import _CSP_PRODUCTION

        assert "base-uri 'none'" in _CSP_PRODUCTION


# ---------------------------------------------------------------------------
# config.py — Settings properties + assert_production_ready
# ---------------------------------------------------------------------------


class TestSettingsProperties:
    def test_is_dev_true_for_development(self):
        from app.config import Settings

        s = Settings(app_env="development")
        assert s.is_dev is True

    def test_is_dev_false_for_production(self):
        from app.config import Settings

        s = Settings(app_env="production")
        assert s.is_dev is False

    def test_effective_anon_key_prefers_jwt(self):
        from app.config import Settings

        s = Settings(supabase_anon_key="anon", supabase_anon_jwt="jwt")
        assert s.effective_anon_key == "jwt"

    def test_effective_anon_key_falls_back_to_anon(self):
        from app.config import Settings

        s = Settings(supabase_anon_key="anon", supabase_anon_jwt="")
        assert s.effective_anon_key == "anon"

    def test_using_hardcoded_anon_key_when_both_empty(self):
        from app.config import Settings

        s = Settings(supabase_anon_key="", supabase_anon_jwt="")
        assert s.using_hardcoded_anon_key is True

    def test_cors_dev_returns_localhost(self):
        from app.config import Settings

        s = Settings(app_env="development")
        origins = s.cors_origins
        assert "http://localhost:3000" in origins

    def test_cors_prod_includes_known_domains(self):
        from app.config import Settings

        s = Settings(app_env="production", app_url="https://volaura.app")
        origins = s.cors_origins
        assert "https://volaura.app" in origins
        assert "https://www.volaura.app" in origins

    def test_cors_prod_includes_mindshift_when_set(self):
        from app.config import Settings

        s = Settings(app_env="production", app_url="https://volaura.app", mindshift_url="https://mindshift.app")
        assert "https://mindshift.app" in s.cors_origins


class TestAssertProductionReady:
    def test_blocks_old_supabase_project(self):
        from app.config import Settings, assert_production_ready

        with (
            patch("app.config.settings", Settings(supabase_url="https://hvykysvdkalkbswmgfut.supabase.co")),
            pytest.raises(RuntimeError, match="old project"),
        ):
            assert_production_ready()

    def test_passes_in_dev_mode(self):
        from app.config import Settings, assert_production_ready

        with patch(
            "app.config.settings",
            Settings(app_env="development", supabase_url="https://dwdgzfusjsobnixgyzjk.supabase.co"),
        ):
            assert_production_ready()

    def test_blocks_prod_without_service_key(self):
        from app.config import Settings, assert_production_ready

        with (
            patch(
                "app.config.settings",
                Settings(
                    app_env="production",
                    supabase_url="https://dwdgzfusjsobnixgyzjk.supabase.co",
                    supabase_service_key="",
                    app_url="https://volaura.app",
                    telegram_webhook_secret="secret",
                ),
            ),
            pytest.raises(RuntimeError, match="SUPABASE_SERVICE_KEY"),
        ):
            assert_production_ready()


class TestValidateProductionSettings:
    def test_warns_no_llm_keys(self):
        from app.config import Settings, validate_production_settings

        with patch(
            "app.config.settings",
            Settings(
                app_env="production",
                supabase_url="https://dwdgzfusjsobnixgyzjk.supabase.co",
                gemini_api_key="",
                groq_api_key="",
                openai_api_key="",
            ),
        ):
            warnings = validate_production_settings()
        assert any("LLM" in w or "keyword fallback" in w for w in warnings)

    def test_no_warnings_in_dev(self):
        from app.config import Settings, validate_production_settings

        with patch("app.config.settings", Settings(app_env="development")):
            warnings = validate_production_settings()
        assert len(warnings) == 0
