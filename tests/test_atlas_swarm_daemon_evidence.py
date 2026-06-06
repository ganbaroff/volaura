"""Phase C — daemon-side evidence excerpt fetcher tests.

Tests the new ``_fetch_evidence_excerpt`` helper and its integration into
``_mark_finding_evidence``. Goal: prove the daemon now opens the cited file
at the cited line and surfaces the actual bytes alongside the agent's claim,
so a reviewer can immediately spot agent-claim vs file-truth mismatches.

Reference: codex-loop.md Phase C.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from tests._paths import script_path as repo_script_path


def _load_daemon():
    script_path = repo_script_path("atlas_swarm_daemon.py")
    spec = importlib.util.spec_from_file_location("atlas_swarm_daemon_evidence_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _fake_repo(tmp_path: Path) -> Path:
    """Build a minimal repo layout under tmp_path with one known file."""
    apps = tmp_path / "apps" / "api"
    apps.mkdir(parents=True)
    target = apps / "main.py"
    target.write_text(
        "\n".join([
            "from fastapi import FastAPI",                # 1
            "from slowapi import Limiter",                # 2
            "",                                          # 3
            "app = FastAPI()",                           # 4
            "limiter = Limiter(key_func=lambda r: r.host)",  # 5
            "",                                          # 6
            "@app.post('/start')",                        # 7
            "@limiter.limit('5/minute')",                 # 8 — RATE LIMIT IS HERE
            "async def start():",                         # 9
            "    return {'ok': True}",                    # 10
        ]),
        encoding="utf-8",
    )
    return target


# ── _fetch_evidence_excerpt direct tests ──────────────────────────────────────

def test_fetch_excerpt_with_structured_line(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _fake_repo(tmp_path)
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)

    finding = {
        "claim": "Rate limiter present on /start",
        "line": 8,
        "evidence_path_or_command": "apps/api/main.py",
    }
    paths = ["apps/api/main.py"]
    excerpt = daemon._fetch_evidence_excerpt(finding, paths)
    assert excerpt is not None
    assert excerpt["path"] == "apps/api/main.py"
    assert excerpt["line"] == 8
    assert excerpt["excerpt_kind"] == "structured-line"
    assert ">> 8: @limiter.limit('5/minute')" in excerpt["excerpt"]
    # Context lines around the target should be visible too.
    assert "7: @app.post('/start')" in excerpt["excerpt"]


def test_fetch_excerpt_with_path_colon_line(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _fake_repo(tmp_path)
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)

    finding = {
        "claim": "Limiter wired",
        "evidence_path_or_command": "apps/api/main.py:5",
    }
    paths = ["apps/api/main.py"]
    excerpt = daemon._fetch_evidence_excerpt(finding, paths)
    assert excerpt is not None
    assert excerpt["line"] == 5
    assert excerpt["excerpt_kind"] == "parsed-from-text"
    assert ">> 5: limiter = Limiter" in excerpt["excerpt"]


def test_fetch_excerpt_returns_none_when_no_paths(monkeypatch, tmp_path):
    daemon = _load_daemon()
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)
    finding = {"claim": "X", "line": 1}
    assert daemon._fetch_evidence_excerpt(finding, []) is None


def test_fetch_excerpt_returns_none_when_no_line_anywhere(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _fake_repo(tmp_path)
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)
    finding = {
        "claim": "File exists",
        "evidence_path_or_command": "apps/api/main.py (the api entry)",
    }
    paths = ["apps/api/main.py"]
    assert daemon._fetch_evidence_excerpt(finding, paths) is None


def test_fetch_excerpt_out_of_range(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _fake_repo(tmp_path)
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)
    finding = {"claim": "X", "line": 999}
    paths = ["apps/api/main.py"]
    excerpt = daemon._fetch_evidence_excerpt(finding, paths)
    assert excerpt is not None
    assert excerpt["excerpt_kind"] == "out-of-range"
    assert excerpt["excerpt"] == ""


def test_fetch_excerpt_rejects_non_int_line():
    daemon = _load_daemon()
    finding = {"claim": "X", "line": "not-a-number"}
    paths = ["apps/api/main.py"]
    # No paths verification monkeypatch here — function should return None
    # regardless because line cannot be coerced.
    assert daemon._fetch_evidence_excerpt(finding, paths) is None


# ── integration via _mark_finding_evidence ────────────────────────────────────

def test_mark_finding_evidence_attaches_excerpt(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _fake_repo(tmp_path)
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)

    finding = {
        "claim": "Rate limiter on /start",
        "line": 8,
        "evidence_path_or_command": "apps/api/main.py:8",
    }
    marked = daemon._mark_finding_evidence(finding)
    assert marked["evidence_status"] == "verified"
    assert "evidence_excerpt" in marked
    assert marked["evidence_excerpt"]["path"] == "apps/api/main.py"
    assert marked["evidence_excerpt"]["line"] == 8
    assert "@limiter.limit" in marked["evidence_excerpt"]["excerpt"]


def test_mark_finding_evidence_no_excerpt_when_no_line(monkeypatch, tmp_path):
    daemon = _load_daemon()
    _fake_repo(tmp_path)
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)

    # No line citation anywhere → evidence_excerpt should be absent but
    # evidence_status falls back to unverified per existing behaviour
    # (since no LINE_PROOF_RE match either).
    finding = {
        "claim": "File present",
        "evidence_path_or_command": "apps/api/main.py exists somewhere",
    }
    marked = daemon._mark_finding_evidence(finding)
    assert "evidence_excerpt" not in marked
    assert marked["evidence_status"] == "unverified"
    assert marked["evidence_reason"] == "missing_line_or_grep_proof"


def test_mark_finding_evidence_unverified_with_no_path(monkeypatch, tmp_path):
    daemon = _load_daemon()
    monkeypatch.setattr(daemon, "REPO_ROOT", tmp_path)

    finding = {
        "claim": "Some general claim with no file reference",
        "line": 42,
    }
    marked = daemon._mark_finding_evidence(finding)
    assert marked["evidence_status"] == "unverified"
    assert marked["evidence_reason"] == "no_existing_file_path"
    assert "evidence_excerpt" not in marked
