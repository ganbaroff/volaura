"""Unit tests for app.services.reeval_worker — 36 tests across 8 categories."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.reeval_worker import (
    BATCH_SIZE,
    MAX_AGE_HOURS,
    MAX_RETRIES,
    POLL_INTERVAL_S,
    STALE_TIMEOUT_S,
    _fetch_pending_batch,
    _mark_processing,
    _process_item,
    _reconcile_aura,
    _reconcile_session,
    _recover_stale_items,
    enqueue_degraded_answer,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_eval_result(composite: float = 0.85, model: str = "gemini-2.5-flash") -> MagicMock:
    er = MagicMock()
    er.composite = composite
    er.model_used = model
    er.to_log.return_value = {"method": "bars", "composite": composite}
    return er


class _FakeQueryBuilder:
    """Mimics Supabase query builder: sync chaining returns self, execute() is async.

    Records call args for assertions.
    """

    def __init__(self) -> None:
        self.execute = AsyncMock()
        self._calls: dict[str, list[tuple]] = {}

    def _record(self, name: str, *args: Any, **kwargs: Any) -> _FakeQueryBuilder:
        self._calls.setdefault(name, []).append((args, kwargs))
        return self

    def table(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("table", *a, **kw)

    def insert(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("insert", *a, **kw)

    def update(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("update", *a, **kw)

    def select(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("select", *a, **kw)

    def eq(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("eq", *a, **kw)

    def lt(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("lt", *a, **kw)

    def order(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("order", *a, **kw)

    def limit(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("limit", *a, **kw)

    def single(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("single", *a, **kw)

    def maybe_single(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("maybe_single", *a, **kw)

    def rpc(self, *a: Any, **kw: Any) -> _FakeQueryBuilder:
        return self._record("rpc", *a, **kw)

    def called(self, name: str) -> bool:
        return name in self._calls

    def call_args_for(self, name: str) -> list[tuple]:
        return self._calls.get(name, [])

    def last_args(self, name: str) -> tuple:
        return self._calls[name][-1]

    def first_positional(self, name: str) -> Any:
        return self._calls[name][-1][0][0]


def _db() -> _FakeQueryBuilder:
    return _FakeQueryBuilder()


def _make_queue_item(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "item-uuid-1",
        "session_id": "sess-1",
        "volunteer_id": "vol-1",
        "question_id": "q-1",
        "competency_slug": "communication",
        "question_en": "What is leadership?",
        "answer_text": "Leadership is guiding people.",
        "expected_concepts": [{"concept": "guidance", "weight": 1.0}],
        "degraded_score": 0.4,
        "retry_count": 0,
        "status": "pending",
        "queued_at": datetime.now(UTC).isoformat(),
    }
    base.update(overrides)
    return base


# ── 1. Constants ─────────────────────────────────────────────────────────────


class TestConstants:
    def test_poll_interval(self):
        assert POLL_INTERVAL_S == 60.0

    def test_batch_size(self):
        assert BATCH_SIZE == 10

    def test_stale_timeout(self):
        assert STALE_TIMEOUT_S == 300.0

    def test_max_retries(self):
        assert MAX_RETRIES == 3

    def test_max_age_hours(self):
        assert MAX_AGE_HOURS == 72.0


# ── 2. enqueue_degraded_answer ───────────────────────────────────────────────


class TestEnqueueDegradedAnswer:
    @pytest.mark.asyncio
    async def test_happy_path_returns_uuid(self):
        db = _db()
        db.execute.return_value = MagicMock(data=[{"id": "new-uuid-123"}])

        result = await enqueue_degraded_answer(
            db,
            session_id="s1",
            volunteer_id="v1",
            question_id="q1",
            competency_slug="communication",
            question_en="What?",
            answer_text="Answer.",
            expected_concepts=[{"c": "x"}],
            degraded_score=0.3,
        )
        assert result == "new-uuid-123"

    @pytest.mark.asyncio
    async def test_returns_none_when_data_empty(self):
        db = _db()
        db.execute.return_value = MagicMock(data=[])

        result = await enqueue_degraded_answer(
            db,
            session_id="s1",
            volunteer_id="v1",
            question_id="q1",
            competency_slug="communication",
            question_en="What?",
            answer_text="Answer.",
            expected_concepts=[],
            degraded_score=0.3,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_error_returns_none_no_raise(self):
        db = _db()
        db.execute.side_effect = Exception("table not found")

        result = await enqueue_degraded_answer(
            db,
            session_id="s1",
            volunteer_id="v1",
            question_id="q1",
            competency_slug="communication",
            question_en="What?",
            answer_text="Answer.",
            expected_concepts=[],
            degraded_score=0.3,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_inserts_correct_payload(self):
        db = _db()
        db.execute.return_value = MagicMock(data=[{"id": "x"}])

        await enqueue_degraded_answer(
            db,
            session_id="s1",
            volunteer_id="v1",
            question_id="q1",
            competency_slug="leadership",
            question_en="Q?",
            answer_text="A.",
            expected_concepts=[{"c": "lead"}],
            degraded_score=0.5,
        )

        assert db.called("table")
        assert db.first_positional("table") == "evaluation_queue"
        payload = db.first_positional("insert")
        assert payload["session_id"] == "s1"
        assert payload["competency_slug"] == "leadership"
        assert payload["status"] == "pending"
        assert payload["degraded_score"] == 0.5


# ── 3. _recover_stale_items ─────────────────────────────────────────────────


class TestRecoverStaleItems:
    @pytest.mark.asyncio
    async def test_recovers_stale_items(self):
        db = _db()
        db.execute.return_value = MagicMock(data=[{"id": "stale-1"}, {"id": "stale-2"}])

        await _recover_stale_items(db)

        assert db.first_positional("table") == "evaluation_queue"
        update_payload = db.first_positional("update")
        assert update_payload["status"] == "pending"
        assert update_payload["started_at"] is None
        eq_calls = [args for args, _ in db.call_args_for("eq")]
        assert ("status", "processing") in eq_calls

    @pytest.mark.asyncio
    async def test_no_stale_items(self):
        db = _db()
        db.execute.return_value = MagicMock(data=[])

        await _recover_stale_items(db)
        assert db.called("update")

    @pytest.mark.asyncio
    async def test_exception_swallowed(self):
        db = _db()
        db.execute.side_effect = Exception("db down")

        await _recover_stale_items(db)


# ── 4. _fetch_pending_batch ─────────────────────────────────────────────────


class TestFetchPendingBatch:
    @pytest.mark.asyncio
    async def test_expires_old_then_fetches(self):
        db = _db()
        expired_result = MagicMock(data=[{"id": "old-1"}])
        fetch_result = MagicMock(data=[_make_queue_item()])
        db.execute.side_effect = [expired_result, fetch_result]

        items = await _fetch_pending_batch(db)
        assert len(items) == 1
        assert items[0]["id"] == "item-uuid-1"

    @pytest.mark.asyncio
    async def test_empty_queue(self):
        db = _db()
        db.execute.side_effect = [
            MagicMock(data=None),
            MagicMock(data=None),
        ]

        items = await _fetch_pending_batch(db)
        assert items == []

    @pytest.mark.asyncio
    async def test_exception_returns_empty_list(self):
        db = _db()
        db.execute.side_effect = Exception("timeout")

        items = await _fetch_pending_batch(db)
        assert items == []

    @pytest.mark.asyncio
    async def test_orders_by_queued_at_asc(self):
        db = _db()
        db.execute.side_effect = [MagicMock(data=None), MagicMock(data=[])]

        await _fetch_pending_batch(db)
        order_calls = db.call_args_for("order")
        assert any(args == ("queued_at",) and kw.get("desc") is False for args, kw in order_calls)

    @pytest.mark.asyncio
    async def test_limits_to_batch_size(self):
        db = _db()
        db.execute.side_effect = [MagicMock(data=None), MagicMock(data=[])]

        await _fetch_pending_batch(db)
        assert db.first_positional("limit") == BATCH_SIZE


# ── 5. _mark_processing ─────────────────────────────────────────────────────


class TestMarkProcessing:
    @pytest.mark.asyncio
    async def test_sets_status_and_started_at(self):
        db = _db()
        db.execute.return_value = MagicMock(data=[])

        await _mark_processing(db, "item-42")

        assert db.first_positional("table") == "evaluation_queue"
        update_payload = db.first_positional("update")
        assert update_payload["status"] == "processing"
        assert "started_at" in update_payload
        eq_calls = [args for args, _ in db.call_args_for("eq")]
        assert ("id", "item-42") in eq_calls
        assert ("status", "pending") in eq_calls


# ── 6. _process_item ────────────────────────────────────────────────────────


class TestProcessItem:
    @pytest.mark.asyncio
    @patch("app.services.reeval_worker.evaluate_answer", new_callable=AsyncMock)
    @patch("app.services.reeval_worker._reconcile_aura", new_callable=AsyncMock)
    @patch("app.services.reeval_worker._reconcile_session", new_callable=AsyncMock)
    @patch("app.services.reeval_worker._mark_processing", new_callable=AsyncMock)
    async def test_happy_path(self, mock_mark, mock_recon_sess, mock_recon_aura, mock_eval):
        eval_result = _make_eval_result(0.9, "gemini-2.5-flash")
        mock_eval.return_value = eval_result
        db = _db()
        db.execute.return_value = MagicMock(data=[])
        item = _make_queue_item()

        await _process_item(db, item)

        mock_mark.assert_awaited_once_with(db, "item-uuid-1")
        mock_eval.assert_awaited_once()
        mock_recon_sess.assert_awaited_once()
        mock_recon_aura.assert_awaited_once()
        assert db.called("update")
        final_update = db.first_positional("update")
        assert final_update["status"] == "done"
        assert final_update["llm_score"] == 0.9

    @pytest.mark.asyncio
    @patch("app.services.reeval_worker.evaluate_answer", new_callable=AsyncMock)
    @patch("app.services.reeval_worker._mark_processing", new_callable=AsyncMock)
    async def test_error_increments_retry_stays_pending(self, mock_mark, mock_eval):
        mock_eval.side_effect = Exception("LLM timeout")
        db = _db()
        db.execute.return_value = MagicMock(data=[])
        item = _make_queue_item(retry_count=1)

        await _process_item(db, item)

        update_payload = db.first_positional("update")
        assert update_payload["retry_count"] == 2
        assert update_payload["status"] == "pending"

    @pytest.mark.asyncio
    @patch("app.services.reeval_worker.evaluate_answer", new_callable=AsyncMock)
    @patch("app.services.reeval_worker._mark_processing", new_callable=AsyncMock)
    async def test_error_at_max_retries_sets_failed(self, mock_mark, mock_eval):
        mock_eval.side_effect = Exception("LLM down")
        db = _db()
        db.execute.return_value = MagicMock(data=[])
        item = _make_queue_item(retry_count=2)

        await _process_item(db, item)

        update_payload = db.first_positional("update")
        assert update_payload["retry_count"] == 3
        assert update_payload["status"] == "failed"

    @pytest.mark.asyncio
    @patch("app.services.reeval_worker.evaluate_answer", new_callable=AsyncMock)
    @patch("app.services.reeval_worker._mark_processing", new_callable=AsyncMock)
    async def test_expected_concepts_json_string_parsed(self, mock_mark, mock_eval):
        eval_result = _make_eval_result()
        mock_eval.return_value = eval_result
        db = _db()
        db.execute.return_value = MagicMock(data=[])
        concepts_as_string = json.dumps([{"c": "x"}])
        item = _make_queue_item(expected_concepts=concepts_as_string)

        with patch("app.services.reeval_worker._reconcile_session", new_callable=AsyncMock), \
             patch("app.services.reeval_worker._reconcile_aura", new_callable=AsyncMock):
            await _process_item(db, item)

        mock_eval.assert_awaited_once()
        call_kwargs = mock_eval.call_args.kwargs
        assert isinstance(call_kwargs["expected_concepts"], list)

    @pytest.mark.asyncio
    @patch("app.services.reeval_worker.evaluate_answer", new_callable=AsyncMock)
    @patch("app.services.reeval_worker._mark_processing", new_callable=AsyncMock)
    async def test_error_update_failure_does_not_raise(self, mock_mark, mock_eval):
        """Double failure: eval fails, then DB update also fails. No exception escapes."""
        mock_eval.side_effect = Exception("LLM down")
        db = _db()
        db.execute.side_effect = Exception("DB also down")
        item = _make_queue_item()

        await _process_item(db, item)

    @pytest.mark.asyncio
    @patch("app.services.reeval_worker.evaluate_answer", new_callable=AsyncMock)
    @patch("app.services.reeval_worker._mark_processing", new_callable=AsyncMock)
    async def test_score_delta_computed(self, mock_mark, mock_eval):
        eval_result = _make_eval_result(0.9)
        mock_eval.return_value = eval_result
        db = _db()
        db.execute.return_value = MagicMock(data=[])
        item = _make_queue_item(degraded_score=0.4)

        with patch("app.services.reeval_worker._reconcile_session", new_callable=AsyncMock), \
             patch("app.services.reeval_worker._reconcile_aura", new_callable=AsyncMock):
            await _process_item(db, item)

        final_update = db.first_positional("update")
        assert final_update["score_delta"] == round(0.9 - 0.4, 4)


# ── 7. _reconcile_session ───────────────────────────────────────────────────


class TestReconcileSession:
    @pytest.mark.asyncio
    async def test_patches_correct_question(self):
        db = _db()
        answers = [
            {"question_id": "q-other", "raw_score": 0.5},
            {"question_id": "q-1", "raw_score": 0.3, "evaluation_log": {}},
        ]
        db.execute.side_effect = [
            MagicMock(data={"answers": answers}),
            MagicMock(data=[]),
        ]
        eval_result = _make_eval_result(0.88)

        await _reconcile_session(
            db,
            session_id="sess-1",
            question_id="q-1",
            llm_score=0.88,
            llm_model="gemini-2.5-flash",
            eval_result=eval_result,
        )

        update_calls = db.call_args_for("update")
        assert len(update_calls) == 1
        patched_answers = update_calls[0][0][0]["answers"]
        target = next(a for a in patched_answers if a["question_id"] == "q-1")
        assert target["raw_score"] == 0.88
        assert target["evaluation_log"]["reeval_from"] == "keyword_fallback"
        assert target["evaluation_log"]["reeval_model"] == "gemini-2.5-flash"
        other = next(a for a in patched_answers if a["question_id"] == "q-other")
        assert other["raw_score"] == 0.5

    @pytest.mark.asyncio
    async def test_session_not_found(self):
        db = _db()
        db.execute.return_value = MagicMock(data=None)

        await _reconcile_session(
            db,
            session_id="nonexistent",
            question_id="q-1",
            llm_score=0.8,
            llm_model="m",
            eval_result=_make_eval_result(),
        )

        assert not db.called("update")

    @pytest.mark.asyncio
    async def test_question_not_in_answers(self):
        db = _db()
        answers = [{"question_id": "q-other", "raw_score": 0.5}]
        db.execute.return_value = MagicMock(data={"answers": answers})

        await _reconcile_session(
            db,
            session_id="sess-1",
            question_id="q-missing",
            llm_score=0.8,
            llm_model="m",
            eval_result=_make_eval_result(),
        )

        assert not db.called("update")

    @pytest.mark.asyncio
    async def test_answers_none_treated_as_empty(self):
        db = _db()
        db.execute.return_value = MagicMock(data={"answers": None})

        await _reconcile_session(
            db,
            session_id="sess-1",
            question_id="q-1",
            llm_score=0.8,
            llm_model="m",
            eval_result=_make_eval_result(),
        )

        assert not db.called("update")

    @pytest.mark.asyncio
    async def test_db_error_propagates(self):
        db = _db()
        db.execute.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            await _reconcile_session(
                db,
                session_id="sess-1",
                question_id="q-1",
                llm_score=0.8,
                llm_model="m",
                eval_result=_make_eval_result(),
            )


# ── 8. _reconcile_aura ──────────────────────────────────────────────────────


class TestReconcileAura:
    @pytest.mark.asyncio
    async def test_patches_when_score_matches_degraded(self):
        db = _db()
        db.execute.side_effect = [
            MagicMock(data={"competency_scores": {"communication": 0.4, "leadership": 0.7}}),
            MagicMock(data=[]),
        ]

        await _reconcile_aura(
            db,
            session_id="sess-1",
            volunteer_id="vol-1",
            competency_slug="communication",
            degraded_score=0.4,
            llm_score=0.85,
        )

        assert db.called("rpc")
        rpc_args = db.last_args("rpc")[0]
        assert rpc_args[0] == "upsert_aura_score"
        assert rpc_args[1] == {
            "p_volunteer_id": "vol-1",
            "p_competency_scores": {"communication": 0.85, "leadership": 0.7},
        }

    @pytest.mark.asyncio
    async def test_skips_when_no_aura_row(self):
        db = _db()
        db.execute.return_value = MagicMock(data=None)

        await _reconcile_aura(
            db,
            session_id="sess-1",
            volunteer_id="vol-1",
            competency_slug="communication",
            degraded_score=0.4,
            llm_score=0.85,
        )

        assert not db.called("rpc")

    @pytest.mark.asyncio
    async def test_skips_when_slug_missing(self):
        db = _db()
        db.execute.return_value = MagicMock(
            data={"competency_scores": {"leadership": 0.7}}
        )

        await _reconcile_aura(
            db,
            session_id="sess-1",
            volunteer_id="vol-1",
            competency_slug="communication",
            degraded_score=0.4,
            llm_score=0.85,
        )

        assert not db.called("rpc")

    @pytest.mark.asyncio
    async def test_skips_when_score_diverged(self):
        db = _db()
        db.execute.return_value = MagicMock(
            data={"competency_scores": {"communication": 0.8}}
        )

        await _reconcile_aura(
            db,
            session_id="sess-1",
            volunteer_id="vol-1",
            competency_slug="communication",
            degraded_score=0.4,
            llm_score=0.85,
        )

        assert not db.called("rpc")

    @pytest.mark.asyncio
    async def test_patches_within_tolerance(self):
        db = _db()
        db.execute.side_effect = [
            MagicMock(data={"competency_scores": {"communication": 0.405}}),
            MagicMock(data=[]),
        ]

        await _reconcile_aura(
            db,
            session_id="sess-1",
            volunteer_id="vol-1",
            competency_slug="communication",
            degraded_score=0.4,
            llm_score=0.85,
        )

        assert db.called("rpc")

    @pytest.mark.asyncio
    async def test_skips_at_tolerance_boundary(self):
        """0.42 - 0.4 = 0.02 > 0.01 tolerance, should skip."""
        db = _db()
        db.execute.return_value = MagicMock(
            data={"competency_scores": {"communication": 0.42}}
        )

        await _reconcile_aura(
            db,
            session_id="sess-1",
            volunteer_id="vol-1",
            competency_slug="communication",
            degraded_score=0.4,
            llm_score=0.85,
        )

        assert not db.called("rpc")

    @pytest.mark.asyncio
    async def test_competency_scores_none_treated_as_empty(self):
        db = _db()
        db.execute.return_value = MagicMock(data={"competency_scores": None})

        await _reconcile_aura(
            db,
            session_id="sess-1",
            volunteer_id="vol-1",
            competency_slug="communication",
            degraded_score=0.4,
            llm_score=0.85,
        )

        assert not db.called("rpc")

    @pytest.mark.asyncio
    async def test_db_error_propagates(self):
        db = _db()
        db.execute.side_effect = Exception("RPC down")

        with pytest.raises(Exception, match="RPC down"):
            await _reconcile_aura(
                db,
                session_id="sess-1",
                volunteer_id="vol-1",
                competency_slug="communication",
                degraded_score=0.4,
                llm_score=0.85,
            )

    @pytest.mark.asyncio
    async def test_llm_score_rounded_to_2_decimals(self):
        db = _db()
        db.execute.side_effect = [
            MagicMock(data={"competency_scores": {"communication": 0.4}}),
            MagicMock(data=[]),
        ]

        await _reconcile_aura(
            db,
            session_id="sess-1",
            volunteer_id="vol-1",
            competency_slug="communication",
            degraded_score=0.4,
            llm_score=0.8567,
        )

        rpc_args = db.last_args("rpc")[0]
        assert rpc_args[1]["p_competency_scores"]["communication"] == 0.86
