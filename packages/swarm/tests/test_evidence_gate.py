"""Tests for the evidence-gate (Session 121, 2026-04-19).

Kills the "narrative-headline without proof" failure mode by downgrading
findings that lack real file paths or observable evidence.
"""
from __future__ import annotations

import pytest

from packages.swarm.contracts import (
    Category,
    FindingContract,
    Impact,
    Severity,
)
from packages.swarm.coordinator import _validate_evidence


def _make(
    *,
    summary: str = "Something is broken in the assessment router",
    recommendation: str = "Fix the broken thing by doing X",
    files: list[str] | None = None,
    evidence: str = "",
    severity: Severity = Severity.P0,
    confidence: float = 0.9,
) -> FindingContract:
    return FindingContract(
        severity=severity,
        category=Category.PRODUCT,
        files=files if files is not None else [],
        summary=summary,
        recommendation=recommendation,
        confidence=confidence,
        est_impact=Impact.HIGH,
        evidence=evidence,
        agent_id="test-agent",
        task_id="test-task",
        run_id="test-run",
    )


class TestEvidenceGate:
    def test_empty_evidence_and_empty_files_downgrades_to_info(self):
        finding = _make(evidence="", files=[])
        out = _validate_evidence(finding)
        assert out.severity == Severity.INFO
        assert out.confidence <= 0.3
        assert out.summary.startswith("⚠ UNVERIFIED")

    def test_short_evidence_below_20_chars_fails(self):
        finding = _make(evidence="too short", files=["packages/swarm/coordinator.py"])
        out = _validate_evidence(finding)
        assert out.severity == Severity.INFO
        assert "no evidence" in out.summary

    def test_bogus_file_paths_downgrade(self):
        finding = _make(
            evidence="grep result: line 42 says 'foo' — clearly demonstrates the bug",
            files=["src/does_not_exist.py", "foo/bar.ts"],
        )
        out = _validate_evidence(finding)
        assert out.severity == Severity.INFO
        assert "0/2 files exist" in out.summary

    def test_valid_finding_passes_through_unchanged(self):
        # Use a path that actually exists in this repo
        finding = _make(
            evidence="grep -n 'FindingContract' returned: line 44 of contracts.py shows class definition with severity enum",
            files=["packages/swarm/contracts.py"],
        )
        out = _validate_evidence(finding)
        assert out.severity == Severity.P0
        assert out.confidence == 0.9
        assert not out.summary.startswith("⚠ UNVERIFIED")

    def test_partial_real_files_passes(self):
        # At least one real path → passes
        finding = _make(
            evidence="file existence check: packages/swarm/contracts.py confirmed; docs/nonexistent.md is a speculative future addition",
            files=["packages/swarm/contracts.py", "docs/nonexistent.md"],
        )
        out = _validate_evidence(finding)
        # files[] validation passes because AT LEAST ONE file exists
        assert out.severity == Severity.P0
        assert not out.summary.startswith("⚠ UNVERIFIED")

    def test_both_failures_compose(self):
        finding = _make(evidence="", files=["missing.py"])
        out = _validate_evidence(finding)
        assert out.severity == Severity.INFO
        assert "no evidence" in out.summary
        assert "0/1 files exist" in out.summary
