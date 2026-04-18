"""Unit tests for assessment service modules: coaching, helpers, rewards.

Covers:
- coaching_service: fallback tips structure, per-competency coverage, default fallback,
  markdown fence stripping, generate_coaching_tips with mocked Gemini
- helpers: question cache, options normalization, make_session_out builder,
  clear_question_cache
- rewards: competency_badge_tier thresholds, CRYSTAL_REWARD constant,
  emit_assessment_rewards idempotency + crystal + skill_verified paths
"""

from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.assessment.coaching_service import (
    _DEFAULT_FALLBACK_TIPS,
    _FALLBACK_TIPS,
    generate_coaching_tips,
)
from app.services.assessment.helpers import (
    _QUESTION_CACHE,
    _QUESTION_CACHE_TTL,
    clear_question_cache,
    fetch_questions,
    make_session_out,
)
from app.services.assessment.rewards import (
    CRYSTAL_REWARD,
    competency_badge_tier,
    emit_assessment_rewards,
)

# ── Helper: Supabase mock that mirrors sync builder + async execute ───────────


def _make_supabase_mock(**kwargs):
    """Build a MagicMock that mirrors Supabase's sync builder chain.

    table().select().eq().eq()...execute() — all sync except execute() which is async.
    """
    db = MagicMock()
    builder = MagicMock()
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.insert.return_value = builder
    builder.upsert.return_value = builder
    builder.single.return_value = builder

    result = MagicMock()
    result.data = kwargs.get("data", [])
    builder.execute = AsyncMock(return_value=result)

    db.table.return_value = builder
    return db, builder


# ── coaching_service ──────────────────────────────────────────────────────────


class TestFallbackTipsStructure:
    ALL_COMPETENCY_SLUGS = [
        "communication",
        "reliability",
        "leadership",
        "english_proficiency",
        "adaptability",
        "tech_literacy",
        "event_performance",
        "empathy_safeguarding",
    ]

    @pytest.mark.parametrize("slug", ALL_COMPETENCY_SLUGS)
    def test_each_competency_has_exactly_3_fallback_tips(self, slug: str):
        tips = _FALLBACK_TIPS[slug]
        assert len(tips) == 3

    @pytest.mark.parametrize("slug", ALL_COMPETENCY_SLUGS)
    def test_each_fallback_tip_has_required_keys(self, slug: str):
        for tip in _FALLBACK_TIPS[slug]:
            assert "title" in tip
            assert "description" in tip
            assert "action" in tip
            assert isinstance(tip["title"], str)
            assert len(tip["title"]) > 0

    def test_default_fallback_has_3_tips(self):
        assert len(_DEFAULT_FALLBACK_TIPS) == 3

    def test_default_fallback_tip_structure(self):
        for tip in _DEFAULT_FALLBACK_TIPS:
            assert set(tip.keys()) == {"title", "description", "action"}

    def test_unknown_slug_falls_back_to_default(self):
        result = _FALLBACK_TIPS.get("nonexistent_slug", _DEFAULT_FALLBACK_TIPS)
        assert result is _DEFAULT_FALLBACK_TIPS


