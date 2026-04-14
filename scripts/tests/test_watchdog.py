"""Tests for scheduled_workflow_watchdog.py.

Locks the consecutive-failure count logic — the whole point of the watchdog is
that 2 in a row triggers an alert, 1 does not, and a success after fails
resets the count.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load watchdog module by direct file path (same pattern the watchdog itself
# uses to load notifier.py, for the same reason: no heavy deps on scripts/).
_SCRIPT = Path(__file__).resolve().parents[1] / "scheduled_workflow_watchdog.py"
_spec = importlib.util.spec_from_file_location("watchdog_under_test", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)

# Stub out the notifier import path before the module executes its top-level
# importlib.util call against notifier.py. Without this, loading the module in
# a test runner can pull the real notifier and touch real files.
_NOTIFIER_STUB = Path(__file__).resolve().parents[1].parent / "packages" / "swarm" / "notifier.py"
assert _NOTIFIER_STUB.exists(), "notifier.py must exist for watchdog import"

_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

_consecutive_failures = _mod._consecutive_failures


def test_no_runs_zero():
    assert _consecutive_failures([]) == 0


def test_one_success_zero():
    assert _consecutive_failures([{"conclusion": "success"}]) == 0


def test_one_failure_one():
    assert _consecutive_failures([{"conclusion": "failure"}]) == 1


def test_two_failures_two():
    runs = [{"conclusion": "failure"}, {"conclusion": "failure"}]
    assert _consecutive_failures(runs) == 2


def test_three_failures_three():
    runs = [{"conclusion": "failure"}] * 3
    assert _consecutive_failures(runs) == 3


def test_failure_then_success_counts_only_the_fresh_failure():
    """Latest first. Failure at index 0, success at index 1 → only 1 consecutive."""
    runs = [{"conclusion": "failure"}, {"conclusion": "success"}, {"conclusion": "failure"}]
    assert _consecutive_failures(runs) == 1


def test_success_at_head_stops_count_even_if_older_failed():
    runs = [{"conclusion": "success"}, {"conclusion": "failure"}, {"conclusion": "failure"}]
    assert _consecutive_failures(runs) == 0


def test_cancelled_does_not_count_as_failure():
    """Only `conclusion == 'failure'` counts. Cancelled / timed_out / skipped
    should NOT trigger the alert — they're often manual aborts, not bugs."""
    runs = [{"conclusion": "cancelled"}, {"conclusion": "failure"}]
    assert _consecutive_failures(runs) == 0


def test_missing_conclusion_treated_as_not_failure():
    runs = [{}, {"conclusion": "failure"}]
    assert _consecutive_failures(runs) == 0


def test_threshold_gate_matches_spec():
    """Alert threshold is 2 — verify the module constant did not drift."""
    assert _mod.MIN_CONSECUTIVE_FAILS == 2
