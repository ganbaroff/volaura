from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


SCRIPT = Path("C:/Projects/VOLAURA/scripts/run_openmanus_hands_task.py")


def load_sidecar():
    spec = importlib.util.spec_from_file_location("openmanus_hands_sidecar", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_load_task_requires_instruction():
    sidecar = load_sidecar()
    args = argparse.Namespace(
        task=None,
        instruction=None,
        mode=None,
        task_id=None,
        max_seconds=None,
    )

    try:
        sidecar.load_task(None, args)
    except ValueError as exc:
        assert "instruction" in str(exc)
    else:
        raise AssertionError("Expected missing instruction to fail")


def test_load_task_defaults_to_browser_observe_tools():
    sidecar = load_sidecar()
    args = argparse.Namespace(
        task=None,
        instruction="Open example.com and report the title.",
        mode=None,
        task_id="test-hands",
        max_seconds=None,
    )

    task = sidecar.load_task(None, args)

    assert task["mode"] == "browser_observe"
    assert task["allowed_tools"] == ["browser_use", "terminate"]
    assert task["task_id"] == "test-hands"


def test_build_guarded_prompt_blocks_posting_and_git():
    sidecar = load_sidecar()
    task = {
        "task_id": "x",
        "mode": "browser_observe",
        "instruction": "Open https://example.com.",
        "allowed_tools": ["browser_use", "terminate"],
        "allowed_domains": ["example.com"],
        "allowed_paths": [],
    }

    prompt = sidecar.build_guarded_prompt(task)

    assert "Never publish, post, send, schedule" in prompt
    assert "Never run git commands" in prompt
    assert "example.com" in prompt
    assert "browser_use, terminate" in prompt


def test_filter_agent_tools_removes_ask_human_and_unlisted_tools():
    sidecar = load_sidecar()

    class Tool:
        def __init__(self, name: str):
            self.name = name

    class Collection:
        def __init__(self):
            self.tools = (
                Tool("browser_use"),
                Tool("ask_human"),
                Tool("str_replace_editor"),
                Tool("terminate"),
            )
            self.tool_map = {tool.name: tool for tool in self.tools}

    class Agent:
        available_tools = Collection()

    kept = sidecar.filter_agent_tools(Agent(), {"browser_use", "terminate"})

    assert kept == ["browser_use", "terminate"]
    assert "ask_human" not in Agent.available_tools.tool_map
    assert "str_replace_editor" not in Agent.available_tools.tool_map


def test_resolve_output_dir_defaults_to_hands_runs():
    sidecar = load_sidecar()

    out = sidecar.resolve_output_dir({"task_id": "abc"}, None)

    assert out == Path("C:/Projects/VOLAURA/memory/atlas/hands-runs/abc")
