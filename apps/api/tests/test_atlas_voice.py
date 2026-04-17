"""Unit tests for app.services.atlas_voice — system prompt builder + file loader."""

from __future__ import annotations

import os
import tempfile

from app.services.atlas_voice import _REPO_ROOT, _load_file, build_atlas_system_prompt


class TestLoadFile:
    def test_missing_file_returns_empty(self):
        result = _load_file("nonexistent/path/file.md", 1000)
        assert result == ""

    def test_truncates_at_max_chars(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("x" * 500)
            f.flush()
            rel = os.path.relpath(f.name, _REPO_ROOT)
        try:
            result = _load_file(rel, 100)
            assert len(result) == 100
        finally:
            os.unlink(f.name)

    def test_reads_full_content_under_limit(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8", dir=str(_REPO_ROOT)) as f:
            f.write("hello atlas")
            f.flush()
            rel = os.path.relpath(f.name, _REPO_ROOT)
        try:
            result = _load_file(rel, 1000)
            assert result == "hello atlas"
        finally:
            os.unlink(f.name)


class TestBuildAtlasSystemPrompt:
    def test_contains_atlas_identity(self):
        prompt = build_atlas_system_prompt()
        assert "Atlas" in prompt

    def test_contains_volaura_positioning(self):
        prompt = build_atlas_system_prompt()
        assert "volunteer" not in prompt.lower() or "Never say" in prompt

    def test_surface_telegram(self):
        prompt = build_atlas_system_prompt(surface="telegram")
        assert "Telegram" in prompt
        assert "3 paragraphs" in prompt

    def test_surface_aura_reflection(self):
        prompt = build_atlas_system_prompt(surface="aura_reflection")
        assert "AURA" in prompt
        assert "strength-first" in prompt

    def test_surface_assessment_coaching(self):
        prompt = build_atlas_system_prompt(surface="assessment_coaching")
        assert "shame-free" in prompt

    def test_surface_lifesim_narrator(self):
        prompt = build_atlas_system_prompt(surface="lifesim_narrator")
        assert "narrating" in prompt

    def test_surface_generic_fallback(self):
        prompt = build_atlas_system_prompt(surface="unknown_surface")
        assert "Russian storytelling" in prompt

    def test_user_context_included(self):
        prompt = build_atlas_system_prompt(user_context="AURA score: 85, Gold badge")
        assert "AURA score: 85" in prompt

    def test_user_context_empty(self):
        prompt = build_atlas_system_prompt(user_context="")
        assert "USER CONTEXT" not in prompt

    def test_max_chars_truncation(self):
        prompt = build_atlas_system_prompt(max_chars=100)
        assert len(prompt) <= 100

    def test_named_by_yusif(self):
        prompt = build_atlas_system_prompt()
        assert "Yusif" in prompt
        assert "2026-04-12" in prompt

    def test_never_volunteer(self):
        prompt = build_atlas_system_prompt()
        assert 'Never say "volunteer"' in prompt

    def test_voice_rules_section(self):
        prompt = build_atlas_system_prompt()
        assert "VOICE RULES" in prompt

    def test_surface_section(self):
        prompt = build_atlas_system_prompt(surface="telegram")
        assert "SURFACE:" in prompt
