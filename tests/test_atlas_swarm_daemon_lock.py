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


# ── Azure token-param tests ───────────────────────────────────────────────────


def test_azure_token_param_o4_mini_returns_max_completion_tokens():
    daemon = _load_daemon_module()
    out = daemon._azure_token_param("o4-mini", 1500)
    assert out == {"max_completion_tokens": 1500}


def test_azure_token_param_o3_mini_returns_max_completion_tokens():
    daemon = _load_daemon_module()
    out = daemon._azure_token_param("o3-mini", 800)
    assert out == {"max_completion_tokens": 800}


def test_azure_token_param_gpt_4o_returns_max_tokens():
    daemon = _load_daemon_module()
    out = daemon._azure_token_param("gpt-4o", 2000)
    assert out == {"max_tokens": 2000}


def test_azure_token_param_gpt_4_1_mini_returns_max_tokens():
    daemon = _load_daemon_module()
    out = daemon._azure_token_param("gpt-4.1-mini", 500)
    assert out == {"max_tokens": 500}


def test_azure_token_param_case_insensitive():
    daemon = _load_daemon_module()
    out = daemon._azure_token_param("O4-Mini", 1000)
    assert out == {"max_completion_tokens": 1000}


# ── Provider mapping tests (post Azure-RAI remap) ─────────────────────────────


def test_remapped_perspectives_are_not_azure():
    daemon = _load_daemon_module()
    remapped = [
        "Security Auditor",
        "Code Quality Engineer",
        "Chief Strategist",
        "QA Engineer",
        "CTO Watchdog",
    ]
    for name in remapped:
        provider, _model = daemon.AGENT_LLM_MAP[name]
        assert provider != "azure", (
            f"{name} must be re-routed off azure (RAI content-filter)"
        )


def test_ux_designer_stays_azure():
    daemon = _load_daemon_module()
    provider, model = daemon.AGENT_LLM_MAP["UX Designer"]
    assert provider == "azure"
    assert model == "gpt-4.1-nano"


def test_ecosystem_auditor_stays_nvidia_heavy():
    daemon = _load_daemon_module()
    provider, _model = daemon.AGENT_LLM_MAP["Ecosystem Auditor"]
    assert provider == "nvidia-heavy"


# ── Git mutation safety tests (CEO directive 2026-05-07) ──────────────────────


def _fake_run_factory(stdout_map):
    """Build a subprocess.run replacement that returns canned stdout per command prefix."""
    from types import SimpleNamespace

    def _run(cmd, **_kw):
        joined = " ".join(str(c) for c in cmd[:4])
        for prefix, stdout in stdout_map.items():
            if joined.startswith(prefix):
                return SimpleNamespace(returncode=0, stdout=stdout, stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return _run


def test_git_commit_push_blocked_without_env_flag(monkeypatch):
    daemon = _load_daemon_module()
    monkeypatch.delenv("ATLAS_GIT_MUTATIONS_ENABLED", raising=False)
    result = daemon._exec_git_commit_push(message="t", files=["a.py"])
    assert result["status"] == "blocked"
    assert "ATLAS_GIT_MUTATIONS_ENABLED" in result["reason"]


def test_git_commit_push_blocked_on_main_without_allow_flag(monkeypatch):
    import subprocess
    daemon = _load_daemon_module()
    monkeypatch.setenv("ATLAS_GIT_MUTATIONS_ENABLED", "true")
    monkeypatch.delenv("ATLAS_ALLOW_MAIN_GIT_MUTATIONS", raising=False)
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run_factory({"git rev-parse --abbrev-ref": "main\n"}),
    )
    result = daemon._exec_git_commit_push(message="t", files=["a.py"])
    assert result["status"] == "blocked"
    assert "main" in result["reason"]


def test_git_commit_push_blocked_pre_staged_unrelated(monkeypatch):
    import subprocess
    daemon = _load_daemon_module()
    monkeypatch.setenv("ATLAS_GIT_MUTATIONS_ENABLED", "true")
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run_factory({
            "git rev-parse --abbrev-ref": "codex/feature\n",
            "git status --porcelain": "M  unrelated.py\n",  # staged unrelated
        }),
    )
    result = daemon._exec_git_commit_push(message="t", files=["a.py"])
    assert result["status"] == "blocked"
    assert "pre-staged" in result["reason"]


def test_git_commit_push_blocked_dirty_unrelated_untracked(monkeypatch):
    import subprocess
    daemon = _load_daemon_module()
    monkeypatch.setenv("ATLAS_GIT_MUTATIONS_ENABLED", "true")
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run_factory({
            "git rev-parse --abbrev-ref": "codex/feature\n",
            "git status --porcelain": "?? unrelated.py\n",  # untracked unrelated
        }),
    )
    result = daemon._exec_git_commit_push(message="t", files=["a.py"])
    assert result["status"] == "blocked"
    assert "unrelated" in result["reason"]


