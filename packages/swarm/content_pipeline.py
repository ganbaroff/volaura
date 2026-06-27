"""
Phase 0 content pipeline — script → TTS → transcribe → render → deliver.

End-to-end proof for ReactionDuet compositions. Uses Orchestrator DAG pattern
with synchronous subprocess steps for Remotion transcribe/render.

Usage:
    python -m packages.swarm.content_pipeline --piece reaction-2026-06-27-post2
    python -m packages.swarm.content_pipeline --piece reaction-2026-06-27-post2 --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

from dotenv import load_dotenv
from loguru import logger

from packages.swarm.content_prompts import ContentPiece, get_piece
from packages.swarm.content_run_logger import ContentRunLogger, new_run_id
from packages.swarm.orchestrator import AgentTask, Orchestrator

# Repo root (packages/swarm → packages → repo)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REMOTION_PKG = REPO_ROOT / "packages" / "remotion"
VOICEOVER_PUBLIC = REMOTION_PKG / "public" / "voiceovers"


@dataclass
class PipelineContext:
    piece: ContentPiece
    run_logger: ContentRunLogger
    dry_run: bool
    run_dir: Path
    script_path: Path | None = None
    audio_path: Path | None = None
    captions_path: Path | None = None
    video_path: Path | None = None
    props_path: Path | None = None
    deliver_note: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)


def _default_props_for_piece(piece: ContentPiece) -> dict[str, Any]:
    """Build Remotion inputProps for ReactionDuet from piece defaults."""
    return {
        "data": {
            "brandHandle": "@volaura.io",
            "accentProduct": "mindshift",
            "sourceImage": "standin/source-placeholder.png",
            "avatarImage": "standin/avatar-placeholder.png",
            "disclosure": "AI-generated · reaksiya",
            "cta": {"line": "Link in bio", "brand": "volaura.io"},
            "audio": f"voiceovers/{piece.piece_id}.wav",
            "captions": None,
        },
    }


def _load_captions_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_subprocess(
    ctx: PipelineContext,
    step_id: str,
    cmd: list[str],
    *,
    cwd: Path | None = None,
    output_path: Path | None = None,
) -> int:
    command_str = " ".join(cmd)
    rec = ctx.run_logger.begin_step(step_id, command_str)

    if ctx.dry_run:
        ctx.run_logger.finish_step(
            rec,
            exit_code=0,
            message="dry-run: skipped execution",
            skipped=True,
        )
        return 0

    # On Windows, pnpm/npx are .cmd shims that CreateProcess cannot launch
    # directly (raises [WinError 2]); route through the command interpreter.
    run_cmd = cmd
    if sys.platform == "win32":
        run_cmd = [os.environ.get("COMSPEC", "cmd.exe"), "/c", *cmd]

    try:
        result = subprocess.run(
            run_cmd,
            cwd=str(cwd or REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            logger.debug("{step} stdout: {out}", step=step_id, out=result.stdout[-500:])
        if result.returncode != 0 and result.stderr:
            logger.error("{step} stderr: {err}", step=step_id, err=result.stderr[-800:])

        ctx.run_logger.finish_step(
            rec,
            exit_code=result.returncode,
            output_path=output_path if result.returncode == 0 else None,
            message=result.stderr.strip()[:300] if result.returncode != 0 else "ok",
        )
        return result.returncode
    except OSError as e:
        ctx.run_logger.finish_step(rec, exit_code=1, message=str(e))
        return 1


async def step_script(ctx: PipelineContext) -> dict[str, Any]:
    """Write TTS script text to run directory."""
    ctx.script_path = ctx.run_dir / "script.txt"
    cmd = f"write script for {ctx.piece.piece_id}"
    rec = ctx.run_logger.begin_step("script", cmd)

    if ctx.dry_run:
        ctx.run_logger.finish_step(
            rec, exit_code=0, message="dry-run", skipped=True,
        )
        return {"script_path": str(ctx.script_path), "chars": len(ctx.piece.script)}

    ctx.script_path.write_text(ctx.piece.script, encoding="utf-8")
    ctx.run_logger.finish_step(
        rec, exit_code=0, output_path=ctx.script_path, message="ok",
    )
    return {"script_path": str(ctx.script_path), "chars": len(ctx.piece.script)}


async def step_tts(ctx: PipelineContext) -> dict[str, Any]:
    """Synthesize voice-over WAV via packages.swarm.tts."""
    ctx.audio_path = ctx.run_dir / f"{ctx.piece.piece_id}.wav"
    public_audio = VOICEOVER_PUBLIC / f"{ctx.piece.piece_id}.wav"
    cmd = [
        sys.executable,
        "-m",
        "packages.swarm.tts",
        "--lang",
        ctx.piece.lang,
        "--text-file",
        str(ctx.script_path or ctx.run_dir / "script.txt"),
        "--out",
        str(ctx.audio_path),
    ]
    rec = ctx.run_logger.begin_step("tts", " ".join(cmd))

    if ctx.dry_run:
        ctx.run_logger.finish_step(rec, exit_code=0, message="dry-run", skipped=True)
        return {"audio_path": str(ctx.audio_path), "skipped": True}

    if not ctx.script_path or not ctx.script_path.is_file():
        ctx.run_logger.finish_step(rec, exit_code=1, message="script.txt missing")
        return {"error": "script missing"}

    # AZ no longer hard-blocks on AZURE_SPEECH_KEY: synthesize() falls back to
    # edge-tts (the same az-AZ-BabekNeural voice, free) when the key is absent.
    try:
        from packages.swarm.tts import synthesize

        result = synthesize(
            text=ctx.script_path.read_text(encoding="utf-8"),
            lang=ctx.piece.lang,
            out_path=ctx.audio_path,
        )
    except Exception as e:
        ctx.run_logger.finish_step(rec, exit_code=1, message=str(e)[:300])
        return {"error": str(e)}

    VOICEOVER_PUBLIC.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ctx.audio_path, public_audio)

    ctx.run_logger.finish_step(
        rec,
        exit_code=0,
        output_path=ctx.audio_path,
        message=f"{result.provider}/{result.voice_id}",
    )
    return {
        "audio_path": str(ctx.audio_path),
        "public_path": str(public_audio),
        "bytes": result.bytes_written,
    }


async def step_transcribe(ctx: PipelineContext) -> dict[str, Any]:
    """Run whisper.cpp via Remotion transcribe script."""
    ctx.captions_path = ctx.run_dir / f"{ctx.piece.piece_id}.captions.json"

    if not ctx.audio_path or not ctx.audio_path.is_file():
        reason = "no audio — transcribe skipped"
        ctx.run_logger.note_skip("transcribe", "pnpm transcribe", reason)
        ctx.artifacts["transcribe_skip_reason"] = reason
        return {"skipped": True, "reason": reason}

    lang_flag = (
        f"--language={ctx.piece.whisper_language}"
        if ctx.piece.whisper_language
        else ""
    )
    cmd = [
        "pnpm",
        "--filter",
        "@volaura/remotion",
        "transcribe",
        str(ctx.audio_path),
        f"--out={ctx.captions_path}",
    ]
    if lang_flag:
        cmd.append(lang_flag)

    code = _run_subprocess(ctx, "transcribe", cmd, output_path=ctx.captions_path)
    if code != 0:
        return {"error": "transcribe failed", "exit_code": code}
    return {"captions_path": str(ctx.captions_path)}


async def step_render(ctx: PipelineContext) -> dict[str, Any]:
    """Render ReactionDuet MP4 via Remotion."""
    ctx.video_path = ctx.run_dir / f"{ctx.piece.piece_id}.mp4"
    ctx.props_path = ctx.run_dir / "props.json"

    if not ctx.audio_path or not ctx.audio_path.is_file():
        reason = "no audio — render skipped"
        ctx.run_logger.note_skip("render", "pnpm render ReactionDuet", reason)
        ctx.artifacts["render_skip_reason"] = reason
        return {"skipped": True, "reason": reason}

    props = _default_props_for_piece(ctx.piece)
    if ctx.captions_path and ctx.captions_path.is_file():
        props["data"]["captions"] = _load_captions_json(ctx.captions_path)

    if not ctx.dry_run:
        ctx.props_path.write_text(
            json.dumps(props, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    cmd = [
        "pnpm",
        "--filter",
        "@volaura/remotion",
        "render",
        "--",
        ctx.piece.composition_id,
        str(ctx.video_path.resolve()),
        f"--props={ctx.props_path.resolve()}",
    ]
    code = _run_subprocess(ctx, "render", cmd, output_path=ctx.video_path)
    if code != 0:
        return {"error": "render failed", "exit_code": code}
    return {"video_path": str(ctx.video_path)}


async def step_deliver(ctx: PipelineContext) -> dict[str, Any]:
    """Deliver preview to CEO via Telegram when credentials present."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("ATLAS_CEO_CHAT_ID") or os.environ.get(
        "TELEGRAM_CEO_CHAT_ID", "",
    )
    cmd = "telegram deliver"
    rec = ctx.run_logger.begin_step("deliver", cmd)

    if ctx.dry_run:
        ctx.run_logger.finish_step(rec, exit_code=0, message="dry-run", skipped=True)
        return {"skipped": True}

    if not bot_token or not chat_id:
        reason = "TELEGRAM_BOT_TOKEN or CEO chat id not set — deliver skipped"
        ctx.run_logger.finish_step(rec, exit_code=0, message=reason, skipped=True)
        ctx.deliver_note = reason
        return {"skipped": True, "reason": reason}

    if not ctx.video_path or not ctx.video_path.is_file():
        reason = "no MP4 to deliver"
        ctx.run_logger.finish_step(rec, exit_code=0, message=reason, skipped=True)
        ctx.deliver_note = reason
        return {"skipped": True, "reason": reason}

    try:
        from telegram import Bot

        bot = Bot(token=bot_token)
        caption = (
            f"🎬 Phase 0 proof — {ctx.piece.piece_id}\n"
            f"Run: {ctx.run_logger.run_id}"
        )
        with ctx.video_path.open("rb") as video_file:
            await bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=caption,
            )
        ctx.run_logger.finish_step(rec, exit_code=0, message="telegram sent")
        ctx.deliver_note = "delivered via Telegram"
        return {"delivered": True}
    except Exception as e:
        ctx.run_logger.finish_step(rec, exit_code=1, message=str(e)[:300])
        ctx.deliver_note = f"deliver failed: {e}"
        return {"error": str(e)}


