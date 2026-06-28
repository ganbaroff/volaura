"""Tests for packages/swarm/providers/litellm_adapter.py.

Phase B1 — keep the LiteLLM adapter aligned with ADR-013.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _load_adapter_module():
    """Import the adapter from this worktree, not a hardcoded sibling checkout."""
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from packages.swarm.providers import litellm_adapter as module

    return module


def _model_strings(model_list: list[dict]) -> list[str]:
    return [str(m.get("litellm_params", {}).get("model", "")) for m in model_list]


def test_model_list_with_empty_env_has_only_ollama():
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={})
    assert len(model_list) == 1
    assert model_list[0]["model_name"] == "ollama-fb"
    assert _model_strings(model_list) == ["ollama/qwen3:8b"]


def test_model_list_drops_cerebras_and_anthropic():
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={
        "CEREBRAS_API_KEY": "sk-cb-test",
        "ANTHROPIC_API_KEY": "sk-ant-test",
    })
    model_strings = _model_strings(model_list)
    assert all(not s.startswith("cerebras/") for s in model_strings), model_strings
    assert all(not s.startswith("anthropic/") for s in model_strings), model_strings
    assert any(s.startswith("ollama/") for s in model_strings)


def test_model_list_with_all_keys_has_nvidia_ollama_gemini_no_cerebras():
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={
        "CEREBRAS_API_KEY": "sk-cb-test",
        "NVIDIA_API_KEY": "nvapi-test",
        "GEMINI_API_KEY": "gem-test",
        "ANTHROPIC_API_KEY": "sk-ant-test",
    })
    model_strings = _model_strings(model_list)
    assert any(s.startswith("nvidia_nim/") for s in model_strings)
    assert any(s.startswith("ollama/") for s in model_strings)
    assert any(s.startswith("gemini/") for s in model_strings)
    assert all(not s.startswith("cerebras/") for s in model_strings), model_strings
    assert all(not s.startswith("anthropic/") for s in model_strings), model_strings


def test_ollama_model_env_override_auto_prefixes():
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={"OLLAMA_MODEL": "qwen3:8b"})
    ollama = next(m for m in model_list if m["model_name"] == "ollama-fb")
    assert ollama["litellm_params"]["model"] == "ollama/qwen3:8b"


def test_model_names_unique():
    adapter = _load_adapter_module()
    model_list = adapter._build_model_list(env={
        "NVIDIA_API_KEY": "nvapi-test",
        "GEMINI_API_KEY": "gem-test",
    })
    names = [m["model_name"] for m in model_list]
    assert len(names) == len(set(names)), names