class TestGenerateCoachingTips:
    @pytest.mark.asyncio
    async def test_no_api_key_returns_fallback(self):
        tips = await generate_coaching_tips(
            session_id="s1",
            competency_id="c1",
            competency_name="Communication",
            competency_slug="communication",
            score=75.0,
            gemini_api_key=None,
        )
        assert len(tips) == 3
        assert tips[0].title == _FALLBACK_TIPS["communication"][0]["title"]

    @pytest.mark.asyncio
    async def test_unknown_slug_uses_default_fallback(self):
        tips = await generate_coaching_tips(
            session_id="s1",
            competency_id="c1",
            competency_name="Mystery",
            competency_slug="mystery_skill",
            score=50.0,
            gemini_api_key=None,
        )
        assert len(tips) == 3
        assert tips[0].title == _DEFAULT_FALLBACK_TIPS[0]["title"]

    @pytest.mark.asyncio
    async def test_gemini_success_returns_parsed_tips(self):
        gemini_response = json.dumps(
            {
                "tips": [
                    {"title": "T1", "description": "D1", "action": "A1"},
                    {"title": "T2", "description": "D2", "action": "A2"},
                    {"title": "T3", "description": "D3", "action": "A3"},
                ]
            }
        )
        mock_response = MagicMock()
        mock_response.text = gemini_response
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            tips = await generate_coaching_tips(
                session_id="s1",
                competency_id="c1",
                competency_name="Reliability",
                competency_slug="reliability",
                score=60.0,
                gemini_api_key="fake-key",
            )
        assert len(tips) == 3
        assert tips[0].title == "T1"

    @pytest.mark.asyncio
    async def test_gemini_markdown_fence_stripped(self):
        fenced = '```json\n{"tips": [{"title":"X","description":"Y","action":"Z"}]}\n```'
        mock_response = MagicMock()
        mock_response.text = fenced
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            tips = await generate_coaching_tips(
                session_id="s1",
                competency_id="c1",
                competency_name="Test",
                competency_slug="communication",
                score=50.0,
                gemini_api_key="fake-key",
            )
        assert len(tips) >= 1
        assert tips[0].title == "X"

    @pytest.mark.asyncio
    async def test_gemini_exception_returns_fallback(self):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("API error")

        with patch("google.genai.Client", return_value=mock_client):
            tips = await generate_coaching_tips(
                session_id="s1",
                competency_id="c1",
                competency_name="Test",
                competency_slug="reliability",
                score=50.0,
                gemini_api_key="fake-key",
            )
        assert len(tips) == 3
        assert tips[0].title == _FALLBACK_TIPS["reliability"][0]["title"]

    @pytest.mark.asyncio
    async def test_gemini_invalid_json_returns_fallback(self):
        mock_response = MagicMock()
        mock_response.text = "not valid json at all"
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            tips = await generate_coaching_tips(
                session_id="s1",
                competency_id="c1",
                competency_name="Test",
                competency_slug="adaptability",
                score=30.0,
                gemini_api_key="fake-key",
            )
        assert len(tips) == 3
        assert tips[0].title == _FALLBACK_TIPS["adaptability"][0]["title"]

    @pytest.mark.asyncio
    async def test_gemini_empty_tips_returns_fallback(self):
        mock_response = MagicMock()
        mock_response.text = '{"tips": []}'
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            tips = await generate_coaching_tips(
                session_id="s1",
                competency_id="c1",
                competency_name="Test",
                competency_slug="leadership",
                score=80.0,
                gemini_api_key="fake-key",
            )
        assert len(tips) == 3
        assert tips[0].title == _FALLBACK_TIPS["leadership"][0]["title"]

    @pytest.mark.asyncio
    async def test_gemini_none_text_returns_fallback(self):
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            tips = await generate_coaching_tips(
                session_id="s1",
                competency_id="c1",
                competency_name="Test",
                competency_slug="tech_literacy",
                score=45.0,
                gemini_api_key="fake-key",
            )
        assert len(tips) == 3
        assert tips[0].title == _FALLBACK_TIPS["tech_literacy"][0]["title"]

    @pytest.mark.asyncio
    async def test_gemini_extra_tips_truncated_to_3(self):
        payload = json.dumps(
            {"tips": [{"title": f"T{i}", "description": f"D{i}", "action": f"A{i}"} for i in range(5)]}
        )
        mock_response = MagicMock()
        mock_response.text = payload
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            tips = await generate_coaching_tips(
                session_id="s1",
                competency_id="c1",
                competency_name="Test",
                competency_slug="communication",
                score=50.0,
                gemini_api_key="fake-key",
            )
        assert len(tips) == 3


# ── helpers ───────────────────────────────────────────────────────────────────


