"""Tests for domain-aware provider selection via TeamLead wiring in engine.py.

TDD: These tests define the expected behavior BEFORE implementation.
Run: pytest packages/swarm/tests/test_team_lead_wiring.py -v

Council prerequisite (Session 26):
- Attacker: must not change behavior when config.domain is None/GENERAL
- QA: must have explicit fallback when filtered pool is empty
- Scaling: pool cardinality change must be intentional and logged
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.swarm.team_leads import (
    ArchitectureTeamLead,
    SecurityTeamLead,
    SpeedTeamLead,
    get_tilead_for_domain,
)
from packages.swarm.swarm_types import DomainTag, SwarmConfig


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_provider(model_name: str) -> MagicMock:
    """Create a minimal mock provider for testing."""
    p = MagicMock()
    p.get_model_name.return_value = model_name
    p.get_provider_name.return_value = model_name.split("/")[0]
    p.is_free.return_value = True
    return p


# Pool that mirrors the real discovered_models.json contents roughly
MOCK_PROVIDERS = [
    _make_provider("gemini-flash-lite-latest"),
    _make_provider("gemini-2.0-flash"),
    _make_provider("gemini-2.5-flash-lite"),
    _make_provider("gemini-2.5-pro"),
    _make_provider("deepseek-chat"),
    _make_provider("llama-3.1-8b-instant"),
    _make_provider("llama-3.3-70b-versatile"),
]


# ── Unit: TeamLead.filter_providers ──────────────────────────────────────────


class TestTeamLeadFilterProviders:
    """TeamLead.filter_providers() contract."""

    def test_security_tilead_prefers_deepseek_and_gemini_pro(self):
        """SecurityTeamLead should select deepseek-chat + gemini-2.5-pro + gemini-2.0-flash."""
        tilead = SecurityTeamLead()
        selected = tilead.filter_providers(MOCK_PROVIDERS)
        names = [p.get_model_name() for p in selected]
        assert "deepseek-chat" in names
        assert "gemini-2.5-pro" in names

    def test_security_tilead_excludes_flash_lite(self):
        """gemini-flash-lite-latest is in avoid_models for security."""
        tilead = SecurityTeamLead()
        selected = tilead.filter_providers(MOCK_PROVIDERS)
        names = [p.get_model_name() for p in selected]
        assert "gemini-flash-lite-latest" not in names

    def test_speed_tilead_prefers_fast_models(self):
        """SpeedTeamLead should prefer flash-lite variants."""
        tilead = SpeedTeamLead()
        selected = tilead.filter_providers(MOCK_PROVIDERS)
        names = [p.get_model_name() for p in selected]
        assert "gemini-flash-lite-latest" in names
        assert "gemini-2.0-flash" in names

    def test_speed_tilead_excludes_slow_models(self):
        """SpeedTeamLead should exclude gemini-2.5-pro and deepseek."""
        tilead = SpeedTeamLead()
        selected = tilead.filter_providers(MOCK_PROVIDERS)
        names = [p.get_model_name() for p in selected]
        assert "gemini-2.5-pro" not in names
        assert "deepseek-chat" not in names

    def test_fallback_when_no_preferred_available(self):
        """If none of preferred_models are in the pool, return full pool minus avoided."""
        tilead = ArchitectureTeamLead()
        # Only have flash-lite which is NOT in preferred but IS in avoid
        tiny_pool = [_make_provider("gemini-flash-lite-latest")]
        selected = tilead.filter_providers(tiny_pool)
        # fallback: all minus avoided (flash-lite is avoided → returns pool as-is per fallback)
        assert len(selected) > 0, "Must never return empty pool"

    def test_general_tilead_uses_speed_lead(self):
        """DomainTag.GENERAL should map to SpeedTeamLead."""
        tilead = get_tilead_for_domain(DomainTag.GENERAL)
        assert isinstance(tilead, SpeedTeamLead)

    def test_security_tilead_lookup(self):
        """DomainTag.SECURITY should map to SecurityTeamLead."""
        tilead = get_tilead_for_domain(DomainTag.SECURITY)
        assert isinstance(tilead, SecurityTeamLead)

    def test_unknown_domain_falls_back_to_speed(self):
        """Unknown domain string should fall back to SpeedTeamLead (not crash)."""
        tilead = get_tilead_for_domain("nonexistent_domain")
        assert isinstance(tilead, SpeedTeamLead)


# ── Integration: engine.decide() with domain filtering ───────────────────────


class TestEngineDecideDomainAware:
    """engine.decide() must route providers through TeamLead when domain != GENERAL.

    These tests mock pm.run() so we don't make real LLM calls.
    They verify that the CORRECT subset of providers is passed to pm.run().
    """

    @pytest.fixture
    def engine_with_mock_providers(self):
        """SwarmEngine with mocked providers — no real LLM calls."""
        with patch("packages.swarm.engine.load_discovered_providers") as mock_load, \
             patch("packages.swarm.engine.ProviderRegistry"), \
             patch("packages.swarm.engine.DecisionMemory"), \
             patch("packages.swarm.engine.AgentMemory"), \
             patch("packages.swarm.engine.StructuredMemory"), \
             patch("packages.swarm.engine.HiveExaminer") as mock_hive, \
             patch("packages.swarm.engine.SkillLibrary"), \
             patch("packages.swarm.engine.MiddlewareChain"), \
             patch("packages.swarm.engine.PMAgent"), \
             patch("packages.swarm.engine.WebResearcher"):

            mock_load.return_value = list(MOCK_PROVIDERS)
            mock_hive.return_value.get_profile.return_value = None

            from packages.swarm.engine import SwarmEngine
            engine = SwarmEngine()
            engine.providers = list(MOCK_PROVIDERS)
            yield engine

    @pytest.mark.asyncio
    async def test_general_domain_uses_full_provider_pool(self, engine_with_mock_providers):
        """When domain=GENERAL, pm.run() should receive all available providers."""
        engine = engine_with_mock_providers
        config = SwarmConfig(question="Quick test", domain=DomainTag.GENERAL)

        captured_providers = []

        async def capture_run(cfg, providers):
            captured_providers.extend(providers)
            mock_report = MagicMock()
            mock_report.agent_results = []
            mock_report.decision_id = None
            return mock_report

        engine.pm.run = capture_run

        await engine.decide(config)

        # GENERAL → full pool (SpeedTeamLead filters out gemini-2.5-pro and deepseek)
        # but GENERAL should pass through without domain filtering
        assert len(captured_providers) == len(MOCK_PROVIDERS)

    @pytest.mark.asyncio
    async def test_security_domain_filters_to_security_pool(self, engine_with_mock_providers):
        """When domain=SECURITY, pm.run() should receive only security-preferred providers."""
        engine = engine_with_mock_providers
        config = SwarmConfig(question="RLS audit", domain=DomainTag.SECURITY)

        captured_providers = []

        async def capture_run(cfg, providers):
            captured_providers.extend(providers)
            mock_report = MagicMock()
            mock_report.agent_results = []
            mock_report.decision_id = None
            return mock_report

        engine.pm.run = capture_run

        await engine.decide(config)

        names = [p.get_model_name() for p in captured_providers]
        # Security pool: deepseek, gemini-2.5-pro, gemini-2.0-flash — NOT flash-lite
        assert "gemini-flash-lite-latest" not in names, (
            "flash-lite is in avoid_models for security — must be excluded"
        )
        assert len(captured_providers) < len(MOCK_PROVIDERS), (
            "Security domain must narrow the provider pool"
        )

    @pytest.mark.asyncio
    async def test_security_domain_never_empties_pool(self, engine_with_mock_providers):
        """Even if security filtering removes all providers, pm.run() must get a non-empty pool."""
        engine = engine_with_mock_providers
        # Give engine only flash-lite (which security avoids)
        engine.providers = [_make_provider("gemini-flash-lite-latest")]
        config = SwarmConfig(question="Edge case", domain=DomainTag.SECURITY)

        captured_providers = []

        async def capture_run(cfg, providers):
            captured_providers.extend(providers)
            mock_report = MagicMock()
            mock_report.agent_results = []
            mock_report.decision_id = None
            return mock_report

        engine.pm.run = capture_run

        await engine.decide(config)

        assert len(captured_providers) > 0, "Pool must never be empty — fallback required"
