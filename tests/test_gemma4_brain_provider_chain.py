"""ADR-013 (2026-05-09) — brain provider precedence + Cerebras gating tests.

CEO directive 2026-05-09 after $7.25 of $10 Cerebras paid balance burned in
~10 hours: brain MUST NOT call Cerebras by default. Cerebras only when env
flag ATLAS_ENABLE_CEREBRAS=true is set. First-tried provider must be a
credits-backed/free-tier one (Groq / Gemini / NVIDIA).

These tests pin the contract so a future refactor that re-promotes Cerebras
to the head of the chain breaks the build.

Reference: docs/adr/ADR-013-2026-05-09-cerebras-spend-incident.md
           memory/atlas/lessons.md Class 38
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch


def _load_brain():
    script_path = Path("C:/Projects/VOLAURA/scripts/gemma4_brain.py")
    assert script_path.exists(), f"canonical brain missing: {script_path}"
    spec = importlib.util.spec_from_file_location(
        "gemma4_brain_test_chain", script_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


# ── fake response helpers ────────────────────────────────────────────────────


class _FakeResponse:
    """Context-managed fake of urllib.request urlopen() return value."""

    def __init__(self, body: dict):
        self._body = json.dumps(body).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _openai_shape(content: str) -> _FakeResponse:
    return _FakeResponse({"choices": [{"message": {"content": content}}]})


def _gemini_shape(content: str) -> _FakeResponse:
    return _FakeResponse(
        {"candidates": [{"content": {"parts": [{"text": content}]}}]}
    )


def _ollama_shape(content: str) -> _FakeResponse:
    return _FakeResponse({"response": content})


def _request_url(req) -> str:
    return req.full_url if hasattr(req, "full_url") else str(req)


# ── ADR-013 §a — Cerebras off by default ─────────────────────────────────────


def test_default_chain_does_not_call_cerebras(monkeypatch):
    """With default env (no ATLAS_ENABLE_CEREBRAS), Cerebras URL must not
    appear in any urlopen call even when CEREBRAS_API_KEY is present."""
    brain = _load_brain()

    monkeypatch.setenv("CEREBRAS_API_KEY", "fake-cerebras-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.delenv("ATLAS_ENABLE_CEREBRAS", raising=False)

    called_urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = _request_url(req)
        called_urls.append(url)
        return _openai_shape("hello-from-mock-groq")

    with patch("urllib.request.urlopen", fake_urlopen):
        out = brain.call_brain_llm("test prompt", max_tokens=100)

    assert out == "hello-from-mock-groq"
    assert any("groq.com" in u for u in called_urls), (
        f"Groq must be called first when key present, got URLs: {called_urls}"
    )
    assert not any("cerebras.ai" in u for u in called_urls), (
        f"Cerebras MUST NOT be called by default (ADR-013), got URLs: {called_urls}"
    )


def test_cerebras_skipped_when_env_flag_unset_even_with_key(monkeypatch):
    """If CEREBRAS_API_KEY is set but ATLAS_ENABLE_CEREBRAS is NOT 'true',
    every other provider is exhausted yet Cerebras is still untouched."""
    brain = _load_brain()

    monkeypatch.setenv("CEREBRAS_API_KEY", "fake-cerebras-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.setenv("NVIDIA_API_KEY", "fake-nvidia-key")
    monkeypatch.delenv("ATLAS_ENABLE_CEREBRAS", raising=False)

    called_urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = _request_url(req)
        called_urls.append(url)
        # ALL non-cerebras providers fail; Cerebras would succeed but must not be tried
        raise Exception(f"simulated provider down: {url}")

    with patch("urllib.request.urlopen", fake_urlopen):
        out = brain.call_brain_llm("test", 50)

    assert out == ""
    assert not any("cerebras.ai" in u for u in called_urls), (
        f"Cerebras MUST stay off when ATLAS_ENABLE_CEREBRAS unset, got: {called_urls}"
    )
    # Sanity: at least Groq / Gemini / NVIDIA were tried
    assert any("groq.com" in u for u in called_urls)
    assert any("generativelanguage" in u for u in called_urls)
    assert any("nvidia.com" in u for u in called_urls)


def test_cerebras_skipped_when_env_flag_explicitly_false(monkeypatch):
    """ATLAS_ENABLE_CEREBRAS=false (or anything other than 'true') = off."""
    brain = _load_brain()

    monkeypatch.setenv("CEREBRAS_API_KEY", "fake-cerebras-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.setenv("ATLAS_ENABLE_CEREBRAS", "false")

    called_urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = _request_url(req)
        called_urls.append(url)
        return _openai_shape("hello")

    with patch("urllib.request.urlopen", fake_urlopen):
        brain.call_brain_llm("test", 50)

    assert not any("cerebras.ai" in u for u in called_urls), (
        f"ATLAS_ENABLE_CEREBRAS=false must keep Cerebras off, got: {called_urls}"
    )


def test_cerebras_skipped_when_env_flag_random_truthy(monkeypatch):
    """Only literal 'true' (case-insensitive) opens the gate. '1', 'yes',
    'on' etc. must NOT be honoured — explicit string contract."""
    brain = _load_brain()

    monkeypatch.setenv("CEREBRAS_API_KEY", "fake-cerebras-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")

    for not_true in ("1", "yes", "on", "TRUE-ish", "enabled", "Y"):
        monkeypatch.setenv("ATLAS_ENABLE_CEREBRAS", not_true)
        called_urls: list[str] = []

        def fake_urlopen(req, timeout=None):
            url = _request_url(req)
            called_urls.append(url)
            raise Exception("groq down")

        with patch("urllib.request.urlopen", fake_urlopen):
            brain.call_brain_llm("test", 50)

        assert not any("cerebras.ai" in u for u in called_urls), (
            f"Only literal 'true' opens the gate; '{not_true}' must NOT, "
            f"got URLs: {called_urls}"
        )


# ── ADR-013 §a — Cerebras attempted only when explicitly enabled ─────────────


def test_cerebras_attempted_when_env_flag_true_and_others_fail(monkeypatch):
    """Cerebras becomes last-resort fallback when ATLAS_ENABLE_CEREBRAS=true."""
    brain = _load_brain()

    monkeypatch.setenv("CEREBRAS_API_KEY", "fake-cerebras-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.setenv("NVIDIA_API_KEY", "fake-nvidia-key")
    monkeypatch.setenv("ATLAS_ENABLE_CEREBRAS", "true")

    called_urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = _request_url(req)
        called_urls.append(url)
        if "cerebras.ai" in url:
            return _openai_shape("from-cerebras-paid")
        raise Exception(f"simulated free-provider failure for {url}")

    with patch("urllib.request.urlopen", fake_urlopen):
        out = brain.call_brain_llm("test prompt", max_tokens=100)

    assert out == "from-cerebras-paid"
    assert any("cerebras.ai" in u for u in called_urls), (
        f"Cerebras must be reachable when ATLAS_ENABLE_CEREBRAS=true and "
        f"every free provider fails; URLs: {called_urls}"
    )
    # Cerebras must be LAST in the order — every free provider tried first
    cerebras_idx = next(
        (i for i, u in enumerate(called_urls) if "cerebras.ai" in u), -1
    )
    assert cerebras_idx == len(called_urls) - 1, (
        f"Cerebras must be last attempted, not first; URLs: {called_urls}"
    )


# ── ADR-013 §a — provider order ──────────────────────────────────────────────


def test_provider_order_groq_first(monkeypatch):
    """First provider tried must be Groq (per CEO directive 2026-05-09)."""
    brain = _load_brain()

    monkeypatch.setenv("GROQ_API_KEY", "fake")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setenv("NVIDIA_API_KEY", "fake")
    monkeypatch.delenv("ATLAS_ENABLE_CEREBRAS", raising=False)

    called_urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = _request_url(req)
        called_urls.append(url)
        return _openai_shape("first-try-success")

    with patch("urllib.request.urlopen", fake_urlopen):
        brain.call_brain_llm("test", 50)

    assert called_urls and "groq.com" in called_urls[0], (
        f"First call must be Groq, got: {called_urls}"
    )


def test_falls_back_to_gemini_when_groq_fails(monkeypatch):
    """Provider chain step 2: Groq fail -> try Gemini next (cerebras off)."""
    brain = _load_brain()

    monkeypatch.setenv("GROQ_API_KEY", "fake")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.delenv("ATLAS_ENABLE_CEREBRAS", raising=False)

    called_urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = _request_url(req)
        called_urls.append(url)
        if "groq.com" in url:
            raise Exception("groq down")
        if "generativelanguage" in url:
            return _gemini_shape("from-gemini")
        raise Exception(f"unexpected url {url}")

    with patch("urllib.request.urlopen", fake_urlopen):
        out = brain.call_brain_llm("test", 50)

    assert out == "from-gemini"
    assert "groq.com" in called_urls[0]
    assert any("generativelanguage" in u for u in called_urls)


def test_falls_back_to_nvidia_when_groq_and_gemini_fail(monkeypatch):
    """Provider chain step 3: Groq + Gemini fail -> try NVIDIA next."""
    brain = _load_brain()

    monkeypatch.setenv("GROQ_API_KEY", "fake")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setenv("NVIDIA_API_KEY", "fake")
    monkeypatch.delenv("ATLAS_ENABLE_CEREBRAS", raising=False)

    called_urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = _request_url(req)
        called_urls.append(url)
        if "nvidia.com" in url:
            return _openai_shape("from-nvidia")
        raise Exception(f"upstream down: {url}")

    with patch("urllib.request.urlopen", fake_urlopen):
        out = brain.call_brain_llm("test", 50)

    assert out == "from-nvidia"
    assert any("nvidia.com" in u for u in called_urls)


def test_falls_back_to_ollama_when_clouds_fail(monkeypatch):
    """Provider chain step 4: every cloud free provider fails -> try Ollama."""
    brain = _load_brain()

    monkeypatch.setenv("GROQ_API_KEY", "fake")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setenv("NVIDIA_API_KEY", "fake")
    monkeypatch.delenv("ATLAS_ENABLE_CEREBRAS", raising=False)

    called_urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = _request_url(req)
        called_urls.append(url)
        if "11434" in url or "ollama" in url:
            return _ollama_shape("from-ollama-local")
        raise Exception("cloud down")

    with patch("urllib.request.urlopen", fake_urlopen):
        out = brain.call_brain_llm("test", 50)

    assert out == "from-ollama-local"


# ── canonical sanity ─────────────────────────────────────────────────────────


def test_canonical_brain_path_is_scripts_gemma4_brain():
    canonical = Path("C:/Projects/VOLAURA/scripts/gemma4_brain.py")
    assert canonical.exists()
    assert canonical.is_file()
