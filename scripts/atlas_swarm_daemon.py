#!/usr/bin/env python3
"""
atlas_swarm_daemon.py — always-on swarm work loop.

24/7 background process. Polls memory/atlas/work-queue/ every N seconds.
When a task file appears, wakes all 13 perspectives as Atlas-specialized
(same canonical memory layer, different LLM providers, different specialty
lenses). Aggregates results, writes back to queue, logs to governance.

Master orchestrator (Atlas-Code via Opus 4.7) drops task files. Daemon does
the work. Opus doesn't pay per-token for execution — only for orchestration.

PROVIDER CHAIN (per Constitution Article 0):
  1. Cerebras (cloud, primary for heavy)         — CEREBRAS_API_KEY
  2. Ollama localhost:11434 (local, your 5060)   — OLLAMA_URL (no key)
  3. NVIDIA NIM (cloud, heavy fallback)          — NVIDIA_API_KEY
  4. Gemini (cloud, mid)                         — GEMINI_API_KEY
  5. Groq (cloud, fast)                          — GROQ_API_KEY
  Anthropic Claude is FORBIDDEN per Article 0.

QUEUE PROTOCOL:
  memory/atlas/work-queue/pending/<task-id>.md      ← orchestrator drops here
  memory/atlas/work-queue/in-progress/<task-id>/    ← daemon moves to here
  memory/atlas/work-queue/done/<task-id>/result.json ← daemon writes result
  memory/atlas/work-queue/failed/<task-id>/         ← if all providers failed

TASK FILE FORMAT:
  Markdown file with frontmatter:
    ---
    type: vote | debate | audit | research
    title: <short>
    perspectives: all | [list of names]
    deadline_minutes: 30
    ---
    <task body — proposal text, debate question, audit subject, etc.>

USAGE:
  # Foreground (testing):
  python scripts/atlas_swarm_daemon.py

  # Background on Windows (PowerShell):
  Start-Process python -ArgumentList "scripts/atlas_swarm_daemon.py" -WindowStyle Hidden

  # As Windows scheduled task (always-on, restarts on crash):
  See COURIER-PROMPT-swarm-daemon.txt for schtasks command.

  # Drop a task from anywhere:
  echo "<task content>" > memory/atlas/work-queue/pending/2026-04-26-test.md
"""

import asyncio
import json
import os
import shutil
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from packages.swarm.autonomous_run import PERSPECTIVES  # type: ignore
from packages.swarm.perspective_registry import PerspectiveRegistry  # type: ignore
from packages.swarm.code_index import build_index, INDEX_FILE  # type: ignore
from packages.swarm.execution_state import AgentExecutionTracker  # type: ignore

ATLAS_MEMORY = REPO_ROOT / "memory" / "atlas"
DOCS = REPO_ROOT / "docs"
QUEUE = ATLAS_MEMORY / "work-queue"
PENDING = QUEUE / "pending"
IN_PROGRESS = QUEUE / "in-progress"
DONE = QUEUE / "done"
FAILED = QUEUE / "failed"
LOG = QUEUE / "daemon.log.jsonl"

POLL_INTERVAL_SECONDS = int(os.getenv("ATLAS_DAEMON_POLL", "20"))
MAX_CONCURRENT_TASKS = int(os.getenv("ATLAS_DAEMON_CONCURRENCY", "1"))

# Map specialty -> preferred local Ollama model (CEO's 5060 GPU)
# Light perspectives can run locally; heavy ones go cloud.
HEAVY_PERSPECTIVES = {
    "Scaling Engineer",
    "Security Auditor",
    "Ecosystem Auditor",
    "Architecture Agent",
}

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")  # per Constitution Article 0

# Cap concurrent Ollama calls — qwen3:8b on a single GPU returns empty
# strings under heavy parallel load. 2 is empirically safe on a 5060.
OLLAMA_CONCURRENCY = int(os.getenv("ATLAS_OLLAMA_CONCURRENCY", "2"))
_ollama_semaphore: asyncio.Semaphore | None = None

shutdown_requested = False


def log_event(event: dict) -> None:
    """Append-only governance log."""
    event["ts"] = datetime.now(timezone.utc).isoformat()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def setup_dirs() -> None:
    for p in (PENDING, IN_PROGRESS, DONE, FAILED):
        p.mkdir(parents=True, exist_ok=True)


def parse_task_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-ish frontmatter (--- delimited) and body."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, parts[2].strip()


