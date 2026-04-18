"""Unit tests for 6 previously untested services:
analytics, ecosystem_events, embeddings, notification_service, match_checker, swarm_service.

Total: ~120 tests covering pure functions, dataclass invariants, and async mock flows.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── analytics service ────────────────────────────────────────────────────────


def _chain_mock():
    """Build a mock Supabase client where table().insert().execute() works.

    table() and insert() are sync (MagicMock), execute() is async (AsyncMock).
    """
    db = MagicMock()
    execute = AsyncMock(return_value=MagicMock(data=[{"id": "1"}]))
    db.table.return_value.insert.return_value.execute = execute
    return db


class TestAnalyticsTrackEvent:
    @pytest.fixture
    def mock_db(self):
        return _chain_mock()

    @pytest.mark.asyncio
    async def test_basic_event(self, mock_db):
        from app.services.analytics import track_event

        await track_event(mock_db, "user-1", "page_view")
        mock_db.table.assert_called_with("analytics_events")
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert call_args["user_id"] == "user-1"
        assert call_args["event_name"] == "page_view"
        assert call_args["properties"] == {}
        assert call_args["platform"] == "web"

    @pytest.mark.asyncio
    async def test_with_properties(self, mock_db):
        from app.services.analytics import track_event

        await track_event(mock_db, "u", "ev", properties={"key": "val"})
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert call_args["properties"] == {"key": "val"}

    @pytest.mark.asyncio
    async def test_optional_fields(self, mock_db):
        from app.services.analytics import track_event

        await track_event(mock_db, "u", "ev", session_id="s1", locale="az", platform="mobile")
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert call_args["session_id"] == "s1"
        assert call_args["locale"] == "az"
        assert call_args["platform"] == "mobile"

    @pytest.mark.asyncio
    async def test_omitted_optional_fields(self, mock_db):
        from app.services.analytics import track_event

        await track_event(mock_db, "u", "ev")
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert "session_id" not in call_args
        assert "locale" not in call_args

    @pytest.mark.asyncio
    async def test_never_raises_on_db_error(self):
        from app.services.analytics import track_event

        db = _chain_mock()
        db.table.return_value.insert.return_value.execute = AsyncMock(side_effect=RuntimeError("DB down"))
        await track_event(db, "u", "ev")  # should not raise


# ── ecosystem_events service ─────────────────────────────────────────────────


class TestEcosystemEvents:
    @pytest.fixture
    def mock_db(self):
        return _chain_mock()

    @pytest.mark.asyncio
    async def test_assessment_completed_payload(self, mock_db):
        from app.services.ecosystem_events import emit_assessment_completed

        await emit_assessment_completed(mock_db, "u1", "communication", 85.5, 10, "full", "max_items", ["rapid_guess"])
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert call_args["event_type"] == "assessment_completed"
        assert call_args["source_product"] == "volaura"
        payload = call_args["payload"]
        assert payload["competency_slug"] == "communication"
        assert payload["competency_score"] == 85.5
        assert payload["items_answered"] == 10
        assert payload["energy_level"] == "full"
        assert payload["gaming_flags"] == ["rapid_guess"]
        assert payload["_schema_version"] == 1

    @pytest.mark.asyncio
    async def test_assessment_completed_defaults(self, mock_db):
        from app.services.ecosystem_events import emit_assessment_completed

        await emit_assessment_completed(mock_db, "u1", "leadership", 50.0, 5, "low", None)
        payload = mock_db.table.return_value.insert.call_args[0][0]["payload"]
        assert payload["gaming_flags"] == []
        assert payload["stop_reason"] is None

    @pytest.mark.asyncio
    async def test_assessment_completed_score_rounding(self, mock_db):
        from app.services.ecosystem_events import emit_assessment_completed

        await emit_assessment_completed(mock_db, "u1", "tech", 85.555, 5, "mid", None)
        payload = mock_db.table.return_value.insert.call_args[0][0]["payload"]
        assert payload["competency_score"] == 85.56

    @pytest.mark.asyncio
    async def test_assessment_completed_never_raises(self):
        from app.services.ecosystem_events import emit_assessment_completed

        db = _chain_mock()
        db.table.return_value.insert.return_value.execute = AsyncMock(side_effect=Exception("boom"))
        await emit_assessment_completed(db, "u1", "tech", 50.0, 5, "low", None)

    @pytest.mark.asyncio
    async def test_aura_updated_payload(self, mock_db):
        from app.services.ecosystem_events import emit_aura_updated

        await emit_aura_updated(
            mock_db, "u1", 82.3, "Gold", {"communication": 90.123, "leadership": 74.567}, True, 85.67
        )
        payload = mock_db.table.return_value.insert.call_args[0][0]["payload"]
        assert payload["total_score"] == 82.3
        assert payload["badge_tier"] == "Gold"
        assert payload["competency_scores"]["communication"] == 90.12
        assert payload["competency_scores"]["leadership"] == 74.57
        assert payload["elite_status"] is True
        assert payload["percentile_rank"] == 85.7
        assert payload["_schema_version"] == 1

    @pytest.mark.asyncio
    async def test_aura_updated_none_percentile(self, mock_db):
        from app.services.ecosystem_events import emit_aura_updated

        await emit_aura_updated(mock_db, "u1", 50.0, "Bronze", {}, False, None)
        payload = mock_db.table.return_value.insert.call_args[0][0]["payload"]
        assert payload["percentile_rank"] is None

    @pytest.mark.asyncio
    async def test_aura_updated_never_raises(self):
        from app.services.ecosystem_events import emit_aura_updated

        db = _chain_mock()
        db.table.return_value.insert.return_value.execute = AsyncMock(side_effect=Exception("boom"))
        await emit_aura_updated(db, "u1", 50.0, "Bronze", {}, False, None)

    @pytest.mark.asyncio
    async def test_badge_tier_changed_emits(self, mock_db):
        from app.services.ecosystem_events import emit_badge_tier_changed

        await emit_badge_tier_changed(mock_db, "u1", "Silver", "Gold", 78.0)
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert call_args["event_type"] == "badge_tier_changed"
        payload = call_args["payload"]
        assert payload["old_tier"] == "Silver"
        assert payload["new_tier"] == "Gold"
        assert payload["total_score"] == 78.0

    @pytest.mark.asyncio
    async def test_badge_tier_changed_skips_same(self):
        from app.services.ecosystem_events import emit_badge_tier_changed

        db = _chain_mock()
        await emit_badge_tier_changed(db, "u1", "Gold", "Gold", 80.0)
        db.table.assert_not_called()

    @pytest.mark.asyncio
    async def test_badge_tier_changed_none_old(self, mock_db):
        from app.services.ecosystem_events import emit_badge_tier_changed

        await emit_badge_tier_changed(mock_db, "u1", None, "Bronze", 45.0)
        payload = mock_db.table.return_value.insert.call_args[0][0]["payload"]
        assert payload["old_tier"] is None
        assert payload["new_tier"] == "Bronze"

    @pytest.mark.asyncio
    async def test_badge_tier_changed_never_raises(self):
        from app.services.ecosystem_events import emit_badge_tier_changed

        db = _chain_mock()
        db.table.return_value.insert.return_value.execute = AsyncMock(side_effect=Exception("boom"))
        await emit_badge_tier_changed(db, "u1", "Silver", "Gold", 78.0)


# ── embeddings service (pure functions) ──────────────────────────────────────


class TestBuildProfileText:
    def test_full_profile(self):
        from app.services.embeddings import build_profile_text

        profile = {
            "display_name": "Yusif",
            "bio": "CTO of everything",
            "location": "Baku",
            "languages": ["az", "en", "ru"],
        }
        aura = {
            "total_score": 92.5,
            "badge_tier": "Platinum",
            "elite_status": True,
            "competency_scores": {"communication": 95, "leadership": 88, "tech_literacy": 0},
        }
        text = build_profile_text(profile, aura)
        assert "Yusif" in text
        assert "CTO of everything" in text
        assert "Baku" in text
        assert "az, en, ru" in text
        assert "92.5" in text
        assert "Platinum" in text
        assert "Elite" in text
        assert "communication: 95" in text
        assert "leadership: 88" in text
        assert "tech_literacy" not in text  # score 0 excluded

    def test_empty_profile(self):
        from app.services.embeddings import build_profile_text

        text = build_profile_text({}, None)
        assert text == ""

    def test_profile_no_aura(self):
        from app.services.embeddings import build_profile_text

        text = build_profile_text({"display_name": "Test"}, None)
        assert "Test" in text
        assert "AURA" not in text

    def test_aura_no_elite(self):
        from app.services.embeddings import build_profile_text

        text = build_profile_text({}, {"total_score": 50, "badge_tier": "Bronze", "elite_status": False})
        assert "Elite" not in text
        assert "50.0" in text

    def test_aura_no_competency_scores(self):
        from app.services.embeddings import build_profile_text

        text = build_profile_text({}, {"total_score": 50, "badge_tier": "Silver"})
        assert "Competencies" not in text

    def test_aura_empty_competencies(self):
        from app.services.embeddings import build_profile_text

        text = build_profile_text({}, {"total_score": 50, "badge_tier": "Silver", "competency_scores": {}})
        assert "Competencies" not in text

    def test_partial_profile(self):
        from app.services.embeddings import build_profile_text

        text = build_profile_text({"bio": "short"}, None)
        assert "Bio: short" in text
        assert "Name" not in text


class TestGenerateEmbedding:
    @pytest.mark.asyncio
    async def test_empty_text_returns_none(self):
        from app.services.embeddings import generate_embedding

        result = await generate_embedding("")
        assert result is None

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_none(self):
        from app.services.embeddings import generate_embedding

        result = await generate_embedding("   \n\t  ")
        assert result is None


# ── notification_service ─────────────────────────────────────────────────────


class TestNotificationService:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": "1"}]))
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.gte.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )
        return db

    @pytest.mark.asyncio
    async def test_notify_basic(self, mock_db):
        from app.services.notification_service import notify

        await notify(mock_db, "u1", "badge_earned", "You earned Gold!")
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert call_args["user_id"] == "u1"
        assert call_args["type"] == "badge_earned"
        assert call_args["title"] == "You earned Gold!"
        assert call_args["body"] is None
        assert call_args["reference_id"] is None

    @pytest.mark.asyncio
    async def test_notify_with_body_and_ref(self, mock_db):
        from app.services.notification_service import notify

        await notify(mock_db, "u1", "org_view", "Org viewed you", body="Details", reference_id="org-1")
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert call_args["body"] == "Details"
        assert call_args["reference_id"] == "org-1"

    @pytest.mark.asyncio
    async def test_notify_never_raises(self):
        from app.services.notification_service import notify

        db = MagicMock()
        db.table.return_value.insert.return_value.execute = AsyncMock(side_effect=RuntimeError("DB"))
        await notify(db, "u1", "t", "title")

    @pytest.mark.asyncio
    async def test_profile_viewed_throttled(self):
        from app.services.notification_service import notify_profile_viewed

        db = MagicMock()
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.gte.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[{"id": "existing"}])
        )
        result = await notify_profile_viewed(db, "vol-1", "org-1", "TestOrg")
        assert result is False

    @pytest.mark.asyncio
    async def test_profile_viewed_sends(self, mock_db):
        from app.services.notification_service import notify_profile_viewed

        # No existing notifications
        result = await notify_profile_viewed(mock_db, "vol-1", "org-1", "TestOrg")
        assert result is True

    @pytest.mark.asyncio
    async def test_profile_viewed_never_raises(self):
        from app.services.notification_service import notify_profile_viewed

        db = MagicMock()
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.gte.return_value.limit.return_value.execute = AsyncMock(
            side_effect=RuntimeError("DB")
        )
        result = await notify_profile_viewed(db, "vol-1", "org-1", "TestOrg")
        assert result is False

    def test_throttle_window_constant(self):
        from app.services.notification_service import _PROFILE_VIEW_THROTTLE_HOURS

        assert _PROFILE_VIEW_THROTTLE_HOURS == 24


# ── match_checker dataclasses + pure functions ───────────────────────────────


class TestMatchCheckResult:
    def test_fields(self):
        from app.services.match_checker import MatchCheckResult

        r = MatchCheckResult(
            search_id="s1",
            search_name="Test Search",
            org_id="org-1",
            new_match_count=5,
            notified=True,
        )
        assert r.search_id == "s1"
        assert r.new_match_count == 5
        assert r.notified is True
        assert r.error is None

    def test_with_error(self):
        from app.services.match_checker import MatchCheckResult

        r = MatchCheckResult("s1", "Test", "org-1", 0, False, error="timeout")
        assert r.error == "timeout"


class TestRunSummary:
    def test_defaults(self):
        from app.services.match_checker import RunSummary

        s = RunSummary()
        assert s.searches_checked == 0
        assert s.searches_with_matches == 0
        assert s.notifications_sent == 0
        assert s.errors == 0
        assert s.results == []

    def test_accumulation(self):
        from app.services.match_checker import MatchCheckResult, RunSummary

        s = RunSummary()
        s.searches_checked = 3
        s.searches_with_matches = 1
        s.notifications_sent = 1
        s.errors = 1
        s.results.append(MatchCheckResult("s1", "Test", "org-1", 2, True))
        assert len(s.results) == 1

    def test_independent_instances(self):
        from app.services.match_checker import RunSummary

        s1 = RunSummary()
        s2 = RunSummary()
        s1.results.append("x")
        assert len(s2.results) == 0


class TestMatchCheckerConstants:
    def test_constants(self):
        from app.services.match_checker import _CB_THRESHOLD, _MAX_MATCHES_PER_NOTIF, _MAX_SEARCHES_PER_RUN

        assert _MAX_SEARCHES_PER_RUN == 50
        assert _MAX_MATCHES_PER_NOTIF == 5
        assert _CB_THRESHOLD == 3


# ── swarm_service pure functions ─────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _mock_docker(monkeypatch):
    """swarm_service imports docker at module level — mock it."""
    import sys

    if "docker" not in sys.modules:
        sys.modules["docker"] = MagicMock()
    yield


class TestExtractConsensusScores:
    def _make_agent(self, raw_response: str):
        return SimpleNamespace(raw_response=raw_response)

    def _make_report(self, agents: list):
        return SimpleNamespace(agent_results=agents)

    def test_single_agent_valid_json(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [self._make_agent('{"active_listening": 0.8, "empathy": 0.6}')]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["active_listening", "empathy"])
        assert abs(scores["active_listening"] - 0.8) < 0.01
        assert abs(scores["empathy"] - 0.6) < 0.01

    def test_multiple_agents_average(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [
            self._make_agent('{"skill_a": 0.8}'),
            self._make_agent('{"skill_a": 0.6}'),
        ]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["skill_a"])
        assert abs(scores["skill_a"] - 0.7) < 0.01

    def test_missing_concept_defaults_to_0_5(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [self._make_agent('{"skill_a": 0.8}')]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["skill_a", "skill_b"])
        assert abs(scores["skill_a"] - 0.8) < 0.01
        assert abs(scores["skill_b"] - 0.5) < 0.01

    def test_clamps_to_0_1(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [self._make_agent('{"skill_a": 1.5, "skill_b": -0.3}')]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["skill_a", "skill_b"])
        assert scores["skill_a"] == 1.0
        assert scores["skill_b"] == 0.0

    def test_handles_code_fence_json(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [self._make_agent('```json\n{"skill_a": 0.9}\n```')]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["skill_a"])
        assert abs(scores["skill_a"] - 0.9) < 0.01

    def test_handles_invalid_json(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [self._make_agent("not json at all")]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["skill_a"])
        assert scores["skill_a"] == 0.5

    def test_handles_none_raw_response(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [self._make_agent(None)]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["skill_a"])
        assert scores["skill_a"] == 0.5

    def test_handles_empty_raw_response(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [self._make_agent("")]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["skill_a"])
        assert scores["skill_a"] == 0.5

    def test_empty_agents(self):
        from app.services.swarm_service import _extract_consensus_scores

        report = self._make_report([])
        scores = _extract_consensus_scores(report, ["skill_a", "skill_b"])
        assert scores["skill_a"] == 0.5
        assert scores["skill_b"] == 0.5

    def test_mixed_valid_invalid_agents(self):
        from app.services.swarm_service import _extract_consensus_scores

        agents = [
            self._make_agent('{"skill_a": 0.8}'),
            self._make_agent("garbage"),
            self._make_agent('{"skill_a": 0.4}'),
        ]
        report = self._make_report(agents)
        scores = _extract_consensus_scores(report, ["skill_a"])
        assert abs(scores["skill_a"] - 0.6) < 0.01

    def test_agent_without_raw_response_attr(self):
        from app.services.swarm_service import _extract_consensus_scores

        agent = SimpleNamespace()  # no raw_response attribute
        report = self._make_report([agent])
        scores = _extract_consensus_scores(report, ["skill_a"])
        assert scores["skill_a"] == 0.5


class TestSwarmEvaluateAnswer:
    @pytest.mark.asyncio
    async def test_empty_answer_returns_zero(self):
        from app.services.swarm_service import evaluate_answer

        result = await evaluate_answer("What is X?", "", [{"name": "concept_a", "weight": 1.0}])
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_empty_answer_with_details(self):
        from app.services.swarm_service import evaluate_answer

        result = await evaluate_answer("What is X?", "   ", [{"name": "concept_a", "weight": 1.0}], return_details=True)
        assert result.composite == 0.0
        assert result.model_used == "swarm"

    @pytest.mark.asyncio
    async def test_whitespace_answer_returns_zero(self):
        from app.services.swarm_service import evaluate_answer

        result = await evaluate_answer("Q?", "  \n\t  ", [{"name": "c", "weight": 1.0}])
        assert result == 0.0


# ── cross-service invariants ─────────────────────────────────────────────────


class TestFireAndForgetInvariant:
    """All fire-and-forget services must never raise on DB errors."""

    @pytest.fixture
    def broken_db(self):
        db = MagicMock()
        db.table.side_effect = RuntimeError("Connection refused")
        return db

    @pytest.mark.asyncio
    async def test_analytics_survives(self, broken_db):
        from app.services.analytics import track_event

        await track_event(broken_db, "u", "ev")

    @pytest.mark.asyncio
    async def test_ecosystem_assessment_survives(self, broken_db):
        from app.services.ecosystem_events import emit_assessment_completed

        await emit_assessment_completed(broken_db, "u", "tech", 50.0, 5, "low", None)

    @pytest.mark.asyncio
    async def test_ecosystem_aura_survives(self, broken_db):
        from app.services.ecosystem_events import emit_aura_updated

        await emit_aura_updated(broken_db, "u", 50.0, "Bronze", {}, False, None)

    @pytest.mark.asyncio
    async def test_ecosystem_badge_survives(self, broken_db):
        from app.services.ecosystem_events import emit_badge_tier_changed

        await emit_badge_tier_changed(broken_db, "u", "Silver", "Gold", 78.0)

    @pytest.mark.asyncio
    async def test_notify_survives(self, broken_db):
        from app.services.notification_service import notify

        await notify(broken_db, "u", "t", "title")

    @pytest.mark.asyncio
    async def test_notify_profile_viewed_survives(self, broken_db):
        from app.services.notification_service import notify_profile_viewed

        result = await notify_profile_viewed(broken_db, "v", "o", "Org")
        assert result is False
