"""Tests for packages/swarm/providers/litellm_adapter.py.

Phase B1 — Constitution Article 0 enforcement.

Acceptance criteria (Codex memo 2026-05-08, codex-loop.md):
- Built router model_list contains no `anthropic/*` model.
- Router still includes at least one non-Anthropic route when env/local
  routes are available.
- Daemon untouched. Test does not import the daemon module.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_adapter_module():
    """Load packages.swarm.providers.litellm_adapter from absolute path.

    Mirrors the importlib pattern used in test_atlas_swarm_daemon_lock.py so
    these tests run cleanly from any CWD without requiring the package layout
    to be on sys.path.
    """
    repo_root = Path("C:/Projects/VOLAURA")
    script_path = repo_root / "packages" / "swarm" / "providers" / "litellm_adapter.py"
    # Adapter does ``from ..swarm_types import ProviderInfo`` and
    # ``from .base import LLMProvider`` — those resolve only when imported as a
    # package. So go through the canonical package import.
    import sys
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from packages.swarm.providers import litellm_adapter as module
    assert script_path.exists(), f"Adapter file missing: {script_path}"
    return module


# ── Pure model_list tests (no Router instantiation) ───────────────────────────

def test_forbidden_prefixes_includes_anthropic():
    adapter = _load_adapter_module()
    assert "anthropic/" in adapter._FORBIDDEN_MODEL_PREFIXES


def test_model_list_with_empty_env_has_only_ollama():
    """No keys set → only the no-key ollama-fb entry, never anthropic."""
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={})
    assert len(model_list) == 1
    assert model_list[0]["model_name"] == "ollama-fb"
    assert _no_anthropic(model_list)


def test_model_list_with_anthropic_key_only_still_has_no_anthropic():
    """Even if ANTHROPIC_API_KEY is present, adapter MUST drop anthropic/*."""
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={"ANTHROPIC_API_KEY": "sk-ant-test"})
    assert _no_anthropic(model_list), (
        f"Anthropic route leaked into model_list: {[m['litellm_params']['model'] for m in model_list]}"
    )
    # Ollama always present as the no-key local fallback.
    assert any(m["model_name"] == "ollama-fb" for m in model_list)


def test_model_list_with_cerebras_and_anthropic_keeps_cerebras_drops_anthropic():
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={
        "CEREBRAS_API_KEY": "sk-cb-test",
        "ANTHROPIC_API_KEY": "sk-ant-test",
    })
    model_strings = [m["litellm_params"]["model"] for m in model_list]
    assert any(s.startswith("cerebras/") for s in model_strings)
    assert all(not s.startswith("anthropic/") for s in model_strings), model_strings


def test_model_list_with_all_keys_has_cerebras_ollama_nvidia_no_anthropic():
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={
        "CEREBRAS_API_KEY": "sk-cb-test",
        "NVIDIA_API_KEY": "nvapi-test",
        "ANTHROPIC_API_KEY": "sk-ant-test",
    })
    model_strings = [m["litellm_params"]["model"] for m in model_list]
    assert any(s.startswith("cerebras/") for s in model_strings)
    assert any(s.startswith("ollama/") for s in model_strings)
    assert any(s.startswith("nvidia_nim/") for s in model_strings)
    assert all(not s.startswith("anthropic/") for s in model_strings), model_strings


def test_model_names_unique():
    """Defensive: prevent duplicate model_name keys that would confuse Router fallback semantics."""
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={
        "CEREBRAS_API_KEY": "sk-cb-test",
        "NVIDIA_API_KEY": "nvapi-test",
    })
    names = [m["model_name"] for m in model_list]
    assert len(names) == len(set(names)), names


# ── End-to-end Router build (requires litellm 1.50+ in user-site) ──────────────

def test_build_router_model_list_has_no_anthropic_even_with_anthropic_key(monkeypatch):
    """Full _build_router path: Router instance's model_list contains no anthropic/*.

    Skipped if litellm is not importable (defensive — adapter test should not
    be the canary for litellm install state).
    """
    adapter = _load_adapter_module()
    if not adapter._LITELLM_AVAILABLE:
        pytest.skip("litellm not available in this environment")

    # Force-reset module router cache + scrub real keys so the test is hermetic.
    monkeypatch.setattr(adapter, "_router", None, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-only")
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    router = adapter._build_router()
    model_strings = [m["litellm_params"]["model"] for m in router.model_list]
    assert all(not s.startswith("anthropic/") for s in model_strings), model_strings
    # At least one non-anthropic route still present (ollama-fb is unconditional).
    assert len(model_strings) >= 1


def test_build_router_raises_when_safe_list_empty(monkeypatch):
    """If the only candidate is anthropic and it gets dropped, Router build must error.

    Crafted by patching _build_model_list so we cover the RuntimeError path
    without resorting to mocking out Router itself.
    """
    adapter = _load_adapter_module()
    if not adapter._LITELLM_AVAILABLE:
        pytest.skip("litellm not available in this environment")

    monkeypatch.setattr(adapter, "_build_model_list", lambda env=None: [])

    with pytest.raises(RuntimeError, match="No LLM credentials"):
        adapter._build_router()


# ── helpers ────────────────────────────────────────────────────────────────────

def _no_anthropic(model_list: list[dict]) -> bool:
    return all(
        not str(m.get("litellm_params", {}).get("model", "")).startswith("anthropic/")
        for m in model_list
    )
