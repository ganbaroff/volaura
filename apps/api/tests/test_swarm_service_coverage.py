"""Coverage tests for app.services.swarm_service — tick 7a.

Targets missing lines:
  68-137  _swarm_evaluate_scores: swarm path (SwarmEngine, docker, env injection)
  162-163 _extract_consensus_scores: scores-found branch (consensus[name] = avg)

asyncio_mode = "auto" (pyproject.toml) — no @pytest.mark.asyncio needed.
"""

from __future__ import annotations

import json
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Ensure docker stub is present before import ───────────────────────────────

if "docker" not in sys.modules:
    _fake_docker = ModuleType("docker")
    _fake_docker.from_env = MagicMock()  # type: ignore[attr-defined]
    sys.modules["docker"] = _fake_docker


# ── Ensure swarm stub is present (packages/swarm not on path in test env) ────

def _ensure_swarm_stub() -> None:
    """Inject minimal fake swarm package so _swarm_evaluate_scores can be imported."""
    if "swarm" in sys.modules:
        return

    fake_swarm = ModuleType("swarm")

    class _StakesLevel:  # noqa: D101
        LOW = "LOW"

    class _DomainTag:  # noqa: D101
        GENERAL = "GENERAL"

    class _SwarmConfig:  # noqa: D101
        def __init__(self, **kwargs: object) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

    class _SwarmEngine:  # noqa: D101
        def __init__(self, **kwargs: object) -> None:
            pass

        async def decide(self, config: object) -> object:  # noqa: D102
            raise NotImplementedError("stub — should be patched in tests")

    fake_swarm.StakesLevel = _StakesLevel  # type: ignore[attr-defined]
    fake_swarm.DomainTag = _DomainTag  # type: ignore[attr-defined]
    fake_swarm.SwarmConfig = _SwarmConfig  # type: ignore[attr-defined]
    fake_swarm.SwarmEngine = _SwarmEngine  # type: ignore[attr-defined]
    sys.modules["swarm"] = fake_swarm


_ensure_swarm_stub()

from app.services.swarm_service import _extract_consensus_scores, _swarm_evaluate_scores

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_agent(raw: str | None) -> MagicMock:
    a = MagicMock()
    a.raw_response = raw
    return a


def _make_report(agents: list[MagicMock], winner: str = "clarity:0.8") -> MagicMock:
    r = MagicMock()
    r.agent_results = agents
    r.winner = winner
    r.winner_score = 0.8
    r.total_latency_ms = 42
    return r


