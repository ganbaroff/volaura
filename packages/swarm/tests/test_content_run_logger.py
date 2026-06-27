"""Tests for content_run_logger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.swarm.content_run_logger import ContentRunLogger, new_run_id


@pytest.fixture
def logger(tmp_path: Path) -> ContentRunLogger:
    return ContentRunLogger(
        run_id="test-run-001",
        piece_id="reaction-test",
        repo_root=tmp_path,
        dry_run=False,
    )


class TestContentRunLogger:
    def test_new_run_id_format(self):
        rid = new_run_id("reaction-2026-06-27-post2")
        assert "reaction-2026-06-27-post2" in rid
        assert "T" in rid

    def test_writes_manifest_and_steps_jsonl(self, logger: ContentRunLogger, tmp_path: Path):
        rec = logger.begin_step("script", "echo hello")
        logger.finish_step(rec, exit_code=0, message="ok")

        run_dir = tmp_path / "memory" / "swarm" / "content-runs" / "test-run-001"
        assert (run_dir / "manifest.json").is_file()
        assert (run_dir / "steps.jsonl").is_file()

        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["run_id"] == "test-run-001"
        assert manifest["piece_id"] == "reaction-test"
        assert len(manifest["steps"]) == 1
        assert manifest["steps"][0]["step_id"] == "script"
        assert manifest["steps"][0]["status"] == "success"
        assert manifest["steps"][0]["exit_code"] == 0

    def test_sha256_on_output_file(self, logger: ContentRunLogger, tmp_path: Path):
        out = tmp_path / "sample.txt"
        out.write_text("phase0 proof", encoding="utf-8")

        rec = logger.begin_step("tts", "tts synth")
        logger.finish_step(rec, exit_code=0, output_path=out)

        manifest = json.loads(
            (logger.run_dir / "manifest.json").read_text(encoding="utf-8"),
        )
        assert manifest["steps"][0]["sha256"]
        assert len(manifest["steps"][0]["sha256"]) == 64

    def test_write_proof(self, logger: ContentRunLogger):
        path = logger.write_proof([("Summary", "All steps passed.")])
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "reaction-test" in text
        assert "## Summary" in text

    def test_note_skip(self, logger: ContentRunLogger):
        logger.note_skip("tts", "azure tts", "no API key")
        manifest = json.loads(
            (logger.run_dir / "manifest.json").read_text(encoding="utf-8"),
        )
        assert manifest["steps"][0]["status"] == "skipped"
        assert "no API key" in manifest["steps"][0]["message"]