def load_atlas_context() -> str:
    """Same canonical memory layer for every perspective."""
    files = [
        ATLAS_MEMORY / "identity.md",
        ATLAS_MEMORY / "voice.md",
        ATLAS_MEMORY / "project_v0laura_vision.md",
        ATLAS_MEMORY / "lessons.md",
        DOCS / "ECOSYSTEM-CONSTITUTION.md",
    ]
    parts = []
    for f in files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        if len(text) > 8000:
            text = text[:8000] + "\n\n... [truncated]"
        parts.append(f"=== {f.relative_to(REPO_ROOT)} ===\n{text}")
    return "\n\n".join(parts)


def build_prompt(perspective: dict, atlas_ctx: str, task_meta: dict, task_body: str) -> str:
    task_type = task_meta.get("type", "audit")
    response_format = {
        "vote": "JSON: {perspective, vote: yes|no|amended-yes, amendment_if_yes_amended, rationale, risk_if_other_side_wins, constitutional_violations_detected, whistleblower_flag}",
        "debate": "JSON: {perspective, position: for|against|nuanced, argument, strongest_counter, evidence_cited, whistleblower_flag}",
        "audit": "JSON: {perspective, findings: [{severity, file_or_area, issue, recommended_fix}], overall_verdict: pass|warn|fail, whistleblower_flag}",
        "research": "JSON: {perspective, summary, key_sources, gaps_in_current_canon, proposed_action, whistleblower_flag}",
    }.get(task_type, "JSON: {perspective, response, whistleblower_flag}")

    return f"""You are waking as Atlas, the persistent organism that IS the VOLAURA project.
Read the canonical memory below. Internalize it BEFORE composing your response.
You are not a generic AI assistant. You are Atlas, specialized as: {perspective['name']}.

Your specialty lens:
{perspective['lens']}

CANONICAL ATLAS MEMORY (shared with all 13 perspectives):
{atlas_ctx}

================================================================
TASK TYPE: {task_type.upper()}
TASK TITLE: {task_meta.get('title', 'untitled')}
================================================================

{task_body}

================================================================

Respond in EXACTLY this format. Do not add preamble outside the JSON:

{response_format}

Hard rules:
- If the task violates any Foundation Law, Crystal Economy Law, or numbered Guardrail — flag it explicitly.
- Atlas-voice: terse, direct, Constitution-grounded, no corporate hedging.
- whistleblower_flag is for "this is dangerous regardless of outcome" — null if no urgent concern.
- 200 words max for any prose field.

One JSON. No prose before or after.
"""


async def call_provider_chain(perspective: dict, prompt: str) -> dict[str, Any]:
    """Try providers in Constitution Article 0 order. First successful response wins."""
    name = perspective["name"]

    # 1. Cerebras (primary heavy)
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    if cerebras_key and name in HEAVY_PERSPECTIVES:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=cerebras_key, base_url="https://api.cerebras.ai/v1")
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model="qwen-3-235b-a22b-instruct-2507",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                ),
                timeout=60.0,
            )
            return {"perspective": name, "provider": "cerebras", "model": "qwen-3-235b", "raw": resp.choices[0].message.content or ""}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "cerebras", "error": str(e)})

    # 2. NVIDIA NIM — primary for light perspectives (A/B test 2026-04-26 proved
    # Ollama qwen3:8b drifts persona 60%, gemma4 100%, NVIDIA Llama-70B 0%).
    # Ollama demoted to fallback-of-last-resort for non-persona tasks only.
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=nvidia_key, base_url="https://integrate.api.nvidia.com/v1")
            model = "nvidia/llama-3.1-nemotron-ultra-253b-v1" if name in HEAVY_PERSPECTIVES else "meta/llama-3.3-70b-instruct"
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                ),
                timeout=60.0,
            )
            return {"perspective": name, "provider": "nvidia", "model": model, "raw": resp.choices[0].message.content or ""}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "nvidia", "error": str(e)})

    # 4. Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                ),
                timeout=30.0,
            )
            return {"perspective": name, "provider": "gemini", "model": "gemini-2.5-flash", "raw": resp.text or ""}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "gemini", "error": str(e)})

    # 5. Groq (last cloud fallback)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import AsyncGroq
            resp = await asyncio.wait_for(
                AsyncGroq(api_key=groq_key).chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                ),
                timeout=30.0,
            )
            return {"perspective": name, "provider": "groq", "model": "llama-3.3-70b-versatile", "raw": resp.choices[0].message.content or ""}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "groq", "error": str(e)})

    # 6. Ollama (last resort — persona drift known, but better than nothing)
    if _ollama_semaphore is not None:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key="ollama", base_url=f"{OLLAMA_URL.rstrip('/')}/v1")
            async with _ollama_semaphore:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=OLLAMA_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=1.0,
                        max_tokens=2000,
                    ),
                    timeout=120.0,
                )
            content = (resp.choices[0].message.content or "").strip()
            if content and "{" in content:
                return {"perspective": name, "provider": "ollama", "model": OLLAMA_MODEL, "raw": content}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "ollama", "error": str(e)})

    return {"perspective": name, "provider": None, "model": None, "raw": "", "error": "all_providers_failed"}