class TestClearQuestionCache:
    def test_clears_both_caches(self):
        from app.services.assessment.helpers import _COMPETENCY_SLUG_CACHE

        _QUESTION_CACHE["test"] = (time.monotonic(), [{"id": "q1"}])
        _COMPETENCY_SLUG_CACHE["test-id"] = "test-slug"
        clear_question_cache()
        assert len(_QUESTION_CACHE) == 0
        assert len(_COMPETENCY_SLUG_CACHE) == 0


class TestMakeSessionOut:
    def _make_cat_state(self, stopped=False, stop_reason=None, items=None):
        state = MagicMock()
        state.stopped = stopped
        state.stop_reason = stop_reason
        state.items = items or []
        return state

    def test_active_session_with_next_question(self):
        state = self._make_cat_state(stopped=False, items=[1, 2])
        q = {
            "id": "q-abc",
            "type": "mcq",
            "scenario_en": "What?",
            "scenario_az": "Nə?",
            "scenario_ru": "Что?",
            "options": [{"text": "A"}, {"text": "B"}],
            "competency_id": "c-123",
        }
        out = make_session_out("sess-1", "communication", state, q)
        assert out.session_id == "sess-1"
        assert out.competency_slug == "communication"
        assert out.questions_answered == 2
        assert out.is_complete is False
        assert out.next_question is not None
        assert out.next_question.id == "q-abc"
        assert out.next_question.question_type == "mcq"
        assert out.next_question.question_en == "What?"

    def test_completed_session_no_next_question(self):
        state = self._make_cat_state(stopped=True, stop_reason="max_items", items=[1, 2, 3])
        q = {
            "id": "q1",
            "type": "mcq",
            "scenario_en": "X",
            "scenario_az": "Y",
            "options": None,
            "competency_id": "c1",
        }
        out = make_session_out("sess-2", "reliability", state, q)
        assert out.is_complete is True
        assert out.stop_reason == "max_items"
        assert out.next_question is None

    def test_no_next_question_dict(self):
        state = self._make_cat_state(stopped=False, items=[])
        out = make_session_out("sess-3", "leadership", state, None)
        assert out.next_question is None
        assert out.questions_answered == 0

    def test_role_level_default(self):
        state = self._make_cat_state()
        out = make_session_out("s", "x", state, None)
        assert out.role_level == "professional"

    def test_role_level_custom(self):
        state = self._make_cat_state()
        out = make_session_out("s", "x", state, None, role_level="senior")
        assert out.role_level == "senior"

    def test_optional_scenario_ru(self):
        state = self._make_cat_state(stopped=False, items=[])
        q = {
            "id": "q1",
            "type": "open_text",
            "scenario_en": "Describe",
            "scenario_az": "Təsvir et",
            "competency_id": "c1",
        }
        out = make_session_out("s", "comm", state, q)
        assert out.next_question is not None
        assert out.next_question.question_ru is None


