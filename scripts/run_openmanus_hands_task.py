"""OpenManus sidecar runner for Atlas hands tasks.

This is the safe doorway between the Atlas swarm and OpenManus.
It runs outside the daemon, writes a structured result file, and keeps
posting / git / broad project work out of the first integration layer.
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import sys
import time
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPENMANUS_ROOT = Path(os.getenv("OPENMANUS_ROOT", "C:/Projects/OpenManus"))
DEFAULT_RUNS_DIR = REPO_ROOT / "memory" / "atlas" / "hands-runs"

MODE_TOOL_DEFAULTS: dict[str, set[str]] = {
    "browser_observe": {"browser_use", "terminate"},
    "file_observe": {"str_replace_editor", "terminate"},
    "content_draft": {"str_replace_editor", "python_execute", "terminate"},
    "research": {"browser_use", "str_replace_editor", "terminate"},
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_task(task_path: Path | None, args: argparse.Namespace) -> dict[str, Any]:
    task: dict[str, Any] = {}
    if task_path:
        task = json.loads(task_path.read_text(encoding="utf-8"))

    if args.instruction:
        task["instruction"] = args.instruction
    if args.mode:
        task["mode"] = args.mode
    if args.task_id:
        task["task_id"] = args.task_id
    if args.max_seconds:
        task["max_seconds"] = args.max_seconds

    task.setdefault("task_id", f"hands-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}")
    task.setdefault("mode", "browser_observe")
    task.setdefault("max_seconds", 180)
    task.setdefault("allowed_domains", [])
    task.setdefault("allowed_paths", [])

    if not task.get("instruction"):
        raise ValueError("Task requires an instruction")
    if task["mode"] not in MODE_TOOL_DEFAULTS:
        raise ValueError(f"Unknown mode: {task['mode']}")

    requested_tools = task.get("allowed_tools")
    if requested_tools:
        task["allowed_tools"] = sorted(set(requested_tools) & MODE_TOOL_DEFAULTS[task["mode"]])
    else:
        task["allowed_tools"] = sorted(MODE_TOOL_DEFAULTS[task["mode"]])
    if "terminate" not in task["allowed_tools"]:
        task["allowed_tools"].append("terminate")

    return task


def resolve_output_dir(task: dict[str, Any], out_dir_arg: str | None) -> Path:
    if out_dir_arg:
        return Path(out_dir_arg)
    if task.get("output_dir"):
        return Path(str(task["output_dir"]))
    return DEFAULT_RUNS_DIR / str(task["task_id"])


def build_guarded_prompt(task: dict[str, Any]) -> str:
    allowed_domains = task.get("allowed_domains") or []
    allowed_paths = task.get("allowed_paths") or []
    allowed_tools = task.get("allowed_tools") or []

    domain_rule = (
        "Allowed domains: " + ", ".join(allowed_domains)
        if allowed_domains
        else "Do not browse the web unless the instruction explicitly names a URL."
    )
    path_rule = (
        "Allowed file paths: " + ", ".join(allowed_paths)
        if allowed_paths
        else "Do not edit files. Read only when the task explicitly requires it."
    )

    return f"""You are Atlas Hands running through the OpenManus sidecar.

TASK ID: {task['task_id']}
MODE: {task['mode']}
ALLOWED TOOLS: {', '.join(allowed_tools)}

INSTRUCTION:
{task['instruction']}

HARD RULES:
1. Do only this task. Do not widen the mission.
2. Never publish, post, send, schedule, purchase, deploy, or message anyone.
3. Never run git commands: no checkout, pull, fetch, rebase, merge, cherry-pick, stash, reset, commit, push.
4. Never ask the human. Use the available context and tools.
5. {domain_rule}
6. {path_rule}
7. If you cannot complete the task safely, terminate with status="failure" and explain briefly.
8. When done, terminate with status="success" and a short Russian summary.
"""


def filter_agent_tools(agent: Any, allowed_tool_names: set[str]) -> list[str]:
    """Remove tools outside the sidecar allowlist from a Manus agent."""
    collection = agent.available_tools
    kept = tuple(tool for tool in collection.tools if tool.name in allowed_tool_names)
    collection.tools = kept
    collection.tool_map = {tool.name: tool for tool in kept}
    return sorted(collection.tool_map)


async def run_openmanus(task: dict[str, Any], openmanus_root: Path) -> str:
    if not openmanus_root.exists():
        raise FileNotFoundError(f"OpenManus root not found: {openmanus_root}")
    if str(openmanus_root) not in sys.path:
        sys.path.insert(0, str(openmanus_root))

    from app.agent.manus import Manus  # type: ignore

    prompt = build_guarded_prompt(task)
    agent = await Manus.create()
    filter_agent_tools(agent, set(task["allowed_tools"]))
    try:
        return await asyncio.wait_for(
            agent.run(prompt),
            timeout=float(task.get("max_seconds", 180)),
        )
    finally:
        with contextlib.suppress(Exception):
            await agent.cleanup()


async def execute_task(task: dict[str, Any], out_dir: Path, openmanus_root: Path) -> dict[str, Any]:
    started = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "task.json").write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")

    result: dict[str, Any] = {
        "task_id": task["task_id"],
        "mode": task["mode"],
        "status": "running",
        "started_at": utc_now(),
        "openmanus_root": str(openmanus_root),
        "output_dir": str(out_dir),
    }
    try:
        run_text = await run_openmanus(task, openmanus_root)
        result.update({
            "status": "success",
            "finished_at": utc_now(),
            "elapsed_s": round(time.time() - started, 3),
            "result_text": run_text,
        })
        return result
    except Exception as exc:  # noqa: BLE001 - sidecar must classify all failures
        result.update({
            "status": "failed",
            "finished_at": utc_now(),
            "elapsed_s": round(time.time() - started, 3),
            "error_type": type(exc).__name__,
            "error": str(exc)[:1000],
            "traceback_tail": "\n".join(traceback.format_exception(exc)[-4:]),
        })
        return result
    finally:
        # The final write happens in main, after execute_task returns.
        pass


async def async_main(args: argparse.Namespace) -> int:
    task = load_task(Path(args.task) if args.task else None, args)
    out_dir = resolve_output_dir(task, args.out_dir)
    result = await execute_task(task, out_dir, Path(args.openmanus_root))
    (out_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    # Console encoding on Windows service shells may be cp1252. Keep stdout
    # ASCII-safe while preserving UTF-8 in result.json above.
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["status"] == "success" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a guarded OpenManus hands task.")
    parser.add_argument("--task", help="Path to JSON task file.")
    parser.add_argument("--instruction", help="Task instruction. Overrides task file instruction.")
    parser.add_argument("--mode", choices=sorted(MODE_TOOL_DEFAULTS), help="Sidecar task mode.")
    parser.add_argument("--task-id", help="Stable task id for output folder naming.")
    parser.add_argument("--out-dir", help="Output directory for task/result JSON.")
    parser.add_argument("--max-seconds", type=int, help="Execution timeout.")
    parser.add_argument("--openmanus-root", default=str(DEFAULT_OPENMANUS_ROOT), help="OpenManus project root.")
    return parser.parse_args()


def main() -> int:
    return asyncio.run(async_main(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