def test_git_commit_push_uses_current_branch(monkeypatch):
    import subprocess
    daemon = _load_daemon_module()
    monkeypatch.setenv("ATLAS_GIT_MUTATIONS_ENABLED", "true")

    pushed_target = []

    from types import SimpleNamespace

    def fake_run(cmd, **_kw):
        joined = " ".join(str(c) for c in cmd[:4])
        if joined.startswith("git rev-parse --abbrev-ref"):
            return SimpleNamespace(returncode=0, stdout="codex/myfeature\n", stderr="")
        if joined.startswith("git status --porcelain"):
            return SimpleNamespace(returncode=0, stdout=" M a.py\n", stderr="")
        if joined.startswith("git push origin"):
            pushed_target.append(cmd[3] if len(cmd) > 3 else None)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:1] == ["python3"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    # Bypass safety_gate import inside function with a real-or-stub allow
    class _OkVerdict:
        level = "ok"
        reason = ""
        blocked_paths: list = []

        def can_auto_execute(self):
            return True

    import sys
    fake_module = type(sys)("scripts.safety_gate")
    fake_module.classify_proposal = lambda *_a, **_kw: _OkVerdict()
    monkeypatch.setitem(sys.modules, "scripts.safety_gate", fake_module)

    result = daemon._exec_git_commit_push(message="t", files=["a.py"])
    assert result.get("branch") == "codex/myfeature", (
        f"branch in result must be codex/myfeature, got {result}"
    )
    assert pushed_target == ["codex/myfeature"], (
        f"git push must target current branch, not hardcoded main; got {pushed_target}"
    )


def test_secrets_dir_in_gitignore():
    from pathlib import Path
    gi = Path("C:/Projects/VOLAURA/.gitignore").read_text(encoding="utf-8")
    lines = [l.strip() for l in gi.splitlines()]
    assert "secrets/" in lines, "secrets/ must be in .gitignore"


# ── In-progress runtime state tests (CEO directive 2026-05-08) ────────────────


def test_in_progress_dir_in_gitignore():
    from pathlib import Path
    gi = Path("C:/Projects/VOLAURA/.gitignore").read_text(encoding="utf-8")
    lines = [l.strip() for l in gi.splitlines()]
    assert "memory/atlas/work-queue/in-progress/*" in lines, (
        "in-progress runtime queue must be gitignored"
    )


def test_task_age_uses_task_id_date_when_mtime_fresh(tmp_path):
    daemon = _load_daemon_module()
    # Dir name is months in the past, but its mtime was JUST touched (e.g. by git checkout)
    task_dir = tmp_path / "2026-01-15-brain-1"
    task_dir.mkdir()
    # mtime defaults to now
    from datetime import datetime, timezone
    now_ts = datetime.now(timezone.utc).timestamp()
    age = daemon._task_age_seconds(task_dir, now_ts)
    # Should detect via the YYYY-MM-DD prefix that this is much older than mtime suggests
    # 2026-01-15 to 2026-05-08 is ~110 days = ~9.5M seconds, well past any sane STALE
    assert age > 30 * 24 * 3600, f"id-date fallback should report >30d age, got {age}"


def test_task_age_uses_started_at_when_present(tmp_path):
    daemon = _load_daemon_module()
    task_dir = tmp_path / "fresh-name-no-date"
    task_dir.mkdir()
    # Write started_at 5 days ago
    from datetime import datetime, timedelta, timezone
    five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
    (task_dir / "started_at.json").write_text(
        json.dumps({"task_id": "fresh-name-no-date",
                     "started_at": five_days_ago.isoformat()}),
        encoding="utf-8",
    )
    now_ts = datetime.now(timezone.utc).timestamp()
    age = daemon._task_age_seconds(task_dir, now_ts)
    assert age >= 4 * 24 * 3600, f"started_at fallback should report ~5d age, got {age}"


def test_archive_stale_uses_unique_failed_destination(tmp_path, monkeypatch):
    daemon = _load_daemon_module()

    in_prog = tmp_path / "in-progress"
    failed = tmp_path / "failed"
    in_prog.mkdir()
    failed.mkdir()

    task_id = "2026-01-01-collision-test"
    stale_dir = in_prog / task_id
    stale_dir.mkdir()
    # Pre-existing failed/<task_id> (collision target)
    existing_fail = failed / task_id
    existing_fail.mkdir()
    (existing_fail / "result.json").write_text(
        json.dumps({"task_id": task_id, "status": "earlier_failure"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(daemon, "IN_PROGRESS", in_prog)
    monkeypatch.setattr(daemon, "FAILED", failed)
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(daemon, "STALE_IN_PROGRESS_SECONDS", 1)
    monkeypatch.setattr(daemon, "log_event", lambda event: None)

    from datetime import datetime, timezone
    future_ts = datetime.now(timezone.utc).timestamp() + 999_999
    recovered = daemon._archive_stale_in_progress(now_ts=future_ts)

    assert recovered == 1
    assert not stale_dir.exists(), "stale dir must be moved out of in-progress"
    # Original failed/<task_id> retains its earlier evidence (not overwritten)
    assert existing_fail.exists()
    assert json.loads((existing_fail / "result.json").read_text(encoding="utf-8"))["status"] == "earlier_failure"
    # Suffix-named sibling exists
    siblings = sorted(p.name for p in failed.iterdir() if p.is_dir())
    assert any(s.startswith(f"{task_id}-stale-") for s in siblings), (
        f"unique suffix dir must exist alongside original; got {siblings}"
    )