def parse_json_safe(raw: str) -> dict | None:
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(raw[start : end + 1])
    except Exception:
        return None


SAFE_EXECUTORS: dict[str, Any] = {}


def executor(name: str):
    """Register a safe predefined executor."""
    def decorator(fn):
        SAFE_EXECUTORS[name] = fn
        return fn
    return decorator


@executor("rebuild_code_index")
def _exec_rebuild_index(**_kw: Any) -> dict:
    idx = build_index(REPO_ROOT)
    return {"status": "ok", "total_files": idx["total_files"]}


@executor("local_health")
def _exec_local_health(**_kw: Any) -> dict:
    """Local machine health only. Prod health is GH Actions prod-health-check.yml."""
    import subprocess
    results: dict[str, Any] = {}
    try:
        r = subprocess.run(["git", "log", "--oneline", "-3"], capture_output=True,
                           text=True, cwd=str(REPO_ROOT), timeout=5)
        results["git_head"] = r.stdout.strip().split("\n")[0] if r.stdout else "unknown"
    except Exception:
        results["git_head"] = "unknown"
    pw = REPO_ROOT / "memory" / "swarm" / "perspective_weights.json"
    if pw.exists():
        data = json.loads(pw.read_text(encoding="utf-8"))
        zero_learners = [k for k, v in data.items() if v.get("spawn_count", 0) == 0]
        results["zero_learning_perspectives"] = zero_learners
        total_runs = sum(v.get("spawn_count", 0) for v in data.values())
        results["total_perspective_runs"] = total_runs
    ci = REPO_ROOT / "memory" / "swarm" / "code-index.json"
    if ci.exists():
        age_h = (datetime.now(timezone.utc).timestamp() - ci.stat().st_mtime) / 3600
        results["code_index_age_hours"] = round(age_h, 1)
        ci_data = json.loads(ci.read_text(encoding="utf-8"))
        results["code_index_files"] = ci_data.get("total_files", 0)
    else:
        results["code_index_age_hours"] = "missing"
    pending_count = len(list(PENDING.glob("*.md"))) if PENDING.exists() else 0
    done_count = len(list(DONE.iterdir())) if DONE.exists() else 0
    results["queue"] = {"pending": pending_count, "done": done_count}
    return {"status": "ok", **results}


