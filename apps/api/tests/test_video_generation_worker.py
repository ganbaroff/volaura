"""Unit tests for app.services.video_generation_worker."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.video_generation_worker import (
    MAX_RETRIES,
    POLL_INTERVAL_S,
    STALE_TIMEOUT_S,
    _fetch_next_job,
    _lock_job,
    _mark_completed,
    _mark_failed,
    _process_job,
    _recover_stale_jobs,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_db():
    """Build mock AsyncClient with synchronous schema().table() chain.

    Supabase fluent API: db.schema("x").table("y").update({}).eq("k","v").execute()
    Only .execute() is awaited. Everything else is synchronous chaining.
    """
    db = MagicMock()
    schema_mock = MagicMock()
    db.schema.return_value = schema_mock
    table_mock = MagicMock()
    schema_mock.table.return_value = table_mock
    return db, table_mock


def _wire_chain(start, methods: list[str], result_data):
    """Wire synchronous method chain ending with async .execute()."""
    current = start
    for name in methods:
        next_m = MagicMock()
        getattr(current, name).return_value = next_m
        current = next_m
    result = MagicMock()
    result.data = result_data
    current.execute = AsyncMock(return_value=result)
    return current


def _make_process_db():
    """Build db mock for _process_job that routes schema() calls to separate tables.

    _process_job calls db.schema("brandedby") multiple times:
      1st: .table("ai_twins") for twin lookup
      2nd+: .table("generations") for _mark_completed/_mark_failed
    """
    db = MagicMock()
    twin_table = MagicMock()
    gen_table = MagicMock()
    call_count = {"n": 0}

    def schema_side_effect(name):
        call_count["n"] += 1
        s = MagicMock()
        if call_count["n"] == 1:
            s.table.return_value = twin_table
        else:
            s.table.return_value = gen_table
        return s

    db.schema.side_effect = schema_side_effect
    return db, twin_table, gen_table


def _wire_twin_lookup(twin_table, twin_data):
    """Wire select().eq().single().execute() on twin_table."""
    _wire_chain(twin_table, ["select", "eq", "single"], twin_data)


def _wire_gen_update(gen_table, result_data=None):
    """Wire update().eq().execute() on gen_table for _mark_completed/_mark_failed."""
    if result_data is None:
        result_data = [{"id": "gen-1"}]
    _wire_chain(gen_table, ["update", "eq"], result_data)


# ── Constants ────────────────────────────────────────────────────────────────


class TestConstants:
    def test_poll_interval(self):
        assert POLL_INTERVAL_S == 15.0

    def test_stale_timeout(self):
        assert STALE_TIMEOUT_S == 600.0

    def test_max_retries(self):
        assert MAX_RETRIES == 2


# ── _recover_stale_jobs ─────────────────────────────────────────────────────


class TestRecoverStaleJobs:
    @pytest.mark.asyncio
    async def test_recovers_stale_items(self):
        db, table = _make_db()
        _wire_chain(table, ["update", "eq", "lt"], [{"id": "g1"}, {"id": "g2"}])

        await _recover_stale_jobs(db)

        db.schema.assert_called_with("brandedby")
        table.update.assert_called_once()
        payload = table.update.call_args[0][0]
        assert payload["status"] == "queued"
        assert payload["processing_started_at"] is None

    @pytest.mark.asyncio
    async def test_no_stale_items(self):
        db, table = _make_db()
        last = _wire_chain(table, ["update", "eq", "lt"], [])

        await _recover_stale_jobs(db)
        last.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_exception_swallowed(self):
        db, table = _make_db()
        table.update.side_effect = RuntimeError("db down")

        await _recover_stale_jobs(db)


# ── _fetch_next_job ──────────────────────────────────────────────────────────


class TestFetchNextJob:
    @pytest.mark.asyncio
    async def test_returns_job(self):
        db, table = _make_db()
        job = {"id": "gen-1", "twin_id": "tw-1", "retry_count": 0}
        _wire_chain(table, ["select", "eq", "order", "order", "limit"], [job])

        got = await _fetch_next_job(db)
        assert got == job

    @pytest.mark.asyncio
    async def test_returns_none_on_empty(self):
        db, table = _make_db()
        _wire_chain(table, ["select", "eq", "order", "order", "limit"], [])

        got = await _fetch_next_job(db)
        assert got is None

    @pytest.mark.asyncio
    async def test_returns_none_when_retry_exhausted(self):
        db, table = _make_db()
        job = {"id": "gen-1", "twin_id": "tw-1", "retry_count": MAX_RETRIES}
        _wire_chain(table, ["select", "eq", "order", "order", "limit"], [job])

        got = await _fetch_next_job(db)
        assert got is None

    @pytest.mark.asyncio
    async def test_returns_none_when_retry_count_none(self):
        db, table = _make_db()
        job = {"id": "gen-1", "twin_id": "tw-1", "retry_count": None}
        _wire_chain(table, ["select", "eq", "order", "order", "limit"], [job])

        got = await _fetch_next_job(db)
        assert got == job

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        db, table = _make_db()
        table.select.side_effect = RuntimeError("boom")

        got = await _fetch_next_job(db)
        assert got is None


# ── _lock_job ────────────────────────────────────────────────────────────────


class TestLockJob:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        db, table = _make_db()
        _wire_chain(table, ["update", "eq", "eq"], [{"id": "gen-1"}])

        assert await _lock_job(db, "gen-1") is True
        payload = table.update.call_args[0][0]
        assert payload["status"] == "processing"
        assert "processing_started_at" in payload

    @pytest.mark.asyncio
    async def test_returns_false_when_no_data(self):
        db, table = _make_db()
        _wire_chain(table, ["update", "eq", "eq"], [])

        assert await _lock_job(db, "gen-1") is False

    @pytest.mark.asyncio
    async def test_returns_false_on_none_data(self):
        db, table = _make_db()
        _wire_chain(table, ["update", "eq", "eq"], None)

        assert await _lock_job(db, "gen-1") is False

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self):
        db, table = _make_db()
        table.update.side_effect = RuntimeError("conflict")

        assert await _lock_job(db, "gen-1") is False


# ── _mark_completed ──────────────────────────────────────────────────────────


class TestMarkCompleted:
    @pytest.mark.asyncio
    async def test_sets_correct_fields(self):
        db, table = _make_db()
        _wire_chain(table, ["update", "eq"], [{"id": "gen-1"}])

        await _mark_completed(db, "gen-1", "https://cdn.example.com/video.mp4")

        payload = table.update.call_args[0][0]
        assert payload["status"] == "completed"
        assert payload["output_url"] == "https://cdn.example.com/video.mp4"
        assert "completed_at" in payload

    @pytest.mark.asyncio
    async def test_exception_swallowed(self):
        db, table = _make_db()
        table.update.side_effect = RuntimeError("db error")

        await _mark_completed(db, "gen-1", "https://cdn.example.com/v.mp4")


# ── _mark_failed ─────────────────────────────────────────────────────────────


class TestMarkFailed:
    @pytest.mark.asyncio
    async def test_requeues_when_retries_remaining(self):
        db, table = _make_db()
        _wire_chain(table, ["update", "eq"], [{"id": "gen-1"}])

        await _mark_failed(db, "gen-1", "transient error", retry_count=0)

        payload = table.update.call_args[0][0]
        assert payload["status"] == "queued"
        assert payload["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_permanent_fail_when_exhausted(self):
        db, table = _make_db()
        _wire_chain(table, ["update", "eq"], [{"id": "gen-1"}])

        await _mark_failed(db, "gen-1", "fatal error", retry_count=MAX_RETRIES - 1)

        payload = table.update.call_args[0][0]
        assert payload["status"] == "failed"
        assert payload["retry_count"] == MAX_RETRIES

    @pytest.mark.asyncio
    async def test_error_truncated_to_500(self):
        db, table = _make_db()
        _wire_chain(table, ["update", "eq"], [{"id": "gen-1"}])

        long_error = "x" * 1000
        await _mark_failed(db, "gen-1", long_error, retry_count=0)

        payload = table.update.call_args[0][0]
        assert len(payload["error_message"]) == 500

    @pytest.mark.asyncio
    async def test_exception_swallowed(self):
        db, table = _make_db()
        table.update.side_effect = RuntimeError("db down")

        await _mark_failed(db, "gen-1", "err", retry_count=0)


# ── _process_job ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _mock_swarm_module():
    """Inject fake swarm.atlas_video_skill into sys.modules — module doesn't exist on disk."""
    mock_module = MagicMock()
    mock_module.AtlasVideoSkill = MagicMock()
    sys.modules.setdefault("swarm", MagicMock())
    sys.modules["swarm.atlas_video_skill"] = mock_module
    yield mock_module
    sys.modules.pop("swarm.atlas_video_skill", None)


