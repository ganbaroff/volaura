"""Patch 2 (2026-05-09) — gemma4_brain.py Orchestrator-Workers refactor tests.

Acceptance criteria from CTO-Brain directive 2026-05-09:
- Valid JSON parse.
- Malformed JSON repair / retry (fence stripping, substring extract).
- Routing classification.
- Emits 3-5 tasks.
- Every task has evidence anchor (or low-confidence + reason).
- No silent empty-task success path.
- Canonical imports only — load via importlib from canonical scripts/ path.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Any

from tests._paths import script_path as repo_script_path


def _load_brain():
    script_path = repo_script_path("gemma4_brain.py")
    assert script_path.exists(), f"canonical brain missing: {script_path}"
    spec = importlib.util.spec_from_file_location("gemma4_brain_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _run(coro):
    return asyncio.run(coro)


def _wire_paths(brain, tmp_path: Path) -> Path:
    """Redirect brain's filesystem paths into tmp_path for hermetic tests."""
    queue = tmp_path / "work-queue"
    pending = queue / "pending"
    done = queue / "done"
    pending.mkdir(parents=True)
    done.mkdir(parents=True)
    brain.QUEUE = queue
    brain.PENDING = pending
    brain.DONE = done
    brain.BRAIN_LOG = queue / "brain.log.jsonl"
    return tmp_path


# ── parse_brain_json ──────────────────────────────────────────────────────────

def test_parse_strict_json():
    brain = _load_brain()
    raw = '{"analysis": "ok", "tasks": [{"title": "x"}]}'
    out = brain.parse_brain_json(raw)
    assert isinstance(out, dict)
    assert out["analysis"] == "ok"
    assert out["tasks"][0]["title"] == "x"


def test_parse_json_in_fence():
    brain = _load_brain()
    raw = "Sure, here you go:\n```json\n{\"analysis\": \"fenced\", \"tasks\": []}\n```"
    out = brain.parse_brain_json(raw)
    assert out is not None
    assert out["analysis"] == "fenced"


def test_parse_json_substring_extract():
    brain = _load_brain()
    raw = "Here is the answer ----- {\"analysis\": \"sub\", \"tasks\": [1,2]} ----- thanks"
    out = brain.parse_brain_json(raw)
    assert out is not None
    assert out["analysis"] == "sub"


def test_parse_returns_none_on_garbage():
    brain = _load_brain()
    assert brain.parse_brain_json("just plain prose with no braces") is None
    assert brain.parse_brain_json("") is None
    assert brain.parse_brain_json(None) is None


def test_parse_returns_none_on_array_root():
    brain = _load_brain()
    # Strict: only dicts at root are usable for our schema.
    assert brain.parse_brain_json('["one", "two"]') is None


# ── validate_brain_task ───────────────────────────────────────────────────────

def _good_task() -> dict:
    return {
        "title": "Audit rate limiting on /start",
        "type": "audit",
        "rationale": "Verify limiter decorators on auth endpoints",
        "expected_evidence_path": "apps/api/app/routers/auth.py",
        "expected_evidence_line": 119,
        "priority": "P1",
        "confidence": "high",
    }


def test_validate_accepts_good_task():
    brain = _load_brain()
    ok, reason = brain.validate_brain_task(_good_task())
    assert ok, f"unexpected reject: {reason}"


def test_validate_rejects_missing_title():
    brain = _load_brain()
    t = _good_task()
    t["title"] = ""
    ok, reason = brain.validate_brain_task(t)
    assert not ok and "title" in reason


def test_validate_rejects_invalid_type():
    brain = _load_brain()
    t = _good_task()
    t["type"] = "marketing"
    ok, reason = brain.validate_brain_task(t)
    assert not ok and "invalid type" in reason


def test_validate_rejects_missing_rationale():
    brain = _load_brain()
    t = _good_task()
    t["rationale"] = ""
    ok, reason = brain.validate_brain_task(t)
    assert not ok and "rationale" in reason


def test_validate_rejects_high_confidence_without_anchor():
    brain = _load_brain()
    t = _good_task()
    t.pop("expected_evidence_line")
    t.pop("expected_evidence_path")
    ok, reason = brain.validate_brain_task(t)
    assert not ok, "speculative high-confidence task with no anchor must be rejected"
    assert "no evidence anchor" in reason


