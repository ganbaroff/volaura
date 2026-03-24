"""
AutonomousUpgradeProtocol — Godel Agent pattern for swarm self-modification.

The swarm can propose improvements to its own code (via self_upgrade.py).
This module handles the full lifecycle:

  backup → validate_syntax → benchmark_before → apply → benchmark_after → commit_or_rollback

Risk levels:
  LOW    — syntax/config changes. validate_syntax only, no benchmark.
  MEDIUM — logic changes. validate + quick benchmark (3 questions).
  HIGH   — architecture changes. validate + full benchmark (5 questions) + human approval required.

Safety guarantees:
  - Never modifies files outside packages/swarm/
  - IMMUTABLE FILES: autonomous_upgrade.py, engine.py, __init__.py cannot be self-modified
    (kimi-k2 feedback: "if an agent modifies the rollback code, rollback won't work")
  - KILL SWITCH: if ~/.swarm/KILL_SWITCH exists, ALL upgrades are blocked instantly
  - Always creates a timestamped backup before any write
  - Audit log written BEFORE apply (not after) — survives crashes
  - Auto-rollback if benchmark regresses by > REGRESSION_THRESHOLD (10%)
  - Auto-rollback on any syntax/import error
  - All operations logged to ~/.swarm/upgrade_log.jsonl

Usage:
    from packages.swarm.autonomous_upgrade import AutonomousUpgradeProtocol, UpgradeProposal

    protocol = AutonomousUpgradeProtocol(engine)
    proposal = UpgradeProposal(
        file_path="packages/swarm/pm.py",
        description="Increase DEBATE_THRESHOLD from 0.50 to 0.60",
        old_snippet="DEBATE_THRESHOLD = 0.50",
        new_snippet="DEBATE_THRESHOLD = 0.60",
        rationale="Agents suggested triggering debate less often to reduce latency",
        risk_level="low",
    )
    result = await protocol.run([proposal])
    print(result)
"""

from __future__ import annotations

import ast
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class UpgradeProposal:
    """One concrete code change to apply to the swarm codebase."""

    file_path: str           # relative to project root, e.g. "packages/swarm/pm.py"
    description: str         # human-readable summary
    old_snippet: str         # exact text to replace (empty = append to file)
    new_snippet: str         # replacement text
    rationale: str = ""      # why this change improves the swarm
    risk_level: str = "medium"  # "low" | "medium" | "high"
    proposed_by: str = "self_upgrade"


@dataclass
class BenchmarkResult:
    questions: list[str]
    success_rate: float   # fraction of decisions that returned a winner
    avg_score: float      # average winner_score
    avg_latency_ms: float
    passed_gate_rate: float  # fraction that passed confidence gate