class TestFetchQuestions:
    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        clear_question_cache()
        yield
        clear_question_cache()

    def _make_db(self, questions):
        db = MagicMock()
        builder = MagicMock()
        builder.select.return_value = builder
        builder.eq.return_value = builder
        result = MagicMock()
        result.data = questions
        builder.execute = AsyncMock(return_value=result)
        db.table.return_value = builder
        return db, builder

    @pytest.mark.asyncio
    async def test_caches_questions(self):
        questions = [
            {
                "id": "q1",
                "type": "mcq",
                "scenario_en": "A",
                "scenario_az": "B",
                "options": None,
                "competency_id": "c1",
            }
        ]
        db, builder = self._make_db(questions)

        r1 = await fetch_questions(db, "c1")
        r2 = await fetch_questions(db, "c1")
        assert len(r1) == 1
        assert len(r2) == 1
        builder.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_normalizes_double_encoded_options(self):
        raw_options = json.dumps([{"text": "A"}, {"text": "B"}])
        questions = [
            {
                "id": "q1",
                "type": "mcq",
                "scenario_en": "X",
                "scenario_az": "Y",
                "options": raw_options,
                "competency_id": "c1",
            }
        ]
        db, _ = self._make_db(questions)

        fetched = await fetch_questions(db, "c1")
        assert isinstance(fetched[0]["options"], list)
        assert fetched[0]["options"][0]["text"] == "A"

    @pytest.mark.asyncio
    async def test_invalid_json_options_set_to_none(self):
        questions = [
            {
                "id": "q1",
                "type": "mcq",
                "scenario_en": "X",
                "scenario_az": "Y",
                "options": "not-json{",
                "competency_id": "c1",
            }
        ]
        db, _ = self._make_db(questions)

        fetched = await fetch_questions(db, "c1")
        assert fetched[0]["options"] is None

    @pytest.mark.asyncio
    async def test_non_list_json_options_set_to_none(self):
        questions = [
            {
                "id": "q1",
                "type": "mcq",
                "scenario_en": "X",
                "scenario_az": "Y",
                "options": '{"key": "val"}',
                "competency_id": "c1",
            }
        ]
        db, _ = self._make_db(questions)

        fetched = await fetch_questions(db, "c1")
        assert fetched[0]["options"] is None

    @pytest.mark.asyncio
    async def test_cache_expiry(self):
        questions = [
            {
                "id": "q1",
                "type": "mcq",
                "scenario_en": "X",
                "scenario_az": "Y",
                "options": None,
                "competency_id": "c1",
            }
        ]
        db, builder = self._make_db(questions)

        await fetch_questions(db, "c1")
        _QUESTION_CACHE["c1"] = (
            time.monotonic() - _QUESTION_CACHE_TTL - 1,
            _QUESTION_CACHE["c1"][1],
        )
        await fetch_questions(db, "c1")
        assert builder.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_returns_copies_not_references(self):
        questions = [
            {
                "id": "q1",
                "type": "mcq",
                "scenario_en": "X",
                "scenario_az": "Y",
                "options": None,
                "competency_id": "c1",
            }
        ]
        db, _ = self._make_db(questions)

        r1 = await fetch_questions(db, "c1")
        r1[0]["id"] = "MUTATED"
        r2 = await fetch_questions(db, "c1")
        assert r2[0]["id"] == "q1"

    @pytest.mark.asyncio
    async def test_empty_result(self):
        db, _ = self._make_db([])
        fetched = await fetch_questions(db, "c-empty")
        assert fetched == []

    @pytest.mark.asyncio
    async def test_none_result_data(self):
        db, _ = self._make_db(None)
        fetched = await fetch_questions(db, "c-none")
        assert fetched == []


# ── rewards ───────────────────────────────────────────────────────────────────


class TestCompetencyBadgeTier:
    @pytest.mark.parametrize(
        "score, expected",
        [
            (100.0, "platinum"),
            (90.0, "platinum"),
            (89.9, "gold"),
            (75.0, "gold"),
            (74.9, "silver"),
            (60.0, "silver"),
            (59.9, "bronze"),
            (40.0, "bronze"),
            (39.9, None),
            (0.0, None),
        ],
    )
    def test_tier_boundaries(self, score: float, expected: str | None):
        assert competency_badge_tier(score) == expected


class TestCrystalReward:
    def test_constant_value(self):
        assert CRYSTAL_REWARD == 50


