from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


def _load_daemon_module():
    script_path = Path("C:/Projects/VOLAURA/scripts/atlas_swarm_daemon.py")
    spec = importlib.util.spec_from_file_location("atlas_swarm_daemon_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_select_bridgeable_proposals_filters_and_sorts(tmp_path, monkeypatch):
    daemon = _load_daemon_module()

    repo_root = tmp_path / "repo"
    proposals_dir = repo_root / "memory" / "swarm"
    proposals_dir.mkdir(parents=True)
    (proposals_dir / "proposals.json").write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "id": "zzz111",
                        "status": "approved",
                        "severity": "low",
                        "timestamp": "2026-05-07T10:00:00Z",
                        "title": "low approved",
                    },
                    {
                        "id": "aaa222",
                        "status": "accepted",
                        "severity": "medium",
                        "timestamp": "2026-05-07T09:00:00Z",
                        "title": "medium accepted",
                    },
                    {
                        "id": "dup333",
                        "status": "approved",
                        "severity": "medium",
                        "timestamp": "2026-05-07T08:00:00Z",
                        "title": "already queued",
                    },
                    {
                        "id": "skip444",
                        "status": "resolved",
                        "severity": "medium",
                        "timestamp": "2026-05-07T07:00:00Z",
                        "title": "resolved",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    pending = repo_root / "memory" / "atlas" / "work-queue" / "pending"
    done = repo_root / "memory" / "atlas" / "work-queue" / "done"
    failed = repo_root / "memory" / "atlas" / "work-queue" / "failed"
    in_progress = repo_root / "memory" / "atlas" / "work-queue" / "in-progress"
    for path in (pending, done, failed, in_progress):
        path.mkdir(parents=True, exist_ok=True)

    (pending / "proposal-dup333.md").write_text("existing", encoding="utf-8")

    monkeypatch.setattr(daemon, "REPO_ROOT", repo_root)
    monkeypatch.setattr(daemon, "PENDING", pending)
    monkeypatch.setattr(daemon, "DONE", done)
    monkeypatch.setattr(daemon, "FAILED", failed)
    monkeypatch.setattr(daemon, "IN_PROGRESS", in_progress)

    selected = daemon._select_bridgeable_proposals(limit=5)

    assert [proposal["id"] for proposal in selected] == ["aaa222", "zzz111"]


def test_run_swarm_coder_executor_marks_success(monkeypatch):
    daemon = _load_daemon_module()
    monkeypatch.setenv("ATLAS_CODE_MUTATIONS_ENABLED", "true")

    def fake_run(cmd, *args, **kwargs):
        joined = " ".join(str(c) for c in cmd[:4])
        if joined.startswith("git rev-parse --abbrev-ref"):
            return SimpleNamespace(returncode=0, stdout="codex/test\n", stderr="")
        if joined.startswith("git status --porcelain"):
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(
            returncode=0,
            stdout="...\n[6/6] Updating proposal status -> implemented\n",
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", fake_run)
    result = daemon._exec_run_swarm_coder(proposal_id="abc123")

    assert result["status"] == "ok"
    assert result["stage"] == "implemented"
    assert result["proposal_id"] == "abc123"


def test_archive_stale_in_progress_unblocks_daemon(tmp_path, monkeypatch):
    daemon = _load_daemon_module()

    repo_root = tmp_path / "repo"
    in_progress = repo_root / "memory" / "atlas" / "work-queue" / "in-progress"
    failed = repo_root / "memory" / "atlas" / "work-queue" / "failed"
    in_progress.mkdir(parents=True)
    failed.mkdir(parents=True)

    stale = in_progress / "old-task"
    stale.mkdir()
    monkeypatch.setattr(daemon, "REPO_ROOT", repo_root)
    monkeypatch.setattr(daemon, "IN_PROGRESS", in_progress)
    monkeypatch.setattr(daemon, "FAILED", failed)
    monkeypatch.setattr(daemon, "STALE_IN_PROGRESS_SECONDS", 10)
    monkeypatch.setattr(daemon, "log_event", lambda event: None)

    recovered = daemon._archive_stale_in_progress(now_ts=stale.stat().st_mtime + 11)

    assert recovered == 1
    assert not stale.exists()
    archived = failed / "old-task"
    assert archived.exists()
    result = json.loads((archived / "result.json").read_text(encoding="utf-8"))
    assert result["error"] == "stale_in_progress_recovered"


def test_run_swarm_coder_executor_marks_blocked(monkeypatch):
    daemon = _load_daemon_module()
    monkeypatch.setenv("ATLAS_CODE_MUTATIONS_ENABLED", "true")

    def fake_run(cmd, *args, **kwargs):
        joined = " ".join(str(c) for c in cmd[:4])
        if joined.startswith("git rev-parse --abbrev-ref"):
            return SimpleNamespace(returncode=0, stdout="codex/test\n", stderr="")
        if joined.startswith("git status --porcelain"):
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(
            returncode=1,
            stdout="[SWARM_CODER] BLOCKED by safety gate\n",
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", fake_run)
    result = daemon._exec_run_swarm_coder(proposal_id="abc123")

    assert result["status"] == "blocked"
    assert result["stage"] == "blocked"
