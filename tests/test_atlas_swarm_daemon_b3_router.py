"""Phase B3 — daemon LiteLLM router fallback tests.

Tests the env-gated `_call_litellm_router_fallback` helper and its
integration into `call_provider_chain`. Goal: prove flag-off behaviour
preserves the current AGENT_LLM_MAP per-agent diversity (CEO directive
2026-04-30 "сколько у нас LLM столько и агентов") AND that flag-on adds
a router safety net only AFTER the assigned model fails.

Reference: codex-loop.md Phase B3.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Any

from tests._paths import script_path as repo_script_path


def _load_daemon():
    script_path = repo_script_path("atlas_swarm_daemon.py")
    spec = importlib.util.spec_from_file_location("atlas_swarm_daemon_b3_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _run(coro):
    return asyncio.run(coro)


# ── helper-level tests ────────────────────────────────────────────────────────

def test_router_fallback_returns_none_when_litellm_unavailable(monkeypatch):
    daemon = _load_daemon()

    # Force the helper to see _LITELLM_AVAILABLE=False via the module it imports.
    import packages.swarm.providers.litellm_adapter as adapter
    monkeypatch.setattr(adapter, "_LITELLM_AVAILABLE", False)

    result = _run(daemon._call_litellm_router_fallback("TestAgent", "hello", 0.5))
    assert result is None


def test_router_fallback_returns_proper_shape_on_success(monkeypatch):
    daemon = _load_daemon()
    import packages.swarm.providers.litellm_adapter as adapter

    monkeypatch.setattr(adapter, "_LITELLM_AVAILABLE", True)

    fake_response = {"verdict": "OK", "evidence": ["one", "two"]}

    class _FakeProvider:
        def __init__(self):
            pass

        async def evaluate(self, prompt, temperature=0.7):
            return fake_response

    monkeypatch.setattr(adapter, "LiteLLMProvider", _FakeProvider)

    result = _run(daemon._call_litellm_router_fallback("Security", "Audit X", 0.3))
    assert result is not None
    assert result["perspective"] == "Security"
    assert result["provider"] == "litellm-router"
    assert "router/" in result["model"]
    assert result["router_fallback"] is True
    assert json.loads(result["raw"]) == fake_response


def test_router_fallback_returns_none_when_evaluate_raises(monkeypatch):
    daemon = _load_daemon()
    import packages.swarm.providers.litellm_adapter as adapter

    monkeypatch.setattr(adapter, "_LITELLM_AVAILABLE", True)

    class _FailingProvider:
        async def evaluate(self, prompt, temperature=0.7):
            raise RuntimeError("simulated upstream 503")

    monkeypatch.setattr(adapter, "LiteLLMProvider", _FailingProvider)

    result = _run(daemon._call_litellm_router_fallback("TestAgent", "hi", 0.5))
    assert result is None


def test_router_fallback_returns_none_when_evaluate_returns_non_dict(monkeypatch):
    daemon = _load_daemon()
    import packages.swarm.providers.litellm_adapter as adapter

    monkeypatch.setattr(adapter, "_LITELLM_AVAILABLE", True)

    class _StringProvider:
        async def evaluate(self, prompt, temperature=0.7):
            return "not a dict"  # type: ignore[return-value]

    monkeypatch.setattr(adapter, "LiteLLMProvider", _StringProvider)

    result = _run(daemon._call_litellm_router_fallback("TestAgent", "hi", 0.5))
    assert result is None


# ── call_provider_chain integration tests ─────────────────────────────────────

def _stub_chain_deps(daemon, monkeypatch):
    """Stub the auxiliary helpers so chain logic can be tested in isolation."""
    monkeypatch.setattr(daemon, "_get_smart_temperature", lambda name, prompt: 0.5)
    monkeypatch.setattr(daemon, "_load_agent_config", lambda name: {"max_tokens": 1500})

    async def _no_subagents(*args, **kwargs):
        return ""

    monkeypatch.setattr(daemon, "_fan_out_sub_agents", _no_subagents)
    # HEAVY_PERSPECTIVES test isolation: ensure no fan-out triggers regardless.
    monkeypatch.setattr(daemon, "HEAVY_PERSPECTIVES", set())
    # Ensure the chain sees a known agent in AGENT_LLM_MAP
    daemon.AGENT_LLM_MAP.setdefault("B3TestAgent", ("ollama", "qwen3:8b"))


def test_chain_router_not_called_when_flag_off(monkeypatch):
    """Default behaviour preserved: flag off + assigned fails → router untouched."""
    daemon = _load_daemon()
    _stub_chain_deps(daemon, monkeypatch)

    async def _assigned_fails(*args, **kwargs):
        return None

    router_calls: list[str] = []

    async def _router_should_not_run(name, prompt, temp):
        router_calls.append(name)
        return None

    monkeypatch.setattr(daemon, "_call_assigned_model", _assigned_fails)
    monkeypatch.setattr(daemon, "_call_litellm_router_fallback", _router_should_not_run)
    monkeypatch.delenv("ATLAS_USE_LITELLM_ROUTER", raising=False)

    result = _run(daemon.call_provider_chain({"name": "B3TestAgent"}, "hi"))
    assert result["error"] == "assigned_model_failed"
    assert router_calls == [], "Router must not be called when flag is off"


def test_chain_router_called_when_flag_on_and_assigned_fails(monkeypatch):
    daemon = _load_daemon()
    _stub_chain_deps(daemon, monkeypatch)

    async def _assigned_fails(*args, **kwargs):
        return None

    async def _router_succeeds(name, prompt, temp):
        return {
            "perspective": name,
            "provider": "litellm-router",
            "model": "router/cerebras→ollama→nvidia",
            "raw": json.dumps({"verdict": "rescued"}),
            "router_fallback": True,
        }

    monkeypatch.setattr(daemon, "_call_assigned_model", _assigned_fails)
    monkeypatch.setattr(daemon, "_call_litellm_router_fallback", _router_succeeds)
    monkeypatch.setenv("ATLAS_USE_LITELLM_ROUTER", "1")

    result = _run(daemon.call_provider_chain({"name": "B3TestAgent"}, "hi"))
    assert result["provider"] == "litellm-router"
    assert result["router_fallback"] is True
    assert result.get("assigned_llm") is False, "Router-rescued result must not claim assigned_llm"
    parsed = json.loads(result["raw"])
    assert parsed["verdict"] == "rescued"


def test_chain_router_not_called_when_assigned_succeeds(monkeypatch):
    """Diversity preserved on the happy path even when flag is on."""
    daemon = _load_daemon()
    _stub_chain_deps(daemon, monkeypatch)

    async def _assigned_ok(name, provider, model, prompt, temp, max_tok):
        return {"perspective": name, "provider": provider, "model": model, "raw": '{"ok": true}'}

    router_calls: list[str] = []

    async def _router_should_not_run(name, prompt, temp):
        router_calls.append(name)
        return None

    monkeypatch.setattr(daemon, "_call_assigned_model", _assigned_ok)
    monkeypatch.setattr(daemon, "_call_litellm_router_fallback", _router_should_not_run)
    monkeypatch.setenv("ATLAS_USE_LITELLM_ROUTER", "1")

    result = _run(daemon.call_provider_chain({"name": "B3TestAgent"}, "hi"))
    assert result["assigned_llm"] is True
    assert result["raw"] == '{"ok": true}'
    assert router_calls == [], (
        "Router must not be called when assigned model succeeds (CEO 2026-04-30: per-agent diversity)"
    )