STEP_ORDER = ["script", "tts", "transcribe", "render", "deliver"]

STEP_RUNNERS: dict[str, Callable[[PipelineContext], Awaitable[dict[str, Any]]]] = {
    "script": step_script,
    "tts": step_tts,
    "transcribe": step_transcribe,
    "render": step_render,
    "deliver": step_deliver,
}


async def pipeline_runner(agent_id: str, input_data: dict[str, Any]) -> dict[str, Any]:
    ctx: PipelineContext = input_data["ctx"]
    runner = STEP_RUNNERS.get(agent_id)
    if not runner:
        raise ValueError(f"Unknown pipeline step: {agent_id}")
    return await runner(ctx)


def _build_orchestrator(ctx: PipelineContext) -> Orchestrator:
    orch = Orchestrator(
        runner=pipeline_runner,
        run_id=ctx.run_logger.run_id,
    )
    prev: str | None = None
    for step_id in STEP_ORDER:
        depends = [prev] if prev else []
        orch.add_task(
            AgentTask(
                task_id=step_id,
                agent_id=step_id,
                input={"ctx": ctx},
                depends_on=depends,
            ),
        )
        prev = step_id
    return orch


def _proof_sections(ctx: PipelineContext, tasks: dict[str, AgentTask]) -> list[tuple[str, str]]:
    lines: list[str] = []
    for step_id in STEP_ORDER:
        t = tasks.get(step_id)
        if not t:
            continue
        # A step can "complete" (no exception) yet return {"error": ...}; treat
        # that as FAILED too, so the proof never shows a false OK.
        result_err = isinstance(t.result, dict) and t.result.get("error")
        status = "FAILED" if (t.error or result_err) else ("OK" if t.completed else "PENDING")
        lines.append(f"- **{step_id}**: {status}")
        if t.result:
            lines.append(f"  - result: `{json.dumps(t.result, ensure_ascii=False)[:200]}`")
        if t.error:
            lines.append(f"  - error: {t.error}")

    artifact_lines = [
        f"- script: `{ctx.script_path}`" if ctx.script_path else "- script: (none)",
        f"- audio: `{ctx.audio_path}`" if ctx.audio_path else "- audio: (none)",
        f"- captions: `{ctx.captions_path}`" if ctx.captions_path else "- captions: (none)",
        f"- video: `{ctx.video_path}`" if ctx.video_path else "- video: (none)",
    ]

    skips = []
    if ctx.artifacts.get("tts_skip_reason"):
        skips.append(f"- TTS: {ctx.artifacts['tts_skip_reason']}")
    if ctx.artifacts.get("transcribe_skip_reason"):
        skips.append(f"- Transcribe: {ctx.artifacts['transcribe_skip_reason']}")
    if ctx.deliver_note:
        skips.append(f"- Deliver: {ctx.deliver_note}")

    return [
        ("Pipeline steps", "\n".join(lines)),
        ("Artifacts", "\n".join(artifact_lines)),
        ("Skips / blockers", "\n".join(skips) if skips else "None"),
        (
            "Kill list (Phase 0)",
            "- No ComfyUI\n- No GPU VM\n- No HeyGen / Postiz / Veo (Phase 1+)",
        ),
    ]