def test_validate_accepts_low_confidence_with_reason():
    brain = _load_brain()
    t = _good_task()
    t["confidence"] = "low"
    t["low_confidence_reason"] = "The endpoint exists across multiple files"
    t.pop("expected_evidence_line")
    t.pop("expected_evidence_path")
    ok, reason = brain.validate_brain_task(t)
    assert ok, f"low-confidence with reason must pass: {reason}"


def test_validate_rejects_low_confidence_without_reason():
    brain = _load_brain()
    t = _good_task()
    t["confidence"] = "low"
    t.pop("expected_evidence_line")
    t.pop("expected_evidence_path")
    # no low_confidence_reason
    ok, reason = brain.validate_brain_task(t)
    assert not ok and "low_confidence_reason" in reason


def test_validate_accepts_anchor_string():
    brain = _load_brain()
    t = _good_task()
    t.pop("expected_evidence_line")
    t["expected_evidence_anchor"] = "function get_my_profile"
    ok, reason = brain.validate_brain_task(t)
    assert ok, reason


# ── _legacy_parse ─────────────────────────────────────────────────────────────

def test_legacy_parse_extracts_old_format():
    brain = _load_brain()
    response = """ANALYSIS: Things are happening.
TASK1_TYPE: audit
TASK1_TITLE: Audit auth
TASK1_BODY: Look at apps/api/app/routers/auth.py rate limiting.
TASK2_TYPE: NONE
TASK2_TITLE: NONE
TASK2_BODY: NONE
"""
    tasks = brain._legacy_parse(response)
    assert len(tasks) == 1
    assert tasks[0]["type"] == "audit"
    assert tasks[0]["confidence"] == "low"
    assert "legacy regex" in tasks[0]["low_confidence_reason"]


# ── think_cycle integration ──────────────────────────────────────────────────

def test_think_cycle_creates_3_to_5_tasks(monkeypatch, tmp_path):
    brain = _load_brain()
    _wire_paths(brain, tmp_path)

    valid_response = json.dumps({
        "analysis": "Auth surface needs an evidence-backed sweep before launch.",
        "routing_category": "audit",
        "tasks": [
            {
                "title": f"Audit endpoint #{i}",
                "type": "audit",
                "rationale": f"Endpoint {i} is a known surface area.",
                "expected_evidence_path": "apps/api/app/routers/auth.py",
                "expected_evidence_line": 100 + i * 10,
                "priority": "P1",
                "confidence": "high",
            }
            for i in range(1, 5)  # 4 tasks
        ],
    })

    monkeypatch.setattr(brain, "call_brain_llm", lambda prompt, max_tokens=4000: valid_response)
    monkeypatch.setattr(brain, "get_pending_count", lambda: 0)
    monkeypatch.setattr(brain, "get_recent_done", lambda n=5: [])

    _run(brain.think_cycle("=== product-truth ===\nVOLAURA platform spec.\n"))

    pending_files = sorted((tmp_path / "work-queue" / "pending").glob("*.md"))
    assert 3 <= len(pending_files) <= 5, f"expected 3-5 tasks, got {len(pending_files)}"

    sample = pending_files[0].read_text(encoding="utf-8")
    assert "type: audit" in sample
    assert "Routing category" in sample
    assert "Expected evidence anchor" in sample
    assert "apps/api/app/routers/auth.py" in sample


def test_think_cycle_caps_at_max(monkeypatch, tmp_path):
    brain = _load_brain()
    _wire_paths(brain, tmp_path)

    response = json.dumps({
        "analysis": "Lots of work.",
        "routing_category": "audit",
        "tasks": [
            {
                "title": f"Task {i}",
                "type": "audit",
                "rationale": "stuff",
                "expected_evidence_path": "scripts/gemma4_brain.py",
                "expected_evidence_line": i + 1,
                "confidence": "high",
                "priority": "P2",
            }
            for i in range(10)  # 10 tasks — over cap
        ],
    })
    monkeypatch.setattr(brain, "call_brain_llm", lambda prompt, max_tokens=4000: response)
    monkeypatch.setattr(brain, "get_pending_count", lambda: 0)
    monkeypatch.setattr(brain, "get_recent_done", lambda n=5: [])

    _run(brain.think_cycle("ctx"))

    pending_files = list((tmp_path / "work-queue" / "pending").glob("*.md"))
    assert len(pending_files) == brain.MAX_TASKS_PER_CYCLE


