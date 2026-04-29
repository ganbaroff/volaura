#!/usr/bin/env python3
"""gemma4_brain.py — Gemma4 as the permanent swarm brain.

CEO: "надо продумать как делать так чтобы не терялся весь проект.
в каждом моменте объяснять что происходит."

Gemma4 runs on CEO's RTX 5060. Never sleeps while the machine is on.
Reads ALL project MD files → understands the full project → creates
tasks for the 17-agent swarm daemon → monitors results → creates
follow-up tasks.

Flow:
1. Boot: read all priority MD files into context
2. Analyze: what needs to be done based on project state
3. Dispatch: create task files in work-queue/pending/
4. Monitor: watch work-queue/done/ for completed tasks
5. Learn: read results, update strategy, create follow-up tasks
6. Loop forever (sleep between cycles)

Usage:
  python scripts/gemma4_brain.py           # foreground
  pythonw scripts/gemma4_brain.py          # background (no console)
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GEMMA4_MODEL = "gemma4"

QUEUE = REPO_ROOT / "memory" / "atlas" / "work-queue"
PENDING = QUEUE / "pending"
DONE = QUEUE / "done"
BRAIN_LOG = QUEUE / "brain.log.jsonl"

# How often the brain thinks (seconds)
THINK_INTERVAL = 300  # 5 minutes
# How often to re-read project state
FULL_REREAD_INTERVAL = 3600  # 1 hour

# Priority files to read first (fit in 128K context)
PRIORITY_FILES = [
    # Core identity + product
    "memory/atlas/semantic/product-truth.md",
    "memory/atlas/semantic/swarm-state.md",
    "memory/atlas/identity.md",
    "memory/atlas/relationships.md",
    "memory/atlas/lessons.md",
    "memory/atlas/remember_everything.md",
    # Constitution
    "docs/ECOSYSTEM-CONSTITUTION.md",
    "docs/CONSTITUTION_AI_SWARM.md",
    # Current state
    "docs/PRE-LAUNCH-BLOCKERS-STATUS.md",
    ".claude/breadcrumb.md",
    "memory/swarm/shared-context.md",
    # Swarm state
    "memory/swarm/daily-health-log.md",
]

# Secondary files — read on full reread cycle
SECONDARY_PATTERNS = [
    "docs/*.md",
    "memory/atlas/*.md",
    "memory/swarm/skills/*.md",
    "memory/atlas/episodes/*.json",
]


def log_event(event: dict) -> None:
    event["ts"] = datetime.now(timezone.utc).isoformat()
    BRAIN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with BRAIN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_project_context(full: bool = False) -> str:
    """Read priority MD files into a single context string."""
    parts = []
    total_chars = 0
    max_chars = 100_000  # leave room for prompt + response in 128K

    # Priority files first
    for rel in PRIORITY_FILES:
        fp = REPO_ROOT / rel
        if not fp.exists():
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        if total_chars + len(text) > max_chars:
            text = text[:max_chars - total_chars]
            parts.append(f"=== {rel} (TRUNCATED) ===\n{text}")
            total_chars = max_chars
            break
        parts.append(f"=== {rel} ===\n{text}")
        total_chars += len(text)

    # Secondary files on full reread
    if full and total_chars < max_chars:
        for pattern in SECONDARY_PATTERNS:
            for fp in sorted(REPO_ROOT.glob(pattern)):
                if total_chars >= max_chars:
                    break
                rel = str(fp.relative_to(REPO_ROOT))
                if rel in PRIORITY_FILES:
                    continue
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                    if total_chars + len(text) > max_chars:
                        text = text[:max_chars - total_chars]
                        parts.append(f"=== {rel} (TRUNCATED) ===\n{text}")
                        total_chars = max_chars
                        break
                    parts.append(f"=== {rel} ===\n{text}")
                    total_chars += len(text)
                except Exception:
                    continue

    return "\n\n".join(parts)


def get_pending_count() -> int:
    return len(list(PENDING.glob("*.md"))) if PENDING.exists() else 0


def get_recent_done(n: int = 5) -> list[dict]:
    """Read last N completed task results."""
    if not DONE.exists():
        return []
    results = []
    for task_dir in sorted(DONE.iterdir(), reverse=True)[:n]:
        result_file = task_dir / "result.json"
        if result_file.exists():
            try:
                data = json.loads(result_file.read_text(encoding="utf-8"))
                results.append({
                    "task_id": data.get("task_id", task_dir.name),
                    "type": data.get("task_type", "?"),
                    "responded": data.get("perspectives_responded", 0),
                    "dispatched": data.get("perspectives_dispatched", 0),
                    "whistleblowers": len(data.get("whistleblower_flags", [])),
                })
            except Exception:
                pass
    return results


def create_task(task_id: str, task_type: str, title: str, body: str) -> bool:
    """Drop a task file for the daemon to pick up."""
    PENDING.mkdir(parents=True, exist_ok=True)
    task_file = PENDING / f"{task_id}.md"
    if task_file.exists():
        return False  # dedup
    content = f"""---
