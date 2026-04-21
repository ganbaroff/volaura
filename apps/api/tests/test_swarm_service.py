"""Unit tests for app.services.swarm_service."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _patch_docker():
    """Inject a fake docker module so swarm_service imports cleanly."""
    if "docker" not in sys.modules:
        fake = ModuleType("docker")
        fake.from_env = MagicMock()
        sys.modules["docker"] = fake


_patch_docker()

from app.services.swarm_service import _extract_consensus_scores, evaluate_answer

# ── _extract_consensus_scores ─────────────────────────────────────────────────


class TestExtractConsensusScores:
    def _agent(self, raw: str):
        a = MagicMock()
        a.raw_response = raw
        return a

    def _report(self, agents):
        r = MagicMock()
        r.agent_results = agents
        return r

    def test_single_agent_valid_json(self):
        report = self._report([self._agent('{"clarity": 0.8, "depth": 0.6}')])
        result = _extract_consensus_scores(report, ["clarity", "depth"])
        assert result["clarity"] == pytest.approx(0.8)
        assert result["depth"] == pytest.approx(0.6)

    def test_multiple_agents_averages(self):
        report = self._report(
            [
                self._agent('{"clarity": 0.8}'),
                self._agent('{"clarity": 0.4}'),
            ]
        )
        result = _extract_consensus_scores(report, ["clarity"])
        assert result["clarity"] == pytest.approx(0.6)

    def test_missing_concept_defaults_to_half(self):
        report = self._report([self._agent('{"clarity": 0.8}')])
        result = _extract_consensus_scores(report, ["clarity", "unknown"])
        assert result["unknown"] == pytest.approx(0.5)

    def test_scores_clamped_to_0_1(self):
        report = self._report([self._agent('{"x": 5.0, "y": -2.0}')])
        result = _extract_consensus_scores(report, ["x", "y"])
        assert result["x"] == pytest.approx(1.0)
        assert result["y"] == pytest.approx(0.0)

    def test_strips_markdown_fences(self):
        report = self._report([self._agent('```json\n{"a": 0.7}\n```')])
        result = _extract_consensus_scores(report, ["a"])
        assert result["a"] == pytest.approx(0.7)

    def test_invalid_json_skipped(self):
        report = self._report(
            [
                self._agent("not json at all"),
                self._agent('{"a": 0.9}'),
            ]
        )
        result = _extract_consensus_scores(report, ["a"])
        assert result["a"] == pytest.approx(0.9)

    def test_no_agents_all_default(self):
        report = self._report([])
        result = _extract_consensus_scores(report, ["x", "y"])
        assert result["x"] == pytest.approx(0.5)
        assert result["y"] == pytest.approx(0.5)

    def test_none_raw_response_skipped(self):
        report = self._report([self._agent(None)])
        result = _extract_consensus_scores(report, ["x"])
        assert result["x"] == pytest.approx(0.5)

    def test_empty_raw_response_skipped(self):
        report = self._report([self._agent("")])
        result = _extract_consensus_scores(report, ["x"])
        assert result["x"] == pytest.approx(0.5)

    def test_non_dict_json_skipped(self):
        report = self._report([self._agent("[0.5, 0.6]")])
        result = _extract_consensus_scores(report, ["x"])
        assert result["x"] == pytest.approx(0.5)


# ── evaluate_answer ──────────────────────────────────────────────────────────


class TestEvaluateAnswer:
    CONCEPTS = [{"name": "clarity", "weight": 1.0}]

    @pytest.mark.asyncio
    async def test_empty_answer_returns_zero(self):
        result = await evaluate_answer("Q?", "", self.CONCEPTS)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_empty_answer_with_details(self):
        result = await evaluate_answer("Q?", "   ", self.CONCEPTS, return_details=True)
        assert result.composite == 0.0
        assert result.model_used == "swarm"

    @pytest.mark.asyncio
    async def test_swarm_failure_falls_back_to_bars(self):
        with (
            patch(
                "app.services.swarm_service._swarm_evaluate_scores",
                new_callable=AsyncMock,
                side_effect=Exception("docker down"),
            ),
            patch(
                "app.core.assessment.bars.evaluate_answer",
                new_callable=AsyncMock,
                return_value=0.75,
            ) as bars_mock,
        ):
            result = await evaluate_answer("Q?", "my answer", self.CONCEPTS)
            assert result == 0.75
            bars_mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_swarm_success_returns_composite(self):
        with (
            patch(
                "app.services.swarm_service._swarm_evaluate_scores",
                new_callable=AsyncMock,
                return_value={"clarity": 0.8},
            ),
            patch(
                "app.core.assessment.bars._aggregate",
                return_value=0.8,
            ),
        ):
            result = await evaluate_answer("Q?", "my answer", self.CONCEPTS)
            assert result == pytest.approx(0.8)

    @pytest.mark.asyncio
    async def test_swarm_success_with_details(self):
        with (
            patch(
                "app.services.swarm_service._swarm_evaluate_scores",
                new_callable=AsyncMock,
                return_value={"clarity": 0.9},
            ),
            patch(
                "app.core.assessment.bars._aggregate",
                return_value=0.9,
            ),
        ):
            result = await evaluate_answer("Q?", "answer", self.CONCEPTS, return_details=True)
            assert result.composite == pytest.approx(0.9)
            assert result.model_used == "swarm"
            assert result.concept_scores == {"clarity": 0.9}

    @pytest.mark.asyncio
    async def test_fallback_passes_return_details(self):
        with (
            patch(
                "app.services.swarm_service._swarm_evaluate_scores",
                new_callable=AsyncMock,
                side_effect=Exception("fail"),
            ),
            patch(
                "app.core.assessment.bars.evaluate_answer",
                new_callable=AsyncMock,
                return_value=MagicMock(score=0.5),
            ) as bars_mock,
        ):
            await evaluate_answer("Q?", "ans", self.CONCEPTS, return_details=True)
            bars_mock.assert_awaited_once()
            call_kwargs = bars_mock.call_args
            assert call_kwargs.kwargs.get("return_details") is True or call_kwargs[1].get("return_details") is True