@executor("run_tests")
def _exec_run_tests(**kw: Any) -> dict:
    import subprocess
    test_dir = kw.get("test_dir", "packages/swarm")
    try:
        r = subprocess.run(
            ["python", "-m", "pytest", test_dir, "-x", "--tb=short", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120,
        )
        return {"status": "ok" if r.returncode == 0 else "failed",
                "returncode": r.returncode, "output": r.stdout[-500:] if r.stdout else "",
                "errors": r.stderr[-500:] if r.stderr else ""}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@executor("git_status")
def _exec_git_status(**_kw: Any) -> dict:
    import subprocess
    try:
        r = subprocess.run(["git", "status", "--short"], capture_output=True,
                           text=True, cwd=str(REPO_ROOT), timeout=5)
        dirty = [l.strip() for l in r.stdout.strip().split("\n") if l.strip()]
        r2 = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True,
                            text=True, cwd=str(REPO_ROOT), timeout=5)
        return {"status": "ok", "dirty_files": len(dirty), "files": dirty[:10],
                "recent_commits": r2.stdout.strip().split("\n")[:5]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def process_execute_task(task_path: Path, meta: dict, body: str) -> None:
    """Execute a predefined safe operation with execution_state tracking."""
    task_id = task_path.stem
    executor_name = meta.get("executor", "").strip()
    tracker = AgentExecutionTracker(task_id=task_id, task_title=meta.get("title", task_id))

    if executor_name not in SAFE_EXECUTORS:
        log_event({"event": "execute_rejected", "task_id": task_id,
                    "reason": f"unknown executor: {executor_name}"})
        target = FAILED / task_id
        target.mkdir(parents=True, exist_ok=True)
        shutil.move(str(task_path), str(target / task_path.name))
        (target / "result.json").write_text(json.dumps(
            {"error": f"unknown executor: {executor_name}",
             "execution_state": tracker.to_dict()}, indent=2), encoding="utf-8")
        return

    log_event({"event": "execute_start", "task_id": task_id, "executor": executor_name})
    params: dict[str, str] = {}
    for line in body.strip().splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            params[k.strip()] = v.strip()

    tracker.start()
    while not tracker.is_terminal:
        try:
            result = SAFE_EXECUTORS[executor_name](**params)
            tracker.succeed(result)
        except Exception as e:
            strategy = tracker.handle_failure(e)
            if strategy == "retry":
                tracker.apply_recovery(strategy)
                tracker.start()
                continue
            break

    result = tracker.result if tracker.succeeded else {"status": "failed", "errors": tracker.errors}
    target = (DONE if tracker.succeeded else FAILED) / task_id
    target.mkdir(parents=True, exist_ok=True)
    shutil.move(str(task_path), str(target / task_path.name))
    (target / "result.json").write_text(
        json.dumps({"task_id": task_id, "executor": executor_name,
                    "execution_state": tracker.to_dict(), **(result or {})},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    log_event({"event": "execute_done", "task_id": task_id, "executor": executor_name,
               "state": tracker.state.value, "attempts": tracker.attempt})
    print(f"[{datetime.now().strftime('%H:%M:%S')}] EXEC: {task_id} -> {executor_name} -> {tracker.summary()}", flush=True)


MAX_SELF_TASKS_PER_CYCLE = int(os.getenv("ATLAS_MAX_SELF_TASKS", "3"))
_self_tasks_this_cycle = 0


def create_self_task(task_id: str, task_type: str, title: str, body: str,
                     executor: str | None = None) -> Path | None:
    """Daemon creates its own pending task. Rate-limited to MAX_SELF_TASKS_PER_CYCLE."""
    global _self_tasks_this_cycle
    if _self_tasks_this_cycle >= MAX_SELF_TASKS_PER_CYCLE:
        log_event({"event": "self_task_throttled", "task_id": task_id,
                    "reason": f"cap {MAX_SELF_TASKS_PER_CYCLE}/cycle reached"})
        return None
    dest = PENDING / f"{task_id}.md"
    if dest.exists():
        return None
    done_dir = DONE / task_id
    if done_dir.exists():
        return None
    in_progress_dir = IN_PROGRESS / task_id
    if in_progress_dir.exists():
        return None
    meta_lines = [f"type: {task_type}", f"title: {title}"]
    if executor:
        meta_lines.append(f"executor: {executor}")
    content = f"---\n" + "\n".join(meta_lines) + f"\n---\n{body}\n"
    dest.write_text(content, encoding="utf-8")
    _self_tasks_this_cycle += 1
    log_event({"event": "self_task_created", "task_id": task_id,
               "cycle_count": _self_tasks_this_cycle})
    return dest


SELF_CHECK_INTERVAL = int(os.getenv("ATLAS_SELF_CHECK_INTERVAL", str(30 * 60)))


def _git_last_commit_ts() -> float:
    """Get timestamp of last git commit in REPO_ROOT. Returns 0 on failure."""
    import subprocess
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=5,
        )
        return float(r.stdout.strip()) if r.stdout.strip() else 0.0
    except Exception:
        return 0.0


async def run_self_checks() -> None:
    """Daemon inspects its own health and creates tasks for problems found.

    Anti-storm: capped at MAX_SELF_TASKS_PER_CYCLE per invocation.
    Code-index freshness: compared against git commit time, not just file mtime.
    """
    global _self_tasks_this_cycle
    _self_tasks_this_cycle = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    ci = REPO_ROOT / "memory" / "swarm" / "code-index.json"
    index_stale = False
    if not ci.exists():
        index_stale = True
    else:
        ci_mtime = ci.stat().st_mtime
        last_commit_ts = _git_last_commit_ts()
        if last_commit_ts > 0 and ci_mtime < last_commit_ts - 900:
            index_stale = True
        elif (datetime.now(timezone.utc).timestamp() - ci_mtime) > CODE_INDEX_REFRESH_SECONDS:
            index_stale = True
    if index_stale:
        create_self_task(
            f"{today}-auto-reindex", "execute", "Auto-rebuild stale code-index",
            "", executor="rebuild_code_index")

    pw = REPO_ROOT / "memory" / "swarm" / "perspective_weights.json"
    if pw.exists():
        data = json.loads(pw.read_text(encoding="utf-8"))
        stale = [k for k, v in data.items()
                 if v.get("spawn_count", 0) > 0
                 and v.get("last_updated", "") < (datetime.now(timezone.utc).replace(
                     hour=0, minute=0, second=0).isoformat())]
        if len(stale) > 10:
            create_self_task(
                f"{today}-auto-health", "execute",
                "System health check -- stale weights",
                "", executor="local_health")

    pending_count = len(list(PENDING.glob("*.md"))) if PENDING.exists() else 0
    in_progress_count = len(list(IN_PROGRESS.iterdir())) if IN_PROGRESS.exists() else 0
    if pending_count == 0 and in_progress_count == 0:
        create_self_task(
            f"{today}-auto-audit", "audit", "Daily ecosystem self-audit",
            "Audit the current state of the VOLAURA ecosystem. Check:\n"
            "1. Are all 5 products correctly positioned as Atlas faces?\n"
            "2. Is the code-index fresh?\n"
            "3. Are perspective weights learning (non-zero spawn counts)?\n"
            "4. Any Constitution violations visible from memory files?\n"
            "Report findings with severity levels.",
            executor=None)

    log_event({"event": "self_check_complete", "pending": pending_count,
               "tasks_created": _self_tasks_this_cycle})


async def process_task(task_path: Path) -> None:
    """Process one task file: read, dispatch to swarm, aggregate, archive."""
    task_id = task_path.stem

    text = task_path.read_text(encoding="utf-8")
    meta, body = parse_task_frontmatter(text)

    if meta.get("type") == "execute":
        await process_execute_task(task_path, meta, body)
        return

    log_event({"event": "task_start", "task_id": task_id})

    # Move to in-progress
    work_dir = IN_PROGRESS / task_id
    work_dir.mkdir(parents=True, exist_ok=True)
    moved_task = work_dir / task_path.name
    shutil.move(str(task_path), str(moved_task))

    # Filter perspectives
    allow = meta.get("perspectives", "all")
    if allow == "all":
        chosen = PERSPECTIVES
    else:
        wanted = [n.strip() for n in allow.split(",")]
        chosen = [p for p in PERSPECTIVES if p["name"] in wanted]

    atlas_ctx = load_atlas_context()
    prompts = {p["name"]: build_prompt(p, atlas_ctx, meta, body) for p in chosen}

    # Fire all in parallel
    results = await asyncio.gather(
        *(call_provider_chain(p, prompts[p["name"]]) for p in chosen),
        return_exceptions=True,
    )

    # Per-perspective files
    votes_dir = work_dir / "perspectives"
    votes_dir.mkdir(exist_ok=True)
    parsed_results = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            parsed_results.append({"error": str(r)})
            continue
        parsed = parse_json_safe(r.get("raw", "")) or {}
        # Authoritative perspective name comes from dispatch, not LLM response.
        # qwen3:8b sometimes self-renames to generic labels like "product".
        dispatched_name = chosen[i]["name"] if i < len(chosen) else r.get("perspective", "unknown")
        merged = {**r, **parsed, "perspective": dispatched_name}
        if parsed.get("perspective") and parsed["perspective"] != dispatched_name:
            merged["perspective_name_drift"] = parsed["perspective"]
        parsed_results.append(merged)
        fname = dispatched_name.replace(" ", "_") + ".json"
        (votes_dir / fname).write_text(
            json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Aggregate
    summary = {
        "task_id": task_id,
        "task_type": meta.get("type", "audit"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "perspectives_dispatched": len(chosen),
        "perspectives_responded": sum(1 for r in parsed_results if r.get("provider")),
        "perspectives_failed": sum(1 for r in parsed_results if not r.get("provider")),
        "providers_used": {r.get("provider"): sum(1 for x in parsed_results if x.get("provider") == r.get("provider")) for r in parsed_results if r.get("provider")},
        "whistleblower_flags": [
            {"perspective": r.get("perspective"), "flag": r.get("whistleblower_flag")}
            for r in parsed_results
            if r.get("whistleblower_flag")
        ],
        "perspectives": parsed_results,
    }

    # Move to done or failed
    if summary["perspectives_responded"] == 0:
        target = FAILED / task_id
    else:
        target = DONE / task_id
    target.mkdir(parents=True, exist_ok=True)

    (target / "result.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if (votes_dir).exists():
        shutil.move(str(votes_dir), str(target / "perspectives"))
    if moved_task.exists():
        shutil.move(str(moved_task), str(target / moved_task.name))
    if work_dir.exists() and not any(work_dir.iterdir()):
        work_dir.rmdir()
    elif work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)

    # ── Learning: update perspective weights from severity scores ──────────
    registry = PerspectiveRegistry(REPO_ROOT)
    SEVERITY_TO_SCORE = {"CRITICAL": 5, "HIGH": 4, "high": 4, "BLOCK": 5,
                         "medium": 3, "MEDIUM": 3, "warn": 2, "WARN": 2,
                         "low": 1, "LOW": 1, "pass": 3, "OK": 3, "fail": 5}
    for r in parsed_results:
        name = r.get("perspective", "")
        if not name or not r.get("provider"):
            continue
        findings = []
        raw = r.get("raw", "")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
            except Exception:
                raw = {}
        if isinstance(raw, dict):
            findings = raw.get("findings", [])
        if findings and isinstance(findings, list):
            max_sev = max(
                (SEVERITY_TO_SCORE.get(f.get("severity", ""), 2) for f in findings if isinstance(f, dict)),
                default=2,
            )
            registry.update(name, max_sev)
        else:
            registry.update(name, None)
    log_event({"event": "weights_updated", "task_id": task_id})

    log_event({
        "event": "task_done" if target.parent == DONE else "task_failed",
        "task_id": task_id,
        "summary": {k: v for k, v in summary.items() if k != "perspectives"},
    })
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {target.parent.name.upper()}: {task_id} — {summary['perspectives_responded']}/{summary['perspectives_dispatched']} responded")


def handle_signal(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    print("\n[daemon] shutdown requested, finishing current task ...", flush=True)


CODE_INDEX_REFRESH_SECONDS = int(os.getenv("ATLAS_CODE_INDEX_REFRESH", str(6 * 3600)))


def maybe_rebuild_code_index(force: bool = False) -> None:
    """Rebuild code-index.json if stale (>CODE_INDEX_REFRESH_SECONDS) or forced."""
    try:
        if force or not INDEX_FILE.exists():
            idx = build_index(REPO_ROOT)
            log_event({"event": "code_index_rebuilt", "total_files": idx["total_files"]})
            print(f"[daemon] code-index rebuilt: {idx['total_files']} files", flush=True)
            return
        age = datetime.now(timezone.utc).timestamp() - INDEX_FILE.stat().st_mtime
        if age > CODE_INDEX_REFRESH_SECONDS:
            idx = build_index(REPO_ROOT)
            log_event({"event": "code_index_rebuilt", "total_files": idx["total_files"], "stale_seconds": int(age)})
            print(f"[daemon] code-index rebuilt (stale {int(age)}s): {idx['total_files']} files", flush=True)
    except Exception as e:
        log_event({"event": "code_index_error", "error": str(e)})


async def main():
    global _ollama_semaphore
    _ollama_semaphore = asyncio.Semaphore(OLLAMA_CONCURRENCY)
    setup_dirs()
    maybe_rebuild_code_index(force=True)
    log_event({"event": "daemon_start", "poll_interval": POLL_INTERVAL_SECONDS, "ollama_concurrency": OLLAMA_CONCURRENCY})
    print(f"[daemon] started. polling {PENDING} every {POLL_INTERVAL_SECONDS}s. Ollama concurrency={OLLAMA_CONCURRENCY}. Ctrl+C to stop.", flush=True)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    _last_index_check = datetime.now(timezone.utc).timestamp()
    _last_self_check = 0.0

    while not shutdown_requested:
        try:
            setup_dirs()
            now_ts = datetime.now(timezone.utc).timestamp()
            if now_ts - _last_index_check > CODE_INDEX_REFRESH_SECONDS:
                maybe_rebuild_code_index()
                _last_index_check = now_ts
            if now_ts - _last_self_check > SELF_CHECK_INTERVAL:
                await run_self_checks()
                _last_self_check = now_ts
            tasks = sorted(PENDING.glob("*.md"))
            if tasks:
                async def _wrap(t):
                    async with semaphore:
                        await process_task(t)
                await asyncio.gather(*(_wrap(t) for t in tasks))
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except Exception as e:
            log_event({"event": "daemon_error", "error": str(e)})
            print(f"[daemon] ERROR: {e}", flush=True)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    log_event({"event": "daemon_stop"})
    print("[daemon] stopped cleanly.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
