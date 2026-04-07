"""
safety_gate.py — Sprint S2 Step 1 — autonomous coding safety rules.

Decides whether a proposal can be auto-implemented by swarm_coder.py
or whether it must wait for explicit CEO approval.

Built Session 91 final — autonomous loop must be SAFE before being live.

DESIGN:
- Conservative by default (auto-deny if unsure)
- 4 levels of risk: AUTO (safe), LOW (warn), MEDIUM (CEO required), HIGH (always block)
- Per-file rules + per-proposal rules + global rules
- Stateless, no DB, pure functions

NEVER auto-commit:
- Database migrations (one wrong DROP destroys everything)
- .env files (secrets exposure)
- pnpm-lock.yaml / package-lock.json (dependency surprises)
- CI/CD configs (.github/workflows/) — could enable malicious code execution
- Secrets paths (apps/api/.env, .ssh, .aws)
- Files >500 LOC change in single commit (too risky for review)
- Changes that touch >5 files (scope creep)
- Anything matching: rm -rf, DROP TABLE, FORCE PUSH, --no-verify

ALWAYS safe to auto-commit:
- *.md docs (documentation only)
- Comments / docstrings additions
- Type hints additions
- Test files (apps/api/tests/, apps/web/__tests__/)
- Locale JSON files (translations)

Usage:
    from safety_gate import classify_proposal, can_auto_execute

    verdict = classify_proposal(proposal_dict, target_files=["scripts/foo.py"])
    if verdict.level == "AUTO":
        # safe to autorun
    elif verdict.level in ("MEDIUM", "HIGH"):
        # require CEO approval via Telegram first
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

# ── Risk levels ─────────────────────────────────────────────────────────


@dataclass
class SafetyVerdict:
    level: str  # "AUTO" | "LOW" | "MEDIUM" | "HIGH"
    reason: str
    blocked_paths: list[str]
    suggestions: list[str]

    def can_auto_execute(self) -> bool:
        return self.level == "AUTO"

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "can_auto_execute": self.can_auto_execute(),
            "reason": self.reason,
            "blocked_paths": self.blocked_paths,
            "suggestions": self.suggestions,
        }


# ── Path rules ──────────────────────────────────────────────────────────

# Patterns that ALWAYS block autonomous execution (HIGH risk)
HIGH_RISK_PATTERNS = [
    r"supabase/migrations/",       # DB migrations
    r"\.env(?!\.example)",          # secrets
    r"\.ssh/",                       # SSH keys
    r"\.aws/",                       # AWS creds
    r"apps/api/\.env",              # backend secrets
    r"\.github/workflows/",         # CI/CD configs
    r"package-lock\.json",          # dep lockfile
    r"pnpm-lock\.yaml",             # dep lockfile
    r"requirements\.txt",           # python deps (need review)
    r"pyproject\.toml",             # python project config
    r"Dockerfile",                   # container config
    r"docker-compose",              # container orchestration
    r"\.vercel/",                    # vercel config
    r"\.railway/",                   # railway config
]

# Patterns that DO NOT block but should warn CEO (MEDIUM risk)
MEDIUM_RISK_PATTERNS = [
    r"apps/api/app/main\.py",       # backend entry point
    r"apps/api/app/deps\.py",       # backend dependency injection
    r"apps/api/app/routers/",       # API endpoints (functional code)
    r"apps/api/app/services/",      # business logic
    r"apps/web/src/middleware\.ts", # auth middleware
    r"apps/web/next\.config\.",     # build config
    r"tailwind\.config\.",          # styling config
    r"tsconfig\.json",              # TypeScript config
    r"packages/swarm/coordinator", # swarm core
    r"packages/swarm/autonomous_run", # swarm core
]

# Patterns that are SAFE to auto-edit (AUTO level)
AUTO_SAFE_PATTERNS = [
    r"\.md$",                        # documentation
    r"docs/",                        # docs directory
    r"apps/web/src/locales/.*\.json$", # translations
    r"apps/api/tests/",             # backend tests
    r"apps/web/__tests__/",         # frontend tests
    r"\.test\.(ts|tsx|py)$",        # test files
    r"\.spec\.(ts|tsx|py)$",        # spec files
    r"memory/",                      # swarm memory (non-critical)
    r"scripts/",                     # CLI utility scripts
    r"\.gitignore$",                # gitignore additions
]


# ── Content rules ───────────────────────────────────────────────────────

# Forbidden actions in proposal content (always block)
FORBIDDEN_ACTIONS = [
    r"\brm\s+-rf\b",
    r"\bDROP\s+TABLE\b",
    r"\bDROP\s+DATABASE\b",
    r"\bTRUNCATE\b",
    r"--no-verify",
    r"--force\s+push",
    r"git\s+push.*--force",
    r"git\s+reset\s+--hard",
    r"git\s+checkout\s+--",
    r"chmod\s+777",
    r"sudo\s+",
    r"curl.*\|\s*sh",   # curl-pipe-shell
    r"wget.*\|\s*sh",
    r"eval\(",          # arbitrary eval
    r"exec\(",
    r"\.env\s*=",       # writing .env
]


# ── Limits ──────────────────────────────────────────────────────────────

MAX_FILES_PER_PROPOSAL = 5
MAX_CONTENT_LENGTH = 8000  # rough proxy for proposal complexity


# ── Classification ──────────────────────────────────────────────────────


def _path_matches(path: str, patterns: list[str]) -> bool:
    """True if path matches any of the patterns (regex, case-insensitive)."""
    p_norm = path.replace("\\", "/").lower()
    return any(re.search(pat.lower(), p_norm) for pat in patterns)


def _scan_content_for_forbidden(content: str) -> list[str]:
    """Return list of forbidden actions detected in proposal content."""
    if not content:
        return []
    found = []
    for pattern in FORBIDDEN_ACTIONS:
        if re.search(pattern, content, re.IGNORECASE):
            found.append(pattern)
    return found


def classify_proposal(
    proposal: dict,
    target_files: list[str] | None = None,
) -> SafetyVerdict:
    """Classify a proposal for autonomous execution safety.

    Args:
        proposal: dict with at least {title, content, severity, agent}
        target_files: optional list of file paths the proposal touches

    Returns:
        SafetyVerdict with level (AUTO/LOW/MEDIUM/HIGH) and reason
    """
    title = str(proposal.get("title", ""))
    content = str(proposal.get("content", "") or proposal.get("description", ""))
    severity = str(proposal.get("severity", "")).lower()
    target_files = target_files or []

    blocked: list[str] = []
    suggestions: list[str] = []

    # ── Rule 1: Forbidden content (HIGH always) ─────────────────────────
    forbidden_found = _scan_content_for_forbidden(title + "\n" + content)
    if forbidden_found:
        return SafetyVerdict(
            level="HIGH",
            reason=f"Proposal contains forbidden actions: {', '.join(forbidden_found[:3])}",
            blocked_paths=[],
            suggestions=["CEO must review and execute manually"],
        )

    # ── Rule 2: critical severity (MEDIUM minimum) ──────────────────────
    if severity == "critical":
        return SafetyVerdict(
            level="MEDIUM",
            reason="Critical severity always requires CEO approval",
            blocked_paths=[],
            suggestions=["CEO approval required via Telegram"],
        )

    # ── Rule 3: scope (>5 files = MEDIUM, >10 = HIGH) ────────────────────
    if len(target_files) > 10:
        return SafetyVerdict(
            level="HIGH",
            reason=f"Touches {len(target_files)} files (limit: 10 for any auto execution)",
            blocked_paths=target_files,
            suggestions=["Split into multiple smaller proposals"],
        )

    if len(target_files) > MAX_FILES_PER_PROPOSAL:
        return SafetyVerdict(
            level="MEDIUM",
            reason=f"Touches {len(target_files)} files (limit: {MAX_FILES_PER_PROPOSAL} for auto)",
            blocked_paths=[],
            suggestions=["CEO approval required, or split proposal"],
        )

    # ── Rule 4: content length proxy ────────────────────────────────────
    if len(content) > MAX_CONTENT_LENGTH:
        return SafetyVerdict(
            level="MEDIUM",
            reason=f"Proposal content too long ({len(content)} chars > {MAX_CONTENT_LENGTH})",
            blocked_paths=[],
            suggestions=["Likely too complex for one auto-implementation; split it"],
        )

    # ── Rule 5: per-file path classification ─────────────────────────────
    high_risk_files: list[str] = []
    medium_risk_files: list[str] = []
    auto_safe_files: list[str] = []
    other_files: list[str] = []

    for f in target_files:
        if _path_matches(f, HIGH_RISK_PATTERNS):
            high_risk_files.append(f)
        elif _path_matches(f, MEDIUM_RISK_PATTERNS):
            medium_risk_files.append(f)
        elif _path_matches(f, AUTO_SAFE_PATTERNS):
            auto_safe_files.append(f)
        else:
            other_files.append(f)

    if high_risk_files:
        return SafetyVerdict(
            level="HIGH",
            reason=f"Touches {len(high_risk_files)} HIGH RISK files (migrations/secrets/CI)",
            blocked_paths=high_risk_files,
            suggestions=["CEO must review and execute manually"],
        )

    if medium_risk_files:
        return SafetyVerdict(
            level="MEDIUM",
            reason=f"Touches {len(medium_risk_files)} MEDIUM risk files (functional code)",
            blocked_paths=[],
            suggestions=[
                "CEO approval required via Telegram /approve",
                f"Files: {', '.join(medium_risk_files)}",
            ],
        )

    # ── Rule 6: only auto-safe files? AUTO ──────────────────────────────
    if target_files and not other_files and auto_safe_files:
        return SafetyVerdict(
            level="AUTO",
            reason=f"All {len(auto_safe_files)} files are in AUTO_SAFE list (docs/tests/locales/scripts)",
            blocked_paths=[],
            suggestions=[],
        )

    # ── Rule 7: no target files specified — LOW (need to determine first) ─
    if not target_files:
        return SafetyVerdict(
            level="LOW",
            reason="No target files identified yet — swarm_coder must run file discovery first",
            blocked_paths=[],
            suggestions=["Run project_qa.py to find relevant files, then re-classify"],
        )

    # ── Rule 8: mix of safe + unknown → LOW (cautious) ──────────────────
    return SafetyVerdict(
        level="LOW",
        reason=f"Mixed file set: {len(auto_safe_files)} safe, {len(other_files)} unclassified",
        blocked_paths=[],
        suggestions=["Manual review recommended OR explicit CEO approval"],
    )


def can_auto_execute(proposal: dict, target_files: list[str] | None = None) -> bool:
    """Convenience: True if proposal can be autonomously executed."""
    return classify_proposal(proposal, target_files).can_auto_execute()


# ── Post-execution diff check ───────────────────────────────────────────


@dataclass
class DiffSafetyVerdict:
    """Result of inspecting an actual git commit's diff for safety violations.

    Catches the case where aider/LLM ignored target_files and edited
    unrelated files, OR injected forbidden patterns into the code.
    """
    safe: bool
    violations: list[str]
    files_changed: list[str]
    files_unexpected: list[str]
    forbidden_patterns_in_diff: list[str]


def verify_commit_safe(
    commit_hash: str,
    expected_files: list[str],
    project_root: Path,
) -> DiffSafetyVerdict:
    """Inspect a git commit's actual diff to verify it stayed within bounds.

    Use this AFTER an aider invocation to catch:
    - Files modified that weren't in expected_files (scope escape)
    - Forbidden patterns inserted into code (rm -rf, git push --force, etc.)

    Args:
        commit_hash: the SHA to inspect (e.g. HEAD)
        expected_files: paths the proposal was allowed to touch (relative to project_root)
        project_root: repo root for git command cwd

    Returns:
        DiffSafetyVerdict with safe=True only if every changed file was expected
        AND no forbidden patterns appear in the diff.
    """
    import subprocess

    violations: list[str] = []
    files_changed: list[str] = []
    files_unexpected: list[str] = []
    forbidden_in_diff: list[str] = []

    # Step 1: list files changed by the commit
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
        files_changed = [
            line.strip().replace("\\", "/")
            for line in result.stdout.splitlines()
            if line.strip()
        ]
    except Exception as e:
        violations.append(f"git show failed: {e}")
        return DiffSafetyVerdict(False, violations, [], [], [])

    # Normalize expected files
    expected_norm = {f.replace("\\", "/").lower() for f in expected_files}

    # Step 2: check every changed file was expected OR matches AUTO_SAFE patterns
    for f in files_changed:
        f_norm = f.lower()
        if f_norm in expected_norm:
            continue
        # Allow auto-safe paths even if not explicitly listed
        if _path_matches(f, AUTO_SAFE_PATTERNS):
            continue
        files_unexpected.append(f)
        violations.append(f"Touched unexpected file: {f}")

    # Step 3: verify no HIGH_RISK files were touched (always block)
    for f in files_changed:
        if _path_matches(f, HIGH_RISK_PATTERNS):
            violations.append(f"Touched HIGH RISK file: {f}")

    # Step 4: scan the actual diff for forbidden patterns
    try:
        diff_result = subprocess.run(
            ["git", "show", commit_hash],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        diff_added_lines: list[str] = []
        for line in diff_result.stdout.splitlines():
            # Only inspect ADDED lines (start with +, not +++)
            if line.startswith("+") and not line.startswith("+++"):
                diff_added_lines.append(line[1:])
        added_text = "\n".join(diff_added_lines)
        for pattern in FORBIDDEN_ACTIONS:
            if re.search(pattern, added_text, re.IGNORECASE):
                forbidden_in_diff.append(pattern)
                violations.append(f"Forbidden pattern in diff: {pattern}")
    except Exception as e:
        violations.append(f"git show diff failed: {e}")

    return DiffSafetyVerdict(
        safe=len(violations) == 0,
        violations=violations,
        files_changed=files_changed,
        files_unexpected=files_unexpected,
        forbidden_patterns_in_diff=forbidden_in_diff,
    )


# ── CLI ─────────────────────────────────────────────────────────────────


def _cli() -> None:
    """Quick CLI test:
    python scripts/safety_gate.py
    """
    test_cases = [
        {
            "name": "Safe docs proposal",
            "proposal": {
                "title": "Update README with Session 91 status",
                "content": "Add a paragraph about new tools",
                "severity": "low",
            },
            "files": ["README.md", "docs/HANDOFF.md"],
            "expected": "AUTO",
        },
        {
            "name": "Migration touch (HIGH block)",
            "proposal": {
                "title": "Add user preferences column",
                "content": "ALTER TABLE profiles add preferences jsonb",
                "severity": "medium",
            },
            "files": ["supabase/migrations/20260408_prefs.sql"],
            "expected": "HIGH",
        },
        {
            "name": "Secret exposure attempt (HIGH)",
            "proposal": {
                "title": "Update API keys",
                "content": "Set new GROQ_API_KEY in apps/api/.env",
                "severity": "high",
            },
            "files": ["apps/api/.env"],
            "expected": "HIGH",
        },
        {
            "name": "rm -rf in content (HIGH)",
            "proposal": {
                "title": "Clean build artifacts",
                "content": "Run `rm -rf node_modules` then rebuild",
                "severity": "low",
            },
            "files": ["scripts/clean.sh"],
            "expected": "HIGH",
        },
        {
            "name": "Critical severity (MEDIUM)",
            "proposal": {
                "title": "Production hotfix",
                "content": "Fix data corruption bug",
                "severity": "critical",
            },
            "files": ["scripts/hotfix.py"],
            "expected": "MEDIUM",
        },
        {
            "name": "Backend router (MEDIUM)",
            "proposal": {
                "title": "Add /v1/me endpoint",
                "content": "New endpoint to return current user",
                "severity": "high",
            },
            "files": ["apps/api/app/routers/users.py"],
            "expected": "MEDIUM",
        },
        {
            "name": "Translations only (AUTO)",
            "proposal": {
                "title": "Translate empty Azerbaijani strings",
                "content": "Add missing AZ translations",
                "severity": "low",
            },
            "files": ["apps/web/src/locales/az/common.json"],
            "expected": "AUTO",
        },
        {
            "name": "7 files (MEDIUM, scope >5 but <=10)",
            "proposal": {
                "title": "Big refactor",
                "content": "Refactor all routers",
                "severity": "medium",
            },
            "files": [f"apps/api/app/routers/{n}.py" for n in "abcdefg"],
            "expected": "MEDIUM",  # 7 files: scope rule fires first (>5 → MEDIUM)
        },
        {
            "name": "12 files (HIGH, scope >10)",
            "proposal": {
                "title": "Massive refactor",
                "content": "Touch many files",
                "severity": "low",
            },
            "files": [f"docs/file_{i}.md" for i in range(12)],
            "expected": "HIGH",
        },
    ]

    print(f"{'Test':<40} {'Expected':<10} {'Got':<10} {'OK'}")
    print("-" * 75)
    passed = 0
    for tc in test_cases:
        verdict = classify_proposal(tc["proposal"], tc["files"])
        ok = verdict.level == tc["expected"]
        passed += 1 if ok else 0
        marker = "OK" if ok else "FAIL"
        print(f"{tc['name']:<40} {tc['expected']:<10} {verdict.level:<10} {marker}")
        if not ok:
            print(f"  reason: {verdict.reason}")

    print("-" * 75)
    print(f"Passed {passed}/{len(test_cases)}")


if __name__ == "__main__":
    _cli()
