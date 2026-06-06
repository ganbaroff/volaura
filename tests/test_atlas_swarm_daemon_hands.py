"""OpenManus Sprint 4 — daemon `run_hands_task` executor tests.

Goal: prove the executor (a) refuses by default, (b) refuses while a
manual operator session is active, (c) validates input, (d) honours
env-overrides for OpenManus root + venv python, (e) shapes the success
result with the sidecar's output.

Reference: codex-loop.md OpenManus Sprint 4 (forthcoming entry).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

from tests._paths import script_path as repo_script_path


def _load_daemon():
    script_path = repo_script_path("atlas_swarm_daemon.py")
    spec = importlib.util.spec_from_file_location("atlas_swarm_daemon_hands_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _wire_paths(daemon, tmp_path: Path) -> Path:
    """Move ATLAS_MEMORY + REPO_ROOT into tmp_path so the executor never
    touches the real repo. Returns the simulated repo root."""
    fake_repo = tmp_path / "repo"
    (fake_repo / "scripts").mkdir(parents=True)
    (fake_repo / "memory" / "atlas" / "runtime").mkdir(parents=True)
    (fake_repo / "memory" / "atlas" / "hands-runs").mkdir(parents=True)
    # Write a stub sidecar so the path-exists guard passes.
    (fake_repo / "scripts" / "run_openmanus_hands_task.py").write_text("# stub", encoding="utf-8")
    daemon.REPO_ROOT = fake_repo
    daemon.ATLAS_MEMORY = fake_repo / "memory" / "atlas"
    return fake_repo


def _fake_openmanus(tmp_path: Path) -> tuple[Path, Path]:
    om_root = tmp_path / "OpenManus"
    om_python = om_root / ".venv" / "Scripts" / "python.exe"
    om_python.parent.mkdir(parents=True, exist_ok=True)
    om_python.write_text("# stub", encoding="utf-8")
    return om_root, om_python


# ── gating tests ──────────────────────────────────────────────────────────────

def test_blocked_without_env_flag(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _wire_paths(daemon, tmp_path)
    monkeypatch.delenv("ATLAS_ALLOW_HANDS_TASKS", raising=False)
    out = daemon._exec_run_hands_task(instruction="anything", mode="browser_observe")
    assert out["status"] == "blocked"
    assert "ATLAS_ALLOW_HANDS_TASKS" in out["reason"]


def test_blocked_when_manual_session_lock_active(monkeypatch, tmp_path):
    daemon = _load_daemon()
    fake_repo = _wire_paths(daemon, tmp_path)
    monkeypatch.setenv("ATLAS_ALLOW_HANDS_TASKS", "true")

    lock = fake_repo / "memory" / "atlas" / "runtime" / "manual-session.lock"
    lock.write_text('{"reason":"operator-session"}', encoding="utf-8")

    out = daemon._exec_run_hands_task(instruction="anything", mode="browser_observe")
    assert out["status"] == "blocked"
    assert "manual_session_lock_active" in out["reason"]


# ── input validation tests ────────────────────────────────────────────────────

def test_missing_instruction_returns_error(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _wire_paths(daemon, tmp_path)
    monkeypatch.setenv("ATLAS_ALLOW_HANDS_TASKS", "true")
    out = daemon._exec_run_hands_task(instruction="", mode="browser_observe")
    assert out["status"] == "error"
    assert "instruction required" in out["error"]


def test_invalid_mode_returns_error(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _wire_paths(daemon, tmp_path)
    monkeypatch.setenv("ATLAS_ALLOW_HANDS_TASKS", "true")
    out = daemon._exec_run_hands_task(instruction="hi", mode="not-a-mode")
    assert out["status"] == "error"
    assert "invalid mode" in out["error"]


# ── openmanus path tests ─────────────────────────────────────────────────────

def test_missing_openmanus_python_returns_error(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _wire_paths(daemon, tmp_path)
    monkeypatch.setenv("ATLAS_ALLOW_HANDS_TASKS", "true")
    monkeypatch.setenv("OPENMANUS_ROOT", str(tmp_path / "no-such-dir"))
    monkeypatch.setenv("OPENMANUS_PYTHON", str(tmp_path / "no-such-python.exe"))
    out = daemon._exec_run_hands_task(instruction="hi", mode="browser_observe")
    assert out["status"] == "error"
    assert "OpenManus venv python not found" in out["error"]


# ── happy-path tests (subprocess mocked) ──────────────────────────────────────

def test_happy_path_writes_task_input_and_returns_summary(monkeypatch, tmp_path):
    daemon = _load_daemon()
    fake_repo = _wire_paths(daemon, tmp_path)
    om_root, om_python = _fake_openmanus(tmp_path)
    monkeypatch.setenv("ATLAS_ALLOW_HANDS_TASKS", "true")
    monkeypatch.setenv("OPENMANUS_ROOT", str(om_root))
    monkeypatch.setenv("OPENMANUS_PYTHON", str(om_python))

    captured: dict[str, Any] = {}

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        # Sidecar is supposed to write result.json into --out-dir. Simulate.
        out_dir_idx = cmd.index("--out-dir") + 1
        out_dir = Path(cmd[out_dir_idx])
        (out_dir / "result.json").write_text(json.dumps({
            "task_id": "t-fake-1",
            "status": "success",
            "elapsed_s": 12.34,
            "result_text": "Открыл example.com, title=Example Domain.",
        }), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "stdout-line", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    out = daemon._exec_run_hands_task(
        instruction="Open example.com and report title",
        mode="browser_observe",
        max_seconds=120,
        allowed_domains="example.com,foo.com",
        task_id="t-fake-1",
    )

    assert out["status"] == "success"
    assert out["task_id"] == "t-fake-1"
    assert out["exit_code"] == 0
    assert out["elapsed_s"] == 12.34
    assert "Открыл example.com" in out["result_text_tail"]

    runs_dir = fake_repo / "memory" / "atlas" / "hands-runs" / "t-fake-1"
    task_input = json.loads((runs_dir / "task.input.json").read_text(encoding="utf-8"))
    assert task_input["instruction"] == "Open example.com and report title"
    assert task_input["mode"] == "browser_observe"
    assert task_input["max_seconds"] == 120
    assert task_input["allowed_domains"] == ["example.com", "foo.com"]
    assert task_input["task_id"] == "t-fake-1"

    # Subprocess command shape
    assert str(om_python) in captured["cmd"]
    assert "--task" in captured["cmd"]
    assert "--openmanus-root" in captured["cmd"]
    assert "--out-dir" in captured["cmd"]


def test_max_seconds_capped_at_600(monkeypatch, tmp_path):
    daemon = _load_daemon()
    fake_repo = _wire_paths(daemon, tmp_path)
    om_root, om_python = _fake_openmanus(tmp_path)
    monkeypatch.setenv("ATLAS_ALLOW_HANDS_TASKS", "true")
    monkeypatch.setenv("OPENMANUS_ROOT", str(om_root))
    monkeypatch.setenv("OPENMANUS_PYTHON", str(om_python))

    def _fake_run(cmd, **kwargs):
        out_dir_idx = cmd.index("--out-dir") + 1
        out_dir = Path(cmd[out_dir_idx])
        (out_dir / "result.json").write_text(json.dumps({"status": "success", "elapsed_s": 1.0}), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    daemon._exec_run_hands_task(
        instruction="long task",
        mode="research",
        max_seconds=99999,
        task_id="t-cap",
    )
    runs_dir = fake_repo / "memory" / "atlas" / "hands-runs" / "t-cap"
    task_input = json.loads((runs_dir / "task.input.json").read_text(encoding="utf-8"))
    assert task_input["max_seconds"] == 600


def test_timeout_returns_timeout_status(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _wire_paths(daemon, tmp_path)
    om_root, om_python = _fake_openmanus(tmp_path)
    monkeypatch.setenv("ATLAS_ALLOW_HANDS_TASKS", "true")
    monkeypatch.setenv("OPENMANUS_ROOT", str(om_root))
    monkeypatch.setenv("OPENMANUS_PYTHON", str(om_python))

    def _raise_timeout(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=30)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)

    out = daemon._exec_run_hands_task(
        instruction="slow",
        mode="browser_observe",
        max_seconds=30,
        task_id="t-timeout",
    )
    assert out["status"] == "timeout"
    assert out["task_id"] == "t-timeout"