class TestProcessJob:
    BASE_JOB = {
        "id": "gen-1",
        "twin_id": "tw-1",
        "input_text": "Hello world script.",
        "retry_count": 0,
    }

    @pytest.mark.asyncio
    @patch("app.services.video_generation_worker.settings")
    async def test_happy_path(self, mock_settings):
        mock_settings.fal_api_key = "fal-key-123"
        db, twin_table, gen_table = _make_process_db()
        _wire_twin_lookup(twin_table, {"photo_url": "https://img.com/face.jpg", "personality_prompt": ""})
        _wire_gen_update(gen_table)

        with patch("swarm.atlas_video_skill.AtlasVideoSkill") as MockSkill:
            instance = MagicMock()
            instance.generate = AsyncMock(return_value="https://cdn.com/video.mp4")
            MockSkill.return_value = instance

            await _process_job(db, self.BASE_JOB)

            MockSkill.assert_called_once_with(fal_api_key="fal-key-123")
            instance.generate.assert_awaited_once_with(
                photo_url="https://img.com/face.jpg",
                script="Hello world script.",
                generation_id="gen-1",
            )

    @pytest.mark.asyncio
    async def test_twin_not_found_marks_failed(self):
        db, twin_table, gen_table = _make_process_db()
        twin_table.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            side_effect=RuntimeError("not found")
        )
        _wire_gen_update(gen_table)

        await _process_job(db, self.BASE_JOB)

        payload = gen_table.update.call_args[0][0]
        assert "Twin lookup failed" in payload["error_message"]

    @pytest.mark.asyncio
    async def test_no_photo_url_marks_failed(self):
        db, twin_table, gen_table = _make_process_db()
        _wire_twin_lookup(twin_table, {"photo_url": "", "personality_prompt": "Some persona."})
        _wire_gen_update(gen_table)

        await _process_job(db, self.BASE_JOB)

        payload = gen_table.update.call_args[0][0]
        assert "no photo_url" in payload["error_message"]

    @pytest.mark.asyncio
    async def test_none_photo_url_marks_failed(self):
        db, twin_table, gen_table = _make_process_db()
        _wire_twin_lookup(twin_table, {"photo_url": None, "personality_prompt": "x"})
        _wire_gen_update(gen_table)

        await _process_job(db, self.BASE_JOB)

        payload = gen_table.update.call_args[0][0]
        assert "no photo_url" in payload["error_message"]

    @pytest.mark.asyncio
    @patch("app.services.video_generation_worker.settings")
    async def test_personality_fallback_uses_first_two_sentences(self, mock_settings):
        mock_settings.fal_api_key = "fal-key"
        db, twin_table, gen_table = _make_process_db()
        personality = "I am an AI twin. I help people learn. I also tell jokes."
        _wire_twin_lookup(twin_table, {"photo_url": "https://img.com/face.jpg", "personality_prompt": personality})
        _wire_gen_update(gen_table)

        job_no_script = {**self.BASE_JOB, "input_text": ""}

        with patch("swarm.atlas_video_skill.AtlasVideoSkill") as MockSkill:
            instance = MagicMock()
            instance.generate = AsyncMock(return_value="https://cdn.com/v.mp4")
            MockSkill.return_value = instance

            await _process_job(db, job_no_script)

            expected_script = "I am an AI twin. I help people learn."
            actual_script = instance.generate.call_args[1]["script"]
            assert actual_script == expected_script

    @pytest.mark.asyncio
    async def test_no_script_no_personality_marks_failed(self):
        db, twin_table, gen_table = _make_process_db()
        _wire_twin_lookup(twin_table, {"photo_url": "https://img.com/face.jpg", "personality_prompt": ""})
        _wire_gen_update(gen_table)

        job_no_script = {**self.BASE_JOB, "input_text": ""}
        await _process_job(db, job_no_script)

        payload = gen_table.update.call_args[0][0]
        assert "No script or personality" in payload["error_message"]

    @pytest.mark.asyncio
    @patch("app.services.video_generation_worker.settings")
    async def test_video_skill_raises_marks_failed(self, mock_settings):
        mock_settings.fal_api_key = "fal-key"
        db, twin_table, gen_table = _make_process_db()
        _wire_twin_lookup(twin_table, {"photo_url": "https://img.com/face.jpg", "personality_prompt": ""})
        _wire_gen_update(gen_table)

        with patch("swarm.atlas_video_skill.AtlasVideoSkill") as MockSkill:
            instance = MagicMock()
            instance.generate = AsyncMock(side_effect=RuntimeError("fal.ai 500"))
            MockSkill.return_value = instance

            await _process_job(db, self.BASE_JOB)

            payload = gen_table.update.call_args[0][0]
            assert "fal.ai 500" in payload["error_message"]

    @pytest.mark.asyncio
    @patch("app.services.video_generation_worker.settings")
    async def test_none_input_text_treated_as_empty(self, mock_settings):
        mock_settings.fal_api_key = "fal-key"
        db, twin_table, gen_table = _make_process_db()
        _wire_twin_lookup(twin_table, {"photo_url": "https://img.com/face.jpg", "personality_prompt": ""})
        _wire_gen_update(gen_table)

        job_none_text = {**self.BASE_JOB, "input_text": None}
        await _process_job(db, job_none_text)

        payload = gen_table.update.call_args[0][0]
        assert "No script or personality" in payload["error_message"]