@dataclass
class UpgradeResult:
    proposal_count: int
    backup_id: str
    applied: bool
    rolled_back: bool
    reason: str           # why applied/rolled_back
    benchmark_before: BenchmarkResult | None = None
    benchmark_after: BenchmarkResult | None = None
    validation_errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class AutonomousUpgradeProtocol:
    """
    Full lifecycle manager for swarm self-modifications.

    Wraps every change in: backup → validate → benchmark_before →
    apply → benchmark_after → commit_or_rollback.

    All destructive operations are reversible via the backup system.
    """

    # How much benchmark regression triggers auto-rollback
    REGRESSION_THRESHOLD = 0.10   # 10% drop in avg_score triggers rollback

    # Benchmark test questions (used before + after, same questions for fair comparison)
    BENCHMARK_QUESTIONS = [
        "Redis vs Postgres for storing user sessions in a web app?",
        "REST vs GraphQL for a mobile app API?",
        "JWT vs server sessions for authentication?",
        "Monolith vs microservices for a startup with 3 engineers?",
        "PostgreSQL vs MongoDB for a social network?",
    ]

    # Files that are allowed to be modified (safety boundary)
    ALLOWED_PATHS = {"packages/swarm/"}

    # IMMUTABLE FILES — the upgrade protocol can NEVER modify these.
    # kimi-k2 feedback: "if an agent modifies the rollback code itself,
    # the rollback won't work — debugging a live system that keeps
    # healing its own wounds shut."
    IMMUTABLE_FILES = {
        "packages/swarm/autonomous_upgrade.py",  # can't modify itself
        "packages/swarm/engine.py",               # core orchestrator
        "packages/swarm/__init__.py",             # public API surface
        "packages/swarm/agent_hive.py",           # hive examiner integrity
    }

    # KILL SWITCH — if this file exists, ALL upgrades are blocked.
    # External watchdog or human can create this file to halt everything.
    KILL_SWITCH_FILENAME = "KILL_SWITCH"

    def __init__(
        self,
        engine: Any,                  # SwarmEngine — imported lazily to avoid circular
        project_root: Path | None = None,
        data_dir: Path | None = None,
    ):
        self.engine = engine
        self.project_root = project_root or self._find_project_root()
        self.backup_dir = (data_dir or Path.home() / ".swarm") / "backups"
        self.log_path = (data_dir or Path.home() / ".swarm") / "upgrade_log.jsonl"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public: full protocol
    # ------------------------------------------------------------------

    async def run(self, proposals: list[UpgradeProposal]) -> UpgradeResult:
        """
        Run the full upgrade protocol for a list of proposals.

        Steps:
        1. Safety check — reject any proposals touching files outside ALLOWED_PATHS
        2. Validate syntax of all proposed changes
        3. Backup all affected files
        4. Benchmark before (skip for LOW risk)
        5. Apply all proposals
        6. Benchmark after (skip for LOW risk)
        7. Compare: if regression → rollback; else → commit (keep changes)
        """
        logger.info(
            "AutonomousUpgrade: starting protocol for {n} proposals",
            n=len(proposals),
        )

        validation_errors: list[str] = []

        # 0. Kill switch — external veto (human or watchdog can halt everything)
        kill_switch_path = (self.backup_dir.parent / self.KILL_SWITCH_FILENAME)
        if kill_switch_path.exists():
            reason = "KILL SWITCH ACTIVE — all upgrades halted. Remove ~/.swarm/KILL_SWITCH to re-enable."
            logger.error(reason)
            self._log_event("kill_switch", proposals, None, False, False, reason)
            return UpgradeResult(
                proposal_count=len(proposals),
                backup_id="",
                applied=False,
                rolled_back=False,
                reason=reason,
            )

        # 1. Safety check — allowed paths + immutable files
        for p in proposals:
            safe = any(p.file_path.startswith(allowed) for allowed in self.ALLOWED_PATHS)
            if not safe:
                err = f"BLOCKED: '{p.file_path}' is outside allowed paths {self.ALLOWED_PATHS}"
                validation_errors.append(err)
                logger.error(err)

            if p.file_path in self.IMMUTABLE_FILES:
                err = (
                    f"BLOCKED: '{p.file_path}' is IMMUTABLE — the upgrade protocol "
                    f"cannot modify its own safety infrastructure. "
                    f"(kimi-k2: 'if agents modify rollback code, rollback won't work')"
                )
                validation_errors.append(err)
                logger.error(err)

        if validation_errors:
            self._log_event("blocked", proposals, None, False, False, "\n".join(validation_errors))
            return UpgradeResult(
                proposal_count=len(proposals),
                backup_id="",
                applied=False,
                rolled_back=False,
                reason="Safety check failed: " + validation_errors[0],
                validation_errors=validation_errors,
            )

        # 2. Validate syntax
        for p in proposals:
            err = self._validate_syntax(p)
            if err:
                validation_errors.append(f"{p.file_path}: {err}")

        if validation_errors:
            self._log_event("syntax_error", proposals, None, False, False, "\n".join(validation_errors))
            return UpgradeResult(
                proposal_count=len(proposals),
                backup_id="",
                applied=False,
                rolled_back=False,
                reason="Syntax validation failed",
                validation_errors=validation_errors,
            )

        # 3. Backup
        backup_id = self._backup(proposals)
        logger.info("AutonomousUpgrade: backup created — {id}", id=backup_id)

        # 4. Determine risk level (use highest among proposals)
        max_risk = self._max_risk(proposals)
        needs_benchmark = max_risk in ("medium", "high")
        needs_approval = max_risk == "high"

        # 5. Benchmark before
        benchmark_before: BenchmarkResult | None = None
        if needs_benchmark:
            questions = self.BENCHMARK_QUESTIONS[:3] if max_risk == "medium" else self.BENCHMARK_QUESTIONS
            logger.info("AutonomousUpgrade: benchmarking BEFORE ({n} questions)...", n=len(questions))
            benchmark_before = await self._benchmark(questions)
            logger.info(
                "Before: score={s:.1f}  success={r:.0%}  gate={g:.0%}",
                s=benchmark_before.avg_score,
                r=benchmark_before.success_rate,
                g=benchmark_before.passed_gate_rate,
            )

        # 6. HIGH risk: output approval request and stop
        if needs_approval:
            summary = self._approval_summary(proposals, benchmark_before)
            self._log_event("approval_required", proposals, backup_id, False, False, summary)
            return UpgradeResult(
                proposal_count=len(proposals),
                backup_id=backup_id,
                applied=False,
                rolled_back=False,
                reason=f"HIGH risk — human approval required.\n{summary}",
                benchmark_before=benchmark_before,
            )

        # 7. Apply (audit log BEFORE apply — survives crashes)
        self._log_event("applying", proposals, backup_id, False, False,
                        f"About to apply {len(proposals)} changes. Backup: {backup_id}")
        apply_errors = self._apply_all(proposals)
        if apply_errors:
            logger.error("AutonomousUpgrade: apply failed — rolling back")
            self._rollback(backup_id, proposals)
            self._log_event("apply_error", proposals, backup_id, False, True, "\n".join(apply_errors))
            return UpgradeResult(
                proposal_count=len(proposals),
                backup_id=backup_id,
                applied=False,
                rolled_back=True,
                reason="Apply failed: " + apply_errors[0],
                validation_errors=apply_errors,
            )
        logger.info("AutonomousUpgrade: changes applied")

        # 8. Benchmark after
        benchmark_after: BenchmarkResult | None = None
        if needs_benchmark and benchmark_before:
            questions = self.BENCHMARK_QUESTIONS[:3] if max_risk == "medium" else self.BENCHMARK_QUESTIONS
            logger.info("AutonomousUpgrade: benchmarking AFTER...")
            benchmark_after = await self._benchmark(questions)
            logger.info(
                "After: score={s:.1f}  success={r:.0%}  gate={g:.0%}",
                s=benchmark_after.avg_score,
                r=benchmark_after.success_rate,
                g=benchmark_after.passed_gate_rate,
            )

            # 9. Compare: regressed?
            score_delta = benchmark_after.avg_score - benchmark_before.avg_score
            relative_regression = -score_delta / max(benchmark_before.avg_score, 1.0)

            if relative_regression > self.REGRESSION_THRESHOLD:
                logger.warning(
                    "AutonomousUpgrade: REGRESSION detected ({d:.1f} score drop = {r:.0%}) — rolling back",
                    d=score_delta, r=relative_regression,
                )
                self._rollback(backup_id, proposals)
                self._log_event("rollback_regression", proposals, backup_id, False, True,
                                f"Score dropped {score_delta:.1f} ({relative_regression:.0%})")
                return UpgradeResult(
                    proposal_count=len(proposals),
                    backup_id=backup_id,
                    applied=False,
                    rolled_back=True,
                    reason=f"Auto-rollback: score dropped {score_delta:.1f} ({relative_regression:.0%} regression)",
                    benchmark_before=benchmark_before,
                    benchmark_after=benchmark_after,
                )

            improvement = f"score +{score_delta:.1f}" if score_delta >= 0 else f"score {score_delta:.1f}"
            logger.info("AutonomousUpgrade: COMMITTED — {imp}", imp=improvement)
            self._log_event("committed", proposals, backup_id, True, False, improvement)

            return UpgradeResult(
                proposal_count=len(proposals),
                backup_id=backup_id,
                applied=True,
                rolled_back=False,
                reason=f"Applied. Benchmark: {improvement}",
                benchmark_before=benchmark_before,
                benchmark_after=benchmark_after,
            )

        # LOW risk (no benchmark): apply and commit
        self._log_event("committed_low_risk", proposals, backup_id, True, False, "LOW risk, no benchmark")
        return UpgradeResult(
            proposal_count=len(proposals),
            backup_id=backup_id,
            applied=True,
            rolled_back=False,
            reason="Applied (LOW risk — no benchmark required)",
        )

    def rollback_manual(self, backup_id: str, proposals: list[UpgradeProposal]) -> bool:
        """Manually trigger a rollback to a specific backup. Returns True on success."""
        return len(self._rollback(backup_id, proposals)) == 0

    def list_backups(self) -> list[dict]:
        """List all available backups with metadata."""
        backups = []
        for d in sorted(self.backup_dir.iterdir(), reverse=True):
            if d.is_dir():
                meta_path = d / "_meta.json"
                if meta_path.exists():
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            backups.append(json.load(f))
                    except (json.JSONDecodeError, OSError):
                        backups.append({"backup_id": d.name, "files": []})
        return backups

    # ------------------------------------------------------------------
    # Internal: validation
    # ------------------------------------------------------------------

    def _validate_syntax(self, proposal: UpgradeProposal) -> str | None:
        """
        Parse the new_snippet as Python. Returns error string or None.

        Also validates that old_snippet exists in the target file
        (so we don't silently fail to apply).
        """
        # Check old_snippet exists in file
        if proposal.old_snippet:
            target = self.project_root / proposal.file_path
            if target.exists():
                content = target.read_text(encoding="utf-8")
                if proposal.old_snippet not in content:
                    return f"old_snippet not found in {proposal.file_path}"

        # Try parsing the new_snippet as valid Python
        # Wrap in a dummy module context for partial snippets
        test_code = f"def _test():\n" + "\n".join(
            f"    {line}" for line in proposal.new_snippet.splitlines()
        )
        try:
            ast.parse(test_code)
        except SyntaxError as e:
            return f"SyntaxError in new_snippet: {e}"

        return None

    # ------------------------------------------------------------------
    # Internal: backup
    # ------------------------------------------------------------------

    def _backup(self, proposals: list[UpgradeProposal]) -> str:
        """Copy all affected files to a timestamped backup directory."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        backup_path = self.backup_dir / ts
        backup_path.mkdir(parents=True, exist_ok=True)

        backed_up: list[str] = []
        for p in proposals:
            src = self.project_root / p.file_path
            if src.exists():
                dst = backup_path / p.file_path.replace("/", "_").replace("\\", "_")
                shutil.copy2(src, dst)
                backed_up.append(p.file_path)

        # Write backup metadata
        meta = {
            "backup_id": ts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "files": backed_up,
            "proposals": [
                {
                    "file": p.file_path,
                    "description": p.description,
                    "risk": p.risk_level,
                }
                for p in proposals
            ],
        }
        with open(backup_path / "_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        return ts

    def _rollback(self, backup_id: str, proposals: list[UpgradeProposal]) -> list[str]:
        """Restore files from backup. Returns list of errors (empty = success)."""
        backup_path = self.backup_dir / backup_id
        errors: list[str] = []

        for p in proposals:
            src_name = p.file_path.replace("/", "_").replace("\\", "_")
            src = backup_path / src_name
            if src.exists():
                dst = self.project_root / p.file_path
                try:
                    shutil.copy2(src, dst)
                    logger.info("Rollback: restored {f}", f=p.file_path)
                except OSError as e:
                    errors.append(f"Could not restore {p.file_path}: {e}")
            else:
                errors.append(f"Backup file not found for {p.file_path}")

        return errors

    # ------------------------------------------------------------------
    # Internal: apply
    # ------------------------------------------------------------------

    def _apply_all(self, proposals: list[UpgradeProposal]) -> list[str]:
        """Apply all proposals. Returns list of errors."""
        errors: list[str] = []
        for p in proposals:
            err = self._apply_one(p)
            if err:
                errors.append(err)
                break  # stop on first error, caller will rollback
        return errors

    def _apply_one(self, proposal: UpgradeProposal) -> str | None:
        """Apply a single proposal. Returns error string or None."""
        target = self.project_root / proposal.file_path
        if not target.exists():
            return f"File not found: {proposal.file_path}"

        try:
            content = target.read_text(encoding="utf-8")

            if proposal.old_snippet:
                if proposal.old_snippet not in content:
                    return f"old_snippet not found in {proposal.file_path} (already applied?)"
                new_content = content.replace(proposal.old_snippet, proposal.new_snippet, 1)
            else:
                # Append mode
                new_content = content + "\n" + proposal.new_snippet

            target.write_text(new_content, encoding="utf-8")
            logger.info("Applied: {desc} → {f}", desc=proposal.description[:60], f=proposal.file_path)
            return None

        except OSError as e:
            return f"Write error for {proposal.file_path}: {e}"

    # ------------------------------------------------------------------
    # Internal: benchmark
    # ------------------------------------------------------------------

    async def _benchmark(self, questions: list[str]) -> BenchmarkResult:
        """Run N quick decisions and collect performance metrics."""
        from .types import SwarmConfig, StakesLevel

        successes = 0
        scores: list[float] = []
        latencies: list[float] = []
        gates: list[bool] = []

        for q in questions:
            try:
                report = await self.engine.quick_decide(q, stakes="low")
                if report.winner:
                    successes += 1
                    scores.append(report.winner_score)
                    latencies.append(float(report.total_latency_ms))
                    gates.append(report.passed_confidence_gate)
            except Exception as e:
                logger.warning("Benchmark question failed: {e}", e=str(e)[:100])

        n = len(questions)
        return BenchmarkResult(
            questions=questions,
            success_rate=successes / max(n, 1),
            avg_score=sum(scores) / max(len(scores), 1),
            avg_latency_ms=sum(latencies) / max(len(latencies), 1),
            passed_gate_rate=sum(gates) / max(len(gates), 1),
        )

    # ------------------------------------------------------------------
    # Internal: helpers
    # ------------------------------------------------------------------

    def _max_risk(self, proposals: list[UpgradeProposal]) -> str:
        order = {"low": 0, "medium": 1, "high": 2}
        return max(proposals, key=lambda p: order.get(p.risk_level, 1)).risk_level

    def _approval_summary(
        self,
        proposals: list[UpgradeProposal],
        benchmark_before: BenchmarkResult | None,
    ) -> str:
        lines = [
            "=" * 55,
            " AUTONOMOUS UPGRADE — HUMAN APPROVAL REQUIRED",
            f" Risk level: HIGH  |  {len(proposals)} proposals",
            "=" * 55,
        ]
        for i, p in enumerate(proposals, 1):
            lines.append(f"\n[{i}] {p.description}")
            lines.append(f"    File: {p.file_path}")
            lines.append(f"    Rationale: {p.rationale[:120]}")
        if benchmark_before:
            lines.append(f"\nCurrent benchmark: score={benchmark_before.avg_score:.1f}  "
                         f"success={benchmark_before.success_rate:.0%}")
        lines.append("\nTo apply: call protocol.rollback_manual() if you change your mind after applying.")
        lines.append("=" * 55)
        return "\n".join(lines)

    def _log_event(
        self,
        event: str,
        proposals: list[UpgradeProposal],
        backup_id: str | None,
        applied: bool,
        rolled_back: bool,
        notes: str,
    ) -> None:
        record = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backup_id": backup_id or "",
            "applied": applied,
            "rolled_back": rolled_back,
            "proposals": [
                {"file": p.file_path, "description": p.description, "risk": p.risk_level}
                for p in proposals
            ],
            "notes": notes[:500],
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        except OSError:
            pass

    @staticmethod
    def _find_project_root() -> Path:
        """Walk up from this file to find the project root (contains packages/)."""
        current = Path(__file__).parent
        for _ in range(5):
            if (current / "packages").exists():
                return current
            current = current.parent
        return Path.cwd()