def _fake_settings(**kwargs: object) -> SimpleNamespace:
    defaults = {
        "gemini_api_key": "key-gemini",
        "openai_api_key": "key-openai",
        "groq_api_key": "key-groq",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── _extract_consensus_scores: scores-FOUND branch (lines 162-163) ───────────

class TestExtractConsensusScoresFoundBranch:
    """Cover the `if scores: consensus[name] = sum/len` branch explicitly."""

    def test_single_concept_single_agent_produces_exact_average(self) -> None:
        """One agent, one concept → average is just that score."""
        report = _make_report([_make_agent('{"speed": 0.72}')])
        result = _extract_consensus_scores(report, ["speed"])
        assert result["speed"] == pytest.approx(0.72)

    def test_three_agents_different_scores_averages_correctly(self) -> None:
        """Three agents → arithmetic mean (line 163 executed 1+ times)."""
        agents = [
            _make_agent('{"emp": 0.6}'),
            _make_agent('{"emp": 0.9}'),
            _make_agent('{"emp": 0.3}'),
        ]
        report = _make_report(agents)
        result = _extract_consensus_scores(report, ["emp"])
        assert result["emp"] == pytest.approx(0.6)  # (0.6+0.9+0.3)/3

    @pytest.mark.parametrize(
        "raw_scores, expected_avg",
        [
            pytest.param([0.0, 1.0], 0.5, id="нулевой_и_единица_среднее_0_5"),
            pytest.param([0.8, 0.8, 0.8], 0.8, id="одинаковые_среднее_не_меняется"),
            pytest.param([1.0], 1.0, id="единственный_агент_максимум"),
        ],
    )
    def test_average_calculation_parametrize(
        self, raw_scores: list[float], expected_avg: float
    ) -> None:
        """Coverage of average branch across common score distributions."""
        agents = [_make_agent(json.dumps({"focus": s})) for s in raw_scores]
        result = _extract_consensus_scores(_make_report(agents), ["focus"])
        assert result["focus"] == pytest.approx(expected_avg, abs=1e-9)


# ── _swarm_evaluate_scores: lines 68-137 ────────────────────────────────────

class TestSwarmEvaluateScores:
    """Cover the _swarm_evaluate_scores function body.

    Lines 68-137 include:
      - sys.path manipulation
      - SwarmEngine + SwarmConfig construction
      - asyncio.wait_for call
      - logger.info call
      - _extract_consensus_scores delegation
      - ValueError raise when no scores
    """

    CONCEPTS = [{"name": "clarity", "weight": 1.0}, {"name": "depth", "weight": 0.5}]

    def _success_report(self) -> MagicMock:
        agents = [
            _make_agent('{"clarity": 0.85, "depth": 0.65}'),
        ]
        return _make_report(agents)

    async def test_returns_concept_scores_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Happy path: engine.decide returns report, scores extracted."""
        monkeypatch.setattr("app.services.swarm_service.settings", _fake_settings())

        # Patch docker.from_env to return a mock client
        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = MagicMock()

        report = self._success_report()

        with (
            patch("app.services.swarm_service.docker") as mock_docker_mod,
            patch("swarm.SwarmEngine") as mock_engine_cls,
        ):
            mock_docker_mod.from_env.return_value = mock_docker_client
            mock_instance = MagicMock()
            mock_instance.decide = AsyncMock(return_value=report)
            mock_engine_cls.return_value = mock_instance

            result = await _swarm_evaluate_scores("What is empathy?", "I listen carefully.", self.CONCEPTS)

        assert "clarity" in result
        assert "depth" in result
        assert result["clarity"] == pytest.approx(0.85)

    async def test_env_injection_includes_api_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API keys from settings are injected into env dict passed to SwarmEngine."""
        fake = _fake_settings(gemini_api_key="gem-123", openai_api_key="oai-456", groq_api_key="groq-789")
        monkeypatch.setattr("app.services.swarm_service.settings", fake)

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = MagicMock()
        report = self._success_report()

        captured_env: dict = {}

        def _capture_engine(**kwargs: object) -> MagicMock:
            captured_env.update(kwargs.get("env", {}))
            m = MagicMock()
            m.decide = AsyncMock(return_value=report)
            return m

        with (
            patch("app.services.swarm_service.docker") as mock_docker_mod,
            patch("swarm.SwarmEngine", side_effect=_capture_engine),
        ):
            mock_docker_mod.from_env.return_value = mock_docker_client
            await _swarm_evaluate_scores("Q?", "A!", self.CONCEPTS)

        assert captured_env.get("GEMINI_API_KEY") == "gem-123"
        assert captured_env.get("OPENAI_API_KEY") == "oai-456"
        assert captured_env.get("GROQ_API_KEY") == "groq-789"

    async def test_raises_value_error_when_no_parseable_scores(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ValueError raised when all agent responses are unparseable (no scores)."""
        monkeypatch.setattr("app.services.swarm_service.settings", _fake_settings())

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = MagicMock()

        # All agents return garbage — no concepts will be found, all default to 0.5...
        # BUT concepts list is EMPTY so consensus dict is empty → ValueError
        bad_report = _make_report([_make_agent("not json"), _make_agent("also bad")])

        with (
            patch("app.services.swarm_service.docker") as mock_docker_mod,
            patch("swarm.SwarmEngine") as mock_engine_cls,
        ):
            mock_docker_mod.from_env.return_value = mock_docker_client
            mock_instance = MagicMock()
            mock_instance.decide = AsyncMock(return_value=bad_report)
            mock_engine_cls.return_value = mock_instance

            with pytest.raises(ValueError, match="no parseable concept scores"):
                # Pass empty concepts list so _extract_consensus_scores returns {}
                await _swarm_evaluate_scores("Q?", "A!", [])

    async def test_timeout_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """asyncio.TimeoutError from wait_for propagates up (caller handles it)."""
        import asyncio

        monkeypatch.setattr("app.services.swarm_service.settings", _fake_settings())

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = MagicMock()

        with (
            patch("app.services.swarm_service.docker") as mock_docker_mod,
            patch("swarm.SwarmEngine") as mock_engine_cls,
            patch("app.services.swarm_service.asyncio.wait_for", side_effect=asyncio.TimeoutError),
        ):
            mock_docker_mod.from_env.return_value = mock_docker_client
            mock_instance = MagicMock()
            mock_engine_cls.return_value = mock_instance

            with pytest.raises(asyncio.TimeoutError):
                await _swarm_evaluate_scores("Q?", "A!", self.CONCEPTS)

    async def test_logger_info_called_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """logger.info fires after successful decide() call."""
        monkeypatch.setattr("app.services.swarm_service.settings", _fake_settings())

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = MagicMock()
        report = self._success_report()

        with (
            patch("app.services.swarm_service.docker") as mock_docker_mod,
            patch("swarm.SwarmEngine") as mock_engine_cls,
            patch("app.services.swarm_service.logger") as mock_logger,
        ):
            mock_docker_mod.from_env.return_value = mock_docker_client
            mock_instance = MagicMock()
            mock_instance.decide = AsyncMock(return_value=report)
            mock_engine_cls.return_value = mock_instance

            await _swarm_evaluate_scores("Q?", "answer", self.CONCEPTS)

        mock_logger.info.assert_called_once()

    async def test_packages_path_added_to_sys_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """packages/ directory gets added to sys.path for swarm package import."""
        monkeypatch.setattr("app.services.swarm_service.settings", _fake_settings())

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = MagicMock()
        report = self._success_report()

        with (
            patch("app.services.swarm_service.docker") as mock_docker_mod,
            patch("swarm.SwarmEngine") as mock_engine_cls,
        ):
            mock_docker_mod.from_env.return_value = mock_docker_client
            mock_instance = MagicMock()
            mock_instance.decide = AsyncMock(return_value=report)
            mock_engine_cls.return_value = mock_instance

            await _swarm_evaluate_scores("Q?", "A!", self.CONCEPTS)

        # packages path should be in sys.path after the call
        assert any("packages" in p for p in sys.path)

    @pytest.mark.parametrize(
        "question, answer, concept_name",
        [
            pytest.param("Что такое эмпатия?", "Слушать активно.", "empathy", id="русский_вопрос"),
            pytest.param("", "some answer", "clarity", id="пустой_вопрос"),
            pytest.param("Q?", "A" * 3000, "depth", id="очень_длинный_ответ_обрезается"),
        ],
    )
    async def test_various_inputs_reach_engine(
        self,
        question: str,
        answer: str,
        concept_name: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Engine.decide is always called regardless of input content."""
        monkeypatch.setattr("app.services.swarm_service.settings", _fake_settings())

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = MagicMock()
        concepts = [{"name": concept_name, "weight": 1.0}]
        report = _make_report([_make_agent(json.dumps({concept_name: 0.7}))])

        with (
            patch("app.services.swarm_service.docker") as mock_docker_mod,
            patch("swarm.SwarmEngine") as mock_engine_cls,
        ):
            mock_docker_mod.from_env.return_value = mock_docker_client
            mock_instance = MagicMock()
            mock_instance.decide = AsyncMock(return_value=report)
            mock_engine_cls.return_value = mock_instance

            result = await _swarm_evaluate_scores(question, answer, concepts)

        mock_instance.decide.assert_awaited_once()
        assert concept_name in result

    async def test_sys_path_insert_branch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover line 77: sys.path.insert when packages_path not yet in sys.path."""
        import os

        monkeypatch.setattr("app.services.swarm_service.settings", _fake_settings())

        mock_docker_client = MagicMock()
        mock_docker_client.containers.run.return_value = MagicMock()
        report = self._success_report()

        # Temporarily remove the packages path so the `if` branch fires
        import app.services.swarm_service as svc_mod

        real_abspath = os.path.abspath(svc_mod.__file__)
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(real_abspath))))
        )
        packages_path = os.path.join(project_root, "packages")

        original_path = sys.path.copy()
        try:
            # Remove packages_path so the if-branch executes
            while packages_path in sys.path:
                sys.path.remove(packages_path)

            with (
                patch("app.services.swarm_service.docker") as mock_docker_mod,
                patch("swarm.SwarmEngine") as mock_engine_cls,
            ):
                mock_docker_mod.from_env.return_value = mock_docker_client
                mock_instance = MagicMock()
                mock_instance.decide = AsyncMock(return_value=report)
                mock_engine_cls.return_value = mock_instance

                await _swarm_evaluate_scores("Q?", "A!", self.CONCEPTS)

            assert packages_path in sys.path
        finally:
            sys.path[:] = original_path


# ── _extract_consensus_scores: except block (lines 162-163) ──────────────────

class TestExtractConsensusScoresExceptBranch:
    """Explicitly cover the except (JSONDecodeError, ValueError, TypeError) branch."""

    @pytest.mark.parametrize(
        "raw",
        [
            pytest.param("not valid json {{{", id="невалидный_json"),
            pytest.param('{"score": "not_a_float_but_NaN"}', id="нефлоат_значение"),
        ],
    )
    def test_except_branch_covered_by_bad_json(self, raw: str) -> None:
        """Malformed agent responses silently skip via except continue (lines 162-163)."""
        agents = [
            _make_agent(raw),           # triggers except → continue
            _make_agent('{"x": 0.7}'),  # valid → contributes
        ]
        result = _extract_consensus_scores(_make_report(agents), ["x"])
        # The good agent provides 0.7; the bad one is skipped
        assert result["x"] == pytest.approx(0.7)

    def test_type_error_branch_non_string_raw(self) -> None:
        """raw_response=42 (int) triggers except TypeError → continue."""
        a = MagicMock()
        a.raw_response = 42  # not a string
        agents = [a, _make_agent('{"z": 0.3}')]
        result = _extract_consensus_scores(_make_report(agents), ["z"])
        assert result["z"] == pytest.approx(0.3)
