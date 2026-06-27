"""
Content run logger — audit trail for video/content pipeline executions.

Writes per-run artifacts under memory/swarm/content-runs/{run_id}/:
  - manifest.json  — run metadata + step summary
  - steps.jsonl    — one JSON line per step (duration, exit_code, sha256, command)
  - PROOF.md       — human-readable proof document for CEO review
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from loguru import logger

StepStatus = Literal["pending", "running", "success", "skipped", "failed"]


@dataclass
class StepRecord:
    step_id: str
    command: str
    status: StepStatus = "pending"
    duration_ms: int = 0
    exit_code: int | None = None
    sha256: str | None = None
    output_path: str | None = None
    message: str = ""
    started_at: str = ""
    finished_at: str = ""


@dataclass
class ContentRunLogger:
    run_id: str
    piece_id: str
    repo_root: Path
    dry_run: bool = False
    steps: list[StepRecord] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)
    _started: float = field(default_factory=time.monotonic)

    @property
    def run_dir(self) -> Path:
        return self.repo_root / "memory" / "swarm" / "content-runs" / self.run_id

    def ensure_dir(self) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        return self.run_dir

    def begin_step(self, step_id: str, command: str) -> StepRecord:
        rec = StepRecord(
            step_id=step_id,
            command=command,
            status="running",
            started_at=_utc_now(),
        )
        self.steps.append(rec)
        logger.info("Content run {run}: step {step} started", run=self.run_id, step=step_id)
        return rec

    def finish_step(
        self,
        rec: StepRecord,
        *,
        exit_code: int,
        output_path: Path | None = None,
        message: str = "",
        skipped: bool = False,
    ) -> None:
        rec.finished_at = _utc_now()
        rec.exit_code = exit_code
        rec.status = "skipped" if skipped else ("success" if exit_code == 0 else "failed")
        rec.message = message

        if rec.started_at:
            try:
                start = datetime.fromisoformat(rec.started_at.replace("Z", "+00:00"))
                end = datetime.fromisoformat(rec.finished_at.replace("Z", "+00:00"))
                rec.duration_ms = int((end - start).total_seconds() * 1000)
            except ValueError:
                rec.duration_ms = int((time.monotonic() - self._started) * 1000)

        if output_path and output_path.is_file():
            rec.output_path = str(output_path)
            rec.sha256 = _sha256_file(output_path)

        self._append_step_jsonl(rec)
        self._write_manifest()
        logger.info(
            "Content run {run}: step {step} {status} ({ms}ms)",
            run=self.run_id,
            step=rec.step_id,
            status=rec.status,
            ms=rec.duration_ms,
        )

    def note_skip(self, step_id: str, command: str, reason: str) -> None:
        rec = self.begin_step(step_id, command)
        self.finish_step(rec, exit_code=0, message=reason, skipped=True)

    def write_proof(self, sections: list[tuple[str, str]]) -> Path:
        """Write PROOF.md with provided markdown sections."""
        self.ensure_dir()
        proof_path = self.run_dir / "PROOF.md"
        header = (
            f"# Content Pipeline Proof — {self.piece_id}\n\n"
            f"- **Run ID:** `{self.run_id}`\n"
            f"- **Dry run:** {self.dry_run}\n"
            f"- **Generated:** {_utc_now()}\n\n"
        )
        body = "\n\n".join(f"## {title}\n\n{text}" for title, text in sections)
        proof_path.write_text(header + body + "\n", encoding="utf-8")
        self._write_manifest()
        return proof_path

    def _append_step_jsonl(self, rec: StepRecord) -> None:
        self.ensure_dir()
        line = json.dumps(asdict(rec), ensure_ascii=False)
        with (self.run_dir / "steps.jsonl").open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _write_manifest(self) -> None:
        self.ensure_dir()
        manifest = {
            "run_id": self.run_id,
            "piece_id": self.piece_id,
            "dry_run": self.dry_run,
            "updated_at": _utc_now(),
            "duration_ms": int((time.monotonic() - self._started) * 1000),
            "steps": [asdict(s) for s in self.steps],
            **self.extras,
        }
        (self.run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def new_run_id(piece_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe = piece_id.replace("/", "-")[:48]
    return f"{ts}-{safe}"
