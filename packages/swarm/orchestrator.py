"""Orchestrator — master agent with completion callbacks and task dependencies.

Replaces flat asyncio.gather with a DAG-aware task runner.
Agents can depend on other agents' results. Master gets notified on completion.

CEO research (Session 88): "оркестратор знает когда кто закончил и передаёт результат дальше"

Usage:
    from swarm.orchestrator import Orchestrator, AgentTask

    orch = Orchestrator(runner=your_agent_runner, on_complete=your_callback)
    orch.add_task(AgentTask("security", "security-agent", {"audit": "law1"}))
    orch.add_task(AgentTask("synthesis", "architect", {"review": "all"}, depends_on=["security"]))
    results = await orch.run_all()
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from loguru import logger

from .shared_memory import post_result, get_context


@dataclass
class AgentTask:
    """A task for one agent, optionally depending on other tasks."""
    task_id: str
    agent_id: str
    input: dict[str, Any]
    depends_on: list[str] = field(default_factory=list)
    result: dict[str, Any] | None = None
    completed: bool = False
    error: str | None = None


class Orchestrator:
    """DAG-aware task runner with completion callbacks."""

    def __init__(
        self,
        runner: Callable[[str, dict], Awaitable[dict | None]],
        on_complete: Callable[[AgentTask, dict], Awaitable[None]] | None = None,
        run_id: str = "",
    ):
        self.runner = runner
        self.on_complete = on_complete
        self.run_id = run_id
        self.tasks: dict[str, AgentTask] = {}
        self._completed: set[str] = set()

    def add_task(self, task: AgentTask) -> None:
        self.tasks[task.task_id] = task

    def _ready_tasks(self) -> list[AgentTask]:
        """Tasks whose dependencies are all completed."""
        ready = []
        for t in self.tasks.values():
            if t.completed:
                continue
            if all(dep in self._completed for dep in t.depends_on):
                ready.append(t)
        return ready

    async def _run_task(self, task: AgentTask) -> None:
        """Run one task: inject dependency context, execute, callback."""
        # Inject results from dependencies into task input
        for dep_id in task.depends_on:
            dep_task = self.tasks.get(dep_id)
            if dep_task and dep_task.result:
                task.input[f"context_from_{dep_id}"] = dep_task.result

        # Also inject shared memory context for this run
        try:
            shared = get_context(self.run_id)
            if shared:
                task.input["shared_memory"] = shared
        except Exception:
            pass

        try:
            result = await self.runner(task.agent_id, task.input)
            task.result = result or {}
            task.completed = True
            self._completed.add(task.task_id)

            # Post to shared memory
            post_result(task.agent_id, task.task_id, task.result, run_id=self.run_id)

            logger.info(
                "Orchestrator: {agent} completed task {task}",
                agent=task.agent_id, task=task.task_id,
            )

            # Fire completion callback
            if self.on_complete and result:
                await self.on_complete(task, result)

        except Exception as e:
            task.error = str(e)[:200]
            task.completed = True
            self._completed.add(task.task_id)
            logger.error(
                "Orchestrator: {agent} failed on {task}: {err}",
                agent=task.agent_id, task=task.task_id, err=task.error,
            )

    async def run_all(self, timeout: float = 300) -> dict[str, AgentTask]:
        """Run all tasks respecting dependencies. Returns task map with results."""
        if not self.tasks:
            return {}

        start = asyncio.get_event_loop().time()

        while len(self._completed) < len(self.tasks):
            if asyncio.get_event_loop().time() - start > timeout:
                logger.warning("Orchestrator: timeout after {t}s", t=timeout)
                break

            ready = self._ready_tasks()
            if not ready:
                # All remaining tasks have unmet dependencies — deadlock
                remaining = [t.task_id for t in self.tasks.values() if not t.completed]
                logger.warning("Orchestrator: deadlock — {n} tasks stuck: {ids}", n=len(remaining), ids=remaining)
                break

            # Run all ready tasks in parallel
            await asyncio.gather(*[self._run_task(t) for t in ready])

        return self.tasks
