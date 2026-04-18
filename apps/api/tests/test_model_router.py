"""Unit tests for app.services.model_router — role-based provider selection."""

from dataclasses import FrozenInstanceError
from unittest.mock import patch

import pytest

from app.services.model_router import ProviderRole, ProviderSpec, select_provider


def _mock_settings(**overrides):
    """Return a mock settings object with sensible defaults (all keys empty)."""
    defaults = {
        "cerebras_api_key": "",
        "nvidia_api_key": "",
        "gemini_api_key": "",
        "groq_api_key": "",
        "anthropic_api_key": "",
        "ollama_enabled": False,
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen3:8b",
    }
    defaults.update(overrides)

    class FakeSettings:
        pass

    s = FakeSettings()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


# ── ProviderRole enum ───────────────────────────────────────────────────


class TestProviderRole:
    def test_four_roles(self):
        assert len(ProviderRole) == 4

    def test_role_values(self):
        assert ProviderRole.JUDGE == "judge"
        assert ProviderRole.WORKER == "worker"
        assert ProviderRole.FAST == "fast"
        assert ProviderRole.SAFE_USER_FACING == "safe_user_facing"


# ── ProviderSpec ────────────────────────────────────────────────────────


class TestProviderSpec:
    def test_frozen(self):
        spec = ProviderSpec(provider="test", model="m", base_url=None, api_key="k", rationale="r", is_fallback=False)
        with pytest.raises(FrozenInstanceError):
            spec.provider = "other"  # type: ignore[misc]

    def test_fields(self):
        spec = ProviderSpec(
            provider="cerebras",
            model="qwen-3-235b",
            base_url="http://x",
            api_key="sk-x",
            rationale="test",
            is_fallback=True,
        )
        assert spec.provider == "cerebras"
        assert spec.is_fallback is True


# ── select_provider — no keys configured ────────────────────────────────


class TestSelectProviderNoKeys:
    @patch("app.services.model_router.settings", _mock_settings())
    def test_judge_returns_none(self):
        assert select_provider(ProviderRole.JUDGE) is None

    @patch("app.services.model_router.settings", _mock_settings())
    def test_worker_returns_none(self):
        assert select_provider(ProviderRole.WORKER) is None

    @patch("app.services.model_router.settings", _mock_settings())
    def test_fast_returns_none(self):
        assert select_provider(ProviderRole.FAST) is None

    @patch("app.services.model_router.settings", _mock_settings())
    def test_safe_user_facing_returns_none(self):
        assert select_provider(ProviderRole.SAFE_USER_FACING) is None


# ── select_provider — cerebras primary ──────────────────────────────────


class TestSelectProviderCerebras:
    @patch("app.services.model_router.settings", _mock_settings(cerebras_api_key="sk-test"))
    def test_judge_selects_cerebras(self):
        spec = select_provider(ProviderRole.JUDGE)
        assert spec is not None
        assert spec.provider == "cerebras"
        assert spec.model == "qwen-3-235b"
        assert spec.is_fallback is False

    @patch("app.services.model_router.settings", _mock_settings(cerebras_api_key="sk-test"))
    def test_worker_does_not_select_cerebras(self):
        spec = select_provider(ProviderRole.WORKER)
        assert spec is None

    @patch("app.services.model_router.settings", _mock_settings(cerebras_api_key="sk-test"))
    def test_fast_does_not_select_cerebras(self):
        spec = select_provider(ProviderRole.FAST)
        assert spec is None


# ── select_provider — ollama ────────────────────────────────────────────


class TestSelectProviderOllama:
    @patch("app.services.model_router.settings", _mock_settings(ollama_enabled=True))
    def test_worker_selects_ollama(self):
        spec = select_provider(ProviderRole.WORKER)
        assert spec is not None
        assert spec.provider == "ollama"
        assert spec.api_key == ""
        assert spec.is_fallback is False

    @patch("app.services.model_router.settings", _mock_settings(ollama_enabled=False))
    def test_ollama_disabled(self):
        spec = select_provider(ProviderRole.WORKER)
        assert spec is None


# ── select_provider — nvidia ────────────────────────────────────────────


