"""Swarm backlog — persistent task tracking with dependencies.

Replaces the proposal inbox (detection) with a real work board (coordination).
Tasks have assignees, dependencies, acceptance criteria, and blocker tracking.
Storage: memory/swarm/backlog.json — append-friendly, backward-compatible.

CLI: python -m packages.swarm.backlog status
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

BACKLOG_PATH = Path(__file__).resolve().parent.parent.parent / "memory" / "swarm" / "backlog.json"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class BacklogTask(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str
    status: TaskStatus = TaskStatus.TODO
    assignee: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)
    blocked_by: Optional[str] = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: Optional[str] = None
    findings: Optional[str] = None


class Backlog:
    def __init__(self, path: Path = BACKLOG_PATH):
        self.path = path
        self._tasks: list[BacklogTask] = []
        self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self._tasks = [BacklogTask(**t) for t in data]
        else:
            self._tasks = []

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([t.model_dump() for t in self._tasks], f, indent=2, ensure_ascii=False)

    def add(self, title: str, assignee: str | None = None, depends_on: list[str] | None = None,
            acceptance_criteria: list[str] | None = None, source: str | None = None) -> BacklogTask:
        task = BacklogTask(
            title=title,
            assignee=assignee,
            depends_on=depends_on or [],
            acceptance_criteria=acceptance_criteria or [],
            source=source,
        )
        self._tasks.append(task)
        self._save()
        return task

    def update(self, task_id: str, **kwargs) -> BacklogTask | None:
        task = self.get(task_id)
        if not task:
            return None
        for k, v in kwargs.items():
            if hasattr(task, k):
                setattr(task, k, v)
        task.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return task

    def get(self, task_id: str) -> BacklogTask | None:
        for t in self._tasks:
            if t.id == task_id:
                return t
        return None

    def by_status(self, status: TaskStatus) -> list[BacklogTask]:
        return [t for t in self._tasks if t.status == status]

    def blocked(self) -> list[BacklogTask]:
        return self.by_status(TaskStatus.BLOCKED)

    def ready(self) -> list[BacklogTask]:
        """Tasks whose dependencies are all DONE."""
        done_ids = {t.id for t in self._tasks if t.status == TaskStatus.DONE}
        return [
            t for t in self._tasks
            if t.status == TaskStatus.TODO
            and all(dep in done_ids for dep in t.depends_on)
        ]

    def dag_order(self) -> list[list[BacklogTask]]:
        """Return tasks grouped into execution waves (topological layers).
        Wave 0 = no deps, Wave 1 = depends on Wave 0, etc."""
        done_ids = {t.id for t in self._tasks if t.status == TaskStatus.DONE}
        remaining = [t for t in self._tasks if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)]
        waves: list[list[BacklogTask]] = []
        placed = set(done_ids)

        while remaining:
            wave = [t for t in remaining if all(d in placed for d in t.depends_on)]
            if not wave:
                waves.append(remaining)
                break
            waves.append(wave)
            placed.update(t.id for t in wave)
            remaining = [t for t in remaining if t.id not in placed]

        return waves

    def board(self) -> str:
        """Human-readable sprint board."""
        lines = ["SWARM BACKLOG", "=" * 40]
        for status in TaskStatus:
            tasks = self.by_status(status)
            if tasks:
                lines.append(f"\n{status.value.upper()} ({len(tasks)})")
                lines.append("-" * 30)
                for t in tasks:
                    assignee = f" [{t.assignee}]" if t.assignee else ""
                    deps = f" (deps: {','.join(t.depends_on)})" if t.depends_on else ""
                    blocker = f" BLOCKED: {t.blocked_by}" if t.blocked_by else ""
                    lines.append(f"  {t.id} {t.title}{assignee}{deps}{blocker}")

        blocked = self.blocked()
        if blocked:
            lines.append(f"\n!! {len(blocked)} task(s) BLOCKED")

        return "\n".join(lines)

    @property
    def all(self) -> list[BacklogTask]:
        return list(self._tasks)


def _cli():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    backlog = Backlog()

    if cmd == "status":
        print(backlog.board())
    elif cmd == "ready":
        for t in backlog.ready():
            print(f"{t.id} {t.title} (assignee: {t.assignee or 'unassigned'})")
    elif cmd == "dag":
        for i, wave in enumerate(backlog.dag_order()):
            print(f"Wave {i}: {', '.join(t.title for t in wave)}")
    elif cmd == "add":
        title = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Untitled task"
        task = backlog.add(title=title)
        print(f"Added: {task.id} — {task.title}")
    else:
        print(f"Unknown command: {cmd}. Use: status, ready, dag, add <title>")


if __name__ == "__main__":
    _cli()
