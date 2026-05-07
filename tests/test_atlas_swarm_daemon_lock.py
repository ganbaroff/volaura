"""
Tests for atlas_swarm_daemon.py single-instance lock and health heartbeat.

Mirrors the importlib + monkeypatch pattern from test_atlas_swarm_daemon_bridge.py.
All tests use tmp_path so they never touch the real runtime/ directory.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path


def _load_daemon_module():
    script_path = Path("C:/Projects/VOLAURA/scripts/atlas_swarm_daemon.py")
    spec = importlib.util.spec_from_file_location("atlas_swarm_daemon_lock_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _wire_paths(daemon, tmp_path):
    """Redirect all filesystem paths in the daemon module to tmp_path."""
    runtime_dir = tmp_path / "runtime"
    lock_file = runtime_dir / "atlas_swarm_daemon.lock"
    health_file = runtime_dir / "daemon-health.json"
    pending = tmp_path / "pending"
    in_progress = tmp_path / "in-progress"
    done = tmp_path / "done"
    failed = tmp_path / "failed"
    log_file = tmp_path / "daemon.log.jsonl"
    for d in (pending, in_progress, done, failed):
        d.mkdir(parents=True, exist_ok=True)
    daemon.RUNTIME_DIR = runtime_dir
    daemon.LOCK_FILE = lock_file
    daemon.HEALTH_FILE = health_file
    daemon.PENDING = pending
    daemon.IN_PROGRESS = in_progress
    daemon.DONE = done
    daemon.FAILED = failed
    # Redirect log_event writes so tests don't pollute the real queue log
    daemon.LOG = log_file
    return runtime_dir, lock_file, health_file


# ── Lock tests ────────────────────────────────────────────────────────────────


def test_acquire_lock_when_no_lock_exists(tmp_path, monkeypatch):
    daemon = _load_daemon_module()
    _, lock_file, _ = _wire_paths(daemon, tmp_path)

    result = daemon.acquire_lock()

    assert result is True, "acquire_lock() should return True when no lock exists"
    assert lock_file.exists(), "LOCK_FILE should be created after acquiring"
    payload = json.loads(lock_file.read_text(encoding="utf-8"))
    assert payload["pid"] == os.getpid()
    assert "started_at" in payload
    assert "cwd" in payload
    assert "command" in payload


def test_acquire_lock_refuses_when_alive_pid_holds_lock(tmp_path, monkeypatch):
    daemon = _load_daemon_module()
    _, lock_file, _ = _wire_paths(daemon, tmp_path)

    # Pre-write lock with our own PID (always alive)
    own_pid = os.getpid()
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(
        json.dumps({"pid": own_pid, "started_at": "2026-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    original_content = lock_file.read_text(encoding="utf-8")

    # Call acquire_lock() from a "different" process perspective by temporarily
    # monkeypatching getpid to return a different value so own_pid != existing_pid
    fake_pid = own_pid + 9999
    monkeypatch.setattr(os, "getpid", lambda: fake_pid)

    result = daemon.acquire_lock()

    assert result is False, "acquire_lock() must refuse when existing PID is alive"
    # Lock file must be untouched
    assert lock_file.read_text(encoding="utf-8") == original_content


def test_acquire_lock_recovers_stale_lock_when_pid_dead(tmp_path, monkeypatch):
    daemon = _load_daemon_module()
    _, lock_file, _ = _wire_paths(daemon, tmp_path)

    dead_pid = 99999999  # guaranteed not to be a real PID on any sane OS
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(
        json.dumps({"pid": dead_pid, "started_at": "2026-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )

    # Force _is_pid_alive to return False for the dead_pid
    monkeypatch.setattr(daemon, "_is_pid_alive", lambda pid: False)

    result = daemon.acquire_lock()

    assert result is True, "acquire_lock() should recover a stale lock and return True"
    payload = json.loads(lock_file.read_text(encoding="utf-8"))
    assert payload["pid"] == os.getpid(), "LOCK_FILE should now contain own PID"


def test_release_lock_removes_file(tmp_path, monkeypatch):
    daemon = _load_daemon_module()
    _, lock_file, _ = _wire_paths(daemon, tmp_path)

    # Acquire first
    acquired = daemon.acquire_lock()
    assert acquired is True
    assert lock_file.exists()

    # Release
    daemon.release_lock()
    assert not lock_file.exists(), "LOCK_FILE should be removed after release"

    # Idempotent — second call must not raise
    daemon.release_lock()


# ── Health tests ──────────────────────────────────────────────────────────────


def test_update_health_writes_required_fields(tmp_path, monkeypatch):
    daemon = _load_daemon_module()
    _, _, health_file = _wire_paths(daemon, tmp_path)

    # Reset module-level started_at so each test gets a fresh timestamp
    daemon._DAEMON_STARTED_AT = None

    daemon.update_health(status="polling")

    assert health_file.exists(), "HEALTH_FILE should be created after update_health()"
    data = json.loads(health_file.read_text(encoding="utf-8"))
    for key in ("status", "pid", "started_at", "last_heartbeat_at", "cwd", "queue_counts"):
        assert key in data, f"Missing required key: {key}"
    assert data["status"] == "polling"
    assert data["pid"] == os.getpid()
    assert isinstance(data["queue_counts"], dict)
    for sub in ("pending", "in_progress", "done", "failed"):
        assert sub in data["queue_counts"], f"queue_counts missing sub-key: {sub}"


def test_update_health_preserves_prior_keys(tmp_path, monkeypatch):
    daemon = _load_daemon_module()
    _, _, health_file = _wire_paths(daemon, tmp_path)

    daemon._DAEMON_STARTED_AT = None

    # First write with a current_task_id
    daemon.update_health(status="busy", current_task_id="abc-task-001")
    data = json.loads(health_file.read_text(encoding="utf-8"))
    assert data.get("current_task_id") == "abc-task-001"

    # Second write without specifying current_task_id (and status != "idle")
    daemon.update_health(status="polling")
    data2 = json.loads(health_file.read_text(encoding="utf-8"))
    # Prior current_task_id must be preserved (not deleted when status != "idle")
    assert data2.get("current_task_id") == "abc-task-001", (
        "update_health() should preserve prior current_task_id when not explicitly cleared"
    )
    assert data2["status"] == "polling"
