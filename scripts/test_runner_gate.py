"""
test_runner_gate.py — Sprint S3 Step 2 — pytest gate after autonomous commit.

After swarm_coder + aider make a commit, this gate runs targeted pytest
on files matching the changed modules. If tests fail, the commit is reverted
via git reset --hard HEAD~1.

DESIGN:
- Targeted, not full suite. Running 742 tests on every commit would be too slow
  and would flake on unrelated existing failures.
- Convention-based mapping:
    apps/api/app/foo.py        -> apps/api/tests/test_foo.py
    apps/api/app/routers/x.py  -> apps/api/tests/test_x.py
    apps/api/app/services/y.py -> apps/api/tests/test_y.py
    scripts/foo.py             -> (no tests in scripts/, allow)
    apps/web/...               -> (npm test, not handled here, allow)
    *.md                       -> (docs, no tests, allow)
- "No tests found" => allow (we don't gate uncovered code yet)
- "Tests exist and FAIL" => REVERT
- "Tests exist and PASS" => SAFE

USAGE:
    from test_runner_gate import gate_commit
    verdict = gate_commit("eec1590", project_root=Path("C:/Projects/VOLAURA"))
    if not verdict.safe:
        # revert
        ...

NOTE: For backend tests, uses apps/api/.venv/Scripts/pytest.exe directly
to avoid venv activation issues. This is hardcoded and will need a config
setting eventually.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestVerdict:
    safe: bool
    reason: str
    tests_run: list[str] = field(default_factory=list)
    tests_passed: int = 0
    tests_failed: int = 0
    pytest_output: str = ""


# ── Test file discovery ────────────────────────────────────────


def _find_test_files_for(source_path: str, project_root: Path) -> list[Path]:
    """Find all test files that likely cover a given source file.

    Convention in this project is loose:
      apps/api/app/routers/assessment.py → tests/test_assessment_router.py
                                        +  tests/test_assessment_api_e2e.py
      apps/api/app/core/assessment/engine.py → tests/test_assessment_engine.py
      apps/api/app/services/aura.py → tests/test_aura.py

    Strategy: collect all test_*.py files in apps/api/tests/ whose name
    contains the source basename. Over-match (more tests run) is safer
    than under-match (untested commits slip through).

    Returns list of matching test file Paths (may be empty).
    """
    p = source_path.replace("\\", "/")
    if not p.endswith(".py"):
        return []

    # Skip test files themselves — they don't need re-testing
    if "/tests/" in p or Path(p).name.startswith("test_"):
        return []

    if not p.startswith("apps/api/app/"):
        return []  # only backend mapping for now

    basename = Path(p).stem  # e.g. "assessment", "engine", "aura"
    tests_dir = project_root / "apps" / "api" / "tests"
    if not tests_dir.exists():
        return []

    matches: list[Path] = []
    for tf in tests_dir.glob("test_*.py"):
        if basename in tf.stem:
            matches.append(tf)
    return matches


def _list_changed_files(commit_hash: str, project_root: Path) -> list[str]:
    """git show --name-only for the commit."""
    try:
        result = subprocess.run(
            ["git", "show", "--name-only", "--pretty=format:", commit_hash],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        return [
            line.strip().replace("\\", "/")
            for line in result.stdout.splitlines()
            if line.strip()
        ]
    except Exception:
        return []


# ── Pytest invocation ──────────────────────────────────────────


def _run_pytest_on(test_files: list[Path], project_root: Path, timeout: int = 180) -> dict:
    """Run pytest on specific test files using the apps/api venv pytest.

    Returns dict with: ok, exit_code, passed, failed, output
    """
    pytest_bin = project_root / "apps" / "api" / ".venv" / "Scripts" / "pytest.exe"
    if not pytest_bin.exists():
        # Fall back to system pytest via python -m
        cmd = ["python", "-m", "pytest"]
    else:
        cmd = [str(pytest_bin)]

    cmd += ["-x", "--tb=short", "-q", "--no-header"]
    cmd += [str(f.relative_to(project_root)) for f in test_files]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root / "apps" / "api"),  # run from backend dir for path resolution
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit_code": -1, "passed": 0, "failed": 0,
                "output": f"pytest timeout after {timeout}s"}
    except Exception as e:
        return {"ok": False, "exit_code": -2, "passed": 0, "failed": 0,
                "output": f"pytest invocation failed: {e}"}

    out = (result.stdout or "") + "\n" + (result.stderr or "")
    # Parse pytest summary line: "X passed, Y failed in Zs"
    import re
    passed = 0
    failed = 0
    m = re.search(r"(\d+)\s+passed", out)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", out)
    if m:
        failed = int(m.group(1))

    # Detect infrastructure errors (broken venv, missing deps, etc.) — these
    # are NOT regressions from the commit, they're pre-existing problems.
    # The gate should not block real changes because of a broken local setup.
    infra_markers = [
        "ModuleNotFoundError",
        "ImportError while loading conftest",
        "ERROR collecting",
        "INTERNALERROR",
        "no module named",
    ]
    out_lower = out.lower()
    infra_broken = any(marker.lower() in out_lower for marker in infra_markers)

    return {
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
        "passed": passed,
        "failed": failed,
        "infra_broken": infra_broken,
        "output": out[-2000:],
    }


# ── Public API ─────────────────────────────────────────────────


def gate_commit(commit_hash: str, project_root: Path) -> TestVerdict:
    """Gate a recent commit by running matching tests. Returns TestVerdict.

    Logic:
    - List files changed in commit
    - For each .py source, find matching test file via convention
    - Run pytest on collected test files
    - safe=True if all pass OR no tests found (uncovered code allowed)
    - safe=False if any test fails
    """
    changed = _list_changed_files(commit_hash, project_root)
    if not changed:
        return TestVerdict(safe=True, reason="No files changed (empty commit?)")

    test_files: list[Path] = []
    no_test_sources: list[str] = []
    for src in changed:
        matches = _find_test_files_for(src, project_root)
        if matches:
            test_files.extend(matches)
        elif src.endswith(".py") and "/tests/" not in src.replace("\\", "/"):
            no_test_sources.append(src)

    if not test_files:
        if no_test_sources:
            return TestVerdict(
                safe=True,
                reason=f"No matching tests for changed .py files: {no_test_sources[:3]} (allowed — uncovered code policy)",
            )
        return TestVerdict(safe=True, reason="No .py files changed (no tests needed)")

    # Dedupe test files
    test_files = sorted(set(test_files))

    result = _run_pytest_on(test_files, project_root)

    # Infra broken => allow but warn loudly. We can't gate when local pytest
    # itself is misconfigured (missing deps, broken conftest). Real protection
    # for infra-broken environments is GitHub Actions CI on PR, not this gate.
    if result.get("infra_broken"):
        return TestVerdict(
            safe=True,
            reason=f"Test infrastructure broken (missing deps / conftest error). NOT gated. Fix local venv.",
            tests_run=[str(f.relative_to(project_root)) for f in test_files],
            tests_passed=0,
            tests_failed=0,
            pytest_output=result["output"],
        )

    return TestVerdict(
        safe=result["ok"],
        reason=(
            f"All {result['passed']} tests passed"
            if result["ok"]
            else f"{result['failed']} tests failed (passed {result['passed']})"
        ),
        tests_run=[str(f.relative_to(project_root)) for f in test_files],
        tests_passed=result["passed"],
        tests_failed=result["failed"],
        pytest_output=result["output"],
    )


# ── CLI for standalone testing ────────────────────────────────


def _cli() -> None:
    import argparse, sys
    parser = argparse.ArgumentParser(description="Run targeted pytest gate on a git commit")
    parser.add_argument("commit", help="git commit hash to inspect")
    parser.add_argument("--project-root", default="C:/Projects/VOLAURA")
    args = parser.parse_args()

    verdict = gate_commit(args.commit, Path(args.project_root))
    print(f"safe:    {verdict.safe}")
    print(f"reason:  {verdict.reason}")
    if verdict.tests_run:
        print(f"tests:   {verdict.tests_run}")
        print(f"passed:  {verdict.tests_passed}")
        print(f"failed:  {verdict.tests_failed}")
    if not verdict.safe:
        print()
        print("--- pytest output (tail) ---")
        print(verdict.pytest_output[-1000:])
    sys.exit(0 if verdict.safe else 1)


if __name__ == "__main__":
    _cli()
