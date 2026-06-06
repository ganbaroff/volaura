"""Tests for OpenManus hands sidecar observation verifier (CEO directive 2026-05-09).

Goal: prove that a Manus agent which terminates without touching any of the
cited files gets flipped from "success" to "failed: required_files_not_observed",
NOT silently reported as success.

Reference: codex-loop.md «не давать рукам врать».
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from tests._paths import script_path as repo_script_path


def _load_sidecar():
    script = repo_script_path("run_openmanus_hands_task.py")
    spec = importlib.util.spec_from_file_location("run_openmanus_hands_task_v", script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


# ── verify_observation ───────────────────────────────────────────────────────

def test_pass_when_no_observation_verb():
    """Tasks that don't explicitly require observation should not need to
    prove file touches (e.g. content_draft tasks reasoning from prompt only)."""
    sc = _load_sidecar()
    task = {"instruction": "Write a haiku about snow.", "mode": "content_draft"}
    ok, reason = sc.verify_observation(task, [])
    assert ok and reason == ""


def test_fail_when_read_instruction_but_empty_trace():
    """The exact prior-session bug: instruction says 'read 3 result.json' but
    trace is empty (terminate-only). Must flip to failed."""
    sc = _load_sidecar()
    task = {"instruction": "Read the 3 most recent result.json files in done/.", "mode": "file_observe"}
    ok, reason = sc.verify_observation(task, [])
    assert not ok
    assert "required_files_not_observed" in reason


def test_fail_when_only_terminate_in_trace():
    """terminate is bookkeeping not work. Trace with only terminate counts as
    zero observations even though trace is non-empty."""
    sc = _load_sidecar()
    task = {"instruction": "Open and inspect file X."}
    trace = [{"tool": "terminate", "args_excerpt": "{...}"}]
    ok, reason = sc.verify_observation(task, trace)
    assert not ok
    assert "required_files_not_observed" in reason


def test_pass_when_str_replace_editor_in_trace():
    sc = _load_sidecar()
    task = {"instruction": "Read the file X."}
    trace = [
        {"tool": "str_replace_editor", "args_excerpt": "view path=X"},
        {"tool": "terminate", "args_excerpt": "{...}"},
    ]
    ok, reason = sc.verify_observation(task, trace)
    assert ok and reason == ""


def test_pass_when_browser_use_in_trace():
    sc = _load_sidecar()
    task = {"instruction": "Open and review https://example.com."}
    trace = [
        {"tool": "browser_use", "args_excerpt": "navigate https://example.com"},
        {"tool": "terminate", "args_excerpt": "{...}"},
    ]
    ok, _ = sc.verify_observation(task, trace)
    assert ok


def test_pass_when_python_execute_in_trace():
    sc = _load_sidecar()
    task = {"instruction": "Inspect logs by running a script."}
    trace = [
        {"tool": "python_execute", "args_excerpt": "code=print('x')"},
        {"tool": "terminate", "args_excerpt": "{...}"},
    ]
    ok, _ = sc.verify_observation(task, trace)
    assert ok


def test_skip_observation_verifier_opt_out():
    """Operator can opt out via task['skip_observation_verifier']=True for
    cases where success doesn't depend on file observation."""
    sc = _load_sidecar()
    task = {
        "instruction": "Read file X.",
        "skip_observation_verifier": True,
    }
    ok, reason = sc.verify_observation(task, [])
    assert ok and reason == ""


def test_observation_verbs_in_russian_dont_trigger_yet():
    """Current verb list is English-only. Russian instruction without English
    verb passes through (no requirement). This is a known limitation —
    reviewer can extend list later. Test documents current behaviour."""
    sc = _load_sidecar()
    task = {"instruction": "Прочитай 3 файла и напиши summary."}
    ok, _ = sc.verify_observation(task, [])
    # Currently passes because no English verb. Test exists to catch when
    # someone later extends _OBSERVATION_VERBS — they should add Russian
    # equivalents AND update this test.
    assert ok  # CHANGE WHEN _OBSERVATION_VERBS gains 'прочитай' / 'открой' etc.


def test_extract_tool_call_trace_handles_missing_memory():
    """A degenerate agent without memory.messages should return empty trace
    (and verifier will then flag the task failed if observation required)."""
    sc = _load_sidecar()

    class _AgentNoMemory:
        pass

    trace = sc._extract_tool_call_trace(_AgentNoMemory())
    assert trace == []


def test_extract_tool_call_trace_extracts_tool_names():
    """Synthetic agent with messages → trace contains tool names + args."""
    sc = _load_sidecar()

    class _Fn:
        def __init__(self, name, args):
            self.name = name
            self.arguments = args

    class _ToolCall:
        def __init__(self, name, args):
            self.function = _Fn(name, args)

    class _Msg:
        def __init__(self, calls):
            self.tool_calls = calls

    class _Memory:
        def __init__(self, msgs):
            self.messages = msgs

    class _Agent:
        def __init__(self):
            self.memory = _Memory([
                _Msg([_ToolCall("str_replace_editor", '{"command": "view", "path": "/x"}')]),
                _Msg([_ToolCall("terminate", '{"status": "success"}')]),
            ])

    trace = sc._extract_tool_call_trace(_Agent())
    tools = [e["tool"] for e in trace]
    assert tools == ["str_replace_editor", "terminate"]
    assert "view" in trace[0]["args_excerpt"]
