"""Phase 0 content pipeline tests — DAG order, dry-run, manifest schema."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from packages.swarm.content_pipeline import (
    STEP_ORDER,
    PipelineContext,
    _build_orchestrator,
    run_phase0_pipeline,
    step_script,
)
from packages.swarm.content_prompts import get_piece
from packages.swarm.content_run_logger import ContentRunLogger


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    (tmp_path / "apps" / "api").mkdir(parents=True)
    (tmp_path / "packages" / "remotion" / "public" / "voiceovers").mkdir(
        parents=True,
    )
    return tmp_path


class TestPipelineDAG:
    def test_step_order(self):
        assert STEP_ORDER == ["script", "tts", "transcribe", "render", "deliver"]

    def test_orchestrator_dependencies_chain(self, tmp_repo: Path):
        piece = get_piece("reaction-2026-06-27-post2")
        logger = ContentRunLogger(
            run_id="dag-test",
            piece_id=piece.piece_id,
            repo_root=tmp_repo,
        )
        run_dir = logger.ensure_dir()
        ctx = PipelineContext(
            piece=piece,
            run_logger=logger,
            dry_run=True,
            run_dir=run_dir,
        )
        orch = _build_orchestrator(ctx)

        assert list(orch.tasks.keys()) == STEP_ORDER
        assert orch.tasks["script"].depends_on == []
        assert orch.tasks["tts"].depends_on == ["script"]
        assert orch.tasks["transcribe"].depends_on == ["tts"]
        assert orch.tasks["render"].depends_on == ["transcribe"]
        assert orch.tasks["deliver"].depends_on == ["render"]


class TestDryRun:
    @pytest.mark.asyncio
    async def test_dry_run_writes_manifest_and_proof(self, tmp_repo: Path):
        with patch("packages.swarm.content_pipeline.REPO_ROOT", tmp_repo):
            result = await run_phase0_pipeline(
                "reaction-2026-06-27-post2",
                dry_run=True,
                run_id="dry-run-test",
            )

        run_dir = Path(result["run_dir"])
        assert (run_dir / "manifest.json").is_file()
        assert (run_dir / "PROOF.md").is_file()
        assert (run_dir / "steps.jsonl").is_file()

        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["dry_run"] is True
        assert manifest["piece_id"] == "reaction-2026-06-27-post2"
        assert len(manifest["steps"]) == len(STEP_ORDER)
        assert all(s["status"] == "skipped" for s in manifest["steps"])


class TestManifestSchema:
    @pytest.mark.asyncio
    async def test_script_step_writes_file(self, tmp_repo: Path):
        piece = get_piece("reaction-2026-06-27-post2")
        logger = ContentRunLogger(
            run_id="script-test",
            piece_id=piece.piece_id,
            repo_root=tmp_repo,
        )
        run_dir = logger.ensure_dir()
        ctx = PipelineContext(
            piece=piece,
            run_logger=logger,
            dry_run=False,
            run_dir=run_dir,
        )
        out = await step_script(ctx)
        assert ctx.script_path and ctx.script_path.is_file()
        assert out["chars"] > 0
        assert "44 süni intellekt" in ctx.script_path.read_text(encoding="utf-8")


class TestSubprocessMock:
    @pytest.mark.asyncio
    async def test_tts_skipped_without_azure_key(self, tmp_repo: Path, monkeypatch):
        monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
        monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)

        piece = get_piece("reaction-2026-06-27-post2")
        logger = ContentRunLogger(
            run_id="tts-skip",
            piece_id=piece.piece_id,
            repo_root=tmp_repo,
        )
        run_dir = logger.ensure_dir()
        ctx = PipelineContext(
            piece=piece,
            run_logger=logger,
            dry_run=False,
            run_dir=run_dir,
        )
        await step_script(ctx)

        with patch("packages.swarm.content_pipeline.REPO_ROOT", tmp_repo):
            from packages.swarm.content_pipeline import step_tts

            result = await step_tts(ctx)

        assert result.get("skipped") is True
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        tts_step = next(s for s in manifest["steps"] if s["step_id"] == "tts")
        assert tts_step["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_subprocess_render_called_with_mock(self, tmp_repo: Path, monkeypatch):
        with patch("packages.swarm.content_pipeline._run_subprocess") as mock_sub:
            mock_sub.return_value = 0

            piece = get_piece("reaction-2026-06-27-post2")
            logger = ContentRunLogger(
                run_id="render-mock",
                piece_id=piece.piece_id,
                repo_root=tmp_repo,
            )
            run_dir = logger.ensure_dir()
            ctx = PipelineContext(
                piece=piece,
                run_logger=logger,
                dry_run=False,
                run_dir=run_dir,
            )
            ctx.script_path = run_dir / "script.txt"
            ctx.script_path.write_text(piece.script, encoding="utf-8")
            ctx.audio_path = run_dir / f"{piece.piece_id}.wav"
            ctx.audio_path.write_bytes(b"RIFF" + b"\x00" * 40)
            ctx.captions_path = run_dir / f"{piece.piece_id}.captions.json"
            ctx.captions_path.write_text("[]", encoding="utf-8")

            with patch("packages.swarm.content_pipeline.REPO_ROOT", tmp_repo):
                from packages.swarm.content_pipeline import step_render

                await step_render(ctx)

            assert mock_sub.called
            args = mock_sub.call_args[0]
            assert args[1] == "render"