class TestSelectProviderNvidia:
    @patch("app.services.model_router.settings", _mock_settings(nvidia_api_key="nvapi-test"))
    def test_judge_nvidia_nemotron(self):
        spec = select_provider(ProviderRole.JUDGE)
        assert spec is not None
        assert spec.provider == "nvidia"
        assert "nemotron" in spec.model

    @patch("app.services.model_router.settings", _mock_settings(nvidia_api_key="nvapi-test"))
    def test_worker_nvidia_llama(self):
        spec = select_provider(ProviderRole.WORKER)
        assert spec is not None
        assert spec.provider == "nvidia"
        assert "llama" in spec.model

    @patch("app.services.model_router.settings", _mock_settings(nvidia_api_key="nvapi-test"))
    def test_fast_nvidia_llama(self):
        spec = select_provider(ProviderRole.FAST)
        assert spec is not None
        assert spec.provider == "nvidia"


# ── select_provider — gemini ────────────────────────────────────────────


class TestSelectProviderGemini:
    @patch("app.services.model_router.settings", _mock_settings(gemini_api_key="AIzaSyTest"))
    def test_safe_user_facing_selects_gemini_pro(self):
        spec = select_provider(ProviderRole.SAFE_USER_FACING)
        assert spec is not None
        assert spec.provider == "gemini"
        assert "pro" in spec.model

    @patch("app.services.model_router.settings", _mock_settings(gemini_api_key="AIzaSyTest"))
    def test_fast_selects_gemini_flash(self):
        spec = select_provider(ProviderRole.FAST)
        assert spec is not None
        assert spec.provider == "gemini"
        assert "flash" in spec.model


# ── select_provider — groq ──────────────────────────────────────────────


class TestSelectProviderGroq:
    @patch("app.services.model_router.settings", _mock_settings(groq_api_key="gsk_test"))
    def test_fast_selects_groq_8b(self):
        spec = select_provider(ProviderRole.FAST)
        assert spec is not None
        assert spec.provider == "groq"
        assert "8b" in spec.model

    @patch("app.services.model_router.settings", _mock_settings(groq_api_key="gsk_test"))
    def test_worker_selects_groq_70b(self):
        spec = select_provider(ProviderRole.WORKER)
        assert spec is not None
        assert spec.provider == "groq"
        assert "70b" in spec.model


# ── select_provider — anthropic last resort ─────────────────────────────


class TestSelectProviderAnthropic:
    @patch("app.services.model_router.settings", _mock_settings(anthropic_api_key="sk-ant-test"))
    def test_safe_user_facing_anthropic_last_resort(self):
        spec = select_provider(ProviderRole.SAFE_USER_FACING)
        assert spec is not None
        assert spec.provider == "anthropic"
        assert spec.is_fallback is True

    @patch("app.services.model_router.settings", _mock_settings(anthropic_api_key="sk-ant-test"))
    def test_judge_never_anthropic(self):
        spec = select_provider(ProviderRole.JUDGE)
        assert spec is None

    @patch("app.services.model_router.settings", _mock_settings(anthropic_api_key="sk-ant-test"))
    def test_worker_never_anthropic(self):
        spec = select_provider(ProviderRole.WORKER)
        assert spec is None

    @patch("app.services.model_router.settings", _mock_settings(anthropic_api_key="sk-ant-test"))
    def test_fast_never_anthropic(self):
        spec = select_provider(ProviderRole.FAST)
        assert spec is None


# ── Fallback marking ────────────────────────────────────────────────────


class TestFallbackMarking:
    @patch("app.services.model_router.settings", _mock_settings(nvidia_api_key="nvapi-test"))
    def test_judge_nvidia_is_fallback_when_not_primary(self):
        spec = select_provider(ProviderRole.JUDGE)
        assert spec is not None
        assert spec.is_fallback is True
        assert "fallback" in spec.rationale.lower()

    @patch("app.services.model_router.settings", _mock_settings(cerebras_api_key="sk-test"))
    def test_judge_cerebras_is_not_fallback(self):
        spec = select_provider(ProviderRole.JUDGE)
        assert spec is not None
        assert spec.is_fallback is False

    @patch("app.services.model_router.settings", _mock_settings(ollama_enabled=True))
    def test_worker_ollama_is_primary(self):
        spec = select_provider(ProviderRole.WORKER)
        assert spec is not None
        assert spec.is_fallback is False

    @patch("app.services.model_router.settings", _mock_settings(nvidia_api_key="nvapi-test"))
    def test_worker_nvidia_is_fallback(self):
        spec = select_provider(ProviderRole.WORKER)
        assert spec is not None
        assert spec.is_fallback is True