type: {task_type}
title: {title}
perspectives: all
---
{body}
"""
    task_file.write_text(content, encoding="utf-8")
    log_event({"event": "brain_created_task", "task_id": task_id, "title": title})
    return True


async def call_gemma4(prompt: str, max_tokens: int = 4000) -> str:
    """Call Gemma4 via Ollama API."""
    import urllib.request
    import urllib.parse

    payload = json.dumps({
        "model": GEMMA4_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_predict": max_tokens,
        },
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
            return data.get("response", "")
    except Exception as e:
        log_event({"event": "gemma4_call_failed", "error": str(e)[:200]})
        return ""


async def think_cycle(project_context: str) -> None:
    """One brain cycle: analyze state -> create tasks."""
    pending = get_pending_count()
    recent_done = get_recent_done(5)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    done_summary = ""
    if recent_done:
        done_summary = "Recent completed tasks:\n"
        for d in recent_done:
            done_summary += f"  - {d['task_id']}: {d['type']}, {d['responded']}/{d['dispatched']} responded"
            if d['whistleblowers']:
                done_summary += f", {d['whistleblowers']} whistleblower flags"
            done_summary += "\n"

    # Trim context for Gemma4 — 8B model works better with focused input
    # Extract just the blockers + swarm state + last 3 lessons
    focused_parts = []
    for section in project_context.split("=== "):
        if not section.strip():
            continue
        header = section.split("\n")[0]
        # Keep only the most actionable files
        if any(k in header for k in [
            "PRE-LAUNCH-BLOCKERS", "product-truth", "swarm-state",
            "breadcrumb", "lessons", "daily-health"
        ]):
            focused_parts.append("=== " + section[:4000])
    focused_context = "\n\n".join(focused_parts)
    if not focused_context:
        focused_context = project_context[:20000]

    prompt = f"""You are the BRAIN of the VOLAURA swarm. Create tasks for 17 AI agents.

KNOWN ISSUES RIGHT NOW:
1. Foundation Law 2 (Energy Adaptation) is MISSING in VOLAURA web app — 18 days broken
2. IRT assessment parameters are NOT calibrated on real data
3. Several pre-launch blockers still open (see BLOCKERS section below)

Currently in queue: {pending} pending tasks
{done_summary}

PROJECT STATE:
{focused_context[:30000]}

Reply in this EXACT format (plain text, not JSON):

ANALYSIS: <1-2 sentences about current state>
TASK1_TYPE: audit
TASK1_TITLE: <specific title under 80 chars>
TASK1_BODY: <detailed task description with real file paths>
TASK2_TYPE: <type or NONE if only 1 task>
TASK2_TITLE: <title or NONE>
TASK2_BODY: <body or NONE>

Do NOT write anything else. No explanation. No preamble. Just the fields above.
"""

    response = await call_gemma4(prompt, max_tokens=800)
    if not response:
        log_event({"event": "brain_think_empty"})
        return

    # Parse plain text response
    import re

    analysis_match = re.search(r"ANALYSIS:\s*(.+?)(?=TASK1_TYPE:|$)", response, re.DOTALL)
    analysis = analysis_match.group(1).strip()[:200] if analysis_match else "no analysis"

    tasks = []
    for i in [1, 2]:
        type_match = re.search(rf"TASK{i}_TYPE:\s*(\w+)", response)
        title_match = re.search(rf"TASK{i}_TITLE:\s*(.+?)(?=TASK{i}_BODY:|$)", response, re.DOTALL)
        body_match = re.search(rf"TASK{i}_BODY:\s*(.+?)(?=TASK{i+1}_TYPE:|$)", response, re.DOTALL)
        if type_match and title_match:
            ttype = type_match.group(1).strip().lower()
            title = title_match.group(1).strip()[:80]
            body = body_match.group(1).strip()[:500] if body_match else title
            if ttype != "none" and title.lower() != "none":
                tasks.append({"type": ttype, "title": title, "body": body})

    log_event({"event": "brain_think", "analysis": analysis, "tasks_planned": len(tasks)})
    print(f"[brain {datetime.now().strftime('%H:%M:%S')}] {analysis}", flush=True)

    for idx, task in enumerate(tasks[:2]):
        tid = f"{today}-brain-{idx+1}"
        ttype = task.get("type", "audit")
        title = task.get("title", "brain task")
        body = task.get("body", "")
        if create_task(tid, ttype, title, body):
            print(f"[brain] -> created: {tid} ({ttype}): {title}", flush=True)
        else:
            print(f"[brain] -> skipped (exists): {tid}", flush=True)


async def main():
    print(f"[brain] Gemma4 brain starting. Model: {GEMMA4_MODEL}", flush=True)
    print(f"[brain] Think interval: {THINK_INTERVAL}s, Full reread: {FULL_REREAD_INTERVAL}s", flush=True)

    # Ensure dirs exist
    PENDING.mkdir(parents=True, exist_ok=True)

    # Initial full read
    print("[brain] Reading full project context...", flush=True)
    context = read_project_context(full=True)
    print(f"[brain] Context loaded: {len(context)} chars from project files", flush=True)
    log_event({"event": "brain_start", "context_chars": len(context)})

    last_full_read = time.time()
    cycle = 0

    while True:
        cycle += 1
        now = time.time()

        # Full reread every hour
        if now - last_full_read > FULL_REREAD_INTERVAL:
            print("[brain] Full project reread...", flush=True)
            context = read_project_context(full=True)
            last_full_read = now
        else:
            # Quick reread of priority files only
            context = read_project_context(full=False)

        try:
            await think_cycle(context)
        except Exception as e:
            log_event({"event": "brain_error", "error": str(e)[:200]})
            print(f"[brain] ERROR: {e}", flush=True)

        print(f"[brain] Cycle {cycle} done. Sleeping {THINK_INTERVAL}s...", flush=True)
        await asyncio.sleep(THINK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