class TestEmitAssessmentRewards:
    def _mock_db(self, already_claimed: bool = False):
        db = MagicMock()
        builder = MagicMock()
        builder.select.return_value = builder
        builder.eq.return_value = builder
        builder.insert.return_value = builder
        builder.upsert.return_value = builder

        reward_result = MagicMock()
        reward_result.data = [{"claimed": True}] if already_claimed else []
        builder.execute = AsyncMock(return_value=reward_result)

        db.table.return_value = builder
        return db

    @pytest.mark.asyncio
    async def test_new_reward_returns_crystal_amount(self):
        db = self._mock_db(already_claimed=False)
        with (
            patch("app.services.assessment.rewards.notify", new_callable=AsyncMock),
            patch(
                "app.services.assessment.rewards.push_crystal_earned",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.assessment.rewards.push_skill_verified",
                new_callable=AsyncMock,
            ),
        ):
            crystals = await emit_assessment_rewards(db, "u1", "communication", 80.0)
        assert crystals == CRYSTAL_REWARD

    @pytest.mark.asyncio
    async def test_already_claimed_returns_zero(self):
        db = self._mock_db(already_claimed=True)
        with (
            patch("app.services.assessment.rewards.notify", new_callable=AsyncMock),
            patch(
                "app.services.assessment.rewards.push_skill_verified",
                new_callable=AsyncMock,
            ),
        ):
            crystals = await emit_assessment_rewards(db, "u1", "reliability", 75.0)
        assert crystals == 0

    @pytest.mark.asyncio
    async def test_below_bronze_no_skill_verified(self):
        db = self._mock_db(already_claimed=False)
        with (
            patch("app.services.assessment.rewards.notify", new_callable=AsyncMock),
            patch(
                "app.services.assessment.rewards.push_crystal_earned",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.assessment.rewards.push_skill_verified",
                new_callable=AsyncMock,
            ) as mock_push,
        ):
            await emit_assessment_rewards(db, "u1", "leadership", 30.0)
        mock_push.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_above_bronze_emits_skill_verified(self):
        db = self._mock_db(already_claimed=False)
        with (
            patch("app.services.assessment.rewards.notify", new_callable=AsyncMock),
            patch(
                "app.services.assessment.rewards.push_crystal_earned",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.assessment.rewards.push_skill_verified",
                new_callable=AsyncMock,
            ) as mock_push,
        ):
            await emit_assessment_rewards(db, "u1", "leadership", 60.0)
        mock_push.assert_awaited_once()
        call_kwargs = mock_push.call_args.kwargs
        assert call_kwargs["badge_tier"] == "silver"

    @pytest.mark.asyncio
    async def test_crystal_insert_failure_does_not_raise(self):
        db = MagicMock()
        builder = MagicMock()
        builder.select.return_value = builder
        builder.eq.return_value = builder

        not_claimed = MagicMock()
        not_claimed.data = []
        builder.execute = AsyncMock(return_value=not_claimed)

        fail_builder = MagicMock()
        fail_builder.execute = AsyncMock(side_effect=Exception("DB down"))
        builder.insert.return_value = fail_builder
        builder.upsert.return_value = fail_builder

        db.table.return_value = builder

        with (
            patch("app.services.assessment.rewards.notify", new_callable=AsyncMock),
            patch(
                "app.services.assessment.rewards.push_crystal_earned",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.assessment.rewards.push_skill_verified",
                new_callable=AsyncMock,
            ),
        ):
            crystals = await emit_assessment_rewards(db, "u1", "comm", 50.0)
        assert isinstance(crystals, int)

    @pytest.mark.asyncio
    async def test_user_jwt_forwarded_to_push(self):
        db = self._mock_db(already_claimed=False)
        with (
            patch("app.services.assessment.rewards.notify", new_callable=AsyncMock),
            patch(
                "app.services.assessment.rewards.push_crystal_earned",
                new_callable=AsyncMock,
            ) as mock_crystal,
            patch(
                "app.services.assessment.rewards.push_skill_verified",
                new_callable=AsyncMock,
            ) as mock_skill,
        ):
            await emit_assessment_rewards(db, "u1", "comm", 90.0, user_jwt="jwt-xyz")
        assert mock_crystal.call_args.kwargs["user_jwt"] == "jwt-xyz"
        assert mock_skill.call_args.kwargs["user_jwt"] == "jwt-xyz"