async def run_phase0_pipeline(
    piece_id: str,
    *,
    dry_run: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    load_dotenv(REPO_ROOT / "apps" / "api" / ".env")

    piece = get_piece(piece_id)
    rid = run_id or new_run_id(piece_id)
    run_logger = ContentRunLogger(
        run_id=rid,
        piece_id=piece_id,
        repo_root=REPO_ROOT,
        dry_run=dry_run,
    )
    run_dir = run_logger.ensure_dir()

    ctx = PipelineContext(
        piece=piece,
        run_logger=run_logger,
        dry_run=dry_run,
        run_dir=run_dir,
    )

    orch = _build_orchestrator(ctx)
    tasks = await orch.run_all(timeout=3600)

    proof_path = run_logger.write_proof(_proof_sections(ctx, tasks))
    logger.info("Phase 0 pipeline complete → {proof}", proof=str(proof_path))

    return {
        "run_id": rid,
        "run_dir": str(run_dir),
        "proof_path": str(proof_path),
        "tasks": {k: {"completed": v.completed, "error": v.error} for k, v in tasks.items()},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VOLAURA Phase 0 content pipeline")
    parser.add_argument(
        "--piece",
        required=True,
        help="Piece id from content_prompts.PIECE_REGISTRY",
    )
    parser.add_argument("--dry-run", action="store_true", help="Log steps without executing")
    args = parser.parse_args(argv)

    try:
        result = asyncio.run(
            run_phase0_pipeline(args.piece, dry_run=args.dry_run),
        )
    except KeyError as e:
        logger.error("{err}", err=str(e))
        return 1
    except Exception as e:
        logger.error("Pipeline failed: {err}", err=str(e))
        return 1

    logger.info("Run {id} → {dir}", id=result["run_id"], dir=result["run_dir"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