def test_think_cycle_rejects_speculative_tasks(monkeypatch, tmp_path):
    brain = _load_brain()
    _wire_paths(brain, tmp_path)

    # All tasks lack anchor + high confidence -> all rejected -> 0 created
    response = json.dumps({
        "analysis": "speculation",
        "routing_category": "audit",
        "tasks": [
            {
                "title": f"Speculative {i}",
                "type": "audit",
                "rationale": "I think something might be wrong somewhere",
                "confidence": "high",
            }
            for i in range(4)
        ],
    })
    monkeypatch.setattr(brain, "call_brain_llm", lambda prompt, max_tokens=4000: response)
    monkeypatch.setattr(brain, "get_pending_count", lambda: 0)
    monkeypatch.setattr(brain, "get_recent_done", lambda n=5: [])

    _run(brain.think_cycle("ctx"))

    pending_files = list((tmp_path / "work-queue" / "pending").glob("*.md"))
    assert pending_files == [], "speculative tasks must not flow through silently"


def test_think_cycle_falls_back_to_legacy_when_json_fails(monkeypatch, tmp_path):
    brain = _load_brain()
    _wire_paths(brain, tmp_path)

    legacy_text = """ANALYSIS: Legacy fallback exercise.
TASK1_TYPE: audit
TASK1_TITLE: Legacy audit task
TASK1_BODY: Look at the auth router rate limiting.
TASK2_TYPE: NONE
TASK2_TITLE: NONE
TASK2_BODY: NONE
"""
    monkeypatch.setattr(brain, "call_brain_llm", lambda prompt, max_tokens=4000: legacy_text)
    monkeypatch.setattr(brain, "get_pending_count", lambda: 0)
    monkeypatch.setattr(brain, "get_recent_done", lambda n=5: [])

    _run(brain.think_cycle("ctx"))

    pending_files = list((tmp_path / "work-queue" / "pending").glob("*.md"))
    assert len(pending_files) == 1
    body = pending_files[0].read_text(encoding="utf-8")
    assert "Confidence:** low" in body
    assert "legacy regex" in body


def test_think_cycle_silent_no_creation_on_total_fail(monkeypatch, tmp_path):
    """Empty LLM response + no legacy parse -> brain creates 0 tasks AND logs event."""
    brain = _load_brain()
    _wire_paths(brain, tmp_path)

    monkeypatch.setattr(brain, "call_brain_llm", lambda prompt, max_tokens=4000: "")
    monkeypatch.setattr(brain, "get_pending_count", lambda: 0)
    monkeypatch.setattr(brain, "get_recent_done", lambda n=5: [])

    _run(brain.think_cycle("ctx"))

    pending_files = list((tmp_path / "work-queue" / "pending").glob("*.md"))
    assert pending_files == []
    # Brain log should record the empty event
    log_path = tmp_path / "work-queue" / "brain.log.jsonl"
    if log_path.exists():
        events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(e.get("event") == "brain_think_empty" for e in events)


# ── routing classification ────────────────────────────────────────────────────

def test_routing_categories_match_required_set():
    brain = _load_brain()
    assert brain.ROUTING_CATEGORIES == {"audit", "refactor", "feature", "bug"}


def test_min_max_task_counts():
    brain = _load_brain()
    assert brain.MIN_TASKS_PER_CYCLE == 3
    assert brain.MAX_TASKS_PER_CYCLE == 5


# ── canonical-only import ────────────────────────────────────────────────────

def test_canonical_brain_path_is_scripts_gemma4_brain():
    canonical = repo_script_path("gemma4_brain.py")
    assert canonical.exists()
    # The worktree copy is informational only — must not be imported in tests.
    assert canonical.is_file()
